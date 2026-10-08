from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os

# Por defecto usa el archivo local; las pruebas automáticas usan otra base temporal
# y en producción (Render + Neon) la URL llega por la variable de entorno.
SQLALCHEMY_DATABASE_URL = os.getenv("BARBERFLOW_DATABASE_URL", "sqlite:///./barberflow.db")

# Neon y otros servicios entregan la URL como "postgres://..." o "postgresql://...".
# SQLAlchemy necesita saber qué driver usar (psycopg 3), así que lo añadimos nosotros.
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://" + SQLALCHEMY_DATABASE_URL[len("postgres://"):]
elif SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
    SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://" + SQLALCHEMY_DATABASE_URL[len("postgresql://"):]

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # check_same_thread solo existe en SQLite
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # pool_pre_ping: comprueba que la conexión sigue viva antes de usarla (Neon duerme la base
    # tras un rato sin uso y cierra las conexiones); pool_recycle: renueva conexiones antiguas.
    engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, pool_recycle=300)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
