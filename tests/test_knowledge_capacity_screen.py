"""Negative and positive contracts for MeG/Phi-2 PLAN_ONLY DOE."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "core/doe/knowledge_capacity.py"
spec = importlib.util.spec_from_file_location("knowledge_capacity", MODULE)
science = importlib.util.module_from_spec(spec)
spec.loader.exec_module(science)


class CapacityPlanContracts(unittest.TestCase):
    def test_small_pilot_has_matched_baselines_and_no_measurements(self):
        plan = science.make_plan(7)
        self.assertEqual(plan["status"], "PLAN_ONLY")
        self.assertEqual(plan["admission"], "BLOCKED_DATA_MODEL_CONTROLLER_AND_EVAL_LOCKS")
        self.assertEqual(len(plan["cells"]), 15)
        self.assertTrue(all(cell["fact_load"] == 100 for cell in plan["cells"]))
        for cell in plan["cells"]:
            self.assertEqual(cell["seed"], 7)
            self.assertFalse(cell["admitted"])
            self.assertFalse(cell["measured"])
            self.assertEqual(
                cell["baseline_cell_id"],
                science.cell_id(100, cell["question_type"], science.BASELINE),
            )
        science.validate_plan(plan)

    def test_conditional_scale_is_45_planned_not_admitted_cells(self):
        plan = science.make_plan(7, include_scale_tiers=True)
        self.assertEqual(len(plan["cells"]), 45)
        self.assertEqual(plan["fact_load_levels"], [100, 500, 1000])
        self.assertEqual(
            len({c["cell_id"] for c in plan["cells"]}), 45,
        )
        self.assertEqual(
            sum(c["tier"] == "conditional_scale" for c in plan["cells"]), 30,
        )
        self.assertTrue(all(not c["admitted"] for c in plan["cells"]))
        science.validate_plan(plan)

    def test_retrieval_is_a_separate_non_closed_book_comparator(self):
        for cell in science.make_plan(0, True)["cells"]:
            if cell["method"] == "retrieval":
                self.assertEqual(cell["knowledge_access"], "retrieval_allowed")
            else:
                self.assertEqual(cell["knowledge_access"], "closed_book")

    def test_honors_source_and_holdout_gates(self):
        original = science.make_plan()
        cases = [
            lambda p: p.update(status="SCIENTIFICALLY_REPRODUCED"),
            lambda p: p.update(admission="ADMITTED"),
            lambda p: p["no_drift_assets"].update(phi2_revision="fabricated"),
            lambda p: p.update(retrieval_is_separate_comparator=False),
            lambda p: p["cells"][0].update(measured=True),
            lambda p: p["cells"][0].update(admitted=True),
            lambda p: p["cells"][0].update(seed=999),
            lambda p: p["cells"][1].update(baseline_cell_id="unmatched"),
            lambda p: p["cells"][4].update(knowledge_access="closed_book"),
            lambda p: p["cells"][4].update(method="meg_diffusion"),
            lambda p: p["cells"].pop(),
            lambda p: p.update(fact_load_levels=[500, 1000]),
            lambda p: p.update(methods=["unchanged_phi2", "meg_diffusion"]),
            lambda p: p.update(question_types=["direct"]),
        ]
        for i, mutation in enumerate(cases):
            report = copy.deepcopy(original)
            mutation(report)
            with self.subTest(case=i):
                with self.assertRaises(ValueError):
                    science.validate_plan(report)

    def test_seed_and_cli_are_deterministic(self):
        self.assertEqual(science.make_plan(23), science.make_plan(23))
        for invalid in (-1, True, "1", 2**31):
            with self.assertRaises(ValueError):
                science.make_plan(invalid)
        output = subprocess.run(
            [sys.executable, str(MODULE), "--seed", "23"],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(output.returncode, 0, output.stderr)
        report = json.loads(output.stdout)
        self.assertEqual(report, science.make_plan(23))


if __name__ == "__main__":
    unittest.main()
