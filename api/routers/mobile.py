"""Endpoints móviles adicionales para Carnes Luévanos iOS.

Copiar como api/routers/mobile.py e incluir el router en api/main.py.
No depende de paquetes de IA externos: puede reenviar a Jelox Studio si se
configuran JELOX_STUDIO_API_URL y JELOX_STUDIO_API_KEY; de lo contrario ofrece
un asistente contextual local respaldado por la base de datos.
"""

from datetime import date, datetime, timedelta
import json
import os
import re
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import get_connection, is_mysql, table_columns, table_exists, transaction


router = APIRouter(prefix="/mobile", tags=["mobile"])


class JeloxIn(BaseModel):
    message: str
    module: str | None = None
    username: str | None = None


MODULES = {
    "prestamos": {
        "title": "Préstamos",
        "table": "prestamos",
        "fields": [
            ("beneficiario", "Beneficiario", "text", True),
            ("concepto", "Concepto", "text", False),
            ("monto", "Monto", "number", True),
            ("vencimiento", "Vencimiento", "date", False),
            ("notas", "Notas", "text", False),
        ],
    },
    "nominas": {
        "title": "Nóminas",
        "table": "nominas",
        "fields": [
            ("empleado", "Empleado", "text", True),
            ("puesto", "Puesto", "text", False),
            ("periodo", "Periodo", "text", True),
            ("sueldo", "Sueldo", "number", True),
            ("bonos", "Bonos", "number", False),
            ("deducciones", "Deducciones", "number", False),
            ("notas", "Notas", "text", False),
        ],
    },
    "abonos": {
        "title": "Abonos",
        "table": "abonos_mobile",
        "fields": [
            ("persona", "Cliente o beneficiario", "text", True),
            ("concepto", "Concepto", "text", True),
            ("monto", "Monto", "number", True),
            ("referencia", "Referencia", "text", False),
        ],
    },
    "empacadora": {
        "title": "Empacadora",
        "table": "empacadora_ventas",
        "fields": [
            ("cliente", "Cliente", "text", True),
            ("folio", "Folio", "text", True),
            ("monto", "Monto", "number", True),
            ("lote", "Lote", "text", False),
        ],
    },
}

ADMIN_MODULES = [
    "ventas", "inventario", "clientes", "pedidos", "proveedores",
    "compras", "rendimiento", "informacion", "configuracion",
]

COMPANY_KEYS = {
    "name": "nombre_empresa",
    "legalName": "razon_social_empresa",
    "taxId": "rif_empresa",
    "phone": "telefono_empresa",
    "email": "correo_empresa",
    "address": "direccion_empresa",
    "currency": "moneda_principal",
}

COMPANY_DEFAULTS = {
    "name": "Carnes Luevanos",
    "legalName": "Carnes Luevanos",
    "taxId": "J-00000000-0",
    "phone": "+52 87 1503 4671",
    "email": "info@carnesluevanos.com",
    "address": "Torreón, Coah.",
    "currency": "USD",
}


def _ensure_admin_tables(conn):
    user_columns = set(table_columns(conn, "usuarios"))
    missing_user_columns = {
        "estado": "VARCHAR(30) DEFAULT 'activo'" if is_mysql() else "TEXT DEFAULT 'activo'",
        "sucursal": "VARCHAR(160)" if is_mysql() else "TEXT",
        "numero_empleado": "VARCHAR(80)" if is_mysql() else "TEXT",
        "ultimo_acceso": "VARCHAR(40)" if is_mysql() else "TEXT",
    }
    for column, definition in missing_user_columns.items():
        if column not in user_columns:
            conn.execute(f"ALTER TABLE usuarios ADD COLUMN {column} {definition}")

    # La instalación original creó la cuenta "admin" antes de incorporar roles.
    # Se migra a administrador para conservar su finalidad sin convertirla en
    # una cuenta superprotegida.
    conn.execute(
        """UPDATE usuarios SET rol='administrador'
           WHERE LOWER(username)='admin'
             AND LOWER(COALESCE(rol, 'usuario'))='usuario'"""
    )

    if is_mysql():
        conn.execute(
            """CREATE TABLE IF NOT EXISTS permisos_usuario (
                id INT AUTO_INCREMENT PRIMARY KEY, usuario_id INT NOT NULL,
                modulo VARCHAR(80) NOT NULL, permitido TINYINT NOT NULL DEFAULT 0,
                UNIQUE KEY permisos_usuario_modulo (usuario_id, modulo))"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS configuracion_sistema (
                id INT AUTO_INCREMENT PRIMARY KEY, clave VARCHAR(120) NOT NULL UNIQUE,
                valor TEXT NOT NULL, descripcion TEXT,
                fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP)"""
        )
    else:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS permisos_usuario (
                id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL,
                modulo TEXT NOT NULL, permitido INTEGER NOT NULL DEFAULT 0,
                UNIQUE(usuario_id, modulo),
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE)"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS configuracion_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT, clave TEXT NOT NULL UNIQUE,
                valor TEXT NOT NULL, descripcion TEXT,
                fecha_modificacion TEXT DEFAULT CURRENT_TIMESTAMP)"""
        )


def _require_admin(conn, actor):
    row = conn.execute(
        "SELECT id, username, COALESCE(rol, 'usuario') AS rol FROM usuarios WHERE LOWER(username)=LOWER(?)",
        ((actor or "").strip(),),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=403, detail="Usuario administrador no encontrado")
    user = dict(row)
    if str(user.get("rol") or "").lower() not in {"super", "administrador", "admin"}:
        raise HTTPException(status_code=403, detail="Solo un administrador puede gestionar roles y permisos")
    return user


def _company_info(conn):
    values = {}
    try:
        rows = conn.execute("SELECT clave, valor FROM configuracion_sistema").fetchall()
        values = {str(dict(row).get("clave")): str(dict(row).get("valor") or "") for row in rows}
    except Exception:
        pass
    return {field: values.get(key, COMPANY_DEFAULTS[field]) for field, key in COMPANY_KEYS.items()}


def _save_user_permissions(conn, user_id, permissions):
    for module in ADMIN_MODULES:
        permitted = 1 if bool((permissions or {}).get(module, False)) else 0
        if is_mysql():
            conn.execute(
                """INSERT INTO permisos_usuario(usuario_id, modulo, permitido) VALUES(?,?,?)
                   ON DUPLICATE KEY UPDATE permitido=VALUES(permitido)""",
                (user_id, module, permitted),
            )
        else:
            conn.execute(
                """INSERT INTO permisos_usuario(usuario_id, modulo, permitido) VALUES(?,?,?)
                   ON CONFLICT(usuario_id, modulo) DO UPDATE SET permitido=excluded.permitido""",
                (user_id, module, permitted),
            )


@router.get("/admin")
def mobile_admin(actor: str):
    conn = get_connection()
    try:
        _ensure_admin_tables(conn)
        conn.commit()
        _require_admin(conn, actor)
        permission_rows = conn.execute(
            "SELECT usuario_id, modulo, permitido FROM permisos_usuario"
        ).fetchall()
        by_user = {}
        for row in permission_rows:
            data = dict(row)
            by_user.setdefault(int(data["usuario_id"]), {})[str(data["modulo"])] = bool(data["permitido"])
        rows = conn.execute(
            """SELECT id, username, COALESCE(nombre, username) AS nombre,
                      COALESCE(rol, 'usuario') AS rol, COALESCE(estado, 'activo') AS estado,
                      COALESCE(sucursal, '') AS sucursal,
                      COALESCE(numero_empleado, '') AS numero_empleado,
                      COALESCE(ultimo_acceso, '') AS ultimo_acceso
               FROM usuarios ORDER BY CASE WHEN LOWER(COALESCE(rol,''))='super' THEN 0 ELSE 1 END, nombre"""
        ).fetchall()
        users = []
        for row in rows:
            data = dict(row)
            user_id = int(data["id"])
            role = str(data.get("rol") or "usuario").lower()
            saved = by_user.get(user_id, {})
            permissions = {
                module: True if role == "super" else bool(saved.get(module, module == "informacion"))
                for module in ADMIN_MODULES
            }
            users.append({
                "id": user_id,
                "username": data.get("username") or "",
                "name": data.get("nombre") or data.get("username") or "Usuario",
                "role": role,
                "status": data.get("estado") or "activo",
                "branch": data.get("sucursal") or "",
                "employeeNumber": data.get("numero_empleado") or "",
                "lastAccess": data.get("ultimo_acceso") or "",
                "permissions": permissions,
            })
        return {"users": users, "company": _company_info(conn)}
    finally:
        conn.close()


@router.post("/admin/users", status_code=201)
def create_mobile_user(payload: dict):
    allowed_roles = {"administrador", "ventas", "compras", "almacen", "usuario"}
    username = str(payload.get("username") or "").strip()
    name = str(payload.get("name") or "").strip()
    password = str(payload.get("password") or "")
    role = str(payload.get("role") or "usuario").strip().lower()
    branch = str(payload.get("branch") or "").strip()
    employee_number = str(payload.get("employeeNumber") or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,50}", username):
        raise HTTPException(status_code=400, detail="El usuario debe tener entre 3 y 50 caracteres y usar solo letras, numeros, punto, guion o guion bajo")
    if len(name) < 3:
        raise HTTPException(status_code=400, detail="Ingresa el nombre completo del usuario")
    if role not in allowed_roles:
        raise HTTPException(status_code=400, detail="Rol no valido")
    try:
        from modulos.auth.seguridad import hash_password

        password_hash = hash_password(password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    with transaction() as conn:
        _ensure_admin_tables(conn)
        _require_admin(conn, payload.get("actor"))
        duplicate = conn.execute(
            "SELECT id FROM usuarios WHERE LOWER(username)=LOWER(?)",
            (username,),
        ).fetchone()
        if duplicate:
            raise HTTPException(status_code=409, detail="Ese nombre de usuario ya existe")
        now = datetime.now()
        cursor = conn.execute(
            """INSERT INTO usuarios
               (username, password, nombre, rol, numero_empleado, sucursal, estado,
                password_cambiada, password_vence, intentos_fallidos,
                mfa_habilitado, requiere_cambio_password)
               VALUES (?, ?, ?, ?, ?, ?, 'activo', ?, ?, 0, 0, 0)""",
            (
                username,
                password_hash,
                name,
                role,
                employee_number or None,
                branch or None,
                now.isoformat(timespec="seconds"),
                (now + timedelta(days=90)).isoformat(timespec="seconds"),
            ),
        )
        user_id = int(cursor.lastrowid)
        permissions = payload.get("permissions") or {}
        _save_user_permissions(conn, user_id, permissions)
        return {
            "id": user_id,
            "username": username,
            "name": name,
            "role": role,
            "status": "activo",
            "branch": branch,
            "employeeNumber": employee_number,
            "lastAccess": "",
            "permissions": {module: bool(permissions.get(module, False)) for module in ADMIN_MODULES},
        }


@router.put("/admin/users/{user_id}")
def update_mobile_user_permissions(user_id: int, payload: dict):
    allowed_roles = {"administrador", "ventas", "compras", "almacen", "usuario"}
    with transaction() as conn:
        _ensure_admin_tables(conn)
        _require_admin(conn, payload.get("actor"))
        target = conn.execute(
            "SELECT id, username, COALESCE(rol, 'usuario') AS rol FROM usuarios WHERE id=?",
            (user_id,),
        ).fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        if str(dict(target).get("rol") or "").lower() == "super":
            raise HTTPException(status_code=409, detail="La cuenta superadministrador está protegida")
        role = str(payload.get("role") or "usuario").strip().lower()
        if role not in allowed_roles:
            raise HTTPException(status_code=400, detail="Rol no válido")
        conn.execute("UPDATE usuarios SET rol=? WHERE id=?", (role, user_id))
        permissions = payload.get("permissions") or {}
        _save_user_permissions(conn, user_id, permissions)
        return {"ok": True, "user_id": user_id, "role": role, "permissions": permissions}


@router.put("/admin/company")
def update_mobile_company(payload: dict):
    with transaction() as conn:
        _ensure_admin_tables(conn)
        _require_admin(conn, payload.get("actor"))
        for field, key in COMPANY_KEYS.items():
            value = str(payload.get(field, COMPANY_DEFAULTS[field])).strip()
            description = f"Configuración comercial: {field}"
            if is_mysql():
                conn.execute(
                    """INSERT INTO configuracion_sistema(clave, valor, descripcion) VALUES(?,?,?)
                       ON DUPLICATE KEY UPDATE valor=VALUES(valor), descripcion=VALUES(descripcion)""",
                    (key, value, description),
                )
            else:
                conn.execute(
                    """INSERT INTO configuracion_sistema(clave, valor, descripcion) VALUES(?,?,?)
                       ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor,
                       descripcion=excluded.descripcion, fecha_modificacion=CURRENT_TIMESTAMP""",
                    (key, value, description),
                )
        return {"ok": True, "company": _company_info(conn)}


def _scalar(conn, query, params=(), default=0):
    try:
        row = conn.execute(query, params).fetchone()
        if not row:
            return default
        try:
            return next(iter(dict(row).values()))
        except Exception:
            return row[0]
    except Exception:
        return default


def _ensure_mobile_tables(conn):
    if is_mysql():
        statements = [
            """CREATE TABLE IF NOT EXISTS abonos_mobile (
                id INT AUTO_INCREMENT PRIMARY KEY, persona VARCHAR(255) NOT NULL,
                concepto VARCHAR(255) NOT NULL, monto DOUBLE NOT NULL DEFAULT 0,
                referencia VARCHAR(255), fecha VARCHAR(30) NOT NULL,
                estado VARCHAR(50) NOT NULL DEFAULT 'Registrado')""",
            """CREATE TABLE IF NOT EXISTS prestamos (
                id INT AUTO_INCREMENT PRIMARY KEY, beneficiario VARCHAR(255) NOT NULL,
                concepto VARCHAR(255), monto DOUBLE DEFAULT 0, pagado DOUBLE DEFAULT 0,
                saldo DOUBLE DEFAULT 0, fecha VARCHAR(30), vencimiento VARCHAR(30),
                estado VARCHAR(50), notas TEXT)""",
            """CREATE TABLE IF NOT EXISTS nominas (
                id INT AUTO_INCREMENT PRIMARY KEY, empleado VARCHAR(255) NOT NULL,
                puesto VARCHAR(255), periodo VARCHAR(100), sueldo DOUBLE DEFAULT 0,
                bonos DOUBLE DEFAULT 0, deducciones DOUBLE DEFAULT 0, neto DOUBLE DEFAULT 0,
                fecha VARCHAR(30), estado VARCHAR(50), notas TEXT)""",
            """CREATE TABLE IF NOT EXISTS empacadora_ventas (
                id INT AUTO_INCREMENT PRIMARY KEY, fecha VARCHAR(30), cliente VARCHAR(255),
                folio VARCHAR(100), monto DOUBLE DEFAULT 0, lote VARCHAR(100))""",
        ]
    else:
        statements = [
            """CREATE TABLE IF NOT EXISTS abonos_mobile (
                id INTEGER PRIMARY KEY AUTOINCREMENT, persona TEXT NOT NULL,
                concepto TEXT NOT NULL, monto REAL NOT NULL DEFAULT 0,
                referencia TEXT, fecha TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'Registrado')""",
            """CREATE TABLE IF NOT EXISTS prestamos (
                id INTEGER PRIMARY KEY AUTOINCREMENT, beneficiario TEXT NOT NULL,
                concepto TEXT, monto REAL DEFAULT 0, pagado REAL DEFAULT 0,
                saldo REAL DEFAULT 0, fecha TEXT, vencimiento TEXT,
                estado TEXT, notas TEXT)""",
            """CREATE TABLE IF NOT EXISTS nominas (
                id INTEGER PRIMARY KEY AUTOINCREMENT, empleado TEXT NOT NULL,
                puesto TEXT, periodo TEXT, sueldo REAL DEFAULT 0,
                bonos REAL DEFAULT 0, deducciones REAL DEFAULT 0, neto REAL DEFAULT 0,
                fecha TEXT, estado TEXT, notas TEXT)""",
            """CREATE TABLE IF NOT EXISTS empacadora_ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, cliente TEXT,
                folio TEXT, monto REAL DEFAULT 0, lote TEXT)""",
        ]
    for statement in statements:
        conn.execute(statement)


def _dashboard(conn):
    today = date.today().isoformat()
    month = today[:7]
    sales_today = _scalar(conn, "SELECT COALESCE(SUM(total),0) FROM ventas WHERE fecha=?", (today,))
    movements = _scalar(conn, "SELECT COUNT(*) FROM ventas WHERE fecha=?", (today,))
    products = _scalar(conn, "SELECT COUNT(*) FROM articulos")
    low_stock = _scalar(conn, "SELECT COUNT(*) FROM articulos WHERE COALESCE(stock,0)<=5")
    clients = _scalar(conn, "SELECT COUNT(*) FROM clientes")
    pending = _scalar(
        conn,
        "SELECT COUNT(*) FROM pedidos_proveedor WHERE LOWER(COALESCE(estado,'')) NOT IN ('completado','recibido')",
    )
    purchases = _scalar(conn, "SELECT COALESCE(SUM(total),0) FROM compras WHERE fecha LIKE ?", (month + "%",))
    revenue = _scalar(conn, "SELECT COALESCE(SUM(total),0) FROM ventas WHERE fecha LIKE ?", (month + "%",))
    cost = _scalar(
        conn,
        "SELECT COALESCE(SUM(COALESCE(costo,0)*COALESCE(cantidad,0)),0) FROM ventas WHERE fecha LIKE ?",
        (month + "%",),
    )
    series = []
    for offset in range(6, -1, -1):
        day = (date.today() - timedelta(days=offset)).isoformat()
        series.append({"fecha": day[5:], "total": float(_scalar(conn, "SELECT COALESCE(SUM(total),0) FROM ventas WHERE fecha=?", (day,)))})
    return {
        "ventas_hoy": float(sales_today or 0),
        "movimientos": int(movements or 0),
        "productos": int(products or 0),
        "stock_bajo": int(low_stock or 0),
        "clientes": int(clients or 0),
        "pedidos_pendientes": int(pending or 0),
        "compras_mes": float(purchases or 0),
        "utilidad_estimada": float(revenue or 0) - float(cost or 0),
        "ventas_serie": series,
    }


@router.get("/dashboard")
def dashboard():
    conn = get_connection()
    try:
        return _dashboard(conn)
    finally:
        conn.close()


def _row_to_record(module, row):
    data = dict(row)
    if module == "prestamos":
        return {
            "id": data["id"],
            "title": data.get("beneficiario") or "Préstamo",
            "subtitle": data.get("concepto") or data.get("fecha") or "",
            "amount": float(data.get("saldo") or data.get("monto") or 0),
            "status": data.get("estado"),
            "metadata": {k: v for k, v in data.items() if v is not None},
        }
    if module == "nominas":
        return {
            "id": data["id"],
            "title": data.get("empleado") or "Nómina",
            "subtitle": " · ".join(filter(None, [data.get("puesto"), data.get("periodo")])),
            "amount": float(data.get("neto") or 0),
            "status": data.get("estado"),
            "metadata": {k: v for k, v in data.items() if v is not None},
        }
    if module == "abonos":
        return {
            "id": data["id"],
            "title": data.get("persona") or "Abono",
            "subtitle": data.get("concepto") or data.get("fecha") or "",
            "amount": float(data.get("monto") or 0),
            "status": data.get("estado"),
            "metadata": {k: v for k, v in data.items() if v is not None},
        }
    return {
        "id": data["id"],
        "title": data.get("cliente") or "Movimiento de empacadora",
        "subtitle": " · ".join(filter(None, [data.get("folio"), data.get("lote"), data.get("fecha")])),
        "amount": float(data.get("monto") or 0),
        "status": None,
        "metadata": {k: v for k, v in data.items() if v is not None},
    }


def _computed_module(module, conn):
    snapshot = _dashboard(conn)
    if module == "rendimiento":
        return {
            "title": "Rendimiento",
            "metrics": [
                {"label": "Ventas hoy", "value": f"${snapshot['ventas_hoy']:,.2f}"},
                {"label": "Utilidad estimada", "value": f"${snapshot['utilidad_estimada']:,.2f}"},
                {"label": "Compras del mes", "value": f"${snapshot['compras_mes']:,.2f}"},
                {"label": "Movimientos", "value": str(snapshot["movimientos"])},
            ],
            "items": [],
            "fields": [],
        }
    if module == "informacion":
        return {
            "title": "Información",
            "metrics": [
                {"label": "Productos", "value": str(snapshot["productos"])},
                {"label": "Clientes", "value": str(snapshot["clientes"])},
                {"label": "Pedidos pendientes", "value": str(snapshot["pedidos_pendientes"])},
                {"label": "Alertas de stock", "value": str(snapshot["stock_bajo"])},
            ],
            "items": [],
            "fields": [],
        }
    if module == "configuracion":
        rows = []
        try:
            rows = conn.execute("SELECT rowid AS id, clave, valor, descripcion FROM configuracion_sistema ORDER BY clave").fetchall()
        except Exception:
            pass
        return {
            "title": "Configuración",
            "metrics": [],
            "items": [
                {
                    "id": dict(row).get("id", index + 1),
                    "title": dict(row).get("clave", "Ajuste"),
                    "subtitle": str(dict(row).get("valor", "")),
                    "amount": None,
                    "status": None,
                    "metadata": dict(row),
                }
                for index, row in enumerate(rows)
            ],
            "fields": [],
        }
    raise HTTPException(status_code=404, detail="Módulo móvil no encontrado")


@router.get("/modules/{module}")
def get_module(module: str):
    conn = get_connection()
    try:
        _ensure_mobile_tables(conn)
        if module not in MODULES:
            return _computed_module(module, conn)
        config = MODULES[module]
        table = config["table"]
        if not table_exists(conn, table):
            items = []
        else:
            items = [_row_to_record(module, row) for row in conn.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 100").fetchall()]
        total = sum(float(item.get("amount") or 0) for item in items)
        metrics = [{"label": "Registros", "value": str(len(items))}, {"label": "Total", "value": f"${total:,.2f}"}]
        fields = [{"key": key, "label": label, "type": kind, "required": required} for key, label, kind, required in config["fields"]]
        return {"title": config["title"], "metrics": metrics, "items": items, "fields": fields}
    finally:
        conn.close()


def _number(value):
    try:
        return float(str(value or 0).replace(",", ""))
    except ValueError:
        return 0.0


@router.post("/modules/{module}", status_code=201)
def create_module_record(module: str, payload: dict):
    if module not in MODULES:
        raise HTTPException(status_code=405, detail="Este módulo es solo de consulta")
    values = {key: payload.get(key) for key, _, _, _ in MODULES[module]["fields"]}
    today = date.today().isoformat()
    with transaction() as conn:
        _ensure_mobile_tables(conn)
        if module == "prestamos":
            amount = _number(values["monto"])
            cursor = conn.execute(
                """INSERT INTO prestamos
                (beneficiario,concepto,monto,pagado,saldo,fecha,vencimiento,estado,notas)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (values["beneficiario"], values["concepto"], amount, 0, amount, today, values["vencimiento"], "Pendiente", values["notas"]),
            )
        elif module == "nominas":
            salary, bonus, deductions = _number(values["sueldo"]), _number(values["bonos"]), _number(values["deducciones"])
            cursor = conn.execute(
                """INSERT INTO nominas
                (empleado,puesto,periodo,sueldo,bonos,deducciones,neto,fecha,estado,notas)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (values["empleado"], values["puesto"], values["periodo"], salary, bonus, deductions, salary + bonus - deductions, today, "Pendiente", values["notas"]),
            )
        elif module == "abonos":
            cursor = conn.execute(
                "INSERT INTO abonos_mobile(persona,concepto,monto,referencia,fecha,estado) VALUES(?,?,?,?,?,'Registrado')",
                (values["persona"], values["concepto"], _number(values["monto"]), values["referencia"], today),
            )
        else:
            cursor = conn.execute(
                "INSERT INTO empacadora_ventas(fecha,cliente,folio,monto,lote) VALUES(?,?,?,?,?)",
                (today, values["cliente"], values["folio"], _number(values["monto"]), values["lote"]),
            )
        return {"id": int(cursor.lastrowid), "ok": True}


def _external_jelox(payload: JeloxIn):
    url = os.getenv("JELOX_STUDIO_API_URL", "").strip()
    if not url:
        return None
    body = json.dumps(
        {"message": payload.message, "context": {"module": payload.module, "username": payload.username}},
        ensure_ascii=False,
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = os.getenv("JELOX_STUDIO_API_KEY", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request(url, data=body, headers=headers, method="POST"), timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        answer = data.get("answer") or data.get("message") or data.get("output")
        if answer:
            return {"answer": str(answer), "suggestions": data.get("suggestions", []), "source": "jelox-studio"}
    except Exception:
        return None


@router.post("/jelox/chat")
def jelox_chat(payload: JeloxIn):
    external = _external_jelox(payload)
    if external:
        external["suggestions"] = external["suggestions"] or ["Resumen de ventas", "Revisar inventario", "Alertas importantes"]
        return external

    text = payload.message.lower()
    conn = get_connection()
    try:
        snapshot = _dashboard(conn)
        if any(word in text for word in ("stock", "inventario", "producto")):
            rows = conn.execute(
                "SELECT articulo,stock FROM articulos WHERE COALESCE(stock,0)<=5 ORDER BY stock,articulo LIMIT 8"
            ).fetchall()
            names = ", ".join(f"{dict(row).get('articulo')} ({dict(row).get('stock')})" for row in rows)
            answer = f"Hay {snapshot['stock_bajo']} productos con stock bajo." + (f" Los prioritarios son: {names}." if names else " No hay productos críticos.")
        elif any(word in text for word in ("venta", "ingreso", "factur")):
            answer = f"Hoy se registran {snapshot['movimientos']} movimientos por ${snapshot['ventas_hoy']:,.2f}. La utilidad estimada del mes es ${snapshot['utilidad_estimada']:,.2f}."
        elif any(word in text for word in ("pedido", "proveedor", "compra")):
            answer = f"Hay {snapshot['pedidos_pendientes']} pedidos pendientes y las compras del mes suman ${snapshot['compras_mes']:,.2f}."
        elif any(word in text for word in ("cliente", "clientes")):
            answer = f"Actualmente hay {snapshot['clientes']} clientes registrados. Puedes abrir Clientes para buscar, crear o actualizar su información."
        else:
            answer = (
                f"Resumen actual: ventas de hoy ${snapshot['ventas_hoy']:,.2f}, "
                f"{snapshot['stock_bajo']} alertas de stock y {snapshot['pedidos_pendientes']} pedidos pendientes. "
                "Puedo profundizar en ventas, inventario, compras, pedidos o clientes."
            )
        return {
            "answer": answer,
            "suggestions": ["¿Qué productos tienen poco stock?", "Resumen de ventas", "Pedidos pendientes"],
            "source": "jelox-local",
        }
    finally:
        conn.close()
