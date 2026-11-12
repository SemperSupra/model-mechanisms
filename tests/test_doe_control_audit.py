"""Falsification tests for cross-method Design of Experiments comparison plans."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "core/doe/audit_controls.py"
spec = importlib.util.spec_from_file_location("audit_controls", SRC)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def reference():
    c = json.loads((ROOT / "examples/doe-cell.synthetic.json").read_text())
    c["cell_id"] = "control"
    c["control"]["comparator_cell_id"] = None
    return c


def pair():
    base = reference()
    candidate = copy.deepcopy(base)
    candidate["cell_id"] = "diffusion"
    candidate["method"]["family"] = "knowledge-editing"
    candidate["method"]["implementation"] = "synthetic-diffusion-fixture"
    candidate["treatment"]["kind"] = "diffusion-generator"
    candidate["control"]["comparator_cell_id"] = "control"
    return base, candidate


class MatchedDesignTests(unittest.TestCase):
    def test_baseline_only_and_matched_pair_pass(self):
        self.assertEqual(audit.validate_cells([reference()])["cell_count"], 1)
        report = audit.validate_cells(list(pair()))
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["paired_treatment_count"], 1)
        self.assertIn("No experimental outcome measured", report["claims"])

    def test_order_independent_and_rep_separated(self):
        baseline, treatment = pair()
        audit.validate_cells([treatment, baseline])
        repeat = copy.deepcopy(treatment)
        reference2 = copy.deepcopy(baseline)
        for x in (reference2, repeat):
            x["rep_id"] = 1
            x["execution"]["seed"] = 89
        self.assertEqual(audit.validate_cells([baseline, treatment, repeat, reference2])["cell_count"], 4)

    def test_missing_baseline_and_self_control_rejected(self):
        a, b = pair()
        with self.assertRaisesRegex(audit.InvalidDesign, "CONTROL_NOT_IN_DESIGN"):
            audit.validate_cells([b])
        a["control"]["comparator_cell_id"] = "control"
        with self.assertRaisesRegex(audit.InvalidDesign, "SELF_CONTROL"):
            audit.validate_cells([a, b])

    def test_paired_task_seed_and_holdout_mismatch_rejected(self):
        changes = (
            lambda b: b["execution"].update(seed=999),
            lambda b: b["execution"].update(resource_class="gpu"),
            lambda b: b["execution"].update(environment_ref="another-runtime"),
            lambda b: b["workload"].update(split="other-split"),
            lambda b: b["workload"].update(dataset_ref="different-dataset"),
            lambda b: b["workload"].update(holdout_manifest_ref="separate-holdout"),
            lambda b: b.update(phase="screen"),
            lambda b: b.update(hypothesis_id="different"),
        )
        for i, change in enumerate(changes):
            a, b = pair()
            change(b)
            with self.subTest(i=i), self.assertRaisesRegex(
                audit.InvalidDesign, "UNMATCHED_CONTROL"
            ):
                audit.validate_cells([a, b])

    def test_control_chaining_and_treated_baseline_rejected(self):
        a, b = pair()
        extra = copy.deepcopy(b)
        extra["cell_id"] = "another-treatment"
        extra["control"]["comparator_cell_id"] = "diffusion"
        with self.assertRaisesRegex(audit.InvalidDesign, "CONTROL_CHAIN"):
            audit.validate_cells([a, b, extra])
        a["treatment"]["kind"] = "static-adapter"
        with self.assertRaisesRegex(audit.InvalidDesign, "CONTROL_TREATED"):
            audit.validate_cells([a, b])

    def test_confirmation_requires_holdout_and_primary_outcome(self):
        a, b = pair()
        for c in (a, b):
            c["phase"] = "confirm"
        with self.assertRaisesRegex(audit.InvalidDesign, "CONFIRMATION_HOLDOUT"):
            audit.validate_cells([a, b])
        for c in (a, b):
            c["workload"]["holdout_manifest_ref"] = "sha256:locked-holdout"
        audit.validate_cells([a, b])
        b["primary_outcome"] = ""
        with self.assertRaisesRegex(audit.InvalidDesign, "CONFIRMATION_OUTCOME"):
            audit.validate_cells([a, b])

    def test_unknown_provider_version_and_duplicates_rejected(self):
        a, b = pair()
        b["execution"]["provider_job_id"] = "provider/job"
        with self.assertRaisesRegex(audit.InvalidDesign, "PARTIAL_PROVIDER"):
            audit.validate_cells([a, b])
        b["execution"]["provider_version"] = "1"
        audit.validate_cells([a, b])
        with self.assertRaisesRegex(audit.InvalidDesign, "DUPLICATE_CELL"):
            audit.validate_cells([a, b, copy.deepcopy(b)])

    def test_invalid_json_schema_and_bad_cell_count(self):
        with self.assertRaisesRegex(audit.InvalidDesign, "SCHEMA_INVALID"):
            audit.validate_cells([{"cell_id": "missing"}])
        with self.assertRaisesRegex(audit.InvalidDesign, "EMPTY"):
            audit.validate_cells([])
        with self.assertRaisesRegex(audit.InvalidDesign, "TOO_MANY"):
            audit.validate_cells([reference()] * 4097)


if __name__ == "__main__":
    unittest.main()
