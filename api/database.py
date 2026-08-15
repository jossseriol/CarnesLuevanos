import sqlite3
import shutil
import os
from contextlib import contextmanager
from pathlib import Path
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
        schema_path = Path(__file__).with_name("mysql_schema.sql")

        if not schema_path.exists():
            raise RuntimeError(
                f"No se encontro el esquema MySQL: {schema_path}"
            )

        conn = get_connection()
        try:
            sql_script = schema_path.read_text(encoding="utf-8")

            for statement in sql_script.split(";"):
                statement = statement.strip()
                if statement:
                    conn.execute(statement)

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        return

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not DATABASE_PATH.exists():
        if DATABASE_SEED_PATH.exists() and DATABASE_SEED_PATH != DATABASE_PATH:
            shutil.copy2(DATABASE_SEED_PATH, DATABASE_PATH)
        else:
            _initialize_empty_database()

def _initialize_empty_database() -> None:
    schema_path = Path(__file__).with_name("sqlite_schema.sql")
    if not schema_path.exists():
        raise RuntimeError(f"No se encontro el esquema inicial: {schema_path}")

    admin_username = os.getenv("CARNES_LUEVANOS_INITIAL_ADMIN_USERNAME", "admin").strip() or "admin"
    admin_password = os.getenv("CARNES_LUEVANOS_INITIAL_ADMIN_PASSWORD", "").strip()
    if not admin_password:
        raise RuntimeError(
            "Define CARNES_LUEVANOS_INITIAL_ADMIN_PASSWORD para crear la base de datos inicial."
        )

    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()

    from modulos.auth.seguridad import ensure_security_schema, hash_password

    ensure_security_schema()

    conn = sqlite3.connect(DATABASE_PATH)
    try:
        row = conn.execute("SELECT id FROM usuarios LIMIT 1").fetchone()
        if row is None:
            cursor = conn.execute(
                """INSERT INTO usuarios
                   (username, password, nombre, rol, estado, requiere_cambio_password)
                   VALUES (?, ?, ?, 'super', 'activo', 0)""",
                (admin_username, hash_password(admin_password), "Administrador Luevanos"),
            )
            admin_id = int(cursor.lastrowid)
            for module in (
                "ventas", "inventario", "clientes", "pedidos", "proveedores",
                "compras", "rendimiento", "informacion", "configuracion",
            ):
                conn.execute(
                    "INSERT INTO permisos_usuario (usuario_id, modulo, permitido) VALUES (?, ?, 1)",
                    (admin_id, module),
                )
        conn.commit()
    finally:
        conn.close()


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
