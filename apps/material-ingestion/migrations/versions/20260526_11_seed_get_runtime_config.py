"""seed get stage runtime config

Revision ID: 20260526_11
Revises: 20260526_10
Create Date: 2026-05-26
"""

from __future__ import annotations

from alembic import op


revision = "20260526_11"
down_revision = "20260526_10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO raw_web_runtime_config (config_key, config_value, enabled, note)
        VALUES
          ('core_worker_get_count', '0', true, 'Worker threads for frontier_get_requested stage'),
          ('core_get_scheduler_enabled', '0', true, 'Auto-enqueue frontier_get_requested events')
        ON CONFLICT (config_key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM raw_web_runtime_config
        WHERE config_key IN ('core_worker_get_count', 'core_get_scheduler_enabled')
        """
    )
