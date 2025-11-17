import os
import json
import asyncio
from typing import Any, Dict
from dotenv import load_dotenv

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

load_dotenv()

PYTHON_BIN = os.environ["PYTHON_BIN"]
MCP_CWD    = os.environ["MCP_CWD"]
SERVER_CMD = [PYTHON_BIN, "server.py"]


async def _call_mcp_async(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Generic async caller for ANY MCP tool (sql_query, get_schema, etc).
    Returns a text string (JSON or plain text).
    """
    server = StdioServerParameters(
        command=SERVER_CMD[0],
        args=SERVER_CMD[1:],
        cwd=MCP_CWD,
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)

            blocks = result.content or []
            for b in blocks:
                
                if getattr(b, "type", None) == "text" or (
                    isinstance(b, dict) and b.get("type") == "text"
                ):
                    return b.text if hasattr(b, "text") else b.get("text", "")

            #dump everything as JSON text as a fallback
            return json.dumps(
                [getattr(b, "__dict__", b) for b in blocks],
                indent=2,
            )


def call_mcp(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Synchronous wrapper for all MCP tools.
    """
    return asyncio.run(_call_mcp_async(tool_name, arguments))


def call_sql_via_mcp(sql: str, params: list[Any] | None = None) -> str:
    """
    Sync wrapper specifically for the sql_query tool.
    """
    return call_mcp("sql_query", {"sql": sql, "params": params or []})
