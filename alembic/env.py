"""Entorno de Alembic.

Se usa de dos formas:
  * Desde la propia aplicación (migraciones.py), que le pasa una conexión ya abierta.
  * Desde la terminal (alembic revision --autogenerate, alembic upgrade head...),
    donde abre su propia conexión con el motor de database.py.
"""
from logging.config import fileConfig

from alembic import context

from database import engine
from models import Base

config = context.config

# Solo configuramos el logging cuando se ejecuta desde la terminal;
# desde la aplicación no queremos tocar los logs de uvicorn.
if config.config_file_name is not None and config.attributes.get("connection") is None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _ejecutar(conexion) -> None:
    context.configure(
        connection=conexion,
        target_metadata=target_metadata,
        render_as_batch=True,  # SQLite no soporta ALTER TABLE completo: Alembic reconstruye la tabla
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    conexion = config.attributes.get("connection")
    if conexion is not None:
        _ejecutar(conexion)
    else:
        with engine.begin() as conexion:
            _ejecutar(conexion)


def run_migrations_offline() -> None:
    """Modo 'alembic upgrade head --sql': genera el SQL sin conectarse."""
    context.configure(
        url=str(engine.url),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
