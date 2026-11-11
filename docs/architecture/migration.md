# Model Mechanisms — selective migration architecture

**New destination:** [public implementation](https://github.com/SemperSupra/model-mechanisms) / [private scientific authority](https://github.com/SemperSupra/model-mechanisms-private), established 2026-11-11. **Authoritative migration workset:** [private #1](https://github.com/SemperSupra/model-mechanisms-private/issues/1).

## Why selective migration

The legacy `SemperSupra/latent-reasoning` already has valuable method-neutral replay, comparison and benchmark methods but also many one-off experimental workflows and research-specific schema classes. The new repository must not blindly mirror a history of provisional experiments or imply that their old outcomes were reproduced in the new environment.

Legacy:
- Public `SemperSupra/latent-reasoning` repo ID `1381367722`; pinned main source revision `c0f7fea8a27825941040e4b4b878841983cc7bc9`.
- Private `SemperSupra/latent-reasoning-private` repo ID `1381369435`; pinned main revision `72da77af054de511439b58eb435bb01052426bef`.
- Active upstream public drafts PR #45 Kaggle direct (fixed synthetic workloads), #47 official MeG source audit, #48 installable synthetic MLX Phi-2 bridge, #49 rename-in-place docs. Existing private #2, #5, #6, #7, #8 remain linked authoritative historical context until explicit transfer.
- Earlier `latent-resoning` and `latent-resoning-private` are bootstrap-only typo repositories, not migration sources.
- `mark-e-deyoung/latent-space-mining-private` is separate evidence-mining methodology, not a model-method implementation.

## Repository layout and boundaries

```text
model-mechanisms/                     PUBLIC
  README.md, AGENTS.md
  core/                               reusable bounded replay, DOE and analysis
  schemas/                            method-neutral v1 contracts
  examples/                           synthetic public-safe fixture specs
  experiments/                        executable Python CLIs, stable flat legacy compatibility
  methods/                            latent reasoning, editing/diffusion, looped computation
  adapters/                           model-specific (Phi-2/Dory) and backend (torch/MLX) ports
  benchmarks/                         licensed sources, procedural generators, sealed split IDs
  campaigns/                          versioned experimental designs, safe public config
  tools/                              CLI entrypoints, validator/receipts
  tests/                              no-secret offline contract and bounded platform oracles
  environments/                       exact pinned runtime identities
  docs/                               architecture, method notes, imports/evidence
  .github/workflows/                  CPU checks, macOS wheel prebuild; gated GPU launch
model-mechanisms-private/             PRIVATE
  README.md, AGENTS.md
  campaigns/                          preregistered hypotheses and control decisions
  doe/                                designs, analysis plans, holdout manifests
  evidence/                           references to native receipts and negative outcomes
  decisions/                          promotion/hold/kill/review
  handoffs/                           small bounded agent/task batons
```

Directories appear only as admitted real content. Scientific authority is in GitHub Issues/PRs, not duplicated in a second task database.

**Scientific campaigns:**
1. Latent vs compute-matched recurrence (original Campaign 0001).
2. Faithful upstream MeG Phi-2 PyTorch/CUDA reference (fixed original protocol, not new-factor DOE).
3. MLX model-intervention/framework port (build + numerical parity; science later on high-memory BigMac).
4. Novel knowledge-capacity augmentation (MeG diffusion vs static/deterministic/RAG baselines).
5. Dory 4-loop pass-specific interventions and loop-depth studies.

No one scientific result is inferred from the success of any other track.

## Experiment framework contract

One **DOE cell identity** and one **bounded replay** handle method heterogeneity; evidence must contain model/tokenizer/dataset/control references, an explicit hypothesis, factors, seed/rep identifiers, evaluation outcome class and provider-native status. A separate `intervention` treatment field handles generated neuron weights and pass masks; never represent factual editing by falsely assigning `reasoning_substrate.class=latent`.

Existing legacy `schemas/replay-spec.schema.json`, `tools/run_replay.py` and `tests/test_replay_runner.py` are initial source-eligible primitives. Introduce them with source SHA/source map; keep their CLI and original flat `experiments.<module>` semantics while validating future method-neutral data models independently. No new scheduler or artifact registry.

## First migration batches

| Batch | Content | Test/acceptance | Status |
| --- | --- | --- | --- |
| B0 | New public/private README, AGENTS and private #1 DLE | Connected GitHub identity, no secret/public-private leak | In progress |
| B1 | Existing replay semantics + method-neutral typed DOE cell + synthetic CLI fixture and contract tests | Public standard GHA runs, native receipts, backward-compatible legacy fixture | Draft workcell |
| B2 | Upstream MeG source audit PR #47; original data/config provenance | Exact author commit and blocked research assets report | Not yet ported |
| B3 | MLX wheel build PR #48, real Phi-2 MLP synthetic interface, wheel SHA receipt | Both standard public macOS runners pass; no large Phi-2 model | Not yet ported |
| B4 | Kaggle direct launcher PR #45 fixed allowlist + provider-native observe logic | Independent review, new repo environment secret setup, no quota overrun | Not yet ported; no credentialed deployment |
| B5 | Legacy latent reasoning experiment slices and selected benchmark generators | Paired controls and source/result provenance, no broad workflow import | Not yet ported |
| B6 | Independent DOE campaign manifests and comparison analysis | Registered hypotheses/controls/holdouts, no premature science | Not yet admitted |

## Cutover gates and anti-duplication

The **old repo pair remains live** through the acceptance of new CI, artifact egress, experiment replay, and private evidence crosswalk. Do not automatically transfer old issues/PRs, mirror workflows, archive old repos, create duplicate Kaggle jobs, or switch provider webhooks.

New repositories have different IDs and do **not inherit** secrets, protected environments, runner/branch restrictions, GitHub App installation access, OIDC identities, public artifacts or issue/PR history. Before any GPU run: independently verify these identities and configure **new** `kaggle-research` environment and secret by secure action, without exposing token values. Public PR CI must remain credential-free.

Archive old source only after exact source→destination crosswalk, immutable receipts and independently tested native workflows. Keep historical repo URLs and read-only references; no reuse of the old slug.

**DLE:** Durable = exact refs and content hashes; Legible = bounded claim/provenance/negative outcomes; Executable = pinned tests/manifests/artifacts. Three audiences: human, automation and agents.
