from __future__ import annotations

from datetime import timedelta
from datetime import UTC, datetime

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebCrawlDecision, RawWebHttpRepresentation, RawWebIngestionEvent


def apply_representation_retention(*, now: datetime | None = None) -> int:
    current = now or datetime.now(UTC)
    session_factory = create_session_factory()
    with session_factory() as session:
        rows = (
            session.query(RawWebHttpRepresentation)
            .filter(
                RawWebHttpRepresentation.expires_full_at <= current,
                RawWebHttpRepresentation.storage_ref != "",
            )
            .all()
        )
        count = 0
        for row in rows:
            row.storage_ref = ""
            row.metadata_only_since = current
            count += 1
        if count:
            session.commit()
        return count


def apply_decision_event_retention(
    *,
    decision_retention_days: int,
    event_retention_days: int,
    now: datetime | None = None,
) -> tuple[int, int]:
    current = now or datetime.now(UTC)
    decision_cutoff = current - timedelta(days=max(1, int(decision_retention_days)))
    event_cutoff = current - timedelta(days=max(1, int(event_retention_days)))
    session_factory = create_session_factory()
    with session_factory() as session:
        deleted_decisions = (
            session.query(RawWebCrawlDecision)
            .filter(RawWebCrawlDecision.recorded_at < decision_cutoff)
            .delete(synchronize_session=False)
        )
        deleted_events = (
            session.query(RawWebIngestionEvent)
            .filter(
                RawWebIngestionEvent.created_at < event_cutoff,
                RawWebIngestionEvent.status.in_(["done", "failed"]),
            )
            .delete(synchronize_session=False)
        )
        if deleted_decisions or deleted_events:
            session.commit()
        return int(deleted_decisions or 0), int(deleted_events or 0)
