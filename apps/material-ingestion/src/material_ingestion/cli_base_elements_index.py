from __future__ import annotations

import argparse
from pathlib import Path

from material_ingestion.exporters import RowFileExporter
from material_ingestion.extractors.uns_base_elements_index_extractor import (
    UnsBaseElementsIndexExtractor,
)
from material_ingestion.matchers import RowDedupeMatcher
from material_ingestion.normalizers import IdentityRowNormalizer
from material_ingestion.pipeline_rows import RowIngestionPipeline
from material_ingestion.sources.uns import UnsPdfPageSource


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract 'Index to UNS Designations by Base Elements' from page ix (PDF page 14)."
    )
    parser.add_argument("--input", required=True, help="Path to UNS PDF file.")
    parser.add_argument("--index-page", type=int, default=14, help="PDF page for base elements index.")
    parser.add_argument("--output", required=True, help="Output file path (.json or .csv).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)

    source = UnsPdfPageSource(pdf_path=Path(args.input), pages=[args.index_page])
    extractor = UnsBaseElementsIndexExtractor()
    normalizer = IdentityRowNormalizer()
    matcher = RowDedupeMatcher(key_fields=["element_name", "symbol", "uns_range"])
    exporter = RowFileExporter(
        output_path=output_path,
        fieldnames=[
            "element_name",
            "symbol",
            "uns_range",
            "index_label",
            "index_pdf_page",
            "row_order",
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
