"""add sitemap extension fields to sitemap entry

Revision ID: 20260525_03
Revises: 20260525_02
Create Date: 2026-05-25 20:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260525_03"
down_revision = "20260525_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("raw_web_sitemap_entry", sa.Column("alternates_json", sa.Text(), nullable=True))
    op.add_column("raw_web_sitemap_entry", sa.Column("images_json", sa.Text(), nullable=True))
    op.add_column("raw_web_sitemap_entry", sa.Column("news_story_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("raw_web_sitemap_entry", "news_story_json")
    op.drop_column("raw_web_sitemap_entry", "images_json")
    op.drop_column("raw_web_sitemap_entry", "alternates_json")

