# B4 — Exact Kaggle native-status interpretation (offline contract)

**Parent:** [Model Mechanisms Kaggle provider hardening PR #6](https://github.com/SemperSupra/model-mechanisms/pull/6).  
**Private DLE:** [Kaggle provider authority #3](https://github.com/SemperSupra/model-mechanisms-private/issues/3).

## Risk and correction

The original B4 adapter used substring checks to classify Kaggle kernel statuses. A value such as `INCOMPLETE` contains `COMPLETE` and could appear terminal-successful; a value such as `SUCCESS_BUT_RUNNING` could appear successful although its full meaning is not defined. The later artifact hash/oracle gate may still block an incorrect outcome, but status normalization should itself **fail closed**.

The revised parser accepts only precisely enumerated active, success, and failed status strings, optionally with the known `KernelStatus.` enum-class and `KERNEL_STATUS_` prefix. Unknown, compound, or contradictory tokens are `UNKNOWN`. Both active-job admission checks and exact-version result observation use this same parser.

## Boundaries

This is an *offline trust-boundary test*, not proof that the current Kaggle SDK uses every enumerated token. The actual SDK status representation and provider version must still be inspected at the later native provider admission gate. Unknown native states block submission or observation instead of guessing; add an explicitly reviewed new status value only after provider-native evidence. The original source-only PR runs have no Kaggle secret, provider network access or GPU/TPU usage.

The test suite adds malicious/ambiguous status examples and fake provider responses proving that unknown statuses block observation before result download, and that a failure status does not attempt to retrieve a successful result.

No provider job has been submitted, no scheduler launched, and no protected workflow/environment enabled by this draft.
