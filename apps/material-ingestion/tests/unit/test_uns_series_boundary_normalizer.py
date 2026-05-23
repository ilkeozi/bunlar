from pathlib import Path
import unittest

from material_ingestion.normalizers.uns.uns_series_boundary_normalizer import (
    UnsSeriesBoundaryNormalizer,
)


class UnsSeriesBoundaryNormalizerTest(unittest.TestCase):
    def test_infers_section_boundaries_and_fallback_target_page(self) -> None:
        pdf_path = Path(
            "data/incoming/uns/epdf.pub_metals-amp-alloys-in-the-unified-numbering-system-8th-ed-1999.pdf"
        )
        rows = [
            {
                "series_token": "Axxxxx",
                "target_label": "1",
                "target_page": 1,
                "target_pdf_page": None,
                "page_resolution": "unresolved",
            },
            {
                "series_token": "Cxxxxx",
                "target_label": "55",
                "target_page": 55,
                "target_pdf_page": None,
                "page_resolution": "unresolved",
            },
        ]

        normalized = UnsSeriesBoundaryNormalizer(pdf_path=pdf_path).normalize(rows)

        self.assertEqual(15, normalized[0]["section_start_pdf_page"])
        self.assertEqual(67, normalized[0]["section_end_pdf_page"])
        self.assertEqual(15, normalized[0]["target_pdf_page"])
        self.assertEqual("section-heading-start", normalized[0]["page_resolution"])

        self.assertEqual(68, normalized[1]["section_start_pdf_page"])
        self.assertEqual(118, normalized[1]["section_end_pdf_page"])


if __name__ == "__main__":
    unittest.main()

