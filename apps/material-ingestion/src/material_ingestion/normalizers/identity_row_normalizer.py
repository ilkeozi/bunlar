from __future__ import annotations

from material_ingestion.normalizers.base import Normalizer
from material_ingestion.sources.base import RawRecord


class IdentityRowNormalizer(Normalizer[list[RawRecord]]):
    def normalize(self, rows: list[RawRecord]) -> list[RawRecord]:
        return rows
