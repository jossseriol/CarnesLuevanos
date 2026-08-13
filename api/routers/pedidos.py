from datetime import date

from fastapi import APIRouter, HTTPException, Query

from ..database import get_connection, rows_to_dicts, transaction
from ..schemas import PedidoProveedorIn


router = APIRouter(prefix="/pedidos-proveedor", tags=["pedidos"])


@router.get("")
def listar_pedidos(
    estado: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    query = "SELECT * FROM pedidos_proveedor WHERE 1 = 1"
    params: list[object] = []

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


@router.get("/{pedido_id}")
def obtener_pedido(pedido_id: int):
    conn = get_connection()
    try:
        pedido = conn.execute(
            "SELECT * FROM pedidos_proveedor WHERE id = ?",
            (pedido_id,),
        ).fetchone()
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")

        detalles = conn.execute(
            "SELECT * FROM pedidos_detalle WHERE pedido_id = ?",
            (pedido_id,),
        ).fetchall()
        data = dict(pedido)
        data["detalles"] = rows_to_dicts(detalles)
        return data
    finally:
        conn.close()


@router.post("", status_code=201)
def crear_pedido(payload: PedidoProveedorIn):
    total = sum(item.cantidad * item.precio_unitario for item in payload.detalles)

    with transaction() as conn:
        cursor = conn.execute(
            """
            INSERT INTO pedidos_proveedor
                (proveedor_nombre, fecha, estado, total, observaciones)
            VALUES (?, ?, 'Pendiente', ?, ?)
            """,
            (payload.proveedor_nombre, date.today().isoformat(), total, payload.observaciones),
        )
        pedido_id = int(cursor.lastrowid)

        for item in payload.detalles:
            subtotal = item.cantidad * item.precio_unitario
            conn.execute(
                """
                INSERT INTO pedidos_detalle
                    (pedido_id, producto_codigo, producto_nombre, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    pedido_id,
                    item.producto_codigo,
                    item.producto_nombre,
                    item.cantidad,
                    item.precio_unitario,
                    subtotal,
                ),
            )

        pedido = conn.execute(
            "SELECT * FROM pedidos_proveedor WHERE id = ?",
            (pedido_id,),
        ).fetchone()
        return dict(pedido)


@router.post("/{pedido_id}/completar")
def completar_pedido(pedido_id: int):
    with transaction() as conn:
        pedido = conn.execute(
            "SELECT * FROM pedidos_proveedor WHERE id = ?",
            (pedido_id,),
        ).fetchone()
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")

        detalles = conn.execute(
            "SELECT producto_codigo, cantidad FROM pedidos_detalle WHERE pedido_id = ?",
            (pedido_id,),
        ).fetchall()

        for detalle in detalles:
            conn.execute(
                "UPDATE productos SET stock = stock + ? WHERE codigo = ?",
                (detalle["cantidad"], detalle["producto_codigo"]),
            )

        conn.execute(
            "UPDATE pedidos_proveedor SET estado = 'Completado' WHERE id = ?",
            (pedido_id,),
        )
        return {"id": pedido_id, "estado": "Completado"}
