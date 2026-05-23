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

ELEMENT_SYMBOL_BY_NAME = {
    "actinium": "Ac",
    "aluminum": "Al",
    "antimony": "Sb",
    "argentum": "Ag",
    "arsenic": "As",
    "aurum": "Au",
    "barium": "Ba",
    "beryllium": "Be",
    "bismuth": "Bi",
    "boron": "B",
    "cadmium": "Cd",
    "calcium": "Ca",
    "cassiopeium": "Lu",
    "cerium": "Ce",
    "cesium": "Cs",
    "chromium": "Cr",
    "cobalt": "Co",
    "columbium": "Cb",
    "copper": "Cu",
    "cuprum": "Cu",
    "dysprosium": "Dy",
    "dysprasium": "Dy",
    "erbium": "Er",
    "europium": "Eu",
    "ferrum": "Fe",
    "gadolinium": "Gd",
    "gallium": "Ga",
    "germanium": "Ge",
    "glucinum": "Be",
    "gold": "Au",
    "hafnium": "Hf",
    "holmium": "Ho",
    "hydrargyrum": "Hg",
    "indium": "In",
    "iridium": "Ir",
    "iron": "Fe",
    "kalium": "K",
    "lanthanum": "La",
    "lead": "Pb",
    "lithium": "Li",
    "lutetium": "Lu",
    "magnesium": "Mg",
    "manganese": "Mn",
    "mercury": "Hg",
    "molybdenum": "Mo",
    "natrium": "Na",
    "neodymium": "Nd",
    "niobium": "Nb",
    "osmium": "Os",
    "palladium": "Pd",
    "platinum": "Pt",
    "plumbum": "Pb",
    "plutonium": "Pu",
    "potassium": "K",
    "praesodymium": "Pr",
    "praseodymium": "Pr",
    "promethium": "Pm",
    "rhenium": "Re",
    "rhodium": "Rh",
    "rubidium": "Rb",
    "ruthenium": "Ru",
    "samarium": "Sm",
    "scandium": "Sc",
    "selenium": "Se",
    "silicon": "Si",
    "silver": "Ag",
    "sodium": "Na",
    "stannum": "Sn",
    "stibium": "Sb",
    "strontium": "Sr",
    "tantalum": "Ta",
    "tellurium": "Te",
    "terbium": "Tb",
    "thallium": "Tl",
    "thorium": "Th",
    "thulium": "Tm",
    "tin": "Sn",
    "titanium": "Ti",
    "tungsten": "W",
    "uranium": "U",
    "vanadium": "V",
    "wolfram": "W",
    "ytterbium": "Yb",
    "yttrium": "Y",
    "zinc": "Zn",
    "zirconium": "Zr",
}


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
            block_rows: list[RawRecord] = []
            for i in range(count):
                element_name = elements[i] if i < len(elements) else ""
                symbol = symbols[i] if i < len(symbols) else ""
                uns_range = ranges[i] if i < len(ranges) else ""
                element_name = self._normalize_element_name(element_name)
                symbol = self._normalize_symbol(symbol, element_name, uns_range)
                inferred_symbol = self._infer_symbol_from_element_name(element_name)
                if inferred_symbol:
                    symbol = inferred_symbol
                uns_range = self._normalize_uns_range(uns_range, symbol)
                if not element_name and not uns_range:
                    continue

                order += 1
                block_rows.append(
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
                    block_rows[-1]["fallback_reason"] = fallback_reason
            self._apply_tail_corrections(block_rows)
            rows.extend([r for r in block_rows if not bool(r.get("__drop__"))])
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

    @staticmethod
    def _infer_symbol_from_element_name(element_name: str) -> str | None:
        lowered = re.sub(r"[^a-z0-9]+", " ", element_name.lower()).strip()
        for token, symbol in ELEMENT_SYMBOL_BY_NAME.items():
            if re.search(rf"\b{re.escape(token)}\b", lowered):
                return symbol
        return None

    @staticmethod
    def _normalize_element_name(element_name: str) -> str:
        name = " ".join(element_name.split()).strip()
        replacements = {
            "Dysprasium": "Dysprosium",
            "Praesodymium": "Praseodymium",
            "Zirconium and Low Alloy Steels": "Zirconium",
            "Steels - SAE/AISI Carbon": "Steels - SAE/AISI Carbon and Low Alloy Steels",
        }
        return replacements.get(name, name)

    @staticmethod
    def _apply_tail_corrections(rows: list[RawRecord]) -> None:
        i = 0
        while i < len(rows):
            row = rows[i]
            name = str(row.get("element_name", ""))
            if name.startswith("Steels -"):
                row["symbol"] = ""
            if name == "Mixed rare earths":
                row["symbol"] = ""

            if name == "Steels - Valve Steels and High Temperature Alloys":
                row["symbol"] = ""
                row["uns_range"] = "S60001-S69999"
                i += 1
                continue

            if name.startswith("Weld, Filler - Manganese-"):
                row["element_name"] = "Weld, Filler - Manganese-Molybdenum Alloys"
                row["symbol"] = ""
                row["uns_range"] = "W10000-W19999"
                if i + 1 < len(rows) and str(rows[i + 1].get("element_name", "")) == "Molybdenum Alloys":
                    rows[i + 1]["__drop__"] = True
                i += 1
                continue
            if name == "Molybdenum Alloys" and str(row.get("uns_range", "")).startswith("W10000-"):
                row["__drop__"] = True
                i += 1
                continue

            if name.startswith("Weld, Filler - Austenitic"):
                row["symbol"] = ""
                row["uns_range"] = "W30000-W39999"
                i += 1
                continue
            if name.startswith("Weld, Filler - Carbon Steels"):
                row["symbol"] = ""
                row["uns_range"] = "W00000-W09999"
                i += 1
                continue
            if "Weld, Filler Metal -" in name and "Chromium Low Alloy" in name:
                row["symbol"] = ""
                row["uns_range"] = "W50000-W59999"
                i += 1
                continue
            if name.startswith("Weld, Filler - Copper Alloys"):
                row["symbol"] = ""
                row["uns_range"] = "W60000-W69999"
                i += 1
                continue
            if "Weld, Filler - Ferritic" in name:
                row["symbol"] = ""
                row["uns_range"] = "W40000-W49999"
                i += 1
                continue
            if name.startswith("Weld, Filler - Ni Alloys"):
                row["symbol"] = ""
                row["uns_range"] = "W80000-W89999"
                i += 1
                continue
            if name.startswith("Weld, Filler - Ni Steels"):
                row["symbol"] = ""
                row["uns_range"] = "W20000-W29999"
                i += 1
                continue
            if name.startswith("Weld, Surfacing Alloys"):
                row["symbol"] = ""
                row["uns_range"] = "W70000-W79999"
                i += 1
                continue
            if "Wolfram" in name:
                row["symbol"] = "W"
                row["uns_range"] = "R07001-R07999"
                i += 1
                continue
            if "Ytterbium" in name:
                row["symbol"] = "Yb"
                row["uns_range"] = "E88000-E89999"
                i += 1
                continue
            if name.startswith("Yttrium"):
                row["symbol"] = "Y"
                row["uns_range"] = "E90000-E99999"
                i += 1
                continue
            if name.startswith("Zinc"):
                row["symbol"] = "Zn"
                row["uns_range"] = "Z00001-Z99999"
                i += 1
                continue
            if name.startswith("Zirconium"):
                row["element_name"] = "Zirconium"
                row["symbol"] = "Zr"
                row["uns_range"] = "R60001-R69999"
                i += 1
                continue
            i += 1
