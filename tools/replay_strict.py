"""Fail-closed, stdlib-only replay admission and bounded subprocess capture.

This module is deliberately scoped to source-safe CPU contract smoke. A future
scientific/GPU executor needs a separately admitted environment and authority.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import threading
from pathlib import Path

MAX_JSON_BYTES = 1 << 20
MAX_CAPTURE_BYTES = 1 << 20
MAX_SMOKE_SECONDS = 120
SPEC_FIELDS = frozenset({
    "schema_version", "id", "resource_class", "environment_ref",
    "module", "arguments", "timeout_seconds",
})
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._/-]*$")
MODULE = re.compile(r"^experiments\.[A-Za-z][A-Za-z0-9_]*$")
ENVIRONMENT = re.compile(r"^environments/[A-Za-z0-9_-]+\.json$")
ARGUMENT_KEY = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


def _unique_object(items: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError(f"DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def _reject_constant(value: str):
    raise ValueError(f"NONFINITE_JSON_CONSTANT:{value}")


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("NONFINITE_JSON_NUMBER")
    return number


def _limited_int(value: str) -> int:
    if len(value.lstrip("-")) > 128:
        raise ValueError("OVERSIZED_JSON_INTEGER")
    return int(value)


def strict_json(raw: bytes):
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError("JSON_BYTE_BUDGET_EXCEEDED")
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
            parse_float=_finite_float,
            parse_int=_limited_int,
        )
    except (UnicodeError, RecursionError) as exc:
        raise ValueError("INVALID_UTF8_OR_JSON_NESTING") from exc


def load_source_safe_spec(path: Path, root: Path) -> dict:
    # This direct executor is for admitted model-free CPU experiments only.
    with path.open("rb") as f:
        raw = f.read(MAX_JSON_BYTES + 1)
    spec = strict_json(raw)
    if not isinstance(spec, dict) or set(spec) != SPEC_FIELDS:
        raise ValueError("REPLAY_SCHEMA_FIELDS_MISMATCH")
    if type(spec["schema_version"]) is not int or spec["schema_version"] != 1:
        raise ValueError("UNSUPPORTED_REPLAY_SCHEMA")
    if not isinstance(spec["id"], str) or not IDENTIFIER.fullmatch(spec["id"]):
        raise ValueError("INVALID_REPLAY_ID")
    if spec["resource_class"] != "cpu":
        raise ValueError("GPU_OR_OTHER_RESOURCE_NOT_ADMITTED_ON_SOURCE_ONLY_REPLAY")
    mod = spec["module"]
    if not isinstance(mod, str) or not MODULE.fullmatch(mod):
        raise ValueError("MODULE_OUTSIDE_EXPERIMENTS")
    args = spec["arguments"]
    if not isinstance(args, dict):
        raise ValueError("ARGUMENTS_NOT_OBJECT")
    for key, value in args.items():
        if not ARGUMENT_KEY.fullmatch(key):
            raise ValueError("INVALID_ARGUMENT_NAME")
        if type(value) not in (str, int, float):
            raise ValueError("INVALID_ARGUMENT_TYPE")
        if type(value) is float and not math.isfinite(value):
            raise ValueError("NONFINITE_ARGUMENT")
        if type(value) is int and abs(value) > (1 << 63) - 1:
            raise ValueError("ARGUMENT_INTEGER_OUT_OF_RANGE")
        if type(value) is str and (len(value) > 4096 or "\x00" in value):
            raise ValueError("ARGUMENT_STRING_OUT_OF_RANGE")
    timeout = spec["timeout_seconds"]
    if type(timeout) is not int or not (1 <= timeout <= MAX_SMOKE_SECONDS):
        raise ValueError("INVALID_SOURCE_ONLY_TIMEOUT")
    env_ref = spec["environment_ref"]
    if not isinstance(env_ref, str) or not ENVIRONMENT.fullmatch(env_ref):
        raise ValueError("UNADMITTED_ENVIRONMENT_PATH")
    env_path = root / env_ref
    if env_path.is_symlink() or not env_path.is_file():
        raise ValueError("ENVIRONMENT_NOT_PINNED_IN_REPOSITORY")
    with env_path.open("rb") as f:
        env = strict_json(f.read(MAX_JSON_BYTES + 1))
    if not isinstance(env, dict):
        raise ValueError("INVALID_ENVIRONMENT_MANIFEST")
    if (type(env.get("schema_version")) is not int or env["schema_version"] != 1
            or env.get("runtime") != "python"
            or env.get("resource_class") != "cpu"
            or env.get("claim") != "source_only_contract_smoke"
            or env.get("requirements_file") is not None
            or env.get("execution_surface") != "public-github-actions-standard"):
        raise ValueError("UNADMITTED_ENVIRONMENT_CLASS")
    allowed = env.get("allowed_modules")
    if not isinstance(allowed, list) or not allowed or any(
        not isinstance(m, str) or not MODULE.fullmatch(m) for m in allowed
    ) or len(allowed) != len(set(allowed)) or mod not in allowed:
        raise ValueError("MODULE_NOT_ADMITTED_BY_ENVIRONMENT")
    module_path = root / (mod.replace(".", "/") + ".py")
    if module_path.is_symlink() or not module_path.is_file():
        raise ValueError("SOURCE_MODULE_NOT_PINNED_IN_REPOSITORY")
    return spec


def bounded_run(argv: list[str], root: Path, timeout_seconds: int):
    """Capture at most 1MiB per stream, kill noisy or timed-out children.

    Separate reader threads avoid pipe deadlocks and unbounded memory buffers.
    This is not a substitute for OS-level CPU, memory and namespace limits.
    """
    proc = subprocess.Popen(
        argv, cwd=root, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,
    )
    chunks = {"stdout": bytearray(), "stderr": bytearray()}
    overflow = threading.Event()

    def drain(kind: str, pipe):
        try:
            while True:
                chunk = pipe.read(16384)
                if not chunk:
                    break
                out = chunks[kind]
                available = MAX_CAPTURE_BYTES - len(out)
                if len(chunk) > available:
                    out.extend(chunk[:max(0, available)])
                    overflow.set()
                    proc.kill()
                    break
                out.extend(chunk)
        finally:
            pipe.close()

    threads = [
        threading.Thread(target=drain, args=("stdout", proc.stdout), daemon=True),
        threading.Thread(target=drain, args=("stderr", proc.stderr), daemon=True),
    ]
    for th in threads:
        th.start()
    try:
        code = proc.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        proc.kill()
        proc.wait()
        raise TimeoutError("REPLAY_EXECUTION_TIMEOUT") from exc
    finally:
        for th in threads:
            th.join(timeout=5)
    if overflow.is_set():
        raise ValueError("REPLAY_OUTPUT_BYTE_BUDGET_EXCEEDED")
    return subprocess.CompletedProcess(argv, code, bytes(chunks["stdout"]), bytes(chunks["stderr"]))


def validate_source_only_receipt(receipt) -> None:
    if not isinstance(receipt, dict):
        raise ValueError("RECEIPT_NOT_OBJECT")
    if (receipt.get("claim") != "model_free_contract_smoke_only"
            or receipt.get("model_loaded") is not False
            or receipt.get("scientific_result") is not False):
        raise ValueError("RECEIPT_FALSE_SCIENTIFIC_CLAIM")
    json.dumps(receipt, allow_nan=False)
