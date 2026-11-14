# COMP-001 — independent operator admission contract

This source-safe Go stdlib workcell implements a **pre-execution compatibility decision**, not a model executor or replacement DOE system. The authority is [Model Mechanisms private COMP-001 #6](https://github.com/SemperSupra/model-mechanisms-private/issues/6). It is a **separate** source branch from in-flight composition [PR #21](https://github.com/SemperSupra/model-mechanisms/pull/21) and B1 method-neutral DOE [PR #1](https://github.com/SemperSupra/model-mechanisms/pull/1); it shares no changed files.

## Exact offline checks

```sh
cd core/operator-admission-go
GOPROXY=off GOTOOLCHAIN=local go test -race -count=1 ./...
GOPROXY=off GOTOOLCHAIN=local go vet ./...
GOPROXY=off GOTOOLCHAIN=local go run ./cmd/admit \
  -manifest examples/public_synthetic_operator.json \
  -candidate examples/public_synthetic_candidate.json
```

`COMPATIBLE_CONTRACT_ONLY_NOT_EXECUTION_AUTHORIZATION` means only that exact backend/weights/representation/rig/units/timebase and declared source class match, the required invariants are present, and bounded resource inputs are syntactically admissible. It **does not** independently verify source rights, model checkpoint contents, runner capacity, private assets, CPE authority, a working 3D model, a passed visual/physics oracle, production service health, or a canonical character. External source/admission/rights checks remain mandatory.

This contract intentionally supports parameter, geometry, motion, activation and weight-adapter kinds, requiring kind-specific source references and dimensional compatibility. An arbitrary neural LoRA cannot be applied to a different base checkpoint or architecture.

The binary does not contact any network endpoint, run an external model, access credentials, or modify files. CI is permitted only for source-safe synthetic examples. Data/policy checks here are **defense in depth**, not an authorization system. Rejecting unknown/duplicate JSON fields prevents ambiguous operator requests; exact artifacts must still be verified by Model Artifact Foundry and independent Model Spelunker probes.

Next integration: project this independent compatibility receipt into the existing B1 DOE schema, then consume it from Stable Character only after R032 P0 #167 numerical/semantic corrections. No duplicate scheduling, registry, or independently invented scientific claims.
