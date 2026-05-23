from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TIn = TypeVar("TIn")
TOut = TypeVar("TOut")


class Exporter(ABC, Generic[TIn, TOut]):
    @abstractmethod
    def export(self, value: TIn) -> TOut:
        """Export input value to target output."""
