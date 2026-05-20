from __future__ import annotations

import json
from dataclasses import asdict

from material_ingestion.exporters.base import Exporter
from material_ingestion.types import MaterialRecord


class JsonExporter(Exporter):
    def __init__(self, pretty: bool = True):
        self.pretty = pretty

    def export(self, records: list[MaterialRecord]) -> str:
        payload = [asdict(record) for record in records]
        if self.pretty:
            return json.dumps(payload, indent=2, sort_keys=True)
        return json.dumps(payload)

