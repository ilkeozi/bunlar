# material-ingestion

Python Nx application for modular material data ingestion.

## Pipeline stages

1. `sources`: pull raw source records (UNS first adapter).
2. `extractors`: convert raw records into a common material shape.
3. `normalizers`: canonicalize naming and field structure.
4. `matchers`: resolve duplicates and cross-source identity.
5. `exporters`: write normalized records to output formats.

## Run with Nx

```bash
npx nx run material-ingestion:run
```

## Install dependencies with Nx

```bash
npx nx run material-ingestion:install
```

Install optional dev extras:

```bash
npx nx run material-ingestion:install-dev
```

## Run tests

```bash
npx nx run material-ingestion:test
```

Run unit tests only:

```bash
npx nx run material-ingestion:test-unit
```

Run integration tests only:

```bash
npx nx run material-ingestion:test-integration
```

Run e2e tests (separate Nx project):

```bash
npx nx run material-ingestion-e2e:e2e
```

## PDF support

UNS PDF ingestion is table-first:

- `pdfplumber` for table extraction (primary path for tabular sections)
- `pypdf` text extraction as fallback when table parsing does not yield entries
- OCR is not used by default

Every extracted row now carries provenance markers:

- `extraction_method` (for example `table_pdfplumber`, `text_pypdf_fallback`)
- `ocr_used` (`false` unless OCR is explicitly introduced later)
- `fallback_reason` (for fallback cases, for example `no_tables_detected`)

Real PDF e2e test defaults to:

- `apps/material-ingestion/data/incoming/uns/epdf.pub_metals-amp-alloys-in-the-unified-numbering-system-8th-ed-1999.pdf`

Or set a custom PDF path:

```bash
UNS_PDF_PATH=/absolute/or/relative/path/to/file.pdf npx nx run material-ingestion-e2e:e2e
```

Extract AWS cross-reference mapping (pages 3-7):

```bash
npx nx run material-ingestion:extract-aws-crossref
```

Direct command with custom range/output:

```bash
cd apps/material-ingestion
PYTHONPATH=src .venv/bin/python -m material_ingestion.cli extract aws-crossref \
  --input data/incoming/uns/epdf.pub_metals-amp-alloys-in-the-unified-numbering-system-8th-ed-1999.pdf \
  --start-page 3 \
  --end-page 7 \
  --output data/working/normalized/uns_aws_cross_reference_pages_3_7.csv
```

Extract UNS series page index from TOC page 12:

```bash
npx nx run material-ingestion:extract-series-page-index
```

Direct command:

```bash
cd apps/material-ingestion
PYTHONPATH=src .venv/bin/python -m material_ingestion.cli extract series-page-index \
  --input data/incoming/uns/epdf.pub_metals-amp-alloys-in-the-unified-numbering-system-8th-ed-1999.pdf \
  --toc-page 12 \
  --output data/working/normalized/uns_series_page_index_toc_page_12.json
```

Extract cross-index of commonly known documents from TOC page 12:

```bash
npx nx run material-ingestion:extract-common-documents-index
```

Direct command:

```bash
cd apps/material-ingestion
PYTHONPATH=src .venv/bin/python -m material_ingestion.cli extract common-documents-index \
  --input data/incoming/uns/epdf.pub_metals-amp-alloys-in-the-unified-numbering-system-8th-ed-1999.pdf \
  --toc-page 12 \
  --output data/working/normalized/uns_common_documents_index_toc_page_12.json
```

Extract "Index to UNS Designations by Base Elements" from page 14 (`ix`):

```bash
npx nx run material-ingestion:extract-base-elements-index
```

Direct command:

```bash
cd apps/material-ingestion
PYTHONPATH=src .venv/bin/python -m material_ingestion.cli extract base-elements-index \
  --input data/incoming/uns/epdf.pub_metals-amp-alloys-in-the-unified-numbering-system-8th-ed-1999.pdf \
  --index-page 14 \
  --output data/working/normalized/uns_base_elements_index_page_14.json
```

Extract series entries using TOC section boundaries:

```bash
npx nx run material-ingestion:extract-series-data
```

Direct command:

```bash
cd apps/material-ingestion
PYTHONPATH=src .venv/bin/python -m material_ingestion.cli extract series-data \
  --input data/incoming/uns/epdf.pub_metals-amp-alloys-in-the-unified-numbering-system-8th-ed-1999.pdf \
  --series-index data/working/normalized/uns_series_page_index_toc_page_12.json \
  --output data/working/normalized/uns_series_entries_from_toc.json
```

This extraction includes:

- `is_replaced` and `replaced_by_codes` from `replaced by` statements
- `inactive_boxed` using boxed-entry marker + page footer note

## TDD approach for changing PDF structures

1. Add/adjust a unit test in `tests/unit/test_uns_pdf_extractor.py` for the new line structure.
2. Update parser rules in `src/material_ingestion/extractors/uns_pdf_extractor.py`.
3. Run integration tests in `tests/integration`.
4. Run the real-PDF e2e test to validate on source files.

Current parser behavior:

- Detects profile (`table-like`, `delimited`, `generic`, `code-only`)
- Applies profile-specific parsing order
- Filters out range/header rows and non-descriptive OCR noise by default
- Supports debug mode with `include_code_only=True` in extractor calls
