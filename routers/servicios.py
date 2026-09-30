from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Servicio, Cliente
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
    return db.query(Servicio).all()

@router.get("/{servicio_id}", response_model=ServicioResponse)
def obtener_servicio(servicio_id: int, db: Session = Depends(get_db)):
    servicio = db.query(Servicio).filter(Servicio.id == servicio_id).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return servicio

@router.put("/{servicio_id}", response_model=ServicioResponse)
def actualizar_servicio(servicio_id: int, servicio_actualizado: ServicioCreate, db: Session = Depends(get_db)):
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
def eliminar_servicio(servicio_id: int, db: Session = Depends(get_db)):
    servicio = db.query(Servicio).filter(Servicio.id == servicio_id).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    
    db.delete(servicio)
    db.commit()
    return {"mensaje": "Servicio eliminado correctamente"}