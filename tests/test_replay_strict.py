"""Adversarial source-only replay admission tests. No model or network I/O."""
import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

from tools.replay_strict import (
    MAX_CAPTURE_BYTES, MAX_JSON_BYTES, bounded_run, strict_json,
    validate_source_only_receipt,
)
from tools.run_replay import ROOT, load_spec


class StrictReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid = json.loads((ROOT / "replays/contract-smoke.json").read_text())

    def load(self, raw: bytes):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "replay.json"
            path.write_bytes(raw)
            return load_spec(path)

    def test_valid_source_only_replay(self):
        value = self.load(json.dumps(self.valid).encode())
        self.assertEqual(value["module"], "experiments.contract_smoke")
        self.assertEqual(value["resource_class"], "cpu")

    def test_hostile_spec_fields_fail_closed(self):
        cases = {
            "gpu_without_admission": ("resource_class", "gpu"),
            "paid_venue": ("resource_class", "kaggle-paid"),
            "foreign_environment": ("environment_ref", "../env.json"),
            "missing_environment": ("environment_ref", "environments/unknown.json"),
            "wrong_module": ("module", "experiments.unknown"),
            "module_outside_package": ("module", "os"),
            "boolean_timeout": ("timeout_seconds", True),
            "too_long_timeout": ("timeout_seconds", 7200),
            "zero_timeout": ("timeout_seconds", 0),
            "nonfinite_argument": ("arguments", {"seed": math.inf}),
            "boolean_argument": ("arguments", {"seed": True}),
            "null_argument": ("arguments", {"seed": None}),
            "unsafe_argument_key": ("arguments", {"--seed": 17}),
            "oversized_integer": ("arguments", {"seed": 2 ** 70}),
        }
        for label, (key, value) in cases.items():
            with self.subTest(label=label):
                data = copy.deepcopy(self.valid)
                data[key] = value
                # Serialize Infinity deliberately as a nonstandard JSON token.
                with self.assertRaises((ValueError, TypeError)):
                    self.load(json.dumps(data, allow_nan=True).encode())
        changed = dict(self.valid)
        changed["unknown"] = {"secrets": "not-a-secret"}
        with self.assertRaises(ValueError):
            self.load(json.dumps(changed).encode())

    def test_rejects_ambiguous_and_large_json(self):
        good = json.dumps(self.valid)
        samples = {
            "duplicate_root_key": good.replace('"module":', '"module": "experiments.invalid", "module":', 1),
            "duplicate_nested_key": good.replace('"seed":', '"seed": 0, "seed":', 1),
            "nonfinite_constant": good.replace('"seed": 17', '"seed": NaN'),
            "numeric_overflow": good.replace('"seed": 17', '"seed": 1e999'),
            "trailing_root_object": good + ' {"module":"experiments.contract_smoke"}',
            "too_many_bytes": good + (" " * MAX_JSON_BYTES),
        }
        for name, sample in samples.items():
            with self.subTest(name=name), self.assertRaises((ValueError, json.JSONDecodeError)):
                self.load(sample.encode())

    def test_receipt_semantics_are_not_inferred_from_truthiness(self):
        valid = {
            "claim": "model_free_contract_smoke_only",
            "model_loaded": False,
            "scientific_result": False,
        }
        validate_source_only_receipt(valid)
        for key, value in [
            ("model_loaded", "false"),
            ("scientific_result", "false"),
            ("claim", "scientifically_valid"),
            ("scientific_result", True),
        ]:
            with self.subTest(key=key, value=value):
                mutated = dict(valid)
                mutated[key] = value
                with self.assertRaises(ValueError):
                    validate_source_only_receipt(mutated)

    def test_receipt_json_rejects_duplicate_or_nonfinite(self):
        for raw in [
            b'{"model_loaded":false,"model_loaded":true}',
            b'{"claim":"model_free_contract_smoke_only","scientific_result":NaN}',
            b'{"scientific_result":1e999}',
            b'{"claim":"a"}{"claim":"b"}',
        ]:
            with self.subTest(raw=raw), self.assertRaises((ValueError, json.JSONDecodeError)):
                strict_json(raw)

    def test_bounded_child_output_and_timeout(self):
        command = [sys.executable, "-c", "print('x' * (2**20 + 10))"]
        with self.assertRaises(ValueError):
            bounded_run(command, ROOT, 5)
        with self.assertRaises(TimeoutError):
            bounded_run([sys.executable, "-c", "import time;time.sleep(3)"], ROOT, 1)
        okay = bounded_run([sys.executable, "-c", "print('ok')"], ROOT, 5)
        self.assertEqual(okay.returncode, 0)
        self.assertEqual(okay.stdout.strip(), b"ok")


if __name__ == "__main__":
    unittest.main()
