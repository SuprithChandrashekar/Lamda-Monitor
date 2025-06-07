#!/usr/bin/env python3
"""
Lambda Monitor - Startup Script
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_environment():
    """Check if environment is properly set up"""
    print("🔍 Checking environment...")
    
    # Check for .env file
    env_file = project_root / ".env"
    if not env_file.exists():
        print("⚠️  Warning: .env file not found. Creating template...")
        create_env_template()
    
    # Check if database exists
    from src.config import settings
    db_path = Path(settings.DATABASE_URL.replace('sqlite:///', ''))
    
    if not db_path.exists():
        print("📦 Database not found. Initializing...")
        init_database()
    else:
        print("✅ Database found")

def create_env_template():
    """Create a template .env file"""
    env_template = """# Lambda Monitor Configuration

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=sqlite:///./lambda_monitor.db

# Social Media API Keys (Add your own keys)
SCRAPE_CREATORS_API_KEY=your_scrape_creators_api_key_here
TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_SECRET=your_twitter_api_secret_here
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret_here
TRUTH_SOCIAL_API_KEY=your_truth_social_api_key_here

# AI Model API Keys (Add your own keys)
NEMOTRON_API_KEY=your_nemotron_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Notifications
NOTIFICATION_ENABLED=true
NOTIFICATION_DELAY=30
"""
    
    with open(".env", "w") as f:
        f.write(env_template)
    
    print("📝 Created .env template file. Please add your API keys!")

def init_database():
    """Initialize the database"""
    try:
        from init_db import main as init_main
        init_main()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("You can try running: python init_db.py")

def start_application():
    """Start the FastAPI application"""
    print("🚀 Starting Lambda Monitor...")
    
    try:
        import uvicorn
        from src.main import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Lambda Monitor stopped")
    except Exception as e:
        print(f"❌ Failed to start application: {e}")

def main():
    """Main startup function"""
    print("=" * 50)
    print("🔥 LAMBDA MONITOR - Market Intelligence System")
    print("=" * 50)
    
    check_environment()
    
    print("\n🌐 Starting web server...")
    print("📊 Dashboard will be available at: http://localhost:8000")
    print("🔌 API endpoints available at: http://localhost:8000/api/")
    print("\n⚡ Press Ctrl+C to stop the server")
    print("-" * 50)
    
    start_application()

if __name__ == "__main__":
    main()