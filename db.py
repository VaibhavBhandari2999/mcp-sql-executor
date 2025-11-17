import os
from typing import Any, List
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

_DB_POOL = None

def _get_pool():
    global _DB_POOL
    if _DB_POOL is None:
        _DB_POOL = pooling.MySQLConnectionPool(
            pool_name="mcp_pool",
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_DATABASE"),
        )
    return _DB_POOL


def query(sql: str, params: List[Any] | None = None) -> list[dict]:

    pool = _get_pool()
    conn = pool.get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or [])
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()
        conn.close()


def get_table_schema(table_name: str) -> str:

    if not table_name.isidentifier():
        raise ValueError("Invalid table name")

    sql = """
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
    ORDER BY ORDINAL_POSITION
    """
    rows = query(
        sql,
        [os.getenv("DB_DATABASE"), table_name],
    )

    if not rows:
        return f"No schema found for table '{table_name}'."

    lines = []
    for r in rows:
        col = r["COLUMN_NAME"]
        dtype = r["DATA_TYPE"]
        nullable = r["IS_NULLABLE"]
        key = r["COLUMN_KEY"] or ""
        pk = " (PK)" if key == "PRI" else ""
        nn = " NOT NULL" if nullable == "NO" else " NULLABLE"
        lines.append(f"{col} {dtype}{pk}{nn}")

    return f"Schema for table {table_name}:\n" + "\n".join(lines)
