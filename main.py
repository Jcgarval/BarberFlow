from fastapi import FastAPI
from database import engine
from models import Base

# Importamos todos nuestros módulos de rutas
from routers import auth, clientes, barberos, servicios, citas, admin

# Crea las tablas en la base de datos si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BarberFlow API")

# Conectamos las rutas a la aplicación principal
app.include_router(auth.router)
app.include_router(clientes.router)
app.include_router(barberos.router)
app.include_router(servicios.router)
app.include_router(citas.router)
app.include_router(admin.router)