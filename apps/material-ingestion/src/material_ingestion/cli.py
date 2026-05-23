from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from material_ingestion.exporters import CsvExporter, JsonExporter
from material_ingestion.exporters.raw_uns_db_exporter import RawUnsDbExporter
from material_ingestion.extractors import (
    UnsAwsCrossReferenceExtractor,
    UnsBaseElementsIndexExtractor,
    UnsCommonDocumentsIndexExtractor,
    UnsSeriesDataExtractor,
    UnsSeriesPageIndexExtractor,
    UnsSimpleMaterialExtractor,
)
from material_ingestion.extractors.uns.uns_page_label_resolver import PageLabelResolver
from material_ingestion.matchers import RowDedupeMatcher, SimpleMaterialMatcher
from material_ingestion.material_ingestion_pipeline import MaterialIngestionPipeline
from material_ingestion.normalizers import (
    CompositeRowNormalizer,
    IdentityRowNormalizer,
    UnsPageReferenceRowNormalizer,
    UnsSeriesBoundaryNormalizer,
    UnsSeriesDataNormalizer,
    UnsSimpleMaterialNormalizer,
)
from material_ingestion.raw_ingestion_pipeline import RawIngestionPipeline
from material_ingestion.sources.uns import (
    UnsPdfPageSource,
    UnsSeriesSectionPageSource,
    UnsSourceAdapter,
)


def _add_material_subcommand(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("material", help="Ingest, normalize, and export material data.")
    parser.add_argument("--source", default="uns", choices=["uns"], help="Material source adapter to use.")
    parser.add_argument("--input", default=None, help="Optional UNS input file (.json or .pdf).")
    parser.add_argument("--output", default=None, help="Optional output file path. Prints to stdout if omitted.")
    parser.add_argument("--compact", action="store_true", help="Use compact JSON output.")
    parser.set_defaults(handler=_run_material)


def _add_extract_subcommands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    extract = subparsers.add_parser("extract", help="Extraction subcommands for UNS datasets.")
    extract_sub = extract.add_subparsers(dest="extract_command", required=True)

    aws = extract_sub.add_parser("aws-crossref", help="Extract AWS-to-UNS cross-reference rows.")
    aws.add_argument("--input", required=True, help="Path to UNS PDF file.")
    aws.add_argument("--start-page", type=int, default=3, help="1-based start page.")
    aws.add_argument("--end-page", type=int, default=7, help="1-based end page (inclusive).")
    aws.add_argument("--output", required=True, help="Output file path (.csv).")
    aws.set_defaults(handler=_run_extract_aws_crossref)

    base_el = extract_sub.add_parser("base-elements-index", help="Extract base-elements index table.")
    base_el.add_argument("--input", required=True, help="Path to UNS PDF file.")
    base_el.add_argument("--index-page", type=int, default=14, help="PDF page for base elements index.")
    base_el.add_argument("--output", required=True, help="Output file path (.csv).")
    base_el.set_defaults(handler=_run_extract_base_elements_index)

    common_docs = extract_sub.add_parser("common-documents-index", help="Extract cross-index document table.")
    common_docs.add_argument("--input", required=True, help="Path to UNS PDF file.")
    common_docs.add_argument("--toc-page", type=int, default=12, help="TOC page number (1-based).")
    common_docs.add_argument("--output", required=True, help="Output file path (.csv).")
    common_docs.set_defaults(handler=_run_extract_common_documents_index)

    series_page = extract_sub.add_parser("series-page-index", help="Extract UNS series page index from TOC.")
    series_page.add_argument("--input", required=True, help="Path to UNS PDF file.")
    series_page.add_argument("--toc-page", type=int, default=12, help="TOC page number (1-based).")
    series_page.add_argument("--output", required=True, help="Output file path (.csv).")
    series_page.set_defaults(handler=_run_extract_series_page_index)

    series_data = extract_sub.add_parser("series-data", help="Extract UNS series entries using section boundaries.")
    series_data.add_argument("--input", required=True, help="Path to UNS PDF file.")
    series_data.add_argument(
        "--series-index",
        required=True,
        help="Path to uns_series_page_index_toc_page_12.json (with section boundaries).",
    )
    series_data.add_argument("--output", required=True, help="Output file path (.csv).")
    series_data.set_defaults(handler=_run_extract_series_data)


def _add_ingest_db_subcommands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    ingest_db = subparsers.add_parser("ingest-db", help="Ingest normalized UNS datasets directly into raw_ DB tables.")
    ingest_sub = ingest_db.add_subparsers(dest="ingest_db_command", required=True)

    uns_all = ingest_sub.add_parser("uns-all", help="Run all UNS extract/normalize flows and upsert into raw_ tables.")
    uns_all.add_argument("--input", required=True, help="Path to UNS PDF file.")
    uns_all.add_argument("--aws-start-page", type=int, default=3, help="AWS cross-reference start page.")
    uns_all.add_argument("--aws-end-page", type=int, default=7, help="AWS cross-reference end page.")
    uns_all.add_argument("--toc-page", type=int, default=12, help="TOC page for indexes.")
    uns_all.add_argument("--base-elements-page", type=int, default=14, help="Base elements index page.")
    uns_all.add_argument(
        "--ingest-source",
        default="uns_pdf",
        help="Ingestion source label (for lineage), e.g. uns_pdf.",
    )
    uns_all.add_argument(
        "--ingest-locator",
        default=None,
        help="Ingestion locator (file path/object key/topic). Defaults to --input.",
    )
    uns_all.add_argument(
        "--ingest-batch-id",
        default=None,
        help="Batch id for idempotent upserts. Defaults to UTC timestamp.",
    )
    uns_all.set_defaults(handler=_run_ingest_db_uns_all)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Material ingestion and UNS extraction CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_material_subcommand(subparsers)
    _add_extract_subcommands(subparsers)
    _add_ingest_db_subcommands(subparsers)
    return parser.parse_args()


def _run_material(args: argparse.Namespace) -> int:
    pipeline = build_pipeline(args)
    _, output = pipeline.run()
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


def build_pipeline(args: argparse.Namespace) -> MaterialIngestionPipeline:
    if args.source != "uns":
        raise ValueError(f"Unsupported source: {args.source}")

    source = UnsSourceAdapter(input_path=args.input)
    extractor = UnsSimpleMaterialExtractor()
    normalizer = UnsSimpleMaterialNormalizer()
    matcher = SimpleMaterialMatcher()
    exporter = JsonExporter(pretty=not args.compact)

    return MaterialIngestionPipeline(
        source=source,
        extractor=extractor,
        normalizer=normalizer,
        matcher=matcher,
        exporter=exporter,
    )


def _run_raw_pipeline(
    *,
    source,
    extractor,
    normalizer,
    matcher,
    output_path: Path,
    fieldnames: list[str],
) -> list[dict[str, object]]:
    if output_path.suffix.lower() == ".csv":
        exporter = CsvExporter(output_path=output_path, fieldnames=fieldnames)
    else:
        # JSON path: write structured rows without forcing CSV formatting.
        class _RawJsonFileExporter:
            def __init__(self, path: Path, allowed_fields: list[str]):
                self.path = path
                self.allowed_fields = allowed_fields
                self._json = JsonExporter(pretty=True)

            def export(self, value):
                projected = [self._project_row(row) for row in value]
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.path.write_text(self._json.export(projected) + "\n", encoding="utf-8")
                return None

            def _project_row(self, row: dict[str, object]) -> dict[str, object]:
                projected: dict[str, object] = {}
                for key in self.allowed_fields:
                    if key not in row:
                        continue
                    cell = row[key]
                    if cell is None:
                        continue
                    if cell == "":
                        continue
                    if isinstance(cell, list) and not cell:
                        continue
                    projected[key] = cell
                return projected

        exporter = _RawJsonFileExporter(output_path, fieldnames)
    rows = RawIngestionPipeline(
        source=source,
        extractor=extractor,
        normalizer=normalizer,
        matcher=matcher,
        exporter=exporter,
    ).run()
    return rows


def _collect_raw_pipeline(
    *,
    source,
    extractor,
    normalizer,
    matcher,
) -> list[dict[str, object]]:
    class _NoopExporter:
        def export(self, value):
            return None

    rows = RawIngestionPipeline(
        source=source,
        extractor=extractor,
        normalizer=normalizer,
        matcher=matcher,
        exporter=_NoopExporter(),
    ).run()
    return rows


def _run_extract_aws_crossref(args: argparse.Namespace) -> int:
    rows = _run_raw_pipeline(
        source=UnsPdfPageSource(pdf_path=Path(args.input), start_page=args.start_page, end_page=args.end_page),
        extractor=UnsAwsCrossReferenceExtractor(),
        normalizer=IdentityRowNormalizer(),
        matcher=RowDedupeMatcher(key_fields=["aws_spec", "aws_designation", "uns"]),
        output_path=Path(args.output),
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
    print(f"Extracted {len(rows)} rows to {args.output}")
    return 0


def _run_extract_base_elements_index(args: argparse.Namespace) -> int:
    rows = _run_raw_pipeline(
        source=UnsPdfPageSource(pdf_path=Path(args.input), pages=[args.index_page]),
        extractor=UnsBaseElementsIndexExtractor(),
        normalizer=IdentityRowNormalizer(),
        matcher=RowDedupeMatcher(key_fields=["element_name", "symbol", "uns_range"]),
        output_path=Path(args.output),
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
    print(f"Extracted {len(rows)} rows to {args.output}")
    return 0


def _run_extract_common_documents_index(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    rows = _run_raw_pipeline(
        source=UnsPdfPageSource(pdf_path=input_path, pages=[args.toc_page]),
        extractor=UnsCommonDocumentsIndexExtractor(),
        normalizer=UnsPageReferenceRowNormalizer(resolver=PageLabelResolver.from_pdf(input_path)),
        matcher=RowDedupeMatcher(key_fields=["document_code", "target_label"]),
        output_path=Path(args.output),
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
    print(f"Extracted {len(rows)} rows to {args.output}")
    return 0


def _run_extract_series_page_index(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    rows = _run_raw_pipeline(
        source=UnsPdfPageSource(pdf_path=input_path, pages=[args.toc_page]),
        extractor=UnsSeriesPageIndexExtractor(),
        normalizer=CompositeRowNormalizer(
            normalizers=[
                UnsPageReferenceRowNormalizer(resolver=PageLabelResolver.from_pdf(input_path)),
                UnsSeriesBoundaryNormalizer(pdf_path=input_path),
            ]
        ),
        matcher=RowDedupeMatcher(key_fields=["series_token", "target_label"]),
        output_path=Path(args.output),
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
    print(f"Extracted {len(rows)} rows to {args.output}")
    return 0


def _run_extract_series_data(args: argparse.Namespace) -> int:
    rows = _run_raw_pipeline(
        source=UnsSeriesSectionPageSource(pdf_path=Path(args.input), series_index_path=Path(args.series_index)),
        extractor=UnsSeriesDataExtractor(),
        normalizer=UnsSeriesDataNormalizer(),
        matcher=RowDedupeMatcher(key_fields=["series_token", "uns_code"]),
        output_path=Path(args.output),
        fieldnames=[
            "series_token",
            "series_description",
            "uns_code",
            "description",
            "chemical_composition_structured",
            "chemical_composition_symbol_check",
            "cross_reference_specifications_structured",
            "cross_reference_specifications_check",
            "entry_pdf_page_start",
            "entry_pdf_page_end",
            "is_replaced",
            "replaced_by_codes",
            "inactive_boxed",
            "extraction_method",
            "fallback_reason",
        ],
    )
    print(f"Extracted {len(rows)} rows to {args.output}")
    return 0


def _run_ingest_db_uns_all(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    locator = args.ingest_locator or args.input
    batch_id = args.ingest_batch_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    exporter = RawUnsDbExporter(
        ingest_source=args.ingest_source,
        ingest_locator=locator,
        ingest_batch_id=batch_id,
    )

    aws_rows = _collect_raw_pipeline(
        source=UnsPdfPageSource(pdf_path=input_path, start_page=args.aws_start_page, end_page=args.aws_end_page),
        extractor=UnsAwsCrossReferenceExtractor(),
        normalizer=IdentityRowNormalizer(),
        matcher=RowDedupeMatcher(key_fields=["aws_spec", "aws_designation", "uns"]),
    )
    common_rows = _collect_raw_pipeline(
        source=UnsPdfPageSource(pdf_path=input_path, pages=[args.toc_page]),
        extractor=UnsCommonDocumentsIndexExtractor(),
        normalizer=UnsPageReferenceRowNormalizer(resolver=PageLabelResolver.from_pdf(input_path)),
        matcher=RowDedupeMatcher(key_fields=["document_code", "target_label"]),
    )
    base_rows = _collect_raw_pipeline(
        source=UnsPdfPageSource(pdf_path=input_path, pages=[args.base_elements_page]),
        extractor=UnsBaseElementsIndexExtractor(),
        normalizer=IdentityRowNormalizer(),
        matcher=RowDedupeMatcher(key_fields=["element_name", "symbol", "uns_range"]),
    )
    series_index_rows = _collect_raw_pipeline(
        source=UnsPdfPageSource(pdf_path=input_path, pages=[args.toc_page]),
        extractor=UnsSeriesPageIndexExtractor(),
        normalizer=CompositeRowNormalizer(
            normalizers=[
                UnsPageReferenceRowNormalizer(resolver=PageLabelResolver.from_pdf(input_path)),
                UnsSeriesBoundaryNormalizer(pdf_path=input_path),
            ]
        ),
        matcher=RowDedupeMatcher(key_fields=["series_token", "target_label"]),
    )

    # Series entries depend on resolved section boundaries from series index.
    from tempfile import NamedTemporaryFile

    with NamedTemporaryFile(mode="w+", suffix=".json", delete=True) as tmp:
        tmp.write(JsonExporter(pretty=False).export(series_index_rows))
        tmp.flush()
        series_entries_rows = _collect_raw_pipeline(
            source=UnsSeriesSectionPageSource(pdf_path=input_path, series_index_path=Path(tmp.name)),
            extractor=UnsSeriesDataExtractor(),
            normalizer=UnsSeriesDataNormalizer(),
            matcher=RowDedupeMatcher(key_fields=["series_token", "uns_code"]),
        )

    inserted = {
        "raw_uns_aws_cross_reference": exporter.export_aws_cross_reference(aws_rows),
        "raw_uns_common_document_index": exporter.export_common_documents_index(common_rows),
        "raw_uns_base_elements_index": exporter.export_base_elements_index(base_rows),
        "raw_uns_series_page_index": exporter.export_series_page_index(series_index_rows),
        "raw_uns_series_entry": exporter.export_series_entries(series_entries_rows),
    }
    print(f"Ingested batch_id={batch_id}")
    for table, count in inserted.items():
        print(f"  {table}: {count} rows")
    return 0


def main() -> int:
    args = parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
