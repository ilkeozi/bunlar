"""add unique constraint on raw_web_extracted_link (source, target)

Revision ID: 20260527_17
Revises: 20260527_16
Create Date: 2026-05-27
"""

from __future__ import annotations

from alembic import op

revision = "20260527_17"
down_revision = "20260527_16"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove duplicate rows, keeping the lowest id per (source, target) pair.
    op.execute(
        """
        DELETE FROM raw_web_extracted_link
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM raw_web_extracted_link
            GROUP BY source_uri_identity_id, target_uri_identity_id
        )
        """
    )
    # Drop the non-unique index — the unique constraint below creates its own.
    op.execute("DROP INDEX IF EXISTS ix_raw_web_extracted_link_source_target")
    op.execute(
        """
        ALTER TABLE raw_web_extracted_link
        ADD CONSTRAINT uq_raw_web_extracted_link_source_target
        UNIQUE (source_uri_identity_id, target_uri_identity_id)
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE raw_web_extracted_link DROP CONSTRAINT IF EXISTS uq_raw_web_extracted_link_source_target"
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_raw_web_extracted_link_source_target
          ON raw_web_extracted_link (source_uri_identity_id, target_uri_identity_id)
        """
    )
