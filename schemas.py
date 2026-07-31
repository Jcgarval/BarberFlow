from pydantic import BaseModel

class BarberoCreate(BaseModel):
    nombre: str

class BarberoResponse(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True

class ClienteCreate(BaseModel):
    nombre: str
    telefono: str

class ClienteResponse(BaseModel):
    id: int
    nombre: str
    telefono: str

    class Config:
        from_attributes = True

class CitaCreate(BaseModel):
    cliente_id: int
    barbero_id: int
    servicio_id: int
    fecha_hora: str  # Use string for datetime representation

class CitaResponse(BaseModel):
    id: int
    cliente_id: int
    barbero_id: int
    servicio_id: int
    fecha_hora: str  # Use string for datetime representation

    class Config:
        from_attributes = True