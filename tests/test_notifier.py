import pytest
from unittest.mock import patch
from datetime import datetime, timezone
from src.notifiers.push_notifier import PushNotifier
from src.database.models import Alert, Post, MonitoredFigure

@pytest.mark.asyncio
async def test_high_priority_notification():
    """Test notification for high-impact posts (FR006)"""
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.status_code = 200
        
        notifier = PushNotifier()
        author = MonitoredFigure(
            id=1,
            name="Elon Musk",
            title="CEO of Tesla",
            platform="twitter",
            platform_id="elonmusk",
            category="industry_leader"
        )
        post = Post(
            id=1,
            content="Tesla stock buyback announced",
            author=author,
            impact_score=0.9,
            platform_post_id="123456",
            posted_at=datetime.now(timezone.utc)
        )
        alert = Alert(
            id=1,
            post=post,
            post_id=1,
            alert_type="high_priority",
            message="High impact post detected",
            sent_at=datetime.now(timezone.utc)
        )
        
        success = await notifier.send_notification(alert)
        assert success
        
        # Verify notification was sent with correct format
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]
        assert "message" in call_args["json"]
        assert "Tesla stock buyback" in call_args["json"]["message"]
        assert call_args["json"]["priority"] == "high"

@pytest.mark.asyncio
async def test_notification_timing():
    """Test time-critical updates (FR007)"""
    start_time = datetime.now(timezone.utc)
    
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.status_code = 200
        
        notifier = PushNotifier()
        author = MonitoredFigure(
            id=2,
            name="Tim Cook",
            title="CEO of Apple",
            platform="twitter",
            platform_id="tim_cook",
            category="industry_leader"
        )
        post = Post(
            id=2,
            content="Major product announcement",
            author=author,
            impact_score=0.8,
            platform_post_id="789012",
            posted_at=datetime.now(timezone.utc)
        )
        alert = Alert(
            id=2,
            post=post,
            post_id=2,
            alert_type="high_priority",
            message="Important announcement",
            sent_at=datetime.now(timezone.utc)
        )
        
        await notifier.send_notification(alert)
        end_time = datetime.now(timezone.utc)
        
        # Verify notification was sent within required time frame (FR007)
        notification_time = end_time - start_time
        assert notification_time.total_seconds() < 5  # Should be sent within 5 seconds

@pytest.mark.asyncio
async def test_failed_notification_handling():
    """Test handling of failed notifications"""
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.status_code = 500
        
        notifier = PushNotifier()
        author = MonitoredFigure(
            id=3,
            name="Test User",
            title="Test Title",
            platform="twitter",
            platform_id="testuser",
            category="other"
        )
        post = Post(
            id=3,
            content="Test content",
            author=author,
            impact_score=0.5,
            platform_post_id="345678",
            posted_at=datetime.now(timezone.utc)
        )
        alert = Alert(
            id=3,
            post=post,
            post_id=3,
            alert_type="normal",
            message="Test alert",
            sent_at=datetime.now(timezone.utc)
        )
        
        success = await notifier.send_notification(alert)
        assert not success  # Should return False for failed notifications
