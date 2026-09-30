from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Cita, Cliente, Barbero, Servicio
from security import verificar_admin

router = APIRouter(prefix="/admin", tags=["Administración"])

@router.get("/citas/detalles")
def obtener_citas_detalladas(db: Session = Depends(get_db), admin: Cliente = Depends(verificar_admin)):
    citas = db.query(Cita).all()
    resultado = []
    
    for cita in citas:
        cliente = db.query(Cliente).filter(Cliente.id == cita.cliente_id).first()
        barbero = db.query(Barbero).filter(Barbero.id == cita.barbero_id).first()
        servicio = db.query(Servicio).filter(Servicio.id == cita.servicio_id).first()
        
        fecha_str = cita.fecha_hora.isoformat() if hasattr(cita.fecha_hora, 'isoformat') else str(cita.fecha_hora)
        
        resultado.append({
            "id": cita.id,
            "fecha_hora": fecha_str,
            "cliente_nombre": cliente.nombre if cliente else "Desconocido",
            "barbero_nombre": barbero.nombre if barbero else "Desconocido",
            "servicio_nombre": servicio.nombre if servicio else "Desconocido"
        })
        
    return resultado