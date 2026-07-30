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