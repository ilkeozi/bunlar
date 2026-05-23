from __future__ import annotations

import re

from material_ingestion.normalizers.base import Normalizer
from material_ingestion.sources.base import RawRecord


REPLACED_BY_PATTERN = re.compile(r"replaced\s+by\s+([A-Z])\s*([0-9OIl]{5})", re.IGNORECASE)
CHEM_TOKEN_PATTERN = re.compile(r"\b[A-Z][a-z]?\s*[0-9]")
SPEC_TOKEN_PATTERN = re.compile(
    r"\b(AA|ASTM|AMS|ASME|AWS|SAE|MIL|FEDERAL|AISI|NACE|UNS|ACI|SFSA)\b",
    re.IGNORECASE,
)
CHEM_START_ELEMENT_VALUE_PATTERN = re.compile(
    r"\b(?:[A-Z][a-z]?|AI|Ci)\s*(?:rem|nom|min|max|[0-9]+(?:\.[0-9]+)?(?:\s*-\s*[0-9]+(?:\.[0-9]+)?)?)\b",
    re.IGNORECASE,
)
CHEM_START_VALUE_ELEMENT_PATTERN = re.compile(
    r"\b[0-9]+(?:\.[0-9]+)?(?:\s*-\s*[0-9]+(?:\.[0-9]+)?)?\s+(?:[A-Z][a-z]?|AI|Ci)\b",
)
AA_SPEC_FRAGMENT_PATTERN = re.compile(r"\bAA\s+A?\s*\d{3,4}(?:\.\d+)?\b", re.IGNORECASE)
GENERIC_SPEC_FRAGMENT_PATTERN = re.compile(
    r"\b(?:ASTM|AMS|ASME|AWS|SAE|MIL|FEDERAL|AISI|NACE|UNS|ACI|SFSA)\s+[A-Z0-9][A-Z0-9()./\-]*(?:\s+[A-Z0-9()./\-]+)?\b",
    re.IGNORECASE,
)
NUMERIC_PATTERN = re.compile(r"^\d+(?:\.\d+)?$")
RANGE_PATTERN = re.compile(r"^(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)$")
ELEMENT_TOKEN_PATTERN = re.compile(r"^(?:[A-Za-z]{1,2}|Other)$")
ELEMENT_CORRECTIONS = {
    "AI": ("Al", "Corrected from text extraction artifact 'AI'"),
    "CI": ("Si", "Corrected from text extraction artifact 'Ci'"),
    "CB": ("Nb", "Normalized legacy niobium symbol 'Cb' to 'Nb'"),
}
KNOWN_CROSSREF_DOCUMENT_CODES = {
    "AA",
    "ACI",
    "AC1",
    "AISI",
    "AMS",
    "ASME",
    "ASTM",
    "AWS",
    "FEDERAL",
    "MAM",
    "MIL",
    "NACE",
    "SAE",
    "SFSA",
    "UNS",
}
DOCUMENT_CODE_CORRECTIONS = {
    "ACME": "ASME",
    "CAE": "SAE",
    "FED": "FEDERAL",
}
ALLOWED_CROSSREF_DOCUMENT_CODES = KNOWN_CROSSREF_DOCUMENT_CODES | set(DOCUMENT_CODE_CORRECTIONS.keys())
CROSSREF_DOC_CODE_PATTERN = re.compile(r"^[A-Z]{2,8}[0-9]?$")
CROSSREF_SPEC_VALUE_PATTERN = re.compile(r"[A-Z]{0,4}\d+(?:\.\d+)?[A-Z]?")
VALID_ELEMENT_SYMBOLS = {
    "H",
    "He",
    "Li",
    "Be",
    "B",
    "C",
    "N",
    "O",
    "F",
    "Ne",
    "Na",
    "Mg",
    "Al",
    "Si",
    "P",
    "S",
    "Cl",
    "Ar",
    "K",
    "Ca",
    "Sc",
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
    "Cu",
    "Zn",
    "Ga",
    "Ge",
    "As",
    "Se",
    "Br",
    "Kr",
    "Rb",
    "Sr",
    "Y",
    "Zr",
    "Nb",
    "Mo",
    "Tc",
    "Ru",
    "Rh",
    "Pd",
    "Ag",
    "Cd",
    "In",
    "Sn",
    "Sb",
    "Te",
    "I",
    "Xe",
    "Cs",
    "Ba",
    "La",
    "Ce",
    "Pr",
    "Nd",
    "Pm",
    "Sm",
    "Eu",
    "Gd",
    "Tb",
    "Dy",
    "Ho",
    "Er",
    "Tm",
    "Yb",
    "Lu",
    "Hf",
    "Ta",
    "W",
    "Re",
    "Os",
    "Ir",
    "Pt",
    "Au",
    "Hg",
    "Tl",
    "Pb",
    "Bi",
    "Po",
    "At",
    "Rn",
    "Fr",
    "Ra",
    "Ac",
    "Th",
    "Pa",
    "U",
    "Np",
    "Pu",
    "Am",
    "Cm",
    "Bk",
    "Cf",
    "Es",
    "Fm",
    "Md",
    "No",
    "Lr",
    "Rf",
    "Db",
    "Sg",
    "Bh",
    "Hs",
    "Mt",
    "Ds",
    "Rg",
    "Cn",
    "Nh",
    "Fl",
    "Mc",
    "Lv",
    "Ts",
    "Og",
}


class UnsSeriesDataNormalizer(Normalizer[list[RawRecord]]):
    def normalize(self, rows: list[RawRecord]) -> list[RawRecord]:
        normalized: list[RawRecord] = []
        for row in rows:
            new_row = dict(row)
            text = str(new_row.get("entry_text", ""))
            raw_lines = [str(x).strip() for x in new_row.get("entry_raw_lines", []) if str(x).strip()]

            replaced_by_codes: list[str] = []
            for m in REPLACED_BY_PATTERN.finditer(text):
                code = self._normalize_code(m.group(1), m.group(2))
                replaced_by_codes.append(code)

            new_row["replaced_by_codes"] = sorted(set(replaced_by_codes))
            new_row["is_replaced"] = bool(replaced_by_codes)

            marker = bool(new_row.get("inactive_boxed_marker"))
            page_note = bool(new_row.get("page_has_boxed_note"))
            new_row["inactive_boxed"] = marker and page_note

            table_description = self._join_lines(new_row.get("table_description_lines", []))
            table_composition = self._join_lines(new_row.get("table_chemical_composition_lines", []))
            table_cross_reference = self._join_lines(new_row.get("table_cross_reference_lines", []))

            if table_description or table_composition or table_cross_reference:
                cleaned_description = self._clean_description(table_description)
                cleaned_composition = self._clean_chemistry(table_composition)
                if not cleaned_description and table_composition:
                    # Some scanned table rows place description text at the start of the
                    # composition column; recover both fields from that blended text.
                    derived_desc_lines, derived_chem_lines, _ = self._split_sections([table_composition])
                    derived_description = self._clean_description(" ".join(derived_desc_lines).strip())
                    derived_composition = self._clean_chemistry(" ".join(derived_chem_lines).strip())
                    if self._is_plausible_description(derived_description):
                        cleaned_description = derived_description
                    if derived_composition:
                        cleaned_composition = derived_composition
                    if not cleaned_description:
                        suffix_description = self._extract_description_suffix(table_composition)
                        if self._is_plausible_description(suffix_description):
                            cleaned_description = suffix_description
                new_row["description"] = cleaned_description
                new_row["chemical_composition"] = cleaned_composition
                new_row["cross_reference_specifications"] = self._clean_specifications(table_cross_reference)
            else:
                desc_lines, chem_lines, spec_lines = self._split_sections(raw_lines)
                new_row["description"] = self._clean_description(" ".join(desc_lines).strip())
                new_row["chemical_composition"] = self._clean_chemistry(" ".join(chem_lines).strip())
                new_row["cross_reference_specifications"] = self._clean_specifications(
                    " ".join(spec_lines).strip()
                )
            new_row["cross_reference_specifications_structured"] = self._parse_cross_reference_specifications(
                str(new_row.get("cross_reference_specifications", ""))
            )
            new_row["cross_reference_specifications_check"] = self._validate_cross_reference_document_codes(
                new_row["cross_reference_specifications_structured"]
            )
            new_row["cross_reference_specifications_flags"] = self._extract_cross_reference_flags(
                str(new_row.get("cross_reference_specifications", ""))
            )
            new_row["chemical_composition_structured"] = self._parse_chemical_composition(
                str(new_row.get("chemical_composition", ""))
            )
            new_row["chemical_composition_symbol_check"] = self._validate_element_symbols(
                new_row["chemical_composition_structured"]
            )
            if self._is_pseudo_entry(new_row):
                continue
            normalized.append(new_row)
        return self._backfill_descriptions(normalized)

    def _backfill_descriptions(self, rows: list[RawRecord]) -> list[RawRecord]:
        groups: dict[tuple[str, int], list[RawRecord]] = {}
        for row in rows:
            token = str(row.get("series_token", ""))
            page = int(row.get("entry_pdf_page_start", 0))
            groups.setdefault((token, page), []).append(row)

        for _, group in groups.items():
            group.sort(key=lambda r: str(r.get("uns_code", "")))
            for i, row in enumerate(group):
                desc = str(row.get("description", "")).strip()
                if desc:
                    continue
                prev_desc = self._nearest_nonempty_desc(group, i, -1)
                next_desc = self._nearest_nonempty_desc(group, i, 1)
                filled = self._pick_backfill_description(prev_desc, next_desc)
                if filled:
                    row["description"] = filled
        return rows

    @staticmethod
    def _nearest_nonempty_desc(group: list[RawRecord], index: int, step: int) -> str:
        j = index + step
        while 0 <= j < len(group):
            candidate = str(group[j].get("description", "")).strip()
            if candidate:
                return candidate
            j += step
        return ""

    @staticmethod
    def _pick_backfill_description(prev_desc: str, next_desc: str) -> str:
        if prev_desc and next_desc:
            prev_head = " ".join(prev_desc.split()[:2]).lower()
            next_head = " ".join(next_desc.split()[:2]).lower()
            if prev_head == next_head:
                return prev_desc
            return ""
        if prev_desc and UnsSeriesDataNormalizer._is_conservative_fill(prev_desc):
            return prev_desc
        if next_desc and UnsSeriesDataNormalizer._is_conservative_fill(next_desc):
            return next_desc
        return ""

    @staticmethod
    def _is_conservative_fill(text: str) -> bool:
        lowered = text.lower()
        if "are no longer active" in lowered:
            return False
        words = text.split()
        if len(words) > 10:
            return False
        return True

    def _split_sections(self, raw_lines: list[str]) -> tuple[list[str], list[str], list[str]]:
        description: list[str] = []
        composition: list[str] = []
        references: list[str] = []
        chemistry_started = False

        for line in raw_lines:
            if not line:
                continue

            normalized = " ".join(line.split())
            line_without_specs, spec_fragments = self._extract_spec_fragments(normalized)
            references.extend(spec_fragments)

            working = line_without_specs.strip(" ,;:")
            if not working:
                continue

            chem_start = self._find_chem_start(working)
            if chem_start is not None:
                desc_part = working[:chem_start].strip(" ,;:")
                chem_part = working[chem_start:].strip()
                if desc_part:
                    description.append(desc_part)
                if chem_part:
                    composition.append(chem_part)
                    chemistry_started = True
                continue

            if chemistry_started and self._looks_like_chemistry_continuation(working):
                composition.append(working)
                continue

            spec_matches = SPEC_TOKEN_PATTERN.findall(working)
            if spec_matches and not CHEM_TOKEN_PATTERN.search(working):
                references.append(working)
                continue

            description.append(working)

        return description, composition, self._dedupe_keep_order(references)

    @staticmethod
    def _find_chem_start(line: str) -> int | None:
        starts: list[int] = []
        m1 = CHEM_START_ELEMENT_VALUE_PATTERN.search(line)
        if m1:
            starts.append(m1.start())
        m2 = CHEM_START_VALUE_ELEMENT_PATTERN.search(line)
        if m2:
            starts.append(m2.start())
        if not starts:
            return None
        return min(starts)

    @staticmethod
    def _extract_spec_fragments(line: str) -> tuple[str, list[str]]:
        fragments: list[str] = []

        def replace_and_collect(pattern: re.Pattern[str], text: str) -> str:
            def _repl(match: re.Match[str]) -> str:
                fragment = " ".join(match.group(0).split())
                fragments.append(fragment)
                return " "

            return pattern.sub(_repl, text)

        working = replace_and_collect(AA_SPEC_FRAGMENT_PATTERN, line)
        working = replace_and_collect(GENERIC_SPEC_FRAGMENT_PATTERN, working)
        working = " ".join(working.split())
        return working, UnsSeriesDataNormalizer._dedupe_keep_order(fragments)

    @staticmethod
    def _looks_like_chemistry_continuation(line: str) -> bool:
        lowered = line.lower()
        if any(token in lowered for token in (" max", " min", " rem", " nom", " total", " each", " balance")):
            return True
        if "other each" in lowered:
            return True
        if re.search(r"\d", line) and re.search(r"\b(?:[A-Z][a-z]?|AI|Ci)\b", line):
            return True
        if re.search(r"^\d", line):
            return True
        return False

    @staticmethod
    def _dedupe_keep_order(items: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for item in items:
            cleaned = item.strip()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            out.append(cleaned)
        return out

    @staticmethod
    def _join_lines(value: object) -> str:
        if not isinstance(value, list):
            return ""
        return " ".join(str(x).strip() for x in value if str(x).strip()).strip()

    @staticmethod
    def _clean_description(value: str) -> str:
        text = re.sub(r"\s+", " ", value).strip(" ,;:")
        text = text.replace("_", " ").replace("~", " ")
        text = re.sub(r"\s+", " ", text).strip(" ,;:")
        return text

    @staticmethod
    def _is_plausible_description(value: str) -> bool:
        text = value.strip()
        if not text:
            return False
        if not re.search(r"[A-Za-z]", text):
            return False
        if re.search(r"\d", text) and len(text.split()) <= 3:
            return False
        lowered = text.lower()
        if lowered in {"other", "nom", "max", "min"}:
            return False
        return True

    @staticmethod
    def _extract_description_suffix(value: str) -> str:
        text = " ".join(value.split())
        m = re.search(
            r"([A-Za-z][A-Za-z\-\s]{2,}(?:Alloy|Alloys|Solder|Steel|Steels|Bronze|Brass))\s*$",
            text,
            flags=re.IGNORECASE,
        )
        if not m:
            return ""
        return UnsSeriesDataNormalizer._clean_description(m.group(1))

    @staticmethod
    def _is_pseudo_entry(row: RawRecord) -> bool:
        desc = str(row.get("description", "")).strip()
        chem = row.get("chemical_composition_structured", [])
        specs = row.get("cross_reference_specifications_structured", [])
        is_replaced = bool(row.get("is_replaced", False))
        inactive_boxed = bool(row.get("inactive_boxed", False))
        if desc in {"", "-"} and not chem and not specs and not is_replaced and not inactive_boxed:
            return True
        return False

    @staticmethod
    def _clean_chemistry(value: str) -> str:
        text = value
        text = text.replace(" rnax", " max").replace(" Rnax", " max")
        text = re.sub(r"\bCi\b", "Si", text)
        text = re.sub(r"(\d)\s+(\d\.\d)", r"\1\2", text)
        text = re.sub(r"(\d\.\d)\s+(\d)", r"\1\2", text)
        text = re.sub(r"(\d\.\d{2})(\d\.\d{2}-\d\.\d{2})", r"\1 \2", text)
        text = re.sub(
            r"\bOther each (\d+(?:\.\d+)?) max\.? total (\d+(?:\.\d+)?) max\b",
            r"Other each \1 max Other total \2 max",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(r"\s+", " ", text).strip(" ,;:")
        return text

    @staticmethod
    def _clean_specifications(value: str) -> str:
        text = value
        text = re.sub(r"\bACTM\b", "ASTM", text)
        text = re.sub(r"\bASTM\s+8(\d{3})\b", r"ASTM B\1", text)
        text = re.sub(r"\bA(\d{3})\s+(\d)\b", r"A\1.\2", text)
        text = re.sub(r"\s+", " ", text).strip(" ,;:")
        # Drop footnote-only artifacts captured from table OCR.
        lowered = text.lower().strip()
        compact = re.sub(r"[^a-z]", "", lowered)
        if compact in {"boxed", "boxedof", "boxedfor", "boxedentriesarenolongeractive"}:
            return ""
        return text

    def _parse_cross_reference_specifications(self, value: str) -> list[dict[str, object]]:
        text = value.strip()
        if not text:
            return []

        raw_tokens = text.split()
        out: list[dict[str, object]] = []
        current_code: str | None = None
        last_spec_index_for_code: dict[str, int] = {}
        i = 0

        while i < len(raw_tokens):
            raw_token = raw_tokens[i]
            token = self._normalize_token(raw_token)
            if not token:
                i += 1
                continue
            cleaned = token.strip(".,;:")
            if not cleaned:
                i += 1
                continue

            upper = cleaned.strip("()[]{}").upper()
            if (
                CROSSREF_DOC_CODE_PATTERN.fullmatch(upper)
                and upper in ALLOWED_CROSSREF_DOCUMENT_CODES
                and not any(ch.isdigit() for ch in upper[1:])
            ):
                current_code = self._normalize_document_code(upper)
                i += 1
                continue

            # AC1-like code token should switch current document code.
            if (
                CROSSREF_DOC_CODE_PATTERN.fullmatch(upper)
                and upper in ALLOWED_CROSSREF_DOCUMENT_CODES
                and any(ch.isdigit() for ch in upper)
            ):
                current_code = self._normalize_document_code(upper)
                i += 1
                continue

            if current_code is None:
                i += 1
                continue

            # Attach parenthesized context to the previous spec for current code,
            # e.g. A29 (5132) -> "A29 (5132)" instead of a duplicate standalone "5132" record.
            raw_clean = raw_token.strip().strip(",;:")
            parenthesized = re.fullmatch(r"\(([^)]+)\)", raw_clean)
            if parenthesized:
                inner = parenthesized.group(1).strip()
                if inner and current_code in last_spec_index_for_code:
                    idx = last_spec_index_for_code[current_code]
                    prev = str(out[idx].get("specification", ""))
                    if f"({inner})" not in prev:
                        out[idx]["specification"] = f"{prev} ({inner})".strip()
                i += 1
                continue

            specs = CROSSREF_SPEC_VALUE_PATTERN.findall(cleaned.upper())
            if not specs and current_code in last_spec_index_for_code:
                context, consumed = self._extract_parenthetical_context(raw_tokens, i)
                if context:
                    idx = last_spec_index_for_code[current_code]
                    prev = str(out[idx].get("specification", ""))
                    if f"({context})" not in prev:
                        out[idx]["specification"] = f"{prev} ({context})".strip()
                    i += consumed
                    continue

            for spec in specs:
                spec = self._normalize_specification_token(spec, current_code)
                # Skip obvious OCR debris as standalone specs.
                if spec.isdigit() and len(spec) <= 2:
                    continue
                out.append(
                    {
                        "document_code": current_code,
                        "specification": spec,
                    }
                )
                last_spec_index_for_code[current_code] = len(out) - 1

            i += 1

        return self._propagate_missing_spec_context(out)

    @staticmethod
    def _normalize_specification_token(spec: str, document_code: str) -> str:
        value = spec.upper()
        # OCR often confuses I/l with 1 in leading alpha+digit specs (JI397 -> J1397, Bl69 -> B169).
        value = re.sub(r"^([A-Z])[IL](\d)", r"\g<1>1\g<2>", value)
        # OCR often confuses O with zero inside numeric regions.
        value = re.sub(r"(?<=\d)O(?=\d)", "0", value)
        if document_code in {"SAE", "AISI"}:
            value = re.sub(r"^JI(\d{3,4})$", r"J1\1", value)
        return value

    @staticmethod
    def _extract_parenthetical_context(tokens: list[str], start: int) -> tuple[str | None, int]:
        token = tokens[start].strip(",;:")
        # Direct (5132) style token.
        direct = re.fullmatch(r"\((\d{3,5})\)", token)
        if direct:
            return direct.group(1), 1

        if start + 1 >= len(tokens):
            return None, 1

        next_token = tokens[start + 1].strip(",;:")
        first = re.sub(r"[^\d]", "", token)
        second = re.sub(r"[^\d]", "", next_token)
        if len(first) == 2 and len(second) == 2:
            # If OCR split/reordered parentheses as "32) (51", reconstruct as 5132.
            if token.endswith(")") and next_token.startswith("("):
                return f"{second}{first}", 2
            # Standard left-to-right split fallback.
            if token.startswith("(") or next_token.endswith(")"):
                return f"{first}{second}", 2
        return None, 1

    @staticmethod
    def _propagate_missing_spec_context(items: list[dict[str, object]]) -> list[dict[str, object]]:
        context_by_code: dict[str, str] = {}
        for item in items:
            code = str(item.get("document_code", "")).strip().upper()
            spec = str(item.get("specification", "")).strip()
            m = re.search(r"\((\d{3,5})\)\s*$", spec)
            if code and m and code not in context_by_code:
                context_by_code[code] = m.group(1)

        for item in items:
            code = str(item.get("document_code", "")).strip().upper()
            spec = str(item.get("specification", "")).strip()
            if not code or not spec or "(" in spec:
                continue
            context = context_by_code.get(code)
            if context:
                item["specification"] = f"{spec} ({context})"
        return items

    @staticmethod
    def _validate_cross_reference_document_codes(
        items: list[dict[str, object]],
    ) -> dict[str, object]:
        unknown: list[str] = []
        seen: set[str] = set()
        for item in items:
            code = str(item.get("document_code", "")).strip().upper()
            if not code:
                continue
            if code in KNOWN_CROSSREF_DOCUMENT_CODES:
                continue
            if code not in seen:
                seen.add(code)
                unknown.append(code)
        return {
            "all_document_codes_known": len(unknown) == 0,
            "unknown_document_codes": unknown,
        }

    @staticmethod
    def _extract_cross_reference_flags(value: str) -> dict[str, object]:
        lowered = value.lower()
        has_boxed = "boxed" in lowered
        flags: dict[str, object] = {"has_boxed_marker": has_boxed}
        if has_boxed:
            flags["boxed_context"] = value
        return flags

    @staticmethod
    def _normalize_document_code(code: str) -> str:
        return DOCUMENT_CODE_CORRECTIONS.get(code, code)

    def _parse_chemical_composition(self, composition: str) -> list[dict[str, object]]:
        text = composition.strip()
        if not text:
            return []

        tokens = text.split()
        out: list[dict[str, object]] = []
        pending_symbols: list[tuple[str, str | None]] = []
        i = 0
        while i < len(tokens):
            token = self._normalize_token(tokens[i])
            if not token:
                i += 1
                continue

            if token.lower() == "other":
                item, next_i = self._parse_other(tokens, i)
                if item:
                    out.append(item)
                i = next_i
                continue

            # If we have pending element symbols that were split from their values
            # across wrapped lines, consume the upcoming numeric/range token here.
            range_for_pending = self._parse_range(token)
            number_for_pending = self._parse_number(token)
            if pending_symbols and (range_for_pending is not None or number_for_pending is not None):
                symbol, symbol_note = pending_symbols.pop(0)
                if range_for_pending is not None:
                    item = {
                        "element_symbol": symbol,
                        "min_percent": range_for_pending[0],
                        "max_percent": range_for_pending[1],
                        "value_type": "range",
                    }
                else:
                    qualifier = ""
                    if i + 1 < len(tokens):
                        nxt = self._normalize_token(tokens[i + 1]).lower().rstrip(".,;:")
                        if nxt in {"max", "min"}:
                            qualifier = nxt
                            i += 1
                    if qualifier == "max":
                        item = {"element_symbol": symbol, "max_percent": number_for_pending, "value_type": "max"}
                    elif qualifier == "min":
                        item = {"element_symbol": symbol, "min_percent": number_for_pending, "value_type": "min"}
                    else:
                        item = {"element_symbol": symbol, "percent": number_for_pending, "value_type": "exact"}

                if symbol_note:
                    item["note"] = symbol_note
                out.append(item)
                i += 1
                continue

            if not ELEMENT_TOKEN_PATTERN.fullmatch(token):
                i += 1
                continue

            symbol, symbol_note = self._normalize_element_symbol(token)
            i += 1
            if i >= len(tokens):
                break

            value_token = self._normalize_token(tokens[i]).lower()
            if value_token in {"rem", "remainder", "balance", "bal"}:
                item: dict[str, object] = {"element_symbol": symbol, "value_type": "remainder"}
                if symbol_note:
                    item["note"] = symbol_note
                out.append(item)
                i += 1
                continue

            value_raw = self._normalize_token(tokens[i])
            value_range = self._parse_range(value_raw)
            if value_range is not None:
                item = {
                    "element_symbol": symbol,
                    "min_percent": value_range[0],
                    "max_percent": value_range[1],
                    "value_type": "range",
                }
                if symbol_note:
                    item["note"] = symbol_note
                out.append(item)
                i += 1
                continue

            value_num = self._parse_number(value_raw)
            if value_num is None:
                # Defer this symbol; a wrapped table line may place the value later.
                pending_symbols.append((symbol, symbol_note))
                continue

            qualifier = ""
            if i + 1 < len(tokens):
                nxt = self._normalize_token(tokens[i + 1]).lower().rstrip(".,;:")
                if nxt in {"max", "min"}:
                    qualifier = nxt
                    i += 1

            if qualifier == "max":
                item = {"element_symbol": symbol, "max_percent": value_num, "value_type": "max"}
            elif qualifier == "min":
                item = {"element_symbol": symbol, "min_percent": value_num, "value_type": "min"}
            else:
                item = {"element_symbol": symbol, "percent": value_num, "value_type": "exact"}

            if symbol_note:
                item["note"] = symbol_note
            out.append(item)
            i += 1

        return self._sanitize_composition_items(out)

    def _sanitize_composition_items(self, items: list[dict[str, object]]) -> list[dict[str, object]]:
        cleaned: list[dict[str, object]] = []
        for item in items:
            symbol = str(item.get("element_symbol", "")).strip()
            if not symbol or symbol == "Other":
                cleaned.append(item)
                continue
            if symbol in VALID_ELEMENT_SYMBOLS:
                cleaned.append(item)
                continue
            # Drop obvious non-element OCR leakage (e.g. Of/By/To) from chemistry parsing.
            if re.fullmatch(r"[A-Za-z]{1,2}", symbol):
                continue
            cleaned.append(item)
        return cleaned

    @staticmethod
    def _validate_element_symbols(items: list[dict[str, object]]) -> dict[str, object]:
        unknown: list[str] = []
        seen: set[str] = set()
        for item in items:
            symbol = str(item.get("element_symbol", "")).strip()
            if not symbol or symbol == "Other":
                continue
            if symbol in VALID_ELEMENT_SYMBOLS:
                continue
            if symbol not in seen:
                seen.add(symbol)
                unknown.append(symbol)
        return {
            "all_symbols_valid": len(unknown) == 0,
            "unknown_symbols": unknown,
        }

    def _parse_other(self, tokens: list[str], start: int) -> tuple[dict[str, object] | None, int]:
        note: str | None = None
        i = start + 1

        if i < len(tokens):
            tok = self._normalize_token(tokens[i]).lower().rstrip(".,;:")
            if tok in {"each", "total"}:
                note = tok
                i += 1

        value: float | None = None
        qualifier = ""
        while i < len(tokens):
            tok = self._normalize_token(tokens[i]).lower().rstrip(".,;:")
            if tok in {"each", "total"} and note is None:
                note = tok
                i += 1
                continue
            parsed = self._parse_number(tok)
            if parsed is not None:
                value = parsed
                i += 1
                if i < len(tokens):
                    q = self._normalize_token(tokens[i]).lower().rstrip(".,;:")
                    if q in {"max", "min"}:
                        qualifier = q
                        i += 1
                break
            if tok in {"max", "min"}:
                qualifier = tok
                i += 1
                continue
            if ELEMENT_TOKEN_PATTERN.fullmatch(tok) and tok.lower() != "other":
                break
            i += 1

        if value is None:
            return None, i

        if qualifier == "min":
            item: dict[str, object] = {"element_symbol": "Other", "min_percent": value, "value_type": "min"}
        else:
            item = {"element_symbol": "Other", "max_percent": value, "value_type": "max"}

        if note:
            item["note"] = note
        return item, i

    @staticmethod
    def _normalize_element_symbol(raw: str) -> tuple[str, str | None]:
        up = raw.upper()
        if up in ELEMENT_CORRECTIONS:
            symbol, note = ELEMENT_CORRECTIONS[up]
            return symbol, note
        if raw.lower() == "other":
            return "Other", None
        if len(raw) == 1:
            return raw.upper(), None
        return raw[0].upper() + raw[1:].lower(), None

    @staticmethod
    def _normalize_token(token: str) -> str:
        cleaned = token.strip().strip(",;:()[]{}")
        cleaned = cleaned.replace("rnax", "max").replace("Rnax", "max")
        cleaned = cleaned.replace("O.", "0.").replace(".O", ".0")
        return cleaned

    @staticmethod
    def _parse_number(token: str) -> float | None:
        cleaned = token.strip().rstrip(".,;:")
        cleaned = cleaned.replace("O", "0").replace("l", "1").replace("I", "1")
        cleaned = cleaned.replace(".0.", "0.")
        if cleaned.startswith("."):
            cleaned = f"0{cleaned}"
        if not NUMERIC_PATTERN.fullmatch(cleaned):
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def _parse_range(token: str) -> tuple[float, float] | None:
        cleaned = token.strip().rstrip(".,;:")
        cleaned = cleaned.replace("O", "0").replace("l", "1").replace("I", "1")
        cleaned = cleaned.replace("--", "-")
        m = RANGE_PATTERN.fullmatch(cleaned)
        if not m:
            return None
        try:
            return float(m.group(1)), float(m.group(2))
        except ValueError:
            return None

    @staticmethod
    def _normalize_code(prefix: str, digits: str) -> str:
        cleaned = digits.upper().replace("O", "0").replace("I", "1").replace("L", "1")
        cleaned = re.sub(r"[^0-9]", "", cleaned)
        cleaned = cleaned[:5].ljust(5, "0")
        return f"{prefix.upper()}{cleaned}"
