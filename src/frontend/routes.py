# src/frontend/routes.py
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Dict
from ..database.connection import get_db
from ..database.models import Post, MonitoredFigure, Alert

router = APIRouter()
templates = Jinja2Templates(directory="src/frontend/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard view"""
    try:
        # Get latest posts with authors
        latest_posts = (
            db.query(Post)
            .join(MonitoredFigure)
            .order_by(Post.posted_at.desc())
            .limit(10)
            .all()
        )
        
        # Get recent alerts
        recent_alerts = (
            db.query(Alert)
            .order_by(Alert.sent_at.desc())
            .limit(5)
            .all()
        )
        
        # Get monitored figures
        figures = db.query(MonitoredFigure).all()
        
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "latest_posts": latest_posts,
                "recent_alerts": recent_alerts,
                "monitored_figures": figures,
                "total_figures": len(figures),
                "total_posts": db.query(Post).count(),
                "total_alerts": db.query(Alert).count()
            }
        )
    except Exception as e:
        print(f"Dashboard error: {e}")
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "latest_posts": [],
                "recent_alerts": [],
                "monitored_figures": [],
                "total_figures": 0,
                "total_posts": 0,
                "total_alerts": 0,
                "error": str(e)
            }
        )

@router.get("/posts", response_class=HTMLResponse)
async def posts_view(request: Request, db: Session = Depends(get_db)):
    """Posts listing and search view"""
    try:
        posts = (
            db.query(Post)
            .join(MonitoredFigure)
            .order_by(Post.posted_at.desc())
            .limit(50)
            .all()
        )
        
        return templates.TemplateResponse(
            "posts.html",
            {"request": request, "posts": posts}
        )
    except Exception as e:
        return templates.Templ