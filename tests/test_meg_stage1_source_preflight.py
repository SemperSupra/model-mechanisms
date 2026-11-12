"""Independent source-only MeG Stage1 math, configuration and hazard controls."""
import importlib.util
import math
from pathlib import Path
import unittest

SOURCE=Path(__file__).resolve().parents[1]/"tools/meg_stage1_source_preflight.py"
spec=importlib.util.spec_from_file_location("stage1",SOURCE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class Stage1PreflightTests(unittest.TestCase):
    def test_scalar_info_nce_two_orthogonal_pairs(self):
        x=[[1.,0.],[0.,1.]]
        loss=m.info_nce_reference(x,x,x,1.0)
        self.assertAlmostEqual(loss,math.log1p(math.exp(-1)),places=12)
        self.assertGreater(loss,0)
    def test_swapped_positive_is_worse(self):
        qs=[[1.,0.],[0.,1.]]
        correct=m.info_nce_reference(qs,qs,qs,1.0)
        wrong=m.info_nce_reference(qs,list(reversed(qs)),qs,1.0)
        self.assertGreater(wrong,correct)
        self.assertAlmostEqual(wrong,math.log(2),places=12)
    def test_singleton_has_no_negative_signal(self):
        self.assertEqual(m.info_nce_reference([[1.,0.]],[[1.,0.]],[[1.,0.]],0.1),0.0)
    def test_row_scales_cancel_and_temperature_valid(self):
        x=[[10.,0.],[0.,10.]]
        y=[[1.,0.],[0.,1.]]
        self.assertAlmostEqual(m.info_nce_reference(x,x,x,1),
                               m.info_nce_reference(y,y,y,1),places=12)
        for t in (0,-1,float("nan"),float("inf")):
            with self.subTest(t=t),self.assertRaises(ValueError):
                m.info_nce_reference(y,y,y,t)
    def test_invalid_batch_vectors_refused(self):
        x=[[1.,0.],[0.,1.]]
        cases=[
          ([],[],[]),
          (x,x,[x[0]]),
          (x,[[1.],[1.]],x),
          ([[0.,0.],[1.,0.]],x,x),
        ]
        for q,p,n in cases:
            with self.subTest(q=q,p=p,n=n),self.assertRaises(ValueError):
                m.info_nce_reference(q,p,n,1.)
    def test_author_source_identity_cannot_be_guessed(self):
        for raw in (b"",b"def train_model(): pass",b"# patched unlicensed source"):
            with self.assertRaisesRegex(ValueError,"AUTHOR_STAGE1_TRAIN_BLOB_MISMATCH"):
                m.inspect_source(raw)
        with self.assertRaisesRegex(ValueError,"AUTHOR_STAGE1_CONFIG_BLOB_MISMATCH"):
            m.parse_fixed_config(b"gpu: 0\n")
    def test_reference_source_identifiers_are_exact_hashes(self):
        for item in (m.TRAIN_BLOB_SHA1,m.CONFIG_BLOB_SHA1):
            self.assertEqual(len(item),40)
            int(item,16)
        self.assertEqual(m.AUTHOR_REVISION,
                         "9fa8ae10cf33c82dd2200057f70dfcb73388cd74")
    def test_git_blob_hash_not_plain_content_hash(self):
        self.assertEqual(m.git_blob_sha1(b"test\n"),"9daeafb9864cf43055ae93beb0afd6c7d144bfa4")

if __name__=="__main__":unittest.main()
