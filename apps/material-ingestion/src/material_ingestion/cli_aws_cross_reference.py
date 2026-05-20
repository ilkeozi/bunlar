from __future__ import annotations

import argparse
from pathlib import Path

from material_ingestion.exporters import RowFileExporter
from material_ingestion.extractors.uns_aws_cross_reference_extractor import (
    UnsAwsCrossReferenceExtractor,
)
from material_ingestion.matchers import RowDedupeMatcher
from material_ingestion.normalizers import IdentityRowNormalizer
from material_ingestion.pipeline_rows import RowIngestionPipeline
from material_ingestion.sources.uns import UnsPdfPageSource


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract AWS-to-UNS cross-reference rows from UNS PDF pages."
    )
    parser.add_argument("--input", required=True, help="Path to UNS PDF file.")
    parser.add_argument("--start-page", type=int, default=3, help="1-based start page.")
    parser.add_argument("--end-page", type=int, default=7, help="1-based end page (inclusive).")
    parser.add_argument("--output", required=True, help="Output file path (.json or .csv).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)

    source = UnsPdfPageSource(
        pdf_path=Path(args.input),
        start_page=args.start_page,
        end_page=args.end_page,
    )
    extractor = UnsAwsCrossReferenceExtractor()
    normalizer = IdentityRowNormalizer()
    matcher = RowDedupeMatcher(key_fields=["aws_spec", "aws_designation", "uns"])
    exporter = RowFileExporter(
        output_path=output_path,
        fieldnames=[
            "aws_spec",
            "aws_designation",
            "uns",
            "page",
            "note",
            "raw_line",
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
