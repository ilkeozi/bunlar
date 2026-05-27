"""seed get retry/backoff runtime config

Revision ID: 20260526_12
Revises: 20260526_11
Create Date: 2026-05-26
"""

from __future__ import annotations

from alembic import op


revision = "20260526_12"
down_revision = "20260526_11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO raw_web_runtime_config (config_key, config_value, enabled, note)
        VALUES
          ('core_get_max_retries', '3', true, 'Max retries for Phase-B GET failures'),
          ('core_get_backoff_base_seconds', '15', true, 'Base backoff seconds for Phase-B GET retries'),
          ('core_get_backoff_max_seconds', '300', true, 'Max backoff seconds for Phase-B GET retries')
        ON CONFLICT (config_key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM raw_web_runtime_config
        WHERE config_key IN (
          'core_get_max_retries',
          'core_get_backoff_base_seconds',
          'core_get_backoff_max_seconds'
        )
        """
    )
