from __future__ import annotations

from abc import ABC, abstractmethod

from material_ingestion.sources.base import RawRecord
from material_ingestion.types import MaterialRecord


class Extractor(ABC):
    @abstractmethod
    def extract(self, source: str, raw: RawRecord) -> MaterialRecord:
        """Map a source-specific raw record into the shared schema."""

