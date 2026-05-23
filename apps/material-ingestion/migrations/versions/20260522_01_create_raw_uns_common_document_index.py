"""create raw uns common document index table

Revision ID: 20260522_01
Revises: 
Create Date: 2026-05-22 19:40:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260522_01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "raw_uns_common_document_index",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ingest_source", sa.String(length=64), nullable=False),
        sa.Column("ingest_locator", sa.Text(), nullable=False),
        sa.Column("ingest_batch_id", sa.String(length=64), nullable=False),
        sa.Column("toc_page", sa.Integer(), nullable=False),
        sa.Column("document_code_raw", sa.String(length=64), nullable=False),
        sa.Column("document_code", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_label", sa.String(length=64), nullable=False),
        sa.Column("target_page", sa.Integer(), nullable=False),
        sa.Column("page_resolution", sa.String(length=32), nullable=False),
        sa.Column("extraction_method", sa.String(length=64), nullable=False),
        sa.Column("ocr_used", sa.Boolean(), nullable=False),
        sa.Column("raw_line", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("char_length(document_code) > 0", name="ck_raw_uns_common_doc_code_nonempty"),
        sa.CheckConstraint("target_page > 0", name="ck_raw_uns_common_doc_target_page_pos"),
        sa.CheckConstraint("toc_page > 0", name="ck_raw_uns_common_doc_toc_page_pos"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ingest_source",
            "ingest_batch_id",
            "toc_page",
            "document_code",
            "target_page",
            name="uq_raw_uns_common_doc_natural",
        ),
    )
    op.create_index("ix_raw_uns_common_doc_code", "raw_uns_common_document_index", ["document_code"], unique=False)
    op.create_index("ix_raw_uns_common_doc_target_page", "raw_uns_common_document_index", ["target_page"], unique=False)
    op.create_index("ix_raw_uns_common_doc_toc_target", "raw_uns_common_document_index", ["toc_page", "target_page"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_raw_uns_common_doc_toc_target", table_name="raw_uns_common_document_index")
    op.drop_index("ix_raw_uns_common_doc_target_page", table_name="raw_uns_common_document_index")
    op.drop_index("ix_raw_uns_common_doc_code", table_name="raw_uns_common_document_index")
    op.drop_table("raw_uns_common_document_index")
