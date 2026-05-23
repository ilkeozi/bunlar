from __future__ import annotations

from material_ingestion.normalizers.base import Normalizer
from material_ingestion.sources.base import RawRecord


class CompositeRowNormalizer(Normalizer[list[RawRecord]]):
    def __init__(self, normalizers: list[Normalizer[list[RawRecord]]]):
        self.normalizers = normalizers

    def normalize(self, rows: list[RawRecord]) -> list[RawRecord]:
        normalized = rows
        for normalizer in self.normalizers:
            normalized = normalizer.normalize(normalized)
        return normalized
