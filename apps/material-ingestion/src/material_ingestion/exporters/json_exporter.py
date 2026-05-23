from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import is_dataclass
from typing import Any

from material_ingestion.exporters.base import Exporter
from material_ingestion.sources.base import RawRecord
from material_ingestion.types import MaterialRecord


class JsonExporter(Exporter[list[RawRecord] | list[MaterialRecord], str]):
    def __init__(self, pretty: bool = True):
        self.pretty = pretty

    def export(self, records: list[RawRecord] | list[MaterialRecord]) -> str:
        payload = [self._to_jsonable(record) for record in records]
        if self.pretty:
            return json.dumps(payload, indent=2, sort_keys=True)
        return json.dumps(payload)

    @staticmethod
    def _to_jsonable(record: RawRecord | MaterialRecord) -> dict[str, Any]:
        if is_dataclass(record):
            return asdict(record)
        return dict(record)
