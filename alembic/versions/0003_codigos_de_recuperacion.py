"""Códigos de recuperación de contraseña

Crea la tabla codigos_recuperacion. Solo la crea si falta, igual que la 0002,
para que funcione también en bases de datos que ya la tuvieran.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if "codigos_recuperacion" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "codigos_recuperacion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clientes.id"), nullable=False),
        sa.Column("codigo_hash", sa.String(), nullable=False),
        sa.Column("creado_en", sa.DateTime(), nullable=False),
        sa.Column("expira_en", sa.DateTime(), nullable=False),
        sa.Column("intentos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("usado", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_codigos_recuperacion_cliente_id", "codigos_recuperacion", ["cliente_id"])


def downgrade() -> None:
    op.drop_index("ix_codigos_recuperacion_cliente_id", table_name="codigos_recuperacion")
    op.drop_table("codigos_recuperacion")