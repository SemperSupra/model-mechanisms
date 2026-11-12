"""No-training controls for Stage1 literal/corrected 2x2 fidelity planning."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"tools/validate_meg_stage1_design.py"
spec=importlib.util.spec_from_file_location("meg_stage1_design",SOURCE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
MANIFEST=ROOT/"campaigns/meg-stage1-fidelity-factorial.json"

class DesignAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.plan=json.loads(MANIFEST.read_text(encoding="utf-8"))
    def test_research_plan_valid(self):
        receipt=mod.validate(self.plan)
        self.assertEqual(receipt["status"],"PASS_PLAN_ONLY")
        self.assertEqual(receipt["factorial_cells"],4)
        self.assertEqual(receipt["observations_measured"],0)
        self.assertFalse(receipt["provider_job_submitted"])
    def test_both_factors_crossed_and_original_baseline(self):
        pairs={(c["paraphrase_policy"],c["gradient_policy"]) for c in self.plan["cells"]}
        self.assertEqual(pairs,{(a,b) for a in mod.PARA for b in mod.GRAD})
        self.assertTrue(all(c["baseline_cell_id"]=="literal-accum" for c in self.plan["cells"]))
    def test_hold_on_fake_metrics_or_training(self):
        mutations=[
            lambda p:p.update(status="PAPER_REPRODUCED"),
            lambda p:p.update(training_run_executed=True),
            lambda p:p.update(publisher_rights_review_complete=True),
            lambda p:p["screen_budget"].update(provider_calls_allowed=True),
            lambda p:p["screen_budget"].update(max_epochs=30000),
            lambda p:p["cells"][0].update(measurement=0.9),
            lambda p:p["cells"][1].update(executed=True),
            lambda p:p["cells"][2].update(character_fragment_pairs=2664),
            lambda p:p["cells"][3].update(baseline_cell_id="typed-reset"),
            lambda p:p["cells"].pop(),
            lambda p:p.update(original_bert_model_revision="invented"),
        ]
        for i,fn in enumerate(mutations):
            p=copy.deepcopy(self.plan)
            fn(p)
            with self.subTest(i=i),self.assertRaises(ValueError):
                mod.validate(p)
    def test_exact_source_and_data_revisions_locked(self):
        p=copy.deepcopy(self.plan)
        p["author_train_git_blob"]="0"*40
        with self.assertRaisesRegex(ValueError,"TRAIN_BLOB_DRIFT"):
            mod.validate(p)

if __name__=="__main__":unittest.main()
