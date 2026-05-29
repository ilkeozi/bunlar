from __future__ import annotations

import unittest

from material_ingestion.services.url_intelligence.models import PatternStats, SourceContext
from material_ingestion.services.url_intelligence.scoring import score_pattern, score_source, score_url
from material_ingestion.services.url_intelligence.uri_parser import parse_url


class URLScoreTechDocTest(unittest.TestCase):

    def test_tech_doc_pdf_high_score(self) -> None:
        parsed = parse_url("https://example.com/tds/Product_TDS.pdf")
        score, reasons = score_url(parsed)
        self.assertGreaterEqual(score, 100)
        self.assertIn("TECH_DOC_FILE_URL", reasons)

    def test_plain_pdf_moderate_score(self) -> None:
        parsed = parse_url("https://example.com/report.pdf")
        score, reasons = score_url(parsed)
        self.assertGreaterEqual(score, 40)
        self.assertIn("DOC_FILE_URL", reasons)

    def test_download_path_bonus(self) -> None:
        parsed = parse_url("https://example.com/downloads/product-list")
        score, reasons = score_url(parsed)
        self.assertGreaterEqual(score, 60)
        self.assertTrue(any("DOWNLOAD_PATH" in r for r in reasons))

    def test_english_segment_bonus(self) -> None:
        parsed = parse_url("https://example.com/global/en/products")
        score, reasons = score_url(parsed)
        self.assertIn("ENGLISH_SIGNAL", reasons)

    def test_english_query_param_bonus(self) -> None:
        parsed = parse_url("https://example.com/page?language=en_US")
        score, reasons = score_url(parsed)
        self.assertIn("ENGLISH_SIGNAL", reasons)

    def test_product_path_bonus(self) -> None:
        parsed = parse_url("https://example.com/products/polymer-series")
        score, reasons = score_url(parsed)
        self.assertIn("PRODUCT_PATH", reasons)


class URLScoreDownloadPathTest(unittest.TestCase):
    """DOWNLOAD_PATH reason code must be a stable identifier regardless of the matched segment."""

    def _reasons(self, url: str) -> list[str]:
        return score_url(parse_url(url))[1]

    def test_downloads_segment_gives_stable_reason(self) -> None:
        reasons = self._reasons("https://example.com/downloads/product-list")
        self.assertIn("DOWNLOAD_PATH", reasons)
        self.assertFalse(any(r.startswith("DOWNLOAD_PATH:") for r in reasons))

    def test_download_center_gives_stable_reason(self) -> None:
        reasons = self._reasons("https://example.com/download-center/")
        self.assertIn("DOWNLOAD_PATH", reasons)
        self.assertFalse(any(r.startswith("DOWNLOAD_PATH:") for r in reasons))

    def test_download_center_html_gives_stable_reason(self) -> None:
        reasons = self._reasons("https://example.com/download_center.html")
        self.assertIn("DOWNLOAD_PATH", reasons)

    def test_apk_download_gives_stable_reason(self) -> None:
        reasons = self._reasons("https://example.com/apk-download/")
        self.assertIn("DOWNLOAD_PATH", reasons)
        self.assertFalse(any(r.startswith("DOWNLOAD_PATH:") for r in reasons))

    def test_reason_summary_aggregates_under_single_key(self) -> None:
        # Simulate what _allocate does: collect reason_codes from multiple URLs
        from material_ingestion.services.url_intelligence.decision import decide
        urls = [
            "https://a.com/downloads/",
            "https://b.com/download-center/",
            "https://c.com/downloadcenter/",
        ]
        summary: dict[str, int] = {}
        for url in urls:
            for rc in decide(url).reason_codes:
                summary[rc] = summary.get(rc, 0) + 1
        # All three must aggregate under the single key DOWNLOAD_PATH
        self.assertIn("DOWNLOAD_PATH", summary)
        self.assertEqual(summary["DOWNLOAD_PATH"], 3)
        self.assertFalse(any(k.startswith("DOWNLOAD_PATH:") for k in summary))


class URLScoreNoisePenaltyTest(unittest.TestCase):

    def test_legal_path_heavy_penalty(self) -> None:
        parsed = parse_url("https://example.com/legal/terms-and-conditions.pdf")
        score, reasons = score_url(parsed)
        self.assertIn("LEGAL_NOISE", reasons)
        # Even though it's a PDF, the legal penalty must dominate
        self.assertLess(score, 0)

    def test_career_path_penalty(self) -> None:
        parsed = parse_url("https://example.com/careers/senior-engineer")
        score, reasons = score_url(parsed)
        self.assertIn("CAREER_NOISE", reasons)
        self.assertLess(score, 0)

    def test_press_path_penalty(self) -> None:
        parsed = parse_url("https://example.com/news/press-release-2024")
        score, reasons = score_url(parsed)
        self.assertIn("PRESS_NOISE", reasons)

    def test_asset_file_penalty(self) -> None:
        parsed = parse_url("https://example.com/assets/app.js")
        score, reasons = score_url(parsed)
        self.assertIn("ASSET_FILE_URL", reasons)
        self.assertLess(score, 0)


class SourceScoreTest(unittest.TestCase):

    def test_sitemap_bonus(self) -> None:
        ctx = SourceContext(came_from_sitemap=True)
        score, reasons = score_source(ctx)
        self.assertGreater(score, 0)
        self.assertIn("SRC_FROM_SITEMAP", reasons)

    def test_sitemap_source_type_bonus(self) -> None:
        ctx = SourceContext(source_type="sitemap")
        score, reasons = score_source(ctx)
        self.assertIn("SRC_FROM_SITEMAP", reasons)

    def test_en_hreflang_bonus(self) -> None:
        ctx = SourceContext(has_english_hreflang=True)
        score, reasons = score_source(ctx)
        self.assertIn("SRC_EN_HREFLANG", reasons)

    def test_doc_listing_source_page_bonus(self) -> None:
        ctx = SourceContext(source_page_role="document_listing")
        score, reasons = score_source(ctx)
        self.assertIn("SRC_PAGE_IS_DOC_LISTING", reasons)
        self.assertGreaterEqual(score, 30)

    def test_anchor_text_tds_bonus(self) -> None:
        ctx = SourceContext(anchor_text="Technical Data Sheet")
        score, reasons = score_source(ctx)
        self.assertIn("SRC_ANCHOR_TEXT_TECH", reasons)

    def test_anchor_text_sds_bonus(self) -> None:
        ctx = SourceContext(anchor_text="Download SDS")
        score, reasons = score_source(ctx)
        self.assertIn("SRC_ANCHOR_TEXT_TECH", reasons)

    def test_navigation_heavy_penalty(self) -> None:
        ctx = SourceContext(source_is_navigation_heavy=True)
        score, reasons = score_source(ctx)
        self.assertLess(score, 0)
        self.assertIn("SRC_NAVIGATION_HEAVY", reasons)

    def test_empty_anchor_no_bonus(self) -> None:
        ctx = SourceContext(anchor_text="")
        score, reasons = score_source(ctx)
        self.assertNotIn("SRC_ANCHOR_TEXT_TECH", reasons)


class PatternScoreTest(unittest.TestCase):

    def test_none_returns_zero(self) -> None:
        score, reasons, details = score_pattern(None)
        self.assertEqual(score, 0)
        self.assertEqual(reasons, [])
        self.assertEqual(details, {})

    def test_zero_samples_returns_zero(self) -> None:
        score, reasons, details = score_pattern(PatternStats(sample_count=0))
        self.assertEqual(score, 0)
        self.assertEqual(details, {})

    def test_high_tech_doc_yield_positive(self) -> None:
        stats = PatternStats(sample_count=50, technical_document_count=40)
        score, reasons, _ = score_pattern(stats)
        self.assertGreater(score, 0)
        self.assertIn("PATTERN_TECH_DOC_YIELD", reasons)

    def test_high_render_rate_negative(self) -> None:
        stats = PatternStats(sample_count=60, render_needed_count=58)
        score, reasons, _ = score_pattern(stats)
        self.assertLess(score, 0)
        self.assertIn("PATTERN_RENDER_HEAVY", reasons)

    def test_low_confidence_applied_as_weak_modifier(self) -> None:
        stats_low = PatternStats(sample_count=5, technical_document_count=5)
        stats_high = PatternStats(sample_count=50, technical_document_count=50)
        score_low, *_ = score_pattern(stats_low)
        score_high, *_ = score_pattern(stats_high)
        self.assertLess(score_low, score_high)

    def test_smoothing_avoids_zero_yield(self) -> None:
        stats = PatternStats(sample_count=30, technical_document_count=0)
        score, *_ = score_pattern(stats)
        self.assertIsInstance(score, int)

    # --- Stable reason code tests ---

    def test_high_confidence_reason_is_stable(self) -> None:
        _, reasons, details = score_pattern(PatternStats(sample_count=50))
        self.assertIn("PATTERN_HIGH_CONFIDENCE", reasons)
        self.assertFalse(any("_N" in r for r in reasons), f"dynamic suffix found: {reasons}")
        self.assertEqual(details["confidence"], "high")
        self.assertEqual(details["sample_count"], 50)

    def test_low_confidence_reason_is_stable(self) -> None:
        _, reasons, details = score_pattern(PatternStats(sample_count=5))
        self.assertIn("PATTERN_LOW_CONFIDENCE", reasons)
        self.assertFalse(any("_N" in r for r in reasons), f"dynamic suffix found: {reasons}")
        self.assertEqual(details["confidence"], "low")

    def test_medium_confidence_reason_is_stable(self) -> None:
        _, reasons, details = score_pattern(PatternStats(sample_count=46))
        self.assertIn("PATTERN_MEDIUM_CONFIDENCE", reasons)
        self.assertFalse(any("_N" in r for r in reasons), f"dynamic suffix found: {reasons}")
        self.assertEqual(details["confidence"], "medium")

    def test_render_heavy_reason_is_stable(self) -> None:
        stats = PatternStats(sample_count=60, render_needed_count=58)
        _, reasons, _ = score_pattern(stats)
        self.assertIn("PATTERN_RENDER_HEAVY", reasons)
        self.assertFalse(any("_0." in r for r in reasons), f"float suffix found: {reasons}")

    def test_slow_reason_is_stable(self) -> None:
        stats = PatternStats(sample_count=50, avg_total_ms=8000.0)
        _, reasons, details = score_pattern(stats)
        self.assertIn("PATTERN_SLOW", reasons)
        self.assertFalse(any("MS" in r for r in reasons), f"MS suffix found: {reasons}")
        self.assertEqual(details["avg_total_ms"], 8000.0)

    def test_tech_doc_yield_reason_is_stable(self) -> None:
        stats = PatternStats(sample_count=50, technical_document_count=40)
        _, reasons, _ = score_pattern(stats)
        self.assertIn("PATTERN_TECH_DOC_YIELD", reasons)
        self.assertFalse(any(r.startswith("PATTERN_TECH_DOC_YIELD_") for r in reasons),
                         f"dynamic suffix found: {reasons}")

    def test_noisy_reason_is_stable(self) -> None:
        stats = PatternStats(sample_count=60, noise_count=50)
        _, reasons, _ = score_pattern(stats)
        self.assertIn("PATTERN_NOISY", reasons)
        self.assertFalse(any("_0." in r for r in reasons), f"float suffix found: {reasons}")

    def test_details_contains_numeric_fields(self) -> None:
        stats = PatternStats(
            sample_count=50,
            render_needed_count=30,
            technical_document_count=5,
            candidate_document_count=10,
            avg_total_ms=1200.0,
        )
        _, _, details = score_pattern(stats)
        self.assertEqual(details["sample_count"], 50)
        self.assertIn("render_needed_rate", details)
        self.assertIn("technical_document_yield", details)
        self.assertIn("candidate_document_yield", details)
        self.assertIn("noise_rate", details)
        self.assertEqual(details["technical_document_count"], 5)
        self.assertEqual(details["candidate_document_count"], 10)
        self.assertEqual(details["avg_total_ms"], 1200.0)


if __name__ == "__main__":
    unittest.main()
