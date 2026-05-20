from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from material_ingestion.sources.base import RawRecord
from material_ingestion.sources.uns.pdf_page_source import UnsPdfPageSource

AWS_ROW_PATTERN = re.compile(
    r"^\s*(A[0-9.]+)\s*\(([^)]*?)\)\s*\.{2,}\s*([A-Z]\d{5})(?:\s+([A-Za-z0-9]+))?\s*$"
)


class UnsAwsCrossReferenceExtractor:
    """Extract AWS-to-UNS cross-reference rows from the UNS PDF."""

    def extract(
        self, pdf_path: Path, start_page: int = 3, end_page: int = 7
    ) -> list[dict[str, str | int]]:
        source = UnsPdfPageSource(pdf_path=pdf_path, start_page=start_page, end_page=end_page)
        return self.extract_rows(source.fetch())

    def extract_rows(self, raw_records: Iterable[RawRecord]) -> list[RawRecord]:
        rows: list[RawRecord] = []
        seen_keys: set[tuple[str, str, str]] = set()
        for raw in raw_records:
            text = str(raw.get("text", ""))
            pdf_page = int(raw.get("pdf_page", 0))
            rows.extend(
                self.extract_from_text(
                    text,
                    page_number=pdf_page,
                    seen_keys=seen_keys,
                    extraction_method=str(raw.get("page_extraction_method", "text_pypdf")),
                    ocr_used=bool(raw.get("ocr_used", False)),
                    fallback_reason=str(raw.get("fallback_reason", "")),
                )
            )
        return rows

    def extract_from_text(
        self,
        text: str,
        page_number: int,
        seen_keys: set[tuple[str, str, str]] | None = None,
        extraction_method: str = "text_pypdf",
        ocr_used: bool = False,
        fallback_reason: str = "",
    ) -> list[dict[str, str | int]]:
        rows: list[dict[str, str | int]] = []
        seen = seen_keys if seen_keys is not None else set()

        for raw_line in text.splitlines():
            normalized = " ".join(raw_line.split())
            if not normalized:
                continue

            match = AWS_ROW_PATTERN.match(normalized)
            if not match:
                continue

            aws_spec = self._normalize_aws_spec(match.group(1))
            aws_designation = match.group(2).strip()
            uns = match.group(3).strip()
            note = (match.group(4) or "").strip()

            key = (aws_spec, aws_designation, uns)
            if key in seen:
                continue
            seen.add(key)

            row: dict[str, str | int] = {
                "aws_spec": aws_spec,
                "aws_designation": aws_designation,
                "uns": uns,
                "page": page_number,
                "raw_line": normalized,
                "extraction_method": extraction_method,
                "ocr_used": ocr_used,
            }
            if fallback_reason:
                row["fallback_reason"] = fallback_reason
            if note:
                row["note"] = note

            rows.append(row)

        return rows

    @staticmethod
    def _normalize_aws_spec(spec: str) -> str:
        # OCR sometimes drops a period: A526 -> A5.26, A513 -> A5.13
        if re.fullmatch(r"A\d{3}", spec):
            return f"A{spec[1]}.{spec[2:]}"
        return spec
