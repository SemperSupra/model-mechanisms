> **Source correction (2026-11-12):** The original stage-zero datasets, edited Phi-2 data, familiarity label files and a `rephrase.prompt` **are available in the official ICLR supplementary ZIP**, source/member hashes verified by [public Actions 43210713738](https://github.com/SemperSupra/model-mechanisms/actions/runs/43210713738) and inventoried in [Foundry PR #72](https://github.com/SemperSupra/model-artifact-foundry/pull/72). This independent seeded derivation is now a **recipe-equivalence / control** workcell, not the preferred source for original data. Use publisher-original input files for the authors' faithful experiment after rights/Foundry admission. Trained stage1–4 checkpoints are still unlocated. See [scientific issue #5](https://github.com/SemperSupra/model-mechanisms-private/issues/5).

# MeG stage-zero independent reconstruction — reproducible derivative boundary

**Science authority:** [Model Mechanisms private #5](https://github.com/SemperSupra/model-mechanisms-private/issues/5).  
**Foundry authority:** [Model Artifact Foundry private #35](https://github.com/SemperSupra/model-artifact-foundry-private/issues/35).  
**Original paper:** [ICLR 2026 / arXiv 2512.14395](https://arxiv.org/abs/2512.14395), official code revision `9fa8ae10cf33c82dd2200057f70dfcb73388cd74`.  
**Claim:** independently reconstructed elementary stage-zero derivatives, **not** recovered author data or reproduced paper metrics.

## Why this is scientific replication, not original checkpoint recovery

The released method supplies source transformations but not the complete original input data, random state, prompt, teacher-neuron data or trained checkpoints. Even an exact reimplementation may produce new bytes, for reasons outside our control. We can still conduct a defensible scientific reconstruction by preserving the method, declaring deviations up front, and assessing downstream results with paired tests.

### Deterministic transforms now implemented

`tools/meg_reconstruct_stage0.py` independently implements two simple disclosed methods:

- `counterfact-ids` — preserves original list order and all record fields, replaces/adds sequential `id` from zero, as described in released `data/add_id_for_cf.py`. No RNG. Byte equivalence requires the **same raw input** and serializer.
- `familiarity-labels` — preserves first 10,000 records in order and independently assigns random labels from 0–9. Released `add_fake_id_for_familiar.py` uses **global unseeded RNG**; this independent reconstruction uses an explicit seed for replayability, so resulting labels are **not asserted author-identical**. The original source's seed/PRNG state is not known.

Each CLI invocation refuses to overwrite a target file, records input/output SHA256, original method commit, derivation, seed and record counts. Output is JSON indent-4, avoiding unverified changes to data schema. Tests use only synthetic public records; CI will not download, print, or distribute any benchmark bytes.

## Example: stage 0 after dataset authorization and separate acquisition

```bash
python3 tools/meg_reconstruct_stage0.py \
  --mode counterfact-ids \
  --input raw/multi_counterfact.json \
  --output derived/multi_counterfact_new_id.json \
  --receipt receipts/multi_counterfact_new_id.receipt.json

python3 tools/meg_reconstruct_stage0.py \
  --mode familiarity-labels \
  --input derived/multi_counterfact_new_id.json \
  --output derived/cf_fake_id_class.json \
  --receipt receipts/cf_fake_id_class.receipt.json \
  --seed 17
```

`raw/`, `derived/` and `receipts/` are illustrative **disposable per-run volume locations**, not committed directories. The actual canonical raw source SHA, license and provenance must be established by Model Artifact Foundry before data can be used or redistributed. Preserve the exact JSON receipt with the artifact lineage.

## Remaining stages and negative controls

- Reconstruct the missing GLM paraphrase prompt transparently with an independently chosen documented prompt as a **new derivation**; do not claim identical original generated texts, and do not execute `trust_remote_code` in Foundry.
- Lock ZsRE source snapshot, generated paraphrase subject splits and sampling seed; test duplicate subjects and training vs held-out leakage.
- Independently implement/query-test the InfoNCE BERT text encoder, entropy familiarity router, per-fact teacher optimization and diffusion generator (stage 1–4), including loss and gradient parity against mathematical paper definitions and bounded CPU oracles before GPU.
- Build original fixed-protocol MeG Phi-2 CUDA training only after Kaggle protected resource/asset permissions and budget are separately admitted. Measure AG/TF reliability/generality/locality and compare with authors’ tables without mislabeling a new seeded retrain as author-byte recovery.
- Red-team whether the apparent locality advantage is driven primarily by *routing abstention*; test unfamiliar paraphrases, entity overlap, same-subject conflicts, out-of-distribution query settings, and a static/deterministic-generator alternative.

## Acceptance and provenance

- **RECIPE_RECONSTRUCTED**: exact behavior on synthetic control inputs with deterministic outputs and recorded source method.
- **DATASET_DERIVED**: authorized raw bytes acquired and SHA-pinned; derived output has provenance and license disposition.
- **PIPELINE_RETRAINED**: stages 1–4 actual native checkpoints with exact environment/seed/model revision.
- **PAPER_METRICS_MATCHED**: predefined tolerance satisfied on correct benchmark protocol, independent of byte-identical author checkpoints.
- **INDEPENDENT_REPLICATION**: novel implementation/seeds/splits confirms effect against appropriate controls.

A CPU test does **not** confer higher scientific status. License-less author code may be inspected but not vendored to this public repository. All independent output bytes should be treated as newly derived artifacts in Foundry, not author originals.
