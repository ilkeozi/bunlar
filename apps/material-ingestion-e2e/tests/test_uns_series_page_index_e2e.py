import os
from pathlib import Path
import unittest

from material_ingestion.extractors.uns_series_page_index_extractor import (
    UnsSeriesPageIndexExtractor,
)


DEFAULT_UNS_PDF = (
    "../material-ingestion/data/incoming/uns/"
    "epdf.pub_metals-amp-alloys-in-the-unified-numbering-system-8th-ed-1999.pdf"
)


class UnsSeriesPageIndexE2ETest(unittest.TestCase):
    def test_extracts_toc_series_index_from_page_12(self) -> None:
        try:
            import pypdf  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("Install dependencies first: npx nx run material-ingestion:install")

        pdf_path = Path(os.environ.get("UNS_PDF_PATH", DEFAULT_UNS_PDF))
        if not pdf_path.exists():
            self.skipTest(
                f"Real UNS PDF not found at {pdf_path}. Set UNS_PDF_PATH to run this e2e test."
            )

        rows = UnsSeriesPageIndexExtractor().extract(pdf_path=pdf_path, toc_page=12)

        self.assertEqual(17, len(rows))
        self.assertTrue(any(row["series"] == "A" and row["target_page"] == 1 for row in rows))
        self.assertTrue(any(row["series"] == "W" and row["target_page"] == 305 for row in rows))
        self.assertTrue(any(row["series"] == "Z" and row["target_page"] == 341 for row in rows))


if __name__ == "__main__":
    unittest.main()

