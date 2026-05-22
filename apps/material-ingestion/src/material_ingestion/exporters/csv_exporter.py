from __future__ import annotations

import csv
from dataclasses import asdict
from dataclasses import is_dataclass
import json
from pathlib import Path
from typing import Any

from material_ingestion.exporters.base import Exporter
from material_ingestion.sources.base import RawRecord
from material_ingestion.types import MaterialRecord


class CsvExporter(Exporter[list[RawRecord] | list[MaterialRecord], None]):
    def __init__(self, output_path: Path, fieldnames: list[str]):
        self.output_path = output_path
        self.fieldnames = fieldnames

    def export(self, rows: list[RawRecord] | list[MaterialRecord]) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        projected_rows = [self._project_row(self._to_record_dict(row)) for row in rows]
        with self.output_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
            for row in projected_rows:
                writer.writerow(row)

    @staticmethod
    def _to_record_dict(row: RawRecord | MaterialRecord) -> RawRecord:
        if is_dataclass(row):
            return asdict(row)
        return dict(row)

    def _project_row(self, row: RawRecord) -> dict[str, str | int | float | bool]:
        projected: RawRecord = {}
        for key in self.fieldnames:
            if key not in row:
                continue
            value = row[key]
            if value is None:
                continue
            if value == "":
                continue
            if isinstance(value, list) and not value:
                continue
            projected[key] = self._to_csv_cell(value)
        return projected

    @staticmethod
    def _to_csv_cell(value: Any) -> str | int | float | bool:
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value, ensure_ascii=False)
        return value
