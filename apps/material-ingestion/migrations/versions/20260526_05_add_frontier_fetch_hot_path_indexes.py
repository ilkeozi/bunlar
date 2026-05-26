"""add frontier fetch hot path indexes

Revision ID: 20260526_05
Revises: 20260526_04
Create Date: 2026-05-26 13:50:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Union

from alembic import op


revision = "20260526_05"
down_revision = "20260526_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_raw_web_frontier_item_run_state_priority_id",
        "raw_web_frontier_item",
        ["crawl_run_id", "state", "priority", "id"],
        unique=False,
    )
    op.create_index(
        "ix_raw_web_http_fetch_attempt_uri_outcome_completed",
        "raw_web_http_fetch_attempt",
        ["uri_identity_id", "outcome", "completed_at"],
        unique=False,
    )
    op.create_index(
        "ix_raw_web_http_fetch_attempt_run_id",
        "raw_web_http_fetch_attempt",
        ["crawl_run_id", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_raw_web_http_fetch_attempt_run_id", table_name="raw_web_http_fetch_attempt")
    op.drop_index("ix_raw_web_http_fetch_attempt_uri_outcome_completed", table_name="raw_web_http_fetch_attempt")
    op.drop_index("ix_raw_web_frontier_item_run_state_priority_id", table_name="raw_web_frontier_item")

