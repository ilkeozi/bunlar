from __future__ import annotations

from typing import Iterable

from material_ingestion.sources.base import RawRecord, SourceAdapter


class RowExtractor:
    def extract_rows(self, raw_records: Iterable[RawRecord]) -> list[RawRecord]:
        raise NotImplementedError


class RowNormalizer:
    def normalize_rows(self, rows: list[RawRecord]) -> list[RawRecord]:
        raise NotImplementedError


class RowMatcher:
    def match_rows(self, rows: list[RawRecord]) -> list[RawRecord]:
        raise NotImplementedError


class RowExporter:
    def export_rows(self, rows: list[RawRecord]) -> None:
        raise NotImplementedError


class RowIngestionPipeline:
    """Generic pipeline for table-like extraction flows."""

    def __init__(
        self,
        source: SourceAdapter,
        extractor: RowExtractor,
        normalizer: RowNormalizer,
        matcher: RowMatcher,
        exporter: RowExporter,
    ):
        self.source = source
        self.extractor = extractor
        self.normalizer = normalizer
        self.matcher = matcher
        self.exporter = exporter

    def run(self) -> list[RawRecord]:
        raw_records = list(self.source.fetch())
        rows = self.extractor.extract_rows(raw_records)
        rows = self.normalizer.normalize_rows(rows)
        rows = self.matcher.match_rows(rows)
        self.exporter.export_rows(rows)
        return rows

