"""Offline red-team fixtures for the emitted MLX wheel and code-source parity."""
import base64
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools/audit_wheel.py"
spec = importlib.util.spec_from_file_location("wheel_audit", SRC)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
INFO = "meg_mlx_bridge-0.1.0.dist-info/"
PACKAGE = "meg_mlx_bridge/"


def make_wheel(root, *, modified=None):
    tree = root / "source"
    path = tree / "src/meg_mlx_bridge"
    path.mkdir(parents=True, exist_ok=True)
    files = {}
    for name in ("__init__.py", "phi2.py", "controller.py"):
        data = ("# approved synthetic " + name + "\n").encode()
        (path / name).write_bytes(data)
        files[PACKAGE + name] = data
    files[INFO + "METADATA"] = b"Metadata-Version: 2.1\nName: meg-mlx-bridge\nVersion: 0.1.0\n"
    files[INFO + "WHEEL"] = b"Wheel-Version: 1.0\nTag: py3-none-any\n"
    files[INFO + "top_level.txt"] = b"meg_mlx_bridge\n"
    if modified:
        modified(files)
    record = io.StringIO()
    for name, data in files.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        record.write(name + ",sha256=" + digest + "," + str(len(data)) + "\n")
    record.write(INFO + "RECORD,,\n")
    files[INFO + "RECORD"] = record.getvalue().encode()
    output = root / "meg_mlx_bridge-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as wheel:
        for name, data in files.items():
            wheel.writestr(name, data)
    return output, tree


class WheelArchivePolicyTests(unittest.TestCase):
    def test_exact_source_and_record_pass(self):
        with tempfile.TemporaryDirectory() as td:
            whl, src = make_wheel(Path(td))
            result = audit.audit_wheel(whl, src)
            self.assertEqual(result["status"], "PASS")
            self.assertFalse(result["model_loaded"])
            self.assertFalse(result["meg_experiment_reproduced"])
            self.assertEqual(len(result["source_module_sha256"]), 3)

    def test_tampered_source_member_rejected_even_with_valid_record(self):
        with tempfile.TemporaryDirectory() as td:
            whl, src = make_wheel(Path(td), modified=lambda f: f.__setitem__(
                PACKAGE + "phi2.py", b"# changed code without review\n"))
            with self.assertRaisesRegex(audit.InvalidWheel, "WHEEL_SOURCE_MISMATCH"):
                audit.audit_wheel(whl, src)

    def test_added_binary_or_credentials_rejected(self):
        for member in ("meg_mlx_bridge/evil.so", "meg_mlx_bridge/.env", "../escape.py"):
            with self.subTest(member=member), tempfile.TemporaryDirectory() as td:
                whl, src = make_wheel(
                    Path(td), modified=lambda f: f.__setitem__(member, b"unreviewed"))
                with self.assertRaisesRegex(audit.InvalidWheel, "UNREVIEWED|ZIP_PATH"):
                    audit.audit_wheel(whl, src)

    def test_modified_record_fails(self):
        with tempfile.TemporaryDirectory() as td:
            whl, src = make_wheel(Path(td))
            replacement = Path(td) / "broken.whl"
            with zipfile.ZipFile(whl) as original, zipfile.ZipFile(replacement, "w") as out:
                for item in original.infolist():
                    data = original.read(item.filename)
                    if item.filename == INFO + "RECORD":
                        data = data.replace(b"sha256=", b"sha512=", 1)
                    out.writestr(item.filename, data)
            with self.assertRaisesRegex(audit.InvalidWheel, "RECORD_DIGEST_MISMATCH"):
                audit.audit_wheel(replacement, src)

    def test_missing_reviewed_module_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            whl, src = make_wheel(Path(td), modified=lambda f: f.pop(PACKAGE + "phi2.py"))
            with self.assertRaisesRegex(audit.InvalidWheel, "MISSING_REVIEWED_MODULE"):
                audit.audit_wheel(whl, src)


if __name__ == "__main__":
    unittest.main()
