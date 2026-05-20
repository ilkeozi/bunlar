import os
import re
from pathlib import Path
import unittest

from material_ingestion.cli import build_pipeline


DEFAULT_UNS_PDF = (
    "../material-ingestion/data/incoming/uns/"
    "epdf.pub_metals-amp-alloys-in-the-unified-numbering-system-8th-ed-1999.pdf"
)


class _Args:
    source = "uns"
    compact = True
    input = ""


class UnsRealPdfE2ETest(unittest.TestCase):
    def test_parses_real_uns_pdf(self) -> None:
        try:
            import pypdf  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("Install dependencies first: npx nx run material-ingestion:install")

        pdf_path = Path(os.environ.get("UNS_PDF_PATH", DEFAULT_UNS_PDF))
        if not pdf_path.exists():
            self.skipTest(
                f"Real UNS PDF not found at {pdf_path}. Set UNS_PDF_PATH to run this e2e test."
            )

        args = _Args()
        args.input = str(pdf_path)
        pipeline = build_pipeline(args)
        records, _ = pipeline.run()

        self.assertGreater(len(records), 0)
        self.assertTrue(any(re.fullmatch(r"[A-Z]\d{5}", record.material_id) for record in records))


if __name__ == "__main__":
    unittest.main()
