from fastapi import APIRouter, HTTPException

from ..database import get_connection, is_mysql, transaction
from ..schemas import LoginIn, MfaEnableIn, UnlockAccountIn


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/mfa/enable")
def mfa_enable(payload: MfaEnableIn):
    if is_mysql():
        raise HTTPException(status_code=503, detail="MFA no migrado en MySQL")
    from modulos.auth.seguridad import enable_mfa
    if not enable_mfa(payload.user_id, payload.secret, payload.code):
        raise HTTPException(status_code=400, detail="Codigo de autenticacion incorrecto")
    return {"ok": True}


@router.post("/login")
def login(payload: LoginIn):
    if is_mysql():
        raise HTTPException(status_code=503, detail="La autenticacion segura MySQL requiere ejecutar la migracion del servidor.")
    from modulos.auth.seguridad import authenticate
    result = authenticate(payload.username, payload.password, payload.otp, payload.device_token)
    if not result.get("ok"):
        if result.get("mfa_setup_required"):
            raise HTTPException(status_code=428, detail={"message": result["message"], "mfa_setup_required": True, "secret": result["secret"], "user_id": result["user_id"]})
        status = 428 if result.get("mfa_required") else 401
        raise HTTPException(status_code=status, detail=result)
    return {"id": result["user_id"], "username": result["username"], "session_id": result["session_id"], "role": result["role"]}


@router.post("/unlock")
def unlock_account(payload: UnlockAccountIn):
    if is_mysql():
        raise HTTPException(status_code=503, detail="El desbloqueo seguro MySQL requiere ejecutar la migracion del servidor.")
    from modulos.auth.seguridad import unlock_user_with_admin
    result = unlock_user_with_admin(
        payload.locked_username,
        payload.admin_username,
        payload.admin_password,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=403, detail=result)
    return result
