"""Add is_group flag to contacts

Revision ID: d9e2a7c4f5b1
Revises: c8a7f1d3e2b4
Create Date: 2026-05-21 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d9e2a7c4f5b1"
down_revision: Union[str, None] = "c8a7f1d3e2b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "contacts",
        sa.Column("is_group", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute(
        "UPDATE contacts SET is_group = TRUE "
        "WHERE LENGTH(phone) >= 15 OR phone LIKE '120363%'"
    )


def downgrade() -> None:
    op.drop_column("contacts", "is_group")
