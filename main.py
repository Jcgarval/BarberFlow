from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta

# Nuevos imports de seguridad
import bcrypt
from jose import jwt

# 1. Importamos los modelos de la base de datos
from models import Base, Barbero, Cliente, Servicio, Cita
from schemas import (
    BarberoCreate, BarberoResponse,
    ClienteCreate, ClienteResponse,
    ServicioCreate, ServicioResponse,
    CitaCreate, CitaResponse,
    LoginRequest
)

# =========================================================
#       CONFIGURACIÓN DE SEGURIDAD Y TOKENS JWT
# =========================================================
SECRET_KEY = "tu_clave_secreta_super_segura"
ALGORITHM = "HS256"

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# =========================================================
#       CONFIGURACIÓN DE BASE DE DATOS SQLITE EN MAIN
# =========================================================
SQLALCHEMY_DATABASE_URL = "sqlite:///./barberflow.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="BarberFlow API")

# =========================================================
#               SISTEMA DE USUARIOS Y LOGIN
# =========================================================

@app.post("/clientes", response_model=ClienteResponse)
def crear_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    # 1. Comprobamos si el email ya existe
    cliente_existente = db.query(Cliente).filter(Cliente.email == cliente.email).first()
    if cliente_existente:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # 2. Encriptamos la contraseña
    hashed_pwd = get_password_hash(cliente.password)
    
    # 3. Guardamos el cliente con la contraseña cifrada
    nuevo_cliente = Cliente(
        nombre=cliente.nombre, 
        telefono=cliente.telefono,
        email=cliente.email,
        hashed_password=hashed_pwd,
        rol=cliente.rol
    )
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    return nuevo_cliente


@app.post("/login")
def login(credenciales: LoginRequest, db: Session = Depends(get_db)):
    # 1. Buscamos al usuario por su email
    cliente = db.query(Cliente).filter(Cliente.email == credenciales.email).first()
    if not cliente:
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
    
    # 2. Comprobamos que la contraseña coincide con la encriptada
    if not verify_password(credenciales.password, cliente.hashed_password):
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
        
    # 3. Generamos el Token JWT con su identidad y su rol
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


# =========================================================
#               CRUD COMPLETO DE BARBEROS (5 Rutas)
# =========================================================

@app.post("/barberos", response_model=BarberoResponse)
def crear_barbero(barbero: BarberoCreate, db: Session = Depends(get_db)):
    nuevo_barbero = Barbero(nombre=barbero.nombre)
    db.add(nuevo_barbero)
    db.commit()
    db.refresh(nuevo_barbero)
    return nuevo_barbero


@app.get("/barberos", response_model=list[BarberoResponse])
def obtener_barberos(db: Session = Depends(get_db)):
    return db.query(Barbero).all()


@app.get("/barberos/{barbero_id}", response_model=BarberoResponse)
def obtener_barbero(barbero_id: int, db: Session = Depends(get_db)):
    barbero = db.query(Barbero).filter(Barbero.id == barbero_id).first()
    if not barbero:
        raise HTTPException(status_code=404, detail="Barbero no encontrado")
    return barbero


@app.put("/barberos/{barbero_id}", response_model=BarberoResponse)
def actualizar_barbero(barbero_id: int, barbero_actualizado: BarberoCreate, db: Session = Depends(get_db)):
    barbero = db.query(Barbero).filter(Barbero.id == barbero_id).first()
    if not barbero:
        raise HTTPException(status_code=404, detail="Barbero no encontrado")
    
    barbero.nombre = barbero_actualizado.nombre
    db.commit()
    db.refresh(barbero)
    return barbero


@app.delete("/barberos/{barbero_id}")
def eliminar_barbero(barbero_id: int, db: Session = Depends(get_db)):
    barbero = db.query(Barbero).filter(Barbero.id == barbero_id).first()
    if not barbero:
        raise HTTPException(status_code=404, detail="Barbero no encontrado")
    
    db.delete(barbero)
    db.commit()
    return {"mensaje": "Barbero eliminado correctamente"}


# =========================================================
#               CRUD COMPLETO DE SERVICIOS (5 Rutas)
# =========================================================

@app.post("/servicios", response_model=ServicioResponse)
def crear_servicio(servicio: ServicioCreate, db: Session = Depends(get_db)):
    nuevo_servicio = Servicio(
        nombre=servicio.nombre,
        duracion_minutos=servicio.duracion_minutos,
        precio=servicio.precio
    )
    db.add(nuevo_servicio)
    db.commit()
    db.refresh(nuevo_servicio)
    return nuevo_servicio


@app.get("/servicios", response_model=list[ServicioResponse])
def obtener_servicios(db: Session = Depends(get_db)):
    return db.query(Servicio).all()


@app.get("/servicios/{servicio_id}", response_model=ServicioResponse)
def obtener_servicio(servicio_id: int, db: Session = Depends(get_db)):
    servicio = db.query(Servicio).filter(Servicio.id == servicio_id).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return servicio


@app.put("/servicios/{servicio_id}", response_model=ServicioResponse)
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


@app.delete("/servicios/{servicio_id}")
def eliminar_servicio(servicio_id: int, db: Session = Depends(get_db)):
    servicio = db.query(Servicio).filter(Servicio.id == servicio_id).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    
    db.delete(servicio)
    db.commit()
    return {"mensaje": "Servicio eliminado correctamente"}


# =========================================================
#                 CRUD COMPLETO DE CITAS (5 Rutas)
# =========================================================

@app.post("/citas", response_model=CitaResponse)
def crear_cita(cita: CitaCreate, db: Session = Depends(get_db)):
    # 0. Control de horario comercial
    if cita.fecha_hora.hour < 9 or cita.fecha_hora.hour >= 20:
        raise HTTPException(
            status_code=400,
            detail="Esa hora no es válida. La barbería abre de 09:00 a 20:00."
        )

    # 1. Validaciones defensivas de integridad relacional
    cliente = db.query(Cliente).filter(Cliente.id == cita.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="El cliente especificado no existe")
    
    barbero = db.query(Barbero).filter(Barbero.id == cita.barbero_id).first()
    if not barbero:
        raise HTTPException(status_code=404, detail="El barbero especificado no existe")
    
    servicio = db.query(Servicio).filter(Servicio.id == cita.servicio_id).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="El servicio especificado no existe")
        
    # Calculamos cuándo terminará este nuevo servicio
    hora_fin = cita.fecha_hora + timedelta(minutes=servicio.duracion_minutos)

    # 2. Lógica anti-solapes (Validación de horarios del barbero)
    citas_barbero = db.query(Cita).filter(Cita.barbero_id == cita.barbero_id).all()
    
    for cita_existente in citas_barbero:
        servicio_existente = db.query(Servicio).filter(Servicio.id == cita_existente.servicio_id).first()
        hora_fin_existente = cita_existente.fecha_hora + timedelta(minutes=servicio_existente.duracion_minutos)

        if cita.fecha_hora < hora_fin_existente and hora_fin > cita_existente.fecha_hora:
            raise HTTPException(
                status_code=400, 
                detail="El barbero ya tiene una cita ocupada en ese horario"
            )

    # 3. Creación limpia de la cita si pasa todos los filtros
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


@app.get("/citas", response_model=list[CitaResponse])
def obtener_citas(barbero_id: int = None, cliente_id: int = None, db: Session = Depends(get_db)):
    query = db.query(Cita)
    if barbero_id is not None:
        query = query.filter(Cita.barbero_id == barbero_id)
    if cliente_id is not None:
        query = query.filter(Cita.cliente_id == cliente_id)
    return query.all()


@app.get("/citas/{cita_id}", response_model=CitaResponse)
def obtener_cita(cita_id: int, db: Session = Depends(get_db)):
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return cita


@app.put("/citas/{cita_id}", response_model=CitaResponse)
def actualizar_cita(cita_id: int, cita_actualizada: CitaCreate, db: Session = Depends(get_db)):
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Validamos que los nuevos IDs existan en la base de datos
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


@app.delete("/citas/{cita_id}")
def eliminar_cita(cita_id: int, db: Session = Depends(get_db)):
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    db.delete(cita)
    db.commit()
    return {"mensaje": "Cita eliminada correctamente"}