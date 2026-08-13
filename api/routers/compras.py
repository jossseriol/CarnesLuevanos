from datetime import date
import unicodedata

from fastapi import APIRouter, HTTPException, Query

from ..database import get_connection, rows_to_dicts, table_exists, transaction
from ..schemas import CompraIn


router = APIRouter(prefix="/compras", tags=["compras"])


def _row_value(row, key, index):
    try:
        return row[key]
    except Exception:
        return row[index]


def _normalizar_producto(texto: str | None) -> str:
    texto = str(texto or "").strip().lower()
    texto = " ".join(texto.split())
    return "".join(
        char for char in unicodedata.normalize("NFD", texto)
        if unicodedata.category(char) != "Mn"
    )


def _sincronizar_compra_con_inventario(conn, producto: str, cantidad: int, costo_unitario: float) -> None:
    if not table_exists(conn, "articulos"):
        return

    producto_normalizado = _normalizar_producto(producto)
    rows = conn.execute("SELECT id, articulo, precio, stock FROM articulos").fetchall()
    for row in rows:
        if _normalizar_producto(_row_value(row, "articulo", 1)) == producto_normalizado:
            articulo_id = _row_value(row, "id", 0)
            precio_actual = _row_value(row, "precio", 2) or costo_unitario
            stock_actual = _row_value(row, "stock", 3) or 0
            conn.execute(
                """
                UPDATE articulos
                SET stock = ?, costo = ?, precio = ?, estado = 'activo'
                WHERE id = ?
                """,
                (stock_actual + cantidad, costo_unitario, precio_actual, articulo_id),
            )
            return

    conn.execute(
        """
        INSERT INTO articulos (codigo, articulo, precio, costo, stock, estado, imagen_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (None, producto.strip(), costo_unitario, costo_unitario, cantidad, "activo", "media/icons/img_default.png"),
    )


@router.get("")
def listar_compras(
    q: str | None = None,
    estado: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    query = "SELECT * FROM compras WHERE 1 = 1"
    params: list[object] = []

    if q:
        like = f"%{q}%"
        query += " AND (proveedor LIKE ? OR factura LIKE ? OR producto LIKE ? OR notas LIKE ?)"
        params.extend([like, like, like, like])

    if estado:
        query += " AND estado = ?"
        params.append(estado)

    query += " ORDER BY fecha DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    conn = get_connection()
    try:
        return rows_to_dicts(conn.execute(query, params).fetchall())
    finally:
        conn.close()


@router.get("/{compra_id}")
def obtener_compra(compra_id: int):
    conn = get_connection()
    try:
        compra = conn.execute("SELECT * FROM compras WHERE id = ?", (compra_id,)).fetchone()
        if not compra:
            raise HTTPException(status_code=404, detail="Compra no encontrada")
        return dict(compra)
    finally:
        conn.close()


@router.post("", status_code=201)
def crear_compra(payload: CompraIn):
    total = payload.cantidad * payload.costo_unitario
    with transaction() as conn:
        cursor = conn.execute(
            """
            INSERT INTO compras
                (proveedor, factura, producto, cantidad, costo_unitario, total, fecha, estado, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.proveedor,
                payload.factura,
                payload.producto,
                payload.cantidad,
                payload.costo_unitario,
                total,
                payload.fecha or date.today().isoformat(),
                payload.estado,
                payload.notas,
            ),
        )
        compra_id = int(cursor.lastrowid)
        if str(payload.estado or "").strip().lower() != "cancelada":
            _sincronizar_compra_con_inventario(conn, payload.producto, payload.cantidad, payload.costo_unitario)
        compra = conn.execute("SELECT * FROM compras WHERE id = ?", (compra_id,)).fetchone()
        return dict(compra)
