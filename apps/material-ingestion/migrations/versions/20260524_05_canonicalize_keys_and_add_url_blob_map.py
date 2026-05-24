"""canonicalize keys and add url blob map

Revision ID: 20260524_05
Revises: 20260524_04
Create Date: 2026-05-24 15:15:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260524_05"
down_revision = "20260524_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("raw_web_pdf_candidate", sa.Column("canonical_pdf_url", sa.Text(), nullable=True))
    op.execute("update raw_web_pdf_candidate set canonical_pdf_url = pdf_url where canonical_pdf_url is null")
    op.alter_column("raw_web_pdf_candidate", "canonical_pdf_url", nullable=False)
    op.drop_constraint("uq_raw_web_pdf_candidate_natural", "raw_web_pdf_candidate", type_="unique")
    op.create_unique_constraint(
        "uq_raw_web_pdf_candidate_natural",
        "raw_web_pdf_candidate",
        ["ingest_source", "ingest_batch_id", "canonical_pdf_url"],
    )

    op.add_column("raw_web_downloaded_file", sa.Column("canonical_source_url", sa.Text(), nullable=True))
    op.execute("update raw_web_downloaded_file set canonical_source_url = source_url where canonical_source_url is null")
    op.alter_column("raw_web_downloaded_file", "canonical_source_url", nullable=False)
    op.drop_constraint("uq_raw_web_downloaded_file_natural", "raw_web_downloaded_file", type_="unique")
    op.create_unique_constraint(
        "uq_raw_web_downloaded_file_natural",
        "raw_web_downloaded_file",
        ["ingest_source", "ingest_batch_id", "canonical_source_url"],
    )

    op.create_table(
        "raw_web_url_blob_map",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("canonical_source_url", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("first_seen_batch_id", sa.String(length=64), nullable=False),
        sa.Column("last_seen_batch_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("canonical_source_url", name="uq_raw_web_url_blob_map_canonical_url"),
    )


def downgrade() -> None:
    op.drop_table("raw_web_url_blob_map")

    op.drop_constraint("uq_raw_web_downloaded_file_natural", "raw_web_downloaded_file", type_="unique")
    op.create_unique_constraint(
        "uq_raw_web_downloaded_file_natural",
        "raw_web_downloaded_file",
        ["ingest_source", "ingest_batch_id", "source_url"],
    )
    op.drop_column("raw_web_downloaded_file", "canonical_source_url")

    op.drop_constraint("uq_raw_web_pdf_candidate_natural", "raw_web_pdf_candidate", type_="unique")
    op.create_unique_constraint(
        "uq_raw_web_pdf_candidate_natural",
        "raw_web_pdf_candidate",
        ["ingest_source", "ingest_batch_id", "pdf_url"],
    )
    op.drop_column("raw_web_pdf_candidate", "canonical_pdf_url")
