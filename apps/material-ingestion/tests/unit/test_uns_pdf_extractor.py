import unittest

from material_ingestion.extractors.uns_pdf_extractor import UnsPdfExtractor


class UnsPdfExtractorTest(unittest.TestCase):
    def test_extracts_uns_codes_and_names_from_text(self) -> None:
        text = """
        G10200 Carbon Steel 1020
        This line should be ignored
        J40301 Stainless 304
        """

        extractor = UnsPdfExtractor()
        records = extractor.extract_raw_records_from_text(text)

        self.assertEqual(2, len(records))
        self.assertEqual("G10200", records[0]["uns"])
        self.assertEqual("Carbon Steel 1020", records[0]["name"])
        self.assertEqual("generic", records[0]["metadata"]["profile"])
        self.assertEqual("J40301", records[1]["uns"])
        self.assertEqual("Stainless 304", records[1]["name"])

    def test_deduplicates_uns_codes(self) -> None:
        text = """
        G10200 Carbon Steel 1020
        G10200 Carbon Steel 1020 alternative row
        """

        extractor = UnsPdfExtractor()
        records = extractor.extract_raw_records_from_text(text)

        self.assertEqual(1, len(records))
        self.assertEqual("G10200", records[0]["uns"])

    def test_uses_fallback_name_when_line_has_only_uns_code(self) -> None:
        text = "A92024"

        extractor = UnsPdfExtractor()
        records = extractor.extract_raw_records_from_text(text, include_code_only=True)

        self.assertEqual(1, len(records))
        self.assertEqual("UNS A92024", records[0]["name"])
        self.assertEqual("code-only", records[0]["metadata"]["profile"])

    def test_excludes_code_only_by_default(self) -> None:
        extractor = UnsPdfExtractor()
        records = extractor.extract_raw_records_from_text("A92024")
        self.assertEqual([], records)

    def test_detects_table_profile(self) -> None:
        text = """
        G10200  Carbon Steel 1020
        J40301  Stainless 304
        """

        extractor = UnsPdfExtractor()
        self.assertEqual("table-like", extractor.detect_structure_profile(text))

        records = extractor.extract_raw_records_from_text(text)
        self.assertEqual("table", records[0]["metadata"]["parser"])

    def test_detects_delimited_profile(self) -> None:
        text = """
        G10200 - Carbon Steel 1020
        J40301: Stainless 304
        """

        extractor = UnsPdfExtractor()
        self.assertEqual("delimited", extractor.detect_structure_profile(text))

        records = extractor.extract_raw_records_from_text(text)
        self.assertEqual("delimited", records[0]["metadata"]["parser"])

    def test_skips_range_rows_and_keeps_material_rows(self) -> None:
        text = """
        A00001 - A99999
        A02020 Aluminum Foundry Alloy, Ag 0.40-1.0
        """

        extractor = UnsPdfExtractor()
        records = extractor.extract_raw_records_from_text(text)

        self.assertEqual(1, len(records))
        self.assertEqual("A02020", records[0]["uns"])

    def test_skips_non_descriptive_names(self) -> None:
        text = """
        R01001 Rol999
        A02020 Aluminum Foundry Alloy
        """

        extractor = UnsPdfExtractor()
        records = extractor.extract_raw_records_from_text(text)

        self.assertEqual(1, len(records))
        self.assertEqual("A02020", records[0]["uns"])


if __name__ == "__main__":
    unittest.main()
