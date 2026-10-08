"""Prepara la base de datos con Alembic: crea las tablas o las actualiza hasta la última versión."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from database import engine

RAIZ = Path(__file__).resolve().parent
REVISION_INICIAL = "0001"  # esquema que tenían las bases de datos creadas antes de usar Alembic


def preparar_base_de_datos(motor=engine) -> None:
    """Aplica todas las migraciones pendientes. Se puede llamar las veces que haga falta.

    - Base nueva (sin tablas): Alembic las crea todas.
    - Base anterior a Alembic (tiene tablas pero no 'alembic_version'): se marca como
      estando en la revisión inicial y se aplican las siguientes, sin perder datos.
    - Base ya gestionada por Alembic: solo se aplican las migraciones que falten.
    """
    config = Config(str(RAIZ / "alembic.ini"))
    config.set_main_option("script_location", str(RAIZ / "alembic"))
    with motor.begin() as conexion:
        config.attributes["connection"] = conexion
        tablas = set(inspect(conexion).get_table_names())
        if "citas" in tablas and "alembic_version" not in tablas:
            command.stamp(config, REVISION_INICIAL)
        command.upgrade(config, "head")
