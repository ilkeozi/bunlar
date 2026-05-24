from __future__ import annotations

import json

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebCrawlDecision


def record_decision(
    *,
    crawl_run_id: int,
    decision_type: str,
    reason_code: str,
    uri_identity_id: int | None = None,
    detail: dict[str, object] | None = None,
) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = RawWebCrawlDecision(
            crawl_run_id=crawl_run_id,
            uri_identity_id=uri_identity_id,
            decision_type=decision_type,
            reason_code=reason_code,
            detail_json=json.dumps(detail or {}, sort_keys=True),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return int(row.id)
