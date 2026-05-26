"""create crawl allowlist rules table

Revision ID: 20260526_03
Revises: 20260526_02
Create Date: 2026-05-26 01:20:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260526_03"
down_revision = "20260526_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "raw_web_crawl_allowlist_rule",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pattern", sa.String(length=255), nullable=False),
        sa.Column("rule_type", sa.String(length=32), nullable=False, server_default="host_glob"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pattern", "rule_type", name="uq_raw_web_crawl_allowlist_rule"),
    )
    op.alter_column("raw_web_crawl_allowlist_rule", "rule_type", server_default=None)
    op.alter_column("raw_web_crawl_allowlist_rule", "enabled", server_default=None)
    op.alter_column("raw_web_crawl_allowlist_rule", "priority", server_default=None)
    op.alter_column("raw_web_crawl_allowlist_rule", "note", server_default=None)


def downgrade() -> None:
    op.drop_table("raw_web_crawl_allowlist_rule")
