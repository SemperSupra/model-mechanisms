# Model Mechanisms

Reproducible research and development of mechanisms that change or extend neural-model capabilities.

This repository is the **public implementation and execution surface** of the [Model Mechanisms research program](https://github.com/SemperSupra/model-mechanisms-private). It contains method-neutral experiment contracts, reproducible implementations, public-safe test fixtures and CI. The private sibling owns the scientific hypotheses, experimental design, private holdouts, evidence interpretation and promotion decisions. The public repository must be operable without access to private material.

## Research areas
- Continuous, latent and recurrent reasoning (Coconut, CODI, recurrent-state models).
- Generated weights and neuron/adapter interventions (MeG, deterministic generators, diffusion, factual knowledge augmentation).
- Model-specific adaptation and controlled recurrent-loop treatments (Phi-2, Dory).
- Faithful reproduction of published experiments, then preregistered DOE with appropriate causal controls and independent qualification.
- Portable model-interface builds for CPU, PyTorch/CUDA, MLX and separately qualified accelerator backends.

## Portfolio boundaries
- **Model Mechanisms:** mechanism implementation and scientific experiment execution.
- **Model Artifact Foundry:** canonical identity, licensing, distribution and verified hydration of checkpoints/adapters.
- **Model Spelunker:** independent model/actor capability qualification.
- **Agent Dispatch:** operational actor routing and scheduling, not a dependency for bounded provider-native research CI.

## Current migration status
**Bootstrap only. No experimental results have been migrated or reproduced in this repository yet.** The original research repositories remain live:
- [Latent Reasoning public](https://github.com/SemperSupra/latent-reasoning)
- [Latent Reasoning private](https://github.com/SemperSupra/latent-reasoning-private)

Active upstream migration sources include original MeG source audit PR #47, MLX bridge build PR #48, and gated Kaggle execution PR #45. These are *not* activated automatically here.

Start with [AGENTS.md](AGENTS.md) and [migration architecture](docs/architecture/migration.md) when those are admitted.

## Working contract
**DLE = Durable, Legible, Executable.** Preserve source, model, dataset, environment and provider-native receipt identity; keep all control and negative results; use reviewable bounded workcells; prioritize meaningful experiments and avoid duplicate infrastructure. Support human, automation and agent audiences.

Do not commit private holdout content, credentials, unlicensed model/source data, or large checkpoint weights. Standard public GHA may build MLX modules with synthetic fixtures but must not be mistaken for model-scale MeG experiments. No paid runners or unreviewed autonomous Kaggle job submissions.
