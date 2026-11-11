#!/usr/bin/env python3
"""Validate admitted public Model Mechanisms experiment contracts, offline.

No dynamic imports, downloaded model code, provider calls or secrets.
"""
from __future__ import annotations
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate() -> dict:
    doe_schema = load(ROOT / "schemas/doe-cell.schema.json")
    replay_schema = load(ROOT / "schemas/replay-spec.schema.json")
    for schema in (doe_schema, replay_schema):
        Draft202012Validator.check_schema(schema)
    doe = Draft202012Validator(doe_schema)
    replay = Draft202012Validator(replay_schema)
    findings = []
    total = 0

    for filename in sorted((ROOT / "examples").glob("doe-cell.*.json")):
        doc = load(filename)
        total += 1
        for error in doe.iter_errors(doc):
            findings.append(f"{filename.relative_to(ROOT)}: {error.message}")
        env_path = doc.get("execution", {}).get("environment_ref")
        if not isinstance(env_path, str) or not (ROOT / env_path).is_file():
            findings.append(f"{filename.relative_to(ROOT)}: missing environment_ref")
        if doc.get("control", {}).get("comparator_cell_id") == doc.get("cell_id"):
            findings.append(f"{filename.relative_to(ROOT)}: self-comparison")

    for filename in sorted((ROOT / "replays").glob("*.json")):
        doc = load(filename)
        total += 1
        for error in replay.iter_errors(doc):
            findings.append(f"{filename.relative_to(ROOT)}: {error.message}")
        env_path = doc.get("environment_ref")
        if not isinstance(env_path, str) or not (ROOT / env_path).is_file():
            findings.append(f"{filename.relative_to(ROOT)}: missing replay environment")
        module = doc.get("module", "")
        if not isinstance(module, str) or not module.startswith("experiments."):
            findings.append(f"{filename.relative_to(ROOT)}: invalid experiment module")
        else:
            candidate = ROOT / (module.replace(".", "/") + ".py")
            if not candidate.is_file():
                findings.append(f"{filename.relative_to(ROOT)}: module not on disk")

    if findings:
        raise ValueError("\n".join(findings))
    return {"schema": "model-mechanisms.contract-validation/v1",
            "status": "PASS", "validated_documents": total,
            "scientific_result": False}


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
