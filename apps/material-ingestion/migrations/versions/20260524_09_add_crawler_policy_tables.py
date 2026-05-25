"""add crawler policy tables

Revision ID: 20260524_09
Revises: 20260524_08
Create Date: 2026-05-24 22:35:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260524_09"
down_revision = "20260524_08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "raw_web_robots_policy",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("host_id", sa.Integer(), nullable=False),
        sa.Column("fetch_status", sa.String(length=32), nullable=False),
        sa.Column("policy_blob", sa.Text(), nullable=False, server_default=""),
        sa.Column("evaluation_summary_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["host_id"], ["raw_web_crawl_host.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_raw_web_robots_policy_host_id", "raw_web_robots_policy", ["host_id"])

    op.create_table(
        "raw_web_sitemap_source",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("host_id", sa.Integer(), nullable=False),
        sa.Column("sitemap_url", sa.Text(), nullable=False),
        sa.Column("discovered_via", sa.String(length=32), nullable=False, server_default="manual"),
        sa.Column("last_fetch_status", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["host_id"], ["raw_web_crawl_host.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("host_id", "sitemap_url", name="uq_raw_web_sitemap_source_unique"),
    )
    op.create_index("ix_raw_web_sitemap_source_host", "raw_web_sitemap_source", ["host_id"])

    op.create_table(
        "raw_web_sitemap_entry",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sitemap_source_id", sa.Integer(), nullable=False),
        sa.Column("uri_identity_id", sa.Integer(), nullable=False),
        sa.Column("lastmod_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["sitemap_source_id"], ["raw_web_sitemap_source.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uri_identity_id"], ["raw_web_uri_identity.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sitemap_source_id", "uri_identity_id", name="uq_raw_web_sitemap_entry_unique"),
    )
    op.create_index("ix_raw_web_sitemap_entry_source", "raw_web_sitemap_entry", ["sitemap_source_id"])


def downgrade() -> None:
    op.drop_index("ix_raw_web_sitemap_entry_source", table_name="raw_web_sitemap_entry")
    op.drop_table("raw_web_sitemap_entry")
    op.drop_index("ix_raw_web_sitemap_source_host", table_name="raw_web_sitemap_source")
    op.drop_table("raw_web_sitemap_source")
    op.drop_index("ix_raw_web_robots_policy_host_id", table_name="raw_web_robots_policy")
    op.drop_table("raw_web_robots_policy")
