"""Offline proof that imported replay semantics and new DOE contracts coexist."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from tools.validate_contracts import ROOT, load, validate
from experiments.contract_smoke import run


class FrameworkContracts(unittest.TestCase):
    def test_all_public_contract_fixtures(self):
        receipt = validate()
        self.assertEqual(receipt["status"], "PASS")
        self.assertGreaterEqual(receipt["validated_documents"], 2)
        self.assertFalse(receipt["scientific_result"])

    def test_method_neutral_knowledge_editing_and_loop_masks(self):
        original = load(ROOT / "examples/doe-cell.synthetic.json")
        schema = load(ROOT / "schemas/doe-cell.schema.json")
        validator = Draft202012Validator(schema)
        for kind, family, mask in (
            ("none", "control", None),
            ("diffusion-generator", "knowledge-editing", None),
            ("recurrent-loop", "recurrent-computation", "0101"),
        ):
            doc = copy.deepcopy(original)
            doc["method"]["family"] = family
            doc["treatment"]["kind"] = kind
            doc["treatment"]["loop_mask"] = mask
            validator.validate(doc)
        doc["treatment"]["loop_mask"] = "NOT-A-LOOP-MASK"
        self.assertTrue(list(validator.iter_errors(doc)))

    def test_contract_rejects_credential_fields(self):
        schema = load(ROOT / "schemas/doe-cell.schema.json")
        doc = load(ROOT / "examples/doe-cell.synthetic.json")
        doc["execution"]["kaggle_api_token"] = "not-a-real-token"
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(doc)))

    def test_deterministic_fixture_independent_of_platform(self):
        self.assertEqual(run(17, 16), run(17, 16))
        self.assertNotEqual(run(17, 16)["values_sha256"], run(18, 16)["values_sha256"])

    def test_real_bounded_replay_produces_independent_receipts(self):
        with tempfile.TemporaryDirectory() as d:
            first = Path(d) / "first.json"
            first_sidecar = Path(d) / "first.meta.json"
            proc = subprocess.run(
                [sys.executable, "tools/run_replay.py",
                 "replays/contract-smoke.json", "--output", str(first),
                 "--metadata", str(first_sidecar)],
                cwd=ROOT, capture_output=True, text=True, timeout=40,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            data = json.loads(first.read_text())
            meta = json.loads(first_sidecar.read_text())
            self.assertEqual(data["claim"], "model_free_contract_smoke_only")
            self.assertFalse(data["scientific_result"])
            self.assertEqual(meta["replay_spec_id"], "bootstrap/contract-smoke")
            import hashlib
            encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
            self.assertEqual(meta["scientific_receipt_sha256"], hashlib.sha256(encoded).hexdigest())


if __name__ == "__main__":
    unittest.main()
