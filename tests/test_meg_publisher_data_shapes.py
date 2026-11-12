"""Synthetic no-network tests for official MeG publisher data census."""
import importlib.util
import json
from pathlib import Path
import unittest

SRC=Path(__file__).resolve().parents[1]/"tools"/"audit_meg_publisher_data_shapes.py"
spec=importlib.util.spec_from_file_location("publisher_data_shapes",SRC)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class PublisherDataShapeTests(unittest.TestCase):
    def test_expected_digests_are_complete(self):
        self.assertEqual(len(mod.EXPECTED),18)
        self.assertEqual(len(set(mod.EXPECTED)),18)
        for name,(digest,size) in mod.EXPECTED.items():
            self.assertTrue(len(digest)==64 and int(digest,16)>=0)
            self.assertGreater(size,0)
            self.assertFalse(name.startswith("/"))
            self.assertNotIn("..",name.split("/"))
    def test_synthetic_record_shape(self):
        data=b'[{"id":0,"src":"invented"}, {"id":1,"rephrase":["x"],"src":"fiction"}]'
        result=mod.validate_shape("test.json",data)
        self.assertEqual(result["record_count"],2)
        self.assertEqual(result["field_names"],["id","rephrase","src"])
        self.assertEqual(mod.validate_shape("README.md",b"hi")["type"],"text")
    def test_non_record_json_rejected(self):
        for raw in (b'{"data":[]}', b'[1,2]',b'false'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):
                mod.validate_shape("wrong.json",raw)
    def test_published_stage1_slices_intersect_only_when_required(self):
        x=mod.overlap_first_last(2000)
        self.assertEqual(x["positional_overlap_count"],1024)
        self.assertFalse(x["validation_and_training_disjoint_by_index"])
        self.assertEqual(mod.overlap_first_last(3024)["positional_overlap_count"],0)
        self.assertTrue(mod.overlap_first_last(10000)["validation_and_training_disjoint_by_index"])
        self.assertEqual(mod.overlap_first_last(2500)["positional_overlap_count"],524)
        with self.assertRaises(ValueError):mod.overlap_first_last(-1)
    def test_no_unpinned_archive_as_success(self):
        with self.assertRaises(ValueError):
            mod.audit(Path("/definitely-does-not-exist/meg.zip"))

if __name__=="__main__":unittest.main()
