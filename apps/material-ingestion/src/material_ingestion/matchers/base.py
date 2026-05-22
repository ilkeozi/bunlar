from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Matcher(ABC, Generic[T]):
    @abstractmethod
    def match(self, value: T) -> T:
        """Apply matching logic and return transformed value."""
