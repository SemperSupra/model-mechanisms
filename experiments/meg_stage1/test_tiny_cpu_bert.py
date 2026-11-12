"""Actual CPU torch tiny-BERT mechanism tests on synthetic token IDs."""
import importlib.util
import math
from pathlib import Path
import unittest
import torch

SCRIPT=Path(__file__).resolve().parent/"tiny_cpu_bert.py"
spec=importlib.util.spec_from_file_location("tiny_bert",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TinyBertStage1Tests(unittest.TestCase):
    def test_info_nce_diagonal_exclusion(self):
        a=torch.eye(2)
        self.assertAlmostEqual(float(m.contrastive(a,a)),math.log1p(math.exp(-1)),places=6)
        self.assertAlmostEqual(float(m.contrastive(a,torch.flip(a,dims=(0,)))),math.log1p(math.exp(1)),places=6)  # flipped positive keys also invert which negatives are masked
    def test_freeze_only_final_transformer_block(self):
        torch.manual_seed(m.SEED)
        model,parameters=m._tiny_model()
        trainable=[n for n,p in model.named_parameters() if p.requires_grad]
        self.assertTrue(trainable)
        self.assertTrue(all(n.startswith("encoder.layer.1.") for n in trainable))
        self.assertTrue(any(not p.requires_grad for p in model.parameters()))
        self.assertEqual(len(parameters),len(trainable))
    def test_pinned_tiny_cpu_gradient_policies_observably_differ(self):
        r=m.run()
        self.assertEqual(r["status"],"ACTUAL_SYNTHETIC_TORCH_CPU_TRAINING")
        self.assertEqual(len(r["policies"]),2)
        left,right=r["policies"]
        self.assertAlmostEqual(left["gradient_norms"][0],right["gradient_norms"][0],places=7)
        self.assertGreater(r["second_step_gradient_norm_diff_abs"],1e-12)
        self.assertFalse(r["pretrained_BERT_weights_loaded"])
        self.assertFalse(r["original_dataset_loaded"])
        self.assertFalse(r["scientific_meg_reproduction"])
        for p in r["policies"]:
            self.assertEqual(len(p["losses"]),3)
            self.assertEqual(len(p["gradient_norms"]),3)
            self.assertTrue(all(math.isfinite(x) for x in p["losses"]))
            self.assertTrue(all(math.isfinite(x) and x>0 for x in p["gradient_norms"]))
    def test_invalid_policy_denied(self):
        with self.assertRaisesRegex(ValueError,"UNAPPROVED_POLICY"):
            m.train_policy("secret-third-treatment")

if __name__=="__main__":unittest.main()
