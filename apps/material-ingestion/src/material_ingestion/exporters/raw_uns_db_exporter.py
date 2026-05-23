from __future__ import annotations

from typing import Any

from sqlalchemy.dialects.postgresql import insert

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import (
    RawUnsAwsCrossReference,
    RawUnsBaseElementsIndex,
    RawUnsCommonDocumentIndex,
    RawUnsSeriesEntry,
    RawUnsSeriesPageIndex,
)


class RawUnsDbExporter:
    def __init__(self, ingest_source: str, ingest_locator: str, ingest_batch_id: str):
        self.ingest_source = ingest_source
        self.ingest_locator = ingest_locator
        self.ingest_batch_id = ingest_batch_id
        self._session_factory = create_session_factory()

    def export_aws_cross_reference(self, rows: list[dict[str, Any]]) -> int:
        payload = [
            {
                "ingest_source": self.ingest_source,
                "ingest_locator": self.ingest_locator,
                "ingest_batch_id": self.ingest_batch_id,
                "aws_spec": str(r.get("aws_spec", "")),
                "aws_designation": str(r.get("aws_designation", "")),
                "aws_designation_raw": str(r.get("aws_designation_raw", r.get("aws_designation", ""))),
                "uns": str(r.get("uns", "")),
                "page": int(r.get("page", 0)),
                "note": (str(r.get("note")) if r.get("note") not in (None, "") else None),
                "raw_line": str(r.get("raw_line", "")),
                "extraction_method": str(r.get("extraction_method", "")),
                "ocr_used": bool(r.get("ocr_used", False)),
            }
            for r in rows
        ]
        return self._upsert(
            RawUnsAwsCrossReference,
            payload,
            ["ingest_source", "ingest_batch_id", "aws_spec", "aws_designation", "uns"],
        )

    def export_base_elements_index(self, rows: list[dict[str, Any]]) -> int:
        payload = [
            {
                "ingest_source": self.ingest_source,
                "ingest_locator": self.ingest_locator,
                "ingest_batch_id": self.ingest_batch_id,
                "element_name": str(r.get("element_name", "")),
                "symbol": str(r.get("symbol", "")),
                "uns_range": str(r.get("uns_range", "")),
                "index_label": str(r.get("index_label", "")),
                "index_pdf_page": int(r.get("index_pdf_page", 0)),
                "row_order": int(r.get("row_order", 0)),
                "extraction_method": str(r.get("extraction_method", "")),
                "ocr_used": bool(r.get("ocr_used", False)),
            }
            for r in rows
        ]
        return self._upsert(
            RawUnsBaseElementsIndex,
            payload,
            ["ingest_source", "ingest_batch_id", "row_order"],
        )

    def export_common_documents_index(self, rows: list[dict[str, Any]]) -> int:
        payload = [
            {
                "ingest_source": self.ingest_source,
                "ingest_locator": self.ingest_locator,
                "ingest_batch_id": self.ingest_batch_id,
                "toc_page": int(r.get("toc_page", 0)),
                "document_code_raw": str(r.get("document_code", "")),
                "document_code": str(r.get("document_code", "")).upper(),
                "description": str(r.get("description", "")),
                "target_label": str(r.get("target_label", "")),
                "target_page": int(r.get("target_page", 0)),
                "page_resolution": str(r.get("page_resolution", "")),
                "extraction_method": str(r.get("extraction_method", "")),
                "ocr_used": bool(r.get("ocr_used", False)),
                "raw_line": str(r.get("raw_line", "")),
            }
            for r in rows
        ]
        return self._upsert(
            RawUnsCommonDocumentIndex,
            payload,
            ["ingest_source", "ingest_batch_id", "toc_page", "document_code", "target_page"],
        )

    def export_series_page_index(self, rows: list[dict[str, Any]]) -> int:
        payload = [
            {
                "ingest_source": self.ingest_source,
                "ingest_locator": self.ingest_locator,
                "ingest_batch_id": self.ingest_batch_id,
                "series": str(r.get("series", "")),
                "series_token": str(r.get("series_token", "")),
                "description": str(r.get("description", "")),
                "target_label": str(r.get("target_label", "")),
                "target_page": int(r.get("target_page", 0)),
                "target_pdf_page": (int(r["target_pdf_page"]) if r.get("target_pdf_page") is not None else None),
                "page_resolution": str(r.get("page_resolution", "")),
                "section_start_pdf_page": (int(r["section_start_pdf_page"]) if r.get("section_start_pdf_page") is not None else None),
                "section_end_pdf_page": (int(r["section_end_pdf_page"]) if r.get("section_end_pdf_page") is not None else None),
                "toc_page": int(r.get("toc_page", 0)),
                "extraction_method": str(r.get("extraction_method", "")),
                "ocr_used": bool(r.get("ocr_used", False)),
            }
            for r in rows
        ]
        return self._upsert(
            RawUnsSeriesPageIndex,
            payload,
            ["ingest_source", "ingest_batch_id", "series_token", "target_page"],
        )

    def export_series_entries(self, rows: list[dict[str, Any]]) -> int:
        payload = [
            {
                "ingest_source": self.ingest_source,
                "ingest_locator": self.ingest_locator,
                "ingest_batch_id": self.ingest_batch_id,
                "series_token": str(r.get("series_token", "")),
                "series_description": str(r.get("series_description", "")),
                "uns_code": str(r.get("uns_code", "")),
                "description": str(r.get("description", "")),
                "chemical_composition_structured": list(r.get("chemical_composition_structured", [])),
                "chemical_composition_symbol_check": dict(r.get("chemical_composition_symbol_check", {})),
                "cross_reference_specifications_structured": list(r.get("cross_reference_specifications_structured", [])),
                "cross_reference_specifications_check": dict(r.get("cross_reference_specifications_check", {})),
                "entry_pdf_page_start": int(r.get("entry_pdf_page_start", 0)),
                "entry_pdf_page_end": int(r.get("entry_pdf_page_end", 0)),
                "is_replaced": bool(r.get("is_replaced", False)),
                "inactive_boxed": bool(r.get("inactive_boxed", False)),
                "extraction_method": str(r.get("extraction_method", "")),
            }
            for r in rows
        ]
        return self._upsert(
            RawUnsSeriesEntry,
            payload,
            ["ingest_source", "ingest_batch_id", "series_token", "uns_code"],
        )

    def _upsert(self, model, payload: list[dict[str, Any]], conflict_cols: list[str]) -> int:
        if not payload:
            return 0
        chunk_size = 500
        total = 0
        with self._session_factory() as session:
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
