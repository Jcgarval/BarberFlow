from datetime import date, datetime, timedelta

import pytest


# ============================================================ disponibilidad
def test_un_dia_libre_ofrece_todas_las_franjas(ana, dia_laborable, franjas):
    horas = franjas(ana, dia_laborable)
    assert horas[0] == "09:00" and horas[-1] == "19:30"
    assert len(horas) == 22  # cada 30 minutos, de 09:00 a 19:30


def test_un_servicio_largo_deja_menos_franjas_al_final(ana, dia_laborable, franjas):
    horas = franjas(ana, dia_laborable, servicio="corte_barba")
    assert horas[-1] == "19:00" and "19:30" not in horas  # 60 min: tiene que acabar a las 20:00


def test_la_disponibilidad_exige_iniciar_sesion(client, catalogo, dia_laborable):
    respuesta = client.get(
        "/citas/disponibilidad",
        params={"barbero_id": catalogo["barbero"]["id"], "servicio_id": catalogo["corte"]["id"], "fecha": dia_laborable.isoformat()},
    )
    assert respuesta.status_code in (401, 403)


def test_el_domingo_no_hay_franjas(ana, proximo_domingo, franjas):
    assert franjas(ana, proximo_domingo) == []


def test_la_disponibilidad_de_algo_inexistente_da_404(client, ana, catalogo, dia_laborable):
    base = {"fecha": dia_laborable.isoformat()}
    assert client.get("/citas/disponibilidad", params={**base, "barbero_id": 999, "servicio_id": catalogo["corte"]["id"]}, headers=ana["headers"]).status_code == 404
    assert client.get("/citas/disponibilidad", params={**base, "barbero_id": catalogo["barbero"]["id"], "servicio_id": 999}, headers=ana["headers"]).status_code == 404


def test_hoy_solo_se_ofrecen_franjas_futuras(ana, franjas):
    if date.today().weekday() == 6:
        pytest.skip("Hoy es domingo y no hay franjas")
    ahora = datetime.now().strftime("%H:%M")
    assert all(hora > ahora for hora in franjas(ana, date.today()))


# ============================================================ reservar
def test_reservar_crea_una_cita_pendiente(ana, reservar, dia_laborable):
    respuesta = reservar(ana, dia_laborable, 10)
    assert respuesta.status_code == 200
    cita = respuesta.json()
    assert cita["estado"] == "pendiente"
    assert cita["barbero"]["nombre"] == "Carlos"
    assert cita["servicio"]["nombre"] == "Corte"


def test_una_franja_reservada_desaparece_de_la_disponibilidad(ana, beto, reservar, franjas, dia_laborable):
    reservar(ana, dia_laborable, 10, servicio="corte_barba")  # ocupa de 10:00 a 11:00
    corte = franjas(beto, dia_laborable)
    assert "10:00" not in corte and "10:30" not in corte
    assert "09:30" in corte and "11:00" in corte
    largo = franjas(beto, dia_laborable, servicio="corte_barba")
    assert "09:30" not in largo  # un servicio de 60 min a las 09:30 pisaría la cita de las 10:00
    assert "09:00" in largo and "11:00" in largo


def test_no_se_puede_reservar_encima_de_otra_cita(ana, beto, reservar, dia_laborable):
    reservar(ana, dia_laborable, 10, servicio="corte_barba")  # 10:00-11:00
    exacta = reservar(beto, dia_laborable, 10)
    parcial = reservar(beto, dia_laborable, 10, 30)
    assert exacta.status_code == 400 and "ocupada" in exacta.json()["detail"]
    assert parcial.status_code == 400


def test_una_cita_justo_a_continuacion_si_se_permite(ana, beto, reservar, dia_laborable):
    reservar(ana, dia_laborable, 10, servicio="corte_barba")
    assert reservar(beto, dia_laborable, 11).status_code == 200


def test_un_cliente_no_puede_reservar_a_nombre_de_otro(ana, beto, reservar, dia_laborable):
    assert reservar(beto, dia_laborable, 10, cliente_id=ana["id"]).status_code == 403


def test_el_administrador_puede_reservar_para_un_cliente(admin, ana, reservar, dia_laborable):
    assert reservar(admin, dia_laborable, 10, cliente_id=ana["id"]).status_code == 200


def test_reservar_exige_iniciar_sesion(client, ana, catalogo, a_las, dia_laborable):
    cuerpo = {"cliente_id": ana["id"], "barbero_id": catalogo["barbero"]["id"], "servicio_id": catalogo["corte"]["id"], "fecha_hora": a_las(dia_laborable, 10)}
    assert client.post("/citas/", json=cuerpo).status_code in (401, 403)


# ============================================================ reglas de horario
def test_no_se_reserva_antes_de_abrir(ana, reservar, dia_laborable):
    assert reservar(ana, dia_laborable, 8).status_code == 400


def test_la_cita_debe_acabar_antes_del_cierre(ana, reservar, dia_laborable):
    assert reservar(ana, dia_laborable, 19, 30, servicio="corte_barba").status_code == 400  # acabaría a las 20:30
    assert reservar(ana, dia_laborable, 19, 30).status_code == 200  # acaba justo a las 20:00


def test_no_se_reserva_en_el_pasado(ana, reservar):
    pasado = date.today() - timedelta(days=1)
    if pasado.weekday() == 6:  # si ayer fue domingo, la respuesta sería «cierra los domingos»: tomamos el sábado
        pasado -= timedelta(days=1)
    respuesta = reservar(ana, pasado, 12)
    assert respuesta.status_code == 400
    assert "pasado" in respuesta.json()["detail"]


def test_no_se_reserva_en_domingo(ana, reservar, proximo_domingo):
    respuesta = reservar(ana, proximo_domingo, 10)
    assert respuesta.status_code == 400
    assert "domingos" in respuesta.json()["detail"]


# ============================================================ modificar una cita
def cuerpo_cita(ana, catalogo, a_las, dia, hora):
    return {"cliente_id": ana["id"], "barbero_id": catalogo["barbero"]["id"], "servicio_id": catalogo["corte"]["id"], "fecha_hora": a_las(dia, hora)}


def test_modificar_una_cita_a_un_hueco_libre_funciona(client, ana, catalogo, reservar, a_las, dia_laborable):
    cita = reservar(ana, dia_laborable, 10).json()
    respuesta = client.put(f"/citas/{cita['id']}", json=cuerpo_cita(ana, catalogo, a_las, dia_laborable, 10), headers=ana["headers"])
    assert respuesta.status_code == 200  # se excluye a sí misma al comprobar solapes
    respuesta = client.put(f"/citas/{cita['id']}", json=cuerpo_cita(ana, catalogo, a_las, dia_laborable, 17), headers=ana["headers"])
    assert respuesta.status_code == 200
    assert respuesta.json()["fecha_hora"].endswith("17:00:00")


def test_modificar_una_cita_tambien_comprueba_solapes_y_domingos(client, ana, beto, catalogo, reservar, a_las, dia_laborable, proximo_domingo):
    reservar(beto, dia_laborable, 10)
    cita = reservar(ana, dia_laborable, 12).json()
    sobre_otra = client.put(f"/citas/{cita['id']}", json=cuerpo_cita(ana, catalogo, a_las, dia_laborable, 10), headers=ana["headers"])
    en_domingo = client.put(f"/citas/{cita['id']}", json=cuerpo_cita(ana, catalogo, a_las, proximo_domingo, 10), headers=ana["headers"])
    assert sobre_otra.status_code == 400
    assert en_domingo.status_code == 400


# ============================================================ quién ve qué
def test_un_cliente_solo_ve_sus_citas(client, ana, beto, reservar, dia_laborable):
    reservar(ana, dia_laborable, 10)
    reservar(beto, dia_laborable, 12)
    propias = client.get("/citas/", headers=ana["headers"]).json()
    assert len(propias) == 1 and propias[0]["cliente_id"] == ana["id"]


def test_un_cliente_no_puede_pedir_las_citas_de_otro(client, ana, beto):
    assert client.get("/citas/", params={"cliente_id": beto["id"]}, headers=ana["headers"]).status_code == 403


def test_el_administrador_ve_todas_y_puede_filtrar(client, admin, ana, beto, catalogo, reservar, dia_laborable):
    reservar(ana, dia_laborable, 10)
    reservar(beto, dia_laborable, 12)
    assert len(client.get("/citas/", headers=admin["headers"]).json()) == 2
    solo_ana = client.get("/citas/", params={"cliente_id": ana["id"]}, headers=admin["headers"]).json()
    assert len(solo_ana) == 1
    assert client.get("/citas/", params={"estado": "cancelada"}, headers=admin["headers"]).json() == []
    assert len(client.get("/citas/", params={"barbero_id": catalogo["barbero"]["id"]}, headers=admin["headers"]).json()) == 2


def test_una_cita_ajena_no_se_puede_ver_ni_borrar(client, ana, beto, reservar, dia_laborable):
    cita = reservar(ana, dia_laborable, 10).json()
    assert client.get(f"/citas/{cita['id']}", headers=beto["headers"]).status_code == 403
    assert client.delete(f"/citas/{cita['id']}", headers=beto["headers"]).status_code == 403
    assert client.get(f"/citas/{cita['id']}", headers=ana["headers"]).status_code == 200


def test_el_propietario_puede_borrar_su_cita(client, ana, reservar, dia_laborable):
    cita = reservar(ana, dia_laborable, 10).json()
    assert client.delete(f"/citas/{cita['id']}", headers=ana["headers"]).status_code == 200
    assert client.get(f"/citas/{cita['id']}", headers=ana["headers"]).status_code == 404


# ============================================================ estados
def cambiar(client, cita, estado, usuario):
    return client.patch(f"/citas/{cita['id']}/estado", json={"estado": estado}, headers=usuario["headers"])


def test_el_administrador_puede_cambiar_a_cualquier_estado(client, admin, ana, reservar, dia_laborable):
    cita = reservar(ana, dia_laborable, 10).json()
    for estado in ("confirmada", "completada", "cancelada", "pendiente"):
        respuesta = cambiar(client, cita, estado, admin)
        assert respuesta.status_code == 200 and respuesta.json()["estado"] == estado


def test_un_estado_inventado_se_rechaza(client, admin, ana, reservar, dia_laborable):
    cita = reservar(ana, dia_laborable, 10).json()
    assert cambiar(client, cita, "inventado", admin).status_code == 422


def test_un_cliente_solo_puede_cancelar(client, ana, reservar, dia_laborable):
    cita = reservar(ana, dia_laborable, 10).json()
    assert cambiar(client, cita, "confirmada", ana).status_code == 403
    assert cambiar(client, cita, "cancelada", ana).json()["estado"] == "cancelada"


def test_un_cliente_no_puede_cancelar_la_cita_de_otro(client, ana, beto, reservar, dia_laborable):
    cita = reservar(ana, dia_laborable, 10).json()
    assert cambiar(client, cita, "cancelada", beto).status_code == 403


def test_una_cita_completada_no_se_puede_cancelar_como_cliente(client, admin, ana, reservar, dia_laborable):
    cita = reservar(ana, dia_laborable, 10).json()
    cambiar(client, cita, "completada", admin)
    assert cambiar(client, cita, "cancelada", ana).status_code == 400


def test_cancelar_libera_el_hueco(client, ana, beto, reservar, franjas, dia_laborable):
    cita = reservar(ana, dia_laborable, 10).json()
    assert "10:00" not in franjas(beto, dia_laborable)
    cambiar(client, cita, "cancelada", ana)
    assert "10:00" in franjas(beto, dia_laborable)
    assert reservar(beto, dia_laborable, 10).status_code == 200


def test_no_se_reactiva_una_cita_cancelada_si_otro_ocupo_su_hueco(client, admin, ana, beto, reservar, dia_laborable):
    cita = reservar(ana, dia_laborable, 10).json()
    cambiar(client, cita, "cancelada", ana)
    reservar(beto, dia_laborable, 10)
    assert cambiar(client, cita, "pendiente", admin).status_code == 400
