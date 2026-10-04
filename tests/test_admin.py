def test_el_detalle_de_citas_solo_lo_ve_el_administrador(client, ana):
    assert client.get("/admin/citas/detalles", headers=ana["headers"]).status_code == 403


def test_el_detalle_incluye_nombres_y_estado_y_va_ordenado_por_fecha(client, admin, ana, catalogo, reservar, dia_laborable):
    # se crean desordenadas a propósito
    ids = {hora: reservar(ana, dia_laborable, hora).json()["id"] for hora in (16, 10, 12)}
    client.patch(f"/citas/{ids[10]}/estado", json={"estado": "confirmada"}, headers=admin["headers"])

    detalle = client.get("/admin/citas/detalles", headers=admin["headers"]).json()
    assert [c["fecha_hora"][11:16] for c in detalle] == ["10:00", "12:00", "16:00"]
    assert [c["estado"] for c in detalle] == ["confirmada", "pendiente", "pendiente"]
    assert detalle[0]["cliente_nombre"] == "Ana"
    assert detalle[0]["barbero_nombre"] == "Carlos"
    assert detalle[0]["servicio_nombre"] == "Corte"
