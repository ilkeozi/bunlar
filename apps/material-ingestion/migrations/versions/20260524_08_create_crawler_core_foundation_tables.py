"""create crawler core foundation tables

Revision ID: 20260524_08
Revises: 20260524_07
Create Date: 2026-05-24 21:40:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260524_08"
down_revision = "20260524_07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "raw_web_crawl_host",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("discovery_source", sa.Text(), nullable=False, server_default=""),
        sa.Column("allowlist_match", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("auto_crawl_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hostname", name="uq_raw_web_crawl_host_hostname"),
    )

    op.create_table(
        "raw_web_uri_identity",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("canonical_uri", sa.Text(), nullable=False),
        sa.Column("normalized_hash", sa.String(length=64), nullable=False),
        sa.Column("host_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["host_id"], ["raw_web_crawl_host.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("canonical_uri", name="uq_raw_web_uri_identity_uri"),
        sa.UniqueConstraint("normalized_hash", name="uq_raw_web_uri_identity_hash"),
    )
    op.create_index("ix_raw_web_uri_identity_host_id", "raw_web_uri_identity", ["host_id"])

    op.create_table(
        "raw_web_uri_alias",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uri_identity_id", sa.Integer(), nullable=False),
        sa.Column("observed_uri", sa.Text(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["uri_identity_id"], ["raw_web_uri_identity.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uri_identity_id", "observed_uri", name="uq_raw_web_uri_alias_unique"),
    )
    op.create_index("ix_raw_web_uri_alias_identity", "raw_web_uri_alias", ["uri_identity_id"])

    op.create_table(
        "raw_web_crawl_run",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_key", sa.String(length=128), nullable=False),
        sa.Column("initiator", sa.String(length=128), nullable=False, server_default="system"),
        sa.Column("force_refresh", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_key", name="uq_raw_web_crawl_run_key"),
    )

    op.create_table(
        "raw_web_frontier_item",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uri_identity_id", sa.Integer(), nullable=False),
        sa.Column("crawl_run_id", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=24), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("state_reason_code", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["uri_identity_id"], ["raw_web_uri_identity.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["crawl_run_id"], ["raw_web_crawl_run.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_raw_web_frontier_item_uri_identity_id", "raw_web_frontier_item", ["uri_identity_id"])
    op.create_index("ix_raw_web_frontier_item_state", "raw_web_frontier_item", ["state"])

    op.create_table(
        "raw_web_crawl_decision",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("crawl_run_id", sa.Integer(), nullable=False),
        sa.Column("uri_identity_id", sa.Integer(), nullable=True),
        sa.Column("decision_type", sa.String(length=32), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=False),
        sa.Column("detail_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["crawl_run_id"], ["raw_web_crawl_run.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uri_identity_id"], ["raw_web_uri_identity.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_raw_web_crawl_decision_run", "raw_web_crawl_decision", ["crawl_run_id"])


def downgrade() -> None:
    op.drop_index("ix_raw_web_crawl_decision_run", table_name="raw_web_crawl_decision")
    op.drop_table("raw_web_crawl_decision")
    op.drop_index("ix_raw_web_frontier_item_state", table_name="raw_web_frontier_item")
    op.drop_index("ix_raw_web_frontier_item_uri_identity_id", table_name="raw_web_frontier_item")
    op.drop_table("raw_web_frontier_item")
    op.drop_table("raw_web_crawl_run")
    op.drop_index("ix_raw_web_uri_alias_identity", table_name="raw_web_uri_alias")
    op.drop_table("raw_web_uri_alias")
    op.drop_index("ix_raw_web_uri_identity_host_id", table_name="raw_web_uri_identity")
    op.drop_table("raw_web_uri_identity")
    op.drop_table("raw_web_crawl_host")
