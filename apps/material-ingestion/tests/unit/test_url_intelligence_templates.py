from __future__ import annotations

import unittest

from material_ingestion.services.url_intelligence.uri_parser import parse_url
from material_ingestion.services.url_intelligence.template_inference import infer_templates


def _templates_by_level(url: str) -> dict[str, str]:
    parsed = parse_url(url)
    candidates = infer_templates(parsed)
    return {c.level: c.template for c in candidates}


class NumericProductRouteTemplateTest(unittest.TestCase):
    """https://products.example.com/global/en/ci/30036817"""

    URL = "https://products.example.com/global/en/ci/30036817"

    def setUp(self) -> None:
        self.templates = _templates_by_level(self.URL)

    def test_exact_template(self) -> None:
        self.assertEqual(self.templates["exact"], "/global/en/ci/30036817")

    def test_specific_template(self) -> None:
        self.assertEqual(self.templates["specific"], "/global/en/ci/{numeric_id}")

    def test_medium_template(self) -> None:
        self.assertEqual(self.templates["medium"], "/global/{language}/ci/{numeric_id}")

    def test_ci_not_replaced(self) -> None:
        # ci must stay as a literal in all templates
        for tmpl in self.templates.values():
            self.assertIn("ci", tmpl)

    def test_deduplicated(self) -> None:
        # All three levels must be distinct
        self.assertEqual(len(set(self.templates.values())), len(self.templates))


class SalesforceRouteTemplateTest(unittest.TestCase):
    """https://www.example.com/s/lg-grade/a0g2p00000XQEZDAA5/aacrylic-acid"""

    URL = "https://www.example.com/s/lg-grade/a0g2p00000XQEZDAA5/aacrylic-acid?language=en_US"

    def setUp(self) -> None:
        self.templates = _templates_by_level(self.URL)

    def test_exact_template(self) -> None:
        self.assertEqual(
            self.templates["exact"],
            "/s/lg-grade/a0g2p00000XQEZDAA5/aacrylic-acid",
        )

    def test_specific_template(self) -> None:
        self.assertEqual(
            self.templates["specific"],
            "/s/lg-grade/{long_id}/aacrylic-acid",
        )

    def test_medium_template(self) -> None:
        self.assertEqual(
            self.templates["medium"],
            "/s/lg-grade/{long_id}/{slug}",
        )

    def test_lg_grade_preserved_in_specific(self) -> None:
        self.assertIn("lg-grade", self.templates["specific"])

    def test_lg_grade_preserved_in_medium(self) -> None:
        self.assertIn("lg-grade", self.templates["medium"])


class TechnicalPDFTemplateTest(unittest.TestCase):
    """https://chemicals.example.com/global/documents/tds-sheets/Palatinol_DOTP_TDS_202305.pdf"""

    URL = "https://chemicals.example.com/global/documents/tds-sheets/Palatinol_DOTP_TDS_202305.pdf"

    def setUp(self) -> None:
        self.templates = _templates_by_level(self.URL)

    def test_exact_template(self) -> None:
        self.assertIn("Palatinol_DOTP_TDS_202305.pdf", self.templates["exact"])

    def test_specific_replaces_file(self) -> None:
        self.assertIn("{technical_document_file}", self.templates["specific"])

    def test_specific_preserves_folder(self) -> None:
        self.assertIn("tds-sheets", self.templates["specific"])


class NoLanguageRouteTemplateTest(unittest.TestCase):
    """When there is no language segment, specific and medium may converge."""

    URL = "https://example.com/products/12345"

    def setUp(self) -> None:
        self.templates = _templates_by_level(self.URL)

    def test_specific_replaces_numeric_id(self) -> None:
        self.assertIn("{numeric_id}", self.templates["specific"])

    def test_no_language_placeholder(self) -> None:
        for tmpl in self.templates.values():
            self.assertNotIn("{language}", tmpl)


class UUIDRouteTemplateTest(unittest.TestCase):

    URL = "https://example.com/items/550e8400-e29b-41d4-a716-446655440000/detail"

    def setUp(self) -> None:
        self.templates = _templates_by_level(self.URL)

    def test_specific_replaces_uuid(self) -> None:
        self.assertIn("{uuid}", self.templates["specific"])

    def test_detail_preserved(self) -> None:
        self.assertIn("detail", self.templates["specific"])


class AssetFileTemplateTest(unittest.TestCase):

    URL = "https://example.com/assets/app.12345.js"

    def setUp(self) -> None:
        self.templates = _templates_by_level(self.URL)

    def test_specific_replaces_asset(self) -> None:
        self.assertIn("{asset_file}", self.templates["specific"])


class FragmentStrippedFromTemplateTest(unittest.TestCase):
    """Fragment must not appear in templates."""

    URL = "https://example.com/downloads#section1"

    def setUp(self) -> None:
        self.templates = _templates_by_level(self.URL)

    def test_no_hash_in_templates(self) -> None:
        for tmpl in self.templates.values():
            self.assertNotIn("#", tmpl)


if __name__ == "__main__":
    unittest.main()
