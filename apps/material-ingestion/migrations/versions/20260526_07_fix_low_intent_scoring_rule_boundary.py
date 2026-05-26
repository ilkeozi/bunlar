"""fix low-intent scoring rule to boundary-aware regex

Revision ID: 20260526_07
Revises: 20260526_06
Create Date: 2026-05-26 14:55:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "20260526_07"
down_revision = "20260526_06"
branch_labels = None
depends_on = None


_OLD_PATTERN = "(legal|privacy|cookie|career|jobs|press|news|investor|media)"
_NEW_PATTERN = "(^|[/._-])(legal|privacy|cookie|career|jobs|press|news|investor|media)([/._-]|$)"


def upgrade() -> None:
    op.execute(
        f"""
        UPDATE raw_web_frontier_score_rule
        SET pattern = '{_NEW_PATTERN}',
            note = 'low-intent sections (boundary-aware)'
        WHERE match_type = 'regex'
          AND weight = -8
          AND priority = 90
          AND pattern = '{_OLD_PATTERN}';
        """
    )


def downgrade() -> None:
    op.execute(
        f"""
        UPDATE raw_web_frontier_score_rule
        SET pattern = '{_OLD_PATTERN}',
            note = 'low-intent sections'
        WHERE match_type = 'regex'
          AND weight = -8
          AND priority = 90
          AND pattern = '{_NEW_PATTERN}';
        """
    )

