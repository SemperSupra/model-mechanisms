# Apple MLX Gaussian representation R0 — free public macOS GHA

**Authority:** `SemperSupra/model-mechanisms-private#1`/B1/B5 and consumer `SemperSupra/stable-character-pipeline-private#168`; same method-neutral DOE, no new scheduler or model-checkpoint rights. This is an experiment, not production library/admitted representation.

**Prior runner census:** Agent Dispatch private #281/#285/#286/#289 verifies standard public `macos-26` ARM64 Apple Paravirtual Metal compute, PyTorch MPS, MLX GPU differentiable small-model inference; ~7.5 GiB RAM with ~3 GiB free at boot. Workloads must be tiny; never infer physical Mac GPU performance from virtual guest. No neural engine assumption.

**Upstream implementation:** `RobotFlow-Labs/gsplat-mlx` exact commit `9e53709a94e9c56fb66db2708d7d728832176713`; `mlx==0.32.4`; source package metadata `Apache-2.0`, but verify the actual repository license (root LICENSE absent at inspection) before redistributing code; test only on original synthetic scene. Its rendered/gradient path is a **pure MLX tile/pixel loop**, while tile intersections use NumPy and CPU readback. Not all of its claimed 405 tests demonstrate full differentiable 3DGS; upstream `tests/test_training.py` explicitly uses a 2D proxy. Do not infer production performance.

## Exact experiment
1. Install pinned MLX on public standard `macos-26` ARM runner (no paid resources, private assets, checkpoints, secrets).
2. Read-only checkout pinned public upstream commit.
3. Confirm Metal MLX GPU; covariance matrix via unit quaternion scales `Sigma=R diag(s^2) R^T`, positive-definite inverse and analytic `d trace(Sigma)/ds = 2s` against autodiff.
4. Actual `gsplat_mlx.rasterization(..., differentiable=True)`: one synthetic 3D Gaussian at z=2m, 32x32 RGB+alpha scene; render x=0 and x=+0.2m. Expected perspective shift `fx*delta/z=24*.2/2=2.4 pixels`. Alpha weighted centroid must track within 0.75px; no image noise/empty render.
5. Differentiable image x-centroid gradient wrt Gaussian x-position must be finite and agree with a symmetric finite-difference oracle at 0.002m (20% relative or 0.5 absolute tolerance). The optimizer can now move Gaussian means based on visual residuals if this is true; **does not** prove shape or semantic meaning.
6. Publish versioned machine-readable receipt and original synthetic PNG pair with SHA-256. Bad version, CPU fallback, finite-but-wrong gradient, wrong image movement, NaN/infinite, no GPU => **RED**. Any source/download/package/Metal failure => evidence with cause and bounded corrective workcell, **not** an unearned pass.

### Scope and follow-on
- Separate **Gaussian/SH/render latent** (`means[N,3]`, `quats[N,4]`, `positive_scales[N,3]`, `opacities[N]`, `SH[N,(degree+1)^2,3]`), **SMPL-X identity/pose/55-joint LBS**, **learned HumanGS transformer/vertex-decoder features**, material/groom, and motion policies. None are interchangeable controls.
- Future numerical DOE: transpose/quaternion/world-camera convention, alpha blending, depth ordering, negative z, near-clipping, zero scales, f32/f16 gradient error, exact 3DGS cross-framework finite gradient, angular/view-dependence, ops GPU coverage, tile explosion; on held-out synthetic cameras. Full scene training and real-human evidence only in separately admitted resource/rights scope.
- Small upstream MLX, fully fused native Metal `rayanht/msplat`, source C++ MLX `a1091150/gsplat-mlx`, PyTorch-MPS `zacsmms/mpsplat` are independent bakeoff competitors, not automatic replacement or combined licenses. `msplat` uses CPU C++/Metal and **not MLX**, but its kernel math and dataflow are useful.
- No automatic HumanGS, meshes, clothing, video substitution, or CPE integration acceptance from this small source-only experiment. No private GHA spend. Review by independent actor, no owner manual gate.

## Run
`python research/apple-mlx-gsplat/probe.py` on a suitable ARM Mac with MLX and pinned source package. Workflow: `.github/workflows/mlx-gsplat-research.yml`. Use the exact branch/revision and CI receipts, never quote upstream self-reported tests as own acceptance.
