"""create raw web stage event tables

Revision ID: 20260524_03
Revises: 20260524_02
Create Date: 2026-05-24 14:45:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260524_03"
down_revision = "20260524_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "raw_web_discovery_event",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("orchestration_id", sa.String(length=64), nullable=False),
        sa.Column("ingest_batch_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("page_url", sa.String(length=2048), nullable=False, server_default=""),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_raw_web_discovery_event_orch_id",
        "raw_web_discovery_event",
        ["orchestration_id", "id"],
        unique=False,
    )
    op.create_index(
        "ix_raw_web_discovery_event_batch_id",
        "raw_web_discovery_event",
        ["ingest_batch_id", "id"],
        unique=False,
    )

    op.create_table(
        "raw_web_candidate_event",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("orchestration_id", sa.String(length=64), nullable=False),
        sa.Column("ingest_batch_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_page_url", sa.String(length=2048), nullable=False, server_default=""),
        sa.Column("pdf_url", sa.String(length=2048), nullable=False, server_default=""),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_raw_web_candidate_event_orch_id",
        "raw_web_candidate_event",
        ["orchestration_id", "id"],
        unique=False,
    )
    op.create_index(
        "ix_raw_web_candidate_event_batch_id",
        "raw_web_candidate_event",
        ["ingest_batch_id", "id"],
        unique=False,
    )
    op.create_index(
        "ix_raw_web_candidate_event_pdf_url",
        "raw_web_candidate_event",
        ["pdf_url"],
        unique=False,
    )

    op.create_table(
        "raw_web_download_event",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("orchestration_id", sa.String(length=64), nullable=False),
        sa.Column("ingest_batch_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=False, server_default=""),
        sa.Column("status_code", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_raw_web_download_event_orch_id",
        "raw_web_download_event",
        ["orchestration_id", "id"],
        unique=False,
    )
    op.create_index(
        "ix_raw_web_download_event_batch_id",
        "raw_web_download_event",
        ["ingest_batch_id", "id"],
        unique=False,
    )
    op.create_index(
        "ix_raw_web_download_event_source_url",
        "raw_web_download_event",
        ["source_url"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_raw_web_download_event_source_url", table_name="raw_web_download_event")
    op.drop_index("ix_raw_web_download_event_batch_id", table_name="raw_web_download_event")
    op.drop_index("ix_raw_web_download_event_orch_id", table_name="raw_web_download_event")
    op.drop_table("raw_web_download_event")

    op.drop_index("ix_raw_web_candidate_event_pdf_url", table_name="raw_web_candidate_event")
    op.drop_index("ix_raw_web_candidate_event_batch_id", table_name="raw_web_candidate_event")
    op.drop_index("ix_raw_web_candidate_event_orch_id", table_name="raw_web_candidate_event")
    op.drop_table("raw_web_candidate_event")

    op.drop_index("ix_raw_web_discovery_event_batch_id", table_name="raw_web_discovery_event")
    op.drop_index("ix_raw_web_discovery_event_orch_id", table_name="raw_web_discovery_event")
    op.drop_table("raw_web_discovery_event")
