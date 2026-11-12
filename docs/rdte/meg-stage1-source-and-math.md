# MeG Stage 1 — exact source identity and independent InfoNCE math preflight

**Scientific authority:** [reconstruction workset #5](https://github.com/SemperSupra/model-mechanisms-private/issues/5). **Original source:** [Wan et al. MeG @ 9fa8ae10](https://github.com/RodeWayne/MeG-for-Knowledge-Editing/tree/9fa8ae10cf33c82dd2200057f70dfcb73388cd74). This is a *source and math oracle*, not a trained encoder.

## Frozen Phi-2/ZsRE reference config

The author's `hparams/stage_1/phi2_zsre.yaml` (Git blob `86cb6baa036fd5da0ba50f465f0f42d55add7366`) declares:

| Parameter | Original value |
| --- | --- |
| Backbone | `bert-base-uncased` fine-tuned text encoder, last transformer block `encoder.layer.11` trainable |
| Dataset | `data/new_split_data/zsre_for_bert_train.json` |
| Dataset selection | **last 2,000** records for training; at most first two `rephrase` variants per record |
| Within-run validation | **first 1,024** records of the same source file |
| Temperature | 1.0 |
| Batch | 4,000 (may equal one full epoch batch if 2 paraphrases per each of the 2,000 records) |
| Epochs | 30,000 in YAML (downstream Stage 2 references `model_epoch_100.pth`) |
| Optimizer | AdamW, LR 0.0001 |
| Checkpoint policy | every fifth epoch |

**Important source fidelity issue:** In `train_bert.py` (Git blob `df2f3eaa23dda322657f2821ffef899f11273bc7`), the `train_model` training loop calls `loss.backward()` and `optimizer.step()` but has **no explicit `optimizer.zero_grad()` in that function**. Gradients therefore accumulate across steps unless reset elsewhere (the released loop does not appear to reset them). The initial faithful reference should report this behavior explicitly. Run a separate, clearly named **corrected optimizer** ablation with zeroing; do not silently replace the author's protocol.

The original `info_nce_loss` L2-normalizes query/positive/key embeddings, uses the paired query–positive cosine as the first logit, the other entries in the current batch as negatives, masks the diagonal, divides by temperature, and applies cross-entropy with the positive at index zero. The independent stdlib oracle in `tools/meg_stage1_source_preflight.py` validates this with orthogonal synthetic vectors. A batch of **one** has no negative contrast and the theoretical loss is zero, so it must not be treated as meaningful training.

## Gates from publisher data

The original author-provided `zsre_for_bert_train.json` is now located in the ICLR 2026 supplement, exact SHA256 `438dc2f1c98aec85f828eaf95fed2f40c19d470a1cdb6723f9103aa8e304ec18`. [Publisher schema census PR #15](https://github.com/SemperSupra/model-mechanisms/pull/15) checks its count and the positional intersection between first-1,024 validation and last-2,000 training records.

Even if positional ranges do not overlap, repeat subjects/paraphrases may leak; a separate privacy-preserving subject-identity/semantic review is required. If they do overlap, distinguish the authors' in-training diagnostic from an independent held-out evaluation (which must use an immutable disjoint holdout).

## Execution allocation

- **Public CPU GHA:** verify pinned author source Git blobs by SHA-1 and parse static AST; run mathematical oracle. No author code imported, no BERT weights downloaded, no dataset bytes republished.
- **Kaggle GPU (future):** prepare disposable pinned PyTorch 2.4.1/Transformers 4.44.2 environment and original BERT/model/data SHA bindings; source-compatible trainable layer, optimizer, exact source data; resource estimator, one fixed job ID and no pending concurrent owner jobs. No actual Kaggle job authorized until separate protected environment/secret and quota gates.
- **Model Artifact Foundry:** independently hydrate authorized original stage-zero datasets and pinned BERT backbone; training result's checkpoint is a *new* reconstructed artifact with model/data/env/seed and source revision lineage.

**Claims:** `SOURCE_AND_MATH_PREFLIGHT_ONLY` until a native training receipt exists. The run may explain a mismatch; it cannot establish original paper fidelity or benefit from diffusion.
