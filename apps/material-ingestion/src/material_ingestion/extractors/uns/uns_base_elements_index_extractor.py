from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from material_ingestion.sources.base import RawRecord
from material_ingestion.sources.uns import UnsPdfPageSource


HEADER_PATTERN = re.compile(r"^Element Svmbol UNS Decianation$", re.IGNORECASE)
SYMBOL_PATTERN = re.compile(r"^[A-Za-z]{1,2}(?:,\s*[A-Za-z]{2})?$")
RANGE_LINE_PATTERN = re.compile(r".*\d.*-.*\d.*")
MERGED_SYMBOL_RANGE_PATTERN = re.compile(r"^([A-Za-z]{1,2})\s+(.+\d.*-.*\d.*)$")
CODE_ONLY_PATTERN = re.compile(r"^[A-Za-z0-9]{5,7}$")
RANGE_TAIL_PATTERN = re.compile(r"^-\s*[A-Za-z0-9]{5,7}$")


class UnsBaseElementsIndexExtractor:
    """Extract page-14 'Index to UNS Designations by Base Elements' table."""

    def extract(self, pdf_path: Path, index_page: int = 14) -> list[RawRecord]:
        source = UnsPdfPageSource(pdf_path=pdf_path, pages=[index_page])
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
    ) -> list[RawRecord]:
        lines = [self._normalize_line(line) for line in text.splitlines() if line.strip()]
        blocks = self._split_blocks(lines)
        rows: list[RawRecord] = []
        order = 0

        for block in blocks:
            elements, symbols, ranges = self._parse_block(block)
            count = max(len(elements), len(ranges), len(symbols))
            for i in range(count):
                element_name = elements[i] if i < len(elements) else ""
                symbol = symbols[i] if i < len(symbols) else ""
                uns_range = ranges[i] if i < len(ranges) else ""
                symbol = self._normalize_symbol(symbol, element_name, uns_range)
                uns_range = self._normalize_uns_range(uns_range, symbol)
                if not element_name and not uns_range:
                    continue

                order += 1
                rows.append(
                    {
                        "element_name": element_name,
                        "symbol": symbol,
                        "uns_range": uns_range,
                        "index_label": "ix",
                        "index_pdf_page": page_number,
                        "row_order": order,
                        "extraction_method": extraction_method,
                        "ocr_used": ocr_used,
                    }
                )
                if fallback_reason:
                    rows[-1]["fallback_reason"] = fallback_reason
        return rows

    def _split_blocks(self, lines: list[str]) -> list[list[str]]:
        header_idx = [i for i, line in enumerate(lines) if HEADER_PATTERN.match(line)]
        blocks: list[list[str]] = []
        for i, start in enumerate(header_idx):
            end = header_idx[i + 1] if i + 1 < len(header_idx) else len(lines)
            block = [line for line in lines[start + 1 : end] if not self._is_footer_line(line)]
            if block:
                blocks.append(block)
        return blocks

    def _parse_block(self, block: list[str]) -> tuple[list[str], list[str], list[str]]:
        symbol_start = next((i for i, line in enumerate(block) if SYMBOL_PATTERN.match(line)), len(block))
        range_start = self._find_range_start(block, symbol_start)

        element_lines = block[:symbol_start]
        symbol_lines = block[symbol_start:range_start]
        range_lines = block[range_start:]

        elements = self._collapse_wrapped_elements(element_lines)
        symbols = [line for line in symbol_lines if SYMBOL_PATTERN.match(line)]
        ranges = self._collapse_ranges(range_lines)

        return elements, symbols, ranges

    def _find_range_start(self, block: list[str], symbol_start: int) -> int:
        for i in range(symbol_start, len(block)):
            line = block[i]
            if RANGE_LINE_PATTERN.match(line):
                return i
            if CODE_ONLY_PATTERN.match(line) and i + 1 < len(block) and RANGE_TAIL_PATTERN.match(block[i + 1]):
                return i
            if RANGE_TAIL_PATTERN.match(line):
                return i
        return len(block)

    def _collapse_wrapped_elements(self, lines: list[str]) -> list[str]:
        rows: list[str] = []
        for line in lines:
            if not rows:
                rows.append(line)
                continue

            if line.startswith("-") or self._is_continuation_line(rows[-1], line):
                rows[-1] = f"{rows[-1]} {line}".replace("  ", " ")
            else:
                rows.append(line)
        return [row.strip() for row in rows]

    def _collapse_ranges(self, lines: list[str]) -> list[str]:
        ranges: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # Handle OCR split rows like:
            # E00000
            # - E00999
            if CODE_ONLY_PATTERN.match(line) and i + 1 < len(lines) and RANGE_TAIL_PATTERN.match(lines[i + 1]):
                ranges.append(f"{line} {lines[i + 1]}")
                i += 2
                continue
            if RANGE_TAIL_PATTERN.match(line):
                i += 1
                continue

            merged = MERGED_SYMBOL_RANGE_PATTERN.match(line)
            if merged:
                symbol = merged.group(1)
                raw_range = merged.group(2)
                ranges.append(f"{symbol} {raw_range}")
                i += 1
                continue
            if RANGE_LINE_PATTERN.match(line):
                ranges.append(line)
            i += 1
        return ranges

    @staticmethod
    def _normalize_line(line: str) -> str:
        return " ".join(line.split())

    @staticmethod
    def _is_footer_line(line: str) -> bool:
        lowered = line.lower()
        return (
            lowered == "ix"
            or lowered.startswith("copyright")
            or lowered.startswith("licensed by information")
            or lowered.startswith("index to uns designations by base elements")
        )

    @staticmethod
    def _is_continuation_line(previous: str, line: str) -> bool:
        continuation_tokens = {
            "High Temperature",
            "Alloys",
            "Stainless Steels",
            "Chromium Low Alloy",
            "and Low Alloy Steels",
        }
        if line in continuation_tokens:
            if line == "Alloys":
                return previous.endswith("High Temperature") or previous.endswith("Molybdenum")
            if line == "Stainless Steels":
                return previous.endswith("- Austenitic") or previous.endswith("- Ferritic")
            if line == "Chromium Low Alloy":
                return previous.endswith("Metal -")
            return True

        if line == "Steels":
            return previous.endswith("Low Alloy")

        if line == "Alloys":
            return True
        return line.startswith("(")

    @staticmethod
    def _normalize_symbol(symbol: str, element_name: str, uns_range: str) -> str:
        symbol = symbol.strip()
        if "," in symbol:
            symbol = symbol.split(",")[0].strip()

        replacements = {
            "AI": "Al",
            "cs": "Cs",
            "os": "Os",
            "sc": "Sc",
            "si": "Si",
            "DY": "Dy",
            "TI": "Tl",
            "v": "V",
        }
        symbol = replacements.get(symbol, symbol)

        if not symbol and uns_range:
            m = re.match(r"^([A-Za-z])", uns_range)
            if m:
                symbol = m.group(1).upper()

        if len(symbol) == 1:
            return symbol.upper()
        if len(symbol) >= 2:
            return symbol[0].upper() + symbol[1:].lower()
        return symbol

    @staticmethod
    def _normalize_uns_range(raw_range: str, symbol: str) -> str:
        text = raw_range.replace("'", "").strip()
        if not text:
            return text

        merged = MERGED_SYMBOL_RANGE_PATTERN.match(text)
        if merged:
            text = merged.group(2)

        text = text.upper()
        text = text.replace(" - ", "-").replace(" -", "-").replace("- ", "-")
        parts = text.split("-", 1)
        if len(parts) != 2:
            return raw_range

        left = UnsBaseElementsIndexExtractor._normalize_code(parts[0], symbol)
        right = UnsBaseElementsIndexExtractor._normalize_code(parts[1], symbol)
        return f"{left}-{right}"

    @staticmethod
    def _normalize_code(code: str, symbol: str) -> str:
        cleaned = "".join(ch for ch in code if ch.isalnum())
        if not cleaned:
            return cleaned

        cleaned = cleaned.upper().replace("O", "0")
        if cleaned[0].isdigit() and symbol:
            cleaned = symbol[0].upper() + cleaned[1:]

        if cleaned[0].isalpha():
            head = cleaned[0]
            tail = cleaned[1:].replace("I", "1").replace("L", "1")
            tail = re.sub(r"[^0-9]", "", tail)
            if len(tail) < 5:
                tail = tail.rjust(5, "0")
            else:
                tail = tail[:5]
            return f"{head}{tail}"

        return cleaned
