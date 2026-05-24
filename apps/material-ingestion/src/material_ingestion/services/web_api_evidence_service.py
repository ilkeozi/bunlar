from __future__ import annotations

import hashlib
import json
from urllib.parse import parse_qs, urlparse

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebApiDocumentCandidate, RawWebApiEndpoint, RawWebApiPageFetch
from material_ingestion.sources.web.web_pdf_discovery import FetchXhrObservation


def _endpoint_url(url: str) -> str:
    p = urlparse(url)
    if not p.scheme or not p.netloc:
        return ""
    return f"{p.scheme}://{p.netloc}{p.path}"


def _document_confidence(url: str) -> tuple[int, str]:
    lower = url.lower()
    if lower.endswith(".pdf"):
        return 9, "url_pdf_suffix"
    if any(token in lower for token in ("download", "datasheet", "sds", "tds", "spec", "pdf")):
        return 6, "url_document_hint"
    return 3, "api_extracted_url"


def persist_api_evidence(
    *,
    orchestration_id: str,
    ingest_batch_id: str,
    observations: list[FetchXhrObservation],
) -> dict[str, int]:
    endpoint_rows: dict[tuple[str, str], RawWebApiEndpoint] = {}
    page_fetch_rows: list[RawWebApiPageFetch] = []
    document_rows: dict[tuple[str, str], RawWebApiDocumentCandidate] = {}

    for obs in observations:
        parsed = urlparse(obs.response_url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        endpoint = _endpoint_url(obs.response_url)

        key = (obs.source_page_url, endpoint)
        if key not in endpoint_rows and endpoint:
            endpoint_rows[key] = RawWebApiEndpoint(
                orchestration_id=orchestration_id,
                ingest_batch_id=ingest_batch_id,
                source_page_url=obs.source_page_url,
                endpoint_url=endpoint,
                sample_request_url=obs.response_url,
                payload_json=json.dumps(
                    {
                        "resource_type": obs.resource_type,
                        "status_code": obs.status_code,
                        "content_type": obs.content_type,
                    },
                    sort_keys=True,
                ),
            )

        page_index = -1
        page_limit = 0
        try:
            if "page" in params and params["page"]:
                page_index = int(params["page"][0])
        except Exception:
            page_index = -1
        try:
            if "limit" in params and params["limit"]:
                page_limit = int(params["limit"][0])
        except Exception:
            page_limit = 0

        extracted_docs = list(getattr(obs, "extracted_documents", []) or [])
        extracted_urls = sorted(set([str(d.get("url")) for d in extracted_docs if d.get("url")] + list(obs.extracted_urls)))
        fingerprint_source = json.dumps(
            {
                "response_url": obs.response_url,
                "status_code": obs.status_code,
                "content_type": obs.content_type,
                "urls": extracted_urls,
            },
            sort_keys=True,
        )
        fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()

        page_fetch_rows.append(
            RawWebApiPageFetch(
                orchestration_id=orchestration_id,
                ingest_batch_id=ingest_batch_id,
                source_page_url=obs.source_page_url,
                request_url=obs.response_url,
                endpoint_url=endpoint,
                page_index=page_index,
                page_limit=page_limit,
                status_code=obs.status_code,
                content_type=obs.content_type,
                response_fingerprint_sha256=fingerprint,
                extracted_url_count=len(extracted_urls),
                request_params_json=json.dumps(params, sort_keys=True),
                payload_json=json.dumps(
                    {
                        "resource_type": obs.resource_type,
                        "is_json": obs.is_json,
                        "extracted_urls": extracted_urls,
                        "extracted_documents": extracted_docs,
                    },
                    sort_keys=True,
                ),
            )
        )

        if not extracted_docs:
            extracted_docs = [{"url": u} for u in extracted_urls]
        for doc in extracted_docs:
            url = str(doc.get("url", "")).strip()
            if not url:
                continue
            conf_score = int(doc.get("score", 0) or 0)
            conf_reason = str(doc.get("reason", "") or "")
            if conf_score <= 0 or not conf_reason:
                conf_score, conf_reason = _document_confidence(url)
            dkey = (obs.response_url, url)
            existing = document_rows.get(dkey)
            row = RawWebApiDocumentCandidate(
                orchestration_id=orchestration_id,
                ingest_batch_id=ingest_batch_id,
                source_page_url=obs.source_page_url,
                response_url=obs.response_url,
                document_url=url,
                confidence_score=conf_score,
                confidence_reason=conf_reason,
                payload_json=json.dumps(
                    {
                        "resource_type": obs.resource_type,
                        "status_code": obs.status_code,
                        "content_type": obs.content_type,
                        "document_metadata": doc,
                    },
                    sort_keys=True,
                ),
            )
            if existing is None or conf_score > existing.confidence_score:
                document_rows[dkey] = row

    session_factory = create_session_factory()
    with session_factory() as session:
        if endpoint_rows:
            session.add_all(list(endpoint_rows.values()))
        if page_fetch_rows:
            session.add_all(page_fetch_rows)
        if document_rows:
            session.add_all(list(document_rows.values()))
        session.commit()

    return {
        "api_endpoints": len(endpoint_rows),
        "api_page_fetches": len(page_fetch_rows),
        "api_document_candidates": len(document_rows),
    }
