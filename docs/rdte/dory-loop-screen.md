# B5 — Dory loop-placement DOE: preregistration scaffolding only

**Private scientific authority:** [model-mechanisms-private #4](https://github.com/SemperSupra/model-mechanisms-private/issues/4).  
**Upstream scientific hypothesis:** [legacy latent-reasoning-private #7](https://github.com/SemperSupra/latent-reasoning-private/issues/7).  
**Required base contract:** [public B1 PR #1](https://github.com/SemperSupra/model-mechanisms/pull/1).  
**State:** DESIGN_ONLY. No Phi-2, Dory, MeG controller, private subject data or GPU has been used.

The public `core/doe/loop_masks.py` produces a deterministic 16-cell screen for four recurrent passes, with every binary activation mask (0000 through 1111). Leftmost bit is earliest pass, rightmost latest. Zero mask is the untreated baseline. No functional role is asserted for any pass.

## Nominal intervention matching

Each nonzero mask divides an exact total nominal strength of 1 equally across its active passes. Examples: `0001` = 1; `1010` = 1/2 each; `1111` = 1/4 each. Exact rational strings avoid floating-point budget drift when planning. This is **not equivalent** to matching actual output activation norm, parameter/controller computations, latency, or device energy, because recurrent dynamics are nonlinear. Those are additional measured outcomes/controls when the scientific experiment becomes admissible.

One fixed, content-identical controller/knowledge payload must be used across all masks within a matched cohort; masks must be paired on the same question IDs and training seed. Include shuffled conditioning, random equal-norm intervention, and compute-matched untreated controls in follow-on **separately enumerated** study strata. Do not conflate source-document retrieval with knowledge stored in generated weights.

## Admission gates

The current planner intentionally sets every asset revision and holdout digest to `null`, every cell `admitted=false` and `measured=false`, and the plan state to `BLOCKED_UNPINNED_ASSETS_AND_PROTOCOL`. It cannot launch an experiment. Before a future executable DOE can be constructed, the private protocol must fix:

- Original Dory architecture/configuration and tokenizer revision, loop implementation and inference cache semantics.
- Frozen controller/generator provenance and selected factual payload.
- Immutable novel-entity datasets, training/evaluation split identity and locked holdout subject groups.
- Equal-trials dataset IDs across masks, exact training seeds and predeclared primary hypothesis/acceptance threshold.
- Controls for compute, cumulative intervention norm, controller memory, inference latency and unrelated-knowledge locality.
- A separate review of any attempt to expose an adapter or private dataset in public manifests.

The original MeG Phi-2/CUDA reproduction and MLX build qualification remain separate campaigns. An available MLX wheel or a green public CI run **does not** authorize Dory model testing.

## Reproduction and review

Public-source, credential-free smoke only:

```bash
python3 core/doe/loop_masks.py --seed 17
python3 -m unittest discover -s tests -p test_loop_mask_screen.py -v
```

The implementation is a pure Python standard-library file without network operations, data/model downloads, file mutation by default, GPU initialization or cloud APIs. Unit tests verify complete unique masks, baseline consistency, exact strength sums, invalid-manifest rejection and deterministic command output.

**Next science gate:** after independently accepted B1 replay/DOE contract, implement a typed bridge from admitted private campaign state to public-safe executable cell manifests; keep the preregistered protocol and heldout lock authority private. Do not publish a fictitious scientific result by converting PLAN_ONLY to ADMITTED without evidence.
