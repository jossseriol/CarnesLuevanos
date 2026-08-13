from datetime import datetime

from fastapi import APIRouter, Query

from ..database import get_connection, is_mysql, rows_to_dicts, transaction
from ..schemas import EventoSistemaIn


router = APIRouter(prefix="/eventos-sistema", tags=["eventos-sistema"])


def asegurar_tabla_eventos(conn):
    if is_mysql():
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS eventos_sistema (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tipo VARCHAR(100) NOT NULL,
                titulo VARCHAR(255) NOT NULL,
                mensaje TEXT NOT NULL,
                usuario VARCHAR(255),
                origen VARCHAR(100),
                fecha VARCHAR(30) NOT NULL,
                leido TINYINT DEFAULT 0
            )
            """
        )
    else:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS eventos_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                titulo TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                usuario TEXT,
                origen TEXT,
                fecha TEXT NOT NULL,
                leido INTEGER DEFAULT 0
            )
            """
        )


@router.get("")
def listar_eventos(
    despues_de_id: int = Query(default=0, ge=0),
    tipo: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    conn = get_connection()
    try:
        asegurar_tabla_eventos(conn)
        query = "SELECT * FROM eventos_sistema WHERE id > ?"
        params: list[object] = [despues_de_id]

        if tipo:
            query += " AND tipo = ?"
            params.append(tipo)

        query += " ORDER BY id ASC LIMIT ?"
        params.append(limit)
        return rows_to_dicts(conn.execute(query, params).fetchall())
    finally:
        conn.close()


@router.post("", status_code=201)
def crear_evento(payload: EventoSistemaIn):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with transaction() as conn:
        asegurar_tabla_eventos(conn)
        cursor = conn.execute(
            """
            INSERT INTO eventos_sistema (tipo, titulo, mensaje, usuario, origen, fecha, leido)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """,
            (payload.tipo, payload.titulo, payload.mensaje, payload.usuario, payload.origen, fecha),
        )
        evento_id = int(cursor.lastrowid)
        evento = conn.execute("SELECT * FROM eventos_sistema WHERE id = ?", (evento_id,)).fetchone()
        return dict(evento)
