"""rename hub terms to authority terms

Revision ID: 20260526_14
Revises: 20260526_13
Create Date: 2026-05-26
"""

from __future__ import annotations

from alembic import op


revision = "20260526_14"
down_revision = "20260526_13"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE raw_web_candidate_document
        SET decision_state = 'promoted_authority'
        WHERE decision_state = 'promoted_hub'
        """
    )
    op.execute(
        """
        UPDATE raw_web_candidate_document
        SET score_reason_json = replace(score_reason_json, '"hub_score":', '"authority_score":')
        WHERE score_reason_json LIKE '%"hub_score":%'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE raw_web_candidate_document
        SET decision_state = 'promoted_hub'
        WHERE decision_state = 'promoted_authority'
        """
    )
    op.execute(
        """
        UPDATE raw_web_candidate_document
        SET score_reason_json = replace(score_reason_json, '"authority_score":', '"hub_score":')
        WHERE score_reason_json LIKE '%"authority_score":%'
        """
    )
