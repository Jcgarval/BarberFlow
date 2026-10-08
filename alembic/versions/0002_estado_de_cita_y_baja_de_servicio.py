"""Estado de las citas y baja lógica de los servicios

Sustituye a la antigua función migrar_columnas() de main.py.
Cada columna se añade solo si falta: así funciona también con bases de datos
que ya habían sido actualizadas a mano por esa función.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columnas(tabla: str) -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(tabla)}


def upgrade() -> None:
    if "estado" not in _columnas("citas"):
        op.add_column(
            "citas",
            sa.Column("estado", sa.String(), nullable=False, server_default="pendiente"),
        )
    if "activo" not in _columnas("servicios"):
        op.add_column(
            "servicios",
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        )


def downgrade() -> None:
    with op.batch_alter_table("servicios") as lote:
        lote.drop_column("activo")
    with op.batch_alter_table("citas") as lote:
        lote.drop_column("estado")
