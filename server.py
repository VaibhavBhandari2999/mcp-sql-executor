import json
from typing import Any, List

from mcp.server.fastmcp import FastMCP
from db import query, get_table_schema

mcp = FastMCP("mcp-mysql-py")


@mcp.tool()
def sql_query(sql: str, params: List[Any] | None = None) -> str:
    """
    Execute a read-only SQL query with placeholders.
    Returns JSON string (list[dict]).
    """
    if not sql.strip().lower().startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")

    rows = query(sql, params or [])
    return json.dumps(rows, default=str)


@mcp.tool()
def get_schema(table_name: str = "parts") -> str:
    """
    Return a readable description of a table schema.
    """
    return get_table_schema(table_name)


if __name__ == "__main__":
    mcp.run()
