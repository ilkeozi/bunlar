from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from material_ingestion.sources.base import RawRecord

UNS_CODE_PATTERN = re.compile(r"\b([A-Z]\d{5})\b")
UNS_TABLE_PATTERN = re.compile(r"^\s*([A-Z]\d{5})\s{2,}(.+?)\s*$")
UNS_DELIMITED_PATTERN = re.compile(r"^\s*([A-Z]\d{5})\s*[-:]\s*(.+?)\s*$")
UNS_GENERIC_PATTERN = re.compile(r"^\s*([A-Z]\d{5})\s+(.+?)\s*$")
UNS_RANGE_STYLE_PATTERN = re.compile(r"^[A-Z][A-Z0-9]{4,5}\s*-\s*[A-Z][A-Z0-9]{4,5}$")

PROFILE_TABLE = "table-like"
PROFILE_DELIMITED = "delimited"
PROFILE_GENERIC = "generic"
PROFILE_CODE_ONLY = "code-only"


class UnsPdfExtractor:
    """Extract source-level UNS rows from PDF text."""

    def extract_raw_records(self, pdf_path: Path, include_code_only: bool = False) -> list[RawRecord]:
        text = self._read_pdf_text(pdf_path)
        return self.extract_raw_records_from_text(text, include_code_only=include_code_only)

    def extract_raw_records_from_text(
        self, text: str, include_code_only: bool = False
    ) -> list[RawRecord]:
        profile = self.detect_structure_profile(text)
        parse_patterns = self._patterns_for_profile(profile)
        rows: list[RawRecord] = []
        seen_uns_codes: set[str] = set()

        for line in self._iter_normalized_lines(text):
            normalized_line = line
            if not normalized_line:
                continue

            parsed = self._parse_line(normalized_line, parse_patterns)
            if parsed is None:
                continue

            uns_code, display_name, parser_name = parsed
            if uns_code in seen_uns_codes:
                continue
            seen_uns_codes.add(uns_code)

            if not self._should_include_record(display_name, parser_name, include_code_only):
                continue

            rows.append(
                {
                    "uns": uns_code,
                    "name": display_name,
                    "standards": [f"UNS {uns_code}"],
                    "metadata": {
                        "extraction_source": "pdf",
                        "extraction_method": "text_pypdf",
                        "ocr_used": False,
                        "profile": profile,
                        "parser": parser_name,
                        "raw_line": normalized_line,
                    },
                }
            )

        return rows

    @staticmethod
    def _should_include_record(name: str, parser_name: str, include_code_only: bool) -> bool:
        if parser_name == "code-only":
            return include_code_only

        normalized = " ".join(name.replace("'", "").split())
        if UNS_CODE_PATTERN.fullmatch(normalized):
            return False
        if UNS_RANGE_STYLE_PATTERN.fullmatch(normalized):
            return False
        if re.search(r"[A-Za-z]{4,}", normalized) is None:
            return False
        return True

    def detect_structure_profile(self, text: str) -> str:
        counts = {
            PROFILE_TABLE: 0,
            PROFILE_DELIMITED: 0,
            PROFILE_GENERIC: 0,
            PROFILE_CODE_ONLY: 0,
        }

        for line in self._iter_normalized_lines(text):
            if UNS_TABLE_PATTERN.match(line):
                counts[PROFILE_TABLE] += 1
            elif UNS_DELIMITED_PATTERN.match(line):
                counts[PROFILE_DELIMITED] += 1
            elif UNS_GENERIC_PATTERN.match(line):
                counts[PROFILE_GENERIC] += 1
            elif UNS_CODE_PATTERN.fullmatch(line):
                counts[PROFILE_CODE_ONLY] += 1

        if counts[PROFILE_TABLE] > 0 and counts[PROFILE_TABLE] >= counts[PROFILE_DELIMITED]:
            return PROFILE_TABLE
        if counts[PROFILE_DELIMITED] > 0:
            return PROFILE_DELIMITED
        if counts[PROFILE_GENERIC] > 0:
            return PROFILE_GENERIC
        return PROFILE_CODE_ONLY

    @staticmethod
    def _patterns_for_profile(profile: str) -> list[tuple[str, re.Pattern[str]]]:
        if profile == PROFILE_TABLE:
            return [
                ("table", UNS_TABLE_PATTERN),
                ("delimited", UNS_DELIMITED_PATTERN),
                ("generic", UNS_GENERIC_PATTERN),
            ]
        if profile == PROFILE_DELIMITED:
            return [
                ("delimited", UNS_DELIMITED_PATTERN),
                ("table", UNS_TABLE_PATTERN),
                ("generic", UNS_GENERIC_PATTERN),
            ]
        return [
            ("generic", UNS_GENERIC_PATTERN),
            ("delimited", UNS_DELIMITED_PATTERN),
            ("table", UNS_TABLE_PATTERN),
        ]

    @staticmethod
    def _parse_line(
        line: str, patterns: Iterable[tuple[str, re.Pattern[str]]]
    ) -> tuple[str, str, str] | None:
        for parser_name, pattern in patterns:
            match = pattern.match(line)
            if match:
                uns_code = match.group(1)
                trailing = match.group(2).strip(" -:\t")
                display_name = trailing if trailing else f"UNS {uns_code}"
                return uns_code, display_name, parser_name

        direct = UNS_CODE_PATTERN.fullmatch(line)
        if direct:
            uns_code = direct.group(1)
            return uns_code, f"UNS {uns_code}", "code-only"

        return None

    @staticmethod
    def _iter_normalized_lines(text: str) -> Iterable[str]:
        for line in text.splitlines():
            # preserve column spacing for table detection while trimming edges
            yield re.sub(r"\s+$", "", re.sub(r"^\s+", "", line))

    @staticmethod
    def _read_pdf_text(pdf_path: Path) -> str:
        try:
            from pypdf import PdfReader
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "PDF extraction requires 'pypdf'. Install it with: python3 -m pip install pypdf"
            ) from exc

        reader = PdfReader(str(pdf_path))
        pages_text: list[str] = []
        for page in reader.pages:
            pages_text.append(page.extract_text() or "")
        return "\n".join(pages_text)
