from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
import json
from fastapi.background import BackgroundTasks
import asyncio
import datetime
from contextlib import asynccontextmanager

from .database.connection import get_db, init_db
from .database.mcp_client import create_mcp_client
from .database.models import MonitoredFigure, Post, Alert, Watchlist
from .fetchers.twitter import TwitterFetcher
from .analyzers.ai_analyzer import AIAnalyzer
from .notifiers.push_notifier import PushNotifier
from .frontend import routes as frontend_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize MCP client and database
    await init_db()
    client = await create_mcp_client()
    yield
    # Cleanup
    await client.close()

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
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                await self.disconnect(connection)

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"status": "ok", "service": "Lambda Monitor"}

@app.get("/figures", response_model=List[dict])
async def get_monitored_figures(db: Session = Depends(get_db)):
    """Get all monitored figures"""
    return db.query(MonitoredFigure).all()

@app.get("/posts/latest", response_model=List[dict])
async def get_latest_posts(
    limit: int = 10,
    min_impact_score: float = None,
    db: Session = Depends(get_db)
):
    """Get latest posts with optional impact score filter"""
    query = db.query(Post).order_by(Post.posted_at.desc())
    
    if min_impact_score is not None:
        query = query.filter(Post.impact_score >= min_impact_score)
    
    return query.limit(limit).all()

@app.get("/alerts", response_model=List[dict])
async def get_alerts(
    limit: int = 10,
    alert_type: str = None,
    db: Session = Depends(get_db)
):
    """Get recent alerts with optional type filter"""
    query = db.query(Alert).order_by(Alert.sent_at.desc())
    
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    
    return query.limit(limit).all()

@app.get("/watchlists", response_model=List[dict])
async def get_watchlists(db: Session = Depends(get_db)):
    """Get all watchlists"""
    return db.query(Watchlist).all()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back received data (for testing)
            await websocket.send_text(f"Message received: {data}")
    except:
        manager.disconnect(websocket)

# Utility function to broadcast updates
async def broadcast_update(update_type: str, data: dict):
    await manager.broadcast(
        json.dumps({
            "type": update_type,
            "data": data
        })
    )

async def fetch_and_analyze_posts():
    """Background task to fetch and analyze new posts"""
    while True:
        try:
            db = next(get_db())
            figures = db.query(MonitoredFigure).all()
            
            for figure in figures:
                # Fetch new posts
                posts = await twitter_fetcher.fetch_posts(
                    figure.platform_id,
                    since=datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
                )
                
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
                        
                        # Analyze post
                        analysis = await ai_analyzer.analyze_post(post)
                        post.impact_score = analysis['market_impact_score']
                        
                        # Create alert if high impact
                        if analysis['market_impact_score'] >= 0.7:
                            alert = Alert(
                                post_id=post.id,
                                alert_type='high_priority',
                                message=f"High impact post from {figure.name}"
                            )
                            db.add(alert)
                            db.commit()
                            
                            # Send notification
                            await notifier.send_notification(alert)
                            
                            # Broadcast update
                            await broadcast_update('new_alert', {
                                'id': alert.id,
                                'message': alert.message
                            })
                        
                        # Broadcast new post
                        await broadcast_update('new_post', {
                            'id': post.id,
                            'content': post.content,
                            'author': figure.name
                        })
            
            db.close()
        except Exception as e:
            print(f"Error in background task: {e}")
        
        # Wait before next iteration
        await asyncio.sleep(60)  # Check every minute

@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup"""
    asyncio.create_task(fetch_and_analyze_posts())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
