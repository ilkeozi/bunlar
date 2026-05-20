from __future__ import annotations

from material_ingestion.extractors.page_label_resolver import PageLabelResolver
from material_ingestion.sources.base import RawRecord


class PageReferenceRowNormalizer:
    def __init__(self, resolver: PageLabelResolver):
        self.resolver = resolver

    def normalize_rows(self, rows: list[RawRecord]) -> list[RawRecord]:
        normalized: list[RawRecord] = []
        for row in rows:
            new_row = dict(row)
            if "target_label" not in new_row and "target_page" in new_row:
                new_row["target_label"] = str(new_row["target_page"])

            target_label = str(new_row.get("target_label", "")).strip()
            if target_label:
                resolved = self.resolver.resolve(target_label)
                new_row["target_label"] = resolved.target_label
                new_row["target_pdf_page"] = resolved.target_pdf_page
                new_row["page_resolution"] = resolved.page_resolution

            normalized.append(new_row)
        return normalized

