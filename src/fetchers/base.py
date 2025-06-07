from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

class SocialMediaFetcher(ABC):
    """Base class for all social media fetchers"""
    
    def __init__(self, api_key: str, api_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the social media platform"""
        pass
    
    @abstractmethod
    async def fetch_posts(self, user_id: str, since: datetime = None) -> List[Dict[str, Any]]:
        """Fetch posts from a specific user"""
        pass
    
    @abstractmethod
    async def get_user_info(self, username: str) -> Dict[str, Any]:
        """Get user information from username"""
        pass
