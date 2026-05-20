import os
from pathlib import Path
import unittest

from material_ingestion.normalizers.uns_series_data_normalizer import UnsSeriesDataNormalizer
from material_ingestion.sources.uns import UnsSeriesSectionPageSource
from material_ingestion.extractors.uns_series_data_extractor import UnsSeriesDataExtractor


DEFAULT_UNS_PDF = (
    "../material-ingestion/data/incoming/uns/"
    "epdf.pub_metals-amp-alloys-in-the-unified-numbering-system-8th-ed-1999.pdf"
)
DEFAULT_SERIES_INDEX = "../material-ingestion/data/working/normalized/uns_series_page_index_toc_page_12.json"


class UnsSeriesDataE2ETest(unittest.TestCase):
    def test_extracts_series_entries_with_replaced_and_boxed_flags(self) -> None:
        try:
            import pypdf  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("Install dependencies first: npx nx run material-ingestion:install")

        pdf_path = Path(os.environ.get("UNS_PDF_PATH", DEFAULT_UNS_PDF))
        index_path = Path(os.environ.get("UNS_SERIES_INDEX_PATH", DEFAULT_SERIES_INDEX))
        if not pdf_path.exists() or not index_path.exists():
            self.skipTest("Required PDF or series index file not found.")

        raw_records = UnsSeriesSectionPageSource(
            pdf_path=pdf_path,
            series_index_path=index_path,
        ).fetch()
        extracted = UnsSeriesDataExtractor().extract_rows(raw_records)
        rows = UnsSeriesDataNormalizer().normalize_rows(extracted)

        self.assertGreater(len(rows), 3000)
        self.assertTrue(any(row["is_replaced"] for row in rows))
        self.assertTrue(any(row["inactive_boxed"] for row in rows))
        self.assertTrue(any(row["series_token"] == "Axxxxx" and row["uns_code"] == "A02020" for row in rows))


if __name__ == "__main__":
    unittest.main()

