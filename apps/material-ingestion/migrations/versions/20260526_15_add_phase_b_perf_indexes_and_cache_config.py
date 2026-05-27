"""add phase-b perf indexes and cache config

Revision ID: 20260526_15
Revises: 20260526_14
Create Date: 2026-05-26
"""

from __future__ import annotations

from alembic import op


revision = "20260526_15"
down_revision = "20260526_14"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_raw_web_extracted_link_target_uri_identity_id
          ON raw_web_extracted_link (target_uri_identity_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_raw_web_extracted_link_source_target
          ON raw_web_extracted_link (source_uri_identity_id, target_uri_identity_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_raw_web_candidate_document_decision_state
          ON raw_web_candidate_document (decision_state)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_raw_web_frontier_item_state_reason_sched_id
          ON raw_web_frontier_item (state, state_reason_code, scheduled_at, id)
        """
    )
    op.execute(
        """
        INSERT INTO raw_web_runtime_config (config_key, config_value, enabled, note)
        VALUES
          ('core_identity_cache_redis_enabled', '1', true, 'Enable Redis-backed URI identity cache in Phase-B GET'),
          ('core_identity_cache_redis_ttl_seconds', '3600', true, 'TTL for Redis URI identity cache entries in seconds'),
          ('core_get_max_links_per_page', '0', true, 'Per-page extracted-link cap for Phase-B GET; 0 means uncapped')
        ON CONFLICT (config_key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_raw_web_frontier_item_state_reason_sched_id")
    op.execute("DROP INDEX IF EXISTS ix_raw_web_candidate_document_decision_state")
    op.execute("DROP INDEX IF EXISTS ix_raw_web_extracted_link_source_target")
    op.execute("DROP INDEX IF EXISTS ix_raw_web_extracted_link_target_uri_identity_id")
    op.execute(
        """
        DELETE FROM raw_web_runtime_config
        WHERE config_key IN (
          'core_identity_cache_redis_enabled',
          'core_identity_cache_redis_ttl_seconds',
          'core_get_max_links_per_page'
        )
        """
    )
