"""create frontier score rules

Revision ID: 20260526_04
Revises: 20260526_03
Create Date: 2026-05-26 13:20:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


revision = "20260526_04"
down_revision = "20260526_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "raw_web_frontier_score_rule",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_type", sa.String(length=16), nullable=False, server_default="contains"),
        sa.Column("pattern", sa.String(length=255), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("match_type", "pattern", name="uq_raw_web_frontier_score_rule"),
    )
    op.create_index(
        "ix_raw_web_frontier_score_rule_enabled_priority",
        "raw_web_frontier_score_rule",
        ["enabled", "priority"],
        unique=False,
    )

    op.execute(
        """
        INSERT INTO raw_web_frontier_score_rule (match_type, pattern, weight, enabled, priority, note) VALUES
        ('regex', '\\.(pdf|doc|docx|xls|xlsx|ppt|pptx)(\\?|$)', 15, true, 10, 'direct document extensions'),
        ('regex', '(datasheet|technical-data-sheet|tds|sds|msds|specification)', 10, true, 20, 'technical document intent'),
        ('regex', '(download|document|product-detail|product)', 5, true, 30, 'general document/product intent'),
        ('regex', '(legal|privacy|cookie|career|jobs|press|news|investor|media)', -8, true, 90, 'low-intent sections');
        """
    )


def downgrade() -> None:
    op.drop_index("ix_raw_web_frontier_score_rule_enabled_priority", table_name="raw_web_frontier_score_rule")
    op.drop_table("raw_web_frontier_score_rule")

