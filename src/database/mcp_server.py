from typing import Any, Dict, List
import os
import sys
from pathlib import Path
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
import sqlite3
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.config import settings

# Initialize FastMCP server
mcp = FastMCP(
    name="sqlite",
    transport="stdio",
    settings={
        "database": settings.DATABASE_URL.replace("sqlite:///", ""),
        "pragmas": settings.SQLITE_PRAGMAS
    }
)

def get_connection():
    """Get a SQLite database connection with proper configuration."""
    conn = sqlite3.connect(settings.DATABASE_URL.replace("sqlite:///", ""))
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    """Initialize the SQLite database connection."""
    conn = get_connection()
    try:
        # Set pragmas
        for pragma, value in settings.SQLITE_PRAGMAS.items():
            conn.execute(f"PRAGMA {pragma}={value}")
        conn.commit()
    finally:
        conn.close()

@mcp.tool("query")
async def execute_query(sql: str) -> Dict[str, Any]:
    """Execute a SQL query against the SQLite database."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        results = [dict(row) for row in cursor.fetchall()]
        conn.commit()
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

if __name__ == "__main__":
    setup_database()
    mcp.run()
