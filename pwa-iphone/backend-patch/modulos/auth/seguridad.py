"""Seguridad centralizada: identidad, Argon2id, MFA, sesiones y permisos."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import platform
import secrets
import socket
import sqlite3
import struct
import time
import urllib.request
import uuid
from datetime import datetime, timedelta
from pathlib import Path

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import InvalidHashError, VerifyMismatchError
except ImportError:  # Mensaje controlado; nunca degradar silenciosamente a un hash inseguro.
    PasswordHasher = None
    InvalidHashError = VerifyMismatchError = ValueError

def _database_path():
    configured_path = os.getenv("DATABASE_PATH", "").strip()
    if configured_path:
        return Path(configured_path).expanduser().resolve()
    return Path(__file__).resolve().parents[2] / "database.db"


DB_PATH = _database_path()
PH = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, salt_len=16) if PasswordHasher else None
MFA_ROLES = {
    "super", "administrador", "admin", "dueño", "dueno", "supervisor",
    "usuario", "vendedor", "compras", "almacen", "almacén",
}
ADMIN_UNLOCK_ROLES = {"super", "administrador", "admin", "dueño", "dueno"}
SESSION_IDLE_MINUTES = 15

PERMISSIONS = (
    "ventas.ver", "ventas.crear", "ventas.editar", "ventas.cancelar", "ventas.reimprimir", "ventas.descuentos",
    "caja.abrir", "caja.cerrar", "caja.retirar", "caja.movimientos",
    "inventario.consultar", "inventario.aumentar", "inventario.disminuir", "inventario.ajustar", "inventario.eliminar",
    "productos.crear", "productos.editar_precio", "productos.editar_costo", "productos.eliminar",
    "compras.crear", "compras.recibir", "compras.modificar", "compras.cancelar",
    "clientes.consultar", "clientes.crear", "clientes.editar", "clientes.exportar",
    "reportes.consultar", "reportes.imprimir", "reportes.pdf", "reportes.excel",
    "usuarios.crear", "usuarios.suspender", "usuarios.roles", "usuarios.passwords",
    "configuracion.empresa", "configuracion.impresoras", "configuracion.impuestos", "configuracion.servidor",
    "respaldos.crear", "respaldos.descargar", "respaldos.restaurar", "respaldos.eliminar",
)


class _ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc, tb):
        try:
            return super().__exit__(exc_type, exc, tb)
        finally:
            self.close()


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=20, factory=_ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def ensure_security_schema():
    with connect() as c:
        cols = {r[1] for r in c.execute("PRAGMA table_info(usuarios)")}
        additions = {
            "numero_empleado": "TEXT", "sucursal": "TEXT", "horario_inicio": "TEXT", "horario_fin": "TEXT",
            "estado": "TEXT NOT NULL DEFAULT 'activo'", "ultimo_acceso": "TEXT", "password_cambiada": "TEXT",
            "password_vence": "TEXT", "intentos_fallidos": "INTEGER NOT NULL DEFAULT 0", "bloqueado_hasta": "TEXT",
            "mfa_secret": "TEXT", "mfa_habilitado": "INTEGER NOT NULL DEFAULT 0", "telefono": "TEXT",
            "requiere_cambio_password": "INTEGER NOT NULL DEFAULT 0",
        }
        for name, definition in additions.items():
            if name not in cols:
                c.execute(f"ALTER TABLE usuarios ADD COLUMN {name} {definition}")
        c.executescript("""
        CREATE TABLE IF NOT EXISTS sesiones_usuario (
          id TEXT PRIMARY KEY, usuario_id INTEGER NOT NULL, dispositivo_id TEXT NOT NULL,
          inicio TEXT NOT NULL, ultima_actividad TEXT NOT NULL, expira TEXT NOT NULL,
          cerrada TEXT, motivo_cierre TEXT, ip TEXT,
          FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE);
        CREATE INDEX IF NOT EXISTS idx_sesiones_usuario_abiertas ON sesiones_usuario(usuario_id, cerrada);
        CREATE TABLE IF NOT EXISTS dispositivos_autorizados (
          id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL, dispositivo_id TEXT NOT NULL,
          nombre TEXT, autorizado INTEGER NOT NULL DEFAULT 1, creado TEXT NOT NULL, ultimo_uso TEXT,
          UNIQUE(usuario_id, dispositivo_id), FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS permisos_accion (
          id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL, permiso TEXT NOT NULL,
          permitido INTEGER NOT NULL DEFAULT 0, UNIQUE(usuario_id, permiso),
          FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS auditoria_seguridad (
          id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT NOT NULL, usuario_id INTEGER,
          evento TEXT NOT NULL, detalle TEXT, dispositivo_id TEXT, exito INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS confirmaciones_criticas (
          token TEXT PRIMARY KEY, usuario_id INTEGER NOT NULL, operacion TEXT NOT NULL,
          creado TEXT NOT NULL, expira TEXT NOT NULL, usado INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS dispositivos_mfa_confiables (
          id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL,
          token_hash TEXT NOT NULL, confiable_hasta TEXT NOT NULL,
          creado TEXT NOT NULL, ultimo_uso TEXT NOT NULL,
          UNIQUE(usuario_id, token_hash),
          FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE);
        """)
        now = datetime.now().isoformat(timespec="seconds")
        c.execute("UPDATE usuarios SET password_cambiada=COALESCE(password_cambiada, ?)", (now,))
        c.execute("UPDATE usuarios SET password_vence=COALESCE(password_vence, ?)", ((datetime.now()+timedelta(days=90)).isoformat(timespec="seconds"),))


def hash_password(password: str) -> str:
    if PH is None:
        raise RuntimeError("Falta instalar argon2-cffi; el sistema no usará un hash inseguro como reemplazo.")
    if len(password) < 10:
        raise ValueError("La contraseña debe tener al menos 10 caracteres.")
    return PH.hash(password)


def _verify_and_upgrade(stored: str, supplied: str):
    if stored.startswith("$argon2id$"):
        try:
            ok = PH.verify(stored, supplied) if PH is not None else False
            return ok, PH.hash(supplied) if ok and PH.check_needs_rehash(stored) else None
        except (VerifyMismatchError, InvalidHashError):
            return False, None
    # Compatibilidad de una sola vez con instalaciones anteriores.
    legacy_ok = hmac.compare_digest(stored, supplied) or hmac.compare_digest(stored, hashlib.sha256(supplied.encode()).hexdigest())
    # Se permite migrar claves antiguas cortas, pero se marca su cambio obligatorio.
    return legacy_ok, PH.hash(supplied) if legacy_ok and PH is not None else None


def device_id() -> str:
    raw = f"{platform.system()}|{platform.node()}|{uuid.getnode()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _audit(c, user_id, event, detail="", success=True):
    c.execute("INSERT INTO auditoria_seguridad(fecha,usuario_id,evento,detalle,dispositivo_id,exito) VALUES(?,?,?,?,?,?)",
              (datetime.now().isoformat(timespec="seconds"), user_id, event, detail, device_id(), int(success)))


def _schedule_allowed(user, now):
    start, end = user["horario_inicio"], user["horario_fin"]
    if not start or not end:
        return True
    current = now.strftime("%H:%M")
    return start <= current <= end if start <= end else (current >= start or current <= end)


def authenticate(username: str, password: str, otp: str | None = None, client_device_token: str | None = None):
    ensure_security_schema()
    now = datetime.now()
    with connect() as c:
        user = c.execute("SELECT * FROM usuarios WHERE lower(username)=lower(?)", (username.strip(),)).fetchone()
        if not user:
            _audit(c, None, "login_fallido", "usuario inexistente", False)
            return {"ok": False, "message": "Usuario o contraseña incorrectos."}
        estado = str(user["estado"] or "activo").strip().lower()
        if estado == "bloqueado":
            _audit(c, user["id"], "login_bloqueado", "requiere desbloqueo administrativo", False)
            return {
                "ok": False,
                "admin_unlock_required": True,
                "locked_username": user["username"],
                "message": "La cuenta está bloqueada. Solo un administrador puede desbloquearla con su contraseña.",
            }
        if estado != "activo":
            _audit(c, user["id"], "login_bloqueado", f"estado={user['estado']}", False)
            return {"ok": False, "message": "La cuenta no está activa. Contacta a un administrador."}
        if user["bloqueado_hasta"] and datetime.fromisoformat(user["bloqueado_hasta"]) > now:
            return {"ok": False, "message": f"Cuenta bloqueada temporalmente hasta {user['bloqueado_hasta']}."}
        if not _schedule_allowed(user, now):
            _audit(c, user["id"], "fuera_de_horario", "", False)
            return {"ok": False, "message": "Acceso fuera del horario autorizado."}
        ok, upgraded = _verify_and_upgrade(user["password"], password)
        if not ok:
            attempts = int(user["intentos_fallidos"] or 0) + 1
            bloqueado = attempts >= 5
            c.execute(
                "UPDATE usuarios SET intentos_fallidos=?, bloqueado_hasta=NULL, estado=? WHERE id=?",
                (attempts, "bloqueado" if bloqueado else "activo", user["id"]),
            )
            _audit(c, user["id"], "password_incorrecta", f"intentos={attempts}", False)
            if bloqueado:
                _audit(c, user["id"], "cuenta_bloqueada", "cinco intentos fallidos; requiere administrador", False)
                return {
                    "ok": False,
                    "admin_unlock_required": True,
                    "locked_username": user["username"],
                    "failed_attempts": attempts,
                    "remaining_attempts": 0,
                    "message": "Cuenta bloqueada después de 5 intentos fallidos. Solo un administrador puede desbloquearla.",
                }
            restantes = 5 - attempts
            return {
                "ok": False,
                "failed_attempts": attempts,
                "remaining_attempts": restantes,
                "message": f"Usuario o contraseña incorrectos. Quedan {restantes} intentos antes del bloqueo.",
            }
        # La migración del hash pertenece a la comprobación de contraseña,
        # nunca al segundo factor. Conserva la misma clave del usuario.
        if upgraded:
            c.execute(
                "UPDATE usuarios SET password=?, password_cambiada=?, requiere_cambio_password=? WHERE id=?",
                (upgraded, now.isoformat(timespec="seconds"), int(len(password) < 10), user["id"]),
            )
            upgraded = None
        dev = device_id()
        devices = c.execute("SELECT COUNT(*) FROM dispositivos_autorizados WHERE usuario_id=?", (user["id"],)).fetchone()[0]
        allowed = c.execute("SELECT autorizado FROM dispositivos_autorizados WHERE usuario_id=? AND dispositivo_id=?", (user["id"], dev)).fetchone()
        if devices and (not allowed or not allowed[0]):
            _audit(c, user["id"], "dispositivo_no_autorizado", "", False)
            return {"ok": False, "message": "Este equipo no está autorizado para esta cuenta."}
        token_hash = hashlib.sha256(str(client_device_token or "").encode("utf-8")).hexdigest() if client_device_token else None
        trusted_mfa = False
        if token_hash:
            trusted_row = c.execute(
                """
                SELECT confiable_hasta FROM dispositivos_mfa_confiables
                WHERE usuario_id=? AND token_hash=?
                """,
                (user["id"], token_hash),
            ).fetchone()
            if trusted_row:
                try:
                    trusted_mfa = datetime.fromisoformat(trusted_row["confiable_hasta"]) > now
                except (TypeError, ValueError):
                    trusted_mfa = False
                if not trusted_mfa:
                    c.execute(
                        "DELETE FROM dispositivos_mfa_confiables WHERE usuario_id=? AND token_hash=?",
                        (user["id"], token_hash),
                    )
        if str(user["rol"] or "").lower() in MFA_ROLES and not trusted_mfa:
            if not user["mfa_habilitado"]:
                return {"ok": False, "mfa_setup_required": True, "secret": new_mfa_secret(),
                        "user_id": user["id"], "message": "Esta cuenta debe activar la autenticación en dos pasos."}
            if not otp:
                return {"ok": False, "mfa_required": True, "message": "Ingresa tu código de autenticación."}
            if not verify_totp(user["mfa_secret"], otp):
                _audit(c, user["id"], "mfa_incorrecto", "", False)
                return {"ok": False, "mfa_required": True, "message": "Código de autenticación incorrecto."}
            if token_hash:
                trusted_until = now + timedelta(days=30)
                c.execute(
                    """
                    INSERT INTO dispositivos_mfa_confiables
                    (usuario_id, token_hash, confiable_hasta, creado, ultimo_uso)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(usuario_id, token_hash) DO UPDATE SET
                      confiable_hasta=excluded.confiable_hasta,
                      ultimo_uso=excluded.ultimo_uso
                    """,
                    (
                        user["id"],
                        token_hash,
                        trusted_until.isoformat(timespec="seconds"),
                        now.isoformat(timespec="seconds"),
                        now.isoformat(timespec="seconds"),
                    ),
                )
        elif trusted_mfa and token_hash:
            c.execute(
                """
                UPDATE dispositivos_mfa_confiables SET ultimo_uso=?
                WHERE usuario_id=? AND token_hash=?
                """,
                (now.isoformat(timespec="seconds"), user["id"], token_hash),
            )
        c.execute("UPDATE usuarios SET intentos_fallidos=0,bloqueado_hasta=NULL,ultimo_acceso=? WHERE id=?", (now.isoformat(timespec="seconds"), user["id"]))
        if not devices:
            c.execute("INSERT INTO dispositivos_autorizados(usuario_id,dispositivo_id,nombre,creado,ultimo_uso) VALUES(?,?,?,?,?)", (user["id"],dev,socket.gethostname(),now.isoformat(timespec="seconds"),now.isoformat(timespec="seconds")))
        else:
            c.execute("UPDATE dispositivos_autorizados SET ultimo_uso=? WHERE usuario_id=? AND dispositivo_id=?", (now.isoformat(timespec="seconds"),user["id"],dev))
        sid = secrets.token_urlsafe(32)
        expires = now + timedelta(hours=12)
        c.execute("INSERT INTO sesiones_usuario(id,usuario_id,dispositivo_id,inicio,ultima_actividad,expira,ip) VALUES(?,?,?,?,?,?,?)", (sid,user["id"],dev,now.isoformat(timespec="seconds"),now.isoformat(timespec="seconds"),expires.isoformat(timespec="seconds"),socket.gethostbyname(socket.gethostname())))
        _audit(c, user["id"], "login_exitoso")
        try:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS notificaciones_sistema (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    titulo TEXT NOT NULL,
                    mensaje TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    leida INTEGER DEFAULT 0,
                    clave TEXT UNIQUE
                )
                """
            )
            login_key = f"jelox-login-{user['id']}-{int(now.timestamp())}"
            c.execute(
                """
                INSERT OR IGNORE INTO notificaciones_sistema
                (tipo, titulo, mensaje, fecha, hora, clave)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "mensaje",
                    "JELOX · Nuevo inicio de sesión",
                    f"{user['username']} ingresó desde la app del iPhone.",
                    now.strftime("%d/%m/%Y"),
                    now.strftime("%H:%M"),
                    login_key,
                ),
            )
        except sqlite3.Error:
            pass
        result = {"ok": True, "username": user["username"], "user_id": user["id"], "role": user["rol"], "session_id": sid,
                  "password_expired": bool(user["password_vence"] and datetime.fromisoformat(user["password_vence"]) <= now)}
    notify_login(result)
    return result


def unlock_user_with_admin(locked_username: str, admin_username: str, admin_password: str):
    """Desbloquea una cuenta únicamente con credenciales de administrador."""
    ensure_security_schema()
    locked_username = str(locked_username or "").strip()
    admin_username = str(admin_username or "").strip()
    if not locked_username or not admin_username or not admin_password:
        return {"ok": False, "message": "Escribe el usuario y la contraseña del administrador."}

    with connect() as c:
        target = c.execute(
            "SELECT id,username,estado FROM usuarios WHERE lower(username)=lower(?)",
            (locked_username,),
        ).fetchone()
        admin = c.execute(
            "SELECT id,username,password,rol,estado FROM usuarios WHERE lower(username)=lower(?)",
            (admin_username,),
        ).fetchone()
        if not target:
            return {"ok": False, "message": "La cuenta bloqueada no existe."}
        if not admin:
            _audit(c, None, "desbloqueo_denegado", f"administrador inexistente; objetivo={locked_username}", False)
            return {"ok": False, "message": "Credenciales de administrador incorrectas."}

        rol = str(admin["rol"] or "").strip().lower()
        estado_admin = str(admin["estado"] or "activo").strip().lower()
        password_ok, upgraded = _verify_and_upgrade(admin["password"], admin_password)
        if rol not in ADMIN_UNLOCK_ROLES or estado_admin != "activo" or not password_ok:
            _audit(c, admin["id"], "desbloqueo_denegado", f"objetivo={locked_username}", False)
            return {"ok": False, "message": "Credenciales de administrador incorrectas o sin autorización."}

        if upgraded:
            c.execute("UPDATE usuarios SET password=? WHERE id=?", (upgraded, admin["id"]))
        c.execute(
            "UPDATE usuarios SET estado='activo', intentos_fallidos=0, bloqueado_hasta=NULL WHERE id=?",
            (target["id"],),
        )
        _audit(c, admin["id"], "cuenta_desbloqueada", f"objetivo={target['username']}", True)
        _audit(c, target["id"], "cuenta_desbloqueada", f"por={admin['username']}", True)
        return {"ok": True, "message": f"La cuenta {target['username']} fue desbloqueada correctamente."}


def touch_session(session_id):
    now = datetime.now()
    with connect() as c:
        s = c.execute("SELECT * FROM sesiones_usuario WHERE id=?", (session_id,)).fetchone()
        if not s or s["cerrada"] or datetime.fromisoformat(s["expira"]) <= now or datetime.fromisoformat(s["ultima_actividad"]) + timedelta(minutes=SESSION_IDLE_MINUTES) <= now:
            if s and not s["cerrada"]:
                c.execute("UPDATE sesiones_usuario SET cerrada=?,motivo_cierre='inactividad o expiracion' WHERE id=?", (now.isoformat(timespec="seconds"), session_id))
            return False
        c.execute("UPDATE sesiones_usuario SET ultima_actividad=? WHERE id=?", (now.isoformat(timespec="seconds"), session_id))
        return True


def close_session(session_id, reason="cierre de sesion"):
    with connect() as c:
        c.execute("UPDATE sesiones_usuario SET cerrada=?,motivo_cierre=? WHERE id=? AND cerrada IS NULL", (datetime.now().isoformat(timespec="seconds"), reason, session_id))


def change_password(user_id, current, new):
    with connect() as c:
        user = c.execute("SELECT password FROM usuarios WHERE id=?", (user_id,)).fetchone()
        if not user or not _verify_and_upgrade(user[0], current)[0]:
            return False
        now = datetime.now()
        c.execute("UPDATE usuarios SET password=?,password_cambiada=?,password_vence=?,requiere_cambio_password=0 WHERE id=?", (hash_password(new),now.isoformat(timespec="seconds"),(now+timedelta(days=90)).isoformat(timespec="seconds"),user_id))
        c.execute("UPDATE sesiones_usuario SET cerrada=?,motivo_cierre='cambio de contraseña' WHERE usuario_id=? AND cerrada IS NULL", (now.isoformat(timespec="seconds"),user_id))
        _audit(c,user_id,"password_cambiada")
        return True


def has_permission(username, permission):
    ensure_security_schema()
    with connect() as c:
        u = c.execute("SELECT id,rol FROM usuarios WHERE username=?", (username,)).fetchone()
        if not u:
            return False
        if str(u["rol"]).lower() in {"super", "dueño", "dueno"}:
            return True
        row = c.execute("SELECT permitido FROM permisos_accion WHERE usuario_id=? AND permiso=?", (u["id"],permission)).fetchone()
        return bool(row and row[0])


def set_permissions(user_id, values):
    unknown = set(values) - set(PERMISSIONS)
    if unknown:
        raise ValueError(f"Permisos desconocidos: {', '.join(sorted(unknown))}")
    with connect() as c:
        for permission, allowed in values.items():
            c.execute("INSERT INTO permisos_accion(usuario_id,permiso,permitido) VALUES(?,?,?) ON CONFLICT(usuario_id,permiso) DO UPDATE SET permitido=excluded.permitido", (user_id,permission,int(bool(allowed))))


def new_mfa_secret():
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def totp(secret, at=None):
    key = base64.b32decode(secret + "=" * ((8-len(secret)%8)%8), casefold=True)
    msg = struct.pack(">Q", int((at or time.time()) // 30))
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 15
    return str((struct.unpack(">I", digest[offset:offset+4])[0] & 0x7fffffff) % 1000000).zfill(6)


def verify_totp(secret, code):
    return bool(secret and code and any(hmac.compare_digest(totp(secret, time.time()+step*30), str(code).zfill(6)) for step in (-1,0,1)))


def enable_mfa(user_id, secret, code):
    if not verify_totp(secret, code):
        return False
    with connect() as c:
        c.execute("UPDATE usuarios SET mfa_secret=?,mfa_habilitado=1 WHERE id=?", (secret,user_id))
        _audit(c,user_id,"mfa_habilitado")
    return True


def request_critical_confirmation(user_id, operation):
    token = str(secrets.randbelow(900000)+100000)
    now = datetime.now()
    with connect() as c:
        c.execute("INSERT INTO confirmaciones_criticas(token,usuario_id,operacion,creado,expira) VALUES(?,?,?,?,?)", (hashlib.sha256(token.encode()).hexdigest(),user_id,operation,now.isoformat(timespec="seconds"),(now+timedelta(minutes=5)).isoformat(timespec="seconds")))
    return token


def confirm_critical(user_id, operation, token):
    digest = hashlib.sha256(str(token).encode()).hexdigest()
    with connect() as c:
        row = c.execute("SELECT expira,usado FROM confirmaciones_criticas WHERE token=? AND usuario_id=? AND operacion=?", (digest,user_id,operation)).fetchone()
        if not row or row[1] or datetime.fromisoformat(row[0]) < datetime.now():
            return False
        c.execute("UPDATE confirmaciones_criticas SET usado=1 WHERE token=?", (digest,))
        return True


def notify_login(info):
    url = os.getenv("CARNES_LUEVANOS_LOGIN_WEBHOOK", "").strip()
    if not url:
        return
    payload = json.dumps({"event":"login", "username":info["username"], "date":datetime.now().isoformat(), "device":socket.gethostname()}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(url,data=payload,headers={"Content-Type":"application/json"}), timeout=4).read()
    except Exception:
        pass


ensure_security_schema()
