from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta

from database import get_db
from models import Cita, Cliente, Barbero, Servicio
from schemas import CitaCreate, CitaResponse

router = APIRouter(prefix="/citas", tags=["Citas"])

@router.post("/", response_model=CitaResponse)
def crear_cita(cita: CitaCreate, db: Session = Depends(get_db)):
    if cita.fecha_hora.hour < 9 or cita.fecha_hora.hour >= 20:
        raise HTTPException(status_code=400, detail="Esa hora no es válida. La barbería abre de 09:00 a 20:00.")

    cliente = db.query(Cliente).filter(Cliente.id == cita.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="El cliente especificado no existe")
    
    barbero = db.query(Barbero).filter(Barbero.id == cita.barbero_id).first()
    if not barbero:
        raise HTTPException(status_code=404, detail="El barbero especificado no existe")
    
    servicio = db.query(Servicio).filter(Servicio.id == cita.servicio_id).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="El servicio especificado no existe")
        
    hora_fin = cita.fecha_hora + timedelta(minutes=servicio.duracion_minutos)

    citas_barbero = db.query(Cita).filter(Cita.barbero_id == cita.barbero_id).all()
    for cita_existente in citas_barbero:
        servicio_existente = db.query(Servicio).filter(Servicio.id == cita_existente.servicio_id).first()
        hora_fin_existente = cita_existente.fecha_hora + timedelta(minutes=servicio_existente.duracion_minutos)

        if cita.fecha_hora < hora_fin_existente and hora_fin > cita_existente.fecha_hora:
            raise HTTPException(status_code=400, detail="El barbero ya tiene una cita ocupada en ese horario")

    nueva_cita = Cita(
        cliente_id=cita.cliente_id,
        barbero_id=cita.barbero_id,
        servicio_id=cita.servicio_id,
        fecha_hora=cita.fecha_hora,
    )
    db.add(nueva_cita)
    db.commit()
    db.refresh(nueva_cita)
    return nueva_cita

@router.get("/", response_model=list[CitaResponse])
def obtener_citas(barbero_id: int = None, cliente_id: int = None, db: Session = Depends(get_db)):
    query = db.query(Cita)
    if barbero_id is not None:
        query = query.filter(Cita.barbero_id == barbero_id)
    if cliente_id is not None:
        query = query.filter(Cita.cliente_id == cliente_id)
    return query.all()

@router.get("/{cita_id}", response_model=CitaResponse)
def obtener_cita(cita_id: int, db: Session = Depends(get_db)):
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return cita

@router.put("/{cita_id}", response_model=CitaResponse)
def actualizar_cita(cita_id: int, cita_actualizada: CitaCreate, db: Session = Depends(get_db)):
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    if not db.query(Cliente).filter(Cliente.id == cita_actualizada.cliente_id).first():
        raise HTTPException(status_code=404, detail="El cliente especificado no existe")
    if not db.query(Barbero).filter(Barbero.id == cita_actualizada.barbero_id).first():
        raise HTTPException(status_code=404, detail="El barbero especificado no existe")
    if not db.query(Servicio).filter(Servicio.id == cita_actualizada.servicio_id).first():
        raise HTTPException(status_code=404, detail="El servicio especificado no existe")

    cita.cliente_id = cita_actualizada.cliente_id
    cita.barbero_id = cita_actualizada.barbero_id
    cita.servicio_id = cita_actualizada.servicio_id
    cita.fecha_hora = cita_actualizada.fecha_hora
    
    db.commit()
    db.refresh(cita)
    return cita

@router.delete("/{cita_id}")
def eliminar_cita(cita_id: int, db: Session = Depends(get_db)):
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    db.delete(cita)
    db.commit()
    return {"mensaje": "Cita eliminada correctamente"}