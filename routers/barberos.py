from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Barbero, Cliente, Cita
from schemas import BarberoCreate, BarberoResponse
from security import verificar_admin

router = APIRouter(prefix="/barberos", tags=["Barberos"])

@router.post("/", response_model=BarberoResponse)
def crear_barbero(barbero: BarberoCreate, db: Session = Depends(get_db), admin: Cliente = Depends(verificar_admin)):
    nuevo_barbero = Barbero(nombre=barbero.nombre)
    db.add(nuevo_barbero)
    db.commit()
    db.refresh(nuevo_barbero)
    return nuevo_barbero

@router.get("/", response_model=list[BarberoResponse])
def obtener_barberos(db: Session = Depends(get_db)):
    # Los barberos dados de baja (activo=False) no aparecen para reservar
    return db.query(Barbero).filter(Barbero.activo.is_not(False)).all()

@router.get("/inactivos", response_model=list[BarberoResponse])
def obtener_barberos_inactivos(db: Session = Depends(get_db), admin: Cliente = Depends(verificar_admin)):
    """Barberos dados de baja (solo admin). Va antes de '/{barbero_id}' para que no lo confunda con un id."""
    return db.query(Barbero).filter(Barbero.activo.is_(False)).all()

@router.get("/{barbero_id}", response_model=BarberoResponse)
def obtener_barbero(barbero_id: int, db: Session = Depends(get_db)):
    barbero = db.query(Barbero).filter(Barbero.id == barbero_id).first()
    if not barbero:
        raise HTTPException(status_code=404, detail="Barbero no encontrado")
    return barbero

@router.put("/{barbero_id}", response_model=BarberoResponse)
def actualizar_barbero(barbero_id: int, barbero_actualizado: BarberoCreate, db: Session = Depends(get_db), admin: Cliente = Depends(verificar_admin)):
    barbero = db.query(Barbero).filter(Barbero.id == barbero_id).first()
    if not barbero:
        raise HTTPException(status_code=404, detail="Barbero no encontrado")
    
    barbero.nombre = barbero_actualizado.nombre
    db.commit()
    db.refresh(barbero)
    return barbero

@router.post("/{barbero_id}/reactivar", response_model=BarberoResponse)
def reactivar_barbero(barbero_id: int, db: Session = Depends(get_db), admin: Cliente = Depends(verificar_admin)):
    barbero = db.query(Barbero).filter(Barbero.id == barbero_id).first()
    if not barbero:
        raise HTTPException(status_code=404, detail="Barbero no encontrado")
    barbero.activo = True
    db.commit()
    db.refresh(barbero)
    return barbero

@router.delete("/{barbero_id}")
def eliminar_barbero(barbero_id: int, db: Session = Depends(get_db), admin: Cliente = Depends(verificar_admin)):
    barbero = db.query(Barbero).filter(Barbero.id == barbero_id).first()
    if not barbero:
        raise HTTPException(status_code=404, detail="Barbero no encontrado")
    
    # Si el barbero tiene citas NO se borra: se da de baja y el historial conserva su nombre.
    tiene_citas = db.query(Cita.id).filter(Cita.barbero_id == barbero_id).first() is not None
    if tiene_citas:
        barbero.activo = False
        db.commit()
        return {"mensaje": "El barbero tiene citas asociadas, así que se ha dado de baja en lugar de borrarse. El historial se conserva."}

    db.delete(barbero)
    db.commit()
    return {"mensaje": "Barbero eliminado correctamente"}