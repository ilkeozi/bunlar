from __future__ import annotations

import re
from typing import Iterable

from material_ingestion.sources.base import RawRecord


UNS_CODE_LINE_PATTERN = re.compile(r"^[\s*'\"‘’“”]*([A-Z])\s*([0-9OIl]{5})(?:\b|\s)(.*)$")
UNS_CODE_ANYWHERE_PATTERN = re.compile(r"\b([A-Z])\s*([0-9OIl]{5})\b")


class UnsSeriesDataExtractor:
    """Extract UNS rows from section pages selected via TOC series index."""

    def extract_rows(self, raw_records: Iterable[RawRecord]) -> list[RawRecord]:
        rows: list[RawRecord] = []
        current: RawRecord | None = None

        sorted_records = sorted(
            raw_records, key=lambda r: (str(r.get("series_token", "")), int(r.get("pdf_page", 0)))
        )

        for rec in sorted_records:
            series_token = str(rec.get("series_token", ""))
            series_desc = str(rec.get("series_description", ""))
            page_text = str(rec.get("text", ""))
            page_number = int(rec.get("pdf_page", 0))
            page_has_boxed_note = "boxed entries are no longer active" in page_text.lower()

            table_rows = rec.get("table_rows")
            if isinstance(table_rows, list) and table_rows:
                current, found_table_entries = self._extract_from_table_rows(
                    rec=rec,
                    table_rows=table_rows,
                    page_has_boxed_note=page_has_boxed_note,
                    page_number=page_number,
                    series_token=series_token,
                    series_desc=series_desc,
                    current=current,
                    rows=rows,
                )
                if found_table_entries:
                    continue

            lines = [line.rstrip() for line in page_text.splitlines() if line.strip()]
            for raw_line in lines:
                normalized = " ".join(raw_line.split())
                if self._should_skip_line(normalized):
                    continue

                code_match = UNS_CODE_LINE_PATTERN.match(raw_line)
                if code_match:
                    if current:
                        rows.append(self._finalize(current))

                    code = self._normalize_code(code_match.group(1), code_match.group(2))
                    desc_part = code_match.group(3).strip()
                    leading_marker = raw_line.lstrip()[:1]
                    current = {
                        "series_token": series_token,
                        "series_description": series_desc,
                        "section_start_pdf_page": rec.get("section_start_pdf_page"),
                        "section_end_pdf_page": rec.get("section_end_pdf_page"),
                        "uns_code": code,
                        "entry_lines": [desc_part] if desc_part else [],
                        "entry_pdf_page_start": page_number,
                        "entry_pdf_page_end": page_number,
                        "inactive_boxed_marker": bool(leading_marker in {"*", "'", "‘", "’", "\"", "“", "”"}),
                        "page_has_boxed_note": page_has_boxed_note,
                        "extraction_method": "text_pypdf_fallback",
                        "ocr_used": bool(rec.get("ocr_used", False)),
                        "fallback_reason": str(rec.get("fallback_reason", "")),
                    }
                    continue

                if current:
                    current["entry_lines"].append(normalized)
                    current["entry_pdf_page_end"] = page_number

        if current:
            rows.append(self._finalize(current))

        return rows

    def _finalize(self, row: RawRecord) -> RawRecord:
        raw_lines = [str(x).strip() for x in row.get("entry_lines", []) if str(x).strip()]
        entry_text = " ".join(raw_lines)
        finalized = dict(row)
        finalized["entry_text"] = entry_text
        finalized["entry_raw_lines"] = raw_lines
        finalized["table_description_lines"] = [
            str(x).strip() for x in row.get("table_description_lines", []) if str(x).strip()
        ]
        finalized["table_chemical_composition_lines"] = [
            str(x).strip() for x in row.get("table_chemical_composition_lines", []) if str(x).strip()
        ]
        finalized["table_cross_reference_lines"] = [
            str(x).strip() for x in row.get("table_cross_reference_lines", []) if str(x).strip()
        ]
        finalized.pop("entry_lines", None)
        return finalized

    def _extract_from_table_rows(
        self,
        rec: RawRecord,
        table_rows: list[object],
        page_has_boxed_note: bool,
        page_number: int,
        series_token: str,
        series_desc: str,
        current: RawRecord | None,
        rows: list[RawRecord],
    ) -> tuple[RawRecord | None, bool]:
        found_table_entries = False

        for raw_row in table_rows:
            cells = self._normalize_table_row(raw_row)
            if not any(cells):
                continue
            if self._is_table_header_row(cells):
                continue

            code_match = UNS_CODE_ANYWHERE_PATTERN.search(cells[0])
            if code_match:
                found_table_entries = True
                if current:
                    rows.append(self._finalize(current))

                code = self._normalize_code(code_match.group(1), code_match.group(2))
                description = cells[1]
                composition = cells[2]
                cross_reference = cells[3]
                entry_lines = [part for part in (description, composition, cross_reference) if part]
                leading_marker = cells[0].lstrip()[:1]

                current = {
                    "series_token": series_token,
                    "series_description": series_desc,
                    "section_start_pdf_page": rec.get("section_start_pdf_page"),
                    "section_end_pdf_page": rec.get("section_end_pdf_page"),
                    "uns_code": code,
                    "entry_lines": entry_lines,
                    "entry_pdf_page_start": page_number,
                    "entry_pdf_page_end": page_number,
                    "inactive_boxed_marker": bool(leading_marker in {"*", "'", "‘", "’", "\"", "“", "”"}),
                    "page_has_boxed_note": page_has_boxed_note,
                    "table_description_lines": [description] if description else [],
                    "table_chemical_composition_lines": [composition] if composition else [],
                    "table_cross_reference_lines": [cross_reference] if cross_reference else [],
                    "extraction_method": "table_pdfplumber",
                    "ocr_used": bool(rec.get("ocr_used", False)),
                    "fallback_reason": "",
                }
                continue

            if current:
                current["entry_pdf_page_end"] = page_number
                if cells[1]:
                    current.setdefault("table_description_lines", []).append(cells[1])
                    current["entry_lines"].append(cells[1])
                if cells[2]:
                    current.setdefault("table_chemical_composition_lines", []).append(cells[2])
                    current["entry_lines"].append(cells[2])
                if cells[3]:
                    current.setdefault("table_cross_reference_lines", []).append(cells[3])
                    current["entry_lines"].append(cells[3])

        return current, found_table_entries

    @staticmethod
    def _normalize_table_row(raw_row: object) -> list[str]:
        if not isinstance(raw_row, list):
            raw_row = [str(raw_row)]

        cells = [" ".join(str(cell or "").split()) for cell in raw_row]
        if len(cells) < 4:
            cells.extend([""] * (4 - len(cells)))
        elif len(cells) > 4:
            cells = cells[:3] + [" ".join(part for part in cells[3:] if part)]
        return cells

    @staticmethod
    def _is_table_header_row(cells: list[str]) -> bool:
        lowered = " ".join(cells).lower()
        return (
            "unified number" in lowered
            or ("number" in lowered and "description" in lowered and "chemical composition" in lowered)
            or "cross reference specifications" in lowered
        )

    @staticmethod
    def _normalize_code(prefix: str, digits: str) -> str:
        cleaned = digits.upper().replace("O", "0").replace("I", "1").replace("L", "1")
        cleaned = re.sub(r"[^0-9]", "", cleaned)
        cleaned = cleaned[:5].ljust(5, "0")
        return f"{prefix.upper()}{cleaned}"

    @staticmethod
    def _should_skip_line(line: str) -> bool:
        lowered = line.lower()
        if not line:
            return True
        skip_prefixes = (
            "copyright ",
            "licensed by information",
            "unified number",
            "number description",
            "chemical composition",
            "cross reference specifications",
            "uns numbers assigned to date",
            "with description of each material covered",
            "references to documents in which the same or",
            "similar materials are described",
            "the chemical compositions listed are for identification purposes",
            "boxed entries are no longer active",
        )
        if lowered.startswith(skip_prefixes):
            return True
        if re.fullmatch(r"\d{1,3}", line):
            return True
        return False
