import pytest
from datetime import datetime, timedelta
from src.database.models import Post, MonitoredFigure, Watchlist, Alert
from sqlalchemy import desc

def test_post_logging(test_db):
    """Test real-time post logging (FR004)"""
    # Create test data
    author = MonitoredFigure(
        name="Jerome Powell",
        title="Federal Reserve Chairman",
        platform="twitter",
        platform_id="federalreserve"
    )
    test_db.add(author)
    
    post = Post(
        platform_post_id="123",
        content="Policy announcement",
        author=author,
        posted_at=datetime.utcnow(),
        impact_score=0.8
    )
    test_db.add(post)
    test_db.commit()
    
    # Verify post was logged
    saved_post = test_db.query(Post).first()
    assert saved_post is not None
    assert saved_post.content == "Policy announcement"
    assert saved_post.author.name == "Jerome Powell"

def test_watchlist_filtering(test_db):
    """Test custom watchlists and filters (FR008)"""
    # Create test watchlist
    watchlist = Watchlist(
        name="Economic Policy",
        keywords='["interest rate", "inflation", "monetary policy"]'
    )
    test_db.add(watchlist)
    
    # Add figures to watchlist
    powell = MonitoredFigure(
        name="Jerome Powell",
        title="Federal Reserve Chairman",
        platform="twitter",
        platform_id="federalreserve"
    )
    watchlist.figures.append(powell)
    test_db.commit()
    
    # Verify watchlist filtering
    saved_watchlist = test_db.query(Watchlist).first()
    assert saved_watchlist is not None
    assert len(saved_watchlist.figures) == 1
    assert "interest rate" in saved_watchlist.keywords

def test_historical_search(test_db):
    """Test historical search functionality (FR010)"""
    # Create test data
    author = MonitoredFigure(name="Elon Musk", title="CEO of Tesla")
    test_db.add(author)
    
    # Add posts from different dates
    dates = [
        datetime.utcnow() - timedelta(days=i)
        for i in range(5)
    ]
    
    for i, date in enumerate(dates):
        post = Post(
            platform_post_id=str(i),
            content=f"Test post {i}",
            author=author,
            posted_at=date,
            impact_score=0.5 + i * 0.1
        )
        test_db.add(post)
    
    test_db.commit()
    
    # Test date filtering
    recent_posts = test_db.query(Post).filter(
        Post.posted_at >= datetime.utcnow() - timedelta(days=3)
    ).all()
    assert len(recent_posts) == 3
    
    # Test impact score filtering
    high_impact_posts = test_db.query(Post).filter(
        Post.impact_score >= 0.7
    ).all()
    assert len(high_impact_posts) == 2
    
    # Test sorting
    sorted_posts = test_db.query(Post).order_by(
        desc(Post.impact_score)
    ).all()
    assert sorted_posts[0].impact_score > sorted_posts[-1].impact_score
