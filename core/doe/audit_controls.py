#!/usr/bin/env python3
"""Read-only DOE cross-cell control integrity and admission sanity checks.

Independent of model/backend. Validates that declared comparisons are actually
paired and that a confirmation study cannot silently omit its holdout lock.
No dataset, model, credential, or cloud provider is read or invoked.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas/doe-cell.schema.json"


class InvalidDesign(ValueError):
    pass


def _matched(left: dict, right: dict) -> bool:
    """Scientific pairing fields that should not change across treatment arms."""
    return all((
        left["campaign_id"] == right["campaign_id"],
        left["design_id"] == right["design_id"],
        left["rep_id"] == right["rep_id"],
        left["phase"] == right["phase"],
        left["hypothesis_id"] == right["hypothesis_id"],
        left["workload"]["suite"] == right["workload"]["suite"],
        left["workload"]["split"] == right["workload"]["split"],
        left["workload"]["dataset_ref"] == right["workload"]["dataset_ref"],
        left["workload"].get("holdout_manifest_ref") == right["workload"].get("holdout_manifest_ref"),
        left["execution"]["seed"] == right["execution"]["seed"],
        left["execution"]["environment_ref"] == right["execution"]["environment_ref"],
        left["execution"]["resource_class"] == right["execution"]["resource_class"],
    ))


def validate_cells(cells: list[dict], schema: dict | None = None) -> dict:
    if not isinstance(cells, list) or not cells:
        raise InvalidDesign("EMPTY_OR_INVALID_CELL_SET")
    if len(cells) > 4096:
        raise InvalidDesign("TOO_MANY_CELLS")
    if schema is None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    keyed = {}
    for item in cells:
        errs = list(validator.iter_errors(item))
        if errs:
            raise InvalidDesign("SCHEMA_INVALID:" + errs[0].message[:120])
        key = (item["campaign_id"], item["design_id"], item["cell_id"], item["rep_id"])
        if key in keyed:
            raise InvalidDesign("DUPLICATE_CELL_IDENTITY")
        keyed[key] = item
        if item["phase"] == "confirm":
            outcome = item.get("primary_outcome")
            holdout = item["workload"].get("holdout_manifest_ref")
            if not isinstance(outcome, str) or not outcome.strip():
                raise InvalidDesign("CONFIRMATION_OUTCOME_UNREGISTERED")
            if not isinstance(holdout, str) or not holdout.strip():
                raise InvalidDesign("CONFIRMATION_HOLDOUT_UNREGISTERED")
        exe = item["execution"]
        if bool(exe.get("provider_job_id")) != bool(exe.get("provider_version")):
            raise InvalidDesign("PARTIAL_PROVIDER_IDENTITY")
    for key, item in keyed.items():
        control = item["control"]["comparator_cell_id"]
        if control is None:
            continue
        if control == item["cell_id"]:
            raise InvalidDesign("SELF_CONTROL")
        other = keyed.get((item["campaign_id"], item["design_id"], control, item["rep_id"]))
        if other is None:
            raise InvalidDesign("CONTROL_NOT_IN_DESIGN_AND_REP")
        if not _matched(item, other):
            raise InvalidDesign("UNMATCHED_CONTROL_TASK_SEED_OR_ENVIRONMENT")
        if other["control"]["comparator_cell_id"] is not None:
            raise InvalidDesign("CONTROL_CHAIN_NOT_BASELINE")
        if other["treatment"]["kind"] != "none":
            raise InvalidDesign("CONTROL_TREATED_NOT_BASELINE")
    return {
        "schema": "model-mechanisms.doe-crosscell-audit/v1",
        "status": "PASS",
        "cell_count": len(cells),
        "paired_treatment_count": sum(
            c["control"]["comparator_cell_id"] is not None for c in cells
        ),
        "claims": ["Design metadata only", "No experimental outcome measured"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("documents", nargs="+", type=Path)
    args = parser.parse_args()
    cells = []
    if len(args.documents) > 100:
        raise SystemExit("too many manifest paths")
    for file in args.documents:
        obj = json.loads(file.read_text(encoding="utf-8"))
        if isinstance(obj, list):
            cells.extend(obj)
        else:
            cells.append(obj)
    print(json.dumps(validate_cells(cells), sort_keys=True))


if __name__ == "__main__":
    main()
