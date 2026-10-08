from fastapi import FastAPI

from migraciones import preparar_base_de_datos

# Importamos todos nuestros módulos de rutas
from routers import auth, clientes, barberos, servicios, citas, admin

# Crea las tablas o las actualiza a la última versión con Alembic (ver carpeta alembic/)
preparar_base_de_datos()

app = FastAPI(title="BarberFlow API")

# Conectamos las rutas a la aplicación principal
app.include_router(auth.router)
app.include_router(clientes.router)
app.include_router(barberos.router)
app.include_router(servicios.router)
app.include_router(citas.router)
app.include_router(admin.router)
