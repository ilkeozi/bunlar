"""add http representation metadata fields

Revision ID: 20260525_04
Revises: 20260525_03
Create Date: 2026-05-25 21:05:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260525_04"
down_revision = "20260525_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("raw_web_http_representation", sa.Column("content_length", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("raw_web_http_representation", sa.Column("content_language", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("raw_web_http_representation", sa.Column("content_encoding", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("raw_web_http_representation", sa.Column("content_disposition", sa.String(length=512), nullable=False, server_default=""))
    op.add_column("raw_web_http_representation", sa.Column("location", sa.Text(), nullable=False, server_default=""))
    op.add_column("raw_web_http_representation", sa.Column("content_location", sa.Text(), nullable=False, server_default=""))
    op.add_column("raw_web_http_representation", sa.Column("link", sa.Text(), nullable=False, server_default=""))
    op.add_column("raw_web_http_representation", sa.Column("vary", sa.String(length=512), nullable=False, server_default=""))
    op.add_column("raw_web_http_representation", sa.Column("allow", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("raw_web_http_representation", sa.Column("accept_ranges", sa.String(length=128), nullable=False, server_default=""))
    op.add_column("raw_web_http_representation", sa.Column("server", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("raw_web_http_representation", sa.Column("x_robots_tag", sa.String(length=512), nullable=False, server_default=""))
    op.add_column("raw_web_http_representation", sa.Column("retry_after", sa.String(length=255), nullable=False, server_default=""))

    op.alter_column("raw_web_http_representation", "content_length", server_default=None)
    op.alter_column("raw_web_http_representation", "content_language", server_default=None)
    op.alter_column("raw_web_http_representation", "content_encoding", server_default=None)
    op.alter_column("raw_web_http_representation", "content_disposition", server_default=None)
    op.alter_column("raw_web_http_representation", "location", server_default=None)
    op.alter_column("raw_web_http_representation", "content_location", server_default=None)
    op.alter_column("raw_web_http_representation", "link", server_default=None)
    op.alter_column("raw_web_http_representation", "vary", server_default=None)
    op.alter_column("raw_web_http_representation", "allow", server_default=None)
    op.alter_column("raw_web_http_representation", "accept_ranges", server_default=None)
    op.alter_column("raw_web_http_representation", "server", server_default=None)
    op.alter_column("raw_web_http_representation", "x_robots_tag", server_default=None)
    op.alter_column("raw_web_http_representation", "retry_after", server_default=None)


def downgrade() -> None:
    op.drop_column("raw_web_http_representation", "retry_after")
    op.drop_column("raw_web_http_representation", "x_robots_tag")
    op.drop_column("raw_web_http_representation", "server")
    op.drop_column("raw_web_http_representation", "accept_ranges")
    op.drop_column("raw_web_http_representation", "allow")
    op.drop_column("raw_web_http_representation", "vary")
    op.drop_column("raw_web_http_representation", "link")
    op.drop_column("raw_web_http_representation", "content_location")
    op.drop_column("raw_web_http_representation", "location")
    op.drop_column("raw_web_http_representation", "content_disposition")
    op.drop_column("raw_web_http_representation", "content_encoding")
    op.drop_column("raw_web_http_representation", "content_language")
    op.drop_column("raw_web_http_representation", "content_length")
