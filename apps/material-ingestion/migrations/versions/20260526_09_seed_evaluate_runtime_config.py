"""seed evaluate runtime config

Revision ID: 20260526_09
Revises: 20260526_08
Create Date: 2026-05-26
"""

from __future__ import annotations

from alembic import op


revision = "20260526_09"
down_revision = "20260526_08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO raw_web_runtime_config (config_key, config_value, enabled, note)
        VALUES
          ('core_worker_evaluate_count', '1', true, 'Worker threads for frontier_evaluate_requested stage'),
          ('core_evaluate_scheduler_enabled', '1', true, 'Auto-enqueue frontier_evaluate_requested events')
        ON CONFLICT (config_key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM raw_web_runtime_config
        WHERE config_key IN ('core_worker_evaluate_count', 'core_evaluate_scheduler_enabled')
        """
    )
