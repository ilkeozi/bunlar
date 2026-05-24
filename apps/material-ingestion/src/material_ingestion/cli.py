from __future__ import annotations

import argparse
import json
import logging
import os
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

from material_ingestion.db import create_session_factory
from material_ingestion.db.models import RawWebDownloadedFile, RawWebPdfCandidate
from material_ingestion.exporters import CsvExporter, JsonExporter
from material_ingestion.exporters.raw_web_db_exporter import RawWebDbExporter
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
from material_ingestion.ai import DeepseekPdfClassifier
from material_ingestion.sources.web import WebFileDownloader, WebPdfDiscovery
from material_ingestion.sources.uns import (
    UnsPdfPageSource,
    UnsSeriesSectionPageSource,
    UnsSourceAdapter,
)

logger = logging.getLogger("material_ingestion.web")


def _configure_logging() -> None:
    level_name = os.getenv("MATERIAL_INGESTION_LOG_LEVEL") or os.getenv("LOG_LEVEL") or "INFO"
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
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


def _add_web_subcommands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    web = subparsers.add_parser("web", help="Website discovery and PDF capture.")
    web_sub = web.add_subparsers(dest="web_command", required=True)

    discover = web_sub.add_parser("discover-pdfs", help="Crawl website pages and persist PDF link candidates.")
    discover.add_argument("--seed-url", required=True, help="Seed URL to start crawling.")
    discover.add_argument("--max-pages", type=int, default=100, help="Maximum HTML pages to crawl.")
    discover.add_argument(
        "--cross-domain",
        action="store_true",
        help="Allow crawling links across domains. Default is same-domain only.",
    )
    discover.add_argument("--output", default=None, help="Optional output JSON path for discovered candidates.")
    discover.add_argument("--ingest-source", default="web_discovery", help="Ingestion source label.")
    discover.add_argument("--ingest-locator", default=None, help="Ingestion locator. Defaults to --seed-url.")
    discover.add_argument(
        "--ingest-batch-id",
        default=None,
        help="Batch id for idempotent upserts. Defaults to UTC timestamp.",
    )
    discover.set_defaults(handler=_run_web_discover_pdfs)

    fetch = web_sub.add_parser("fetch-pdfs", help="Download discovered PDF candidates from DB.")
    fetch.add_argument("--ingest-batch-id", required=True, help="Discovery batch id to read PDF candidates from.")
    fetch.add_argument("--min-score", type=int, default=5, help="Minimum candidate score to download.")
    fetch.add_argument("--limit", type=int, default=None, help="Max PDFs to download; omit for no cap.")
    fetch.add_argument(
        "--output-root",
        default="data/incoming/web",
        help="Root directory to store downloaded raw files.",
    )
    fetch.add_argument("--ingest-source", default="web_download", help="Ingestion source label for downloads.")
    fetch.add_argument("--ingest-locator", default="raw_web_pdf_candidate", help="Ingestion locator label.")
    fetch.add_argument(
        "--download-batch-id",
        default=None,
        help="Batch id for download table upserts. Defaults to UTC timestamp.",
    )
    fetch.set_defaults(handler=_run_web_fetch_pdfs)

    run = web_sub.add_parser("run", help="Run website discovery and PDF download end-to-end.")
    run.add_argument("--seed-url", required=True, help="Seed URL to start crawling.")
    run.add_argument("--max-pages", type=int, default=100, help="Maximum HTML pages to crawl.")
    run.add_argument(
        "--cross-domain",
        action="store_true",
        help="Allow crawling links across domains. Default is same-domain only.",
    )
    run.add_argument("--min-score", type=int, default=5, help="Minimum candidate score to download.")
    run.add_argument("--limit", type=int, default=None, help="Max PDFs to download; omit for no cap.")
    run.add_argument(
        "--output-root",
        default="data/incoming/web",
        help="Root directory to store downloaded raw files.",
    )
    run.add_argument(
        "--discover-batch-id",
        default=None,
        help="Optional batch id for discovery upserts. Defaults to UTC timestamp.",
    )
    run.add_argument(
        "--download-batch-id",
        default=None,
        help="Optional batch id for download upserts. Defaults to UTC timestamp.",
    )
    run.add_argument("--ingest-source-discovery", default="web_discovery", help="Discovery ingestion source label.")
    run.add_argument("--ingest-source-download", default="web_download", help="Download ingestion source label.")
    run.set_defaults(handler=_run_web_run)


def _is_probable_pdf_candidate(candidate: RawWebPdfCandidate) -> bool:
    pdf_url = (getattr(candidate, "pdf_url", "") or "").strip().lower()
    reason = (getattr(candidate, "reason", "") or "").strip().lower()
    if pdf_url.endswith(".pdf") or "url_pdf_suffix" in reason:
        return True
    return "api_json_url" in reason


def _parse_preferred_languages() -> set[str]:
    raw = os.getenv("MATERIAL_INGESTION_PREFERRED_LANGUAGES", "en,english")
    return {part.strip().lower() for part in raw.split(",") if part.strip()}


def _candidate_language_hints(candidate: RawWebPdfCandidate) -> set[str]:
    hints: set[str] = set()
    url = (getattr(candidate, "pdf_url", "") or "").strip()
    reason = (getattr(candidate, "reason", "") or "").strip().lower()

    parsed = urlparse(url)
    for seg in [p for p in parsed.path.split("/") if p]:
        low = seg.lower()
        if re.fullmatch(r"[a-z]{2}(-[a-z]{2})?", low):
            hints.add(low.split("-", 1)[0])

    decoded = unquote(url).lower()
    if "_english" in decoded or "-english" in decoded or "/english" in decoded:
        hints.add("english")

    for token in reason.split(","):
        token = token.strip()
        if token.startswith("lang_"):
            hints.add(token.removeprefix("lang_"))
    return hints


def _matches_preferred_language(candidate: RawWebPdfCandidate, preferred_languages: set[str]) -> bool:
    if not preferred_languages:
        return True
    hints = _candidate_language_hints(candidate)
    if not hints:
        # Unknown language: keep it to stay generic and avoid false negatives.
        return True
    return any(hint in preferred_languages for hint in hints)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Material ingestion and UNS extraction CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_material_subcommand(subparsers)
    _add_extract_subcommands(subparsers)
    _add_ingest_db_subcommands(subparsers)
    _add_web_subcommands(subparsers)
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


def _run_web_discover_pdfs(args: argparse.Namespace) -> int:
    ingest_source = args.ingest_source
    ingest_locator = args.ingest_locator or args.seed_url
    ingest_batch_id = args.ingest_batch_id or datetime.now(UTC).strftime("batch_%Y%m%d_%H%M%S")

    discovery = WebPdfDiscovery()
    logger.info(
        "starting discovery seed_url=%s max_pages=%s same_domain_only=%s",
        args.seed_url,
        args.max_pages,
        not args.cross_domain,
    )
    pages, candidates, fetch_observations = discovery.discover(
        seed_url=args.seed_url,
        same_domain_only=not args.cross_domain,
        max_pages=args.max_pages,
        strategy="auto",
        progress=lambda msg: logger.debug(msg),
    )

    candidate_rows = [
        {
            "source_page_url": c.source_page_url,
            "pdf_url": c.pdf_url,
            "anchor_text": c.anchor_text,
            "score": c.score,
            "reason": c.reason,
        }
        for c in candidates
    ]
    exporter = RawWebDbExporter(
        ingest_source=ingest_source,
        ingest_locator=ingest_locator,
        ingest_batch_id=ingest_batch_id,
    )
    page_count = exporter.export_pages(pages)
    candidate_count = exporter.export_candidates(candidate_rows)
    fetch_observation_count = exporter.export_fetch_xhr_observations([
        {
            "source_page_url": o.source_page_url,
            "response_url": o.response_url,
            "resource_type": o.resource_type,
            "status_code": o.status_code,
            "content_type": o.content_type,
            "is_json": o.is_json,
            "extracted_urls_json": json.dumps(o.extracted_urls, sort_keys=True),
            "extracted_url_count": len(o.extracted_urls),
        }
        for o in fetch_observations
    ])

    if args.output:
        out = {
            "seed_url": args.seed_url,
            "ingest_batch_id": ingest_batch_id,
            "pages": pages,
            "candidates": candidate_rows,
        }
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"Discovered batch_id={ingest_batch_id}")
    print(f"  crawled_pages: {page_count}")
    print(f"  pdf_candidates: {candidate_count}")
    print(f"  fetch_xhr_observations: {fetch_observation_count}")
    return 0


def _run_web_fetch_pdfs(args: argparse.Namespace) -> int:
    download_batch_id = args.download_batch_id or datetime.now(UTC).strftime("batch_%Y%m%d_%H%M%S")
    logger.info(
        "starting fetch discovery_batch_id=%s min_score=%s limit=%s output_root=%s",
        args.ingest_batch_id,
        args.min_score,
        args.limit,
        args.output_root,
    )
    session_factory = create_session_factory()
    with session_factory() as session:
        query = (
            session.query(RawWebPdfCandidate)
            .filter(
                RawWebPdfCandidate.ingest_batch_id == args.ingest_batch_id,
                RawWebPdfCandidate.score >= args.min_score,
            )
            .order_by(RawWebPdfCandidate.score.desc(), RawWebPdfCandidate.id.asc())
        )
        if args.limit is not None:
            query = query.limit(args.limit)
        rows = query.all()
        already_downloaded_urls = {
            row[0]
            for row in (
                session.query(RawWebDownloadedFile.source_url)
                .filter(
                    RawWebDownloadedFile.ingest_locator == "raw_web_pdf_candidate",
                    RawWebDownloadedFile.ingest_source == args.ingest_source,
                    RawWebDownloadedFile.ingest_batch_id == args.ingest_batch_id,
                )
                .all()
            )
            if row and row[0]
        }
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    deepseek_classifier = DeepseekPdfClassifier(api_key=deepseek_key) if deepseek_key else None
    preferred_languages = _parse_preferred_languages()
    filtered_rows: list[RawWebPdfCandidate] = []
    skipped_non_pdf = 0
    skipped_non_preferred_language = 0
    deepseek_promoted = 0
    for row in rows:
        if not _matches_preferred_language(row, preferred_languages):
            skipped_non_preferred_language += 1
            continue
        if _is_probable_pdf_candidate(row):
            filtered_rows.append(row)
            continue
        if deepseek_classifier is None:
            skipped_non_pdf += 1
            continue
        try:
            if deepseek_classifier.is_likely_pdf(
                pdf_url=getattr(row, "pdf_url", "") or "",
                anchor_text=getattr(row, "anchor_text", "") or "",
                reason=getattr(row, "reason", "") or "",
                source_page_url=getattr(row, "source_page_url", "") or "",
            ):
                filtered_rows.append(row)
                deepseek_promoted += 1
            else:
                skipped_non_pdf += 1
        except Exception as exc:
            logger.warning("deepseek classification failed candidate_id=%s error=%s", getattr(row, "id", "n/a"), exc)
            skipped_non_pdf += 1

    if skipped_non_pdf:
        logger.info("fetch skipped_non_pdf_like=%s", skipped_non_pdf)
    if skipped_non_preferred_language:
        logger.info("fetch skipped_non_preferred_language=%s", skipped_non_preferred_language)
    if deepseek_promoted:
        logger.info("fetch deepseek_promoted=%s", deepseek_promoted)

    deduped_rows: list[RawWebPdfCandidate] = []
    seen_urls: set[str] = set()
    skipped_duplicate_url = 0
    for row in filtered_rows:
        url = (getattr(row, "pdf_url", "") or "").strip()
        if not url:
            continue
        if url in seen_urls:
            skipped_duplicate_url += 1
            continue
        seen_urls.add(url)
        deduped_rows.append(row)
    if skipped_duplicate_url:
        logger.info("fetch skipped_duplicate_url=%s", skipped_duplicate_url)

    skipped_already_downloaded = 0
    pending_rows: list[RawWebPdfCandidate] = []
    for row in deduped_rows:
        url = (getattr(row, "pdf_url", "") or "").strip()
        if url in already_downloaded_urls:
            skipped_already_downloaded += 1
            continue
        pending_rows.append(row)
    if skipped_already_downloaded:
        logger.info("fetch skipped_already_downloaded=%s", skipped_already_downloaded)

    downloader = WebFileDownloader(
        max_retries=int(os.getenv("MATERIAL_INGESTION_DOWNLOAD_MAX_RETRIES", "4")),
        backoff_base_seconds=float(os.getenv("MATERIAL_INGESTION_DOWNLOAD_BACKOFF_BASE_SECONDS", "1.0")),
        backoff_max_seconds=float(os.getenv("MATERIAL_INGESTION_DOWNLOAD_BACKOFF_MAX_SECONDS", "20.0")),
        jitter_seconds=float(os.getenv("MATERIAL_INGESTION_DOWNLOAD_JITTER_SECONDS", "0.25")),
    )
    request_delay_seconds = float(os.getenv("MATERIAL_INGESTION_DOWNLOAD_REQUEST_DELAY_SECONDS", "0.0"))
    output_root = Path(args.output_root)
    downloaded_rows: list[dict[str, object]] = []
    for row in pending_rows:
        if request_delay_seconds > 0:
            time.sleep(request_delay_seconds)
        logger.debug("fetch downloading candidate_id=%s url=%s", getattr(row, "id", "n/a"), row.pdf_url)
        try:
            downloaded = downloader.download_pdf(source_url=row.pdf_url, output_root=output_root)
        except Exception as exc:
            logger.warning("fetch download_failed url=%s error=%s", row.pdf_url, exc)
            continue
        logger.debug(
            "fetch downloaded bytes=%s status=%s path=%s",
            downloaded.size_bytes,
            downloaded.status_code,
            downloaded.stored_path,
        )
        downloaded_rows.append(
            {
                "source_url": downloaded.source_url,
                "stored_path": downloaded.stored_path,
                "sha256": downloaded.sha256,
                "size_bytes": downloaded.size_bytes,
                "content_type": downloaded.content_type,
                "status_code": downloaded.status_code,
            }
        )

    exporter = RawWebDbExporter(
        ingest_source=args.ingest_source,
        ingest_locator=args.ingest_locator,
        ingest_batch_id=download_batch_id,
    )
    saved = exporter.export_downloaded_files(downloaded_rows)
    print(f"Downloaded batch_id={download_batch_id}")
    print(f"  selected_candidates: {len(rows)}")
    print(f"  skipped_non_preferred_language: {skipped_non_preferred_language}")
    print(f"  probable_pdf_candidates: {len(deduped_rows)}")
    print(f"  skipped_already_downloaded: {skipped_already_downloaded}")
    print(f"  pending_candidates: {len(pending_rows)}")
    print(f"  downloaded_files: {saved}")
    return 0


def _run_web_run(args: argparse.Namespace) -> int:
    discover_batch_id = args.discover_batch_id or datetime.now(UTC).strftime("batch_%Y%m%d_%H%M%S")
    download_batch_id = args.download_batch_id or datetime.now(UTC).strftime("batch_%Y%m%d_%H%M%S")

    logger.info("starting web run orchestration")
    discover_args = argparse.Namespace(
        seed_url=args.seed_url,
        max_pages=args.max_pages,
        cross_domain=args.cross_domain,
        output=None,
        ingest_source=args.ingest_source_discovery,
        ingest_locator=None,
        ingest_batch_id=discover_batch_id,
    )
    _run_web_discover_pdfs(discover_args)

    fetch_args = argparse.Namespace(
        ingest_batch_id=discover_batch_id,
        min_score=args.min_score,
        limit=args.limit,
        output_root=args.output_root,
        ingest_source=args.ingest_source_download,
        ingest_locator="raw_web_pdf_candidate",
        download_batch_id=download_batch_id,
    )
    _run_web_fetch_pdfs(fetch_args)

    print("Web run summary")
    print(f"  discover_batch_id: {discover_batch_id}")
    print(f"  download_batch_id: {download_batch_id}")
    print(f"  seed_url: {args.seed_url}")
    print(f"  max_pages: {args.max_pages}")
    print(f"  min_score: {args.min_score}")
    print(f"  limit: {args.limit if args.limit is not None else 'none'}")
    print(f"  output_root: {args.output_root}")
    return 0


def main() -> int:
    _configure_logging()
    args = parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
