from pathlib import Path
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
      # Database Settings
    DATABASE_URL: str = "sqlite:///./lambda_monitor.db"
    SQLITE_PRAGMAS: dict = {
        "journal_mode": "wal",
        "cache_size": -64 * 1000,  # 64MB cache
        "foreign_keys": "ON",
        "synchronous": "NORMAL"
    }
    MCP_SERVER_PORT: int = 5000
    MCP_SERVER_HOST: str = "localhost"
    
    # Social Media API Keys
    SCRAPE_CREATORS_API_KEY: str = ""
    TWITTER_API_KEY: str = ""
    TWITTER_API_SECRET: str = ""
    TWITTER_BEARER_TOKEN: str = ""
    TWITTER_ACCESS_TOKEN: str = ""
    TWITTER_ACCESS_TOKEN_SECRET: str = ""
    TRUTH_SOCIAL_API_KEY: str = ""
    
    # AI Model Settings
    NEMOTRON_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
      # Notification Settings
    NOTIFICATION_ENABLED: bool = True
    NOTIFICATION_DELAY: int = 30  # seconds
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )

settings = Settings()
