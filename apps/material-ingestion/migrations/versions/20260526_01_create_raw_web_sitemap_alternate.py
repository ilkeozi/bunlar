"""create normalized sitemap alternates table

Revision ID: 20260526_01
Revises: 20260525_04
Create Date: 2026-05-26 00:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260526_01"
down_revision = "20260525_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "raw_web_sitemap_alternate",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sitemap_entry_id", sa.Integer(), nullable=False),
        sa.Column("hreflang", sa.String(length=64), nullable=False),
        sa.Column("href", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["sitemap_entry_id"], ["raw_web_sitemap_entry.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sitemap_entry_id", "hreflang", "href", name="uq_raw_web_sitemap_alternate_unique"),
    )
    op.create_index("ix_raw_web_sitemap_alternate_hreflang", "raw_web_sitemap_alternate", ["hreflang"], unique=False)
    op.create_index("ix_raw_web_sitemap_alternate_entry", "raw_web_sitemap_alternate", ["sitemap_entry_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_raw_web_sitemap_alternate_entry", table_name="raw_web_sitemap_alternate")
    op.drop_index("ix_raw_web_sitemap_alternate_hreflang", table_name="raw_web_sitemap_alternate")
    op.drop_table("raw_web_sitemap_alternate")
