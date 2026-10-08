from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

from migraciones import preparar_base_de_datos
from models import Base

ULTIMA_REVISION = "0002"


def _base_antigua(motor, con_columnas_nuevas=False):
    """Crea las tablas como estaban antes de Alembic (y antes de 'estado' y 'activo')."""
    extra_servicio = ", activo BOOLEAN NOT NULL DEFAULT 1" if con_columnas_nuevas else ""
    extra_cita = ", estado VARCHAR NOT NULL DEFAULT 'pendiente'" if con_columnas_nuevas else ""
    with motor.begin() as conexion:
        conexion.execute(text(f"CREATE TABLE servicios (id INTEGER PRIMARY KEY, nombre VARCHAR, duracion_minutos INTEGER, precio FLOAT{extra_servicio})"))
        conexion.execute(text(f"CREATE TABLE citas (id INTEGER PRIMARY KEY, cliente_id INTEGER, barbero_id INTEGER, servicio_id INTEGER, fecha_hora DATETIME{extra_cita})"))
        conexion.execute(text("INSERT INTO servicios (id, nombre, duracion_minutos, precio) VALUES (1, 'Corte', 30, 12.5)"))
        conexion.execute(text("INSERT INTO citas (id, cliente_id, barbero_id, servicio_id, fecha_hora) VALUES (1, 1, 1, 1, '2030-01-01 10:00:00')"))


def _revision_actual(motor):
    with motor.connect() as conexion:
        return conexion.execute(text("SELECT version_num FROM alembic_version")).scalar()


def test_una_base_nueva_se_crea_con_todas_las_tablas_y_queda_al_dia(tmp_path):
    motor = create_engine(f"sqlite:///{tmp_path}/nueva.db")
    preparar_base_de_datos(motor)
    assert set(Base.metadata.tables) <= set(inspect(motor).get_table_names())
    assert _revision_actual(motor) == ULTIMA_REVISION


def test_las_migraciones_producen_exactamente_el_esquema_de_los_modelos(tmp_path):
    """Si alguien cambia models.py y olvida crear su migración, esta prueba falla."""
    motor = create_engine(f"sqlite:///{tmp_path}/esquema.db")
    preparar_base_de_datos(motor)
    with motor.connect() as conexion:
        diferencias = compare_metadata(MigrationContext.configure(conexion), Base.metadata)
    assert diferencias == []


def test_una_base_anterior_a_alembic_se_actualiza_sin_perder_datos(tmp_path):
    """Una base creada antes de existir 'estado' y 'activo' se actualiza sin perder datos."""
    motor = create_engine(f"sqlite:///{tmp_path}/antigua.db")
    _base_antigua(motor)

    preparar_base_de_datos(motor)

    inspector = inspect(motor)
    assert "estado" in [c["name"] for c in inspector.get_columns("citas")]
    assert "activo" in [c["name"] for c in inspector.get_columns("servicios")]
    with motor.connect() as conexion:
        assert conexion.execute(text("SELECT estado FROM citas WHERE id = 1")).scalar() == "pendiente"
        assert conexion.execute(text("SELECT activo FROM servicios WHERE id = 1")).scalar() == 1
        assert conexion.execute(text("SELECT nombre FROM servicios WHERE id = 1")).scalar() == "Corte"
    assert _revision_actual(motor) == ULTIMA_REVISION


def test_una_base_ya_actualizada_a_mano_no_da_error(tmp_path):
    """Bases que ya pasaron por la antigua migrar_columnas(): ya tienen las columnas nuevas."""
    motor = create_engine(f"sqlite:///{tmp_path}/a_mano.db")
    _base_antigua(motor, con_columnas_nuevas=True)
    preparar_base_de_datos(motor)
    assert _revision_actual(motor) == ULTIMA_REVISION
    with motor.connect() as conexion:
        assert conexion.execute(text("SELECT nombre FROM servicios WHERE id = 1")).scalar() == "Corte"


def test_la_migracion_se_puede_repetir_sin_error(tmp_path):
    motor = create_engine(f"sqlite:///{tmp_path}/otra.db")
    _base_antigua(motor)
    preparar_base_de_datos(motor)
    preparar_base_de_datos(motor)  # la segunda vez no debe hacer nada ni fallar
    assert _revision_actual(motor) == ULTIMA_REVISION
