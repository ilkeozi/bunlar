import unittest

from material_ingestion.extractors.uns_base_elements_index_extractor import (
    UnsBaseElementsIndexExtractor,
)


class UnsBaseElementsIndexExtractorTest(unittest.TestCase):
    def test_extracts_rows_from_structured_text_block(self) -> None:
        text = """
        Element Svmbol UNS Decianation
        Actinium
        Aluminum
        Ac
        Al
        E00000 - E00999
        A00001 - A99999
        """
        rows = UnsBaseElementsIndexExtractor().extract_from_text(text, page_number=14)
        self.assertEqual(2, len(rows))
        self.assertEqual("Actinium", rows[0]["element_name"])
        self.assertEqual("Ac", rows[0]["symbol"])
        self.assertEqual("E00000-E00999", rows[0]["uns_range"])
        self.assertEqual("Aluminum", rows[1]["element_name"])
        self.assertEqual("Al", rows[1]["symbol"])
        self.assertEqual("A00001-A99999", rows[1]["uns_range"])

    def test_merges_wrapped_entries(self) -> None:
        text = """
        Element Svmbol UNS Decianation
        Steels
        - AISI H
        H
        H00001 - H99999
        """
        rows = UnsBaseElementsIndexExtractor().extract_from_text(text, page_number=14)
        self.assertEqual(1, len(rows))
        self.assertEqual("Steels - AISI H", rows[0]["element_name"])
        self.assertEqual("H", rows[0]["symbol"])
        self.assertEqual("H00001-H99999", rows[0]["uns_range"])


if __name__ == "__main__":
    unittest.main()

