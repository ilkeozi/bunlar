"""create evaluation rules

Revision ID: 20260526_08
Revises: 20260526_07
Create Date: 2026-05-26
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260526_08"
down_revision = "20260526_07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "raw_web_evaluation_rule",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False, server_default="defer"),
        sa.Column("match_type", sa.String(length=16), nullable=False, server_default="contains"),
        sa.Column("pattern", sa.String(length=255), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("action", "match_type", "pattern", name="uq_raw_web_evaluation_rule"),
    )
    op.create_index(
        "ix_raw_web_evaluation_rule_enabled_priority",
        "raw_web_evaluation_rule",
        ["enabled", "priority"],
        unique=False,
    )
    op.execute(
        """
        INSERT INTO raw_web_evaluation_rule (action, match_type, pattern, weight, enabled, priority, note) VALUES
          ('promote', 'contains', '/product', 6, true, 20, 'Product pages are high-intent'),
          ('promote', 'contains', '/document/', 8, true, 30, 'Document paths are strong signals'),
          ('promote', 'contains', '/datasheet', 10, true, 40, 'Datasheet URL signal'),
          ('skip', 'regex', '(^|[/._-])(legal|privacy|cookie)([/._-]|$)', -8, true, 200, 'Policy/legal pages'),
          ('skip', 'regex', '(^|[/._-])(career|jobs)([/._-]|$)', -6, true, 210, 'Career pages'),
          ('defer', 'regex', '(^|[/._-])(press|news|investor|media)([/._-]|$)', -4, true, 220, 'Lower priority news/media pages')
        """
    )
    op.alter_column("raw_web_evaluation_rule", "action", server_default=None)
    op.alter_column("raw_web_evaluation_rule", "match_type", server_default=None)
    op.alter_column("raw_web_evaluation_rule", "weight", server_default=None)
    op.alter_column("raw_web_evaluation_rule", "enabled", server_default=None)
    op.alter_column("raw_web_evaluation_rule", "priority", server_default=None)
    op.alter_column("raw_web_evaluation_rule", "note", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_raw_web_evaluation_rule_enabled_priority", table_name="raw_web_evaluation_rule")
    op.drop_table("raw_web_evaluation_rule")
