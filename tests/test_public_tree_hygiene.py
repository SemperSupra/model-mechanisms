"""Unit and live-tree tests for public source hygiene guard."""
import importlib.util
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
script = ROOT / "tools/validate_public_tree.py"
spec = importlib.util.spec_from_file_location("source_hygiene", script)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class PublicTreeHygiene(unittest.TestCase):
    def test_good_small_source_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "tools/script.py"
            path.parent.mkdir()
            path.write_text("print('test')\n")
            self.assertEqual(guard.check_entry(root, "tools/script.py"), [])

    def test_sensitive_paths_denied(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = (
                "kaggle.json", ".env", ".env.production",
                ".kaggle-latent/control-receipt.json",
                "node_modules/pkg/index.js", "__pycache__/x.pyc",
                "models/model.safetensors", "weights/file.gguf",
                "artifacts/checkpoint.pth", "dist/tool.whl",
                "credentials.json", "id_ed25519",
            )
            for item in paths:
                with self.subTest(item=item):
                    f = root / item
                    f.parent.mkdir(parents=True, exist_ok=True)
                    f.write_bytes(b"source-only-test")
                    self.assertTrue(guard.check_entry(root, item))

    def test_missing_symlink_and_oversized_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.assertIn("TRACKED_FILE_MISSING", guard.check_entry(root, "not-there.py"))
            large = root / "large.py"
            with large.open("wb") as fp:
                fp.truncate(guard.MAX_TRACKED_BYTES + 1)
            self.assertIn("TRACKED_FILE_OVERSIZE", guard.check_entry(root, "large.py"))
            good = root / "good.py"
            good.write_text("# test")
            (root / "linked.py").symlink_to(good)
            self.assertIn("TRACKED_SYMLINK", guard.check_entry(root, "linked.py"))

    def test_traversal_and_absolute_paths_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            for path in ("/etc/passwd", "../outside", "a/../../b", "a\\b", ""):
                with self.subTest(path=path):
                    self.assertEqual(guard.check_entry(Path(td), path), ["UNSAFE_PATH"])

    def test_actual_git_tree_has_no_model_bytes_or_credentials(self):
        report = guard.scan(ROOT)
        self.assertEqual(report["status"], "PASS", report["violations"])
        self.assertGreaterEqual(report["tracked_file_count"], 4)


if __name__ == "__main__":
    unittest.main()
