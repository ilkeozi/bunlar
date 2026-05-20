import os
from pathlib import Path
import unittest

from material_ingestion.extractors.uns_base_elements_index_extractor import (
    UnsBaseElementsIndexExtractor,
)


DEFAULT_UNS_PDF = (
    "../material-ingestion/data/incoming/uns/"
    "epdf.pub_metals-amp-alloys-in-the-unified-numbering-system-8th-ed-1999.pdf"
)


class UnsBaseElementsIndexE2ETest(unittest.TestCase):
    def test_extracts_base_elements_index_from_page_14(self) -> None:
        try:
            import pypdf  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("Install dependencies first: npx nx run material-ingestion:install")

        pdf_path = Path(os.environ.get("UNS_PDF_PATH", DEFAULT_UNS_PDF))
        if not pdf_path.exists():
            self.skipTest(
                f"Real UNS PDF not found at {pdf_path}. Set UNS_PDF_PATH to run this e2e test."
            )

        rows = UnsBaseElementsIndexExtractor().extract(pdf_path=pdf_path, index_page=14)
        self.assertGreater(len(rows), 80)
        self.assertTrue(
            any(row["element_name"] == "Aluminum" and row["uns_range"].startswith("A00001") for row in rows)
        )
        self.assertTrue(
            any(
                "SAE/AISI Carbon" in row["element_name"] and row["uns_range"].startswith("G00001")
                for row in rows
            )
        )


if __name__ == "__main__":
    unittest.main()
