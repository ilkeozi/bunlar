from __future__ import annotations

import json

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebCrawlDecision


def _should_persist_decision(*, decision_type: str, reason_code: str) -> bool:
    normalized_type = (decision_type or "").strip().lower()
    normalized_reason = (reason_code or "").strip().lower()
    if normalized_reason.startswith("redirect_"):
        return True
    return normalized_type in {"skip", "defer", "reject", "error"}


def record_decision(
    *,
    crawl_run_id: int,
    decision_type: str,
    reason_code: str,
    uri_identity_id: int | None = None,
    detail: dict[str, object] | None = None,
) -> int:
    if not _should_persist_decision(decision_type=decision_type, reason_code=reason_code):
        return 0
    session_factory = create_session_factory()
    with session_factory() as session:
        detail_json = json.dumps(detail or {}, sort_keys=True)
        existing = (
            session.query(RawWebCrawlDecision)
            .filter(
                RawWebCrawlDecision.crawl_run_id == crawl_run_id,
                RawWebCrawlDecision.uri_identity_id == uri_identity_id,
                RawWebCrawlDecision.decision_type == decision_type,
                RawWebCrawlDecision.reason_code == reason_code,
            )
            .order_by(RawWebCrawlDecision.id.asc())
            .first()
        )
        if existing is not None:
            if (existing.detail_json or "") != detail_json:
                existing.detail_json = detail_json
                session.commit()
            return int(existing.id)

        row = RawWebCrawlDecision(
            crawl_run_id=crawl_run_id,
            uri_identity_id=uri_identity_id,
            decision_type=decision_type,
            reason_code=reason_code,
            detail_json=detail_json,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return int(row.id)
