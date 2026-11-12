#!/usr/bin/env python3
"""Inspect ICLR MeG supplementary ZIP metadata without extracting or executing.

Output is a sanitized content/filename digest inventory. Third-party code or
model bytes are never imported, extracted or copied into repository artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import io
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


def inspect_inner_zip(raw: bytes, origin: str) -> dict:
    """Inspect one embedded ZIP level only, with byte and member limits.

    The nested archive stays inside process memory; nothing is extracted to
    disk or installed. No further recursive ZIP traversal is attempted.
    """
    if len(raw) > MAX_ARCHIVE_BYTES:
        raise ValueError("NESTED_ARCHIVE_OVERSIZED")
    items = []
    total = 0
    with zipfile.ZipFile(io.BytesIO(raw)) as zip_file:
        infos = zip_file.infolist()
        if not 1 <= len(infos) <= MAX_FILES:
            raise ValueError("NESTED_INVALID_MEMBER_COUNT")
        seen = set()
        for ent in infos:
            name = ent.filename
            path = PurePosixPath(name)
            if (not name or name.startswith("/") or "\\" in name
                or ".." in path.parts or name in seen):
                raise ValueError("NESTED_UNSAFE_OR_DUPLICATE_MEMBER")
            seen.add(name)
            if stat.S_ISLNK(ent.external_attr >> 16) or ent.flag_bits & 1:
                raise ValueError("NESTED_SYMLINK_OR_ENCRYPTION")
            if ent.file_size > MAX_MEMBER_BYTES:
                raise ValueError("NESTED_MEMBER_OVERSIZED")
            total += ent.file_size
            if total > MAX_UNPACKED_TOTAL:
                raise ValueError("NESTED_ZIP_BOMB_SIZE")
            if ent.is_dir():
                continue
            with zip_file.open(ent) as stream:
                digest = sha_stream(stream)
            items.append({
                "name": name,
                "sha256": digest,
                "bytes": ent.file_size,
                "possible_protocol_input": any(k in name.lower() for k in INTERESTING),
            })
    return {
        "outer_member": origin,
        "archive_sha256": hashlib.sha256(raw).hexdigest(),
        "member_count": len(items),
        "uncompressed_bytes": total,
        "members": items,
        "extracted": False,
        "executed": False,
    }


def inspect(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("SUPPLEMENT_ARCHIVE_MISSING_OR_TOO_LARGE")
    with path.open("rb") as fp:
        archive_sha = sha_stream(fp)
    if not zipfile.is_zipfile(path):
        raise ValueError("NOT_A_ZIP_SUPPLEMENT")
    members = []
    nested_archives = []
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
            if name.lower().endswith(".zip"):
                with archive.open(entry) as stream:
                    nested = stream.read(MAX_ARCHIVE_BYTES + 1)
                nested_archives.append(inspect_inner_zip(nested, name))
    return {
        "schema": "model-mechanisms.iclr-supplement-inventory/v1",
        "status": "METADATA_INSPECTED_ONLY",
        "source": ICLR_SUPPLEMENT_URL,
        "archive_sha256": archive_sha,
        "archive_bytes": path.stat().st_size,
        "member_count": len(members),
        "members": members,
        "nested_archives": nested_archives,
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
        "nested": [
            {
                "outer_member": n["outer_member"],
                "member_count": n["member_count"],
                "uncompressed_bytes": n["uncompressed_bytes"],
                "members": [
                    {"name": m["name"], "bytes": m["bytes"], "sha256": m["sha256"]}
                    for m in n["members"][:150]
                ],
                "truncated_in_log": len(n["members"]) > 150,
            }
            for n in report["nested_archives"]
        ],
        "author_checkpoint_recovered": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
