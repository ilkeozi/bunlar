"""add index on raw_web_crawl_decision (uri_identity_id, reason_code)

Revision ID: 20260527_16
Revises: 20260526_15
Create Date: 2026-05-27
"""

from __future__ import annotations

from alembic import op

revision = "20260527_16"
down_revision = "20260526_15"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_raw_web_crawl_decision_uri_reason
          ON raw_web_crawl_decision (uri_identity_id, reason_code)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_raw_web_crawl_decision_uri_reason")
