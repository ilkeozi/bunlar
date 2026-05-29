from __future__ import annotations

import unittest

from material_ingestion.services.url_intelligence import decide
from material_ingestion.services.url_intelligence.models import (
    NextAction,
    PatternStats,
    SegmentKind,
    SourceContext,
    URLRole,
)


class Test01NumericProductRoute(unittest.TestCase):
    """https://products.basf.com/global/en/ci/30036817"""

    def setUp(self) -> None:
        self.result = decide("https://products.basf.com/global/en/ci/30036817")

    def test_ci_is_literal(self) -> None:
        ci_seg = next(s for s in self.result.debug["segments"] if s["raw"] == "ci")
        self.assertEqual(ci_seg["kind"], SegmentKind.LITERAL.value)

    def test_en_is_language(self) -> None:
        en_seg = next(s for s in self.result.debug["segments"] if s["raw"] == "en")
        self.assertEqual(en_seg["kind"], SegmentKind.LANGUAGE.value)

    def test_medium_template_present(self) -> None:
        templates = {c.level: c.template for c in self.result.templates}
        self.assertEqual(templates["medium"], "/global/{language}/ci/{numeric_id}")

    def test_role_is_product_or_generic(self) -> None:
        self.assertIn(
            self.result.url_role,
            (URLRole.PRODUCT_LIKE_PAGE, URLRole.GENERIC_HTML, URLRole.UNKNOWN),
        )

    def test_not_technical_document(self) -> None:
        self.assertNotEqual(self.result.url_role, URLRole.TECHNICAL_DOCUMENT)


class Test02ShortRouteSegmentEd(unittest.TestCase):
    """https://products.basf.com/global/en/ed/30036817 — 'ed' must not be language."""

    def setUp(self) -> None:
        self.result = decide("https://products.basf.com/global/en/ed/30036817")

    def test_ed_is_literal(self) -> None:
        ed_seg = next(s for s in self.result.debug["segments"] if s["raw"] == "ed")
        self.assertEqual(ed_seg["kind"], SegmentKind.LITERAL.value)


class Test03TechnicalPDF(unittest.TestCase):
    """https://chemicals.basf.com/global/documents/tds-sheets/Palatinol_DOTP_TDS_202305.pdf"""

    URL = "https://chemicals.basf.com/global/documents/tds-sheets/Palatinol_DOTP_TDS_202305.pdf"

    def setUp(self) -> None:
        self.result = decide(self.URL)

    def test_role_is_technical_document(self) -> None:
        self.assertEqual(self.result.url_role, URLRole.TECHNICAL_DOCUMENT)

    def test_action_is_fetch_document(self) -> None:
        self.assertEqual(self.result.next_action, NextAction.FETCH_DOCUMENT)

    def test_template_includes_placeholder(self) -> None:
        templates = {c.level: c.template for c in self.result.templates}
        self.assertIn("{technical_document_file}", templates["specific"])

    def test_high_url_score(self) -> None:
        self.assertGreaterEqual(self.result.scores.url_score, 100)

    def test_reason_code_present(self) -> None:
        self.assertIn("TECH_DOC_FILE_URL", self.result.reason_codes)

    def test_canonical_url_has_no_fragment(self) -> None:
        self.assertNotIn("#", self.result.canonical_url)


class Test04SDSPDF(unittest.TestCase):
    """https://example.com/files/Safety_Data_Sheet_Product_X_EN.pdf"""

    def setUp(self) -> None:
        self.result = decide("https://example.com/files/Safety_Data_Sheet_Product_X_EN.pdf")

    def test_role_is_technical_document(self) -> None:
        self.assertEqual(self.result.url_role, URLRole.TECHNICAL_DOCUMENT)

    def test_action_is_fetch_document(self) -> None:
        self.assertEqual(self.result.next_action, NextAction.FETCH_DOCUMENT)


class Test05LegalPDF(unittest.TestCase):
    """https://example.com/legal/terms-and-conditions.pdf"""

    def setUp(self) -> None:
        self.result = decide("https://example.com/legal/terms-and-conditions.pdf")

    def test_role_is_noise_or_document(self) -> None:
        self.assertIn(self.result.url_role, (URLRole.NOISE, URLRole.DOCUMENT))

    def test_not_high_priority_fetch(self) -> None:
        self.assertNotEqual(self.result.next_action, NextAction.FETCH_DOCUMENT)

    def test_noise_reason_code_present(self) -> None:
        self.assertIn("LEGAL_NOISE", self.result.reason_codes)

    def test_score_is_negative(self) -> None:
        self.assertLess(self.result.scores.url_score, 0)


class Test06DownloadListingPage(unittest.TestCase):
    """https://plastics-rubber.basf.com/global/en/performance_polymers/downloads"""

    URL = "https://plastics-rubber.basf.com/global/en/performance_polymers/downloads"

    def setUp(self) -> None:
        self.result = decide(self.URL)

    def test_role_is_document_listing(self) -> None:
        self.assertEqual(self.result.url_role, URLRole.DOCUMENT_LISTING)

    def test_action_is_inspect_or_api(self) -> None:
        self.assertIn(
            self.result.next_action,
            (NextAction.INSPECT_STATIC_HTML, NextAction.API_DISCOVERY),
        )

    def test_positive_score_from_downloads(self) -> None:
        self.assertGreater(self.result.scores.url_score, 0)

    def test_download_reason_code(self) -> None:
        self.assertTrue(
            any("DOWNLOAD_PATH" in r for r in self.result.reason_codes)
        )


class Test07HashClientState(unittest.TestCase):
    """Fragment is stripped from canonical URL; preserved in debug."""

    URL = "https://plastics-rubber.basf.com/global/en/performance_polymers/downloads#%7B%220%22:%5B%5D%7D"

    def setUp(self) -> None:
        self.result = decide(self.URL)

    def test_canonical_url_has_no_fragment(self) -> None:
        self.assertNotIn("#", self.result.canonical_url)

    def test_canonical_url_is_correct(self) -> None:
        expected = "https://plastics-rubber.basf.com/global/en/performance_polymers/downloads"
        self.assertEqual(self.result.canonical_url, expected)

    def test_fragment_in_debug(self) -> None:
        # Decoded JSON-like state should be preserved in debug
        self.assertIn("fragment", self.result.debug)
        self.assertTrue(len(self.result.debug["fragment"]) > 0)

    def test_templates_match_fragment_stripped_path(self) -> None:
        for tmpl in self.result.templates:
            self.assertNotIn("#", tmpl.template)


class Test08SalesforceRoute(unittest.TestCase):
    """https://www.lgchemon.com/s/lg-grade/a0g2p00000XQEZDAA5/aacrylic-acid?language=en_US"""

    URL = "https://www.lgchemon.com/s/lg-grade/a0g2p00000XQEZDAA5/aacrylic-acid?language=en_US"

    def setUp(self) -> None:
        self.result = decide(self.URL)

    def test_long_id_classified(self) -> None:
        segs = {s["raw"]: s["kind"] for s in self.result.debug["segments"]}
        self.assertEqual(segs["a0g2p00000XQEZDAA5"], SegmentKind.LONG_ID.value)

    def test_slug_classified(self) -> None:
        segs = {s["raw"]: s["kind"] for s in self.result.debug["segments"]}
        self.assertEqual(segs["aacrylic-acid"], SegmentKind.SLUG.value)

    def test_medium_template(self) -> None:
        templates = {c.level: c.template for c in self.result.templates}
        self.assertEqual(templates["medium"], "/s/lg-grade/{long_id}/{slug}")

    def test_specific_template(self) -> None:
        templates = {c.level: c.template for c in self.result.templates}
        self.assertEqual(templates["specific"], "/s/lg-grade/{long_id}/aacrylic-acid")

    def test_english_query_param_scored(self) -> None:
        self.assertIn("ENGLISH_SIGNAL", self.result.reason_codes)

    def test_query_params_in_debug(self) -> None:
        self.assertIn("language", self.result.debug["query_params"])


class Test09AssetFile(unittest.TestCase):
    """https://example.com/assets/app.12345.js"""

    def setUp(self) -> None:
        self.result = decide("https://example.com/assets/app.12345.js")

    def test_role_is_asset(self) -> None:
        self.assertEqual(self.result.url_role, URLRole.ASSET)

    def test_action_is_reject(self) -> None:
        self.assertEqual(self.result.next_action, NextAction.REJECT)

    def test_negative_score(self) -> None:
        self.assertLess(self.result.scores.url_score, 0)


class Test10LowYieldStaticPattern(unittest.TestCase):
    """Generic HTML page + pattern showing 59/60 renders needed, 0 documents."""

    URL = "https://example.com/en/some-category/overview"

    STATS = PatternStats(
        sample_count=60,
        render_needed_count=59,
        candidate_document_count=0,
        technical_document_count=0,
    )

    def setUp(self) -> None:
        self.result = decide(self.URL, stats=self.STATS)

    def test_action_is_stop_static_get(self) -> None:
        self.assertEqual(self.result.next_action, NextAction.STOP_STATIC_GET)


class Test11TechDocOverridesLowYieldPattern(unittest.TestCase):
    """A TDS PDF must always be fetched, even when the page pattern is terrible."""

    URL = "https://example.com/documents/foo_TDS.pdf"

    STATS = PatternStats(
        sample_count=60,
        render_needed_count=59,
        candidate_document_count=0,
        technical_document_count=0,
    )

    def setUp(self) -> None:
        self.result = decide(self.URL, stats=self.STATS)

    def test_role_is_technical_document(self) -> None:
        self.assertEqual(self.result.url_role, URLRole.TECHNICAL_DOCUMENT)

    def test_action_is_fetch_document(self) -> None:
        self.assertEqual(self.result.next_action, NextAction.FETCH_DOCUMENT)


class Test12AnchorTextBonus(unittest.TestCase):
    """Generic PDF URL gets a score boost from 'Technical Data Sheet' anchor."""

    URL = "https://example.com/documents/file.pdf"

    def test_anchor_text_boosts_score(self) -> None:
        without_ctx = decide(self.URL)
        with_ctx = decide(
            self.URL,
            context=SourceContext(anchor_text="Technical Data Sheet"),
        )
        self.assertGreater(with_ctx.scores.source_score, without_ctx.scores.source_score)
        self.assertIn("SRC_ANCHOR_TEXT_TECH", with_ctx.reason_codes)


class DecisionStructureTest(unittest.TestCase):
    """Sanity-check the shape of the returned URLDecision."""

    def test_result_has_all_fields(self) -> None:
        result = decide("https://example.com/products")
        self.assertIsNotNone(result.canonical_url)
        self.assertIsNotNone(result.url_role)
        self.assertIsNotNone(result.next_action)
        self.assertIsInstance(result.templates, list)
        self.assertIsInstance(result.reason_codes, list)
        self.assertIsInstance(result.debug, dict)

    def test_final_score_is_sum(self) -> None:
        result = decide("https://example.com/products")
        expected = (
            result.scores.url_score
            + result.scores.source_score
            + result.scores.pattern_score
        )
        self.assertEqual(result.scores.final_score, expected)

    def test_empty_path(self) -> None:
        result = decide("https://example.com/")
        self.assertIsNotNone(result.url_role)

    def test_canonical_strips_fragment(self) -> None:
        result = decide("https://example.com/page#section")
        self.assertNotIn("#", result.canonical_url)

    def test_selected_template_in_templates(self) -> None:
        result = decide("https://example.com/global/en/products/12345")
        tmpl_paths = {c.template for c in result.templates}
        self.assertIn(result.selected_template, tmpl_paths)


if __name__ == "__main__":
    unittest.main()
