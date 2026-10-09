import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Cita, Cliente
from schemas import ClienteCreate, ClienteResponse, EliminarCuentaRequest
from security import get_password_hash, get_usuario_actual, verify_password

# Usamos prefix para no repetir "/clientes" en cada ruta
router = APIRouter(prefix="/clientes", tags=["Clientes"])

ESTADOS_ACTIVOS = ("pendiente", "confirmada")  # citas que todavía ocupan hueco


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


@router.delete("/me")
def eliminar_mi_cuenta(
    datos: EliminarCuentaRequest,
    db: Session = Depends(get_db),
    usuario: Cliente = Depends(get_usuario_actual),
):
    """Borra la cuenta del usuario que hace la petición.

    No se elimina la fila: se anonimizan sus datos personales para que el historial de citas
    siga existiendo (con cliente "Cliente eliminado") y las citas futuras se cancelan para liberar el hueco.
    """
    if usuario.rol == "admin":
        raise HTTPException(status_code=403, detail="Las cuentas de administrador no se pueden eliminar desde la app")

    # bcrypt no admite más de 72 bytes: una contraseña así nunca puede ser la correcta
    if len(datos.password.encode("utf-8")) > 72 or not verify_password(datos.password, usuario.hashed_password):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    futuras = (
        db.query(Cita)
        .filter(
            Cita.cliente_id == usuario.id,
            Cita.estado.in_(ESTADOS_ACTIVOS),
            Cita.fecha_hora >= datetime.now(),
        )
        .all()
    )
    for cita in futuras:
        cita.estado = "cancelada"

    usuario.nombre = "Cliente eliminado"
    # ".invalid" es un dominio reservado: nadie puede registrarlo ni iniciar sesión con él
    usuario.email = f"eliminado-{usuario.id}@anonimo.invalid"
    usuario.telefono = None
    # contraseña aleatoria que nadie conoce (y el email ya no existe, así que tampoco hay login posible)
    usuario.hashed_password = get_password_hash(secrets.token_urlsafe(32))
    db.commit()

    return {"mensaje": "Tu cuenta se ha eliminado. Tus datos personales se han borrado."}
