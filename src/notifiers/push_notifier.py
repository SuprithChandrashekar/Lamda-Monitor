import json
from typing import Dict, Any
import httpx
from .base import BaseNotifier
from ..database.models import Alert, Post
from ..config import settings

class PushNotifier(BaseNotifier):
    def __init__(self):
        self.client = httpx.AsyncClient()
        self.notification_delay = settings.NOTIFICATION_DELAY
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send push notification to configured endpoints"""
        try:
            message = await self.format_message(alert)
            
            # This would be replaced with actual push notification service
            # Example using a generic webhook
            response = await self.client.post(
                "https://api.pushnotification.com/v1/send",
                json={
                    "message": message,
                    "priority": "high" if alert.alert_type == "high_priority" else "normal",
                    "data": {
                        "alert_id": alert.id,
                        "post_id": alert.post_id,
                        "type": alert.alert_type
                    }
                }
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send notification: {e}")
            return False
    
    async def format_message(self, alert: Alert) -> str:
        """Format alert into a user-friendly notification message"""
        post = alert.post
        author = post.author
        
        if alert.alert_type == "high_priority":
            return f"🚨 High Priority: New post from {author.name}\n{post.content[:100]}..."
        elif alert.alert_type == "market_impact":
            return f"📈 Market Alert: {author.name} posted about market conditions\n{post.content[:100]}..."
        else:
            return f"ℹ️ {author.name} has posted: {post.content[:100]}..."
