from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable


RawRecord = dict[str, Any]


class SourceAdapter(ABC):
    source_name: str

    @abstractmethod
    def fetch(self) -> Iterable[RawRecord]:
        """Return raw records from the source."""

