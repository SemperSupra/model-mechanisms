# First accepted-source import inventory (B1)

**Status:** proposed, verification in new-native public CI required. No MeG training, no Phi-2 checkpoint, no MLX model, no scientific effect measured.

| Destination | Source | Source identity | Change |
| --- | --- | --- | --- |
| `tools/run_replay.py` | [legacy runner](https://github.com/SemperSupra/latent-reasoning/blob/c0f7fea8a27825941040e4b4b878841983cc7bc9/tools/run_replay.py) | commit `c0f7fea8a27825941040e4b4b878841983cc7bc9`, blob `432fd6cfebe1f747bae20a1ce70720881bdc0faf` | Same bounded no-shell replay semantics; new `MODEL_MECHANISMS_SOURCE_REVISION` provenance variable; stricter flat module-name grammar |
| `tests/test_replay_runner.py` | [legacy tests](https://github.com/SemperSupra/latent-reasoning/blob/c0f7fea8a27825941040e4b4b878841983cc7bc9/tests/test_replay_runner.py) | blob `9974399c4f18da3f246fe32a821ceac7ad8b8611` | Imported unchanged as backward-compatibility oracle |
| `schemas/replay-spec.schema.json` | [legacy replay spec](https://github.com/SemperSupra/latent-reasoning/blob/c0f7fea8a27825941040e4b4b878841983cc7bc9/schemas/replay-spec.schema.json) | blob `ec081d220f037b1cefcb54c707c951d42b50071b` | Repository schema `$id` and title updated, v1 fields preserved |
| `schemas/doe-cell.schema.json` | New-original Model Mechanisms contract | bootstrap branch | Independent method-neutral experimental treatment/control descriptor, does **not** relabel MeG as latent reasoning |
| `experiments/contract_smoke.py`, `tests/test_model_mechanisms_contracts.py` | New-original public-safe synthetic fixtures | bootstrap branch | No model or benchmark, deterministic hash/oracles |
| `.github/workflows/validate-contracts.yml` | New original public CI | bootstrap branch | Free standard Ubuntu; **no** private checkout, Kaggle secret or GPU |

**No old raw scientific outcomes or model/checkpoint bytes copied.** That evidence remains linked to old issues, immutable commits, and recorded native run receipts.

## Scientific and operational gates

- Passing the new public workflow is only **FRAMEWORK_CONTRACT_PASS**.
- Faithful original MeG/CUDA reproduction will be migrated separately from legacy PR #47 when datasets and exact original artifacts are admitted; no paper results are claimed.
- MLX prebuilt bridging is available in legacy draft PR #48 and must be built + validated on the **new** public macOS CI before being admitted here; these are build tests, not Phi-2/MeG scientific experiments.
- Kaggle direct launch is under separate legacy PR #45. **No credentialed Kaggle workflow in this bootstrap**. New repository does not inherit old secret or protected environment; separate explicit owner/independent review required.
- Private research authority and crosswalk: [new private issue #1](https://github.com/SemperSupra/model-mechanisms-private/issues/1).

This import uses a selected, version-pinned source snapshot and retains the original Git history in the active legacy repository. The new repository is intentionally not a Git mirror.
