# src/database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from ..config import settings
import asyncio

# Create engine with proper SQLite configuration
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 20
    },
    pool_pre_ping=True,
    echo=False  # Set to True for debugging SQL queries
)

# Provide engine accessor for modules that need the raw engine
def get_engine():
    """Return the SQLAlchemy engine instance."""
    return engine

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

def get_db():
    """Get database session - synchronous version"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_db_async():
    """Get database session - asynchronous version"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    from .models import Base
    Base.metadata.create_all(bind=engine)

def get_session() -> Session:
    """Get a database session directly"""
    return SessionLocal()
