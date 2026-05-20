from __future__ import annotations

import csv
import json
from pathlib import Path

from material_ingestion.sources.base import RawRecord


class RowFileExporter:
    def __init__(self, output_path: Path, fieldnames: list[str]):
        self.output_path = output_path
        self.fieldnames = fieldnames

    def export_rows(self, rows: list[RawRecord]) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        projected_rows = [self._project_row(row) for row in rows]
        if self.output_path.suffix.lower() == ".csv":
            with self.output_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()
                for row in projected_rows:
                    writer.writerow(row)
            return

        self.output_path.write_text(
            json.dumps(projected_rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    def _project_row(self, row: RawRecord) -> RawRecord:
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
            projected[key] = value
        return projected
