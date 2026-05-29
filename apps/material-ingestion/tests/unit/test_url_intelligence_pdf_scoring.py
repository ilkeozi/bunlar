"""Tests for PDF priority ordering and legal/brochure classification (Issue 1)."""
from __future__ import annotations

import unittest

from material_ingestion.services.url_intelligence.decision import decide
from material_ingestion.services.url_intelligence.models import (
    NextAction,
    SourceContext,
    URLRole,
)
from material_ingestion.services.url_intelligence.scoring import score_url
from material_ingestion.services.url_intelligence.uri_parser import parse_url


class TestTechDocBeatsGenericPdf(unittest.TestCase):

    def test_tds_pdf_beats_brochure_pdf(self) -> None:
        tds_score, tds_reasons = score_url(parse_url("https://example.com/files/Product_TDS.pdf"))
        brochure_score, _ = score_url(parse_url("https://example.com/files/brochure.pdf"))
        self.assertIn("TECH_DOC_FILE_URL", tds_reasons)
        self.assertGreater(tds_score, brochure_score)

    def test_safety_data_sheet_beats_brochure(self) -> None:
        sds_score, sds_reasons = score_url(parse_url("https://example.com/files/Safety_Data_Sheet.pdf"))
        brochure_score, _ = score_url(parse_url("https://example.com/files/product-brochure.pdf"))
        self.assertIn("TECH_DOC_FILE_URL", sds_reasons)
        self.assertGreater(sds_score, brochure_score)

    def test_tech_doc_score_at_least_100(self) -> None:
        score, _ = score_url(parse_url("https://example.com/tds/polymer_TDS.pdf"))
        self.assertGreaterEqual(score, 100)

    def test_brochure_pdf_score_well_below_tech_doc(self) -> None:
        tds_score, _ = score_url(parse_url("https://example.com/Product_TDS.pdf"))
        brochure_score, _ = score_url(parse_url("https://example.com/brochure.pdf"))
        self.assertGreater(tds_score - brochure_score, 50)


class TestBrochurePdfPenalty(unittest.TestCase):

    def test_brochure_filename_penalty_applied(self) -> None:
        score, reasons = score_url(parse_url("https://example.com/product-brochure.pdf"))
        self.assertIn("BROCHURE_FILENAME", reasons)

    def test_flyer_filename_penalty_applied(self) -> None:
        score, reasons = score_url(parse_url("https://example.com/series-flyer.pdf"))
        self.assertIn("BROCHURE_FILENAME", reasons)

    def test_leaflet_filename_penalty_applied(self) -> None:
        score, reasons = score_url(parse_url("https://example.com/leaflet.pdf"))
        self.assertIn("BROCHURE_FILENAME", reasons)

    def test_brochure_pdf_score_reduced(self) -> None:
        plain_score, _ = score_url(parse_url("https://example.com/product.pdf"))
        brochure_score, _ = score_url(parse_url("https://example.com/product-brochure.pdf"))
        self.assertLess(brochure_score, plain_score)


class TestLegalDocFilenameRejected(unittest.TestCase):

    def test_general_conditions_footer_is_noise(self) -> None:
        result = decide("https://example.com/downloads/General-Conditions_Footer.pdf")
        self.assertEqual(result.url_role, URLRole.NOISE)
        self.assertEqual(result.next_action, NextAction.REJECT)

    def test_conditions_of_sale_is_noise(self) -> None:
        result = decide("https://example.com/downloads/Conditions_of_Sale.pdf")
        self.assertEqual(result.url_role, URLRole.NOISE)
        self.assertEqual(result.next_action, NextAction.REJECT)

    def test_gtc_pdf_is_noise(self) -> None:
        result = decide("https://example.com/docs/GTC.pdf")
        self.assertEqual(result.url_role, URLRole.NOISE)
        self.assertEqual(result.next_action, NextAction.REJECT)

    def test_agb_pdf_is_noise(self) -> None:
        result = decide("https://example.com/docs/AGB.pdf")
        self.assertEqual(result.url_role, URLRole.NOISE)
        self.assertEqual(result.next_action, NextAction.REJECT)

    def test_legal_doc_filename_penalty_in_score(self) -> None:
        score, reasons = score_url(parse_url("https://example.com/Conditions_of_Sale.pdf"))
        self.assertIn("LEGAL_DOC_FILENAME", reasons)
        # Score should be negative: DOC_FILE_URL(40) - LEGAL_DOC_FILENAME(80) = -40
        self.assertLess(score, 0)


class TestGenericBrochureAction(unittest.TestCase):

    def test_brochure_pdf_deferred_without_strong_context(self) -> None:
        result = decide("https://example.com/product-brochure.pdf")
        # Score: 40 (DOC) - 30 (BROCHURE) = 10 < 50 → DEFER
        self.assertEqual(result.next_action, NextAction.DEFER)
        self.assertEqual(result.url_role, URLRole.DOCUMENT)

    def test_brochure_pdf_fetched_with_strong_doc_listing_source(self) -> None:
        ctx = SourceContext(
            source_page_role="document_listing",
            source_page_produced_document_candidates=True,
        )
        result = decide("https://example.com/product-brochure.pdf", context=ctx)
        # Score: 40 - 30 + 30 (doc_listing) + 20 (produced_docs) = 60 >= 50 → FETCH
        self.assertEqual(result.next_action, NextAction.FETCH_DOCUMENT)

    def test_plain_pdf_with_good_score_fetched(self) -> None:
        ctx = SourceContext(came_from_sitemap=True, source_page_produced_document_candidates=True)
        result = decide("https://example.com/product-data.pdf", context=ctx)
        # Score: 40 (DOC) + 15 (sitemap) + 20 (produced_docs) = 75 >= 50 → FETCH
        self.assertEqual(result.next_action, NextAction.FETCH_DOCUMENT)

    def test_tech_doc_always_fetched_regardless_of_score(self) -> None:
        result = decide("https://example.com/Product_TDS.pdf")
        self.assertEqual(result.next_action, NextAction.FETCH_DOCUMENT)
        self.assertEqual(result.url_role, URLRole.TECHNICAL_DOCUMENT)

    def test_plain_pdf_no_context_score_based(self) -> None:
        # "report.pdf" — no product/download/resource tokens → score=40 < 50 → DEFER
        result = decide("https://example.com/report.pdf")
        self.assertEqual(result.next_action, NextAction.DEFER)

    def test_plain_pdf_with_product_path_and_sitemap_fetched(self) -> None:
        # products/ path (+25) + sitemap (+15) + DOC_FILE_URL (40) = 80 >= 50 → FETCH
        ctx = SourceContext(came_from_sitemap=True)
        result = decide("https://example.com/products/polymer-a-data.pdf", context=ctx)
        self.assertEqual(result.next_action, NextAction.FETCH_DOCUMENT)


class TestBASFStyleDAMUrls(unittest.TestCase):
    """Generic PDFs under deep resource/product paths must not outrank TDS/SDS files."""

    _BASE = "https://www.basf.com/global/documents/en/products/polymers"

    def test_generic_pdf_url_score_capped(self) -> None:
        # DOC(40) + RESOURCE(40) + PRODUCT(25) + ENGLISH(10) = 115 raw → capped at 45
        score, reasons = score_url(parse_url(f"{self._BASE}/polymer-A-overview.pdf"))
        self.assertLessEqual(score, 45)
        self.assertIn("DOC_URL_SCORE_CAPPED", reasons)

    def test_tds_pdf_at_same_path_not_capped(self) -> None:
        score, reasons = score_url(parse_url(f"{self._BASE}/polymer-A-TDS.pdf"))
        self.assertGreaterEqual(score, 100)
        self.assertIn("TECH_DOC_FILE_URL", reasons)
        self.assertNotIn("DOC_URL_SCORE_CAPPED", reasons)

    def test_tds_outranks_generic_pdf_at_same_dam_path(self) -> None:
        tds_score, _ = score_url(parse_url(f"{self._BASE}/polymer-A-TDS.pdf"))
        gen_score, _ = score_url(parse_url(f"{self._BASE}/polymer-A-overview.pdf"))
        self.assertGreater(tds_score, gen_score)

    def test_brochure_pdf_at_dam_path_capped_lower(self) -> None:
        score, reasons = score_url(parse_url(f"{self._BASE}/polymer-A-brochure.pdf"))
        self.assertLessEqual(score, 30)
        self.assertIn("BROCHURE_FILENAME", reasons)
        self.assertIn("DOC_URL_SCORE_CAPPED", reasons)

    def test_generic_pdf_needs_source_context_to_reach_fetch(self) -> None:
        # url_score capped at 45 < 50 → DEFER without source context
        result = decide(f"{self._BASE}/polymer-A-overview.pdf")
        self.assertEqual(result.next_action, NextAction.DEFER)

    def test_generic_pdf_fetched_with_strong_source_context(self) -> None:
        ctx = SourceContext(
            source_page_role="document_listing",
            source_page_produced_document_candidates=True,
        )
        result = decide(f"{self._BASE}/polymer-A-overview.pdf", context=ctx)
        # url_score=45 + source_score(30+20)=50 → final=95 ≥ 50 → FETCH
        self.assertEqual(result.next_action, NextAction.FETCH_DOCUMENT)

    def test_terms_pdf_rejected_despite_deep_product_path(self) -> None:
        result = decide(f"{self._BASE}/Terms_and_Conditions.pdf")
        self.assertEqual(result.url_role, URLRole.NOISE)
        self.assertEqual(result.next_action, NextAction.REJECT)

    def test_sales_pdf_rejected(self) -> None:
        result = decide(f"{self._BASE}/General_Sales_Conditions.pdf")
        self.assertEqual(result.url_role, URLRole.NOISE)
        self.assertEqual(result.next_action, NextAction.REJECT)


if __name__ == "__main__":
    unittest.main()
