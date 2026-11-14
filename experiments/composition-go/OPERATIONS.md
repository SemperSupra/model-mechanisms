# COMP-001 — Build/deploy/O&M contract

## What is operational today
The source-safe `fixture` command is a disposable deterministic CLI: `go test -race ./...`, `go vet ./...`, `go build -trimpath -o ./fixture ./cmd/fixture`, then `./fixture`. This does not expose a network endpoint, need secrets, or deploy a service. No OCI/GHCR release exists from this workcell.

## Proposed common runtime
- Author one versioned **Go** control-plane/worker entrypoint with future subcommands `plan`, `run`, `evaluate`, `replay`, `health`, `serve`. Keep source and config Git-authoritative; no competing scheduler (Agent Dispatch owns placements/admission).
- Immutable `OperatorManifest`, `CandidatePack`, `DeltaProposal`, `EvaluationReceipt`, `JobStatus` schemas. Idempotency key binds Git SHA, model/weights, typed input, method version, seed and evaluator revision. No in-place mutation of base character.
- Native numeric modules run as isolated whitelisted adapters: MHR/Anny/PyTorch, Blender Python, SOFA, sovereign visual VLM; independent failure and source/rights gates. Never execute arbitrary user-supplied shell commands.
- After exact-head source/rights and security gates, publish pinned slim multiarch OCI image to GHCR. **Same source/tag** for TrueNAS, OCI VPS and GHA, with separate arch-specific immutable image digests; don't pretend linux/amd64 and linux/arm64 bytes identical. BigMac uses a macOS/arm64 build from the identical Git revision for native Blender/MLX.
- TrueNAS: isolated resource-bounded disposable GPU/CPU workcells and short-lived coordinator. OCI VPS: CPU/light orchestration, not assumed GPU. Free public GHA: sanitized source-safe CPU DOE only, no protected assets. Tailnet-only read-only R032 browser sees approved generated receipts/artifacts; no public ingress or Tailscale Funnel.
- Artifacts are immutable content-addressed external custody, never worker-local `/tmp` as sole record; Git DLE indexes exact hash and acceptance. Secrets from approved runtime secret injection only, never Git.

## Health, observability, recovery
- Liveness and readiness **separate**: process responsiveness != calibrated model success. Readiness requires admitted backend/weights, valid source, storage quota and capacity.
- Prometheus/OpenTelemetry optional after operational need; minimum JSON logs/receipt for source SHA, job ID, stage, backend, duration, peak memory/VRAM, GPU seconds, input/output hashes, unit/calibration failures, resource admission and error class. Avoid private media or sensitive concept text in logs.
- Bounded concurrency, deadline, cancellation and cleanup, no reliance on worker-local memory for authority. Restart must re-read source/config and reconcile idempotent job receipts. Running job abandoned on worker death is requeued only when artifact evidence proves safe retry.
- Rollback = stop admitted route/worker, select previous signed/verified image/config/operator, cold-replay last known-good fixture, preserve immutable previous CharacterPacks and evidence; no silent data migration.
- Scheduled operations only after a real admitted service/deployment and executor exist; O&M status currently `NOT_DEPLOYED`. No background work is promised.
- Security: fixed allowlisted adapter process commands, resource and egress confinement, source/weight license admission, no ACL widening, no public protected media, no unapproved paid runners.

## Required deployment acceptance
Independent exact source-head review and Go negative tests; OCI build+SBOM+checksum/scanner; safe supply-chain pins; isolated workcell preflight; admission of actual node/port/TLS/tailnet identity; production/canon gates separately. Verify restart, lost-worker, duplicate job, invalid/missing weights, bad input and full rollback on the exact admitted venue. Record observed working URL only after cross-device test, never infer it from configuration.
