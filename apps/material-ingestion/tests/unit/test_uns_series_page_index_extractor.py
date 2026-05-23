import unittest

from material_ingestion.extractors.uns.uns_series_page_index_extractor import (
    UnsSeriesPageIndexExtractor,
)


class UnsSeriesPageIndexExtractorTest(unittest.TestCase):
    def test_extracts_series_page_entries_from_toc_text(self) -> None:
        text = """
        Listing of UNS Numbers Assigned to Date. with Description of Each Material Covered and
        References to Documents in Which the Same or Similar Materials are Described .
        Axxxxx
        cxxxxx
        zxxxxx
        Aluminum and Aluminum Alloys ................................................................................ 1
        Copper and Copper Alloys ....................................................................................... 55
        Zinc and Zinc Alloys ............................................................................................... 341
        Cross Index of Commonly Known Documents Which Describe Materials Same as or Similar to
        """
        rows = UnsSeriesPageIndexExtractor().extract_from_text(text, page_number=12)

        self.assertEqual(3, len(rows))
        self.assertEqual("A", rows[0]["series"])
        self.assertEqual(1, rows[0]["target_page"])
        self.assertEqual("C", rows[1]["series"])
        self.assertEqual(55, rows[1]["target_page"])
        self.assertEqual("Z", rows[2]["series"])
        self.assertEqual(341, rows[2]["target_page"])

    def test_handles_wrapped_descriptions(self) -> None:
        text = """
        Listing of UNS Numbers Assigned to Date. with Description of Each Material Covered and
        References to Documents in Which the Same or Similar Materials are Described .
        sxxxxx
        Heat and Corrosion Resistant Steels (Including
        Stainless). Valve Steels. and Iron-Base “Superalloys” .......................................... 269
        Cross Index of Commonly Known Documents Which Describe Materials Same as or Similar to
        """
        rows = UnsSeriesPageIndexExtractor().extract_from_text(text, page_number=12)
        self.assertEqual(1, len(rows))
        self.assertEqual("S", rows[0]["series"])
        self.assertEqual(269, rows[0]["target_page"])


if __name__ == "__main__":
    unittest.main()

