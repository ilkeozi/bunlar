import unittest

from material_ingestion.extractors.uns.uns_series_data_extractor import UnsSeriesDataExtractor


class UnsSeriesDataExtractorTest(unittest.TestCase):
    def test_extracts_from_table_rows_with_method_marker(self) -> None:
        raw_records = [
            {
                "series_token": "Axxxxx",
                "series_description": "Aluminum and Aluminum Alloys",
                "section_start_pdf_page": 100,
                "section_end_pdf_page": 120,
                "pdf_page": 100,
                "text": "",
                "table_rows": [
                    ["UNIFIED NUMBER", "DESCRIPTION", "CHEMICAL COMPOSITION", "CROSS REFERENCE SPECIFICATIONS"],
                    [
                        "A12062",
                        "Aluminum Foundry Alloy, Ingot",
                        "AI rem Cu 4.2-5.0 Fe 0.07 max Mg",
                        "AA A2062",
                    ],
                ],
                "page_extraction_method": "table_pdfplumber",
                "ocr_used": False,
            }
        ]

        rows = UnsSeriesDataExtractor().extract_rows(raw_records)

        self.assertEqual(1, len(rows))
        self.assertEqual("A12062", rows[0]["uns_code"])
        self.assertEqual("table_pdfplumber", rows[0]["extraction_method"])
        self.assertEqual(["Aluminum Foundry Alloy, Ingot"], rows[0]["table_description_lines"])
        self.assertEqual(["AA A2062"], rows[0]["table_cross_reference_lines"])

    def test_falls_back_to_text_when_table_has_no_entries(self) -> None:
        raw_records = [
            {
                "series_token": "Axxxxx",
                "series_description": "Aluminum and Aluminum Alloys",
                "section_start_pdf_page": 100,
                "section_end_pdf_page": 120,
                "pdf_page": 100,
                "text": "A12062 Aluminum Foundry Alloy, AI rem Cu 4.2-5.0 Fe 0.07 max Mg AA A2062",
                "table_rows": [["UNIFIED NUMBER", "DESCRIPTION", "CHEMICAL COMPOSITION", "CROSS REFERENCE SPECIFICATIONS"]],
                "page_extraction_method": "text_pypdf_fallback",
                "fallback_reason": "no_tables_detected",
                "ocr_used": False,
            }
        ]

        rows = UnsSeriesDataExtractor().extract_rows(raw_records)

        self.assertEqual(1, len(rows))
        self.assertEqual("A12062", rows[0]["uns_code"])
        self.assertEqual("text_pypdf_fallback", rows[0]["extraction_method"])
        self.assertEqual("no_tables_detected", rows[0]["fallback_reason"])


if __name__ == "__main__":
    unittest.main()
