from __future__ import annotations

import re
from pathlib import Path

from material_ingestion.normalizers.base import Normalizer
from material_ingestion.sources.base import RawRecord


class UnsSeriesBoundaryNormalizer(Normalizer[list[RawRecord]]):
    """Infer series section start/end pdf pages from section heading pages."""

    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path

    def normalize(self, rows: list[RawRecord]) -> list[RawRecord]:
        boundaries = self._build_boundaries()
        normalized: list[RawRecord] = []

        for row in rows:
            new_row = dict(row)
            token = str(new_row.get("series_token", "")).strip()
            start_end = boundaries.get(token)
            if start_end:
                start_page, end_page = start_end
                new_row["section_start_pdf_page"] = start_page
                new_row["section_end_pdf_page"] = end_page

                if new_row.get("target_pdf_page") in ("", None):
                    new_row["target_pdf_page"] = start_page
                    new_row["page_resolution"] = "section-heading-start"

            normalized.append(new_row)

        return normalized

    def _build_boundaries(self) -> dict[str, tuple[int, int]]:
        try:
            from pypdf import PdfReader
        except ModuleNotFoundError as exc:
            raise RuntimeError("Series boundary normalization requires 'pypdf'.") from exc

        reader = PdfReader(str(self.pdf_path))
        starts: list[tuple[str, int]] = []

        for idx, page in enumerate(reader.pages, start=1):
            text = " ".join((page.extract_text() or "").split())
            match = re.search(r"([A-Z])\s*x\s*x\s*x\s*x\s*x\s*Number Series", text, flags=re.IGNORECASE)
            if not match:
                continue
            token = f"{match.group(1).upper()}xxxxx"
            starts.append((token, idx))

        starts = self._dedupe_token_starts(starts)
        boundaries: dict[str, tuple[int, int]] = {}
        for i, (token, start_page) in enumerate(starts):
            end_page = starts[i + 1][1] - 1 if i + 1 < len(starts) else len(reader.pages)
            boundaries[token] = (start_page, end_page)

        return boundaries

    @staticmethod
    def _dedupe_token_starts(starts: list[tuple[str, int]]) -> list[tuple[str, int]]:
        result: list[tuple[str, int]] = []
        seen: set[str] = set()
        for token, page in starts:
            if token in seen:
                continue
            seen.add(token)
            result.append((token, page))
        return sorted(result, key=lambda item: item[1])
