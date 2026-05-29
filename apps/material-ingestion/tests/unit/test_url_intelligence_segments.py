from __future__ import annotations

import unittest

from material_ingestion.services.url_intelligence.segment_predicates import classify_segment
from material_ingestion.services.url_intelligence.models import SegmentKind


class SegmentLiteralTest(unittest.TestCase):
    """Short route tokens must not be mis-classified."""

    def test_ci_is_literal(self) -> None:
        self.assertEqual(classify_segment("ci"), SegmentKind.LITERAL)

    def test_ed_is_literal(self) -> None:
        self.assertEqual(classify_segment("ed"), SegmentKind.LITERAL)

    def test_cp_is_literal(self) -> None:
        self.assertEqual(classify_segment("cp"), SegmentKind.LITERAL)

    def test_ec_is_literal(self) -> None:
        self.assertEqual(classify_segment("ec"), SegmentKind.LITERAL)

    def test_ap_is_literal(self) -> None:
        self.assertEqual(classify_segment("ap"), SegmentKind.LITERAL)

    def test_us_is_literal(self) -> None:
        # "us" is a market code, not a language
        self.assertNotEqual(classify_segment("us"), SegmentKind.LANGUAGE)

    def test_eu_is_literal(self) -> None:
        self.assertNotEqual(classify_segment("eu"), SegmentKind.LANGUAGE)

    def test_single_char_is_literal(self) -> None:
        self.assertEqual(classify_segment("s"), SegmentKind.LITERAL)

    def test_api_version_is_literal(self) -> None:
        self.assertEqual(classify_segment("v1"), SegmentKind.LITERAL)

    def test_downloads_is_literal(self) -> None:
        self.assertEqual(classify_segment("downloads"), SegmentKind.LITERAL)

    def test_global_is_market_region(self) -> None:
        self.assertEqual(classify_segment("global"), SegmentKind.MARKET_OR_REGION)

    def test_emea_is_market_region(self) -> None:
        self.assertEqual(classify_segment("emea"), SegmentKind.MARKET_OR_REGION)


class SegmentLanguageTest(unittest.TestCase):

    def test_en_is_language(self) -> None:
        self.assertEqual(classify_segment("en"), SegmentKind.LANGUAGE)

    def test_de_is_language(self) -> None:
        self.assertEqual(classify_segment("de"), SegmentKind.LANGUAGE)

    def test_fr_is_language(self) -> None:
        self.assertEqual(classify_segment("fr"), SegmentKind.LANGUAGE)

    def test_zh_is_language(self) -> None:
        self.assertEqual(classify_segment("zh"), SegmentKind.LANGUAGE)

    def test_en_us_locale_is_language(self) -> None:
        self.assertEqual(classify_segment("en-US"), SegmentKind.LANGUAGE)

    def test_en_us_underscore_locale_is_language(self) -> None:
        self.assertEqual(classify_segment("en_US"), SegmentKind.LANGUAGE)

    def test_fr_fr_locale_is_language(self) -> None:
        self.assertEqual(classify_segment("fr-FR"), SegmentKind.LANGUAGE)


class SegmentNumericIDTest(unittest.TestCase):

    def test_eight_digit_id(self) -> None:
        self.assertEqual(classify_segment("30036817"), SegmentKind.NUMERIC_ID)

    def test_five_digit_id(self) -> None:
        self.assertEqual(classify_segment("12345"), SegmentKind.NUMERIC_ID)

    def test_two_digits_not_numeric_id(self) -> None:
        # Only 2 digits — below the 3-digit threshold
        self.assertNotEqual(classify_segment("12"), SegmentKind.NUMERIC_ID)


class SegmentLongIDTest(unittest.TestCase):

    def test_salesforce_id(self) -> None:
        self.assertEqual(classify_segment("a0g2p00000XQEZDAA5"), SegmentKind.LONG_ID)

    def test_long_mixed_case_alphanumeric(self) -> None:
        self.assertEqual(classify_segment("ABC123DEF456GHI789"), SegmentKind.LONG_ID)

    def test_short_mixed_does_not_qualify(self) -> None:
        # 8 chars — below the 12-char threshold
        self.assertNotEqual(classify_segment("Abc12345"), SegmentKind.LONG_ID)


class SegmentUUIDTest(unittest.TestCase):

    def test_standard_uuid(self) -> None:
        self.assertEqual(
            classify_segment("550e8400-e29b-41d4-a716-446655440000"),
            SegmentKind.UUID,
        )

    def test_uppercase_uuid(self) -> None:
        self.assertEqual(
            classify_segment("550E8400-E29B-41D4-A716-446655440000"),
            SegmentKind.UUID,
        )


class SegmentSlugTest(unittest.TestCase):

    def test_hyphenated_chemical_name(self) -> None:
        self.assertEqual(classify_segment("aacrylic-acid"), SegmentKind.SLUG)

    def test_underscore_category(self) -> None:
        self.assertEqual(classify_segment("performance_polymers"), SegmentKind.SLUG)

    def test_short_hyphen_not_slug(self) -> None:
        # 'lg-grade': 'lg' part is only 2 chars → literal
        self.assertEqual(classify_segment("lg-grade"), SegmentKind.LITERAL)

    def test_tds_sheets_is_slug(self) -> None:
        # Each part 'tds' and 'sheets' has 3+ chars and total >= 9
        self.assertEqual(classify_segment("tds-sheets"), SegmentKind.SLUG)

    def test_code_slug_with_digits(self) -> None:
        # Contains digits → code_slug
        self.assertEqual(classify_segment("Ultramid-B3S"), SegmentKind.CODE_SLUG)


class SegmentDateLikeTest(unittest.TestCase):

    def test_yyyymmdd(self) -> None:
        self.assertEqual(classify_segment("20230501"), SegmentKind.DATE_LIKE)

    def test_dashed_date(self) -> None:
        self.assertEqual(classify_segment("2023-05-01"), SegmentKind.DATE_LIKE)


class SegmentFileTest(unittest.TestCase):

    def test_tds_pdf_is_technical(self) -> None:
        self.assertEqual(
            classify_segment("Palatinol_DOTP_TDS_202305.pdf"),
            SegmentKind.TECHNICAL_DOCUMENT_FILE,
        )

    def test_safety_data_sheet_pdf(self) -> None:
        self.assertEqual(
            classify_segment("Safety_Data_Sheet_Product_X_EN.pdf"),
            SegmentKind.TECHNICAL_DOCUMENT_FILE,
        )

    def test_sds_pdf(self) -> None:
        self.assertEqual(classify_segment("product_sds.pdf"), SegmentKind.TECHNICAL_DOCUMENT_FILE)

    def test_msds_pdf(self) -> None:
        self.assertEqual(classify_segment("msds_material.pdf"), SegmentKind.TECHNICAL_DOCUMENT_FILE)

    def test_plain_pdf_is_document(self) -> None:
        self.assertEqual(classify_segment("terms-and-conditions.pdf"), SegmentKind.DOCUMENT_FILE)

    def test_docx_is_document(self) -> None:
        self.assertEqual(classify_segment("report.docx"), SegmentKind.DOCUMENT_FILE)

    def test_js_is_asset(self) -> None:
        self.assertEqual(classify_segment("app.12345.js"), SegmentKind.ASSET_FILE)

    def test_css_is_asset(self) -> None:
        self.assertEqual(classify_segment("styles.css"), SegmentKind.ASSET_FILE)

    def test_png_is_asset(self) -> None:
        self.assertEqual(classify_segment("logo.png"), SegmentKind.ASSET_FILE)

    def test_svg_is_asset(self) -> None:
        self.assertEqual(classify_segment("icon.svg"), SegmentKind.ASSET_FILE)

    def test_technical_overrides_document(self) -> None:
        # Both .pdf extension AND TDS token → technical_document_file wins
        kind = classify_segment("My_Product_TDS.pdf")
        self.assertEqual(kind, SegmentKind.TECHNICAL_DOCUMENT_FILE)


if __name__ == "__main__":
    unittest.main()
