"""add redirect tracking fields to http fetch attempt

Revision ID: 20260526_02
Revises: 20260526_01
Create Date: 2026-05-26 00:55:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260526_02"
down_revision = "20260526_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("raw_web_http_fetch_attempt", sa.Column("requested_url", sa.Text(), nullable=False, server_default=""))
    op.add_column("raw_web_http_fetch_attempt", sa.Column("final_url", sa.Text(), nullable=False, server_default=""))
    op.add_column("raw_web_http_fetch_attempt", sa.Column("redirect_count", sa.Integer(), nullable=False, server_default="0"))

    op.alter_column("raw_web_http_fetch_attempt", "requested_url", server_default=None)
    op.alter_column("raw_web_http_fetch_attempt", "final_url", server_default=None)
    op.alter_column("raw_web_http_fetch_attempt", "redirect_count", server_default=None)


def downgrade() -> None:
    op.drop_column("raw_web_http_fetch_attempt", "redirect_count")
    op.drop_column("raw_web_http_fetch_attempt", "final_url")
    op.drop_column("raw_web_http_fetch_attempt", "requested_url")
