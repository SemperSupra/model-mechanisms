"""Plan-only Dory loop-mask DOE contracts; no model or provider required."""
import copy
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "core/doe/loop_masks.py"
spec = importlib.util.spec_from_file_location("loop_masks", SRC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class LoopScreenContracts(unittest.TestCase):
    def test_full_factorial_has_16_distinct_masks(self):
        plan = mod.make_plan(11)
        self.assertEqual(plan["status"], "PLAN_ONLY")
        self.assertEqual(plan["admission"], "BLOCKED_UNPINNED_ASSETS_AND_PROTOCOL")
        self.assertEqual(plan["loop_depth"], 4)
        cells = plan["cells"]
        self.assertEqual(len(cells), 16)
        self.assertEqual(len({c["cell_id"] for c in cells}), 16)
        self.assertEqual(cells[0]["loop_mask"], "0000")
        self.assertEqual(cells[-1]["loop_mask"], "1111")
        self.assertTrue(all(not c["admitted"] and not c["measured"] for c in cells))
        self.assertTrue(all(c["reference_control_cell_id"] == "mask-0000" for c in cells))
        self.assertTrue(all(c["seed"] == 11 for c in cells))
        mod.validate_plan(plan)

    def test_nominal_aggregate_strength_constant_for_nonzero_masks(self):
        for cell in mod.make_plan()["cells"]:
            active = cell["active_pass_count"]
            per = Fraction(cell["nominal_strength_each_active_pass"])
            if active == 0:
                self.assertEqual(per, 0)
                self.assertEqual(cell["treatment"], "untreated_baseline")
            else:
                self.assertEqual(active * per, 1)
                self.assertEqual(cell["treatment"], "same_frozen_intervention")

    def test_cross_run_design_deterministic_and_bounded(self):
        self.assertEqual(mod.make_plan(4), mod.make_plan(4))
        self.assertNotEqual(mod.make_plan(4)["seed"], mod.make_plan(5)["seed"])
        for invalid in (-1, True, 2**31, "4"):
            with self.assertRaises(ValueError):
                mod.make_plan(invalid)

    def test_unequal_or_illegal_masks_rejected(self):
        for mutation in (
            lambda p: p["cells"].pop(),
            lambda p: p["cells"][2].update(loop_mask="0000"),
            lambda p: p["cells"][8].update(active_pass_count=9),
            lambda p: p["cells"][8].update(nominal_strength_each_active_pass="1"),
            lambda p: p["cells"][8].update(reference_control_cell_id="mask-1111"),
            lambda p: p["cells"][8].update(measured=True),
            lambda p: p.update(status="SCIENTIFIC_RESULT"),
            lambda p: p.update(admission="ADMITTED"),
            lambda p: p["frozen_inputs"].update(backbone_revision="invented"),
            lambda p: p.update(matched_task_ids_digest="private"),
        ):
            doc = copy.deepcopy(mod.make_plan())
            mutation(doc)
            with self.assertRaises(ValueError):
                mod.validate_plan(doc)

    def test_cli_stdout_standalone(self):
        proc = subprocess.run(
            [sys.executable, str(SRC), "--seed", "17"],
            cwd=ROOT, capture_output=True, text=True, timeout=8,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        doc = json.loads(proc.stdout)
        self.assertEqual(doc["seed"], 17)
        mod.validate_plan(doc)
        self.assertEqual(doc["cells"][0]["loop_mask"], "0000")


if __name__ == "__main__":
    unittest.main()
