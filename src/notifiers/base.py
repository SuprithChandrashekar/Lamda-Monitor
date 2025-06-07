from abc import ABC, abstractmethod
from typing import Dict, Any
from ..database.models import Alert, Post

class BaseNotifier(ABC):
    """Base class for notification systems"""
    
    @abstractmethod
    async def send_notification(self, alert: Alert) -> bool:
        """Send a notification based on an alert"""
        pass
    
    @abstractmethod
    async def format_message(self, alert: Alert) -> str:
        """Format the alert into a notification message"""
        pass
