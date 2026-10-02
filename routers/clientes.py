from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Cliente
from schemas import ClienteCreate, ClienteResponse
from security import get_password_hash

# Usamos prefix para no repetir "/clientes" en cada ruta
router = APIRouter(prefix="/clientes", tags=["Clientes"])

@router.post("/", response_model=ClienteResponse)
def crear_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    cliente_existente = db.query(Cliente).filter(Cliente.email == cliente.email).first()
    if cliente_existente:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    hashed_pwd = get_password_hash(cliente.password)
    
    nuevo_cliente = Cliente(
        nombre=cliente.nombre, 
        email=cliente.email,
        hashed_password=hashed_pwd,
        rol="cliente"  # el rol nunca se acepta desde fuera; los admins se crean con crear_admin.py
    )
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    return nuevo_cliente