from __future__ import annotations

from abc import ABC, abstractmethod

from material_ingestion.types import MaterialRecord


class Exporter(ABC):
    @abstractmethod
    def export(self, records: list[MaterialRecord]) -> str:
        """Serialize records into an output string."""

