from __future__ import annotations

from material_ingestion.matchers.base import Matcher
from material_ingestion.sources.base import RawRecord


class RowDedupeMatcher(Matcher[list[RawRecord]]):
    def __init__(self, key_fields: list[str]):
        self.key_fields = key_fields

    def match(self, rows: list[RawRecord]) -> list[RawRecord]:
        seen: set[tuple[str, ...]] = set()
        deduped: list[RawRecord] = []
        for row in rows:
            key = tuple(str(row.get(field, "")) for field in self.key_fields)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(row)
        return deduped
