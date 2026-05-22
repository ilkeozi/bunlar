from __future__ import annotations

from typing import Iterable

from material_ingestion.exporters.base import Exporter
from material_ingestion.matchers.base import Matcher
from material_ingestion.normalizers.base import Normalizer
from material_ingestion.sources.base import RawRecord, SourceAdapter


class RawExtractor:
    def extract_rows(self, raw_records: Iterable[RawRecord]) -> list[RawRecord]:
        raise NotImplementedError


class RawIngestionPipeline:
    """Generic pipeline for table-like extraction flows."""

    def __init__(
        self,
        source: SourceAdapter,
        extractor: RawExtractor,
        normalizer: Normalizer[list[RawRecord]],
        matcher: Matcher[list[RawRecord]],
        exporter: Exporter[list[RawRecord], None],
    ):
        self.source = source
        self.extractor = extractor
        self.normalizer = normalizer
        self.matcher = matcher
        self.exporter = exporter

    def run(self) -> list[RawRecord]:
        raw_records = list(self.source.fetch())
        rows = self.extractor.extract_rows(raw_records)
        rows = self.normalizer.normalize(rows)
        rows = self.matcher.match(rows)
        self.exporter.export(rows)
        return rows
