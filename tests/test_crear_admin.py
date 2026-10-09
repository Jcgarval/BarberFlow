"""Pruebas del script crear_admin.py: la única forma de crear administradores."""
import pytest

import crear_admin
from database import SessionLocal
from models import Cliente


def ejecutar(monkeypatch, argumentos, contrasena="clave-segura-123"):
    monkeypatch.setattr("sys.argv", ["crear_admin.py", *argumentos])
    monkeypatch.setattr("getpass.getpass", lambda *_: contrasena)
    crear_admin.main()


def usuario(email):
    db = SessionLocal()
    try:
        return db.query(Cliente).filter(Cliente.email == email).first()
    finally:
        db.close()


def test_crea_un_administrador_nuevo(client, monkeypatch):
    ejecutar(monkeypatch, ["Nuria Admin", "nuria@example.com"])
    creado = usuario("nuria@example.com")
    assert creado is not None and creado.rol == "admin"
    # y puede iniciar sesión con la contraseña elegida
    respuesta = client.post("/login", json={"email": "nuria@example.com", "password": "clave-segura-123"})
    assert respuesta.status_code == 200 and respuesta.json()["rol"] == "admin"


def test_asciende_a_un_usuario_existente_sin_cambiar_su_contrasena(client, ana, monkeypatch):
    ejecutar(monkeypatch, ["Ana", ana["email"]], contrasena="no-se-usa")
    assert usuario(ana["email"]).rol == "admin"
    assert client.post("/login", json={"email": ana["email"], "password": "clave1234"}).status_code == 200


def test_cambia_la_contrasena_de_un_usuario_existente(client, ana, monkeypatch):
    ejecutar(monkeypatch, ["Ana", ana["email"], "--cambiar-password"], contrasena="contrasena-nueva-456")
    assert usuario(ana["email"]).rol == "admin"
    assert client.post("/login", json={"email": ana["email"], "password": "contrasena-nueva-456"}).status_code == 200
    assert client.post("/login", json={"email": ana["email"], "password": "clave1234"}).status_code == 400


def test_no_cambia_la_contrasena_si_la_nueva_es_demasiado_corta(client, ana, monkeypatch):
    with pytest.raises(SystemExit):
        ejecutar(monkeypatch, ["Ana", ana["email"], "--cambiar-password"], contrasena="1234")
    assert client.post("/login", json={"email": ana["email"], "password": "clave1234"}).status_code == 200


def test_rechaza_contrasenas_demasiado_cortas(monkeypatch):
    with pytest.raises(SystemExit):
        ejecutar(monkeypatch, ["Corto", "corto@example.com"], contrasena="1234")
    assert usuario("corto@example.com") is None


def test_sin_los_argumentos_necesarios_muestra_la_ayuda_y_sale(monkeypatch):
    with pytest.raises(SystemExit):
        ejecutar(monkeypatch, ["solo-un-argumento"])