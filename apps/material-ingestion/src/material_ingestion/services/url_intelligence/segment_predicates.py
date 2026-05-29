from __future__ import annotations

import re

from .models import SegmentKind

# Explicit ISO 639-1 allowlist. Short route tokens that happen to be 2 chars
# (ci, ed, cp, ec, ap, us, eu, uk, ...) are intentionally excluded.
_LANGUAGE_CODES: frozenset[str] = frozenset({
    "en", "de", "fr", "es", "it", "pt", "nl", "pl", "cs", "sk",
    "hu", "ro", "hr", "sl", "sr", "bg", "ru", "tr", "ar", "zh",
    "ja", "ko", "th", "vi", "id", "ms", "fi", "sv", "da", "nb",
    "no", "el", "he", "fa", "hi", "bn",
})

# Locale pattern: en-US, en_US, zh-CN, fr-FR, de-DE …
_LOCALE_RE = re.compile(r"^[a-z]{2}[-_][A-Za-z]{2,4}$")

_MARKET_REGION_TOKENS: frozenset[str] = frozenset({
    "global", "emea", "apac", "latam", "amer", "row",
    "worldwide", "international", "ww",
})

_ASSET_EXTENSIONS: frozenset[str] = frozenset({
    ".js", ".css", ".ts", ".map",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
    ".woff", ".woff2", ".ttf", ".eot",
    ".json", ".xml",
})

_DOCUMENT_EXTENSIONS: frozenset[str] = frozenset({
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".ppt", ".pptx", ".odt", ".ods", ".odp",
})

# Substrings (case-insensitive) that promote a document file to technical.
# Checked against the full decoded filename.
_TECHNICAL_DOC_TOKENS: tuple[str, ...] = (
    "tds", "sds", "msds", "pds",
    "datasheet", "data-sheet", "data_sheet",
    "technical-data", "technical_data",
    "safety-data-sheet", "safety_data_sheet",
    "product-data-sheet", "product_data_sheet",
    "safety data sheet", "technical data sheet",
    "product data sheet",
)

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

_NUMERIC_ID_RE = re.compile(r"^\d{3,}$")

_DATE_RE = re.compile(
    r"^("
    r"\d{4}[-_/]\d{2}[-_/]\d{2}"                          # 2023-05-01 / 2023_05_01
    r"|"
    r"(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])"  # plausible YYYYMMDD
    r")$"
)

# Long IDs: 12+ alphanumeric chars, no separators.  The additional digit/upper
# checks below prevent long lowercase words from being mis-classified.
_LONG_ID_CHARS_RE = re.compile(r"^[A-Za-z0-9]{12,}$")


def _file_ext(segment: str) -> str:
    dot = segment.rfind(".")
    if dot > 0:
        return segment[dot:].lower()
    return ""


def _is_technical_document_file(segment: str) -> bool:
    lower = segment.lower()
    return any(tok in lower for tok in _TECHNICAL_DOC_TOKENS)


def classify_segment(segment: str, position: int = 0, total_segments: int = 1) -> SegmentKind:
    """Classify one decoded URL path segment into a SegmentKind.

    position and total_segments are accepted for future positional heuristics
    but the current implementation is position-independent for robustness.
    """
    if not segment:
        return SegmentKind.LITERAL

    ext = _file_ext(segment)

    if ext in _DOCUMENT_EXTENSIONS:
        if _is_technical_document_file(segment):
            return SegmentKind.TECHNICAL_DOCUMENT_FILE
        return SegmentKind.DOCUMENT_FILE

    if ext in _ASSET_EXTENSIONS:
        return SegmentKind.ASSET_FILE

    lower = segment.lower()

    if _UUID_RE.match(segment):
        return SegmentKind.UUID

    # Date check before numeric so 20230501 is DATE_LIKE, not NUMERIC_ID
    if _DATE_RE.match(segment):
        return SegmentKind.DATE_LIKE

    if _NUMERIC_ID_RE.match(segment):
        return SegmentKind.NUMERIC_ID

    # Language: strict allowlist only; locale pattern (en-US / en_US)
    if lower in _LANGUAGE_CODES:
        return SegmentKind.LANGUAGE

    if _LOCALE_RE.match(segment):
        lang_part = re.split(r"[-_]", segment.lower())[0]
        if lang_part in _LANGUAGE_CODES:
            return SegmentKind.LANGUAGE

    if lower in _MARKET_REGION_TOKENS:
        return SegmentKind.MARKET_OR_REGION

    # Long alphanumeric IDs (Salesforce-style, hex tokens, etc.)
    if _LONG_ID_CHARS_RE.match(segment):
        has_digit = any(c.isdigit() for c in segment)
        has_upper = any(c.isupper() for c in segment)
        if has_digit and (has_upper or len(segment) >= 16):
            return SegmentKind.LONG_ID

    # Slug / code-slug: segments with hyphens or underscores
    sep = "-" if "-" in segment else ("_" if "_" in segment else None)
    if sep:
        parts = segment.split(sep)
        min_part = min(len(p) for p in parts) if parts else 0
        if min_part >= 3 and len(segment) >= 9:
            has_digit = any(c.isdigit() for c in segment)
            has_upper = any(c.isupper() for c in segment)
            if has_digit or has_upper:
                return SegmentKind.CODE_SLUG
            return SegmentKind.SLUG

    return SegmentKind.LITERAL
