from __future__ import annotations

import argparse
from pathlib import Path

from material_ingestion.exporters import RowFileExporter
from material_ingestion.extractors.page_label_resolver import PageLabelResolver
from material_ingestion.extractors.uns_common_documents_index_extractor import (
    UnsCommonDocumentsIndexExtractor,
)
from material_ingestion.matchers import RowDedupeMatcher
from material_ingestion.normalizers import PageReferenceRowNormalizer
from material_ingestion.pipeline_rows import RowIngestionPipeline
from material_ingestion.sources.uns import UnsPdfPageSource


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract TOC cross-index document table and target pages."
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
    extractor = UnsCommonDocumentsIndexExtractor()
    normalizer = PageReferenceRowNormalizer(resolver=PageLabelResolver.from_pdf(input_path))
    matcher = RowDedupeMatcher(key_fields=["document_code", "target_label"])
    exporter = RowFileExporter(
        output_path=output_path,
        fieldnames=[
            "document_code",
            "description",
            "target_label",
            "target_page",
            "target_pdf_page",
            "page_resolution",
            "toc_page",
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
