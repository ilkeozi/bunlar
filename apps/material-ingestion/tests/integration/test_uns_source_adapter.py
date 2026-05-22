from pathlib import Path
import unittest
from unittest.mock import patch

from material_ingestion.sources.uns.adapter import UnsSourceAdapter


class UnsSourceAdapterTest(unittest.TestCase):
    def test_uses_pdf_extractor_for_pdf_inputs(self) -> None:
        adapter = UnsSourceAdapter(input_path="data/incoming/uns/sample.pdf")

        expected = [{"uns": "G10200", "name": "Carbon Steel 1020"}]
        with patch(
            "material_ingestion.extractors.uns.uns_pdf_extractor.UnsPdfExtractor.extract_raw_records",
            return_value=expected,
        ) as mocked:
            result = list(adapter.fetch())

        mocked.assert_called_once_with(Path("data/incoming/uns/sample.pdf"))
        self.assertEqual(expected, result)


if __name__ == "__main__":
    unittest.main()

