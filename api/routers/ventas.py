from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Query

from ..database import get_connection, is_mysql, rows_to_dicts, table_columns, transaction
from ..schemas import VentaIn


router = APIRouter(prefix="/ventas", tags=["ventas"])


def _siguiente_factura(conn) -> int:
    row = conn.execute("SELECT COALESCE(MAX(factura), 0) + 1 AS numero FROM ventas").fetchone()
    return int(row["numero"])


def _buscar_producto(conn, codigo: str | None, producto: str | None):
    if codigo:
        row = conn.execute(
            """
            SELECT 'articulos' AS tabla, codigo, articulo AS nombre, precio, costo, stock
            FROM articulos
            WHERE codigo = ? AND LOWER(estado) = 'activo'
            """,
            (codigo,),
        ).fetchone()
        if row:
            return row

    if producto:
        row = conn.execute(
            """
            SELECT 'articulos' AS tabla, codigo, articulo AS nombre, precio, costo, stock
            FROM articulos
            WHERE articulo = ? AND LOWER(estado) = 'activo'
            """,
            (producto,),
        ).fetchone()
        if row:
            return row

    raise HTTPException(status_code=404, detail=f"Producto no encontrado: {codigo or producto}")


@router.get("")
def listar_ventas(
    fecha: str | None = None,
    factura: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    row_id = "id AS row_id" if is_mysql() else "rowid AS row_id"
    query = f"SELECT {row_id}, * FROM ventas WHERE 1 = 1"
    params: list[object] = []

    if fecha:
        query += " AND fecha = ?"
        params.append(fecha)

    if factura is not None:
        query += " AND factura = ?"
        params.append(factura)

    query += " ORDER BY fecha DESC, hora DESC, factura DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    conn = get_connection()
    try:
        return rows_to_dicts(conn.execute(query, params).fetchall())
    finally:
        conn.close()


@router.get("/resumen")
def resumen_ventas(fecha: str | None = None):
    fecha_consulta = fecha or date.today().isoformat()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(total), 0) AS total, COUNT(*) AS movimientos
            FROM ventas
            WHERE fecha = ?
            """,
            (fecha_consulta,),
        ).fetchone()
        return {"fecha": fecha_consulta, "total": row["total"], "movimientos": row["movimientos"]}
    finally:
        conn.close()


@router.post("", status_code=201)
def crear_venta(payload: VentaIn):
    ahora = datetime.now()
    fecha = ahora.date().isoformat()
    hora = ahora.strftime("%H:%M:%S")

    with transaction() as conn:
        factura = _siguiente_factura(conn)
        ventas_columns = table_columns(conn, "ventas")
        venta_rows = []
        total_general = 0.0

        for item in payload.items:
            producto = _buscar_producto(conn, item.codigo, item.producto)

            if producto["stock"] < item.cantidad:
                raise HTTPException(
                    status_code=409,
                    detail=f"Stock insuficiente para {producto['nombre']}",
                )

            subtotal = float(producto["precio"]) * item.cantidad
            total_general += subtotal

            data = {
                "factura": factura,
                "cliente": payload.cliente,
                "articulo": producto["nombre"],
                "precio": producto["precio"],
                "cantidad": item.cantidad,
                "total": subtotal,
                "fecha": fecha,
                "hora": hora,
                "costo": producto["costo"],
            }
            insert_data = {key: value for key, value in data.items() if key in ventas_columns}
            fields = ", ".join(insert_data.keys())
            placeholders = ", ".join(["?"] * len(insert_data))
            cursor = conn.execute(
                f"INSERT INTO ventas ({fields}) VALUES ({placeholders})",
                tuple(insert_data.values()),
            )
            venta_rowid = int(cursor.lastrowid)

            conn.execute(
                "UPDATE articulos SET stock = stock - ? WHERE codigo = ? OR articulo = ?",
                (item.cantidad, producto["codigo"], producto["nombre"]),
            )

            conn.execute(
                """
                INSERT INTO detalle_ventas
                    (venta_id, producto, precio_unitario, cantidad, subtotal)
                VALUES (?, ?, ?, ?, ?)
                """,
                (venta_rowid, producto["nombre"], producto["precio"], item.cantidad, subtotal),
            )

            venta_rows.append({**data, "row_id": venta_rowid})

        return {
            "factura": factura,
            "cliente": payload.cliente,
            "fecha": fecha,
            "hora": hora,
            "total": total_general,
            "items": venta_rows,
        }
