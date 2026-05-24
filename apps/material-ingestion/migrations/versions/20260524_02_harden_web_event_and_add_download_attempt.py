"""harden web event table and add download attempt telemetry

Revision ID: 20260524_02
Revises: 20260524_01
Create Date: 2026-05-24 14:35:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260524_02"
down_revision: Union[str, Sequence[str], None] = "20260524_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("raw_web_ingestion_event", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("raw_web_ingestion_event", sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("raw_web_ingestion_event", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("raw_web_ingestion_event", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("raw_web_ingestion_event", sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("raw_web_ingestion_event", "attempt_count", server_default=None)

    op.create_table(
        "raw_web_download_attempt",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ingest_source", sa.String(length=64), nullable=False),
        sa.Column("ingest_locator", sa.Text(), nullable=False),
        sa.Column("ingest_batch_id", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("wait_seconds", sa.Integer(), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=False),
        sa.Column("error_class", sa.String(length=128), nullable=False),
        sa.Column("error_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("raw_web_download_attempt")
    op.drop_column("raw_web_ingestion_event", "heartbeat_at")
    op.drop_column("raw_web_ingestion_event", "finished_at")
    op.drop_column("raw_web_ingestion_event", "started_at")
    op.drop_column("raw_web_ingestion_event", "next_retry_at")
    op.drop_column("raw_web_ingestion_event", "attempt_count")

