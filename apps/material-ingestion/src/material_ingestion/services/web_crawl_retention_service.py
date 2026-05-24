from __future__ import annotations

from datetime import UTC, datetime

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebHttpRepresentation


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
