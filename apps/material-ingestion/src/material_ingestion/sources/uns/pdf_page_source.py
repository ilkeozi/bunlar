from __future__ import annotations

from pathlib import Path
from typing import Iterable

from material_ingestion.sources.base import RawRecord, SourceAdapter


class UnsPdfPageSource(SourceAdapter):
    source_name = "uns-pdf"

    def __init__(
        self,
        pdf_path: Path,
        start_page: int | None = None,
        end_page: int | None = None,
        pages: list[int] | None = None,
    ):
        self.pdf_path = pdf_path
        self.start_page = start_page
        self.end_page = end_page
        self.pages = pages

    def fetch(self) -> Iterable[RawRecord]:
        try:
            from pypdf import PdfReader
        except ModuleNotFoundError as exc:
            raise RuntimeError("PDF source requires 'pypdf'. Install dependencies first.") from exc

        reader = PdfReader(str(self.pdf_path))
        page_numbers = self._select_page_numbers(total_pages=len(reader.pages))
        rows: list[RawRecord] = []

        for pdf_page in page_numbers:
            text = reader.pages[pdf_page - 1].extract_text() or ""
            rows.append(
                {
                    "pdf_path": str(self.pdf_path),
                    "pdf_page": pdf_page,
                    "text": text,
                    "page_extraction_method": "text_pypdf",
                    "ocr_used": False,
                }
            )
        return rows

    def _select_page_numbers(self, total_pages: int) -> list[int]:
        if self.pages:
            selected = sorted(set(self.pages))
        else:
            start = self.start_page or 1
            end = self.end_page or total_pages
            if start < 1 or end < start:
                raise ValueError("Invalid page range for UNS PDF source.")
            selected = list(range(start, min(end, total_pages) + 1))

        if selected and (selected[0] < 1 or selected[-1] > total_pages):
            raise ValueError("Requested page is out of bounds for the provided PDF.")
        return selected
