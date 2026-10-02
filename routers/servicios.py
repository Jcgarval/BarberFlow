from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Servicio, Cliente, Cita
from schemas import ServicioCreate, ServicioResponse
from security import verificar_admin

router = APIRouter(prefix="/servicios", tags=["Servicios"])

@router.post("/", response_model=ServicioResponse)
def crear_servicio(servicio: ServicioCreate, db: Session = Depends(get_db), admin: Cliente = Depends(verificar_admin)):
    nuevo_servicio = Servicio(
        nombre=servicio.nombre,
        duracion_minutos=servicio.duracion_minutos,
        precio=servicio.precio
    )
    db.add(nuevo_servicio)
    db.commit()
    db.refresh(nuevo_servicio)
    return nuevo_servicio

@router.get("/", response_model=list[ServicioResponse])
def obtener_servicios(db: Session = Depends(get_db)):
    # Los servicios dados de baja (activo=False) no se ofrecen para reservar
    return db.query(Servicio).filter(Servicio.activo.is_not(False)).all()

@router.get("/{servicio_id}", response_model=ServicioResponse)
def obtener_servicio(servicio_id: int, db: Session = Depends(get_db)):
    servicio = db.query(Servicio).filter(Servicio.id == servicio_id).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return servicio

@router.put("/{servicio_id}", response_model=ServicioResponse)
def actualizar_servicio(servicio_id: int, servicio_actualizado: ServicioCreate, db: Session = Depends(get_db), admin: Cliente = Depends(verificar_admin)):
    servicio = db.query(Servicio).filter(Servicio.id == servicio_id).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    
    servicio.nombre = servicio_actualizado.nombre
    servicio.duracion_minutos = servicio_actualizado.duracion_minutos
    servicio.precio = servicio_actualizado.precio
    db.commit()
    db.refresh(servicio)
    return servicio

@router.delete("/{servicio_id}")
def eliminar_servicio(servicio_id: int, db: Session = Depends(get_db), admin: Cliente = Depends(verificar_admin)):
    servicio = db.query(Servicio).filter(Servicio.id == servicio_id).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    
    # Si el servicio tiene citas (aunque sean antiguas o canceladas) NO se borra:
    # se da de baja para que no se pueda reservar, pero el historial sigue mostrando su nombre.
    tiene_citas = db.query(Cita.id).filter(Cita.servicio_id == servicio_id).first() is not None
    if tiene_citas:
        servicio.activo = False
        db.commit()
        return {"mensaje": "El servicio tiene citas asociadas, así que se ha dado de baja en lugar de borrarse. El historial se conserva."}

    db.delete(servicio)
    db.commit()
    return {"mensaje": "Servicio eliminado correctamente"}