# COMP-001 synthetic composition-operator smoke

Private scientific/operations authority: [Model Mechanisms #6](https://github.com/SemperSupra/model-mechanisms-private/issues/6). Application consumer: Stable Character private R033 #168.

This is a deterministic, **model-free linear correction** fixture. It tests a generic secondary operator that adjusts a two-coordinate latent state while preserving a separately observed feature. It does **not** train or evaluate a neural model, represent an actual 3D human, establish anatomy, accept user preference, or deploy any runtime service. No protected input or rights issue is present.

## Exact local verification
```sh
cd experiments/composition-go
GOPROXY=off GOTOOLCHAIN=local go test -race -count=1 ./...
GOPROXY=off GOTOOLCHAIN=local go vet ./...
GOPROXY=off GOTOOLCHAIN=local go build -trimpath -o ./fixture ./cmd/fixture
./fixture
```

`T0-untreated` is the unmodified base. `T1-direct` corrects one coordinate and leaks into an independently measured feature. `T2-constrained` solves the coupled 2x2 inverse to preserve it. `Tneg-equal-norm-shuffle` moves the same-sized intervention to a wrong coordinate. Negative tests reject invalid budget, singular mapping, non-finite inputs and unsupported operator kinds.

The contract's `claim` is always `SYNTHETIC_LINEAR_ORACLE_ONLY_NOT_A_LEARNED_MODEL`; it cannot be promoted to character quality. Correctness in these tiny fully observed linear fixtures is **not** evidence that learned corrections outperform an honest deterministic optimizer. See the preregistered DOE for native geometry and held-out tests.

This folder is intentionally independent of the in-flight B1 Python method-neutral DOE schema in draft PR #1. Once both independent branches pass technical review, compose receipts via a versioned adapter to the existing DOE schema instead of creating a second registry/scheduler. No public CI dispatch or release implied by this draft.
