from fastapi import FastAPI
from sqlalchemy import inspect, text
from database import engine
from models import Base

# Importamos todos nuestros módulos de rutas
from routers import auth, clientes, barberos, servicios, citas, admin

# Crea las tablas en la base de datos si no existen
Base.metadata.create_all(bind=engine)

def migrar_columna_estado():
    """create_all no añade columnas a tablas que ya existen: la añadimos a mano si falta."""
    columnas = [c["name"] for c in inspect(engine).get_columns("citas")]
    if "estado" not in columnas:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE citas ADD COLUMN estado VARCHAR NOT NULL DEFAULT 'pendiente'"))

migrar_columna_estado()

app = FastAPI(title="BarberFlow API")

# Conectamos las rutas a la aplicación principal
app.include_router(auth.router)
app.include_router(clientes.router)
app.include_router(barberos.router)
app.include_router(servicios.router)
app.include_router(citas.router)
app.include_router(admin.router)