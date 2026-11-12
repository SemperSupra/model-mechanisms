# MeG Stage1 — preregistered 2×2 protocol-fidelity controls (no training)

**Science authority:** [Model Mechanisms #5](https://github.com/SemperSupra/model-mechanisms-private/issues/5). **Source identity:** exact original `train_bert.py` Git blob `df2f3eaa23dda322657f2821ffef899f11273bc7`; original `phi2_zsre.yaml` blob `86cb6baa036fd5da0ba50f465f0f42d55add7366`; publisher dataset SHA256 `438dc2f1c98aec85f828eaf95fed2f40c19d470a1cdb6723f9103aa8e304ec18`.

Two independently observed source conditions require separate scientific variables before MeG Stage1 can be faithfully evaluated:

1. **Paraphrase interpretation.** Under last-2,000 author training records, 1,332 `rephrase` fields are strings, 668 are lists. The released source loops over the first two iterable items, yielding **2,664 single-character fragment pairs** within a literal 4,000-pair training set; a type-corrected policy wrapping whole string as one paraphrase produces **2,668** valid question pairs. Neither result is a trained-model metric.
2. **Gradient-reset policy.** The released `train_model` calls `optimizer.step` but has no explicit `optimizer.zero_grad`. Corrected reset is a controlled ablation, not part of the published source as inspected.

## Four experimental cells

| | As-published gradient accumulation | Reset gradients each batch |
| --- | --- | --- |
| As-published character iteration | `literal-accum` — literal source baseline | `literal-reset` |
| Corrected full-question paraphrases | `typed-accum` | `typed-reset` |

The [immutable plan](../../campaigns/meg-stage1-fidelity-factorial.json) enumerates four unadmitted, unmeasured cells with identical input/model identity requirements and the source-derived pair counts.

**Admission is blocked:** original BERT model revision must be pinned in Foundry, rights-reviewed original publisher data hydrated, heldout subject groups locked, and a small synthetic/training correctness budget approved. The public plan permits at most 16 records, one CPU-only epoch and **no provider API calls**; those are caps for future qualification, not work already performed. Do not execute the original 30,000-epoch budget without separate owner-approved GPU quota and original vs correction review.

A later science workcell must measure per-cell paired heldout accuracy, generality/locality and wall-clock/model resource cost, plus actual optimizer-gradient behavior, under at least independently repeated seeds. Include an isolated original reference run and transparent correction deviations; do not call an improved corrected run author-equivalent. No real BERT training, knowledge editing, Kaggle submission or paper metric is claimed by this plan.

The workflow only validates the plan and its negative controls using free standard public Ubuntu GHA. It does not duplicate Agent Dispatch or create a scheduled workload.
