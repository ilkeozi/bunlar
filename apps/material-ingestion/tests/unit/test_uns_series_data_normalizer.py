import unittest

from material_ingestion.normalizers.uns.uns_series_data_normalizer import UnsSeriesDataNormalizer


class UnsSeriesDataNormalizerTest(unittest.TestCase):
    def test_detects_replaced_by_codes(self) -> None:
        rows = [
            {
                "entry_text": "A12012 Replaced by A12011 Casting replaced by A03360",
                "inactive_boxed_marker": False,
                "page_has_boxed_note": False,
            }
        ]
        out = UnsSeriesDataNormalizer().normalize(rows)
        self.assertTrue(out[0]["is_replaced"])
        self.assertEqual(["A03360", "A12011"], out[0]["replaced_by_codes"])

    def test_marks_inactive_boxed_when_marker_and_page_note_present(self) -> None:
        rows = [
            {
                "entry_text": "A02220 Aluminum Foundry Alloy",
                "inactive_boxed_marker": True,
                "page_has_boxed_note": True,
            }
        ]
        out = UnsSeriesDataNormalizer().normalize(rows)
        self.assertTrue(out[0]["inactive_boxed"])

    def test_builds_structured_chemical_composition(self) -> None:
        rows = [
            {
                "entry_text": "",
                "entry_raw_lines": [],
                "table_description_lines": ["Aluminum Foundry Alloy, Casting"],
                "table_chemical_composition_lines": [
                    "AI rem Cu 1.0-1.5 Fe 0.13 max Ci 4.5-5.5 Ti 0.20 max Zn 0.05 max Other each 0.05 max total 0.15 max"
                ],
                "table_cross_reference_lines": [],
                "inactive_boxed_marker": False,
                "page_has_boxed_note": False,
            }
        ]
        out = UnsSeriesDataNormalizer().normalize(rows)[0]
        structured = out["chemical_composition_structured"]
        self.assertGreaterEqual(len(structured), 8)
        self.assertTrue(out["chemical_composition_symbol_check"]["all_symbols_valid"])
        self.assertEqual([], out["chemical_composition_symbol_check"]["unknown_symbols"])

        self.assertEqual("Al", structured[0]["element_symbol"])
        self.assertEqual("remainder", structured[0]["value_type"])

        cu = next(x for x in structured if x["element_symbol"] == "Cu")
        self.assertEqual("range", cu["value_type"])
        self.assertEqual(1.0, cu["min_percent"])
        self.assertEqual(1.5, cu["max_percent"])

        fe = next(x for x in structured if x["element_symbol"] == "Fe")
        self.assertEqual("max", fe["value_type"])
        self.assertEqual(0.13, fe["max_percent"])

        si = next(x for x in structured if x["element_symbol"] == "Si")
        self.assertEqual("range", si["value_type"])

        other_each = next(
            x for x in structured if x["element_symbol"] == "Other" and x.get("note") == "each"
        )
        self.assertEqual(0.05, other_each["max_percent"])

        other_total = next(
            x for x in structured if x["element_symbol"] == "Other" and x.get("note") == "total"
        )
        self.assertEqual(0.15, other_total["max_percent"])

    def test_flags_unknown_element_symbols(self) -> None:
        rows = [
            {
                "entry_text": "",
                "entry_raw_lines": [],
                "table_description_lines": ["Test Alloy"],
                "table_chemical_composition_lines": ["Xx 0.20 max Al rem"],
                "table_cross_reference_lines": [],
                "inactive_boxed_marker": False,
                "page_has_boxed_note": False,
            }
        ]
        out = UnsSeriesDataNormalizer().normalize(rows)[0]
        check = out["chemical_composition_symbol_check"]
        self.assertFalse(check["all_symbols_valid"])
        self.assertEqual(["Xx"], check["unknown_symbols"])

    def test_builds_structured_cross_reference_specifications(self) -> None:
        rows = [
            {
                "entry_text": "",
                "entry_raw_lines": [],
                "table_description_lines": ["Wrought Aluminum Alloy, Heat Treatable"],
                "table_chemical_composition_lines": ["Al rem Cu 5.5-6.5 Fe 0.20 max"],
                "table_cross_reference_lines": ["AA 2004 AMS 4208 MAM 4208; 4209"],
                "inactive_boxed_marker": False,
                "page_has_boxed_note": False,
            }
        ]
        out = UnsSeriesDataNormalizer().normalize(rows)[0]
        refs = out["cross_reference_specifications_structured"]
        self.assertEqual(
            [
                {"document_code": "AA", "specification": "2004"},
                {"document_code": "AMS", "specification": "4208"},
                {"document_code": "MAM", "specification": "4208"},
                {"document_code": "MAM", "specification": "4209"},
            ],
            refs,
        )
        self.assertTrue(out["cross_reference_specifications_check"]["all_document_codes_known"])

    def test_flags_unknown_cross_reference_document_code(self) -> None:
        rows = [
            {
                "entry_text": "",
                "entry_raw_lines": [],
                "table_description_lines": ["Test"],
                "table_chemical_composition_lines": ["Al rem"],
                "table_cross_reference_lines": ["ZZZ 1234"],
                "inactive_boxed_marker": False,
                "page_has_boxed_note": False,
            }
        ]
        out = UnsSeriesDataNormalizer().normalize(rows)[0]
        check = out["cross_reference_specifications_check"]
        self.assertFalse(check["all_document_codes_known"])
        self.assertEqual(["ZZZ"], check["unknown_document_codes"])

    def test_extracts_boxed_cross_reference_flag(self) -> None:
        rows = [
            {
                "entry_text": "",
                "entry_raw_lines": [],
                "table_description_lines": ["Test"],
                "table_chemical_composition_lines": ["Al rem"],
                "table_cross_reference_lines": ["AA 249.0 'Boxed of"],
                "inactive_boxed_marker": False,
                "page_has_boxed_note": False,
            }
        ]
        out = UnsSeriesDataNormalizer().normalize(rows)[0]
        flags = out["cross_reference_specifications_flags"]
        self.assertTrue(flags["has_boxed_marker"])


if __name__ == "__main__":
    unittest.main()
