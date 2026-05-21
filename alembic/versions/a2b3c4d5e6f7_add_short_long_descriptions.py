"""Add short_description and long_description to products and services

Revision ID: a2b3c4d5e6f7
Revises: f1c2d3e4a5b6
Create Date: 2026-05-21 06:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, None] = "f1c2d3e4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("short_description", sa.String(), nullable=True))
    op.add_column("products", sa.Column("long_description", sa.Text(), nullable=True))
    op.add_column("services", sa.Column("short_description", sa.String(), nullable=True))
    op.add_column("services", sa.Column("long_description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("services", "long_description")
    op.drop_column("services", "short_description")
    op.drop_column("products", "long_description")
    op.drop_column("products", "short_description")
