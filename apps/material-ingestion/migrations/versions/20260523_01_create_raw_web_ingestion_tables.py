"""create raw web ingestion tables

Revision ID: 20260523_01
Revises: 20260522_04
Create Date: 2026-05-23 14:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260523_01"
down_revision: Union[str, Sequence[str], None] = "20260522_04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "raw_web_page_crawl",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ingest_source", sa.String(length=64), nullable=False),
        sa.Column("ingest_locator", sa.Text(), nullable=False),
        sa.Column("ingest_batch_id", sa.String(length=64), nullable=False),
        sa.Column("page_url", sa.Text(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("crawl_ok", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ingest_source", "ingest_batch_id", "page_url", name="uq_raw_web_page_crawl_natural"),
    )
    op.create_index("ix_raw_web_page_crawl_page_url", "raw_web_page_crawl", ["page_url"], unique=False)

    op.create_table(
        "raw_web_pdf_candidate",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ingest_source", sa.String(length=64), nullable=False),
        sa.Column("ingest_locator", sa.Text(), nullable=False),
        sa.Column("ingest_batch_id", sa.String(length=64), nullable=False),
        sa.Column("source_page_url", sa.Text(), nullable=False),
        sa.Column("pdf_url", sa.Text(), nullable=False),
        sa.Column("anchor_text", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ingest_source", "ingest_batch_id", "pdf_url", name="uq_raw_web_pdf_candidate_natural"),
    )
    op.create_index("ix_raw_web_pdf_candidate_pdf_url", "raw_web_pdf_candidate", ["pdf_url"], unique=False)
    op.create_index("ix_raw_web_pdf_candidate_score", "raw_web_pdf_candidate", ["score"], unique=False)

    op.create_table(
        "raw_web_downloaded_file",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ingest_source", sa.String(length=64), nullable=False),
        sa.Column("ingest_locator", sa.Text(), nullable=False),
        sa.Column("ingest_batch_id", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("stored_path", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ingest_source",
            "ingest_batch_id",
            "source_url",
            name="uq_raw_web_downloaded_file_natural",
        ),
    )
    op.create_index("ix_raw_web_downloaded_file_sha256", "raw_web_downloaded_file", ["sha256"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_raw_web_downloaded_file_sha256", table_name="raw_web_downloaded_file")
    op.drop_table("raw_web_downloaded_file")

    op.drop_index("ix_raw_web_pdf_candidate_score", table_name="raw_web_pdf_candidate")
    op.drop_index("ix_raw_web_pdf_candidate_pdf_url", table_name="raw_web_pdf_candidate")
    op.drop_table("raw_web_pdf_candidate")

    op.drop_index("ix_raw_web_page_crawl_page_url", table_name="raw_web_page_crawl")
    op.drop_table("raw_web_page_crawl")
