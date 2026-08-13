import sqlite3
import shutil
from contextlib import contextmanager
from typing import Any, Iterable

from .config import (
    DATABASE_PATH,
    DATABASE_SEED_PATH,
    DB_ENGINE,
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
)


def is_mysql() -> bool:
    return DB_ENGINE == "mysql"


def _translate_placeholders(sql: str) -> str:
    return sql.replace("?", "%s")


class MySQLConnection:
    def __init__(self):
        try:
            import pymysql
        except ImportError as exc:
            raise RuntimeError("PyMySQL no esta instalado. Instala requirements-cloud-mysql.txt.") from exc

        self._conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )

    def execute(self, sql: str, params: Iterable[Any] | None = None):
        cursor = self._conn.cursor()
        cursor.execute(_translate_placeholders(sql), tuple(params or ()))
        return cursor

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    def close(self) -> None:
        self._conn.close()


def ensure_database_ready() -> None:
    if is_mysql():
        return
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATABASE_PATH.exists() and DATABASE_SEED_PATH.exists():
        shutil.copy2(DATABASE_SEED_PATH, DATABASE_PATH)


def get_connection():
    if is_mysql():
        return MySQLConnection()

    ensure_database_ready()
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transaction():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def rows_to_dicts(rows: Iterable[Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def table_exists(conn, table_name: str) -> bool:
    if is_mysql():
        row = conn.execute("SHOW TABLES LIKE ?", (table_name,)).fetchone()
        return row is not None

    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def table_columns(conn, table_name: str) -> list[str]:
    if is_mysql():
        rows = conn.execute(f"SHOW COLUMNS FROM {table_name}").fetchall()
        return [row["Field"] for row in rows]

    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [row["name"] for row in rows]


def insert_row(conn, table_name: str, data: dict[str, Any]) -> int:
    columns = table_columns(conn, table_name)
    clean_data = {key: value for key, value in data.items() if key in columns}

    if not clean_data:
        raise ValueError("No hay campos validos para insertar")

    field_names = ", ".join(clean_data.keys())
    placeholders = ", ".join(["?"] * len(clean_data))

    cursor = conn.execute(
        f"INSERT INTO {table_name} ({field_names}) VALUES ({placeholders})",
        tuple(clean_data.values()),
    )
    return int(cursor.lastrowid)


def update_row(
    conn,
    table_name: str,
    row_id: int,
    data: dict[str, Any],
    id_column: str = "id",
) -> int:
    columns = table_columns(conn, table_name)
    clean_data = {
        key: value
        for key, value in data.items()
        if key in columns and key != id_column and value is not None
    }

    if not clean_data:
        raise ValueError("No hay campos validos para actualizar")

    assignments = ", ".join([f"{key} = ?" for key in clean_data])
    params = tuple(clean_data.values()) + (row_id,)
    cursor = conn.execute(
        f"UPDATE {table_name} SET {assignments} WHERE {id_column} = ?",
        params,
    )
    return cursor.rowcount
