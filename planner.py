import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

from mcp_client import call_mcp

load_dotenv()

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

PROMPT_TEMPLATE = """You translate a natural-language question into a safe SQL plan for MySQL.

You MUST:
- Return STRICT JSON with fields:
  - sql: string with %s placeholders
  - params: array (positional parameters)
- Only use tables/columns that exist in the schema below. Use SELECT only (read-only).

Here is the current schema you can rely on:
{schema}
"""

_SCHEMA_CACHE: Dict[str, str] = {}
_SCHEMA_BLOB: str | None = None
TABLES = ["parts"]


def _get_all_schemas() -> str:
    """
    Fetch and cache schemas for mentioned tables
    """
    
    global _SCHEMA_BLOB
    if _SCHEMA_BLOB is not None:
        return _SCHEMA_BLOB

    lines: list[str] = []
    for table in TABLES:
        if table not in _SCHEMA_CACHE:
            schema = call_mcp("get_schema", {"table_name": table})
            if not schema:
                schema = f"(No schema returned for {table}.)"
            _SCHEMA_CACHE[table] = schema

        lines.append(_SCHEMA_CACHE[table])
        lines.append("") #Add blank line between tables

    _SCHEMA_BLOB = "\n".join(lines)
    return _SCHEMA_BLOB


def plan_sql(user_question: str) -> Dict[str, Any]:

    schema_text = _get_all_schemas()
    system_prompt = PROMPT_TEMPLATE.format(schema=schema_text)

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Question: {user_question}\nReturn ONLY JSON (no prose).",
            },
        ],
        temperature=0,
    )

    content = resp.choices[0].message.content.strip()
    start = content.find("{")
    end = content.rfind("}")
    parsed = json.loads(content[start : end + 1])

    return parsed
