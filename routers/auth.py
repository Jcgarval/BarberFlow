from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

import correo
from database import get_db
from models import Cliente, CodigoRecuperacion
from schemas import LoginRequest, RestablecerPasswordRequest, SolicitudRecuperacion
from security import (
    create_access_token,
    generar_codigo_recuperacion,
    get_password_hash,
    hash_codigo_recuperacion,
    verificar_codigo_recuperacion,
    verify_password,
)

# Creamos el router para las rutas de autenticación
router = APIRouter(tags=["Auth"])

CADUCIDAD_CODIGO_MINUTOS = 15
MAX_INTENTOS_CODIGO = 5          # fallos permitidos antes de invalidar el código
ESPERA_ENTRE_CODIGOS_SEGUNDOS = 60

MENSAJE_SOLICITUD = (
    f"Si el correo está registrado, te hemos enviado un código de 6 dígitos "
    f"que caduca en {CADUCIDAD_CODIGO_MINUTOS} minutos."
)


def _ahora() -> datetime:
    """Hora UTC sin zona horaria (así se guardan las fechas de los códigos)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _codigo_invalido() -> HTTPException:
    # Mismo mensaje para "correo inexistente", "caducado", "usado" e "incorrecto": no da pistas
    return HTTPException(status_code=400, detail="Código incorrecto o caducado")


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


@router.post("/auth/olvide-password")
def olvide_password(
    datos: SolicitudRecuperacion,
    tareas: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Envía un código de 6 dígitos al correo. Responde siempre lo mismo, exista o no la cuenta,
    para que nadie pueda averiguar qué correos están registrados."""
    respuesta = {"mensaje": MENSAJE_SOLICITUD}
    ahora = _ahora()

    # Limpieza: los códigos ya caducados no se guardan más
    db.query(CodigoRecuperacion).filter(CodigoRecuperacion.expira_en < ahora).delete()
    db.commit()

    cliente = db.query(Cliente).filter(Cliente.email == datos.email).first()
    if cliente is None:
        return respuesta

    # Máximo un código por minuto y cuenta (evita llenar el buzón de alguien)
    reciente = (
        db.query(CodigoRecuperacion)
        .filter(
            CodigoRecuperacion.cliente_id == cliente.id,
            CodigoRecuperacion.creado_en > ahora - timedelta(seconds=ESPERA_ENTRE_CODIGOS_SEGUNDOS),
        )
        .first()
    )
    if reciente is not None:
        return respuesta

    # Un código nuevo anula los anteriores
    db.query(CodigoRecuperacion).filter(CodigoRecuperacion.cliente_id == cliente.id).delete()
    codigo = generar_codigo_recuperacion()
    db.add(
        CodigoRecuperacion(
            cliente_id=cliente.id,
            codigo_hash=hash_codigo_recuperacion(cliente.id, codigo),
            creado_en=ahora,
            expira_en=ahora + timedelta(minutes=CADUCIDAD_CODIGO_MINUTOS),
        )
    )
    db.commit()

    # El envío va en segundo plano: no retrasa la respuesta ni delata si la cuenta existe
    tareas.add_task(correo.enviar_codigo_recuperacion, cliente.email, codigo, CADUCIDAD_CODIGO_MINUTOS)
    return respuesta


@router.post("/auth/restablecer-password")
def restablecer_password(datos: RestablecerPasswordRequest, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.email == datos.email).first()
    if cliente is None:
        raise _codigo_invalido()

    registro = (
        db.query(CodigoRecuperacion)
        .filter(CodigoRecuperacion.cliente_id == cliente.id, CodigoRecuperacion.usado.is_(False))
        .order_by(CodigoRecuperacion.creado_en.desc())
        .first()
    )
    if registro is None or registro.expira_en < _ahora() or registro.intentos >= MAX_INTENTOS_CODIGO:
        raise _codigo_invalido()

    if not verificar_codigo_recuperacion(cliente.id, datos.codigo, registro.codigo_hash):
        registro.intentos += 1
        db.commit()
        raise _codigo_invalido()

    cliente.hashed_password = get_password_hash(datos.nueva_password)
    registro.usado = True
    db.commit()
    return {"mensaje": "Contraseña actualizada. Ya puedes iniciar sesión."}