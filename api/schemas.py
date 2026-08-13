from typing import Optional

from pydantic import BaseModel, Field


class ArticuloBase(BaseModel):
    codigo: Optional[str] = None
    articulo: str
    precio: float = Field(ge=0)
    costo: float = Field(ge=0)
    stock: int = Field(ge=0)
    estado: str = "activo"
    imagen_path: Optional[str] = None


class ArticuloUpdate(BaseModel):
    codigo: Optional[str] = None
    articulo: Optional[str] = None
    precio: Optional[float] = Field(default=None, ge=0)
    costo: Optional[float] = Field(default=None, ge=0)
    stock: Optional[int] = Field(default=None, ge=0)
    estado: Optional[str] = None
    imagen_path: Optional[str] = None


class ClienteBase(BaseModel):
    nombre: str
    cedula: Optional[str] = None
    celular: Optional[str] = None
    direccion: Optional[str] = None
    correo: Optional[str] = None


class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    cedula: Optional[str] = None
    celular: Optional[str] = None
    direccion: Optional[str] = None
    correo: Optional[str] = None


class ProveedorBase(BaseModel):
    empresa: str
    rif: str
    celular: Optional[str] = None
    direccion: Optional[str] = None
    correo: Optional[str] = None


class ProveedorUpdate(BaseModel):
    empresa: Optional[str] = None
    rif: Optional[str] = None
    celular: Optional[str] = None
    direccion: Optional[str] = None
    correo: Optional[str] = None


class PedidoDetalleIn(BaseModel):
    producto_codigo: str
    producto_nombre: str
    cantidad: int = Field(gt=0)
    precio_unitario: float = Field(default=0, ge=0)


class PedidoProveedorIn(BaseModel):
    proveedor_nombre: str
    observaciones: Optional[str] = None
    detalles: list[PedidoDetalleIn] = []


class VentaItemIn(BaseModel):
    codigo: Optional[str] = None
    producto: Optional[str] = None
    cantidad: int = Field(gt=0)


class VentaIn(BaseModel):
    cliente: Optional[str] = "Cliente General"
    items: list[VentaItemIn] = Field(min_length=1)


class LoginIn(BaseModel):
    username: str
    password: str
    otp: Optional[str] = None
    device_token: Optional[str] = None


class MfaEnableIn(BaseModel):
    user_id: int
    secret: str
    code: str


class UnlockAccountIn(BaseModel):
    locked_username: str
    admin_username: str
    admin_password: str


class CompraIn(BaseModel):
    proveedor: str
    factura: Optional[str] = None
    producto: str
    cantidad: int = Field(gt=0)
    costo_unitario: float = Field(ge=0)
    fecha: Optional[str] = None
    estado: str = "Registrada"
    notas: Optional[str] = None

class EventoSistemaIn(BaseModel):
    tipo: str
    titulo: str
    mensaje: str
    usuario: Optional[str] = None
    origen: Optional[str] = None
