from pydantic import BaseModel, EmailStr
from datetime import datetime

# =========================================================
#                 ESQUEMAS PARA BARBEROS
# =========================================================
class BarberoCreate(BaseModel):
    nombre: str

class BarberoResponse(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True


# =========================================================
#                 ESQUEMAS PARA CLIENTES
# =========================================================
class ClienteCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: str = "cliente"

class ClienteResponse(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    rol: str

    class Config:
        from_attributes = True


# =========================================================
#                 ESQUEMAS PARA SERVICIOS
# =========================================================
class ServicioCreate(BaseModel):
    nombre: str
    duracion_minutos: int
    precio: float

class ServicioResponse(BaseModel):
    id: int
    nombre: str
    duracion_minutos: int
    precio: float

    class Config:
        from_attributes = True


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

    barbero: BarberoInfo
    servicio: ServicioInfo

    class Config:
        from_attributes = True

# =========================================================
#                 ESQUEMAS PARA LOGIN
# =========================================================
class LoginRequest(BaseModel):
    email: EmailStr
    password: str