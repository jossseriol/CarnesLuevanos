import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException

from ..config import DATABASE_PATH
from ..database import get_connection, is_mysql, transaction
from ..schemas import LoginIn, MfaEnableIn, UnlockAccountIn

router = APIRouter(prefix="/auth", tags=["auth"])


def _security_module():
    from modulos.auth import seguridad

    if seguridad.DB_PATH.resolve() != DATABASE_PATH.resolve():
        raise HTTPException(
            status_code=503,
            detail="La base de usuarios no coincide con la base activa del sistema.",
        )
    return seguridad


@router.post("/mfa/enable")
def mfa_enable(payload: MfaEnableIn):
    if is_mysql():
        raise HTTPException(status_code=503, detail="MFA no migrado en MySQL")
    seguridad = _security_module()
    if not seguridad.enable_mfa(payload.user_id, payload.secret, payload.code):
        raise HTTPException(status_code=400, detail="Codigo de autenticacion incorrecto")
    return {"ok": True}


@router.post("/bootstrap-admin", status_code=201)
def bootstrap_admin(payload: dict):
    if not is_mysql():
        raise HTTPException(status_code=400, detail="Este endpoint es solo para MySQL")

    username = str(payload.get("username") or "admin").strip()
    password = str(payload.get("password") or "")
    nombre = str(payload.get("nombre") or "Administrador").strip()

    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Usuario invalido")

    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe tener al menos 8 caracteres",
        )

    from argon2 import PasswordHasher

    password_hash = PasswordHasher().hash(password)
    now = datetime.now()

    with transaction() as conn:
        existente = conn.execute(
            "SELECT id FROM usuarios LIMIT 1"
        ).fetchone()

        if existente:
            raise HTTPException(
                status_code=409,
                detail="Ya existe un usuario. Bootstrap deshabilitado.",
            )

        cursor = conn.execute(
            """
            INSERT INTO usuarios
            (
                username,
                password,
                nombre,
                rol,
                estado,
                password_cambiada,
                password_vence,
                intentos_fallidos,
                mfa_habilitado,
                requiere_cambio_password
            )
            VALUES (?, ?, ?, 'administrador', 'activo', ?, ?, 0, 0, 0)
            """,
            (
                username,
                password_hash,
                nombre,
                now.isoformat(timespec="seconds"),
                (now + timedelta(days=90)).isoformat(timespec="seconds"),
            ),
        )

        return {
            "id": int(cursor.lastrowid),
            "username": username,
            "role": "administrador",
        }




@router.post("/login")
def login(payload: LoginIn):
    if not is_mysql():
        seguridad = _security_module()
        result = seguridad.authenticate(
            payload.username,
            payload.password,
            payload.otp,
            payload.device_token,
        )

        if not result.get("ok"):
            if result.get("mfa_setup_required"):
                raise HTTPException(
                    status_code=428,
                    detail={
                        "message": result["message"],
                        "mfa_setup_required": True,
                        "secret": result["secret"],
                        "user_id": result["user_id"],
                    },
                )

            status = 428 if result.get("mfa_required") else 401
            raise HTTPException(status_code=status, detail=result)

        return {
            "id": result["user_id"],
            "username": result["username"],
            "session_id": result["session_id"],
            "role": result["role"],
        }

    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, VerificationError

    conn = get_connection()

    try:
        user = conn.execute(
            """
            SELECT *
            FROM usuarios
            WHERE LOWER(username) = LOWER(?)
            LIMIT 1
            """,
            (payload.username.strip(),),
        ).fetchone()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Usuario o contraseña incorrectos",
            )

        if str(user.get("estado") or "activo").lower() != "activo":
            raise HTTPException(
                status_code=403,
                detail="La cuenta no esta activa",
            )

        ph = PasswordHasher()

        try:
            ph.verify(user["password"], payload.password)
        except (VerifyMismatchError, VerificationError):
            raise HTTPException(
                status_code=401,
                detail="Usuario o contraseña incorrectos",
            )

        now = datetime.now()
        session_id = secrets.token_urlsafe(32)
        expires = now + timedelta(hours=12)

        conn.execute(
            """
            INSERT INTO sesiones_usuario
            (
                id,
                usuario_id,
                dispositivo_id,
                inicio,
                ultima_actividad,
                expira,
                ip
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                user["id"],
                payload.device_token or "mobile",
                now.isoformat(timespec="seconds"),
                now.isoformat(timespec="seconds"),
                expires.isoformat(timespec="seconds"),
                None,
            ),
        )

        conn.execute(
            """
            UPDATE usuarios
            SET ultimo_acceso = ?,
                intentos_fallidos = 0,
                bloqueado_hasta = NULL
            WHERE id = ?
            """,
            (
                now.isoformat(timespec="seconds"),
                user["id"],
            ),
        )

        conn.commit()

        return {
            "id": user["id"],
            "username": user["username"],
            "session_id": session_id,
            "role": user["rol"],
        }

    finally:
        conn.close()


@router.post("/unlock")
def unlock_account(payload: UnlockAccountIn):
    if is_mysql():
        raise HTTPException(status_code=503, detail="El desbloqueo seguro MySQL requiere ejecutar la migracion del servidor.")
    seguridad = _security_module()
    result = seguridad.unlock_user_with_admin(
        payload.locked_username,
        payload.admin_username,
        payload.admin_password,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=403, detail=result)
    return result
