from __future__ import annotations

from material_ingestion.exporters.base import Exporter
from material_ingestion.extractors.base import Extractor
from material_ingestion.matchers.base import Matcher
from material_ingestion.normalizers.base import Normalizer
from material_ingestion.sources.base import SourceAdapter
from material_ingestion.types import MaterialRecord


class MaterialIngestionPipeline:
    def __init__(
        self,
        source: SourceAdapter,
        extractor: Extractor,
        normalizer: Normalizer[MaterialRecord],
        matcher: Matcher[MaterialRecord],
        exporter: Exporter[list[MaterialRecord], str],
    ):
        self.source = source
        self.extractor = extractor
        self.normalizer = normalizer
        self.matcher = matcher
        self.exporter = exporter

    def run(self) -> tuple[list[MaterialRecord], str]:
        records: list[MaterialRecord] = []
        for raw in self.source.fetch():
            record = self.extractor.extract(self.source.source_name, raw)
            record = self.normalizer.normalize(record)
            record = self.matcher.match(record)
            records.append(record)

        output = self.exporter.export(records)
        return records, output
