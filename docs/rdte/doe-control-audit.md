# Cross-cell DOE comparison integrity (proposed)

**Dependency:** [public B1 DOE/replay PR #1](https://github.com/SemperSupra/model-mechanisms/pull/1).  
**Scientific authority:** [new private B5 workset #4](https://github.com/SemperSupra/model-mechanisms-private/issues/4).

## Finding
The first method-neutral DOE schema validates individual cells, but cannot establish that a claimed comparator actually exists or that it uses the same task, split, seed, resource and evaluation environment. A schema-valid treatment could therefore be compared to an unrelated baseline or an absent control. Those are **causal inference defects** even when every JSON document validates.

## Correction
`core/doe/audit_controls.py` is an offline, read-only cross-cell auditor:

- Validate each cell against the existing v1 schema before inter-cell comparisons.
- Require unique `(campaign_id, design_id, cell_id, rep_id)` identities and bound input to 4,096 cells.
- Require every non-null comparator to exist in the same campaign/design/repetition; forbid self- or chained comparisons and require comparator treatment kind `none`.
- Verify matched suite, split, dataset reference, holdout ID, hypothesis, phase, seed, resource class and environment reference.
- For confirmation-phase cells require a declared primary outcome and nonblank holdout-manifest reference.
- Reject partially recorded provider-native job IDs/versions; neither alone is a credible execution identity.
- Report only count and source-only validation status: **no scientific effects are measured**.

**Scope limit:** This does not prove dataset contents match their identifiers, prevent memorization or hidden holdout leakage, determine statistical significance, or establish hardware equivalence. Further independent controls and Foundry/Spelunker evidence remain required before any experiment is admitted.

## Execute without models, network, cloud credentials
```bash
python3 -m unittest discover -s tests -p 'test_doe_control_audit.py' -v
python3 core/doe/audit_controls.py examples/doe-cell.synthetic.json
```

The first fixture is an unmeasured synthetic baseline; the pair tests cover valid untreated/treatment comparisons and reject cross-run drift.

Keep the design contract independent of any single mechanism; MeG diffusion, static adapters, retrieval and Dory loop treatments are all valid method families. A green CI run means **comparison-plan structure validated**, not a reproduced paper or measured capability.
