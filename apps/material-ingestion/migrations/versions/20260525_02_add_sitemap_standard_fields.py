"""add sitemap standard fields to sitemap entry

Revision ID: 20260525_02
Revises: 20260525_01
Create Date: 2026-05-25 19:55:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260525_02"
down_revision = "20260525_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("raw_web_sitemap_entry", sa.Column("changefreq", sa.String(length=32), nullable=True))
    op.add_column("raw_web_sitemap_entry", sa.Column("priority", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("raw_web_sitemap_entry", "priority")
    op.drop_column("raw_web_sitemap_entry", "changefreq")

