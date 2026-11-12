#!/usr/bin/env python3
"""Audit the actual generated MLX bridge wheel against reviewed source bytes.

Source-only / read-only. Detect unexpected archive members, duplicate paths,
symlinks, missing core modules, changed package code and incorrect RECORD
checksums. Does not execute a wheel, pip, native extension, model or network.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
from io import StringIO
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile

EXPECTED_MODULES = (
    "__init__.py", "controller.py", "phi2.py",
)
PACKAGE = "meg_mlx_bridge/"
MAX_MEMBERS = 80
MAX_UNCOMPRESSED_BYTES = 2_000_000


class InvalidWheel(ValueError):
    pass


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit_wheel(wheel_path: Path, source_tree: Path) -> dict:
    wheel_path = wheel_path.resolve()
    source_tree = source_tree.resolve()
    if not wheel_path.is_file() or wheel_path.stat().st_size > 2_000_000:
        raise InvalidWheel("WHEEL_UNAVAILABLE_OR_OVERSIZED")
    module_paths = {PACKAGE + name for name in EXPECTED_MODULES}
    expected_data = {
        PACKAGE + name: (source_tree / "src" / "meg_mlx_bridge" / name).read_bytes()
        for name in EXPECTED_MODULES
    }
    with zipfile.ZipFile(wheel_path) as wheel:
        info = wheel.infolist()
        paths = [entry.filename for entry in info]
        if len(paths) < len(EXPECTED_MODULES) + 3 or len(paths) > MAX_MEMBERS:
            raise InvalidWheel("BAD_WHEEL_MEMBER_COUNT")
        if len(paths) != len(set(paths)):
            raise InvalidWheel("DUPLICATE_ZIP_NAMES")
        for member in info:
            path = PurePosixPath(member.filename)
            if (member.filename.startswith("/") or "\\" in member.filename
                or any(component in ("", ".", "..") for component in member.filename.split("/"))
                or not path.parts):
                raise InvalidWheel("ZIP_PATH_TRAVERSAL")
            if stat.S_ISLNK(member.external_attr >> 16):
                raise InvalidWheel("WHEEL_SYMLINK")
            if member.file_size > MAX_UNCOMPRESSED_BYTES:
                raise InvalidWheel("OVERSIZED_MEMBER")
            name = member.filename
            if not (name in module_paths or re.fullmatch(
                r"meg_mlx_bridge-0[.]1[.]0[.]dist-info/(?:METADATA|WHEEL|RECORD|top_level[.]txt|licenses/[-a-zA-Z0-9_.]+)",
                name,
            )):
                raise InvalidWheel("UNREVIEWED_WHEEL_MEMBER:" + name[:80])
        if not module_paths.issubset(set(paths)):
            raise InvalidWheel("MISSING_REVIEWED_MODULE")
        for name, expected in expected_data.items():
            if wheel.read(name) != expected:
                raise InvalidWheel("WHEEL_SOURCE_MISMATCH:" + name)
        record_path = "meg_mlx_bridge-0.1.0.dist-info/RECORD"
        if record_path not in paths:
            raise InvalidWheel("RECORD_MISSING")
        rows = list(csv.reader(StringIO(wheel.read(record_path).decode("utf-8"))))
        if len(rows) != len(paths):
            raise InvalidWheel("RECORD_INCOMPLETE")
        recorded = set()
        for row in rows:
            if len(row) != 3:
                raise InvalidWheel("RECORD_ROW_INVALID")
            name, hashed, size = row
            if name in recorded or name not in paths:
                raise InvalidWheel("RECORD_NAME_MISMATCH")
            recorded.add(name)
            if name == record_path:
                if hashed or size:
                    raise InvalidWheel("RECORD_SELF_DIGEST_INVALID")
                continue
            data = wheel.read(name)
            sha = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode("ascii")
            if hashed != "sha256=" + sha or size != str(len(data)):
                raise InvalidWheel("RECORD_DIGEST_MISMATCH:" + name)
        if recorded != set(paths):
            raise InvalidWheel("RECORD_SET_MISMATCH")
        metadata = wheel.read("meg_mlx_bridge-0.1.0.dist-info/METADATA").decode("utf-8")
        if "\nName: meg-mlx-bridge\n" not in "\n" + metadata or "\nVersion: 0.1.0\n" not in "\n" + metadata:
            raise InvalidWheel("PACKAGE_IDENTITY_MISMATCH")
        tag = wheel.read("meg_mlx_bridge-0.1.0.dist-info/WHEEL").decode("utf-8")
        if "\nTag: py3-none-any\n" not in "\n" + tag:
            raise InvalidWheel("NOT_PURE_PYTHON_WHEEL")
    return {
        "schema": "model-mechanisms.mlx-wheel-audit/v1",
        "status": "PASS",
        "wheel_filename": wheel_path.name,
        "wheel_sha256": _digest(wheel_path.read_bytes()),
        "source_module_sha256": {name: _digest(data) for name, data in expected_data.items()},
        "member_count": len(paths),
        "proof": "reviewed source equality and wheel RECORD integrity only",
        "model_loaded": False,
        "meg_experiment_reproduced": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit_wheel(args.wheel, args.source), sort_keys=True))


if __name__ == "__main__":
    main()
