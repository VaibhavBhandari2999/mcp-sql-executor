import os
from typing import Any, List
import mysql.connector
from mysql.connector import pooling
import psycopg
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv

load_dotenv()

DB_ENGINE = os.getenv("DB_ENGINE", "mysql").lower()

_mysql_pool = None
_pg_pool: ConnectionPool | None = None

def _get_mysql_pool():

    global _mysql_pool
    if _mysql_pool is None:
        _mysql_pool = pooling.MySQLConnectionPool(
            pool_name="mcp_mysql_pool",
            pool_size=5,
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_DATABASE"),
        )
    return _mysql_pool

def _get_pg_pool() -> ConnectionPool:

    global _pg_pool
    if _pg_pool is None:
        dsn = (
            f"host={os.getenv('DB_HOST', '127.0.0.1')} "
            f"port={os.getenv('DB_PORT', '5432')} "
            f"dbname={os.getenv('DB_DATABASE')} "
            f"user={os.getenv('DB_USER')} "
            f"password={os.getenv('DB_PASSWORD')}"
        )
        _pg_pool = ConnectionPool(dsn)
    return _pg_pool


def query(sql: str, params: List[Any] | None = None) -> list[dict]:

    params = params or []

    if DB_ENGINE == "mysql":
        pool = _get_mysql_pool()
        conn = pool.get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows
        finally:
            cur.close()
            conn.close()

    elif DB_ENGINE == "postgres":
        pool = _get_pg_pool()
        with pool.connection() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
                return rows

    else:
        raise ValueError(f"Unsupported DB_ENGINE: {DB_ENGINE}")


def get_table_schema(table_name: str) -> str:

    if not table_name.isidentifier():
        raise ValueError("Invalid table name")

    if DB_ENGINE == "mysql":
        sql = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """
        rows = query(sql, [os.getenv("DB_DATABASE"), table_name])

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

        return f"Schema for table {table_name} (MySQL):\n" + "\n".join(lines)

    elif DB_ENGINE == "postgres":
        sql = """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s
        ORDER BY ordinal_position;
        """
        rows = query(sql, [table_name])

        if not rows:
            return f"No schema found for table '{table_name}'."

        lines = []
        for r in rows:
            col = r["column_name"]
            dtype = r["data_type"]
            nullable = r["is_nullable"]
            default = r["column_default"]
            nn = " NOT NULL" if nullable == "NO" else " NULLABLE"
            default_str = f" DEFAULT {default}" if default is not None else ""
            lines.append(f"{col} {dtype}{nn}{default_str}")

        return f"Schema for table {table_name} (Postgres):\n" + "\n".join(lines)

    else:
        raise ValueError(f"Unsupported DB_ENGINE: {DB_ENGINE}")