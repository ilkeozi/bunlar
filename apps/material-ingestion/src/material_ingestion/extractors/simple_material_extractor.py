from __future__ import annotations

from material_ingestion.extractors.base import Extractor
from material_ingestion.sources.base import RawRecord
from material_ingestion.types import MaterialRecord


class SimpleMaterialExtractor(Extractor):
    def extract(self, source: str, raw: RawRecord) -> MaterialRecord:
        material_id = str(raw.get("uns") or raw.get("id") or raw.get("material_id") or "")
        name = str(raw.get("name") or material_id)

        return MaterialRecord(
            source=source,
            material_id=material_id,
            name=name,
            aliases=list(raw.get("aliases", [])),
            composition=dict(raw.get("composition", {})),
            properties=dict(raw.get("properties", {})),
            standards=list(raw.get("standards", [])),
            metadata=dict(raw.get("metadata", {})),
        )

