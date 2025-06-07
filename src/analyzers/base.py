from abc import ABC, abstractmethod
from typing import Dict, Any, List
from ..database.models import Post

class BaseAnalyzer(ABC):
    """Base class for content analyzers"""
    
    @abstractmethod
    async def analyze_post(self, post: Post) -> Dict[str, Any]:
        """Analyze a post and return analysis results"""
        pass
    
    @abstractmethod
    async def get_market_impact_score(self, post: Post) -> float:
        """Calculate market impact score based on post content and author"""
        pass
    
    @abstractmethod
    async def extract_tags(self, post: Post) -> List[str]:
        """Extract relevant tags from post content"""
        pass