from __future__ import annotations

import argparse
from pathlib import Path

from material_ingestion.exporters import RowFileExporter
from material_ingestion.extractors.page_label_resolver import PageLabelResolver
from material_ingestion.extractors.uns_series_page_index_extractor import (
    UnsSeriesPageIndexExtractor,
)
from material_ingestion.matchers import RowDedupeMatcher
from material_ingestion.normalizers import (
    CompositeRowNormalizer,
    PageReferenceRowNormalizer,
    UnsSeriesBoundaryNormalizer,
)
from material_ingestion.pipeline_rows import RowIngestionPipeline
from material_ingestion.sources.uns import UnsPdfPageSource


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract page-number index for UNS series from the table-of-contents page."
    )
    parser.add_argument("--input", required=True, help="Path to UNS PDF file.")
    parser.add_argument("--toc-page", type=int, default=12, help="TOC page number (1-based).")
    parser.add_argument("--output", required=True, help="Output file path (.json or .csv).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    source = UnsPdfPageSource(pdf_path=input_path, pages=[args.toc_page])
    extractor = UnsSeriesPageIndexExtractor()
    normalizer = CompositeRowNormalizer(
        normalizers=[
            PageReferenceRowNormalizer(resolver=PageLabelResolver.from_pdf(input_path)),
            UnsSeriesBoundaryNormalizer(pdf_path=input_path),
        ]
    )
    matcher = RowDedupeMatcher(key_fields=["series_token", "target_label"])
    exporter = RowFileExporter(
        output_path=output_path,
        fieldnames=[
            "series",
            "series_token",
            "description",
            "target_label",
            "target_page",
            "target_pdf_page",
            "page_resolution",
            "section_start_pdf_page",
            "section_end_pdf_page",
            "toc_page",
            "extraction_method",
            "ocr_used",
            "fallback_reason",
        ],
    )

    rows = RowIngestionPipeline(
        source=source,
        extractor=extractor,
        normalizer=normalizer,
        matcher=matcher,
        exporter=exporter,
    ).run()
    print(f"Extracted {len(rows)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
