from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from material_ingestion.extractors.uns_pdf_extractor import UnsPdfExtractor
from material_ingestion.sources.base import RawRecord, SourceAdapter


class UnsSourceAdapter(SourceAdapter):
    source_name = "uns"

    def __init__(self, input_path: str | None = None):
        self.input_path = Path(input_path) if input_path else None

    def fetch(self) -> Iterable[RawRecord]:
        if self.input_path is None:
            return self._sample_records()

        if self.input_path.suffix.lower() == ".pdf":
            extractor = UnsPdfExtractor()
            return extractor.extract_raw_records(self.input_path)

        with self.input_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("UNS input JSON must be a list of records.")

        return data

    @staticmethod
    def _sample_records() -> list[RawRecord]:
        return [
            {
                "uns": "G10200",
                "name": "Carbon Steel 1020",
                "composition": {"C": "0.17-0.23%", "Mn": "0.30-0.60%"},
                "properties": {"yield_strength_mpa": 350},
                "standards": ["UNS G10200"],
            }
        ]
