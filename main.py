from fastapi import FastAPI, Depends, HTTPException
from models import Barbero, Cliente, SessionLocal
from schemas import BarberoCreate, BarberoResponse, ClienteCreate, ClienteResponse, CitaCreate, CitaResponse

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def bienvenida():
    return {"mensaje": "Bienvenido a la API de BarberFlow"}

@app.post("/barberos")
def crear_barbero(barbero: BarberoCreate, db= Depends(get_db)):
    nuevo_barbero = Barbero(nombre=barbero.nombre)
    db.add(nuevo_barbero)
    db.commit()
    return dict(mensaje="Barbero creado exitosamente", barbero_id=nuevo_barbero.id)

@app.get("/barberos", response_model=list[BarberoResponse])
def obtener_barberos(db=Depends(get_db)):
    barberos = db.query(Barbero).all()
    return barberos

@app.get("/barberos/{barbero_id}", response_model=BarberoResponse)
def obtener_barbero(barbero_id: int, db=Depends(get_db)):
    barbero = db.query(Barbero).filter(Barbero.id == barbero_id).first()
    if barbero is None:
        raise HTTPException(status_code=404, detail="Barbero no encontrado")
    return barbero

@app.put("/barberos/{barbero_id}", response_model=BarberoResponse)
def actualizar_barbero(barbero_id: int, barbero_actualizado: BarberoCreate, db=Depends(get_db)):
    barbero = db.query(Barbero).filter(Barbero.id == barbero_id).first()
    if barbero is None:
        raise HTTPException(status_code=404, detail="Barbero no encontrado")
    barbero.nombre = barbero_actualizado.nombre
    db.commit()
    return barbero

@app.delete("/barberos/{barbero_id}")
def eliminar_barbero(barbero_id: int, db=Depends(get_db)):
    barbero = db.query(Barbero).filter(Barbero.id == barbero_id).first()
    if barbero is None:
        raise HTTPException(status_code=404, detail="Barbero no encontrado")
    db.delete(barbero)
    db.commit()
    return {"mensaje": "Barbero eliminado correctamente"}

@app.post("/clientes", response_model=ClienteResponse)
def crear_cliente(cliente: ClienteCreate, db=Depends(get_db)):
    nuevo_cliente = Cliente(nombre=cliente.nombre, telefono=cliente.telefono)
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)  # Refresh to get the generated ID
    return nuevo_cliente

@app.get("/clientes", response_model=list[ClienteResponse])
def obtener_clientes(db=Depends(get_db)):
    clientes = db.query(Cliente).all()
    return clientes

@app.get("/clientes/{cliente_id}", response_model=ClienteResponse)
def obtener_cliente(cliente_id: int, db=Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@app.put("/clientes/{cliente_id}", response_model=ClienteResponse)
def actualizar_cliente(cliente_id: int, cliente_actualizado: ClienteCreate, db=Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    cliente.nombre = cliente_actualizado.nombre
    cliente.telefono = cliente_actualizado.telefono
    db.commit()
    return cliente

@app.delete("/clientes/{cliente_id}")
def eliminar_cliente(cliente_id: int, db=Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    db.delete(cliente)
    db.commit()
    return {"mensaje": "Cliente eliminado correctamente"}

@app.post("/citas", response_model=CitaResponse)
def crear_cita(cita: CitaCreate, db=Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cita.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="El cliente especificado no existe")
    barbero = db.query(Barbero).filter(Barbero.id == cita.barbero_id).first()
    if not barbero:
        raise HTTPException(status_code=404, detail="El barbero especificado no existe")
    servicio = db.query(Servicio).filter(Servicio.id == cita.servicio_id).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="El servicio especificado no existe")
    nuevo_cita = Cita(
        cliente_id=cita.cliente_id,
        barbero_id=cita.barbero_id,
        servicio_id=cita.servicio_id,
        fecha_hora=datetime.fromisoformat(cita.fecha_hora)
    )
    db.add(nuevo_cita)
    db.commit()
    db.refresh(nuevo_cita)  # Refresh to get the generated ID
    return nuevo_cita

@app.get("/citas", response_model=list[CitaResponse])
def obtener_citas(db=Depends(get_db)):
    citas = db.query(Cita).all()
    return citas

@app.get("/citas/{cita_id}", response_model=CitaResponse)
def obtener_cita(cita_id: int, db=Depends(get_db)):
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if cita is None:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return cita

@app.put("/citas/{cita_id}", response_model=CitaResponse)
def actualizar_cita(cita_id: int, cita_actualizada: CitaCreate, db=Depends(get_db)):
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if cita is None:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    cita.cliente_id = cita_actualizada.cliente_id
    cita.barbero_id = cita_actualizada.barbero_id
    cita.servicio_id = cita_actualizada.servicio_id
    cita.fecha_hora = datetime.fromisoformat(cita_actualizada.fecha_hora)
    db.commit()
    return cita

@app.delete("/citas/{cita_id}")
def eliminar_cita(cita_id: int, db=Depends(get_db)):
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if cita is None:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    db.delete(cita)
    db.commit()
    return {"mensaje": "Cita eliminada correctamente"}