"""Pruebas del borrado de cuenta (DELETE /clientes/me): anonimiza al cliente y conserva el historial."""
from datetime import datetime, timedelta

from database import SessionLocal
from models import Cita, Cliente


def borrar(client, usuario, password="clave1234"):
    return client.request("DELETE", "/clientes/me", json={"password": password}, headers=usuario["headers"])


def cliente_en_bd(cliente_id):
    db = SessionLocal()
    try:
        return db.query(Cliente).filter(Cliente.id == cliente_id).first()
    finally:
        db.close()


def crear_cita_pasada(cliente_id, catalogo, estado="completada"):
    db = SessionLocal()
    try:
        cita = Cita(
            cliente_id=cliente_id,
            barbero_id=catalogo["barbero"]["id"],
            servicio_id=catalogo["corte"]["id"],
            fecha_hora=datetime.now() - timedelta(days=3),
            estado=estado,
        )
        db.add(cita)
        db.commit()
        db.refresh(cita)
        return cita.id
    finally:
        db.close()


# ------------------------------------------------------------------ borrado correcto
def test_eliminar_la_cuenta_anonimiza_los_datos_personales(client, ana):
    respuesta = borrar(client, ana)
    assert respuesta.status_code == 200

    cliente = cliente_en_bd(ana["id"])
    assert cliente is not None  # la fila se conserva para no romper el historial
    assert cliente.nombre == "Cliente eliminado"
    assert cliente.email == f"eliminado-{ana['id']}@anonimo.invalid"
    assert cliente.telefono is None
    assert cliente.rol == "cliente"


def test_tras_eliminar_la_cuenta_no_se_puede_entrar_ni_con_el_token_antiguo(client, ana):
    borrar(client, ana)
    assert client.post("/login", json={"email": ana["email"], "password": "clave1234"}).status_code == 400
    assert client.get("/citas/", headers=ana["headers"]).status_code == 401


def test_el_email_de_una_cuenta_eliminada_se_puede_volver_a_registrar(client, ana):
    borrar(client, ana)
    respuesta = client.post("/clientes/", json={"nombre": "Ana", "email": ana["email"], "password": "clave1234"})
    assert respuesta.status_code == 200
    assert respuesta.json()["id"] != ana["id"]


# ------------------------------------------------------------------ historial de citas
def test_las_citas_futuras_se_cancelan_y_liberan_el_hueco(client, admin, ana, beto, reservar, franjas, dia_laborable):
    cita = reservar(ana, dia_laborable, 10).json()
    assert "10:00" not in franjas(beto, dia_laborable)

    borrar(client, ana)

    assert client.get(f"/citas/{cita['id']}", headers=admin["headers"]).json()["estado"] == "cancelada"
    assert "10:00" in franjas(beto, dia_laborable)
    assert reservar(beto, dia_laborable, 10).status_code == 200


def test_las_citas_pasadas_se_conservan_sin_cambiar_de_estado(client, admin, ana, catalogo):
    cita_id = crear_cita_pasada(ana["id"], catalogo, estado="completada")
    borrar(client, ana)

    cita = client.get(f"/citas/{cita_id}", headers=admin["headers"]).json()
    assert cita["estado"] == "completada"
    assert cita["cliente_id"] == ana["id"]

    detalle = [c for c in client.get("/admin/citas/detalles", headers=admin["headers"]).json() if c["id"] == cita_id][0]
    assert detalle["cliente_nombre"] == "Cliente eliminado"


def test_eliminar_una_cuenta_no_toca_a_los_demas_clientes(client, admin, ana, beto, reservar, dia_laborable):
    cita_beto = reservar(beto, dia_laborable, 12).json()
    borrar(client, ana)

    assert cliente_en_bd(beto["id"]).nombre == "Beto"
    assert client.get(f"/citas/{cita_beto['id']}", headers=beto["headers"]).json()["estado"] == "pendiente"


# ------------------------------------------------------------------ rechazos
def test_con_la_contrasena_incorrecta_no_se_elimina_nada(client, ana, reservar, dia_laborable):
    cita = reservar(ana, dia_laborable, 10).json()

    assert borrar(client, ana, password="otra-clave1").status_code == 400

    assert cliente_en_bd(ana["id"]).nombre == "Ana"
    assert client.post("/login", json={"email": ana["email"], "password": "clave1234"}).status_code == 200
    assert client.get(f"/citas/{cita['id']}", headers=ana["headers"]).json()["estado"] == "pendiente"


def test_una_contrasena_de_mas_de_72_bytes_se_rechaza_sin_error_500(client, ana):
    assert borrar(client, ana, password="a1" * 40).status_code == 400
    assert cliente_en_bd(ana["id"]).nombre == "Ana"


def test_un_administrador_no_puede_eliminar_su_cuenta_por_esta_via(client, admin):
    assert borrar(client, admin, password="clave1234").status_code == 403
    assert cliente_en_bd(admin["id"]).rol == "admin"


def test_eliminar_la_cuenta_exige_iniciar_sesion(client):
    respuesta = client.request("DELETE", "/clientes/me", json={"password": "clave1234"})
    assert respuesta.status_code in (401, 403)


def test_eliminar_la_cuenta_exige_enviar_la_contrasena(client, ana):
    respuesta = client.request("DELETE", "/clientes/me", headers=ana["headers"])
    assert respuesta.status_code == 422
    assert cliente_en_bd(ana["id"]).nombre == "Ana"
