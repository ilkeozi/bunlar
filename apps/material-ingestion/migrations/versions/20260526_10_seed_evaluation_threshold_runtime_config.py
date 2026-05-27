"""seed evaluation threshold runtime config

Revision ID: 20260526_10
Revises: 20260526_09
Create Date: 2026-05-26
"""

from __future__ import annotations

from alembic import op


revision = "20260526_10"
down_revision = "20260526_09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO raw_web_runtime_config (config_key, config_value, enabled, note)
        VALUES ('core_evaluation_promote_threshold', '6', true, 'Promote threshold for frontier evaluation scoring')
        ON CONFLICT (config_key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM raw_web_runtime_config
        WHERE config_key = 'core_evaluation_promote_threshold'
        """
    )
