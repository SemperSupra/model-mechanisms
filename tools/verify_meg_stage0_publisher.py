#!/usr/bin/env python3
"""Cross-check original publisher CounterFact-ID artifact vs independent recipe.

Reads official ZIP only in memory; does not execute, import or publish any
third-party author code, model or raw benchmark bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

from meg_reconstruct_stage0 import make_artifacts

OUTER_SHA = "d8abdd06a77318d0af5f6f3414092eafe3b29a3fe10eb890704d6c237c760d71"
INNER_SHA = "10f0cad94529f9d1522a34dad9379e6f7e15ea51f9500180fe4f892edffde088"
RAW_SHA = "977a6acce4705507b5fd6bfcea8f61cd78f9ed0f9cd9c9a6bcd6c8a3ed61c833"
PUBLISHED_SHA = "f36ac1453742dae5481565982fdaefeadd74e5bca957ea4054e63d02c3969afc"
INNER = "code_and_data_for_our_MeG/data_for_our_MeG.zip"
RAW_PATH = "data_for_our_MeG/raw_data/multi_counterfact.json"
PUBLISHED_PATH = "data_for_our_MeG/new_split_data/multi_counterfact_new_id.json"


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compare(raw: bytes, published: bytes) -> dict:
    generated, receipt = make_artifacts(mode="counterfact-ids", input_data=raw)
    byte_match = generated == published
    semantic_match = json.loads(generated) == json.loads(published)
    return {
        "schema": "model-mechanisms.meg-stage0-publisher-parity/v1",
        "result": ("MATCHED_BYTES" if byte_match
                   else "MATCHED_SEMANTICS_ONLY" if semantic_match
                   else "DIVERGED"),
        "input_sha256": hash_bytes(raw),
        "published_output_sha256": hash_bytes(published),
        "reconstruction_sha256": hash_bytes(generated),
        "record_count": receipt["output_records"],
        "byte_equal": byte_match,
        "semantic_equal": semantic_match,
        "claim": "STAGE_ZERO_RECIPE_PARITY_ONLY",
        "author_original_trained_weights_recovered": False,
        "scientific_meg_results_reproduced": False,
    }


def inspect_official_archive(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size > 512_000_000:
        raise ValueError("INVALID_PUBLISHER_ARCHIVE_SIZE")
    outer = path.read_bytes()
    if hash_bytes(outer) != OUTER_SHA:
        raise ValueError("PUBLISHER_OUTER_SHA256_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(outer)) as zp:
        inner = zp.read(INNER)
    if hash_bytes(inner) != INNER_SHA:
        raise ValueError("PUBLISHER_DATA_ARCHIVE_SHA256_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(inner)) as z:
        for name in (RAW_PATH, PUBLISHED_PATH):
            if z.getinfo(name).file_size > 70_000_000:
                raise ValueError("EXCESSIVE_MEMBER")
        raw, published = z.read(RAW_PATH), z.read(PUBLISHED_PATH)
    if hash_bytes(raw) != RAW_SHA or hash_bytes(published) != PUBLISHED_SHA:
        raise ValueError("PUBLISHER_DATA_MEMBER_SHA256_MISMATCH")
    result = compare(raw, published)
    result["official_iclr_outer_sha256"] = OUTER_SHA
    result["official_iclr_data_archive_sha256"] = INNER_SHA
    result["data_redistributed"] = False
    result["author_code_executed"] = False
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-supplement", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    result = inspect_official_archive(args.official_supplement)
    if args.receipt.exists():
        raise SystemExit("REFUSE_OVERWRITE_RECEIPT")
    args.receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if not result["semantic_equal"]:
        raise SystemExit("INDEPENDENT_RECIPE_DIVERGED")


if __name__ == "__main__":
    main()
