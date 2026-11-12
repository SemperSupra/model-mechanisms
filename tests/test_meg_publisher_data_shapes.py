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
    def test_overlap_is_aggregate_only_and_detects_textual_leakage(self):
        records=[{"src":f"Fictional question {i}","rephrase":[f"paraphrase {i}"]} for i in range(4000)]
        self.assertEqual(mod.text_overlap_first_last(records)["unique_src_overlap"],0)
        self.assertEqual(mod.text_overlap_first_last(records)["validation_records_with_any_exact_text_overlap"],0)
        records[3000]["rephrase"]=["  FICTIONAL   question 12 "]
        result=mod.text_overlap_first_last(records)
        self.assertEqual(result["unique_src_overlap"],0)
        self.assertGreater(result["unique_src_or_rephrase_overlap"],0)
        self.assertEqual(result["validation_records_with_any_exact_text_overlap"],1)
        self.assertFalse(result["question_text_or_hashes_emitted"])
        self.assertFalse(result["semantic_subject_overlap_evaluated"])
        self.assertNotIn("Fictional question 12",str(result))
    def test_stage1_invalid_text_shape_rejected(self):
        for records in ([{"src":0,"rephrase":[]}],
                        [{"src":"x","rephrase":"not-a-list"}],
                        [{"src":"x","rephrase":[42]}]):
            with self.subTest(records=records),self.assertRaises(ValueError):
                mod.text_overlap_first_last(records)
    def test_stage1_schema_mismatch_reports_aggregate_blocker(self):
        items=[{"question":"synthetic","answers":["x"]},{"src":"invented","rephrase":["rewrite"]}]
        report=mod.stage1_field_profile(items)
        self.assertEqual(report["trainer_compatible_records"],1)
        self.assertFalse(report["trainer_compatible"])
        self.assertFalse(report["source_values_emitted"])
        self.assertNotIn("synthetic",str(report))
    def test_literal_character_fragment_vs_type_corrected_counts(self):
        rows=[
            {"src":"one", "rephrase":["full paraphrase 1","full paraphrase 2"]},
            {"src":"two", "rephrase":"Hello world"},
            {"src":"three", "rephrase":"X"},
            {"src":"four", "rephrase":""},
        ]
        report=mod.stage1_field_profile(rows)["all"]
        self.assertEqual(report["as_published_contrastive_pairs"],5)
        self.assertEqual(report["type_corrected_contrastive_pairs"],4)
        self.assertEqual(report["as_published_character_fragment_pairs"],3)
        self.assertEqual(report["string_fields_shorter_than_two_characters"],2)
        self.assertEqual(report["rephrase_as_string"],3)
        self.assertEqual(report["rephrase_list_of_strings"],1)
    def test_no_unpinned_archive_as_success(self):
        with self.assertRaises(ValueError):
            mod.audit(Path("/definitely-does-not-exist/meg.zip"))

if __name__=="__main__":unittest.main()
