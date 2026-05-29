"""add ttfb_ms, read_ms, total_ms to raw_web_http_fetch_attempt

Revision ID: 20260527_18
Revises: 20260527_17
Create Date: 2026-05-27
"""

from __future__ import annotations

from alembic import op

revision = "20260527_18"
down_revision = "20260527_17"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE raw_web_http_fetch_attempt
            ADD COLUMN IF NOT EXISTS ttfb_ms  INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS read_ms  INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS total_ms INTEGER NOT NULL DEFAULT 0
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE raw_web_http_fetch_attempt
            DROP COLUMN IF EXISTS ttfb_ms,
            DROP COLUMN IF EXISTS read_ms,
            DROP COLUMN IF EXISTS total_ms
        """
    )
