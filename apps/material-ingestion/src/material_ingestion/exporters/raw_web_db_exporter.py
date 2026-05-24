from __future__ import annotations

from typing import Any

from sqlalchemy.dialects.postgresql import insert

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import (
    RawWebDownloadedFile,
    RawWebFetchXhrObservation,
    RawWebPageCrawl,
    RawWebPageObservation,
    RawWebPdfCandidate,
)
from material_ingestion.services.web_url_canonicalizer import canonicalize_url


class RawWebDbExporter:
    def __init__(self, ingest_source: str, ingest_locator: str, ingest_batch_id: str):
        self.ingest_source = ingest_source
        self.ingest_locator = ingest_locator
        self.ingest_batch_id = ingest_batch_id
        self._session_factory = create_session_factory()

    def export_pages(self, rows: list[dict[str, object]]) -> int:
        payload = [
            {
                "ingest_source": self.ingest_source,
                "ingest_locator": self.ingest_locator,
                "ingest_batch_id": self.ingest_batch_id,
                "page_url": str(r.get("url", "")),
                "status_code": int(r.get("status_code", 0)),
                "content_type": str(r.get("content_type", "")),
                "crawl_ok": bool(r.get("crawl_ok", False)),
            }
            for r in rows
        ]
        return self._upsert(
            model=RawWebPageCrawl,
            payload=payload,
            conflict_cols=["ingest_source", "ingest_batch_id", "page_url"],
            replace_existing=True,
        )

    def export_candidates(self, rows: list[dict[str, object]]) -> int:
        payload = [
            {
                "ingest_source": self.ingest_source,
                "ingest_locator": self.ingest_locator,
                "ingest_batch_id": self.ingest_batch_id,
                "source_page_url": str(r.get("source_page_url", "")),
                "pdf_url": str(r.get("pdf_url", "")),
                "canonical_pdf_url": str(r.get("canonical_pdf_url", "")) or canonicalize_url(str(r.get("pdf_url", ""))),
                "anchor_text": str(r.get("anchor_text", "")),
                "score": int(r.get("score", 0)),
                "reason": str(r.get("reason", "")),
            }
            for r in rows
        ]
        return self._upsert(
            model=RawWebPdfCandidate,
            payload=payload,
            conflict_cols=["ingest_source", "ingest_batch_id", "canonical_pdf_url"],
            replace_existing=True,
        )

    def export_page_observations(self, rows: list[dict[str, object]]) -> int:
        payload = [
            {
                "ingest_source": self.ingest_source,
                "ingest_locator": self.ingest_locator,
                "ingest_batch_id": self.ingest_batch_id,
                "page_url": str(r.get("page_url", "")),
                "page_title": str(r.get("page_title", "")),
                "text_excerpt": str(r.get("text_excerpt", "")),
                "raw_html": str(r.get("raw_html", "")),
                "raw_html_sha256": str(r.get("raw_html_sha256", "")),
                "raw_html_bytes": int(r.get("raw_html_bytes", 0)),
                "raw_html_truncated": bool(r.get("raw_html_truncated", False)),
                "anchor_count": int(r.get("anchor_count", 0)),
                "input_count": int(r.get("input_count", 0)),
                "button_count": int(r.get("button_count", 0)),
                "form_count": int(r.get("form_count", 0)),
                "has_download_keywords": bool(r.get("has_download_keywords", False)),
                "payload_json": str(r.get("payload_json", "{}")),
            }
            for r in rows
        ]
        return self._upsert(
            model=RawWebPageObservation,
            payload=payload,
            conflict_cols=["ingest_source", "ingest_batch_id", "page_url"],
            replace_existing=True,
        )


    def export_fetch_xhr_observations(self, rows: list[dict[str, object]]) -> int:
        deduped: dict[tuple[str, str], dict[str, object]] = {}
        for r in rows:
            payload_row = {
                "ingest_source": self.ingest_source,
                "ingest_locator": self.ingest_locator,
                "ingest_batch_id": self.ingest_batch_id,
                "source_page_url": str(r.get("source_page_url", "")),
                "response_url": str(r.get("response_url", "")),
                "resource_type": str(r.get("resource_type", "")),
                "status_code": int(r.get("status_code", 0)),
                "content_type": str(r.get("content_type", "")),
                "is_json": bool(r.get("is_json", False)),
                "extracted_urls_json": str(r.get("extracted_urls_json", "[]")),
                "extracted_url_count": int(r.get("extracted_url_count", 0)),
            }
            key = (payload_row["source_page_url"], payload_row["response_url"])
            existing = deduped.get(key)
            if existing is None:
                deduped[key] = payload_row
                continue

            # Prefer richer observation when same page/response appears multiple times.
            existing_quality = (
                int(bool(existing["is_json"])),
                int(existing["extracted_url_count"]),
                int(bool(existing["content_type"])),
            )
            new_quality = (
                int(bool(payload_row["is_json"])),
                int(payload_row["extracted_url_count"]),
                int(bool(payload_row["content_type"])),
            )
            if new_quality > existing_quality:
                deduped[key] = payload_row
        payload = list(deduped.values())
        return self._upsert(
            model=RawWebFetchXhrObservation,
            payload=payload,
            conflict_cols=["ingest_source", "ingest_batch_id", "source_page_url", "response_url"],
            replace_existing=True,
        )

    def export_downloaded_files(self, rows: list[dict[str, object]], *, replace_existing: bool = False) -> int:
        payload = [
            {
                "ingest_source": self.ingest_source,
                "ingest_locator": self.ingest_locator,
                "ingest_batch_id": self.ingest_batch_id,
                "source_url": str(r.get("source_url", "")),
                "canonical_source_url": str(r.get("canonical_source_url", "")) or canonicalize_url(str(r.get("source_url", ""))),
                "stored_path": str(r.get("stored_path", "")),
                "sha256": str(r.get("sha256", "")),
                "size_bytes": int(r.get("size_bytes", 0)),
                "content_type": str(r.get("content_type", "")),
                "status_code": int(r.get("status_code", 0)),
            }
            for r in rows
        ]
        return self._upsert(
            model=RawWebDownloadedFile,
            payload=payload,
            conflict_cols=["ingest_source", "ingest_batch_id", "canonical_source_url"],
            replace_existing=replace_existing,
        )

    def _upsert(
        self,
        *,
        model: Any,
        payload: list[dict[str, object]],
        conflict_cols: list[str],
        replace_existing: bool,
    ) -> int:
        if not payload:
            return 0

        chunk_size = 500
        total = 0
        with self._session_factory() as session:
            if replace_existing:
                session.query(model).filter(
                    model.ingest_source == self.ingest_source,
                    model.ingest_batch_id == self.ingest_batch_id,
                ).delete(synchronize_session=False)

            for i in range(0, len(payload), chunk_size):
                chunk = payload[i : i + chunk_size]
                stmt = insert(model).values(chunk)
                update_cols = {
                    c.name: stmt.excluded[c.name]
                    for c in model.__table__.columns
                    if c.name not in {"id", "created_at", *conflict_cols}
                }
                stmt = stmt.on_conflict_do_update(index_elements=conflict_cols, set_=update_cols)
                session.execute(stmt)
                total += len(chunk)
            session.commit()

        return total
