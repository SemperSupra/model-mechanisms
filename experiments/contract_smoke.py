#!/usr/bin/env python3
"""Model-free, deterministic public-safe replay fixture; not a scientific result."""
import argparse
import hashlib
import json
import random


def run(seed: int, count: int) -> dict:
    if seed < 0 or not 1 <= count <= 1024:
        raise ValueError("out-of-range synthetic fixture parameters")
    rng = random.Random(seed)
    values = [rng.randrange(0, 2**16) for _ in range(count)]
    payload = json.dumps(values, separators=(",", ":")).encode()
    return {
        "schema": "model-mechanisms.synthetic-replay/v1",
        "state": "PASS",
        "claim": "model_free_contract_smoke_only",
        "seed": seed,
        "count": count,
        "values_sha256": hashlib.sha256(payload).hexdigest(),
        "model_loaded": False,
        "scientific_result": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--count", type=int, default=16)
    args = parser.parse_args()
    print(json.dumps(run(args.seed, args.count), sort_keys=True))
