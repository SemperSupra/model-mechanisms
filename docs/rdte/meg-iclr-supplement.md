# MeG ICLR 2026 official supplemental archive — provenance and safe inspection

Official ICLR 2026 MeG proceedings include a **supplementary ZIP** linked by the conference publisher:

https://proceedings.iclr.cc/paper_files/paper/2026/file/7926a9c34166da5a6a681cc0fe6d8a28-Supplemental-Conference.zip

The archive is a distinct author-provided source from the GitHub repository and paper. It may contain original method details or additional data necessary for reimplementation. **Its actual contents must be verified before any claim that specific files are present.**

This workcell downloads only that exact published URL into an ephemeral GitHub Actions runner, bounds archive bytes, enumerates members with SHA-256 and sizes, rejects traversal and symlink entries, and uploads only sanitized metadata. It never extracts the archive, executes code, installs packages, runs a model, publishes archive bytes or declares original trained checkpoints recovered.

## Why this matters

Before rebuilding unavailable MeG artifacts, inspect the publisher's supplement for training recipes, missing paraphrase prompt, evaluation specs, RNG details, ablations and code/license notices. If supplied, use exact publisher file hashes to improve independent reconstruction. If not, record a negative result with immutable archive identity; do not invent contents.

## Scientific and license boundaries

- The authors' GitHub tree still has a missing top-level source license and trained components; publisher availability does not confer blanket redistribution permission.
- An archive member filename containing `checkpoint` does not establish an authentic trained checkpoint; examine format/hash/provenance under later explicit approval.
- The metadata report cannot confirm correctness of claims, peer-review ratings, or a replication. Reviewer remarks require actual OpenReview text; OpenReview anti-bot access currently limits direct automated inspection.
- Continue stage 0 deterministic source reimplementation separately in [public PR #12](https://github.com/SemperSupra/model-mechanisms/pull/12).
- Private scientific authority: [Model Mechanisms #5](https://github.com/SemperSupra/model-mechanisms-private/issues/5).
- Model Artifact Foundry ingestion authority: [private #35](https://github.com/SemperSupra/model-artifact-foundry-private/issues/35).

**Expected output:** `official-meg-supplement-metadata` containing `inventory.json`, not the ZIP contents. Machine state `METADATA_INSPECTED_ONLY`. No automatic promotion to Foundry or claim of paper replication.
