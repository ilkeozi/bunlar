"""create raw web api evidence tables

Revision ID: 20260524_04
Revises: 20260524_03
Create Date: 2026-05-24 15:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260524_04"
down_revision = "20260524_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "raw_web_api_endpoint",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("orchestration_id", sa.String(length=64), nullable=False),
        sa.Column("ingest_batch_id", sa.String(length=64), nullable=False),
        sa.Column("source_page_url", sa.String(length=2048), nullable=False, server_default=""),
        sa.Column("endpoint_url", sa.String(length=2048), nullable=False),
        sa.Column("sample_request_url", sa.String(length=2048), nullable=False, server_default=""),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_raw_web_api_endpoint_orch_id", "raw_web_api_endpoint", ["orchestration_id", "id"], unique=False)
    op.create_index("ix_raw_web_api_endpoint_batch_id", "raw_web_api_endpoint", ["ingest_batch_id", "id"], unique=False)
    op.create_index("ix_raw_web_api_endpoint_endpoint_url", "raw_web_api_endpoint", ["endpoint_url"], unique=False)

    op.create_table(
        "raw_web_api_page_fetch",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("orchestration_id", sa.String(length=64), nullable=False),
        sa.Column("ingest_batch_id", sa.String(length=64), nullable=False),
        sa.Column("source_page_url", sa.String(length=2048), nullable=False, server_default=""),
        sa.Column("request_url", sa.String(length=2048), nullable=False),
        sa.Column("endpoint_url", sa.String(length=2048), nullable=False),
        sa.Column("page_index", sa.Integer(), nullable=False, server_default="-1"),
        sa.Column("page_limit", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status_code", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content_type", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("response_fingerprint_sha256", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("extracted_url_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("request_params_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_raw_web_api_page_fetch_orch_id", "raw_web_api_page_fetch", ["orchestration_id", "id"], unique=False)
    op.create_index("ix_raw_web_api_page_fetch_batch_id", "raw_web_api_page_fetch", ["ingest_batch_id", "id"], unique=False)
    op.create_index("ix_raw_web_api_page_fetch_request_url", "raw_web_api_page_fetch", ["request_url"], unique=False)

    op.create_table(
        "raw_web_api_document_candidate",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("orchestration_id", sa.String(length=64), nullable=False),
        sa.Column("ingest_batch_id", sa.String(length=64), nullable=False),
        sa.Column("source_page_url", sa.String(length=2048), nullable=False, server_default=""),
        sa.Column("response_url", sa.String(length=2048), nullable=False, server_default=""),
        sa.Column("document_url", sa.String(length=2048), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence_reason", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_raw_web_api_document_candidate_orch_id", "raw_web_api_document_candidate", ["orchestration_id", "id"], unique=False)
    op.create_index("ix_raw_web_api_document_candidate_batch_id", "raw_web_api_document_candidate", ["ingest_batch_id", "id"], unique=False)
    op.create_index("ix_raw_web_api_document_candidate_document_url", "raw_web_api_document_candidate", ["document_url"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_raw_web_api_document_candidate_document_url", table_name="raw_web_api_document_candidate")
    op.drop_index("ix_raw_web_api_document_candidate_batch_id", table_name="raw_web_api_document_candidate")
    op.drop_index("ix_raw_web_api_document_candidate_orch_id", table_name="raw_web_api_document_candidate")
    op.drop_table("raw_web_api_document_candidate")

    op.drop_index("ix_raw_web_api_page_fetch_request_url", table_name="raw_web_api_page_fetch")
    op.drop_index("ix_raw_web_api_page_fetch_batch_id", table_name="raw_web_api_page_fetch")
    op.drop_index("ix_raw_web_api_page_fetch_orch_id", table_name="raw_web_api_page_fetch")
    op.drop_table("raw_web_api_page_fetch")

    op.drop_index("ix_raw_web_api_endpoint_endpoint_url", table_name="raw_web_api_endpoint")
    op.drop_index("ix_raw_web_api_endpoint_batch_id", table_name="raw_web_api_endpoint")
    op.drop_index("ix_raw_web_api_endpoint_orch_id", table_name="raw_web_api_endpoint")
    op.drop_table("raw_web_api_endpoint")
