import unittest

from material_ingestion.extractors.uns.uns_base_elements_index_extractor import (
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
        self.assertEqual("", rows[0]["symbol"])
        self.assertEqual("H00001-H99999", rows[0]["uns_range"])

    def test_recovers_symbols_from_element_name_when_ocr_symbols_shift(self) -> None:
        text = """
        Element Svmbol UNS Decianation
        Dysprasium
        Erbium
        Europium
        Er
        Eu
        Fe
        E46000 - E47999
        E48000 - E49999
        E50000 - E51999
        """
        rows = UnsBaseElementsIndexExtractor().extract_from_text(text, page_number=14)
        self.assertEqual(3, len(rows))
        self.assertEqual("Dy", rows[0]["symbol"])
        self.assertEqual("Er", rows[1]["symbol"])
        self.assertEqual("Eu", rows[2]["symbol"])


if __name__ == "__main__":
    unittest.main()
