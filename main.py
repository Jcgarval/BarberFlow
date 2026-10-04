from fastapi import FastAPI
from sqlalchemy import inspect, text
from database import engine
from models import Base

# Importamos todos nuestros módulos de rutas
from routers import auth, clientes, barberos, servicios, citas, admin

# Crea las tablas en la base de datos si no existen
Base.metadata.create_all(bind=engine)

def migrar_columnas(motor=engine):
    """create_all no añade columnas a tablas que ya existen: las añadimos a mano si faltan."""
    nuevas = [
        ("citas", "estado", "VARCHAR NOT NULL DEFAULT 'pendiente'"),
        ("servicios", "activo", "BOOLEAN NOT NULL DEFAULT 1"),
    ]
    inspector = inspect(motor)
    for tabla, columna, definicion in nuevas:
        existentes = [c["name"] for c in inspector.get_columns(tabla)]
        if columna not in existentes:
            with motor.begin() as conn:
                conn.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}"))

migrar_columnas()

app = FastAPI(title="BarberFlow API")

# Conectamos las rutas a la aplicación principal
app.include_router(auth.router)
app.include_router(clientes.router)
app.include_router(barberos.router)
app.include_router(servicios.router)
app.include_router(citas.router)
app.include_router(admin.router)