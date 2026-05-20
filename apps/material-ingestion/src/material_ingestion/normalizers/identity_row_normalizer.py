from __future__ import annotations

from material_ingestion.sources.base import RawRecord


class IdentityRowNormalizer:
    def normalize_rows(self, rows: list[RawRecord]) -> list[RawRecord]:
        return rows

