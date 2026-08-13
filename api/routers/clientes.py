from fastapi import APIRouter, HTTPException, Query

from ..database import get_connection, insert_row, rows_to_dicts, transaction, update_row
from ..schemas import ClienteBase, ClienteUpdate


router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get("")
def listar_clientes(
    buscar: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    query = "SELECT * FROM clientes WHERE 1 = 1"
    params: list[object] = []

    if buscar:
        query += " AND (nombre LIKE ? OR cedula LIKE ? OR celular LIKE ? OR correo LIKE ?)"
        params.extend([f"%{buscar}%"] * 4)

    query += " ORDER BY nombre LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    conn = get_connection()
    try:
        return rows_to_dicts(conn.execute(query, params).fetchall())
    finally:
        conn.close()


@router.get("/{cliente_id}")
def obtener_cliente(cliente_id: int):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return dict(row)


@router.post("", status_code=201)
def crear_cliente(payload: ClienteBase):
    with transaction() as conn:
        cliente_id = insert_row(conn, "clientes", payload.model_dump())
        row = conn.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
        return dict(row)


@router.put("/{cliente_id}")
def actualizar_cliente(cliente_id: int, payload: ClienteUpdate):
    with transaction() as conn:
        updated = update_row(
            conn,
            "clientes",
            cliente_id,
            payload.model_dump(exclude_unset=True),
        )
        if updated == 0:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        row = conn.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
        return dict(row)


@router.delete("/{cliente_id}", status_code=204)
def eliminar_cliente(cliente_id: int):
    with transaction() as conn:
        cursor = conn.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
