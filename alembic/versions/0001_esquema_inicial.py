"""Esquema inicial (el que había antes de añadir estados y bajas)

Revision ID: 0001
Revises:
Create Date: 2026-10-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "barberos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_barberos_id", "barberos", ["id"])
    op.create_index("ix_barberos_nombre", "barberos", ["nombre"])

    op.create_table(
        "clientes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=True),
        sa.Column("telefono", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.Column("rol", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_clientes_id", "clientes", ["id"])
    op.create_index("ix_clientes_nombre", "clientes", ["nombre"])
    op.create_index("ix_clientes_email", "clientes", ["email"], unique=True)

    # En el esquema original los servicios todavía no tenían la columna "activo"
    op.create_table(
        "servicios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=True),
        sa.Column("duracion_minutos", sa.Integer(), nullable=True),
        sa.Column("precio", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_servicios_id", "servicios", ["id"])
    op.create_index("ix_servicios_nombre", "servicios", ["nombre"])

    # ... ni las citas la columna "estado"
    op.create_table(
        "citas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=True),
        sa.Column("barbero_id", sa.Integer(), nullable=True),
        sa.Column("servicio_id", sa.Integer(), nullable=True),
        sa.Column("fecha_hora", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["barbero_id"], ["barberos.id"]),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]),
        sa.ForeignKeyConstraint(["servicio_id"], ["servicios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_citas_id", "citas", ["id"])


def downgrade() -> None:
    op.drop_index("ix_citas_id", table_name="citas")
    op.drop_table("citas")
    op.drop_index("ix_servicios_nombre", table_name="servicios")
    op.drop_index("ix_servicios_id", table_name="servicios")
    op.drop_table("servicios")
    op.drop_index("ix_clientes_email", table_name="clientes")
    op.drop_index("ix_clientes_nombre", table_name="clientes")
    op.drop_index("ix_clientes_id", table_name="clientes")
    op.drop_table("clientes")
    op.drop_index("ix_barberos_nombre", table_name="barberos")
    op.drop_index("ix_barberos_id", table_name="barberos")
    op.drop_table("barberos")
