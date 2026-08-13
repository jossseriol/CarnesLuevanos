# API para Android

Esta API conecta la app de escritorio Tkinter/CustomTkinter con `database.db`.

## Instalacion

```bash
pip install -r requirements-api.txt
```

## Ejecutar

Desde la carpeta del proyecto:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

En la misma computadora puedes abrir la documentación de la API:

```text
http://127.0.0.1:8000/docs
```

Desde Android, usa la IP de la computadora donde corre la API:

```text
http://IP-DE-LA-PC:8000/api/articulos
http://IP-DE-LA-PC:8000/api/clientes
http://IP-DE-LA-PC:8000/api/ventas
```

## Endpoints principales

- `POST /api/auth/login`
- `GET /api/articulos`
- `POST /api/articulos`
- `PUT /api/articulos/{id}`
- `DELETE /api/articulos/{id}`
- `GET /api/clientes`
- `POST /api/clientes`
- `GET /api/proveedores`
- `POST /api/proveedores`
- `GET /api/pedidos-proveedor`
- `POST /api/pedidos-proveedor`
- `POST /api/pedidos-proveedor/{id}/completar`
- `GET /api/ventas`
- `GET /api/ventas/resumen`
- `POST /api/ventas`

## Ejemplo de venta

```json
{
  "cliente": "Cliente General",
  "items": [
    {
      "codigo": "7501234567890",
      "cantidad": 2
    }
  ]
}
```

La venta descuenta stock en `articulos`, guarda renglones en `ventas` y crea registros en `detalle_ventas`.
