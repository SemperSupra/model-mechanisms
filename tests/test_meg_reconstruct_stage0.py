"""Source-only method reconstruction; no author checkpoint or dataset downloaded."""
import copy
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools/meg_reconstruct_stage0.py"
spec = importlib.util.spec_from_file_location("meg_stage0", SRC)
method = importlib.util.module_from_spec(spec)
spec.loader.exec_module(method)


class StageZeroMethodContracts(unittest.TestCase):
    def setUp(self):
        self.raw = [
            {"subject": "Synthetic person A", "requested_rewrite": {"target_new": "x"}},
            {"subject": "Synthetic person B", "id": 999},
            {"subject": "Synthetic person C", "fake_label": -7},
        ]
        self.data = json.dumps(self.raw, ensure_ascii=True).encode()

    def test_counterfact_order_and_source_invariance(self):
        original = copy.deepcopy(self.raw)
        result = method.reconstruct_counterfact_ids(self.raw)
        self.assertEqual([x["id"] for x in result], [0, 1, 2])
        self.assertEqual(result[1]["subject"], "Synthetic person B")
        self.assertEqual(original, self.raw)
        out, receipt = method.make_artifacts(mode="counterfact-ids", input_data=self.data)
        self.assertEqual(receipt["input_sha256"], method.sha256(self.data))
        self.assertEqual(receipt["output_sha256"], method.sha256(out))
        self.assertIsNone(receipt["random_seed"])
        self.assertEqual(json.loads(out), result)
        self.assertEqual(receipt["claim"], "NOT_AUTHOR_IDENTICAL")

    def test_familiarity_seed_controls_randomness(self):
        existing = copy.deepcopy(self.raw)
        a, rec_a = method.make_artifacts(mode="familiarity-labels", input_data=self.data, seed=19)
        b, rec_b = method.make_artifacts(mode="familiarity-labels", input_data=self.data, seed=19)
        self.assertEqual(a, b)
        self.assertEqual(rec_a, rec_b)
        self.assertEqual(self.raw, existing)
        expected_rng = random.Random(19)
        expected = [expected_rng.randint(0, 9) for _ in range(3)]
        actual = [x["fake_label"] for x in json.loads(a)]
        self.assertEqual(actual, expected)
        self.assertTrue(all(0 <= x <= 9 for x in actual))
        self.assertFalse(rec_a["original_random_state_recovered"])
        self.assertFalse(rec_a["scientific_reproduction_complete"])

    def test_train_subset_is_bounded_source_order(self):
        out, receipt = method.make_artifacts(
            mode="familiarity-labels", input_data=self.data, seed=17, count=2
        )
        data = json.loads(out)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["subject"], "Synthetic person A")
        self.assertEqual(data[1]["subject"], "Synthetic person B")
        self.assertEqual(receipt["output_records"], 2)
        self.assertEqual(receipt["count_limit"], 2)

    def test_missing_seed_invalid_rng_and_mode_fail(self):
        for kwargs in (
            {"mode": "familiarity-labels"},
            {"mode": "familiarity-labels", "seed": -1},
            {"mode": "familiarity-labels", "seed": True},
            {"mode": "counterfact-ids", "seed": 7},
            {"mode": "unreviewed"},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    method.make_artifacts(input_data=self.data, **kwargs)

    def test_invalid_source_structure_rejected(self):
        for invalid in (b'{"not":"list"}', b"[1,2,3]", b"false"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                method.make_artifacts(mode="counterfact-ids", input_data=invalid)

    def test_new_output_only_and_readable_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inp, out, receipt = (root / "raw.json", root / "derived.json", root / "receipt.json")
            inp.write_bytes(self.data)
            cmd = [
                sys.executable, str(SRC), "--mode", "familiarity-labels",
                "--input", str(inp), "--output", str(out), "--receipt", str(receipt),
                "--seed", "29",
            ]
            first = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            self.assertEqual(first.returncode, 0, first.stderr)
            meta = json.loads(receipt.read_text())
            self.assertEqual(meta["output_sha256"], method.sha256(out.read_bytes()))
            self.assertEqual(meta["status"], "RECONSTRUCTED_DERIVATIVE")
            second = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("OUTPUT_PATHS_MUST_BE_DISTINCT_AND_NEW", second.stderr)

    def test_same_input_hash_and_seeds_are_explicit(self):
        out, receipt = method.make_artifacts(
            mode="familiarity-labels", input_data=self.data, seed=81
        )
        self.assertEqual(receipt["upstream_meg_revision"],
                         "9fa8ae10cf33c82dd2200057f70dfcb73388cd74")
        self.assertFalse(receipt["third_party_code_executed"])
        self.assertFalse(receipt["author_original_weights_recovered"])
        self.assertNotEqual(
            out, method.make_artifacts(mode="familiarity-labels",
                                       input_data=self.data, seed=82)[0]
        )


if __name__ == "__main__":
    unittest.main()
