# src/main.py
from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
import json
from fastapi.responses import HTMLResponse
import asyncio
import datetime
from contextlib import asynccontextmanager

from .database.connection import get_db, init_db, get_session
from .database.models import MonitoredFigure, Post, Alert, Watchlist
from .fetchers.twitter import TwitterFetcher
from .analyzers.ai_analyzer import AIAnalyzer
from .notifiers.push_notifier import PushNotifier
from .frontend import routes as frontend_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    print("🔧 Initializing database...")
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
    
    # Start background tasks
    print("🔄 Starting background tasks...")
    task = asyncio.create_task(fetch_and_analyze_posts())
    
    yield
    
    # Cleanup
    print("🧹 Cleaning up...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Lambda Monitor", 
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/frontend/static"), name="static")

# Include frontend routes
app.include_router(frontend_routes.router)

# Initialize components
twitter_fetcher = TwitterFetcher()
ai_analyzer = AIAnalyzer()
notifier = PushNotifier()

# Connection manager for WebSocket clients
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

@app.get("/")
async def root():
    """Root endpoint - redirect to dashboard"""
    return HTMLResponse("""
    <html>
        <head>
            <title>Lambda Monitor</title>
            <meta http-equiv="refresh" content="0; url=/dashboard">
        </head>
        <body>
            <p>Redirecting to <a href="/dashboard">dashboard</a>...</p>
        </body>
    </html>
    """)

@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    return {"status": "ok", "service": "Lambda Monitor"}

@app.get("/api/figures")
async def get_monitored_figures(db: Session = Depends(get_db)):
    """Get all monitored figures"""
    try:
        figures = db.query(MonitoredFigure).all()
        return [
            {
                "id": fig.id,
                "name": fig.name,
                "title": fig.title,
                "platform": fig.platform,
                "platform_id": fig.platform_id,
                "category": fig.category,
                "created_at": fig.created_at.isoformat() if fig.created_at else None
            }
            for fig in figures
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/posts/latest")
async def get_latest_posts(
    limit: int = 10,
    min_impact_score: float = None,
    db: Session = Depends(get_db)
):
    """Get latest posts with optional impact score filter"""
    try:
        query = db.query(Post).order_by(Post.posted_at.desc())
        
        if min_impact_score is not None:
            query = query.filter(Post.impact_score >= min_impact_score)
        
        posts = query.limit(limit).all()
        return [
            {
                "id": post.id,
                "content": post.content,
                "posted_at": post.posted_at.isoformat() if post.posted_at else None,
                "impact_score": post.impact_score,
                "author": {
                    "name": post.author.name,
                    "title": post.author.title
                } if post.author else None
            }
            for post in posts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts")
async def get_alerts(
    limit: int = 10,
    alert_type: str = None,
    db: Session = Depends(get_db)
):
    """Get recent alerts with optional type filter"""
    try:
        query = db.query(Alert).order_by(Alert.sent_at.desc())
        
        if alert_type:
            query = query.filter(Alert.alert_type == alert_type)
        
        alerts = query.limit(limit).all()
        return [
            {
                "id": alert.id,
                "alert_type": alert.alert_type,
                "message": alert.message,
                "sent_at": alert.sent_at.isoformat() if alert.sent_at else None,
                "post_id": alert.post_id
            }
            for alert in alerts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/watchlists")
async def get_watchlists(db: Session = Depends(get_db)):
    """Get all watchlists"""
    try:
        watchlists = db.query(Watchlist).all()
        return [
            {
                "id": wl.id,
                "name": wl.name,
                "description": wl.description,
                "keywords": wl.keywords,
                "created_at": wl.created_at.isoformat() if wl.created_at else None
            }
            for wl in watchlists
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back received data (for testing)
            await websocket.send_text(f"Message received: {data}")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)

# Utility function to broadcast updates
async def broadcast_update(update_type: str, data: dict):
    """Broadcast updates to all connected WebSocket clients"""
    message = json.dumps({
        "type": update_type,
        "data": data,
        "timestamp": datetime.datetime.utcnow().isoformat()
    })
    await manager.broadcast(message)

async def fetch_and_analyze_posts():
    """Background task to fetch and analyze new posts"""
    print("🔄 Background task started: fetching and analyzing posts")
    
    while True:
        try:
            # Get database session
            db = get_session()
            
            try:
                figures = db.query(MonitoredFigure).all()
                print(f"📊 Monitoring {len(figures)} figures")
                
                for figure in figures:
                    try:
                        # Fetch new posts
                        posts = await twitter_fetcher.fetch_posts(
                            figure.platform_id,
                            since=datetime.datetime.utcnow() - datetime.timedelta(hours=1)
                        )
                        
                        print(f"📥 Found {len(posts)} posts for {figure.name}")
                        
                        for post_data in posts:
                            # Check if post already exists
                            existing = db.query(Post).filter_by(
                                platform_post_id=post_data['platform_post_id']
                            ).first()
                            
                            if not existing:
                                # Create new post
                                post = Post(
                                    platform_post_id=post_data['platform_post_id'],
                                    content=post_data['content'],
                                    posted_at=post_data['posted_at'],
                                    author_id=figure.id
                                )
                                db.add(post)
                                db.commit()
                                db.refresh(post)
                                
                                print(f"💾 Saved new post from {figure.name}")
                                
                                # Analyze post
                                try:
                                    analysis = await ai_analyzer.analyze_post(post)
                                    post.impact_score = analysis['market_impact_score']
                                    db.commit()
                                    
                                    print(f"🧠 Analysis complete - Impact score: {analysis['market_impact_score']}")
                                    
                                    # Create alert if high impact
                                    if analysis['market_impact_score'] >= 0.7:
                                        alert = Alert(
                                            post_id=post.id,
                                            alert_type='high_priority',
                                            message=f"High impact post from {figure.name}: {post.content[:100]}..."
                                        )
                                        db.add(alert)
                                        db.commit()
                                        
                                        print(f"🚨 High impact alert created for {figure.name}")
                                        
                                        # Send notification
                                        try:
                                            await notifier.send_notification(alert)
                                        except Exception as e:
                                            print(f"⚠️ Notification failed: {e}")
                                        
                                        # Broadcast update
                                        await broadcast_update('new_alert', {
                                            'id': alert.id,
                                            'message': alert.message,
                                            'alert_type': alert.alert_type
                                        })
                                    
                                    # Broadcast new post
                                    await broadcast_update('new_post', {
                                        'id': post.id,
                                        'content': post.content,
                                        'author': figure.name,
                                        'impact_score': post.impact_score
                                    })
                                    
                                except Exception as e:
                                    print(f"⚠️ Analysis failed for post {post.id}: {e}")
                    
                    except Exception as e:
                        print(f"⚠️ Error processing {figure.name}: {e}")
                        continue
            
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Error in background task: {e}")
        
        # Wait before next iteration
        print("⏳ Waiting 5 minutes before next check...")
        await asyncio.sleep(300)  # Check every 5 minutes

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)