"""add raw_web_page_text table

Revision ID: 20260527_19
Revises: 20260527_18
Create Date: 2026-05-28
"""

from __future__ import annotations

from alembic import op

revision = "20260527_19"
down_revision = "20260527_18"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_web_page_text (
            id               SERIAL PRIMARY KEY,
            fetch_attempt_id INTEGER NOT NULL REFERENCES raw_web_http_fetch_attempt(id) ON DELETE CASCADE,
            title            TEXT    NOT NULL DEFAULT '',
            meta_description TEXT    NOT NULL DEFAULT '',
            h1               TEXT    NOT NULL DEFAULT '',
            lang             VARCHAR(32) NOT NULL DEFAULT '',
            body_text        TEXT    NOT NULL DEFAULT '',
            raw_html_length  INTEGER NOT NULL DEFAULT 0,
            text_length      INTEGER NOT NULL DEFAULT 0,
            text_ratio       REAL    NOT NULL DEFAULT 0.0,
            render_needed    BOOLEAN NOT NULL DEFAULT FALSE,
            extracted_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_raw_web_page_text_fetch_attempt UNIQUE (fetch_attempt_id)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_raw_web_page_text_render_needed
            ON raw_web_page_text (render_needed)
            WHERE render_needed = TRUE
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS raw_web_page_text")
