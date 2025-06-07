from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from ..config import settings
from .mcp_client import create_mcp_client

async def get_engine():
    client = await create_mcp_client()
    return create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        future=True
    )

async def get_db():
    engine = await get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        await engine.dispose()

async def init_db():
    engine = await get_engine()
    Base = declarative_base()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
