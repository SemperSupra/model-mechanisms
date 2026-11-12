"""Synthetic Stage1 publisher split negative controls: text never leaves receipt."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("meg_stage1_text_overlap",ROOT/"tools/meg_stage1_text_overlap.py")
audit=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(audit)

def fixture():
    data=[{"src":f"Invented Q-{i}","rephrase":[f"Invented P-{i}a",f"Invented P-{i}b"]} for i in range(4000)]
    for i in range(2668,4000):
        data[i]["rephrase"]=f"Complete invented question {i}?"
    return data

class TextOverlapTests(unittest.TestCase):
    def test_distinct_synthetic_subjects_have_no_exact_collisions(self):
        result=audit.compare(fixture())
        self.assertEqual(result["policies"]["literal"]["training_pair_count"],4000)
        self.assertEqual(result["policies"]["corrected"]["training_pair_count"],2668)
        self.assertEqual(result["policies"]["literal"]["validation_records_with_any_exact_text_collision"],0)
        self.assertEqual(result["policies"]["corrected"]["validation_records_with_any_exact_text_collision"],0)
        self.assertFalse(result["question_text_or_hashes_emitted"])
        self.assertFalse(result["subject_or_semantic_leakage_tested"])
    def test_normalization_and_literal_characters_are_not_misrepresented(self):
        self.assertEqual(audit.norm("  FOO  bar  "),"foo bar")
        self.assertEqual(audit.norm("Ｆｏｏ"),"foo")
        self.assertEqual(audit.phrases({"rephrase":"Hello world?"},"literal"),["H","e"])
        self.assertEqual(audit.phrases({"rephrase":"Hello world?"},"corrected"),["Hello world?"])
        for value in (None,0,{"nested":1}):
            with self.subTest(value=value),self.assertRaises(ValueError):
                audit.phrases({"rephrase":value},"literal")
    def test_overlap_detects_source_and_rephrase_collisions(self):
        records=fixture()
        records[2500]["src"]="  INVENTED  Q-12 "
        records[2501]["rephrase"]=["Invented P-13a","Other"]
        result=audit.compare(records)
        for label in ("literal","corrected"):
            m=result["policies"][label]
            self.assertEqual(m["validation_src_in_training_src"],1)
            self.assertEqual(m["validation_rephrase_in_training_paraphrases"],1)
            self.assertEqual(m["validation_records_with_any_exact_text_collision"],2)
            self.assertNotIn("Invented",str(result))
    def test_reject_wrong_record_count_validation_types_and_input(self):
        x=fixture()
        with self.assertRaisesRegex(ValueError,"EXPECTED_EXACT_4000"):
            audit.compare(x[:-1])
        x[0]["rephrase"]="not a valid validation list"
        with self.assertRaisesRegex(ValueError,"BAD_VALIDATION_REPHRASE_LIST"):
            audit.compare(x)
        with self.assertRaises(ValueError):
            audit.original_records(Path("/not-a-real-meg-publisher.zip"))

if __name__=="__main__":unittest.main()
