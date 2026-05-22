from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Normalizer(ABC, Generic[T]):
    @abstractmethod
    def normalize(self, value: T) -> T:
        """Normalize input into canonical formatting."""
