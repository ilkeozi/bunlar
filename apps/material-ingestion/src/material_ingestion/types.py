from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MaterialRecord:
    source: str
    material_id: str
    name: str
    aliases: list[str] = field(default_factory=list)
    composition: dict[str, Any] = field(default_factory=dict)
    properties: dict[str, Any] = field(default_factory=dict)
    standards: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

