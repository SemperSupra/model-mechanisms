# MeG Stage 2 — familiarity routing source preflight (independent)

**Source:** official author revision `9fa8ae10cf33c82dd2200057f70dfcb73388cd74`, `train_familiar.py` Git blob `a4bfdd000ab04a4b79eca68b816ebd541efa555a`, Stage2 config blob `85902387314cae916cd5ec62ce3c0d5f660dffbb`. **Science DLE:** [Model Mechanisms private #5](https://github.com/SemperSupra/model-mechanisms-private/issues/5).

## A source-parsing blocker independent of checkpoints

The author's released `train_familiar.py` contains a syntactically invalid dictionary return in `get_config`: the line assigning `threshold` is missing a comma before `bert_checkpoint_path`. This blocks parsing **before any model is trained or loaded**. The audit first verifies the exact source Git blob, then confirms that the original **fails** `ast.parse`, and that an *in-memory diagnostic single-comma repair* parses. It does not write, execute, or redistribute a modified copy of the author's unlicensed source. Fixing the comma must be an explicitly recorded deviation for the independent reconstruction.

## Mathematical routing oracle and stage dependencies

The original model classifies a query across 10 randomly generated familiarity labels. It computes Shannon entropy on softmax probabilities and abstains from editing if entropy **strictly exceeds** the threshold. Phi-2/ZsRE Stage2 declares threshold `0.1` (nats), Stage1 checkpoint `./checkpoints_trained_bert/bert_phi2_zsre/model_epoch_100.pth`, and batch/epoch targets: 1024/1800 for 1024 edits; 1024/1400 for 2048; 1024/2100 for 4096; 2000/4000 for 10,000.

Our stdlib 10-way softmax/entropy oracle tests uniform random-like output (entropy ln(10)≈2.3026, abstains), confident output (near-zero entropy, routes to max-logit class), strict threshold and invalid logits. This is **not a trained familiarity classifier or proof of routing accuracy**.

The released Stage2 trainer *does* explicitly call `optimizer.zero_grad()`; this differs from the Stage1 source. It seeds `42` in its entrypoint and uses `torch.load` for the Stage1 BERT checkpoint. Do not unpickle unverified remote `.pth` in Foundry. The Stage1 source/experimental lineages and original label bytes must be pinned before the separate GPU workcell.

**Qualification:** only free public Ubuntu CPU standard GitHub Actions; exact original source and YAML downloaded as plain text and statically inspected, never imported or executed. No model/checkpoint/benchmark dataset bytes, provider admission, author code vendoring, scientific results, or license promotion.

**Admission status:** BLOCKED_SOURCE_SYNTAX_AND_MISSING_STAGE1_CHECKPOINT. Explicit source-correction deviation and Stage1 checkpoint are prerequisites.
