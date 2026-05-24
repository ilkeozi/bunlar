"""add raw html fields to raw_web_page_observation

Revision ID: 20260524_07
Revises: 20260524_06
Create Date: 2026-05-24 20:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260524_07"
down_revision = "20260524_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "raw_web_page_observation",
        sa.Column("raw_html", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "raw_web_page_observation",
        sa.Column("raw_html_sha256", sa.String(length=64), nullable=False, server_default=""),
    )
    op.add_column(
        "raw_web_page_observation",
        sa.Column("raw_html_bytes", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "raw_web_page_observation",
        sa.Column("raw_html_truncated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("raw_web_page_observation", "raw_html_truncated")
    op.drop_column("raw_web_page_observation", "raw_html_bytes")
    op.drop_column("raw_web_page_observation", "raw_html_sha256")
    op.drop_column("raw_web_page_observation", "raw_html")
