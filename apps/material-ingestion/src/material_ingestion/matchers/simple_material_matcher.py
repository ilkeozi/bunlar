from __future__ import annotations

from material_ingestion.matchers.base import Matcher
from material_ingestion.types import MaterialRecord


class SimpleMaterialMatcher(Matcher):
    def match(self, record: MaterialRecord) -> MaterialRecord:
        # Initial key for future cross-source matching.
        record.metadata["match_key"] = f"{record.source}:{record.material_id}"
        return record

