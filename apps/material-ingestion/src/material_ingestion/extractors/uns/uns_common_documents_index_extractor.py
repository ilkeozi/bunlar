from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from material_ingestion.sources.base import RawRecord
from material_ingestion.sources.uns import UnsPdfPageSource


ENTRY_PATTERN = re.compile(r"^(.*?)\s*\.{2,}\s*(\d{1,3})$")
UPPER_TOKEN_PATTERN = re.compile(r"^[A-Z0-9]{2,8}$")


class UnsCommonDocumentsIndexExtractor:
    """Extract the 'Cross Index of Commonly Known Documents' table from the TOC page."""

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
        block = self._extract_cross_index_block(lines)
        return self._parse_entries(
            block,
            page_number=page_number,
            extraction_method=extraction_method,
            ocr_used=ocr_used,
            fallback_reason=fallback_reason,
        )

    @staticmethod
    def _normalize_line(line: str) -> str:
        return " ".join(line.split())

    def _extract_cross_index_block(self, lines: list[str]) -> list[str]:
        start_idx = -1
        end_idx = len(lines)
        for idx, line in enumerate(lines):
            if line.startswith("Cross Index of Commonly Known Documents"):
                start_idx = idx
            if line.startswith("Index of Common Trade Names") and start_idx != -1:
                end_idx = idx
                break
        if start_idx == -1:
            return []
        return lines[start_idx:end_idx]

    def _parse_entries(
        self,
        block_lines: list[str],
        page_number: int,
        extraction_method: str,
        ocr_used: bool,
        fallback_reason: str,
    ) -> list[dict[str, str | int]]:
        rows: list[dict[str, str | int]] = []
        pending_prefix = ""
        pending_line = ""

        for line in block_lines:
            if line.startswith("Cross Index of Commonly Known Documents"):
                continue
            if line.startswith("Those Covered by UNS Numbers"):
                continue

            if UPPER_TOKEN_PATTERN.fullmatch(line):
                pending_prefix = line
                continue

            pending_line = f"{pending_line} {line}".strip() if pending_line else line
            match = ENTRY_PATTERN.match(pending_line)
            if not match:
                continue

            title = match.group(1).strip(" .")
            target_page = int(match.group(2))
            reconstructed_line = pending_line

            if pending_prefix and title.startswith("("):
                title = f"{pending_prefix} {title}"
                reconstructed_line = f"{pending_prefix} {pending_line}"
                pending_prefix = ""

            code, description = self._split_code_and_description(title)
            rows.append(
                {
                    "document_code": code,
                    "description": description,
                    "target_label": str(target_page),
                    "target_page": target_page,
                    "toc_page": page_number,
                    "raw_line": reconstructed_line,
                    "extraction_method": extraction_method,
                    "ocr_used": ocr_used,
                }
            )
            if fallback_reason:
                rows[-1]["fallback_reason"] = fallback_reason
            pending_line = ""

        return rows

    @staticmethod
    def _split_code_and_description(title: str) -> tuple[str, str]:
        # Typical: "ASTM (American Society for Testing and Materials) Numbers"
        m = re.match(r"^([A-Z0-9]{2,8})\s+(.+)$", title)
        if m:
            return m.group(1), title

        # Fallback: "Federal Specification Numbers"
        head = title.split()[0] if title else ""
        return head, title
