from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from material_ingestion.sources.base import RawRecord
from material_ingestion.sources.uns import UnsPdfPageSource

SERIES_TOKEN_PATTERN = re.compile(r"^([A-Za-z])x{5}$")
ENTRY_PATTERN = re.compile(r"^(.*?)\s*\.{2,}\s*(\d{1,3})$")


class UnsSeriesPageIndexExtractor:
    """Extract UNS series -> listing page index entries from the table of contents page."""

    def extract(self, pdf_path: Path, toc_page: int = 12) -> list[dict[str, str | int]]:
        if toc_page < 1:
            raise ValueError("toc_page must be 1-based.")

        source = UnsPdfPageSource(pdf_path=pdf_path, pages=[toc_page])
        return self.extract_rows(source.fetch())

    def extract_rows(self, raw_records: Iterable[RawRecord]) -> list[RawRecord]:
        rows: list[RawRecord] = []
        for raw in raw_records:
            text = str(raw.get("text", ""))
            pdf_page = int(raw.get("pdf_page", 0))
            rows.extend(
                self.extract_from_text(
                    text=text,
                    page_number=pdf_page,
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
        extraction_method: str = "text_pypdf",
        ocr_used: bool = False,
        fallback_reason: str = "",
    ) -> list[dict[str, str | int]]:
        lines = [self._normalize_line(line) for line in text.splitlines() if line.strip()]
        series_tokens = self._extract_series_tokens(lines)
        listing_lines = self._extract_listing_block(lines)
        entries = self._parse_entries(listing_lines)
        return self._assign_series(entries, series_tokens, page_number, extraction_method, ocr_used, fallback_reason)

    @staticmethod
    def _normalize_line(line: str) -> str:
        return " ".join(line.replace("..", ".").split())

    def _extract_series_tokens(self, lines: list[str]) -> list[str]:
        tokens: list[str] = []
        for line in lines:
            match = SERIES_TOKEN_PATTERN.match(line)
            if match:
                tokens.append(match.group(1).upper())
        return tokens

    def _extract_listing_block(self, lines: list[str]) -> list[str]:
        start_idx = -1
        end_idx = len(lines)
        for idx, line in enumerate(lines):
            if "Listing of UNS Numbers Assigned to Date" in line:
                start_idx = idx
            if "Cross Index of Commonly Known Documents" in line and start_idx != -1:
                end_idx = idx
                break
        if start_idx == -1:
            return []
        return lines[start_idx:end_idx]

    def _parse_entries(self, listing_lines: list[str]) -> list[tuple[str, int]]:
        entries: list[tuple[str, int]] = []
        pending_desc: str | None = None

        for line in listing_lines:
            if SERIES_TOKEN_PATTERN.match(line):
                continue
            if line.startswith("Listing of UNS Numbers Assigned to Date"):
                continue
            if line.startswith("References to Documents"):
                continue

            match = ENTRY_PATTERN.match(line)
            if match:
                desc = match.group(1).strip(" .")
                page = int(match.group(2))
                if pending_desc:
                    desc = f"{pending_desc} {desc}".strip()
                    pending_desc = None
                entries.append((desc, page))
                continue

            # continuation line of a wrapped description
            if pending_desc:
                pending_desc = f"{pending_desc} {line}".strip()
            else:
                pending_desc = line

        return entries

    def _assign_series(
        self,
        entries: list[tuple[str, int]],
        series_tokens: list[str],
        toc_page: int,
        extraction_method: str,
        ocr_used: bool,
        fallback_reason: str,
    ) -> list[dict[str, str | int]]:
        keyword_map = [
            (r"\bAluminum and Aluminum Alloys\b", "A"),
            (r"\bCopper and Copper Alloys\b", "C"),
            (r"\bRare Earth and Similar Metals and Alloys\b", "E"),
            (r"\bCast Irons\b", "F"),
            (r"\bAISI and SAE Carbon and Alloy Steels\b", "G"),
            (r"\bAISI and SAE H-Steels\b", "H"),
            (r"\bCast Steels\b", "J"),
            (r"\bMiscellaneous Steels and Ferrous Alloys\b", "K"),
            (r"\bLow Melting Metals and Alloys\b", "L"),
            (r"\bMiscellaneous Nonferrous Metals and Alloys\b", "M"),
            (r"\bNickel and Nickel Alloys\b", "N"),
            (r"\bPrecious Metals and Alloys\b", "P"),
            (r"\bReactive and Refractory Metals and Alloys\b", "R"),
            (r"\bHeat and Corrosion Resistant Steels\b", "S"),
            (r"\bTool Steels\b", "T"),
            (r"\bWelding Filler Metals\b", "W"),
            (r"\bZinc and Zinc Alloys\b", "Z"),
        ]
        token_pool = list(series_tokens)

        rows: list[dict[str, str | int]] = []
        for description, page in entries:
            series: str | None = None
            for pattern, mapped in keyword_map:
                if re.search(pattern, description, flags=re.IGNORECASE):
                    series = mapped
                    break

            if series is None and token_pool:
                series = token_pool.pop(0)

            row = {
                "series": series or "",
                "series_token": f"{series}xxxxx" if series else "",
                "description": description,
                "target_label": str(page),
                "target_page": page,
                "toc_page": toc_page,
                "extraction_method": extraction_method,
                "ocr_used": ocr_used,
            }
            if fallback_reason:
                row["fallback_reason"] = fallback_reason
            rows.append(row)

        return rows
