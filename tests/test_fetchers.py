import pytest
from unittest.mock import patch, MagicMock
import httpx
from datetime import datetime
from src.fetchers.twitter import TwitterFetcher

@pytest.fixture
def mock_tweets_response():
    return {
        "tweets": [
            {
                "id": "1234567890",
                "text": "Test tweet content about monetary policy",
                "created_at": "2025-06-07T10:00:00Z",
                "likes": 100,
                "retweets": 50,
                "replies": 25
            }
        ]
    }

@pytest.mark.asyncio
async def test_twitter_fetcher_api(mock_tweets_response):
    """Test Twitter API fetching functionality using ScrapeCreators"""
    with patch.object(httpx.AsyncClient, 'get') as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: mock_tweets_response
        )
        
        fetcher = TwitterFetcher()
        posts = await fetcher.fetch_posts("federalreserve")
        
        assert len(posts) > 0
        assert posts[0]['content'] == mock_tweets_response["tweets"][0]["text"]
        assert posts[0]['metrics']['likes'] == 100

@pytest.mark.asyncio
async def test_twitter_rate_limit_handling(mock_tweets_response):
    """Test rate limit handling (FR012)"""
    with patch.object(httpx.AsyncClient, 'get') as mock_get:
        # First call returns 429 (rate limit)
        mock_get.side_effect = [
            MagicMock(status_code=429, text="Rate limit exceeded"),
            # Second call succeeds
            MagicMock(
                status_code=200,
                json=lambda: mock_tweets_response
            )
        ]
        
        fetcher = TwitterFetcher()
        posts = await fetcher.fetch_posts("federalreserve")
        
        assert len(posts) > 0
        assert posts[0]['content'] == mock_tweets_response["tweets"][0]["text"]

@pytest.mark.asyncio
async def test_selenium_fallback():
    """Test browser automation fallback (FR013)"""
    with patch.object(httpx.AsyncClient, 'get') as mock_get:
        # API fails completely
        mock_get.return_value = MagicMock(status_code=500)
        
        with patch('selenium.webdriver.Chrome') as mock_driver:
            mock_element = MagicMock()
            mock_element.find_element.return_value.text = "Test tweet content"
            mock_element.find_element.return_value.get_attribute.return_value = "2025-06-07T10:00:00Z"
            mock_driver.return_value.find_elements.return_value = [mock_element]
            
            fetcher = TwitterFetcher()
            posts = await fetcher.fetch_posts("federalreserve", use_selenium=True)
            
            assert len(posts) > 0
            assert "Test tweet content" in posts[0]['content']
