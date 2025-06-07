#!/usr/bin/env python3
"""
Initialize the Lambda Monitor database with tables and sample data
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.database.connection import get_engine
from src.database.models import Base, MonitoredFigure, Watchlist
from sqlalchemy.orm import sessionmaker

def init_database():
    """Initialize the database and create all tables"""
    print("Initializing database...")
    
    # Create database directory if it doesn't exist
    from src.config import settings
    db_path = Path(settings.DATABASE_URL.replace('sqlite:///', '')).absolute()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create engine and create all tables
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    
    print(f"Database created at: {db_path}")
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def add_sample_data():
    """Add sample monitored figures and watchlists"""
    print("Adding sample data...")
    
    db = init_database()
    
    try:
        # Check if data already exists
        existing_figures = db.query(MonitoredFigure).count()
        if existing_figures > 0:
            print("Sample data already exists. Skipping...")
            return
        
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
                "name": "Donald Trump",
                "title": "Former President",
                "platform": "twitter",
                "platform_id": "realDonaldTrump",
                "category": "political"
            },
            {
                "name": "Jerome Powell",
                "title": "Federal Reserve Chair",
                "platform": "twitter",
                "platform_id": "federalreserve",
                "category": "financial"
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
            },
            {
                "name": "Satya Nadella",
                "title": "CEO of Microsoft",
                "platform": "twitter",
                "platform_id": "satyanadella",
                "category": "industry_leader"
            }
        ]
        
        # Add figures to database
        all_figures = []
        for figure_data in political_figures + industry_leaders:
            figure = MonitoredFigure(**figure_data)
            db.add(figure)
            all_figures.append(figure)
        
        # Create sample watchlists
        watchlists_data = [
            {
                "name": "Political Leaders",
                "description": "Major political figures from key global economies",
                "keywords": '["policy", "economy", "regulation", "government"]'
            },
            {
                "name": "Tech Leaders",
                "description": "CEOs and leaders in technology sector",
                "keywords": '["AI", "technology", "innovation", "startup"]'
            },
            {
                "name": "Financial Leaders",
                "description": "Central bank officials and financial regulators",
                "keywords": '["interest rate", "inflation", "monetary policy", "banking"]'
            }
        ]
        
        for watchlist_data in watchlists_data:
            watchlist = Watchlist(**watchlist_data)
            db.add(watchlist)
        
        db.commit()
        print(f"Added {len(all_figures)} monitored figures and {len(watchlists_data)} watchlists")
        
    except Exception as e:
        print(f"Error adding sample data: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main initialization function"""
    print("=== Lambda Monitor Database Initialization ===")
    
    try:
        add_sample_data()
        print("\n✅ Database initialization completed successfully!")
        print("\nYou can now run the application with:")
        print("python -m src.main")
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())