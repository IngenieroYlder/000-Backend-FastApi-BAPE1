"""Add bot whitelist

Revision ID: c8a7f1d3e2b4
Revises: 999d5957bff3
Create Date: 2026-05-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c8a7f1d3e2b4"
down_revision: Union[str, None] = "999d5957bff3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "whatsapp_sessions",
        sa.Column("bot_whitelist_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "whatsapp_sessions",
        sa.Column("bot_whitelist_numbers", sa.JSON(), nullable=True, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("whatsapp_sessions", "bot_whitelist_numbers")
    op.drop_column("whatsapp_sessions", "bot_whitelist_enabled")
