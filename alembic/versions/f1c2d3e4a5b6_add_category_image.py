"""Add image column to product_categories and service_categories

Revision ID: f1c2d3e4a5b6
Revises: d9e2a7c4f5b1
Create Date: 2026-05-21 06:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1c2d3e4a5b6"
down_revision: Union[str, None] = "d9e2a7c4f5b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "product_categories",
        sa.Column("image", sa.String(), nullable=True),
    )
    op.add_column(
        "service_categories",
        sa.Column("image", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("service_categories", "image")
    op.drop_column("product_categories", "image")
