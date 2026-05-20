import json
import unittest

from material_ingestion.cli import build_pipeline


class _Args:
    source = "uns"
    input = None
    compact = True


class PipelineTest(unittest.TestCase):
    def test_runs_uns_pipeline(self) -> None:
        pipeline = build_pipeline(_Args())
        records, output = pipeline.run()

        self.assertEqual(1, len(records))
        self.assertEqual("uns", records[0].source)
        self.assertIn("match_key", records[0].metadata)

        parsed = json.loads(output)
        self.assertEqual("G10200", parsed[0]["material_id"])


if __name__ == "__main__":
    unittest.main()

