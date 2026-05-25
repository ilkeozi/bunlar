"""add crawler observation tables

Revision ID: 20260525_01
Revises: 20260524_09
Create Date: 2026-05-25 14:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260525_01"
down_revision = "20260524_09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "raw_web_http_fetch_attempt",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uri_identity_id", sa.Integer(), nullable=False),
        sa.Column("crawl_run_id", sa.Integer(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("outcome", sa.String(length=32), nullable=False, server_default="success"),
        sa.Column("reason_code", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["uri_identity_id"], ["raw_web_uri_identity.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["crawl_run_id"], ["raw_web_crawl_run.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "raw_web_http_representation",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("fetch_attempt_id", sa.Integer(), nullable=False),
        sa.Column("storage_ref", sa.Text(), nullable=False, server_default=""),
        sa.Column("content_type", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("etag", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("last_modified", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("cache_control", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("expires_full_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("metadata_only_since", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["fetch_attempt_id"], ["raw_web_http_fetch_attempt.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "raw_web_extracted_link",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_uri_identity_id", sa.Integer(), nullable=False),
        sa.Column("target_uri_identity_id", sa.Integer(), nullable=False),
        sa.Column("rel", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("anchor_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["source_uri_identity_id"], ["raw_web_uri_identity.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_uri_identity_id"], ["raw_web_uri_identity.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "raw_web_page_metadata",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uri_identity_id", sa.Integer(), nullable=False),
        sa.Column("canonical_hint", sa.Text(), nullable=False, server_default=""),
        sa.Column("robots_meta_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("hreflang_map_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["uri_identity_id"], ["raw_web_uri_identity.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "raw_web_structured_data_record",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uri_identity_id", sa.Integer(), nullable=False),
        sa.Column("format", sa.String(length=32), nullable=False, server_default="jsonld"),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["uri_identity_id"], ["raw_web_uri_identity.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "raw_web_candidate_document",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uri_identity_id", sa.Integer(), nullable=False),
        sa.Column("source_uri_identity_id", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("classification", sa.String(length=64), nullable=False, server_default="new"),
        sa.Column("decision_state", sa.String(length=32), nullable=False, server_default="new"),
        sa.Column("decision_reason_code", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["uri_identity_id"], ["raw_web_uri_identity.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_uri_identity_id"], ["raw_web_uri_identity.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uri_identity_id", "source_uri_identity_id", name="uq_raw_web_candidate_document_unique"),
    )
    op.create_index("ix_raw_web_candidate_document_uri", "raw_web_candidate_document", ["uri_identity_id"])


def downgrade() -> None:
    op.drop_index("ix_raw_web_candidate_document_uri", table_name="raw_web_candidate_document")
    op.drop_table("raw_web_candidate_document")
    op.drop_table("raw_web_structured_data_record")
    op.drop_table("raw_web_page_metadata")
    op.drop_table("raw_web_extracted_link")
    op.drop_table("raw_web_http_representation")
    op.drop_table("raw_web_http_fetch_attempt")
