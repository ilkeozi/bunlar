"""create raw web ingestion event table

Revision ID: 20260524_01
Revises: 20260523_02
Create Date: 2026-05-24 14:20:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260524_01"
down_revision: Union[str, Sequence[str], None] = "20260523_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "raw_web_ingestion_event",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("orchestration_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("error_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_raw_web_ingestion_event_orch_status",
        "raw_web_ingestion_event",
        ["orchestration_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_raw_web_ingestion_event_orch_id",
        "raw_web_ingestion_event",
        ["orchestration_id", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_raw_web_ingestion_event_orch_id", table_name="raw_web_ingestion_event")
    op.drop_index("ix_raw_web_ingestion_event_orch_status", table_name="raw_web_ingestion_event")
    op.drop_table("raw_web_ingestion_event")

