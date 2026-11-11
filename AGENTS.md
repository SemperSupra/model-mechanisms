# AGENTS.md — Model Mechanisms public implementation

**Mission:** develop, reconstruct, falsify and port mechanisms that change model capabilities; do not conflate latent reasoning, knowledge editing, diffusion generation or recurrent loops.

## Authority and onboarding
- Read [README.md](README.md), [migration plan](docs/architecture/migration.md) and the private scientific [workset #1](https://github.com/SemperSupra/model-mechanisms-private/issues/1) if authorized.
- The public repo must be independently buildable and reviewable without any private GitHub checkout.
- **DLE = Durable, Legible, Executable.** Record exact source/model/data/env revisions, test outcomes, receipt hashes and known limitations; do not invent success.

## Workcell discipline
- Work in small branches/PRs with independent tests; batch unrelated analysis and preparation, do not launch scientific workloads until their admission gates pass.
- Provide one clean method-neutral DOE/replay/evidence contract. Add model-specific methods and backend adapters behind explicit interfaces; avoid duplicate runners and registries.
- Keep source compatibility with imported legacy `experiments.<module>` replay format until validated migration.
- Preserve both positive and negative results, original paper configuration, and scientific vs engineering status boundaries.

## Security and cost
- No secret or private holdout content in public source, Actions environment, artifact or logs.
- No automatic Kaggle credentialed workflow until reviewed fixed allowlist, quota/active-job gates and owner acceptance; PRs never receive Kaggle secrets.
- Public standard GHA Ubuntu is for low-cost source/tests; public standard macOS is for **prebuilt MLX packaging and tiny synthetic compatibility tests**, not full Phi-2/MeG science.
- Do not run paid/private runner minutes, model-scale downloads, broad subprocess shell commands, untrusted-source execution, or unstated long-duration workloads.
- Model Artifact Foundry owns checkpoint provenance/hydration; Model Spelunker owns independent qualification. Agent Dispatch is not needed for bounded direct free-tier experiments.

## Required result
For any workcell report: input ref/hashes, command, bounded environment, actual pass/fail evidence, exact artifact SHA and limits. Distinguish `SOURCE_AUDIT_PASS`, `BUILD_COMPATIBLE`, `REFERENCE_REPRODUCED`, and `DOE_QUALIFIED` (none implies the next).

## Audiences
Humans need explanation and comparisons; automation needs schemas and native provider status; agents need discoverable small stable tasks and stop conditions.
