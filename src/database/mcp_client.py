from mcp_wrapper import MCPClient
from typing import Any, Dict, AsyncGenerator
import asyncio
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..config import settings

class DatabaseClient:
    def __init__(self):
        self.engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False},
            echo=True
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> Any:
        """Execute a SQL query and return results"""
        session = self.SessionLocal()
        try:
            result = session.execute(query, params or {})
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

async def create_mcp_client() -> MCPClient:
    """Create and configure the MCP client for SQLite database connections."""
    client = await MCPClient.create(
        server_name="sqlite",
        settings={
            "database": settings.DATABASE_URL.replace("sqlite:///", ""),
            "pragmas": settings.SQLITE_PRAGMAS
        }
    )
    return client

async def get_db() -> AsyncGenerator[MCPClient, None]:
    """Get a database connection using MCP."""
    client = await create_mcp_client()
    try:
        yield client
    finally:
        await client.close()
