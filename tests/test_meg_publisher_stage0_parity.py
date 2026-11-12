"""Independent CounterFact recipe comparison source-only controls."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import verify_meg_stage0_publisher as m
from meg_reconstruct_stage0 import make_artifacts


class PublisherStage0ParityTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.dumps([{"a":"one"},{"a":"two"}]).encode()
        self.output, _ = make_artifacts(mode="counterfact-ids", input_data=self.raw)

    def test_byte_identical_reconstruction(self):
        report = m.compare(self.raw, self.output)
        self.assertTrue(report["byte_equal"])
        self.assertTrue(report["semantic_equal"])
        self.assertEqual(report["result"], "MATCHED_BYTES")
        self.assertFalse(report["scientific_meg_results_reproduced"])

    def test_semantic_equivalence_does_not_claim_byte_identity(self):
        minimized = json.dumps(json.loads(self.output), separators=(",", ":")).encode()
        report = m.compare(self.raw, minimized)
        self.assertTrue(report["semantic_equal"])
        self.assertFalse(report["byte_equal"])
        self.assertEqual(report["result"], "MATCHED_SEMANTICS_ONLY")

    def test_wrong_original_values_report_divergence(self):
        altered = json.loads(self.output)
        altered[0]["id"] = 42
        report = m.compare(self.raw, json.dumps(altered).encode())
        self.assertFalse(report["semantic_equal"])
        self.assertEqual(report["result"], "DIVERGED")

    def test_source_archive_identifiers_are_fixed(self):
        self.assertEqual(len(m.OUTER_SHA),64)
        self.assertEqual(len(m.INNER_SHA),64)
        self.assertEqual(len(m.RAW_SHA),64)
        self.assertEqual(len(m.PUBLISHED_SHA),64)


if __name__ == "__main__":
    unittest.main()
