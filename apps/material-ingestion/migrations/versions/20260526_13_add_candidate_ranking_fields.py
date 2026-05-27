"""add candidate ranking fields

Revision ID: 20260526_13
Revises: 20260526_12
Create Date: 2026-05-26
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260526_13"
down_revision = "20260526_12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "raw_web_candidate_document",
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "raw_web_candidate_document",
        sa.Column("distinct_source_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "raw_web_candidate_document",
        sa.Column("score_reason_json", sa.Text(), nullable=False, server_default="{}"),
    )
    op.alter_column("raw_web_candidate_document", "score", server_default=None)
    op.alter_column("raw_web_candidate_document", "distinct_source_count", server_default=None)
    op.alter_column("raw_web_candidate_document", "score_reason_json", server_default=None)


def downgrade() -> None:
    op.drop_column("raw_web_candidate_document", "score_reason_json")
    op.drop_column("raw_web_candidate_document", "distinct_source_count")
    op.drop_column("raw_web_candidate_document", "score")
