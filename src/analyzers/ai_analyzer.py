import json
import asyncio
import httpx
from typing import Dict, List, Any
import google.generativeai as genai
from .base import BaseAnalyzer
from ..database.models import Post
from ..config import settings

MARKET_KEYWORDS = [
    'stock', 'market', 'economy', 'interest rate', 'inflation',
    'policy', 'regulation', 'AI', 'technology', 'trade'
]

class AIAnalyzer(BaseAnalyzer):
    def __init__(self):
        # Initialize Gemini API
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        # Initialize Nemotron API client
        self.nemotron_client = httpx.AsyncClient(
            base_url="https://nvidia.api/v1/chat",
            headers={
                "Authorization": f"Bearer {settings.NEMOTRON_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=30.0  # 30 second timeout
        )
        self.nemotron_model = "nvidia/llama-3.1-nemotron-70b-instruct"

    async def analyze_post(self, post: Post) -> Dict[str, Any]:
        """Perform comprehensive analysis of a post"""
        try:
            # Run analyses in parallel for better performance
            sentiment, market_impact = await asyncio.gather(
                self._analyze_sentiment(post.content),
                self.get_market_impact_score(post)
            )
            
            # Generate summary and tags (these use Gemini API)
            summary = await self._generate_summary(post.content)
            tags = await self.extract_tags(post)
            context = await self._generate_context(post)
            
            return {
                'sentiment': sentiment,
                'summary': summary,
                'tags': tags,
                'market_impact_score': market_impact,
                'context': context
            }
        except Exception as e:
            print(f"Error analyzing post: {e}")
            return {
                'sentiment': {'label': 'neutral', 'score': 0.5},
                'summary': post.content[:100] + "..." if post.content else "",
                'tags': [],
                'market_impact_score': 0.5,
                'context': f"Post by {post.author.name} on {post.posted_at}" if post.author else ""
            }

    async def get_market_impact_score(self, post: Post) -> float:
        """Calculate market impact score based on content and author"""
        try:
            # Add author context for better analysis
            prompt = f"""Analyze the market impact of this post by {post.author.name} ({post.author.title}):
            {post.content}
            
            Rate the potential impact on financial markets from 0.0 (no impact) to 1.0 (major impact).
            Respond with only a number between 0.0 and 1.0."""

            response = await self.nemotron_client.post(
                "/completions",
                json={
                    "model": self.nemotron_model,
                    "messages": [
                        {"role": "system", "content": "You are an expert in financial market analysis."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 10
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                score_text = result['choices'][0]['message']['content'].strip()
                try:
                    score = float(score_text)
                    return min(max(score, 0.0), 1.0)
                except ValueError:
                    return 0.5
            return 0.5
        except Exception as e:
            print(f"Error getting market impact score: {e}")
            return 0.5

    async def extract_tags(self, post: Post) -> List[str]:
        """Extract relevant tags from the post content"""
        try:
            prompt = f"""Analyze this post and identify relevant market-related tags from these categories: {', '.join(MARKET_KEYWORDS)}
            Return only the relevant tags as a comma-separated list.
            Post: {post.content}"""
            
            response = await self._async_generate_content(prompt)
            if response:
                tags = [tag.strip() for tag in response.split(',')]
                return [tag for tag in tags if tag.lower() in [k.lower() for k in MARKET_KEYWORDS]]
            return []
        except Exception as e:
            print(f"Error extracting tags: {e}")
            return []
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of the text"""
        try:
            prompt = f"""Analyze the sentiment of this text:
            {text}
            
            Respond with a JSON object containing 'label' (positive, negative, or neutral) and 'score' (0.0 to 1.0).
            Example: {{"label": "positive", "score": 0.8}}"""

            response = await self.nemotron_client.post(
                "/completions",
                json={
                    "model": self.nemotron_model,
                    "messages": [
                        {"role": "system", "content": "You are a sentiment analysis expert."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 50
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                sentiment_text = result['choices'][0]['message']['content']
                try:
                    sentiment_data = json.loads(sentiment_text)
                    return {
                        'label': sentiment_data.get('label', 'neutral'),
                        'score': min(max(float(sentiment_data.get('score', 0.5)), 0.0), 1.0)
                    }
                except (json.JSONDecodeError, ValueError):
                    return {'label': 'neutral', 'score': 0.5}
            return {'label': 'neutral', 'score': 0.5}
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            return {'label': 'neutral', 'score': 0.5}

    async def _async_generate_content(self, prompt: str) -> str:
        """Wrapper for async Gemini API calls"""
        try:
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                prompt
            )
            return response.text if response and response.text else ""
        except Exception as e:
            print(f"Error generating content: {e}")
            return ""

    async def _generate_summary(self, text: str, max_words: int = 50) -> str:
        """Generate a concise summary of the text"""
        try:
            prompt = f"Summarize this text in {max_words} words or less: {text}"
            return await self._async_generate_content(prompt) or text[:100] + "..."
        except Exception as e:
            print(f"Error generating summary: {e}")
            return text[:100] + "..."

    async def _generate_context(self, post: Post) -> str:
        """Generate contextual information about the post"""
        try:
            prompt = f"""Provide relevant context for this post, considering the author's role and the content:
            Author: {post.author.name} ({post.author.title})
            Post: {post.content}
            Include potential implications for financial markets."""
            
            return await self._async_generate_content(prompt) or f"Post by {post.author.name} on {post.posted_at}"
        except Exception as e:
            print(f"Error generating context: {e}")
            return f"Post by {post.author.name} on {post.posted_at}"
