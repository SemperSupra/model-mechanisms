# MeG Phi-2 source-audit import provenance

New-native target: [Model Mechanisms](https://github.com/SemperSupra/model-mechanisms).  
Legacy upstream PR: [latent-reasoning #47](https://github.com/SemperSupra/latent-reasoning/pull/47), inspected head `0091a62606c0bbca5da4c2d555dd480a7a9e772e`.

| Path | Original legacy Git blob |
| --- | --- |
| `tools/meg_phi2_source_preflight.py` | `becf57ac8c7c428109527d85af09ce08c3d76ab0` |
| `tests/test_meg_phi2_source_preflight.py` | `661975ced5b568618c084932abc9056901b6947b` |
| `.github/workflows/meg-phi2-source-preflight.yml` | `12172f4ddb1b8d410406510ebde3be795b68f765` |
| `docs/rdte/meg-phi2-source-preflight.md` | `e77f3de900475694a5dc0577af47270079fbc6fe` |

Changes are limited to canonical authority links and pinning the same GitHub artifact-upload action used by the other public CI workflows. The original author source is **not vendored or executed**; the workflow shallow-fetches fixed upstream `RodeWayne/MeG-for-Knowledge-Editing` commit `9fa8ae10cf33c82dd2200057f70dfcb73388cd74` and inspects text/sha hashes only.

The success condition is `source_integrity=PASS` with research assets explicitly reported missing. It is **not** an environment build or MeG paper reproduction.

Historical native source-only reference: [legacy CI run 43033282018](https://github.com/SemperSupra/latent-reasoning/actions/runs/43033282018). A new-repo CI pass is required to admit this migrated component.

Scientific workset: [new migration #1](https://github.com/SemperSupra/model-mechanisms-private/issues/1), with [original research #5](https://github.com/SemperSupra/latent-reasoning-private/issues/5) preserved.
