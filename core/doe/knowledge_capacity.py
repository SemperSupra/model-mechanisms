#!/usr/bin/env python3
"""Deterministic PLAN ONLY for staged Phi-2 knowledge-capacity comparisons.

No model/data/teacher/controller/weights are accessed, no cloud provider is
called, and no outcome is measured. This is a preregistration planning oracle.
"""
from __future__ import annotations

import argparse
from itertools import product
import json

SCHEMA = "model-mechanisms.knowledge-capacity-plan/v1"
LOADS = (100, 500, 1000)
TASKS = ("direct", "paraphrase", "multihop")
METHODS = (
    "unchanged_phi2",
    "static_lora",
    "deterministic_generator",
    "meg_diffusion",
    "retrieval",
)
BASELINE = "unchanged_phi2"
CLOSED_BOOK = set(METHODS) - {"retrieval"}


def cell_id(load: int, task: str, method: str) -> str:
    return f"facts-{load}/task-{task}/method-{method}"


def make_plan(seed: int = 0, include_scale_tiers: bool = False) -> dict:
    if type(seed) is not int or not 0 <= seed < 2**31:
        raise ValueError("seed must be a bounded nonnegative integer")
    if type(include_scale_tiers) is not bool:
        raise ValueError("include_scale_tiers must be boolean")
    loads = LOADS if include_scale_tiers else LOADS[:1]
    cells = []
    for load, task, method in product(loads, TASKS, METHODS):
        cells.append({
            "cell_id": cell_id(load, task, method),
            "fact_load": load,
            "question_type": task,
            "method": method,
            "knowledge_access": "retrieval_allowed" if method == "retrieval" else "closed_book",
            "baseline_cell_id": cell_id(load, task, BASELINE),
            "seed": seed,
            "tier": "initial_screen" if load == 100 else "conditional_scale",
            "admitted": False,
            "measured": False,
        })
    report = {
        "schema": SCHEMA,
        "status": "PLAN_ONLY",
        "admission": "BLOCKED_DATA_MODEL_CONTROLLER_AND_EVAL_LOCKS",
        "campaign_id": "meg-phi2-knowledge-augmentation-v1",
        "hypothesis": (
            "Diffusion-generated neurons can supply genuinely new verified "
            "facts to Phi-2 more effectively per total system cost than alternatives."
        ),
        "backbone": "microsoft/phi-2",
        "fact_load_levels": list(loads),
        "methods": list(METHODS),
        "question_types": list(TASKS),
        "seed": seed,
        "initial_screen_only": not include_scale_tiers,
        "primary_outcome": "unseen_synthetic_fact_question_accuracy",
        "secondary_outcomes": [
            "paraphrase_accuracy", "multihop_accuracy",
            "existing_knowledge_locality", "unrelated_regressions",
            "controller_bytes", "adapter_bytes", "backbone_bytes",
            "peak_memory_bytes", "inference_latency_ms",
            "training_device_seconds", "inference_device_seconds",
        ],
        "factual_novelty_requirement": (
            "Synthetic entities and relations must be generated and "
            "committed after frozen backbone checkpoint selection; "
            "training and held-out subject groups must be disjoint."
        ),
        "retrieval_is_separate_comparator": True,
        "negative_controls_required_at_confirmation": [
            "shuffled_conditioning", "random_equal_norm_weights",
            "deterministic_generator_same_teacher",
        ],
        "no_drift_assets": {
            "phi2_revision": None,
            "tokenizer_revision": None,
            "teacher_revision": None,
            "me_g_generator_revision": None,
            "static_adapter_revision": None,
            "deterministic_controller_revision": None,
            "dataset_split_digest": None,
            "heldout_group_manifest_digest": None,
            "harness_revision": None,
            "environment_digest": None,
        },
        "cells": cells,
        "notes": [
            "The original MeG paper reproduction remains a separate fixed-protocol campaign.",
            "A model-size comparison must include the controller, adapter and corpus bytes.",
            "Retrieval-allowed scores must not be presented as closed-book knowledge capacity.",
            "500 and 1000 fact tiers remain conditional; no GPU budget committed.",
            "No scientific result can be inferred from a planning or CI PASS.",
        ],
    }
    validate_plan(report)
    return report


def validate_plan(doc: dict) -> None:
    if (doc.get("schema") != SCHEMA or doc.get("status") != "PLAN_ONLY"
        or doc.get("admission") != "BLOCKED_DATA_MODEL_CONTROLLER_AND_EVAL_LOCKS"):
        raise ValueError("not an unadmitted knowledge-capacity plan")
    loads = tuple(doc.get("fact_load_levels", ()))
    if loads not in (LOADS[:1], LOADS):
        raise ValueError("invalid or out-of-order fact-load tiers")
    if doc.get("methods") != list(METHODS) or doc.get("question_types") != list(TASKS):
        raise ValueError("method/task requirements changed")
    if doc.get("retrieval_is_separate_comparator") is not True:
        raise ValueError("retrieval must be separately identified")
    if doc.get("initial_screen_only") is not (loads == LOADS[:1]):
        raise ValueError("screening tier mismatch")
    assets = doc.get("no_drift_assets")
    if not isinstance(assets, dict) or not assets or any(v is not None for v in assets.values()):
        raise ValueError("unapproved experiment artifact identity")
    cells = doc.get("cells")
    expected = {cell_id(n, task, method) for n, task, method in product(loads, TASKS, METHODS)}
    if not isinstance(cells, list) or len(cells) != len(expected):
        raise ValueError("wrong number of matched cells")
    ids = [c.get("cell_id") for c in cells if isinstance(c, dict)]
    if len(ids) != len(expected) or set(ids) != expected:
        raise ValueError("missing, repeated or unexpected cell IDs")
    for c in cells:
        load, task, method = c.get("fact_load"), c.get("question_type"), c.get("method")
        if (load not in loads or task not in TASKS or method not in METHODS
            or c.get("cell_id") != cell_id(load, task, method)
            or c.get("baseline_cell_id") != cell_id(load, task, BASELINE)
            or c.get("knowledge_access") != ("closed_book" if method in CLOSED_BOOK else "retrieval_allowed")
            or c.get("seed") != doc.get("seed")
            or c.get("tier") != ("initial_screen" if load == 100 else "conditional_scale")
            or c.get("admitted") is not False
            or c.get("measured") is not False):
            raise ValueError("cell violates fixed experimental control plan")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--include-conditional-scale", action="store_true")
    args = parser.parse_args()
    print(json.dumps(make_plan(args.seed, args.include_conditional_scale),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
