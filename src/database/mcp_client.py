from typing import Dict, Any
from mcp import MCPClient
from ..config import settings

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

async def get_db() -> MCPClient:
    """Get a database connection using MCP."""
    client = await create_mcp_client()
    try:
        yield client
    finally:
        await client.close()
