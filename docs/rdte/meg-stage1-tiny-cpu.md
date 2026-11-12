# Stage1 numerical progression: executable tiny random BERT on free CPU Actions

**Purpose:** qualify the independent MeG Stage1 contrastive training implementation mechanics before author-revision BERT and publisher datasets have completed Foundry rights/validator admission. Stacked on [4-cell Stage1 fidelity DOE PR #17](https://github.com/SemperSupra/model-mechanisms/pull/17).

This workcell **actually executes** `torch==2.4.1` and `transformers==4.44.2` on a disposable public Ubuntu CPU Actions runner, with pinned package versions, explicit seed and threads=1. It creates a **randomly initialized, synthetic** BERT with two transformer blocks, 32 hidden dimensions, four attention heads, and a 96-token invented vocabulary. It freezes all weights except the last transformer block and implements the original diagonal-masked, L2-normalized InfoNCE objective with temperature 1.0. There are three gradient updates across synthetic question/paraphrase token pairs.

Two policy traces start from equal initialization and inputs:

- **Source-literal gradient accumulation**: omit `optimizer.zero_grad()` as the released Stage1 `train_bert.py` does.
- **Corrected gradient reset**: zero gradients before each backward/optimizer step.

Both traces use AdamW LR 1e-4 and publish only synthetic scalar losses and gradient norms (never random weights). The tests require equality of first-step gradients and non-identity of second-step aggregate gradients, checking an actual `BertModel` forward/backward rather than an invented toy scalar objective.

**Explicit limits:** the original publisher dataset is **not read**, no pretrained BERT weights/tokenizer are downloaded, no original 12-layer/768-hidden BERT training, no model editing, diffusion, familiarity router, inference accuracy, benchmark results, or paper reproduction. Tiny synthetic numerical smoke is an engineering qualification, not a scientific performance claim. No CPU estimate here should be extrapolated to full author 30,000-epoch training cost.

**Repository and host hygiene:** all pip installs and caches are confined to the disposable public GHA runner, `--no-cache-dir` used, no private minutes or expensive accelerator, checkout persists no credentials, job has read-only contents, and no model checkpoint is published. A small JSON artifact receipt only.

Research [private #5](https://github.com/SemperSupra/model-mechanisms-private/issues/5); source data [Foundry private #35](https://github.com/SemperSupra/model-artifact-foundry-private/issues/35). No scientific launch or merge admission implied.
