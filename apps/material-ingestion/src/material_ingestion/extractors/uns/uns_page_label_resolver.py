from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


LABEL_PATTERN = re.compile(r"(?i)^([ivxlcdm]{1,8}|\d{1,4})$")


@dataclass(slots=True)
class PageLabelResolution:
    target_label: str
    target_pdf_page: int | None
    page_resolution: str


class PageLabelResolver:
    def __init__(
        self,
        footer_map: dict[str, list[int]],
        pypdf_map: dict[str, list[int]],
        allow_pypdf_fallback: bool = False,
    ):
        self.footer_map = footer_map
        self.pypdf_map = pypdf_map
        self.allow_pypdf_fallback = allow_pypdf_fallback

    @classmethod
    def from_pdf(cls, pdf_path: Path, allow_pypdf_fallback: bool = False) -> "PageLabelResolver":
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        footer_map: dict[str, list[int]] = {}
        pypdf_map: dict[str, list[int]] = {}

        for idx, page in enumerate(reader.pages):
            pdf_page = idx + 1
            text = page.extract_text() or ""
            footer_label = _extract_footer_label(text)
            if footer_label:
                footer_map.setdefault(_normalize_label(footer_label), []).append(pdf_page)

        for idx, label in enumerate(getattr(reader, "page_labels", []) or []):
            normalized = _normalize_label(str(label))
            if normalized:
                pypdf_map.setdefault(normalized, []).append(idx + 1)

        return cls(
            footer_map=footer_map,
            pypdf_map=pypdf_map,
            allow_pypdf_fallback=allow_pypdf_fallback,
        )

    def resolve(self, target_label: str | int) -> PageLabelResolution:
        label = _normalize_label(str(target_label))

        footer_pages = self.footer_map.get(label, [])
        if len(footer_pages) == 1:
            return PageLabelResolution(label, footer_pages[0], "exact-footer")
        if len(footer_pages) > 1:
            return PageLabelResolution(label, footer_pages[0], "ambiguous-footer")

        if self.allow_pypdf_fallback:
            pypdf_pages = self.pypdf_map.get(label, [])
            if len(pypdf_pages) == 1:
                return PageLabelResolution(label, pypdf_pages[0], "fallback-pypdf-label")
            if len(pypdf_pages) > 1:
                return PageLabelResolution(label, pypdf_pages[0], "ambiguous-pypdf-label")

        return PageLabelResolution(label, None, "unresolved")


def _extract_footer_label(text: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None

    tail = lines[-20:]
    candidates: list[str] = []
    for line in tail:
        if LABEL_PATTERN.fullmatch(line):
            candidates.append(line)

    if not candidates:
        return None

    # Prefer the last multi-character/number candidate to avoid OCR artifacts like lone "I".
    preferred = [c for c in candidates if not (len(c) == 1 and c.upper() == "I")]
    if preferred:
        return preferred[-1]
    return candidates[-1]


def _normalize_label(label: str) -> str:
    value = label.strip()
    if not value:
        return ""
    if value.isdigit():
        return str(int(value))
    return value.lower()
