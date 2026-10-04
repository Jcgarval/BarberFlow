"""Configuración común de las pruebas.

Las pruebas usan una base de datos SQLite temporal y una clave secreta propia,
así que nunca tocan `barberflow.db` ni crean el archivo `.secret_key`.
"""
import os
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

# --- Entorno aislado: debe configurarse ANTES de importar la aplicación ---
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
_CARPETA_TEMPORAL = tempfile.mkdtemp(prefix="barberflow_pruebas_")
os.environ["BARBERFLOW_DATABASE_URL"] = f"sqlite:///{_CARPETA_TEMPORAL}/pruebas.db"
os.environ["BARBERFLOW_SECRET_KEY"] = "clave-solo-para-las-pruebas"
os.environ["BARBERFLOW_BCRYPT_ROUNDS"] = "4"  # mínimo de bcrypt: las pruebas van mucho más rápido

import pytest
from fastapi.testclient import TestClient

import main
from database import SessionLocal, engine
from models import Base, Cliente
from security import get_password_hash


@pytest.fixture(autouse=True)
def base_de_datos_limpia():
    """Cada prueba empieza con las tablas vacías."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="session")
def client():
    return TestClient(main.app)


# ---------------------------------------------------------------- usuarios
@pytest.fixture
def crear_usuario(client):
    """Crea un usuario directamente en la base de datos e inicia sesión con él."""
    def _crear(nombre="Ana", email="ana@example.com", password="clave1234", rol="cliente"):
        db = SessionLocal()
        try:
            usuario = Cliente(nombre=nombre, email=email, hashed_password=get_password_hash(password), rol=rol)
            db.add(usuario)
            db.commit()
            db.refresh(usuario)
            usuario_id = usuario.id
        finally:
            db.close()
        respuesta = client.post("/login", json={"email": email, "password": password})
        assert respuesta.status_code == 200, respuesta.text
        return {
            "id": usuario_id,
            "email": email,
            "headers": {"Authorization": f"Bearer {respuesta.json()['access_token']}"},
        }
    return _crear


@pytest.fixture
def admin(crear_usuario):
    return crear_usuario("Admin", "admin@example.com", rol="admin")


@pytest.fixture
def ana(crear_usuario):
    return crear_usuario("Ana", "ana@example.com")


@pytest.fixture
def beto(crear_usuario):
    return crear_usuario("Beto", "beto@example.com")


# ---------------------------------------------------------------- catálogo
@pytest.fixture
def catalogo(client, admin):
    """Un barbero y dos servicios (30 y 60 minutos)."""
    barbero = client.post("/barberos/", json={"nombre": "Carlos"}, headers=admin["headers"]).json()
    corte = client.post(
        "/servicios/", json={"nombre": "Corte", "duracion_minutos": 30, "precio": 12}, headers=admin["headers"]
    ).json()
    corte_barba = client.post(
        "/servicios/", json={"nombre": "Corte y barba", "duracion_minutos": 60, "precio": 20}, headers=admin["headers"]
    ).json()
    return {"barbero": barbero, "corte": corte, "corte_barba": corte_barba}


# ---------------------------------------------------------------- fechas
@pytest.fixture
def dia_laborable():
    """Un día futuro que no es domingo (mañana, o pasado mañana si mañana es domingo)."""
    dia = date.today() + timedelta(days=1)
    if dia.weekday() == 6:
        dia += timedelta(days=1)
    return dia


@pytest.fixture
def proximo_domingo():
    dia = date.today() + timedelta(days=1)
    while dia.weekday() != 6:
        dia += timedelta(days=1)
    return dia


@pytest.fixture
def a_las():
    """a_las(dia, 10, 30) -> '2026-10-05T10:30:00'"""
    def _a_las(dia, hora, minuto=0):
        return datetime(dia.year, dia.month, dia.day, hora, minuto).isoformat()
    return _a_las


# ---------------------------------------------------------------- citas
@pytest.fixture
def reservar(client, catalogo, a_las):
    """reservar(usuario, dia, 10, servicio='corte') -> respuesta de POST /citas/"""
    def _reservar(usuario, dia, hora, minuto=0, *, servicio="corte", cliente_id=None, headers=None):
        cuerpo = {
            "cliente_id": cliente_id if cliente_id is not None else usuario["id"],
            "barbero_id": catalogo["barbero"]["id"],
            "servicio_id": catalogo[servicio]["id"],
            "fecha_hora": a_las(dia, hora, minuto),
        }
        return client.post("/citas/", json=cuerpo, headers=headers or usuario["headers"])
    return _reservar


@pytest.fixture
def franjas(client, catalogo):
    """franjas(usuario, dia, servicio='corte') -> lista de horas libres 'HH:MM'"""
    def _franjas(usuario, dia, servicio="corte"):
        respuesta = client.get(
            "/citas/disponibilidad",
            params={"barbero_id": catalogo["barbero"]["id"], "servicio_id": catalogo[servicio]["id"], "fecha": dia.isoformat()},
            headers=usuario["headers"],
        )
        assert respuesta.status_code == 200, respuesta.text
        return respuesta.json()["franjas"]
    return _franjas
