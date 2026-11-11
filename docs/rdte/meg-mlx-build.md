# MLX Phi-2 bridge — prebuilt package, not a research experiment

**Purpose:** compile, install, and test a reusable MLX-native, MeG-style Phi-2 neuron-editing bridge on *free standard public macOS GitHub Actions runners*. The **scientific MeG experiment** runs later on a sufficiently provisioned local Mac after the complete controller has been ported and compared against the original PyTorch/CUDA method.

## Source and migration provenance

Selected vertical-slice import from legacy [latent-reasoning PR #48](https://github.com/SemperSupra/latent-reasoning/pull/48), exact head `8e25447313fd2be95568d1bf639373e47ffa4677`. Files moved from `experiments/meg_mlx` to `adapters/backends/mlx/meg_phi2` without algorithmic changes.

| New path suffix | Legacy Git blob SHA |
| --- | --- |
| `pyproject.toml` | `8e3326f080d3ba9bc5cb770b8a2fad1113aa71fd` |
| `src/meg_mlx_bridge/__init__.py` | `6aad28023e9b99107a6616eaac327c94211fa98d` |
| `src/meg_mlx_bridge/controller.py` | `ed8fe8acb000fa9cec58a67f01742ed4ebba4b9a` |
| `src/meg_mlx_bridge/phi2.py` | `1fbdcc1300ccb7bd726c03ed1f4c02bbd8e8a8e2` |
| `tests/test_phi2_bridge.py` | `f8532140dc439b3a901ca7d040c4529c878ec32c` |
| `surrogate_gpu.py` | `0bedfa5c551988f44fc20427e48e1c5d6924a940` |
| `.github/workflows/meg-mlx-build.yml` | adapted from legacy workflow blob `a47730ca05dfe29a895a0b5a52fd6bca37090fca` |

The existing legacy macOS wheel run [43036302389](https://github.com/SemperSupra/latent-reasoning/actions/runs/43036302389) passed 6/6 tests on both standard `macos-26` and `xcode-27`; the **new repo must independently pass its own run**. A legacy passed result is not sufficient by itself.

## What the bridge implements

- Export/import the three-tensor upstream MeG Phi-2 one-neuron JSON format (last `fc1` row + bias, last `fc2` column).
- Apply a reversible frozen-backbone Phi-2 MLP neuron **replacement**, not an additional neuron.
- Validate exact no-op control, numerical agreement with direct full-weight replacement, strict shapes, valid gradient, and one real-dimension Phi-2 MLP fixture without loading the full checkpoint.
- Provide a deterministic controller protocol for later generated/diffusion weights.

**Not yet implemented:** MeG's released text/query encoder, familiarity model, full teacher-neuron training, diffusion generator/sampler, end-to-end training or paper-faithful evaluation on MLX. The bridge is a **build-compatible portability component**, not a complete MeG port and not an edited-factual-accuracy result.

## Build and local BigMac handoff

Public CI builds `meg_mlx_bridge-0.1.0-py3-none-any.whl` under `adapters/backends/mlx/meg_phi2/`, installs it on standard ARM64 macOS and publishes wheel + hashed `build-receipt.json`. Match the downloaded wheel SHA256 to its receipt before local use; wheel bytes can differ between runner environments.

For a high-memory local Mac after the wheel is approved and downloaded:

```bash
python3.11 -m venv ~/Projects/meg-mlx-venv
source ~/Projects/meg-mlx-venv/bin/activate
python -m pip install 'mlx==0.32.4' 'mlx-lm==0.31.3' 'numpy==2.1.1'
python -m pip install --no-deps ./meg_mlx_bridge-0.1.0-py3-none-any.whl
python -c 'import meg_mlx_bridge; print("MLX bridge imported")'
```

This is a package import smoke, **not** proof of a local full-model experiment. Full scientific use must separately pin Phi-2 model/tokenizer revision, reference PyTorch semantics, full MeG pipeline, private evaluation data, and BigMac environment identity.

## Governance

New scientific migration workset [model-mechanisms-private #1](https://github.com/SemperSupra/model-mechanisms-private/issues/1) preserves original MeG engineering research [legacy #6](https://github.com/SemperSupra/latent-reasoning-private/issues/6). Public macOS runners must run only model-free/synthetic tests within their ~7-GiB advertised RAM class; no Kaggle credential or unreviewed workload.
