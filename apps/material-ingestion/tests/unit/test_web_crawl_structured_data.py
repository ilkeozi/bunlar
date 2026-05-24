import unittest

from material_ingestion.services.web_crawl_structured_data_service import extract_structured_data_records


class WebCrawlStructuredDataTest(unittest.TestCase):
    def test_extract_structured_data_records_parses_jsonld(self) -> None:
        html = """
        <html>
          <head>
            <script type="application/ld+json">
              {"@context":"https://schema.org","@type":"Dataset","name":"Spec Sheet"}
            </script>
          </head>
          <body></body>
        </html>
        """
        records = extract_structured_data_records(html)
        self.assertEqual(1, len(records))
        self.assertEqual("jsonld", records[0]["format"])
        self.assertEqual("Dataset", records[0]["payload"]["@type"])

    def test_extract_structured_data_records_skips_invalid_payload(self) -> None:
        html = '<script type="application/ld+json">{invalid json}</script>'
        records = extract_structured_data_records(html)
        self.assertEqual([], records)
