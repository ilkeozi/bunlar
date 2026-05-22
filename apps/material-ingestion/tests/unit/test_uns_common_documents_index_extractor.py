import unittest

from material_ingestion.extractors.uns.uns_common_documents_index_extractor import (
    UnsCommonDocumentsIndexExtractor,
)


class UnsCommonDocumentsIndexExtractorTest(unittest.TestCase):
    def test_extracts_entries_with_wrapped_lines(self) -> None:
        text = """
        Cross Index of Commonly Known Documents Which Describe Materials Same as or Similar to
        Those Covered by UNS Numbers
        AISI (American Iron and Steel Institute) including SAE (Society of
        Automotive Engineers) Numbers (Carbon and Low Alloy Steels) ............................ 359
        Index of Common Trade Names ............................................................................................ 439
        """
        rows = UnsCommonDocumentsIndexExtractor().extract_from_text(text, page_number=12)

        self.assertEqual(1, len(rows))
        self.assertEqual("AISI", rows[0]["document_code"])
        self.assertEqual(359, rows[0]["target_page"])

    def test_extracts_aws_when_prefix_is_split(self) -> None:
        text = """
        Cross Index of Commonly Known Documents Which Describe Materials Same as or Similar to
        Those Covered by UNS Numbers
        AWS
        (American Welding Society) Numbers ...................................................................... 413
        Index of Common Trade Names ............................................................................................ 439
        """
        rows = UnsCommonDocumentsIndexExtractor().extract_from_text(text, page_number=12)

        self.assertEqual(1, len(rows))
        self.assertEqual("AWS", rows[0]["document_code"])
        self.assertEqual(413, rows[0]["target_page"])

    def test_extracts_non_acronym_entry(self) -> None:
        text = """
        Cross Index of Commonly Known Documents Which Describe Materials Same as or Similar to
        Those Covered by UNS Numbers
        Federal Specification Numbers .............................................................................................. 421
        Index of Common Trade Names ............................................................................................ 439
        """
        rows = UnsCommonDocumentsIndexExtractor().extract_from_text(text, page_number=12)

        self.assertEqual(1, len(rows))
        self.assertEqual("Federal", rows[0]["document_code"])
        self.assertEqual(421, rows[0]["target_page"])


if __name__ == "__main__":
    unittest.main()

