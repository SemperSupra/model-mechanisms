#!/usr/bin/env python3
"""Independent, deterministic stage-zero MeG data reconstruction primitives.

Original reimplementation of two published simple transformations, not a copy
of author source. No models, network, GPU, dependencies or provider APIs.
Original trained artifacts, RNG state, and data are NOT recovered by this tool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random

MAX_INPUT_BYTES = 180_000_000
MAX_RECORDS = 1_000_000
MAX_FAMILIARITY_COUNT = 10_000


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_records(source: Path) -> tuple[list[dict], bytes]:
    if not source.is_file() or source.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("SOURCE_MISSING_OR_OVERSIZED")
    raw = source.read_bytes()
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("SOURCE_OVERSIZED")
    parsed = json.loads(raw)
    if (not isinstance(parsed, list)
        or len(parsed) > MAX_RECORDS
        or not all(isinstance(x, dict) for x in parsed)):
        raise ValueError("SOURCE_MUST_BE_BOUNDED_RECORD_LIST")
    return parsed, raw


def reconstruct_counterfact_ids(records: list[dict]) -> list[dict]:
    """CounterFact source-order indexing; original source adds id=0,1,..."""
    if not isinstance(records, list) or not all(isinstance(x, dict) for x in records):
        raise ValueError("INVALID_RECORD_LIST")
    return [{**item, "id": i} for i, item in enumerate(records)]


def reconstruct_familiarity_labels(
    records: list[dict], *, seed: int, count: int = MAX_FAMILIARITY_COUNT
) -> list[dict]:
    """Seeded independent facsimile of original unseeded randint(0,9) labels.

    A fixed seed makes this NEW derivation replayable; it does not reproduce
    unknown author RNG state or original-label bytes.
    """
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("SEED_REQUIRED_AND_BOUNDED")
    if type(count) is not int or not 1 <= count <= MAX_FAMILIARITY_COUNT:
        raise ValueError("INVALID_COUNT")
    if not isinstance(records, list) or not all(isinstance(x, dict) for x in records):
        raise ValueError("INVALID_RECORD_LIST")
    rng = random.Random(seed)
    return [{**item, "fake_label": rng.randint(0, 9)}
            for item in records[:count]]


def serialize_records(records: list[dict]) -> bytes:
    """JSON formatting follows the disclosed author's Python indent-4 layout.

    Output byte equivalence requires identical records *and* serialization,
    not just comparable JSON values.
    """
    return json.dumps(records, indent=4, ensure_ascii=True).encode("utf-8")


def make_artifacts(
    *, mode: str, input_data: bytes, seed: int | None = None,
    count: int = MAX_FAMILIARITY_COUNT
) -> tuple[bytes, dict]:
    records = json.loads(input_data)
    if (not isinstance(records, list)
        or len(records) > MAX_RECORDS
        or not all(isinstance(x, dict) for x in records)):
        raise ValueError("INVALID_INPUT_RECORDS")
    if mode == "counterfact-ids":
        if seed is not None:
            raise ValueError("COUNTERFACT_IDS_DOES_NOT_USE_RNG")
        result = reconstruct_counterfact_ids(records)
        derivation = "counterfact-id-order-v1"
    elif mode == "familiarity-labels":
        if seed is None:
            raise ValueError("FAMILIARITY_LABELS_REQUIRE_EXPLICIT_SEED")
        result = reconstruct_familiarity_labels(records, seed=seed, count=count)
        derivation = "familiarity-class-rng-v1"
    else:
        raise ValueError("UNKNOWN_MODE")
    out_bytes = serialize_records(result)
    return out_bytes, {
        "schema": "model-mechanisms.meg-derived-data/v1",
        "status": "RECONSTRUCTED_DERIVATIVE",
        "source_method": "independent-reimplementation-of-released-transformation",
        "upstream_meg_revision": "9fa8ae10cf33c82dd2200057f70dfcb73388cd74",
        "derivation_id": derivation,
        "input_sha256": sha256(input_data),
        "output_sha256": sha256(out_bytes),
        "input_records": len(records),
        "output_records": len(result),
        "random_seed": seed,
        "count_limit": count if seed is not None else None,
        "claim": "NOT_AUTHOR_IDENTICAL",
        "author_original_weights_recovered": False,
        "original_random_state_recovered": False,
        "scientific_reproduction_complete": False,
        "third_party_code_executed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("counterfact-ids", "familiarity-labels"), required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--count", type=int, default=MAX_FAMILIARITY_COUNT)
    args = parser.parse_args()

    paths = [p.resolve() for p in (args.input, args.output, args.receipt)]
    if len(set(paths)) != 3 or any(p.exists() for p in paths[1:]):
        raise SystemExit("OUTPUT_PATHS_MUST_BE_DISTINCT_AND_NEW")
    if args.mode == "counterfact-ids" and args.count != MAX_FAMILIARITY_COUNT:
        raise SystemExit("COUNTERFACT_MODE_DISALLOWS_COUNT")
    _, input_data = load_records(args.input)
    output, receipt = make_artifacts(
        mode=args.mode, input_data=input_data, seed=args.seed, count=args.count
    )
    # Refuse overwrite: irreversible data-provenance collisions are unacceptable.
    with args.output.open("xb") as stream:
        stream.write(output)
    with args.receipt.open("xb") as stream:
        stream.write((json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
