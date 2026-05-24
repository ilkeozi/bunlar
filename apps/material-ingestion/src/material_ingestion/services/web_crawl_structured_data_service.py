from __future__ import annotations

import json
import re

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebStructuredDataRecord


def extract_structured_data_records(html: str) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    pattern = re.compile(
        r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(?P<payload>.*?)</script>",
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(html or ""):
        payload_raw = (match.group("payload") or "").strip()
        if not payload_raw:
            continue
        try:
            parsed = json.loads(payload_raw)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            records.append({"format": "jsonld", "payload": parsed})
            continue
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    records.append({"format": "jsonld", "payload": item})
    return records


def persist_structured_data_record(*, uri_identity_id: int, format_name: str, payload: dict[str, object]) -> int:
    session_factory = create_session_factory()
    with session_factory() as session:
        row = RawWebStructuredDataRecord(
            uri_identity_id=uri_identity_id,
            format=format_name,
            payload_json=json.dumps(payload, sort_keys=True),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return int(row.id)
