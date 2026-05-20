from __future__ import annotations

import argparse
from pathlib import Path

from material_ingestion.exporters import JsonExporter
from material_ingestion.extractors import SimpleMaterialExtractor
from material_ingestion.matchers import SimpleMaterialMatcher
from material_ingestion.normalizers import SimpleMaterialNormalizer
from material_ingestion.pipeline import MaterialIngestionPipeline
from material_ingestion.sources.uns import UnsSourceAdapter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest, normalize, and export engineering material data."
    )
    parser.add_argument(
        "--source",
        default="uns",
        choices=["uns"],
        help="Material source adapter to use.",
    )
    parser.add_argument(
        "--input",
        default=None,
        help="Optional UNS input file (.json or .pdf).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output file path. Prints to stdout if omitted.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Use compact JSON output.",
    )
    return parser.parse_args()


def build_pipeline(args: argparse.Namespace) -> MaterialIngestionPipeline:
    if args.source != "uns":
        raise ValueError(f"Unsupported source: {args.source}")

    source = UnsSourceAdapter(input_path=args.input)
    extractor = SimpleMaterialExtractor()
    normalizer = SimpleMaterialNormalizer()
    matcher = SimpleMaterialMatcher()
    exporter = JsonExporter(pretty=not args.compact)

    return MaterialIngestionPipeline(
        source=source,
        extractor=extractor,
        normalizer=normalizer,
        matcher=matcher,
        exporter=exporter,
    )


def main() -> int:
    args = parse_args()
    pipeline = build_pipeline(args)
    _, output = pipeline.run()

    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
