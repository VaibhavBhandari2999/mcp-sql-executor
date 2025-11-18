import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from mcp_client import call_mcp

load_dotenv()

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.getenv("OPENAI_BASE_URL"),
)

MODEL = os.getenv("OPENAI_MODEL")
DB_ENGINE = os.getenv("DB_TYPE").lower()

PROMPT_TEMPLATE = """You translate a natural-language question into a safe SQL plan for a {db_engine} database.

You MUST:
- Return STRICT JSON with fields:
  - sql: string with %s placeholders
  - params: array (positional parameters)
- Only use tables/columns that exist in the schema below. Use SELECT only (read-only).

You may use ONLY these tables:
{table_list}

Table relationships (for JOINs):
{relationship_list}

Here are the schemas for these tables:
{schema_blob}
"""

with open("schema_config.json") as f:
    cfg = json.load(f)

TABLES = cfg["tables"]
TABLE_RELATIONSHIPS = cfg.get("relationships", [])
_SCHEMA_CACHE: Dict[str, str] = {}
_SCHEMA_BLOB: str | None = None


def _get_all_schemas() -> str:

    global _SCHEMA_BLOB
    if _SCHEMA_BLOB is not None:
        return _SCHEMA_BLOB

    lines: list[str] = []
    for table in TABLES:
        if table not in _SCHEMA_CACHE:
            schema = call_mcp("get_schema", {"table_name": table})
            if not schema:
                schema = f"(No schema returned for table '{table}'.)"
            _SCHEMA_CACHE[table] = schema

        lines.append(_SCHEMA_CACHE[table])
        lines.append("")#Insert a blank line between tables so its easier to decipher

    _SCHEMA_BLOB = "\n".join(lines)
    return _SCHEMA_BLOB


def plan_sql(user_question: str) -> Dict[str, Any]:

    schema_blob = _get_all_schemas()
    table_list = ", ".join(TABLES) if TABLES else "(none)"
    relationship_list = (
        "- " + "\n- ".join(TABLE_RELATIONSHIPS)
        if TABLE_RELATIONSHIPS
        else "(no explicit relationships defined)"
    )

    system_prompt = PROMPT_TEMPLATE.format(
        db_engine=DB_ENGINE,
        table_list=table_list,
        relationship_list=relationship_list,
        schema_blob=schema_blob,
    )

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
