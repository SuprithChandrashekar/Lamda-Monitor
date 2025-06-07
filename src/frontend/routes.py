from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Dict
from ..database.connection import get_db
from ..database.models import Post, MonitoredFigure, Alert

router = APIRouter()
templates = Jinja2Templates(directory="src/frontend/templates")

@router.get("/")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard view"""
    latest_posts = db.query(Post).order_by(Post.posted_at.desc()).limit(10).all()
    recent_alerts = db.query(Alert).order_by(Alert.sent_at.desc()).limit(5).all()
    figures = db.query(MonitoredFigure).all()
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "latest_posts": latest_posts,
            "recent_alerts": recent_alerts,
            "monitored_figures": figures
        }
    )

@router.get("/posts")
async def posts_view(request: Request, db: Session = Depends(get_db)):
    """Posts listing and search view"""
    posts = db.query(Post).order_by(Post.posted_at.desc()).limit(50).all()
    return templates.TemplateResponse(
        "posts.html",
        {"request": request, "posts": posts}
    )

@router.get("/alerts")
async def alerts_view(request: Request, db: Session = Depends(get_db)):
    """Alerts listing view"""
    alerts = db.query(Alert).order_by(Alert.sent_at.desc()).limit(50).all()
    return templates.TemplateResponse(
        "alerts.html",
        {"request": request, "alerts": alerts}
    )

@router.get("/figures")
async def figures_view(request: Request, db: Session = Depends(get_db)):
    """Monitored figures management view"""
    figures = db.query(MonitoredFigure).all()
    return templates.TemplateResponse(
        "figures.html",
        {"request": request, "figures": figures}
    )
