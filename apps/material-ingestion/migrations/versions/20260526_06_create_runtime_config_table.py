"""create runtime config table

Revision ID: 20260526_06
Revises: 20260526_05
Create Date: 2026-05-26 14:25:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260526_06"
down_revision = "20260526_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "raw_web_runtime_config",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("config_key", sa.String(length=64), nullable=False),
        sa.Column("config_value", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("config_key", name="uq_raw_web_runtime_config_key"),
    )

    op.execute(
        """
        INSERT INTO raw_web_runtime_config (config_key, config_value, enabled, note) VALUES
        ('core_worker_discover_count', '1', true, 'default discover stage worker count'),
        ('core_worker_build_count', '1', true, 'default build stage worker count'),
        ('core_worker_fetch_count', '1', true, 'default fetch stage worker count');
        """
    )

    op.alter_column("raw_web_runtime_config", "enabled", server_default=None)
    op.alter_column("raw_web_runtime_config", "note", server_default=None)


def downgrade() -> None:
    op.drop_table("raw_web_runtime_config")

