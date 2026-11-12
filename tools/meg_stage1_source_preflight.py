#!/usr/bin/env python3
"""Independent Stage-1 MeG Phi-2/ZsRE numerical and protocol preflight.

Read-only inspection of author's exact SHA-pinned text, never execute/import
its code. Pure stdlib InfoNCE reference oracle operates on synthetic vectors;
this is not a BERT model, optimizer, training result or GPU workload.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import re

AUTHOR_REVISION = "9fa8ae10cf33c82dd2200057f70dfcb73388cd74"
TRAIN_BLOB_SHA1 = "df2f3eaa23dda322657f2821ffef899f11273bc7"
CONFIG_BLOB_SHA1 = "86cb6baa036fd5da0ba50f465f0f42d55add7366"
SUPPORTED_KEYS = {
    "gpu", "model_para_type", "data_type", "temperature",
    "epochs", "batch_size", "lr", "data_dir",
}
EXPECTED_CONFIG = {
    "gpu": 3, "model_para_type": "phi2", "data_type": "zsre",
    "temperature": 1.0, "epochs": 30000, "batch_size": 4000,
    "lr": 1e-4, "data_dir": "data/new_split_data/zsre_for_bert_train.json",
}

def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def parse_fixed_config(raw: bytes) -> dict:
    if git_blob_sha1(raw) != CONFIG_BLOB_SHA1:
        raise ValueError("AUTHOR_STAGE1_CONFIG_BLOB_MISMATCH")
    mapping = {}
    for line in raw.decode("utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError("UNSUPPORTED_CONFIG_LINE")
        k, v = [x.strip() for x in line.split(":", 1)]
        if k in mapping or k not in SUPPORTED_KEYS or not v:
            raise ValueError("UNEXPECTED_CONFIG_KEY")
        mapping[k] = v
    values = {
        "gpu": int(mapping["gpu"]),
        "model_para_type": mapping["model_para_type"],
        "data_type": mapping["data_type"],
        "temperature": float(mapping["temperature"]),
        "epochs": int(mapping["epochs"]),
        "batch_size": int(mapping["batch_size"]),
        "lr": float(mapping["lr"]),
        "data_dir": mapping["data_dir"],
    }
    if values != EXPECTED_CONFIG or set(mapping) != SUPPORTED_KEYS:
        raise ValueError("SOURCE_CONFIG_VALUE_DRIFT")
    return values

def inspect_source(raw: bytes) -> dict:
    if git_blob_sha1(raw) != TRAIN_BLOB_SHA1:
        raise ValueError("AUTHOR_STAGE1_TRAIN_BLOB_MISMATCH")
    source = raw.decode("utf-8")
    module = ast.parse(source)
    funcs = {node.name: node for node in module.body if isinstance(node, ast.FunctionDef)}
    if not {"train_model", "val", "info_nce_loss", "CustomDataset"}.intersection(funcs) >= {"train_model", "val", "info_nce_loss"}:
        raise ValueError("EXPECTED_TRAINING_FUNCTIONS_MISSING")
    tr = funcs["train_model"]
    calls = []
    for node in ast.walk(tr):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                calls.append((node.func.value.id, node.func.attr))
    steps = sum(1 for a, b in calls if a == "optimizer" and b == "step")
    resets = sum(1 for a, b in calls if a == "optimizer" and b == "zero_grad")
    # Immutable author revision, not rewritten code: this is a factual audit.
    if steps != 1:
        raise ValueError("UNEXPECTED_OPTIMIZER_PROTOCOL")
    if "raw_data = self.orig_data[-2000:]" not in source:
        raise ValueError("EXPECTED_TRAINING_SLICE_MISSING")
    if "raw_data=raw_data[0:1024]" not in source:
        raise ValueError("EXPECTED_VALIDATION_SLICE_MISSING")
    if "if index < 2:" not in source:
        raise ValueError("EXPECTED_REPHRASE_COUNT_MISSING")
    return {
        "source_git_blob_sha1": TRAIN_BLOB_SHA1,
        "training_source_last_records": 2000,
        "validation_first_records": 1024,
        "train_zsre_max_rephrases_per_record": 2,
        "optimizer_step_call_sites": steps,
        "optimizer_zero_grad_call_sites_in_train_model": resets,
        "gradient_reset_present_in_train_model": resets > 0,
        "warning": ("NO_PER_BATCH_OPTIMIZER_ZERO_GRAD_IN_RELEASED_TRAIN_MODEL"
                    if not resets else "RESET_CALL_PRESENT"),
    }

def unit(row: list[float]) -> list[float]:
    norm = math.sqrt(sum(v*v for v in row))
    if norm <= 0 or not math.isfinite(norm):
        raise ValueError("INVALID_ZERO_OR_NONFINITE_VECTOR")
    return [v/norm for v in row]

def info_nce_reference(
    queries: list[list[float]],
    positives: list[list[float]],
    negative_keys: list[list[float]],
    temperature: float,
) -> float:
    """Independent scalar equivalent of released diagonal-masked InfoNCE.

    Positive is query_i dot positive_i. All negative_key_j except j=i are
    denominator negatives. For batch=1 the loss is zero and gives no signal.
    """
    n = len(queries)
    if not isinstance(temperature, (float, int)) or not math.isfinite(temperature) or temperature <= 0:
        raise ValueError("INVALID_TEMPERATURE")
    if n < 1 or n != len(positives) or n != len(negative_keys) or n > 4096:
        raise ValueError("INVALID_BATCH_SIZES")
    dims = {len(v) for v in queries + positives + negative_keys}
    if len(dims) != 1 or next(iter(dims)) < 1:
        raise ValueError("VECTOR_DIMENSION_MISMATCH")
    qs, ps, ks = [[unit(row) for row in batch] for batch in (queries, positives, negative_keys)]
    results = []
    for i in range(n):
        logits = [sum(a*b for a,b in zip(qs[i], ps[i])) / temperature]
        logits.extend(
            sum(a*b for a,b in zip(qs[i], ks[j])) / temperature
            for j in range(n) if j != i
        )
        hi = max(logits)
        log_den = hi + math.log(sum(math.exp(x-hi) for x in logits))
        results.append(log_den - logits[0])
    return sum(results)/n

def report(source: bytes, config: bytes) -> dict:
    src = inspect_source(source)
    cfg = parse_fixed_config(config)
    result = {
        "schema": "model-mechanisms.meg-stage1-source-preflight/v1",
        "status": "SOURCE_AND_MATH_PREFLIGHT_ONLY",
        "method": "MeG Phi2 ZsRE stage1 BERT contrastive training",
        "author_source_revision": AUTHOR_REVISION,
        "config_git_blob_sha1": CONFIG_BLOB_SHA1,
        "config": cfg,
        "source_audit": src,
        "cpu_oracle": {
            "two_sample_cosine_loss": info_nce_reference(
                [[1.,0.],[0.,1.]], [[1.,0.],[0.,1.]], [[1.,0.],[0.,1.]], 1.0),
            "single_sample_loss": info_nce_reference(
                [[1.,0.]], [[1.,0.]], [[1.,0.]], 1.0),
        },
        "deployment_risk": (
            "Original 30000-epoch requested configuration and absent per-batch "
            "gradient reset require scoped budget/experimental decision; "
            "source code must not be silently patched."
        ),
        "model_loaded": False, "checkpoint_created": False,
        "science_reproduced": False, "provider_job_submitted": False,
    }
    return result

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--author-train",type=Path,required=True)
    parser.add_argument("--author-config",type=Path,required=True)
    parser.add_argument("--receipt",type=Path,required=True)
    args=parser.parse_args()
    if args.receipt.exists():raise SystemExit("REFUSE_OVERWRITE")
    document=report(args.author_train.read_bytes(), args.author_config.read_bytes())
    args.receipt.write_text(json.dumps(document,indent=2,sort_keys=True)+"\n")
    print(json.dumps(document,sort_keys=True))

if __name__=="__main__":main()
