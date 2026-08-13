from fastapi import APIRouter, HTTPException, Query

from ..database import get_connection, insert_row, rows_to_dicts, transaction, update_row
from ..schemas import ArticuloBase, ArticuloUpdate


router = APIRouter(prefix="/articulos", tags=["articulos"])


@router.get("")
def listar_articulos(
    buscar: str | None = None,
    activos: bool = True,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    query = "SELECT * FROM articulos WHERE 1 = 1"
    params: list[object] = []

    if activos:
        query += " AND LOWER(estado) = 'activo'"

    if buscar:
        query += " AND (codigo LIKE ? OR articulo LIKE ?)"
        params.extend([f"%{buscar}%", f"%{buscar}%"])

    query += " ORDER BY articulo LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    conn = get_connection()
    try:
        return rows_to_dicts(conn.execute(query, params).fetchall())
    finally:
        conn.close()


@router.get("/{articulo_id}")
def obtener_articulo(articulo_id: int):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM articulos WHERE id = ?", (articulo_id,)).fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Articulo no encontrado")
    return dict(row)


@router.post("", status_code=201)
def crear_articulo(payload: ArticuloBase):
    with transaction() as conn:
        articulo_id = insert_row(conn, "articulos", payload.model_dump())
        row = conn.execute("SELECT * FROM articulos WHERE id = ?", (articulo_id,)).fetchone()
        return dict(row)


@router.put("/{articulo_id}")
def actualizar_articulo(articulo_id: int, payload: ArticuloUpdate):
    with transaction() as conn:
        updated = update_row(
            conn,
            "articulos",
            articulo_id,
            payload.model_dump(exclude_unset=True),
        )
        if updated == 0:
            raise HTTPException(status_code=404, detail="Articulo no encontrado")
        row = conn.execute("SELECT * FROM articulos WHERE id = ?", (articulo_id,)).fetchone()
        return dict(row)


@router.delete("/{articulo_id}", status_code=204)
def eliminar_articulo(articulo_id: int):
    with transaction() as conn:
        cursor = conn.execute("DELETE FROM articulos WHERE id = ?", (articulo_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Articulo no encontrado")
