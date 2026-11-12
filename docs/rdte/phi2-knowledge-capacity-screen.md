# B5 — Phi-2 knowledge-capacity DOE: staged protocol and controls

**Scientific workset:** [Model Mechanisms private #4](https://github.com/SemperSupra/model-mechanisms-private/issues/4).  
**Legacy scientific authority:** [latent-reasoning-private #7](https://github.com/SemperSupra/latent-reasoning-private/issues/7).  
**Depends on:** [shared framework PR #1](https://github.com/SemperSupra/model-mechanisms/pull/1), and successful faithful original MeG reproduction before a scientific effectiveness claim.

## Primary question

Can a separately trained, diffusion-generated-neuron controller make *verifiably novel facts* available to Phi-2 more efficiently than static adaptation, a deterministic generator, and retrieval, measured at **whole-system** storage, compute and latency costs?

This question is **not** answered by reproducing original MeG editing on ZsRE/CounterFact, and does not presume that diffusion generates unavailable facts from nowhere. The novel facts must have a verified source in training/document conditioning/teacher/controller, absent from the frozen Phi-2 checkpoint and hidden from the inference prompt.

## Stage-gated design

Initial source-only plan: **15 conceptual cells** = 100 verified synthetic facts × three question tasks (direct, paraphrase, multi-hop) × five method arms:

| Method | Allowed factual access | Role |
| --- | --- | --- |
| Unchanged Phi-2 | Closed-book | Matched baseline |
| Static LoRA | Closed-book | Ordinary learnable adaptation |
| Deterministic hypernetwork | Closed-book | Tests benefit of learned weight generation *without diffusion* |
| MeG diffusion generator | Closed-book | Candidate scientific treatment |
| RAG | Retrieval allowed | External-memory comparator, **not** a closed-book capacity result |

For each task family, every method is paired to the **same** unchanged-model baseline under the same fact load and seed, with the exact held-out task IDs frozen before experiments. Controller training subject groups and held-out evaluation subject groups must be disjoint.

The optional `--include-conditional-scale` adds the 500/1000 fact tiers to yield 45 planned cells. These higher tiers are **conditional**, not automatically funded, admitted or executed. Later independent training seeds/replications and shuffled-conditioning/random equal-norm controls are a separate evidence-gated confirmatory stage, not a giant up-front cross-product.

## Required scientific safeguards

- Commit model and tokenizer revision, trained text encoder/familiarity/MeG generator, deterministic controller and teacher revisions; keep original author reference separate.
- Generate genuinely novel synthetic knowledge after model checkpoint freeze; establish source docs/teacher provenance and explicit training/evaluation isolation.
- Preregister primary `unseen_synthetic_fact_question_accuracy` and secondary generality, multi-hop, locality, unrelated knowledge regression.
- Measure whole-system cost: frozen Phi-2 weights, generator/controller, adapters, data or retrieval indexes; inference latency, training and inference device-seconds, peak RAM/VRAM.
- Separate RAG results from *closed-book* accuracy and disclose retrieval opportunities in inference prompts.
- Use held-out subjects and independent seeds, paired analysis, negative controls, and later independent Model Spelunker qualification.

## Admission status

All current plans are `PLAN_ONLY` with `BLOCKED_DATA_MODEL_CONTROLLER_AND_EVAL_LOCKS`; every model, dataset, controller, teacher, evaluation and environment identity field is `null`. Every cell is `admitted=false` and `measured=false`. The model checkpoint, data and workload are **not** downloaded or executed by the planning tool.

```bash
python3 core/doe/knowledge_capacity.py --seed 17
python3 core/doe/knowledge_capacity.py --seed 17 --include-conditional-scale
python3 -m unittest discover -s tests -p test_knowledge_capacity_screen.py -v
```

All commands are standard library, bounded model-free source inspections and negative contract tests. This module requires no Kaggle, Metal, CUDA, secrets or network access. A green CI result is only a reproducible **DOE plan** and does not prove MeG's factual capacity.
