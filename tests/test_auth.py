from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

import security


def registrar(client, **extra):
    cuerpo = {"nombre": "Ana", "email": "ana@example.com", "password": "clave1234"}
    cuerpo.update(extra)
    return client.post("/clientes/", json=cuerpo)


def test_registro_crea_un_cliente(client):
    respuesta = registrar(client)
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["rol"] == "cliente"
    assert datos["email"] == "ana@example.com"
    assert "password" not in datos and "hashed_password" not in datos


def test_registro_ignora_el_rol_enviado(client):
    """Nadie puede hacerse administrador desde el registro."""
    respuesta = registrar(client, rol="admin")
    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == "cliente"


def test_registro_con_email_repetido_falla(client):
    registrar(client)
    respuesta = registrar(client)
    assert respuesta.status_code == 400
    assert "registrado" in respuesta.json()["detail"]


def test_registro_con_email_invalido_falla(client):
    assert registrar(client, email="no-es-un-correo").status_code == 422


def test_login_correcto_devuelve_token_y_datos(client):
    registrar(client)
    respuesta = client.post("/login", json={"email": "ana@example.com", "password": "clave1234"})
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["token_type"] == "bearer"
    assert datos["access_token"]
    assert datos["rol"] == "cliente"
    assert datos["nombre"] == "Ana"


def test_login_con_contrasena_incorrecta_falla(client):
    registrar(client)
    respuesta = client.post("/login", json={"email": "ana@example.com", "password": "otra-clave"})
    assert respuesta.status_code == 400


def test_login_con_usuario_inexistente_falla(client):
    respuesta = client.post("/login", json={"email": "nadie@example.com", "password": "clave1234"})
    assert respuesta.status_code == 400


@pytest.mark.parametrize("ruta", ["/citas/", "/admin/citas/detalles", "/barberos/inactivos"])
def test_las_rutas_protegidas_exigen_token(client, ruta):
    assert client.get(ruta).status_code in (401, 403)


def test_un_token_manipulado_se_rechaza(client):
    respuesta = client.get("/citas/", headers={"Authorization": "Bearer abc.def.ghi"})
    assert respuesta.status_code == 401


def test_un_token_caducado_se_rechaza(client, ana):
    caducado = jwt.encode(
        {"sub": ana["email"], "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        security.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    respuesta = client.get("/citas/", headers={"Authorization": f"Bearer {caducado}"})
    assert respuesta.status_code == 401


def test_un_token_firmado_con_otra_clave_se_rechaza(client, ana):
    """Si alguien fabrica un token con una clave distinta, no sirve."""
    falso = jwt.encode(
        {"sub": ana["email"], "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "una-clave-que-no-es-la-del-servidor",
        algorithm=security.ALGORITHM,
    )
    respuesta = client.get("/citas/", headers={"Authorization": f"Bearer {falso}"})
    assert respuesta.status_code == 401


def test_un_cliente_no_puede_entrar_en_rutas_de_administrador(client, ana):
    assert client.get("/admin/citas/detalles", headers=ana["headers"]).status_code == 403


# ------------------------------------------------------------------ validación del registro
@pytest.mark.parametrize("password", [
    "corta1",                 # menos de 8 caracteres
    "solo-letras-largas",     # sin número
    "123456789",              # sin letra
    "        ",               # solo espacios
    "a1" * 40,                # 80 bytes: bcrypt no la admite
    "ñ" * 37 + "1",           # 38 caracteres pero 75 bytes
])
def test_registro_rechaza_contrasenas_no_validas(client, password):
    assert registrar(client, password=password).status_code == 422


def test_registro_acepta_una_contrasena_de_72_bytes(client):
    assert registrar(client, password="a1" * 36).status_code == 200


@pytest.mark.parametrize("nombre", ["", "   ", "x" * 61])
def test_registro_rechaza_nombres_no_validos(client, nombre):
    assert registrar(client, nombre=nombre).status_code == 422


def test_registro_guarda_el_nombre_sin_espacios_sobrantes(client):
    assert registrar(client, nombre="  Ana  ").json()["nombre"] == "Ana"
