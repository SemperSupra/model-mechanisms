#!/usr/bin/env python3
"""Fail-closed source-only public repository hygiene scan.

Checks only tracked Git files. It is NOT secret-value detection, license review,
malware scanning, or a substitute for GitHub secret scanning/branch protection.
"""
from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MAX_TRACKED_BYTES = 2_000_000
BLOCKED_EXACT_NAMES = {
    ".env", "kaggle.json", "id_rsa", "id_ed25519", "credentials.json",
    "service-account.json", ".netrc", ".npmrc", ".pypirc",
}
BLOCKED_DIRS = {
    ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", ".kaggle-latent", ".kaggle", "checkpoints",
}
BLOCKED_EXTENSIONS = (
    ".safetensors", ".gguf", ".pth", ".pt", ".ckpt", ".onnx",
    ".pfx", ".p12", ".pem", ".key", ".whl", ".dmg", ".zip",
    ".tar.gz",
)


def check_entry(root: Path, relative: str) -> list[str]:
    """Return policy violations; do not load or print source file bytes."""
    if not relative or "\x00" in relative or "\\" in relative:
        return ["UNSAFE_PATH"]
    name = PurePosixPath(relative)
    if name.is_absolute() or any(part in (".", "..", "") for part in name.parts):
        return ["UNSAFE_PATH"]
    lower_parts = tuple(part.lower() for part in name.parts)
    basename = lower_parts[-1]
    problems = []
    if (basename in BLOCKED_EXACT_NAMES
        or basename.startswith(".env.")
        or any(part in BLOCKED_DIRS or part.startswith(".kaggle-") for part in lower_parts[:-1])):
        problems.append("CREDENTIAL_OR_TRANSIENT_PATH")
    if basename.endswith(BLOCKED_EXTENSIONS):
        problems.append("BINARY_MODEL_OR_PACKAGED_ARTIFACT")
    path = root.joinpath(*name.parts)
    try:
        if path.is_symlink():
            problems.append("TRACKED_SYMLINK")
        elif not path.is_file():
            problems.append("TRACKED_FILE_MISSING")
        elif path.stat().st_size > MAX_TRACKED_BYTES:
            problems.append("TRACKED_FILE_OVERSIZE")
    except OSError:
        problems.append("TRACKED_FILE_UNREADABLE")
    return problems


def scan(root: Path) -> dict:
    root = root.resolve()
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        capture_output=True, check=True, timeout=20,
    )
    paths = [os.fsdecode(part) for part in result.stdout.split(b"\x00") if part]
    if not paths:
        raise ValueError("NO_TRACKED_FILES")
    violations = [
        {"path": path, "reasons": reasons}
        for path in sorted(paths)
        if (reasons := check_entry(root, path))
    ]
    return {
        "schema": "model-mechanisms.public-tree-hygiene/v1",
        "status": "PASS" if not violations else "FAIL",
        "tracked_file_count": len(paths),
        "violations": violations,
        "claims": [
            "Public tracked-path and file-size review only",
            "No source contents, credentials or models read or executed",
            "Not proof of license or secret-value safety",
        ],
    }


def main() -> None:
    report = scan(ROOT)
    print(json.dumps(report, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
