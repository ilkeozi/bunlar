from __future__ import annotations

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebCandidateDocument


def persist_candidate_document(
    *,
    uri_identity_id: int,
    source_uri_identity_id: int,
    mime_type: str,
    classification: str,
    score: int = 0,
    distinct_source_count: int = 0,
    score_reason_json: str = "{}",
    decision_state: str,
    decision_reason_code: str,
) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = (
            session.query(RawWebCandidateDocument)
            .filter(
                RawWebCandidateDocument.uri_identity_id == uri_identity_id,
                RawWebCandidateDocument.source_uri_identity_id == source_uri_identity_id,
            )
            .first()
        )
        if row is None:
            row = RawWebCandidateDocument(
                uri_identity_id=uri_identity_id,
                source_uri_identity_id=source_uri_identity_id,
                mime_type=mime_type,
                classification=classification,
                score=max(0, int(score)),
                distinct_source_count=max(0, int(distinct_source_count)),
                score_reason_json=str(score_reason_json or "{}"),
                decision_state=decision_state,
                decision_reason_code=decision_reason_code,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return int(row.id)

        row.mime_type = mime_type
        row.classification = classification
        row.score = max(0, int(score))
        row.distinct_source_count = max(0, int(distinct_source_count))
        row.score_reason_json = str(score_reason_json or "{}")
        row.decision_state = decision_state
        row.decision_reason_code = decision_reason_code
        session.commit()
        return int(row.id)
