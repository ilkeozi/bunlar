import os
from pathlib import Path
import unittest

from material_ingestion.extractors.uns_common_documents_index_extractor import (
    UnsCommonDocumentsIndexExtractor,
)


DEFAULT_UNS_PDF = (
    "../material-ingestion/data/incoming/uns/"
    "epdf.pub_metals-amp-alloys-in-the-unified-numbering-system-8th-ed-1999.pdf"
)


class UnsCommonDocumentsIndexE2ETest(unittest.TestCase):
    def test_extracts_cross_index_table_from_toc_page(self) -> None:
        try:
            import pypdf  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("Install dependencies first: npx nx run material-ingestion:install")

        pdf_path = Path(os.environ.get("UNS_PDF_PATH", DEFAULT_UNS_PDF))
        if not pdf_path.exists():
            self.skipTest(
                f"Real UNS PDF not found at {pdf_path}. Set UNS_PDF_PATH to run this e2e test."
            )

        rows = UnsCommonDocumentsIndexExtractor().extract(pdf_path=pdf_path, toc_page=12)

        self.assertEqual(10, len(rows))
        self.assertTrue(any(row["document_code"] == "AA" and row["target_page"] == 349 for row in rows))
        self.assertTrue(any(row["document_code"] == "AWS" and row["target_page"] == 413 for row in rows))
        self.assertTrue(
            any(row["document_code"] == "Federal" and row["target_page"] == 421 for row in rows)
        )


if __name__ == "__main__":
    unittest.main()

