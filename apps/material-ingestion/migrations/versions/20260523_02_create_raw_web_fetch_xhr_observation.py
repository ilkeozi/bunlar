"""create raw web fetch xhr observation table

Revision ID: 20260523_02
Revises: 20260523_01
Create Date: 2026-05-23 16:45:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260523_02"
down_revision: Union[str, Sequence[str], None] = "20260523_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "raw_web_fetch_xhr_observation",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ingest_source", sa.String(length=64), nullable=False),
        sa.Column("ingest_locator", sa.Text(), nullable=False),
        sa.Column("ingest_batch_id", sa.String(length=64), nullable=False),
        sa.Column("source_page_url", sa.Text(), nullable=False),
        sa.Column("response_url", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.String(length=32), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("is_json", sa.Boolean(), nullable=False),
        sa.Column("extracted_urls_json", sa.Text(), nullable=False),
        sa.Column("extracted_url_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ingest_source",
            "ingest_batch_id",
            "source_page_url",
            "response_url",
            name="uq_raw_web_fetch_xhr_observation_natural",
        ),
    )
    op.create_index(
        "ix_raw_web_fetch_xhr_observation_source_page_url",
        "raw_web_fetch_xhr_observation",
        ["source_page_url"],
        unique=False,
    )
    op.create_index(
        "ix_raw_web_fetch_xhr_observation_response_url",
        "raw_web_fetch_xhr_observation",
        ["response_url"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_raw_web_fetch_xhr_observation_response_url", table_name="raw_web_fetch_xhr_observation")
    op.drop_index("ix_raw_web_fetch_xhr_observation_source_page_url", table_name="raw_web_fetch_xhr_observation")
    op.drop_table("raw_web_fetch_xhr_observation")
