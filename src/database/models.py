from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base

# Create the declarative base
Base = declarative_base()

# Make sure the base class is available at the module level
__all__ = ['Base', 'MonitoredFigure', 'Post', 'PostAnalysis', 'Alert', 'Watchlist']

# Association tables
figure_watchlist = Table(
    'figure_watchlist',
    Base.metadata,
    Column('figure_id', Integer, ForeignKey('monitored_figures.id')),
    Column('watchlist_id', Integer, ForeignKey('watchlists.id'))
)

class MonitoredFigure(Base):
    __tablename__ = 'monitored_figures'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    title = Column(String)
    platform = Column(String, nullable=False)  # twitter, truth_social, etc.
    platform_id = Column(String, nullable=False)
    category = Column(String)  # political, industry_leader
    created_at = Column(DateTime, default=datetime.utcnow)
    
    posts = relationship("Post", back_populates="author")
    watchlists = relationship("Watchlist", secondary=figure_watchlist, back_populates="figures")

class Post(Base):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    platform_post_id = Column(String, nullable=False)
    content = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey('monitored_figures.id'))
    posted_at = Column(DateTime, nullable=False)
    captured_at = Column(DateTime, default=datetime.utcnow)
    impact_score = Column(Float)
    market_relevance = Column(Float)
    
    author = relationship("MonitoredFigure", back_populates="posts")
    analysis = relationship("PostAnalysis", back_populates="post", uselist=False)
    alerts = relationship("Alert", back_populates="post")

class PostAnalysis(Base):
    __tablename__ = 'post_analyses'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    summary = Column(String)
    context = Column(String)
    market_impact_analysis = Column(String)
    tags = Column(String)  # JSON string of tags
    created_at = Column(DateTime, default=datetime.utcnow)
    
    post = relationship("Post", back_populates="analysis")

class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    alert_type = Column(String, nullable=False)  # high_priority, market_impact, etc.
    message = Column(String, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    post = relationship("Post", back_populates="alerts")

class Watchlist(Base):
    __tablename__ = 'watchlists'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    keywords = Column(String)  # JSON string of keywords
    created_at = Column(DateTime, default=datetime.utcnow)
    
    figures = relationship("MonitoredFigure", secondary=figure_watchlist, back_populates="watchlists")
