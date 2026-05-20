from __future__ import annotations

import argparse
from pathlib import Path

from material_ingestion.exporters import RowFileExporter
from material_ingestion.extractors.uns_series_data_extractor import UnsSeriesDataExtractor
from material_ingestion.matchers import RowDedupeMatcher
from material_ingestion.normalizers import UnsSeriesDataNormalizer
from material_ingestion.pipeline_rows import RowIngestionPipeline
from material_ingestion.sources.uns import UnsSeriesSectionPageSource


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract UNS series entries based on TOC-generated series boundaries."
    )
    parser.add_argument("--input", required=True, help="Path to UNS PDF file.")
    parser.add_argument(
        "--series-index",
        required=True,
        help="Path to uns_series_page_index_toc_page_12.json (with section boundaries).",
    )
    parser.add_argument("--output", required=True, help="Output path (.json or .csv).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)

    source = UnsSeriesSectionPageSource(
        pdf_path=Path(args.input),
        series_index_path=Path(args.series_index),
    )
    extractor = UnsSeriesDataExtractor()
    normalizer = UnsSeriesDataNormalizer()
    matcher = RowDedupeMatcher(key_fields=["series_token", "uns_code"])
    exporter = RowFileExporter(
        output_path=output_path,
        fieldnames=[
            "series_token",
            "series_description",
            "uns_code",
            "description",
            "chemical_composition",
            "chemical_composition_structured",
            "chemical_composition_symbol_check",
            "cross_reference_specifications",
            "cross_reference_specifications_structured",
            "cross_reference_specifications_check",
            "cross_reference_specifications_flags",
            "entry_pdf_page_start",
            "entry_pdf_page_end",
            "is_replaced",
            "replaced_by_codes",
            "inactive_boxed",
            "extraction_method",
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
