from pydantic import BaseModel
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
    telefono: str

class ClienteResponse(BaseModel):
    id: int
    nombre: str
    telefono: str

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

class CitaResponse(BaseModel):
    id: int
    cliente_id: int
    barbero_id: int
    servicio_id: int
    fecha_hora: datetime

    class Config:
        from_attributes = True