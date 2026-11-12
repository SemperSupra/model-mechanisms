#!/usr/bin/env python3
"""Plan-only, deterministic full 2^4 loop-mask screen for recurrent editing.

This module emits a scientific DESIGN and never imports a model, controller,
dataset, GPU runtime, provider SDK or credentials. It deliberately fails
admission until all study assets are independently fixed and approved.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
from itertools import product
import json
from pathlib import Path


SCHEMA = "model-mechanisms.loop-placement-plan/v1"
DEPTH = 4
CONTROLS = (
    "untreated_baseline",
    "shuffled_conditioning",
    "equal_norm_random_intervention",
    "compute_matched_unedited",
)


def nominal_strength(mask: str, total: Fraction = Fraction(1, 1)) -> str:
    """Return exact rational per-active-pass strength (never a rounded float).

    Equal nominal summed strength does not imply matched effective activation
    norm, wall time, cumulative change, or generated-weight compute.
    """
    if not mask or any(ch not in "01" for ch in mask):
        raise ValueError("loop_mask must be a nonempty binary string")
    active = mask.count("1")
    if not active:
        return "0"
    return str(total / active)


def make_plan(seed: int = 0) -> dict:
    if type(seed) is not int or not 0 <= seed <= 2**31 - 1:
        raise ValueError("seed must be a bounded nonnegative integer")
    cells = []
    # Keep the mask's leftmost bit tied to the FIRST (not last) recurrent pass.
    for bits in product("01", repeat=DEPTH):
        mask = "".join(bits)
        active = mask.count("1")
        cells.append({
            "cell_id": f"mask-{mask}",
            "loop_mask": mask,
            "active_pass_count": active,
            "pass_order": "left_to_right_earliest_to_latest",
            "treatment": "untreated_baseline" if active == 0 else "same_frozen_intervention",
            "nominal_strength_each_active_pass": nominal_strength(mask),
            "reference_control_cell_id": "mask-0000",
            "seed": seed,
            "admitted": False,
            "measured": False,
        })
    plan = {
        "schema": SCHEMA,
        "status": "PLAN_ONLY",
        "admission": "BLOCKED_UNPINNED_ASSETS_AND_PROTOCOL",
        "campaign_id": "dory-loop-knowledge-v1",
        "design_id": "four-loop-full-mask-screen-v1",
        "hypothesis": "loop placement changes the effectiveness of externally supplied knowledge",
        "model_family": "Dory",
        "loop_depth": DEPTH,
        "factor": "pass_specific_intervention_enabled",
        "factor_levels": ["0", "1"],
        "nominal_total_treatment_strength": "1",
        "strength_comparison_caveat": (
            "Equal nominal summed intervention strength does not equalize "
            "resulting activation norm, latency, energy or controller cost."
        ),
        "controls_required_beyond_mask_zero": list(CONTROLS[1:]),
        "primary_outcome": "heldout_novel_fact_accuracy",
        "secondary_outcomes": [
            "generality", "locality", "multihop_accuracy", "unrelated_fact_regression",
            "wall_time_s", "device_seconds", "peak_memory_bytes",
            "controller_bytes", "generated_weight_bytes",
        ],
        "frozen_inputs": {
            "backbone_revision": None,
            "controller_revision": None,
            "dataset_split_digest": None,
            "holdout_manifest_digest": None,
            "evaluation_harness_revision": None,
            "runtime_environment_digest": None,
        },
        "matched_task_ids_digest": None,
        "seed": seed,
        "cells": cells,
        "notes": [
            "No claims about functional roles of earlier or later loops.",
            "All cells are unadmitted and unmeasured, including the baseline.",
            "No model, training, inference or cloud job is launched by this plan.",
            "Do not select a winning mask on the confirmation holdout.",
        ],
    }
    validate_plan(plan)
    return plan


def validate_plan(plan: dict) -> None:
    if plan.get("schema") != SCHEMA or plan.get("status") != "PLAN_ONLY":
        raise ValueError("not a plan-only screen")
    if plan.get("admission") != "BLOCKED_UNPINNED_ASSETS_AND_PROTOCOL":
        raise ValueError("unapproved scientific admission state")
    if plan.get("loop_depth") != DEPTH:
        raise ValueError("unexpected loop depth")
    cells = plan.get("cells")
    expected = {"".join(bits) for bits in product("01", repeat=DEPTH)}
    if not isinstance(cells, list) or len(cells) != len(expected):
        raise ValueError("requires every one of the 16 masks")
    observed = [cell.get("loop_mask") for cell in cells if isinstance(cell, dict)]
    if len(observed) != len(expected) or set(observed) != expected:
        raise ValueError("missing, duplicated or invalid loop masks")
    for cell in cells:
        mask = cell["loop_mask"]
        if (cell.get("cell_id") != f"mask-{mask}"
            or cell.get("reference_control_cell_id") != "mask-0000"
            or cell.get("active_pass_count") != mask.count("1")
            or cell.get("nominal_strength_each_active_pass") != nominal_strength(mask)
            or cell.get("admitted") is not False
            or cell.get("measured") is not False):
            raise ValueError("cell differs from fixed, unadmitted study contract")
    assets = plan.get("frozen_inputs")
    if not isinstance(assets, dict) or any(v is not None for v in assets.values()):
        raise ValueError("this design is unpinned; asset fields must remain null")
    if plan.get("matched_task_ids_digest") is not None:
        raise ValueError("heldout tasks cannot be injected into public plan")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    report = json.dumps(make_plan(args.seed), sort_keys=True, indent=2) + "\n"
    if args.output is None:
        print(report, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
