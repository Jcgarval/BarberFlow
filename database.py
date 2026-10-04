from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os

# Por defecto usa el archivo local; las pruebas automáticas usan otra base temporal
SQLALCHEMY_DATABASE_URL = os.getenv("BARBERFLOW_DATABASE_URL", "sqlite:///./barberflow.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()