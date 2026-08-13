from fastapi import APIRouter, HTTPException, Query

from ..database import get_connection, insert_row, rows_to_dicts, transaction, update_row
from ..schemas import ProveedorBase, ProveedorUpdate


router = APIRouter(prefix="/proveedores", tags=["proveedores"])


@router.get("")
def listar_proveedores(
    buscar: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    query = "SELECT * FROM proveedores WHERE 1 = 1"
    params: list[object] = []

    if buscar:
        query += " AND (empresa LIKE ? OR rif LIKE ? OR celular LIKE ? OR correo LIKE ?)"
        params.extend([f"%{buscar}%"] * 4)

    query += " ORDER BY empresa LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    conn = get_connection()
    try:
        return rows_to_dicts(conn.execute(query, params).fetchall())
    finally:
        conn.close()


@router.post("", status_code=201)
def crear_proveedor(payload: ProveedorBase):
    with transaction() as conn:
        proveedor_id = insert_row(conn, "proveedores", payload.model_dump())
        row = conn.execute("SELECT * FROM proveedores WHERE id = ?", (proveedor_id,)).fetchone()
        return dict(row)


@router.put("/{proveedor_id}")
def actualizar_proveedor(proveedor_id: int, payload: ProveedorUpdate):
    with transaction() as conn:
        updated = update_row(
            conn,
            "proveedores",
            proveedor_id,
            payload.model_dump(exclude_unset=True),
        )
        if updated == 0:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        row = conn.execute("SELECT * FROM proveedores WHERE id = ?", (proveedor_id,)).fetchone()
        return dict(row)


@router.delete("/{proveedor_id}", status_code=204)
def eliminar_proveedor(proveedor_id: int):
    with transaction() as conn:
        cursor = conn.execute("DELETE FROM proveedores WHERE id = ?", (proveedor_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
