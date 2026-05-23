"""create additional raw uns tables

Revision ID: 20260522_02
Revises: 20260522_01
Create Date: 2026-05-22 20:05:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260522_02"
down_revision: Union[str, Sequence[str], None] = "20260522_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "raw_uns_aws_cross_reference",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ingest_source", sa.String(length=64), nullable=False),
        sa.Column("ingest_locator", sa.Text(), nullable=False),
        sa.Column("ingest_batch_id", sa.String(length=64), nullable=False),
        sa.Column("aws_spec", sa.String(length=64), nullable=False),
        sa.Column("aws_designation", sa.String(length=128), nullable=False),
        sa.Column("uns", sa.String(length=16), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("raw_line", sa.Text(), nullable=False),
        sa.Column("extraction_method", sa.String(length=64), nullable=False),
        sa.Column("ocr_used", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("page > 0", name="ck_raw_uns_aws_page_pos"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ingest_source",
            "ingest_batch_id",
            "aws_spec",
            "aws_designation",
            "uns",
            name="uq_raw_uns_aws_natural",
        ),
    )
    op.create_index("ix_raw_uns_aws_spec", "raw_uns_aws_cross_reference", ["aws_spec"], unique=False)
    op.create_index("ix_raw_uns_aws_uns", "raw_uns_aws_cross_reference", ["uns"], unique=False)

    op.create_table(
        "raw_uns_base_elements_index",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ingest_source", sa.String(length=64), nullable=False),
        sa.Column("ingest_locator", sa.Text(), nullable=False),
        sa.Column("ingest_batch_id", sa.String(length=64), nullable=False),
        sa.Column("element_name", sa.String(length=128), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("uns_range", sa.String(length=64), nullable=False),
        sa.Column("index_label", sa.String(length=32), nullable=False),
        sa.Column("index_pdf_page", sa.Integer(), nullable=False),
        sa.Column("row_order", sa.Integer(), nullable=False),
        sa.Column("extraction_method", sa.String(length=64), nullable=False),
        sa.Column("ocr_used", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("index_pdf_page > 0", name="ck_raw_uns_base_idx_page_pos"),
        sa.CheckConstraint("row_order >= 0", name="ck_raw_uns_base_row_order_nonneg"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ingest_source",
            "ingest_batch_id",
            "element_name",
            "symbol",
            "uns_range",
            name="uq_raw_uns_base_natural",
        ),
    )
    op.create_index("ix_raw_uns_base_symbol", "raw_uns_base_elements_index", ["symbol"], unique=False)

    op.create_table(
        "raw_uns_series_page_index",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ingest_source", sa.String(length=64), nullable=False),
        sa.Column("ingest_locator", sa.Text(), nullable=False),
        sa.Column("ingest_batch_id", sa.String(length=64), nullable=False),
        sa.Column("series", sa.String(length=64), nullable=False),
        sa.Column("series_token", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_label", sa.String(length=32), nullable=False),
        sa.Column("target_page", sa.Integer(), nullable=False),
        sa.Column("target_pdf_page", sa.Integer(), nullable=True),
        sa.Column("page_resolution", sa.String(length=32), nullable=False),
        sa.Column("section_start_pdf_page", sa.Integer(), nullable=True),
        sa.Column("section_end_pdf_page", sa.Integer(), nullable=True),
        sa.Column("toc_page", sa.Integer(), nullable=False),
        sa.Column("extraction_method", sa.String(length=64), nullable=False),
        sa.Column("ocr_used", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("target_page > 0", name="ck_raw_uns_series_idx_target_page_pos"),
        sa.CheckConstraint("toc_page > 0", name="ck_raw_uns_series_idx_toc_page_pos"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ingest_source",
            "ingest_batch_id",
            "series_token",
            "target_page",
            name="uq_raw_uns_series_idx_natural",
        ),
    )
    op.create_index("ix_raw_uns_series_idx_token", "raw_uns_series_page_index", ["series_token"], unique=False)

    op.create_table(
        "raw_uns_series_entry",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ingest_source", sa.String(length=64), nullable=False),
        sa.Column("ingest_locator", sa.Text(), nullable=False),
        sa.Column("ingest_batch_id", sa.String(length=64), nullable=False),
        sa.Column("series_token", sa.String(length=32), nullable=False),
        sa.Column("series_description", sa.Text(), nullable=False),
        sa.Column("uns_code", sa.String(length=16), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("chemical_composition_structured", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("chemical_composition_symbol_check", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cross_reference_specifications_structured", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cross_reference_specifications_check", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("entry_pdf_page_start", sa.Integer(), nullable=False),
        sa.Column("entry_pdf_page_end", sa.Integer(), nullable=False),
        sa.Column("is_replaced", sa.Boolean(), nullable=False),
        sa.Column("inactive_boxed", sa.Boolean(), nullable=False),
        sa.Column("extraction_method", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("entry_pdf_page_end >= entry_pdf_page_start", name="ck_raw_uns_series_entry_end_ge_start"),
        sa.CheckConstraint("entry_pdf_page_start > 0", name="ck_raw_uns_series_entry_start_page_pos"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ingest_source",
            "ingest_batch_id",
            "series_token",
            "uns_code",
            name="uq_raw_uns_series_entry_natural",
        ),
    )
    op.create_index("ix_raw_uns_series_entry_series_token", "raw_uns_series_entry", ["series_token"], unique=False)
    op.create_index("ix_raw_uns_series_entry_uns_code", "raw_uns_series_entry", ["uns_code"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_raw_uns_series_entry_uns_code", table_name="raw_uns_series_entry")
    op.drop_index("ix_raw_uns_series_entry_series_token", table_name="raw_uns_series_entry")
    op.drop_table("raw_uns_series_entry")

    op.drop_index("ix_raw_uns_series_idx_token", table_name="raw_uns_series_page_index")
    op.drop_table("raw_uns_series_page_index")

    op.drop_index("ix_raw_uns_base_symbol", table_name="raw_uns_base_elements_index")
    op.drop_table("raw_uns_base_elements_index")

    op.drop_index("ix_raw_uns_aws_uns", table_name="raw_uns_aws_cross_reference")
    op.drop_index("ix_raw_uns_aws_spec", table_name="raw_uns_aws_cross_reference")
    op.drop_table("raw_uns_aws_cross_reference")
