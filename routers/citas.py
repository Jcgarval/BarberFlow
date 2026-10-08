from datetime import datetime, date, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Cita, Cliente, Barbero, Servicio
from schemas import CitaCreate, CitaResponse, EstadoUpdate, DisponibilidadResponse
from security import get_usuario_actual

router = APIRouter(prefix="/citas", tags=["Citas"])

HORA_APERTURA = 9
HORA_CIERRE = 20
PASO_MINUTOS = 30  # las franjas se ofrecen cada 30 minutos
DURACION_POR_DEFECTO = 30  # por si el servicio de una cita antigua fue borrado
DIAS_CERRADO = {6}  # días en los que la barbería no abre (lunes=0 ... domingo=6)
LIMITE_POR_DEFECTO = 100  # citas que devuelve GET /citas/ si no se indica "limit"
LIMITE_MAXIMO = 200  # tope de "limit" para que nadie pida la tabla entera de golpe


# ---------------------------------------------------------
#                       AYUDAS
# ---------------------------------------------------------
def _es_admin(usuario: Cliente) -> bool:
    return usuario.rol == "admin"


def _obtener_cita_con_permiso(cita_id: int, usuario: Cliente, db: Session) -> Cita:
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    if not _es_admin(usuario) and cita.cliente_id != usuario.id:
        raise HTTPException(status_code=403, detail="Esta cita no es tuya")
    return cita


def _citas_activas_del_dia(db: Session, barbero_id: int, dia: date, excluir_id: int | None = None):
    """Devuelve [(inicio, fin)] de las citas NO canceladas del barbero ese día."""
    inicio_dia = datetime.combine(dia, time.min)
    fin_dia = inicio_dia + timedelta(days=1)

    query = (
        db.query(Cita, Servicio.duracion_minutos)
        .outerjoin(Servicio, Servicio.id == Cita.servicio_id)
        .filter(
            Cita.barbero_id == barbero_id,
            Cita.estado != "cancelada",
            Cita.fecha_hora >= inicio_dia,
            Cita.fecha_hora < fin_dia,
        )
    )
    if excluir_id is not None:
        query = query.filter(Cita.id != excluir_id)

    huecos = []
    for cita, duracion in query.all():
        duracion = duracion or DURACION_POR_DEFECTO
        huecos.append((cita.fecha_hora, cita.fecha_hora + timedelta(minutes=duracion)))
    return huecos


def _validar_horario(inicio: datetime, duracion: int):
    """Comprueba día de apertura, horario comercial (la cita entera debe caber) y que no sea en el pasado."""
    if inicio.weekday() in DIAS_CERRADO:
        raise HTTPException(status_code=400, detail="La barbería cierra los domingos")
    fin = inicio + timedelta(minutes=duracion)
    apertura = datetime.combine(inicio.date(), time(HORA_APERTURA))
    cierre = datetime.combine(inicio.date(), time(HORA_CIERRE))

    if inicio < apertura or fin > cierre:
        raise HTTPException(
            status_code=400,
            detail=f"La cita debe terminar dentro del horario de la barbería ({HORA_APERTURA:02d}:00 a {HORA_CIERRE:02d}:00).",
        )
    if inicio < datetime.now():
        raise HTTPException(status_code=400, detail="No se pueden pedir citas en el pasado")
    return fin


def _validar_sin_solape(db: Session, barbero_id: int, inicio: datetime, fin: datetime, excluir_id: int | None = None):
    for otro_inicio, otro_fin in _citas_activas_del_dia(db, barbero_id, inicio.date(), excluir_id):
        if inicio < otro_fin and fin > otro_inicio:
            raise HTTPException(status_code=400, detail="El barbero ya tiene una cita ocupada en ese horario")


def _comprobar_entidades(db: Session, cliente_id: int, barbero_id: int, servicio_id: int) -> Servicio:
    if not db.query(Cliente).filter(Cliente.id == cliente_id).first():
        raise HTTPException(status_code=404, detail="El cliente especificado no existe")
    barbero = db.query(Barbero).filter(Barbero.id == barbero_id).first()
    if not barbero:
        raise HTTPException(status_code=404, detail="El barbero especificado no existe")
    if barbero.activo is False:
        raise HTTPException(status_code=400, detail="Ese barbero no está disponible")
    servicio = db.query(Servicio).filter(Servicio.id == servicio_id).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="El servicio especificado no existe")
    if servicio.activo is False:
        raise HTTPException(status_code=400, detail="Ese servicio ya no está disponible")
    return servicio


# ---------------------------------------------------------
#                 DISPONIBILIDAD (franjas libres)
#   Debe ir ANTES de "/{cita_id}" para que no la confunda.
# ---------------------------------------------------------
@router.get("/disponibilidad", response_model=DisponibilidadResponse)
def obtener_disponibilidad(
    barbero_id: int,
    servicio_id: int,
    fecha: date,
    db: Session = Depends(get_db),
    usuario: Cliente = Depends(get_usuario_actual),
):
    barbero = db.query(Barbero).filter(Barbero.id == barbero_id).first()
    if not barbero:
        raise HTTPException(status_code=404, detail="El barbero especificado no existe")
    if barbero.activo is False:
        raise HTTPException(status_code=400, detail="Ese barbero no está disponible")
    servicio = db.query(Servicio).filter(Servicio.id == servicio_id).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="El servicio especificado no existe")
    if servicio.activo is False:
        raise HTTPException(status_code=400, detail="Ese servicio ya no está disponible")

    ocupados = _citas_activas_del_dia(db, barbero_id, fecha)
    cierre = datetime.combine(fecha, time(HORA_CIERRE))
    ahora = datetime.now()

    franjas = []
    inicio = datetime.combine(fecha, time(HORA_APERTURA))
    # En los días de cierre no se ofrece ninguna franja
    while fecha.weekday() not in DIAS_CERRADO and inicio + timedelta(minutes=servicio.duracion_minutos) <= cierre:
        fin = inicio + timedelta(minutes=servicio.duracion_minutos)
        libre = inicio > ahora and all(not (inicio < o_fin and fin > o_ini) for o_ini, o_fin in ocupados)
        if libre:
            franjas.append(inicio.strftime("%H:%M"))
        inicio += timedelta(minutes=PASO_MINUTOS)

    return DisponibilidadResponse(
        fecha=fecha,
        barbero_id=barbero_id,
        servicio_id=servicio_id,
        duracion_minutos=servicio.duracion_minutos,
        franjas=franjas,
    )


# ---------------------------------------------------------
#                          CRUD
# ---------------------------------------------------------
@router.post("/", response_model=CitaResponse)
def crear_cita(cita: CitaCreate, db: Session = Depends(get_db), usuario: Cliente = Depends(get_usuario_actual)):
    # Un cliente solo puede reservar a su nombre; el admin puede reservar para cualquiera.
    if not _es_admin(usuario) and cita.cliente_id != usuario.id:
        raise HTTPException(status_code=403, detail="Solo puedes reservar citas a tu nombre")

    servicio = _comprobar_entidades(db, cita.cliente_id, cita.barbero_id, cita.servicio_id)
    fin = _validar_horario(cita.fecha_hora, servicio.duracion_minutos)
    _validar_sin_solape(db, cita.barbero_id, cita.fecha_hora, fin)

    nueva_cita = Cita(
        cliente_id=cita.cliente_id,
        barbero_id=cita.barbero_id,
        servicio_id=cita.servicio_id,
        fecha_hora=cita.fecha_hora,
        estado="pendiente",
    )
    db.add(nueva_cita)
    db.commit()
    db.refresh(nueva_cita)
    return nueva_cita


@router.get("/", response_model=list[CitaResponse])
def obtener_citas(
    barbero_id: int | None = None,
    cliente_id: int | None = None,
    estado: str | None = None,
    skip: int = Query(0, ge=0, description="Citas que se saltan al principio de la lista"),
    limit: int = Query(LIMITE_POR_DEFECTO, ge=1, le=LIMITE_MAXIMO, description="Máximo de citas a devolver"),
    db: Session = Depends(get_db),
    usuario: Cliente = Depends(get_usuario_actual),
):
    if not _es_admin(usuario):
        if cliente_id is not None and cliente_id != usuario.id:
            raise HTTPException(status_code=403, detail="Solo puedes ver tus propias citas")
        cliente_id = usuario.id

    query = db.query(Cita)
    if barbero_id is not None:
        query = query.filter(Cita.barbero_id == barbero_id)
    if cliente_id is not None:
        query = query.filter(Cita.cliente_id == cliente_id)
    if estado is not None:
        query = query.filter(Cita.estado == estado)
    # Se ordena también por id para que dos citas a la misma hora no cambien de página entre peticiones
    return query.order_by(Cita.fecha_hora, Cita.id).offset(skip).limit(limit).all()


@router.get("/{cita_id}", response_model=CitaResponse)
def obtener_cita(cita_id: int, db: Session = Depends(get_db), usuario: Cliente = Depends(get_usuario_actual)):
    return _obtener_cita_con_permiso(cita_id, usuario, db)


@router.put("/{cita_id}", response_model=CitaResponse)
def actualizar_cita(
    cita_id: int,
    cita_actualizada: CitaCreate,
    db: Session = Depends(get_db),
    usuario: Cliente = Depends(get_usuario_actual),
):
    cita = _obtener_cita_con_permiso(cita_id, usuario, db)

    if not _es_admin(usuario) and cita_actualizada.cliente_id != usuario.id:
        raise HTTPException(status_code=403, detail="No puedes pasar la cita a otro cliente")

    servicio = _comprobar_entidades(
        db, cita_actualizada.cliente_id, cita_actualizada.barbero_id, cita_actualizada.servicio_id
    )
    fin = _validar_horario(cita_actualizada.fecha_hora, servicio.duracion_minutos)
    _validar_sin_solape(db, cita_actualizada.barbero_id, cita_actualizada.fecha_hora, fin, excluir_id=cita.id)

    cita.cliente_id = cita_actualizada.cliente_id
    cita.barbero_id = cita_actualizada.barbero_id
    cita.servicio_id = cita_actualizada.servicio_id
    cita.fecha_hora = cita_actualizada.fecha_hora

    db.commit()
    db.refresh(cita)
    return cita


@router.patch("/{cita_id}/estado", response_model=CitaResponse)
def cambiar_estado(
    cita_id: int,
    datos: EstadoUpdate,
    db: Session = Depends(get_db),
    usuario: Cliente = Depends(get_usuario_actual),
):
    cita = _obtener_cita_con_permiso(cita_id, usuario, db)

    if not _es_admin(usuario):
        # El cliente solo puede cancelar su propia cita, y solo si aún no se ha realizado.
        if datos.estado != "cancelada":
            raise HTTPException(status_code=403, detail="Solo puedes cancelar tus citas")
        if cita.estado == "completada":
            raise HTTPException(status_code=400, detail="Una cita completada no se puede cancelar")

    # Si se reactiva una cita cancelada, hay que comprobar que su hueco sigue libre.
    if cita.estado == "cancelada" and datos.estado != "cancelada":
        servicio = db.query(Servicio).filter(Servicio.id == cita.servicio_id).first()
        duracion = servicio.duracion_minutos if servicio else DURACION_POR_DEFECTO
        fin = cita.fecha_hora + timedelta(minutes=duracion)
        _validar_sin_solape(db, cita.barbero_id, cita.fecha_hora, fin, excluir_id=cita.id)

    cita.estado = datos.estado
    db.commit()
    db.refresh(cita)
    return cita


@router.delete("/{cita_id}")
def eliminar_cita(cita_id: int, db: Session = Depends(get_db), usuario: Cliente = Depends(get_usuario_actual)):
    cita = _obtener_cita_con_permiso(cita_id, usuario, db)
    db.delete(cita)
    db.commit()
    return {"mensaje": "Cita eliminada correctamente"}
