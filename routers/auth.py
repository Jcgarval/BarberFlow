from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Cliente
from schemas import LoginRequest
from security import verify_password, create_access_token

# Creamos el router para las rutas de autenticación
router = APIRouter(tags=["Auth"])

@router.post("/login")
def login(credenciales: LoginRequest, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.email == credenciales.email).first()
    if not cliente:
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
    
    if not verify_password(credenciales.password, cliente.hashed_password):
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
        
    access_token = create_access_token(
        data={"sub": cliente.email, "rol": cliente.rol, "id": cliente.id}
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "rol": cliente.rol, 
        "id": cliente.id,
        "nombre": cliente.nombre
    }