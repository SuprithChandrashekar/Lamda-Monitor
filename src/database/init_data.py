import os
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.config import settings
from src.database.models import Base, MonitoredFigure, Watchlist

def init_database():
    """Initialize the database and create all tables"""
    # Create database directory if it doesn't exist
    db_path = Path(settings.DATABASE_URL.replace('sqlite:///', '')).absolute()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create engine and create all tables
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def init_sample_data():
    """Initialize the database with sample data"""
    db = init_database()
    
    # Create sample monitored figures
    political_figures = [
        {
            "name": "Joe Biden",
            "title": "President of the United States",
            "platform": "twitter",
            "platform_id": "POTUS",
            "category": "political"
        },
        {
            "name": "Rishi Sunak",
            "title": "Prime Minister of the UK",
            "platform": "twitter",
            "platform_id": "RishiSunak",
            "category": "political"
        }
    ]
    
    industry_leaders = [
        {
            "name": "Elon Musk",
            "title": "CEO of Tesla and X",
            "platform": "twitter",
            "platform_id": "elonmusk",
            "category": "industry_leader"
        },
        {
            "name": "Sam Altman",
            "title": "CEO of OpenAI",
            "platform": "twitter",
            "platform_id": "sama",
            "category": "industry_leader"
        }
    ]
    
    # Add figures to database
    for figure_data in political_figures + industry_leaders:
        figure = MonitoredFigure(**figure_data)
        db.add(figure)
    
    # Create sample watchlists
    watchlists = [
        {
            "name": "Political Leaders",
            "description": "Major political figures from key global economies",
            "keywords": '["policy", "economy", "regulation"]'
        },
        {
            "name": "Tech Leaders",
            "description": "CEOs and leaders in technology sector",
            "keywords": '["AI", "technology", "innovation"]'
        }
    ]
    
    for watchlist_data in watchlists:
        watchlist = Watchlist(**watchlist_data)
        db.add(watchlist)
    
    db.commit()
    db.close()

if __name__ == "__main__":
    init_sample_data()
