import pytest
from unittest.mock import patch
from src.analyzers.ai_analyzer import AIAnalyzer
from src.database.models import Post, MonitoredFigure

@pytest.mark.asyncio
async def test_market_impact_analysis(mock_nemotron_response, test_db):
    """Test market impact score calculation (FR003)"""
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_nemotron_response
        
        analyzer = AIAnalyzer()
        author = MonitoredFigure(name="Jerome Powell", title="Federal Reserve Chairman")
        post = Post(
            content="We are increasing interest rates by 25 basis points.",
            author=author
        )
        
        result = await analyzer.analyze_post(post)
        
        assert 'market_impact_score' in result
        assert isinstance(result['market_impact_score'], float)
        assert 0 <= result['market_impact_score'] <= 1

@pytest.mark.asyncio
async def test_sentiment_analysis(mock_nemotron_response):
    """Test sentiment analysis functionality (FR005)"""
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_nemotron_response
        
        analyzer = AIAnalyzer()
        sentiment = await analyzer._analyze_sentiment("Positive market outlook")
        
        assert 'label' in sentiment
        assert 'score' in sentiment
        assert sentiment['label'] in ['positive', 'negative', 'neutral']

@pytest.mark.asyncio
async def test_context_generation(mock_gemini_response):
    """Test contextual analysis (FR005)"""
    with patch('google.generativeai.GenerativeModel.generate_content') as mock_generate:
        mock_generate.return_value = mock_gemini_response
        
        analyzer = AIAnalyzer()
        author = MonitoredFigure(name="Jerome Powell", title="Federal Reserve Chairman")
        post = Post(
            content="Important policy announcement coming.",
            author=author
        )
        
        context = await analyzer._generate_context(post)
        assert len(context) > 0
        assert "market" in context.lower()
