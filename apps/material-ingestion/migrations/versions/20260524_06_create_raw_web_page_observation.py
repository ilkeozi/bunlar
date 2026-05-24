"""create raw_web_page_observation table

Revision ID: 20260524_06
Revises: 20260524_05
Create Date: 2026-05-24 18:50:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260524_06"
down_revision = "20260524_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "raw_web_page_observation",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ingest_source", sa.String(length=64), nullable=False),
        sa.Column("ingest_locator", sa.Text(), nullable=False),
        sa.Column("ingest_batch_id", sa.String(length=64), nullable=False),
        sa.Column("page_url", sa.Text(), nullable=False),
        sa.Column("page_title", sa.Text(), nullable=False, server_default=""),
        sa.Column("text_excerpt", sa.Text(), nullable=False, server_default=""),
        sa.Column("anchor_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("input_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("button_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("form_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("has_download_keywords", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ingest_source",
            "ingest_batch_id",
            "page_url",
            name="uq_raw_web_page_observation_natural",
        ),
    )
    op.create_index("ix_raw_web_page_observation_page_url", "raw_web_page_observation", ["page_url"])


def downgrade() -> None:
    op.drop_index("ix_raw_web_page_observation_page_url", table_name="raw_web_page_observation")
    op.drop_table("raw_web_page_observation")

