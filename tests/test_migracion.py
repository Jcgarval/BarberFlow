from sqlalchemy import create_engine, inspect, text

import main


def test_la_migracion_actualiza_una_base_de_datos_antigua(tmp_path):
    """Una base creada antes de existir 'estado' y 'activo' se actualiza sin perder datos."""
    motor = create_engine(f"sqlite:///{tmp_path}/antigua.db")
    with motor.begin() as conexion:
        conexion.execute(text("CREATE TABLE servicios (id INTEGER PRIMARY KEY, nombre VARCHAR, duracion_minutos INTEGER, precio FLOAT)"))
        conexion.execute(text("CREATE TABLE citas (id INTEGER PRIMARY KEY, cliente_id INTEGER, barbero_id INTEGER, servicio_id INTEGER, fecha_hora DATETIME)"))
        conexion.execute(text("INSERT INTO servicios VALUES (1, 'Corte', 30, 12.5)"))
        conexion.execute(text("INSERT INTO citas VALUES (1, 1, 1, 1, '2030-01-01 10:00:00')"))

    main.migrar_columnas(motor)

    inspector = inspect(motor)
    assert "estado" in [c["name"] for c in inspector.get_columns("citas")]
    assert "activo" in [c["name"] for c in inspector.get_columns("servicios")]
    with motor.connect() as conexion:
        assert conexion.execute(text("SELECT estado FROM citas WHERE id = 1")).scalar() == "pendiente"
        assert conexion.execute(text("SELECT activo FROM servicios WHERE id = 1")).scalar() == 1


def test_la_migracion_se_puede_repetir_sin_error(tmp_path):
    motor = create_engine(f"sqlite:///{tmp_path}/otra.db")
    with motor.begin() as conexion:
        conexion.execute(text("CREATE TABLE servicios (id INTEGER PRIMARY KEY, nombre VARCHAR, duracion_minutos INTEGER, precio FLOAT)"))
        conexion.execute(text("CREATE TABLE citas (id INTEGER PRIMARY KEY, cliente_id INTEGER, barbero_id INTEGER, servicio_id INTEGER, fecha_hora DATETIME)"))
    main.migrar_columnas(motor)
    main.migrar_columnas(motor)  # la segunda vez no debe hacer nada ni fallar
