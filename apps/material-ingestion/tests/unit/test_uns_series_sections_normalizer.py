import unittest

from material_ingestion.normalizers.uns_series_data_normalizer import UnsSeriesDataNormalizer


class UnsSeriesSectionsNormalizerTest(unittest.TestCase):
    def test_splits_description_composition_and_specs(self) -> None:
        rows = [
            {
                "entry_text": "",
                "entry_raw_lines": [
                    "Aluminum Foundry Alloy, Casting",
                    "AI rem Cu 4.0-5.2 Fe 0.15 max Mg 0.15-0.55",
                    "AA 201.0 ASTM B26 SAE J452",
                ],
                "inactive_boxed_marker": False,
                "page_has_boxed_note": False,
            }
        ]
        out = UnsSeriesDataNormalizer().normalize_rows(rows)[0]
        self.assertIn("Aluminum Foundry Alloy", out["description"])
        self.assertIn("AI rem Cu", out["chemical_composition"])
        self.assertIn("AA 201.0", out["cross_reference_specifications"])

    def test_splits_inline_description_chemistry_and_specs(self) -> None:
        rows = [
            {
                "entry_text": "",
                "entry_raw_lines": [
                    "Aluminum Foundry Alloy, AI rem Cu 4.2-5.0 Fe 0.07 max Mg AA A2062",
                    "Ingot 0.20-0.35 Mn 0.20-0.50 Ni 0.03 max",
                    "Ci 0.05 max Sn 0.05 rnax Ti",
                    "0.15-0.25 Zn 0.05 rnax Other each",
                    "0.05 max. total 0.15 max",
                ],
                "inactive_boxed_marker": False,
                "page_has_boxed_note": False,
            }
        ]
        out = UnsSeriesDataNormalizer().normalize_rows(rows)[0]
        self.assertIn("Aluminum Foundry Alloy", out["description"])
        self.assertIn("Ingot", out["description"])
        self.assertIn("AI rem Cu 4.2-5.0 Fe 0.07 max Mg", out["chemical_composition"])
        self.assertIn("0.20-0.35 Mn 0.20-0.50 Ni 0.03 max", out["chemical_composition"])
        self.assertIn("AA A2062", out["cross_reference_specifications"])

    def test_prefers_table_column_values_when_present(self) -> None:
        rows = [
            {
                "entry_text": "Noisy OCR fallback line",
                "entry_raw_lines": ["Noisy OCR fallback line"],
                "table_description_lines": ["Aluminum Foundry Alloy, Ingot"],
                "table_chemical_composition_lines": [
                    "AI rem Cu 4.2-5.0 Fe 0.07 max Mg 0.20-0.35 Mn 0.20-0.50 Ni 0.03 max",
                ],
                "table_cross_reference_lines": ["AA A2062"],
                "inactive_boxed_marker": False,
                "page_has_boxed_note": False,
            }
        ]
        out = UnsSeriesDataNormalizer().normalize_rows(rows)[0]
        self.assertEqual("Aluminum Foundry Alloy, Ingot", out["description"])
        self.assertIn("AI rem Cu 4.2-5.0", out["chemical_composition"])
        self.assertEqual("AA A2062", out["cross_reference_specifications"])


if __name__ == "__main__":
    unittest.main()
