from __future__ import annotations

from material_ingestion.normalizers.base import Normalizer
from material_ingestion.types import MaterialRecord


class UnsSimpleMaterialNormalizer(Normalizer[MaterialRecord]):
    def normalize(self, record: MaterialRecord) -> MaterialRecord:
        record.name = " ".join(record.name.strip().split())
        record.material_id = record.material_id.strip().upper()
        record.standards = sorted(set(record.standards))
        return record
