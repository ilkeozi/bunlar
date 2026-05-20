import os
from pathlib import Path
import unittest

from material_ingestion.extractors.uns_aws_cross_reference_extractor import (
    UnsAwsCrossReferenceExtractor,
)


DEFAULT_UNS_PDF = (
    "../material-ingestion/data/incoming/uns/"
    "epdf.pub_metals-amp-alloys-in-the-unified-numbering-system-8th-ed-1999.pdf"
)


class UnsAwsCrossReferenceE2ETest(unittest.TestCase):
    def test_extracts_aws_cross_reference_rows_from_pages_3_to_7(self) -> None:
        try:
            import pypdf  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("Install dependencies first: npx nx run material-ingestion:install")

        pdf_path = Path(os.environ.get("UNS_PDF_PATH", DEFAULT_UNS_PDF))
        if not pdf_path.exists():
            self.skipTest(
                f"Real UNS PDF not found at {pdf_path}. Set UNS_PDF_PATH to run this e2e test."
            )

        extractor = UnsAwsCrossReferenceExtractor()
        rows = extractor.extract(pdf_path=pdf_path, start_page=3, end_page=7)

        self.assertGreater(len(rows), 200)
        self.assertTrue(any(row["aws_spec"] == "A5.4" and row["uns"] == "W30813" for row in rows))
        self.assertTrue(any(row["aws_spec"] == "A5.23" and row["uns"] == "K21451" for row in rows))


if __name__ == "__main__":
    unittest.main()

