from __future__ import annotations

from abc import ABC, abstractmethod

from material_ingestion.types import MaterialRecord


class Matcher(ABC):
    @abstractmethod
    def match(self, record: MaterialRecord) -> MaterialRecord:
        """Attach matching metadata (dedupe/cross-source identity)."""

