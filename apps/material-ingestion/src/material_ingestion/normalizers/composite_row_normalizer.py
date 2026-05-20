from __future__ import annotations

from material_ingestion.sources.base import RawRecord


class CompositeRowNormalizer:
    def __init__(self, normalizers: list[object]):
        self.normalizers = normalizers

    def normalize_rows(self, rows: list[RawRecord]) -> list[RawRecord]:
        normalized = rows
        for normalizer in self.normalizers:
            normalized = normalizer.normalize_rows(normalized)
        return normalized

