# B3 — MLX wheel code-source parity and artifact inventory

**Stacked dependency:** [public MLX bridge PR #3](https://github.com/SemperSupra/model-mechanisms/pull/3), new-native model adapter `adapters/backends/mlx/meg_phi2`.

## Correctness risk

The existing standard macOS GHA passes six MLX PhiMLP/GPU tests and produces an installable wheel with a SHA256 receipt. But a wheel's digest alone does **not** establish that the archive contains only the reviewed adapter source. Build backends may inadvertently package extra files or altered implementation bytes. The wheel is destined for a high-memory sovereign Mac; inspect its payload before promotion.

## Added independent source-only evidence

`adapters/backends/mlx/meg_phi2/tools/audit_wheel.py` reads the actual emitted wheel and the reviewable source tree and verifies:

1. Exactly the three expected pure-Python package modules match source **byte-for-byte**.
2. No unexpected package/module file, native binary, symlink, traversal member, duplicate name, excessive expansion, or oversized archive.
3. Exact metadata `meg-mlx-bridge==0.1.0`, pure `py3-none-any` wheel tag, complete PEP 427 `RECORD` file list and per-member SHA256.
4. The audited wheel digest is identical to the SHA256 subsequently placed in the build provenance receipt. Persist `wheel-audit.json` with the wheel, synthetic-GPU receipt, and provenance receipt.

A stdlib hostile-wheel fixture independently checks changed code, injected files, altered RECORD entries, and missing modules on free Ubuntu **before** consuming the two public macOS build jobs.

## Deliberate boundaries

This is **build and software supply-chain qualification**, not a full MeG MLX algorithm port, full Phi-2 model inference, model-edit benchmark, or independent scientific reproduction. The audit does not execute the wheel, verify the external upstream author's licensing, sign artifacts, or establish byte-for-byte reproducibility across platform/time; the existing macOS jobs still install the wheel and exercise actual tiny MLX MLP interfaces.

Wheel digest identities should be treated as immutable post-build references for later BigMac installation; no binary is committed to Git. Keep package/version restrictions explicit and review any expansion of its file allowlist.

All CI is on standard free public runners with no model/secret/Kaggle provider access.
