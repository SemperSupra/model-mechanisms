"""Source-only negative controls for the official ICLR supplement audit."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools/audit_meg_iclr_supplement.py"
spec = importlib.util.spec_from_file_location("audit_meg_iclr_supplement", SRC)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class SupplementIndexTests(unittest.TestCase):
    def make_zip(self, base: Path, files: dict[str, bytes]):
        path = base / "supplement.zip"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as f:
            for name, data in files.items():
                f.writestr(name, data)
        return path

    def test_metadata_only_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.make_zip(Path(tmp), {
                "supplement/readme.txt": b"synthetic appendix text",
                "supplement/figures.pdf": b"synthetic placeholder only",
            })
            report = tool.inspect(path)
            self.assertEqual(report["status"], "METADATA_INSPECTED_ONLY")
            self.assertEqual(report["member_count"], 2)
            self.assertTrue(any(x["possible_protocol_input"] for x in report["members"]))
            self.assertFalse(report["files_extracted"])
            self.assertFalse(report["author_checkpoint_recovered"])
            self.assertFalse(report["paper_reproduced"])
            self.assertEqual(len(report["archive_sha256"]), 64)

    def test_path_traversal_duplicate_and_abs_rejected(self):
        for name in ("../escape.txt", "/etc/passwd", "a/../b", "a\\evil.txt"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                path = self.make_zip(Path(tmp), {name: b"bad"})
                with self.assertRaises(ValueError):
                    tool.inspect(path)

    def test_not_a_zip_and_member_size_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "notzip.zip"
            path.write_bytes(b"hello")
            with self.assertRaisesRegex(ValueError, "NOT_A_ZIP"):
                tool.inspect(path)
        with tempfile.TemporaryDirectory() as tmp:
            path = self.make_zip(Path(tmp), {"huge.bin": b"0" * 250})
            old = tool.MAX_MEMBER_BYTES
            try:
                tool.MAX_MEMBER_BYTES = 100
                with self.assertRaisesRegex(ValueError, "OVERSIZED"):
                    tool.inspect(path)
            finally:
                tool.MAX_MEMBER_BYTES = old

    def test_no_execution_even_with_scripts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.make_zip(Path(tmp), {"stage4/train.py": b"raise Exception('untrusted')"})
            info = tool.inspect(path)
            self.assertEqual(info["member_count"], 1)
            self.assertTrue(info["members"][0]["possible_protocol_input"])
            self.assertFalse(info["third_party_code_executed"])


    def test_nested_official_style_code_and_data_archives(self):
        import io
        def nested(files):
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as zf:
                for name, data in files.items():
                    zf.writestr(name, data)
            return stream.getvalue()
        with tempfile.TemporaryDirectory() as tmp:
            code = nested({"README.md": b"synthetic readme"})
            data = nested({
                "data/new_split_data/zsre_train.json": b'{"synthetic":true}',
                "data/raw_data/get_rephrase.prompt": b"synthetic test prompt",
            })
            path = self.make_zip(Path(tmp), {
                "code_and_data_for_our_MeG/code_for_our_MeG.zip": code,
                "code_and_data_for_our_MeG/data_for_our_MeG.zip": data,
            })
            report = tool.inspect(path)
            self.assertEqual(report["member_count"], 2)
            self.assertEqual(len(report["nested_archives"]), 2)
            self.assertEqual(report["nested_archives"][1]["member_count"], 2)
            self.assertTrue(
                any(m["possible_protocol_input"]
                    for m in report["nested_archives"][1]["members"])
            )
            self.assertFalse(report["files_extracted"])
            self.assertFalse(report["third_party_code_executed"])

if __name__ == "__main__":
    unittest.main()
