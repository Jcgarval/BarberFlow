"""Pruebas de la recuperación de contraseña por correo (código de 6 dígitos) y del envío con Brevo."""
import logging
from datetime import datetime, timedelta, timezone

import httpx
import pytest

import correo
from database import SessionLocal
from models import CodigoRecuperacion


def ahora():
    return datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture
def correos(monkeypatch):
    """Sustituye el envío real y apunta a qué correo y código se habrían enviado."""
    enviados = []
    monkeypatch.setattr(
        correo,
        "enviar_codigo_recuperacion",
        lambda destino, codigo, minutos: enviados.append({"destino": destino, "codigo": codigo}),
    )
    return enviados


def pedir(client, email="ana@example.com"):
    return client.post("/auth/olvide-password", json={"email": email})


def restablecer(client, codigo, password="nueva1234", email="ana@example.com"):
    return client.post(
        "/auth/restablecer-password",
        json={"email": email, "codigo": codigo, "nueva_password": password},
    )


def login(client, password, email="ana@example.com"):
    return client.post("/login", json={"email": email, "password": password})


def cambiar_registro(**cambios):
    db = SessionLocal()
    try:
        registro = db.query(CodigoRecuperacion).one()
        for campo, valor in cambios.items():
            setattr(registro, campo, valor)
        db.commit()
    finally:
        db.close()


def otro_codigo(codigo):
    return "000000" if codigo != "000000" else "111111"


# ------------------------------------------------------------------ pedir el código
def test_pedir_el_codigo_envia_6_digitos_al_correo(client, ana, correos):
    assert pedir(client).status_code == 200
    assert len(correos) == 1
    assert correos[0]["destino"] == "ana@example.com"
    assert len(correos[0]["codigo"]) == 6 and correos[0]["codigo"].isdigit()


def test_no_se_revela_si_el_correo_existe(client, ana, correos):
    existe = pedir(client)
    no_existe = pedir(client, "nadie@example.com")
    assert existe.status_code == no_existe.status_code == 200
    assert existe.json() == no_existe.json()
    assert [c["destino"] for c in correos] == ["ana@example.com"]


def test_el_codigo_no_se_guarda_en_claro(client, ana, correos):
    pedir(client)
    db = SessionLocal()
    try:
        registro = db.query(CodigoRecuperacion).one()
        assert registro.codigo_hash != correos[0]["codigo"]
        assert len(registro.codigo_hash) == 64  # SHA-256 en hexadecimal
    finally:
        db.close()


def test_un_correo_con_formato_invalido_se_rechaza(client):
    assert pedir(client, "no-es-un-correo").status_code == 422


def test_no_se_envian_dos_codigos_en_menos_de_un_minuto(client, ana, correos):
    pedir(client)
    pedir(client)
    assert len(correos) == 1


def test_un_codigo_nuevo_anula_el_anterior(client, ana, correos):
    pedir(client)
    cambiar_registro(creado_en=ahora() - timedelta(seconds=61))  # ya ha pasado el minuto de espera
    pedir(client)
    assert len(correos) == 2
    primero, segundo = correos[0]["codigo"], correos[1]["codigo"]
    if primero != segundo:  # (1 entre un millón: coincidirían por azar)
        assert restablecer(client, primero).status_code == 400
    assert restablecer(client, segundo).status_code == 200


# ------------------------------------------------------------------ restablecer la contraseña
def test_con_el_codigo_correcto_se_cambia_la_contrasena(client, ana, correos):
    pedir(client)
    assert restablecer(client, correos[0]["codigo"]).status_code == 200
    assert login(client, "nueva1234").status_code == 200
    assert login(client, "clave1234").status_code == 400


def test_el_codigo_solo_sirve_una_vez(client, ana, correos):
    pedir(client)
    codigo = correos[0]["codigo"]
    assert restablecer(client, codigo).status_code == 200
    assert restablecer(client, codigo, password="otra12345").status_code == 400
    assert login(client, "nueva1234").status_code == 200


def test_un_codigo_incorrecto_se_rechaza_sin_cambiar_nada(client, ana, correos):
    pedir(client)
    respuesta = restablecer(client, otro_codigo(correos[0]["codigo"]))
    assert respuesta.status_code == 400
    assert "incorrecto o caducado" in respuesta.json()["detail"]
    assert login(client, "clave1234").status_code == 200


def test_tras_5_fallos_el_codigo_deja_de_valer_aunque_sea_el_correcto(client, ana, correos):
    pedir(client)
    codigo = correos[0]["codigo"]
    for _ in range(5):
        assert restablecer(client, otro_codigo(codigo)).status_code == 400
    assert restablecer(client, codigo).status_code == 400
    assert login(client, "clave1234").status_code == 200


def test_un_codigo_caducado_se_rechaza(client, ana, correos):
    pedir(client)
    cambiar_registro(expira_en=ahora() - timedelta(minutes=1))
    assert restablecer(client, correos[0]["codigo"]).status_code == 400


def test_restablecer_con_un_correo_inexistente_da_el_mismo_error(client, correos):
    respuesta = restablecer(client, "123456", email="nadie@example.com")
    assert respuesta.status_code == 400
    assert "incorrecto o caducado" in respuesta.json()["detail"]


def test_la_nueva_contrasena_debe_cumplir_las_reglas_y_el_codigo_sigue_valiendo(client, ana, correos):
    pedir(client)
    codigo = correos[0]["codigo"]
    assert restablecer(client, codigo, password="corta").status_code == 422
    assert restablecer(client, codigo, password="solo-letras-sin-numero").status_code == 422
    assert restablecer(client, codigo).status_code == 200


@pytest.mark.parametrize("codigo", ["12345", "1234567", "12ab56", ""])
def test_el_codigo_debe_tener_exactamente_6_digitos(client, ana, correos, codigo):
    assert restablecer(client, codigo).status_code == 422


def test_al_eliminar_la_cuenta_se_borran_sus_codigos(client, ana, correos):
    pedir(client)
    respuesta = client.request("DELETE", "/clientes/me", json={"password": "clave1234"}, headers=ana["headers"])
    assert respuesta.status_code == 200
    db = SessionLocal()
    try:
        assert db.query(CodigoRecuperacion).count() == 0
    finally:
        db.close()


# ------------------------------------------------------------------ envío con Brevo
class _RespuestaOk:
    def raise_for_status(self):
        pass


def test_el_correo_se_envia_a_la_api_de_brevo(monkeypatch):
    monkeypatch.setenv("BREVO_API_KEY", "clave-falsa")
    monkeypatch.setenv("BREVO_SENDER_EMAIL", "yo@example.com")
    llamadas = []

    def falso_post(url, **kwargs):
        llamadas.append((url, kwargs))
        return _RespuestaOk()

    monkeypatch.setattr(correo.httpx, "post", falso_post)
    correo.enviar_codigo_recuperacion("ana@example.com", "123456", 15)

    url, kwargs = llamadas[0]
    assert url == correo.URL_BREVO
    assert kwargs["headers"]["api-key"] == "clave-falsa"
    assert kwargs["json"]["to"] == [{"email": "ana@example.com"}]
    assert kwargs["json"]["sender"]["email"] == "yo@example.com"
    assert "123456" in kwargs["json"]["textContent"]
    assert "123456" in kwargs["json"]["htmlContent"]


def test_si_brevo_falla_el_error_no_se_propaga(monkeypatch, caplog):
    monkeypatch.setenv("BREVO_API_KEY", "clave-falsa")
    monkeypatch.setenv("BREVO_SENDER_EMAIL", "yo@example.com")

    def falso_post(url, **kwargs):
        raise httpx.ConnectError("sin red")

    monkeypatch.setattr(correo.httpx, "post", falso_post)
    caplog.set_level(logging.ERROR)
    correo.enviar_codigo_recuperacion("ana@example.com", "123456", 15)  # no debe lanzar excepción
    assert "Brevo" in caplog.text
    assert "123456" not in caplog.text


def _sin_configuracion(monkeypatch):
    monkeypatch.delenv("BREVO_API_KEY", raising=False)
    monkeypatch.delenv("BREVO_SENDER_EMAIL", raising=False)

    def no_debe_llamarse(*args, **kwargs):
        raise AssertionError("no debería enviarse nada sin configuración")

    monkeypatch.setattr(correo.httpx, "post", no_debe_llamarse)


def test_sin_configuracion_no_envia_ni_escribe_el_codigo_en_el_log(monkeypatch, caplog):
    _sin_configuracion(monkeypatch)
    monkeypatch.delenv("BARBERFLOW_MOSTRAR_CODIGO_EN_LOG", raising=False)
    caplog.set_level(logging.WARNING)
    correo.enviar_codigo_recuperacion("ana@example.com", "123456", 15)
    assert "BREVO_API_KEY" in caplog.text
    assert "123456" not in caplog.text


def test_en_modo_desarrollo_el_codigo_se_escribe_en_el_log(monkeypatch, caplog):
    _sin_configuracion(monkeypatch)
    monkeypatch.setenv("BARBERFLOW_MOSTRAR_CODIGO_EN_LOG", "1")
    caplog.set_level(logging.WARNING)
    correo.enviar_codigo_recuperacion("ana@example.com", "123456", 15)
    assert "123456" in caplog.text