import os
import pytest
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base
from src.config import settings

# Use SQLite in-memory database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def test_db():
    """Create a fresh database for each test"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)

@pytest.fixture
def mock_twitter_api():
    """Mock Twitter API responses"""
    return {
        "tweets": [
            {
                "id": "123",
                "text": "We are increasing interest rates by 25 basis points.",
                "created_at": "2025-06-07T12:00:00Z",
                "author": {
                    "id": "456",
                    "name": "Jerome Powell",
                    "username": "federalreserve"
                }
            }
        ]
    }

@pytest.fixture
def mock_nemotron_response():
    """Mock Nemotron API responses"""
    return {
        "choices": [{
            "message": {
                "content": '{"label": "negative", "score": 0.8}'
            }
        }]
    }

@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API responses"""
    mock_response = MagicMock()
    mock_response.text = "This is a summary of market implications and potential impact on financial markets."
    return mock_response
