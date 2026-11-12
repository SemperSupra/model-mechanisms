#!/usr/bin/env python3
"""Inspect ICLR MeG supplementary ZIP metadata without extracting or executing.

Output is a sanitized content/filename digest inventory. Third-party code or
model bytes are never imported, extracted or copied into repository artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from pathlib import PurePosixPath
import stat
import zipfile

MAX_ARCHIVE_BYTES = 512_000_000
MAX_MEMBER_BYTES = 512_000_000
MAX_UNPACKED_TOTAL = 1_500_000_000
MAX_FILES = 2000
ICLR_SUPPLEMENT_URL = (
    "https://proceedings.iclr.cc/paper_files/paper/2026/file/"
    "7926a9c34166da5a6a681cc0fe6d8a28-Supplemental-Conference.zip"
)
INTERESTING = ("prompt", "config", "hyper", "dataset", "zsre", "counterfact",
               "checkpoint", "weight", "familiar", "encoder", "rephrase", "repro",
               "seed", "random", "script", "train", "evaluation", "readme", "license")


def sha_stream(stream) -> str:
    h = hashlib.sha256()
    while chunk := stream.read(1024 * 256):
        h.update(chunk)
    return h.hexdigest()


def inspect(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("SUPPLEMENT_ARCHIVE_MISSING_OR_TOO_LARGE")
    with path.open("rb") as fp:
        archive_sha = sha_stream(fp)
    if not zipfile.is_zipfile(path):
        raise ValueError("NOT_A_ZIP_SUPPLEMENT")
    members = []
    total_size = 0
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if not 1 <= len(entries) <= MAX_FILES:
            raise ValueError("INVALID_MEMBER_COUNT")
        seen = set()
        for entry in entries:
            name = entry.filename
            item = PurePosixPath(name)
            if (name.startswith("/") or "\\" in name or not item.parts
                or any(c in ("", ".", "..") for c in name.split("/") if c != name.split("/")[-1])
                or ".." in item.parts or name in seen):
                raise ValueError("UNSAFE_OR_DUPLICATE_MEMBER")
            seen.add(name)
            if stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError("SYMLINK_IN_SUPPLEMENT")
            if entry.flag_bits & 1:
                raise ValueError("ENCRYPTED_SUPPLEMENT_MEMBER")
            if entry.file_size > MAX_MEMBER_BYTES:
                raise ValueError("OVERSIZED_SUPPLEMENT_MEMBER")
            total_size += entry.file_size
            if total_size > MAX_UNPACKED_TOTAL:
                raise ValueError("ZIP_BOMB_SIZE")
            if entry.is_dir():
                continue
            with archive.open(entry) as stream:
                digest = sha_stream(stream)
            members.append({
                "name": name,
                "sha256": digest,
                "bytes": entry.file_size,
                "possible_protocol_input": any(k in name.lower() for k in INTERESTING),
            })
    return {
        "schema": "model-mechanisms.iclr-supplement-inventory/v1",
        "status": "METADATA_INSPECTED_ONLY",
        "source": ICLR_SUPPLEMENT_URL,
        "archive_sha256": archive_sha,
        "archive_bytes": path.stat().st_size,
        "member_count": len(members),
        "members": members,
        "files_extracted": False,
        "third_party_code_executed": False,
        "author_checkpoint_recovered": False,
        "paper_reproduced": False,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--zip", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    report = inspect(args.zip)
    if args.output.exists():
        raise SystemExit("REFUSE_OVERWRITE")
    with args.output.open("x", encoding="utf-8") as file:
        json.dump(report, file, indent=2, sort_keys=True)
    print(json.dumps({
        "schema": report["schema"], "status": report["status"],
        "archive_sha256": report["archive_sha256"],
        "member_count": report["member_count"],
        "possible_protocol_inputs": [i["name"] for i in report["members"] if i["possible_protocol_input"]],
        "members": [{"name": i["name"], "bytes": i["bytes"], "sha256": i["sha256"]} for i in report["members"]],
        "author_checkpoint_recovered": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
