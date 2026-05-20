from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from typing import Iterable

from material_ingestion.sources.base import RawRecord, SourceAdapter


class UnsSeriesSectionPageSource(SourceAdapter):
    source_name = "uns-series-pages"

    def __init__(self, pdf_path: Path, series_index_path: Path):
        self.pdf_path = pdf_path
        self.series_index_path = series_index_path

    def fetch(self) -> Iterable[RawRecord]:
        try:
            from pypdf import PdfReader
        except ModuleNotFoundError as exc:
            raise RuntimeError("Series section page source requires 'pypdf'.") from exc

        index_rows = json.loads(self.series_index_path.read_text(encoding="utf-8"))
        reader = PdfReader(str(self.pdf_path))
        total_pages = len(reader.pages)

        sections: list[tuple[str, str, int, int]] = []
        page_numbers: set[int] = set()
        for idx_row in index_rows:
            token = str(idx_row.get("series_token", "")).strip()
            desc = str(idx_row.get("description", "")).strip()
            if not token:
                continue

            start = idx_row.get("section_start_pdf_page")
            end = idx_row.get("section_end_pdf_page")
            if not isinstance(start, int) or not isinstance(end, int):
                continue

            start = max(1, start)
            end = min(total_pages, end)
            if end < start:
                continue

            sections.append((token, desc, start, end))
            for pdf_page in range(start, end + 1):
                page_numbers.add(pdf_page)

        table_rows_by_page, table_status_by_page = self._extract_table_rows_by_page(sorted(page_numbers))

        records: list[RawRecord] = []
        for token, desc, start, end in sections:
            for pdf_page in range(start, end + 1):
                page_text = reader.pages[pdf_page - 1].extract_text() or ""
                table_rows = table_rows_by_page.get(pdf_page, [])
                table_status = table_status_by_page.get(pdf_page, "")
                if table_rows:
                    method = "table_pdfplumber"
                else:
                    method = "text_pypdf_fallback"

                records.append(
                    {
                        "series_token": token,
                        "series_description": desc,
                        "section_start_pdf_page": start,
                        "section_end_pdf_page": end,
                        "pdf_page": pdf_page,
                        "text": page_text,
                        "table_rows": table_rows,
                        "page_extraction_method": method,
                        "ocr_used": False,
                        "fallback_reason": table_status if method == "text_pypdf_fallback" else "",
                    }
                )

        return records

    def _extract_table_rows_by_page(
        self, page_numbers: list[int]
    ) -> tuple[dict[int, list[list[str]]], dict[int, str]]:
        if not page_numbers:
            return {}, {}

        try:
            import pdfplumber
        except ModuleNotFoundError:
            return {}, {page: "pdfplumber_not_installed" for page in page_numbers}

        rows_by_page: dict[int, list[list[str]]] = {}
        status_by_page: dict[int, str] = {}
        table_settings = {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "intersection_tolerance": 3,
        }

        with pdfplumber.open(str(self.pdf_path)) as pdf:
            total_pages = len(pdf.pages)
            for page_number in page_numbers:
                if page_number < 1 or page_number > total_pages:
                    status_by_page[page_number] = "page_out_of_bounds"
                    continue

                page = pdf.pages[page_number - 1]
                extracted_rows: list[list[str]] = []
                try:
                    tables = page.extract_tables(table_settings=table_settings) or []
                except Exception:
                    status_by_page[page_number] = "table_extraction_error"
                    continue

                for table in tables:
                    for raw_row in table:
                        if not raw_row:
                            continue
                        normalized_row = [self._normalize_cell(cell) for cell in raw_row]
                        if any(normalized_row):
                            extracted_rows.append(normalized_row)

                if not extracted_rows:
                    extracted_rows = self._extract_column_rows_from_words(page)
                    if extracted_rows:
                        rows_by_page[page_number] = extracted_rows
                        status_by_page[page_number] = "table_words_detected"
                        continue

                if extracted_rows:
                    rows_by_page[page_number] = extracted_rows
                    status_by_page[page_number] = "table_detected"
                else:
                    status_by_page[page_number] = "no_tables_detected"

        return rows_by_page, status_by_page

    def _extract_column_rows_from_words(self, page: Any) -> list[list[str]]:
        words = page.extract_words(
            x_tolerance=2,
            y_tolerance=2,
            keep_blank_chars=False,
            use_text_flow=True,
        ) or []
        if not words:
            return []

        desc_x = self._find_header_x(words, "DESCRIPTION")
        chem_x = self._find_header_x(words, "CHEMICAL")
        spec_x = self._find_header_x(words, "CROSS")
        unified_x = self._find_header_x(words, "UNIFIED")

        if desc_x is None or chem_x is None or spec_x is None or unified_x is None:
            return []

        tops = [
            self._find_header_top(words, "NUMBER"),
            self._find_header_top(words, "DESCRIPTION"),
            self._find_header_top(words, "COMPOSITION"),
            self._find_header_top(words, "SPECIFICATIONS"),
        ]
        header_tops = [float(top) for top in tops if top is not None]
        if len(header_tops) < 2:
            return []
        header_top = max(header_tops)

        start_top = header_top + 12
        starts = [float(unified_x), float(desc_x), float(chem_x), float(spec_x)]
        if not (starts[0] < starts[1] < starts[2] < starts[3]):
            return []

        cutoffs = [
            starts[0] - 1.0,
            starts[1] - 10.0,
            starts[2] - 10.0,
            starts[3] - 10.0,
            float(page.width) + 1.0,
        ]
        line_cells = self._build_lines_from_words(words=words, bounds=cutoffs, start_top=start_top)
        return self._lines_to_series_rows(line_cells)

    @staticmethod
    def _find_header_x(words: list[dict[str, Any]], token: str) -> float | None:
        token_upper = token.upper()
        for word in words:
            if str(word.get("text", "")).upper() == token_upper:
                return float(word.get("x0", 0.0))
        return None

    @staticmethod
    def _find_header_top(words: list[dict[str, Any]], token: str) -> float | None:
        token_upper = token.upper()
        for word in words:
            if str(word.get("text", "")).upper() == token_upper:
                return float(word.get("top", 0.0))
        return None

    def _build_lines_from_words(
        self, words: list[dict[str, Any]], bounds: list[float], start_top: float
    ) -> list[dict[int, str]]:
        line_map: dict[int, dict[int, list[tuple[float, str]]]] = {}

        for word in words:
            text = self._normalize_cell(word.get("text", ""))
            if not text:
                continue
            top = float(word.get("top", 0.0))
            if top < start_top:
                continue
            if self._is_footer_word(text):
                continue

            x0 = float(word.get("x0", 0.0))
            col = self._column_for_x(x0, bounds)
            line_key = int(round(top * 2))  # half-point-ish bucket
            line_map.setdefault(line_key, {}).setdefault(col, []).append((x0, text))

        lines: list[dict[int, str]] = []
        for key in sorted(line_map.keys()):
            cols = line_map[key]
            joined: dict[int, str] = {}
            for col, pieces in cols.items():
                pieces_sorted = [text for _, text in sorted(pieces, key=lambda item: item[0])]
                joined[col] = self._normalize_cell(" ".join(pieces_sorted))
            if any(joined.values()):
                lines.append(joined)
        return lines

    @staticmethod
    def _column_for_x(x0: float, bounds: list[float]) -> int:
        for idx in range(len(bounds) - 1):
            if bounds[idx] <= x0 < bounds[idx + 1]:
                return idx
        return 3

    @staticmethod
    def _is_footer_word(text: str) -> bool:
        lowered = text.lower()
        return lowered.startswith("copyright") or lowered.startswith("licensed")

    def _lines_to_series_rows(self, lines: list[dict[int, str]]) -> list[list[str]]:
        rows: list[list[str]] = []
        current: dict[str, list[str] | str] | None = None

        for line in lines:
            code_cell = line.get(0, "")
            desc_cell = line.get(1, "")
            chem_cell = line.get(2, "")
            spec_cell = line.get(3, "")

            uns_code = self._extract_uns_code(code_cell)
            if uns_code:
                if current:
                    rows.append(self._finalize_series_row(current))
                current = {
                    "code": uns_code,
                    "desc": [desc_cell] if desc_cell else [],
                    "chem": [chem_cell] if chem_cell else [],
                    "spec": [spec_cell] if spec_cell else [],
                }
                continue

            if current is None:
                continue
            if desc_cell:
                current["desc"].append(desc_cell)  # type: ignore[union-attr]
            if chem_cell:
                current["chem"].append(chem_cell)  # type: ignore[union-attr]
            if spec_cell:
                current["spec"].append(spec_cell)  # type: ignore[union-attr]

        if current:
            rows.append(self._finalize_series_row(current))
        return rows

    def _extract_uns_code(self, text: str) -> str | None:
        cleaned = "".join(ch for ch in text.upper() if ch.isalnum())
        if not cleaned or not cleaned[0].isalpha():
            return None

        prefix = cleaned[0]
        tail = cleaned[1:].replace("O", "0").replace("I", "1").replace("L", "1")
        tail = re.sub(r"[^0-9]", "", tail)
        if len(tail) < 5:
            return None
        return f"{prefix}{tail[:5]}"

    def _finalize_series_row(self, row: dict[str, list[str] | str]) -> list[str]:
        code = str(row.get("code", "")).strip()
        desc = self._normalize_cell(" ".join(str(x) for x in row.get("desc", [])))
        chem = self._normalize_cell(" ".join(str(x) for x in row.get("chem", [])))
        spec = self._normalize_cell(" ".join(str(x) for x in row.get("spec", [])))
        return [code, desc, chem, spec]

    @staticmethod
    def _normalize_cell(cell: object) -> str:
        text = str(cell or "")
        text = text.replace("\n", " ")
        return re.sub(r"\s+", " ", text).strip()
