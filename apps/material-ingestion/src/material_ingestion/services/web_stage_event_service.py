from __future__ import annotations

import json

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebCandidateEvent, RawWebDiscoveryEvent, RawWebDownloadEvent


def append_discovery_events(rows: list[dict[str, object]]) -> int:
    if not rows:
        return 0
    session_factory = create_session_factory()
    with session_factory() as session:
        session.add_all(
            [
                RawWebDiscoveryEvent(
                    orchestration_id=str(r.get("orchestration_id", "")),
                    ingest_batch_id=str(r.get("ingest_batch_id", "")),
                    event_type=str(r.get("event_type", "")),
                    page_url=str(r.get("page_url", "")),
                    payload_json=json.dumps(r.get("payload", {}), sort_keys=True),
                )
                for r in rows
            ]
        )
        session.commit()
    return len(rows)


def append_candidate_events(rows: list[dict[str, object]]) -> int:
    if not rows:
        return 0
    session_factory = create_session_factory()
    with session_factory() as session:
        session.add_all(
            [
                RawWebCandidateEvent(
                    orchestration_id=str(r.get("orchestration_id", "")),
                    ingest_batch_id=str(r.get("ingest_batch_id", "")),
                    event_type=str(r.get("event_type", "")),
                    candidate_id=int(r.get("candidate_id", 0) or 0),
                    source_page_url=str(r.get("source_page_url", "")),
                    pdf_url=str(r.get("pdf_url", "")),
                    payload_json=json.dumps(r.get("payload", {}), sort_keys=True),
                )
                for r in rows
            ]
        )
        session.commit()
    return len(rows)


def append_download_events(rows: list[dict[str, object]]) -> int:
    if not rows:
        return 0
    session_factory = create_session_factory()
    with session_factory() as session:
        session.add_all(
            [
                RawWebDownloadEvent(
                    orchestration_id=str(r.get("orchestration_id", "")),
                    ingest_batch_id=str(r.get("ingest_batch_id", "")),
                    event_type=str(r.get("event_type", "")),
                    source_url=str(r.get("source_url", "")),
                    status_code=int(r.get("status_code", 0) or 0),
                    payload_json=json.dumps(r.get("payload", {}), sort_keys=True),
                )
                for r in rows
            ]
        )
        session.commit()
    return len(rows)
