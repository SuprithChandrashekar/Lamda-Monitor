# lamda_monitor/mcp_wrapper.py
import asyncio, sys
from contextlib import AsyncExitStack
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    """
    Drop-in replacement for the tutorial’s MCPClient – only the methods
    Lamda Monitor actually calls are implemented.
    """
    def __init__(self):
        self._stack        = AsyncExitStack()
        self._session: Optional[ClientSession] = None

    # ---------- connection ----------
    async def connect(self, server_script: str):
        cmd = "python" if server_script.endswith(".py") else "node"
        params = StdioServerParameters(command=cmd, args=[server_script])
        reader, writer = await self._stack.enter_async_context(stdio_client(params))
        self._session  = await self._stack.enter_async_context(ClientSession(reader, writer))
        await self._session.initialize()                               # handshake
        tools = (await self._session.list_tools()).tools
        print("Connected to MCP server with tools:", [t.name for t in tools])

    # ---------- pass-through helpers ----------
    async def list_tools(self):
        return await self._session.list_tools()

    async def call_tool(self, name: str, args: dict | None = None):
        return await self._session.call_tool(name, args or {})

    # ---------- graceful shutdown ----------
    async def close(self):
        await self._stack.aclose()
