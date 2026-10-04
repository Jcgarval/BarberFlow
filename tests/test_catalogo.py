import pytest


# ------------------------------------------------------------------ permisos
def test_los_listados_son_publicos(client, catalogo):
    assert client.get("/barberos/").status_code == 200
    assert client.get("/servicios/").status_code == 200


@pytest.mark.parametrize("ruta, cuerpo", [
    ("/barberos/", {"nombre": "Marta"}),
    ("/servicios/", {"nombre": "Tinte", "duracion_minutos": 60, "precio": 25}),
])
def test_solo_el_administrador_crea_barberos_y_servicios(client, ana, ruta, cuerpo):
    assert client.post(ruta, json=cuerpo, headers=ana["headers"]).status_code == 403
    assert client.post(ruta, json=cuerpo).status_code in (401, 403)


def test_un_cliente_no_puede_ver_ni_reactivar_bajas(client, ana, catalogo):
    assert client.get("/barberos/inactivos", headers=ana["headers"]).status_code == 403
    assert client.get("/servicios/inactivos", headers=ana["headers"]).status_code == 403
    assert client.post(f"/barberos/{catalogo['barbero']['id']}/reactivar", headers=ana["headers"]).status_code == 403
    assert client.post(f"/servicios/{catalogo['corte']['id']}/reactivar", headers=ana["headers"]).status_code == 403


def test_un_cliente_no_puede_borrar_ni_editar(client, ana, catalogo):
    assert client.delete(f"/servicios/{catalogo['corte']['id']}", headers=ana["headers"]).status_code == 403
    assert client.put(
        f"/barberos/{catalogo['barbero']['id']}", json={"nombre": "X"}, headers=ana["headers"]
    ).status_code == 403


# ------------------------------------------------------------------ validación
def crear_servicio(client, admin, **cambios):
    cuerpo = {"nombre": "Prueba", "duracion_minutos": 30, "precio": 10}
    cuerpo.update(cambios)
    return client.post("/servicios/", json=cuerpo, headers=admin["headers"])


@pytest.mark.parametrize("cambios", [
    {"duracion_minutos": 0},
    {"duracion_minutos": -30},
    {"duracion_minutos": 481},
    {"precio": -1},
    {"precio": 1001},
    {"nombre": ""},
    {"nombre": "   "},
    {"nombre": "x" * 61},
])
def test_un_servicio_con_datos_invalidos_se_rechaza(client, admin, cambios):
    assert crear_servicio(client, admin, **cambios).status_code == 422


@pytest.mark.parametrize("cambios", [{"duracion_minutos": 480}, {"duracion_minutos": 1}, {"precio": 0}, {"precio": 1000}])
def test_los_limites_validos_se_aceptan(client, admin, cambios):
    assert crear_servicio(client, admin, **cambios).status_code == 200


def test_el_nombre_se_guarda_sin_espacios_sobrantes(client, admin):
    assert crear_servicio(client, admin, nombre="  Corte clásico  ").json()["nombre"] == "Corte clásico"


def test_un_barbero_sin_nombre_se_rechaza(client, admin):
    assert client.post("/barberos/", json={"nombre": "  "}, headers=admin["headers"]).status_code == 422


def test_actualizar_un_servicio_tambien_valida(client, admin, catalogo):
    ruta = f"/servicios/{catalogo['corte']['id']}"
    assert client.put(ruta, json={"nombre": "X", "duracion_minutos": 0, "precio": 5}, headers=admin["headers"]).status_code == 422
    respuesta = client.put(ruta, json={"nombre": "Corte nuevo", "duracion_minutos": 45, "precio": 14.5}, headers=admin["headers"])
    assert respuesta.status_code == 200
    assert respuesta.json()["duracion_minutos"] == 45


# ------------------------------------------------------------------ baja lógica
def test_un_servicio_sin_citas_se_borra_del_todo(client, admin, catalogo):
    id_servicio = catalogo["corte"]["id"]
    respuesta = client.delete(f"/servicios/{id_servicio}", headers=admin["headers"])
    assert respuesta.status_code == 200
    assert client.get(f"/servicios/{id_servicio}").status_code == 404


def test_un_servicio_con_citas_se_da_de_baja_y_conserva_el_historial(client, admin, ana, catalogo, reservar, dia_laborable):
    cita = reservar(ana, dia_laborable, 15).json()
    respuesta = client.delete(f"/servicios/{catalogo['corte']['id']}", headers=admin["headers"])
    assert respuesta.status_code == 200
    assert "baja" in respuesta.json()["mensaje"]

    # ya no se ofrece, pero aparece en las bajas
    assert all(s["id"] != catalogo["corte"]["id"] for s in client.get("/servicios/").json())
    assert [s["id"] for s in client.get("/servicios/inactivos", headers=admin["headers"]).json()] == [catalogo["corte"]["id"]]

    # el historial sigue mostrando su nombre (no "Desconocido")
    detalle = [c for c in client.get("/admin/citas/detalles", headers=admin["headers"]).json() if c["id"] == cita["id"]][0]
    assert detalle["servicio_nombre"] == "Corte"
    propia = [c for c in client.get("/citas/", headers=ana["headers"]).json() if c["id"] == cita["id"]][0]
    assert propia["servicio"]["nombre"] == "Corte"


def test_no_se_reserva_con_un_servicio_dado_de_baja(client, admin, ana, catalogo, reservar, dia_laborable):
    reservar(ana, dia_laborable, 15)  # para que tenga citas y se dé de baja en vez de borrarse
    client.delete(f"/servicios/{catalogo['corte']['id']}", headers=admin["headers"])
    respuesta = reservar(ana, dia_laborable, 17)
    assert respuesta.status_code == 400
    assert "ya no está disponible" in respuesta.json()["detail"]
    consulta = client.get(
        "/citas/disponibilidad",
        params={"barbero_id": catalogo["barbero"]["id"], "servicio_id": catalogo["corte"]["id"], "fecha": dia_laborable.isoformat()},
        headers=ana["headers"],
    )
    assert consulta.status_code == 400


def test_reactivar_un_servicio_lo_devuelve_al_catalogo(client, admin, ana, catalogo, reservar, dia_laborable):
    reservar(ana, dia_laborable, 15)
    client.delete(f"/servicios/{catalogo['corte']['id']}", headers=admin["headers"])
    respuesta = client.post(f"/servicios/{catalogo['corte']['id']}/reactivar", headers=admin["headers"])
    assert respuesta.status_code == 200
    assert any(s["id"] == catalogo["corte"]["id"] for s in client.get("/servicios/").json())
    assert client.get("/servicios/inactivos", headers=admin["headers"]).json() == []
    assert reservar(ana, dia_laborable, 17).status_code == 200


def test_un_barbero_con_citas_se_da_de_baja_y_se_puede_reactivar(client, admin, ana, catalogo, reservar, dia_laborable):
    reservar(ana, dia_laborable, 15)
    id_barbero = catalogo["barbero"]["id"]
    assert "baja" in client.delete(f"/barberos/{id_barbero}", headers=admin["headers"]).json()["mensaje"]
    assert all(b["id"] != id_barbero for b in client.get("/barberos/").json())
    assert reservar(ana, dia_laborable, 17).status_code == 400

    assert client.post(f"/barberos/{id_barbero}/reactivar", headers=admin["headers"]).status_code == 200
    assert any(b["id"] == id_barbero for b in client.get("/barberos/").json())
    assert reservar(ana, dia_laborable, 17).status_code == 200


def test_un_barbero_sin_citas_se_borra_del_todo(client, admin, catalogo):
    id_barbero = catalogo["barbero"]["id"]
    assert client.delete(f"/barberos/{id_barbero}", headers=admin["headers"]).status_code == 200
    assert client.get(f"/barberos/{id_barbero}").status_code == 404


def test_reactivar_algo_que_no_existe_da_404(client, admin):
    assert client.post("/servicios/9999/reactivar", headers=admin["headers"]).status_code == 404
    assert client.post("/barberos/9999/reactivar", headers=admin["headers"]).status_code == 404


def test_la_ruta_inactivos_no_se_confunde_con_un_id(client, admin):
    assert client.get("/barberos/inactivos", headers=admin["headers"]).status_code == 200
    assert client.get("/servicios/inactivos", headers=admin["headers"]).status_code == 200
