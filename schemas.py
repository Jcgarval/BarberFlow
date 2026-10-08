from typing import Annotated
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator
from datetime import datetime, date
from typing import Literal

# =========================================================
#                 ESQUEMAS PARA BARBEROS
# =========================================================
# Nombre sin espacios sobrantes, obligatorio y de longitud razonable
NombreCorto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]

class BarberoCreate(BaseModel):
    nombre: NombreCorto

class BarberoResponse(BaseModel):
    id: int
    nombre: str

    model_config = ConfigDict(from_attributes=True)


# =========================================================
#                 ESQUEMAS PARA CLIENTES
# =========================================================
class ClienteCreate(BaseModel):
    nombre: NombreCorto          # sin espacios sobrantes, de 1 a 60 caracteres
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validar_password(cls, valor: str) -> str:
        if len(valor) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        if len(valor.encode("utf-8")) > 72:  # límite de bcrypt
            raise ValueError("La contraseña es demasiado larga (máximo 72 bytes)")
        if not any(c.isalpha() for c in valor) or not any(c.isdigit() for c in valor):
            raise ValueError("La contraseña debe incluir al menos una letra y un número")
        return valor

class ClienteResponse(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    rol: str

    model_config = ConfigDict(from_attributes=True)


# =========================================================
#                 ESQUEMAS PARA SERVICIOS
# =========================================================
class ServicioCreate(BaseModel):
    nombre: NombreCorto
    duracion_minutos: int = Field(gt=0, le=480)   # entre 1 y 480 minutos
    precio: float = Field(ge=0, le=1000)

class ServicioResponse(BaseModel):
    id: int
    nombre: str
    duracion_minutos: int
    precio: float

    model_config = ConfigDict(from_attributes=True)


# =========================================================
#                   ESQUEMAS PARA CITAS
# =========================================================
class CitaCreate(BaseModel):
    cliente_id: int
    barbero_id: int
    servicio_id: int
    fecha_hora: datetime  # Pydantic convertirá el string ISO a datetime automáticamente

class BarberoInfo(BaseModel):
    nombre: str

class ServicioInfo(BaseModel):
    nombre: str

class CitaResponse(BaseModel):
    id: int
    cliente_id: int
    barbero_id: int
    servicio_id: int
    fecha_hora: datetime
    estado: str

    barbero: BarberoInfo
    servicio: ServicioInfo

    model_config = ConfigDict(from_attributes=True)

# =========================================================
#                 ESQUEMAS PARA LOGIN
# =========================================================
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# =========================================================
#            ESQUEMAS: ESTADOS Y DISPONIBILIDAD
# =========================================================
class EstadoUpdate(BaseModel):
    estado: Literal["pendiente", "confirmada", "completada", "cancelada"]

class DisponibilidadResponse(BaseModel):
    fecha: date
    barbero_id: int
    servicio_id: int
    duracion_minutos: int
    franjas: list[str]  # horas de inicio libres en formato "HH:MM"
