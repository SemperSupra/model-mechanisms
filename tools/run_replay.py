#!/usr/bin/env python3
"""Run a bounded experiment replay spec without invoking a shell."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

# Preserve the legacy 'python tools/run_replay.py' entrypoint without relying on
# a globally installed package or implicit PYTHONPATH.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.replay_strict import (bounded_run, load_source_safe_spec, strict_json,
                                 validate_source_only_receipt)


ROOT = Path(__file__).resolve().parents[1]


def load_spec(path: Path) -> dict:
    """Validate a source-only replay at the point of execution, not only CI."""
    return load_source_safe_spec(path, ROOT)


def argv_for(spec: dict) -> list[str]:
    argv=[sys.executable,"-m",spec["module"]]
    for key,value in spec["arguments"].items():
        argv.extend([f"--{key.replace('_','-')}",str(value)])
    return argv


def git_head() -> str | None:
    try:
        result=subprocess.run(
            ["git","rev-parse","HEAD"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
        return result.stdout.strip()
    except Exception:
        return None


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_revision() -> str | None:
    return git_head() or os.environ.get("MODEL_MECHANISMS_SOURCE_REVISION")


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("spec",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--metadata",type=Path,required=True)
    args=parser.parse_args()

    spec=load_spec(args.spec)
    argv=argv_for(spec)

    started=time.time()
    perf=time.perf_counter()
    proc=bounded_run(argv, ROOT, spec["timeout_seconds"])
    elapsed=time.perf_counter()-perf

    if proc.returncode != 0:
        sys.stderr.buffer.write(proc.stderr)
        raise SystemExit(proc.returncode)

    # Scientific experiment stdout must be one valid JSON document.
    receipt=strict_json(proc.stdout)
    validate_source_only_receipt(receipt)
    serialized=json.dumps(receipt,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")

    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.metadata.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(serialized+b"\n")

    metadata={
        "schema_version":1,
        "replay_spec_id":spec["id"],
        "replay_spec_sha256":sha256_bytes(
            json.dumps(spec,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")
        ),
        "scientific_receipt_sha256":sha256_bytes(serialized),
        "module":spec["module"],
        "arguments":spec["arguments"],
        "resource_class":spec["resource_class"],
        "environment_ref":spec["environment_ref"],
        "command_argv":argv[1:],
        "git_head":git_head(),
        "source_revision":source_revision(),
        "execution":{
            "started_unix":started,
            "elapsed_seconds":elapsed,
            "python_version":platform.python_version(),
            "python_implementation":platform.python_implementation(),
            "system":platform.system(),
            "release":platform.release(),
            "machine":platform.machine(),
            "github_actions":os.environ.get("GITHUB_ACTIONS")=="true",
            "runner_os":os.environ.get("RUNNER_OS"),
            "runner_arch":os.environ.get("RUNNER_ARCH"),
            "container_contract":os.environ.get("LATENT_REASONING_CONTAINER"),
        },
    }
    args.metadata.write_text(json.dumps(metadata,sort_keys=True)+"\n")

    # Only a compact non-scientific execution summary goes to stdout.
    print(json.dumps({
        "replay_spec_id":spec["id"],
        "scientific_receipt_sha256":metadata["scientific_receipt_sha256"],
        "elapsed_seconds":elapsed,
        "github_actions":metadata["execution"]["github_actions"],
    },sort_keys=True))


if __name__=="__main__":
    main()
