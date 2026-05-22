import unittest

from material_ingestion.extractors.uns.uns_aws_cross_reference_extractor import (
    UnsAwsCrossReferenceExtractor,
)


class UnsAwsCrossReferenceExtractorTest(unittest.TestCase):
    def test_extracts_standard_row(self) -> None:
        text = "A5.4 (E308L) ............... W30813"
        rows = UnsAwsCrossReferenceExtractor().extract_from_text(text, page_number=3)

        self.assertEqual(1, len(rows))
        self.assertEqual("A5.4", rows[0]["aws_spec"])
        self.assertEqual("E308L", rows[0]["aws_designation"])
        self.assertEqual("W30813", rows[0]["uns"])
        self.assertEqual(3, rows[0]["page"])

    def test_extracts_row_with_no_space_before_paren(self) -> None:
        text = "A5.23(EA3K) ............... K21451"
        rows = UnsAwsCrossReferenceExtractor().extract_from_text(text, page_number=6)

        self.assertEqual(1, len(rows))
        self.assertEqual("A5.23", rows[0]["aws_spec"])
        self.assertEqual("EA3K", rows[0]["aws_designation"])
        self.assertEqual("K21451", rows[0]["uns"])

    def test_extracts_row_with_note_suffix(self) -> None:
        text = "A5.8 (BCuZn-F) ............. C49080 ob"
        rows = UnsAwsCrossReferenceExtractor().extract_from_text(text, page_number=4)

        self.assertEqual(1, len(rows))
        self.assertEqual("ob", rows[0]["note"])

    def test_normalizes_ocr_style_spec_numbers(self) -> None:
        text = "A526 (EGxxT-W) ........... W20131"
        rows = UnsAwsCrossReferenceExtractor().extract_from_text(text, page_number=7)

        self.assertEqual(1, len(rows))
        self.assertEqual("A5.26", rows[0]["aws_spec"])

    def test_ignores_non_data_lines(self) -> None:
        text = """
        AWS
        A5.4
        This is a header
        """
        rows = UnsAwsCrossReferenceExtractor().extract_from_text(text, page_number=3)
        self.assertEqual([], rows)


if __name__ == "__main__":
    unittest.main()

