"""Source-only hostile tests for Stage2 paper reproduction, no author execution."""
import importlib.util
import math
from pathlib import Path
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"tools/meg_stage2_router_preflight.py"
spec=importlib.util.spec_from_file_location("meg_stage2",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class RouterSourceTests(unittest.TestCase):
    def test_uniform_entropy_causes_abstention(self):
        x=m.route([0.]*10)
        self.assertAlmostEqual(x["entropy"],math.log(10),places=12)
        self.assertTrue(x["abstained"])
        self.assertEqual(x["class_index"],-1)
    def test_peaked_distribution_uses_non_abstaining_class(self):
        x=m.route([20.]+[-20.]*9)
        self.assertLess(x["entropy"],0.1)
        self.assertFalse(x["abstained"])
        self.assertEqual(x["class_index"],0)
        y=m.route([-20.]*7+[20.]+[-20.]*2)
        self.assertEqual(y["class_index"],7)
    def test_exact_threshold_comparison_and_numeric_stability(self):
        logits=[1000.]+[-1000.]*9
        self.assertEqual(m.route(logits)["class_index"],0)
        self.assertEqual(m.route(logits,0.)["class_index"],-1)  # source clamps p >=1e-8, leaving small positive entropy
        self.assertEqual(m.route(logits,1e-5)["class_index"],0)
        self.assertTrue(m.route([0.]*10,math.log(10)-1e-5)["abstained"])
        self.assertFalse(m.route([0.]*10,math.log(10)+1e-5)["abstained"])
    def test_bad_10class_shape_nonfinite_probs_and_threshold_rejected(self):
        for logits in ([],[0.]*9,[float("nan")]+[0.]*9,[float("inf")]+[0.]*9):
            with self.subTest(logits=logits),self.assertRaises(ValueError):
                m.route(logits)
        for probs in ([0.]*10,[0.2]*10,[float("nan")]+[0.]*9,[-0.1]+[0.]*9):
            with self.subTest(probs=probs),self.assertRaises(ValueError):
                m.entropy_probabilities(probs)
        for threshold in (-1.,float("nan"),float("inf")):
            with self.subTest(threshold=threshold),self.assertRaises(ValueError):
                m.route([0.]*10,threshold)
    def test_static_source_identity_guard(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_IDENTITY_MISMATCH"):
            m.inspect_author_source(b'not author source')
        with self.assertRaisesRegex(ValueError,"HPARAM_IDENTITY_MISMATCH"):
            m.inspect_config(b'not pinned yaml')
    def test_git_blob_values_are_pinned_and_untrusted_checkpoint_state_declared(self):
        self.assertEqual(len(m.TRAIN_BLOB),40)
        self.assertEqual(len(m.CONFIG_BLOB),40)
        self.assertEqual(m.EXPECTED_THRESHOLD,0.1)
        self.assertEqual(m.EXPECTED_SIZES[1024],(1024,1800))
        self.assertTrue("STAGE" in m.TRAIN_BLOB or len(m.AUTHOR)==40)

if __name__=="__main__":unittest.main()
