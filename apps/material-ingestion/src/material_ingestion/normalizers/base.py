from __future__ import annotations

from abc import ABC, abstractmethod

from material_ingestion.types import MaterialRecord


class Normalizer(ABC):
    @abstractmethod
    def normalize(self, record: MaterialRecord) -> MaterialRecord:
        """Normalize a material record into canonical formatting."""

