# B4 — Direct Kaggle provider-adapter source migration preflight

**Authority:** [Model Mechanisms migration #1](https://github.com/SemperSupra/model-mechanisms-private/issues/1), [B4 #3](https://github.com/SemperSupra/model-mechanisms-private/issues/3). This is the planned new-native *candidate*, distinct from [legacy standalone experimental Kaggle PR #45](https://github.com/SemperSupra/latent-reasoning/pull/45) and its [hardening child #50](https://github.com/SemperSupra/latent-reasoning/pull/50).

## Exact origin and immutable mapping (2026-11-11)

Source repo `SemperSupra/latent-reasoning`, exact approved-to-inspect **candidate** commit `7b71810eef4a4e1d5bed6d83bbb9e6d6a3f2ce62`. This is not a merged or authorized credentialed provider deployment.

| Exact original | Original Git blob | B4 destination / treatment |
| --- | --- | --- |
| `tools/kaggle_latent_direct.py` | `9f8c5768a05d0cd69ab50e29434d432c0c17fac1` | `adapters/providers/kaggle/direct.py`, selectively retarget root/workload paths, distinct `mech-b4-` namespace, control schema, duplicate-active scan |
| `experiments/kaggle_latent/gpu_device.py` | `d9ca584b13f518092cffd8a955473214bff9f7b8` | `adapters/providers/kaggle/workloads/gpu_device.py`, exact byte copy |
| `experiments/kaggle_latent/tpu_bridge.py` | `d3439b304b2c2af84c4b15b7d3accb64a56abbac` | `adapters/providers/kaggle/workloads/tpu_bridge.py`, exact byte copy |
| `tests/test_kaggle_latent_direct.py` | `5e503ffe0b084f93feaadf5199f3304a51243f2f` | `tests/test_kaggle_direct_port.py`, retarget import and isolated namespace and replace privileged workflow assertion with no-secret preflight; preserve native source-binding, TPU-finite negative controls |

Current new-native projected code blob IDs: controller `e45d36e212d7a2f1cef748c943bd77433c0d93dc`, imported GPU `d9ca584b13f518092cffd8a955473214bff9f7b8`, imported TPU `d3439b304b2c2af84c4b15b7d3accb64a56abbac`; tests `675b97671e393b3b8c097ea6d71969904f982e18`.

## Boundaries

**Implemented:** narrowly scoped fixed-workload provider-controller candidate with the original two hardware/synthetic bridge cases, preserved source SHA and native version/active job/quotas/observed scientific receipt checks, and 16 tests including hostile controls. Separate `b4-kaggle-direct-source-preflight` public CI uses a **new disposable standard Ubuntu runner**, Python standard library, no Internet dependency downloads, no secrets, only `plan` and offline tests.

**Not implemented/admitted:** The new repository has **no privileged `workflow_dispatch` submit/observe workflow**, no newly configured `kaggle-research` secret/environment and no verified user provider quota or run. Never rely on inherited tokens or imply that old repo's environment grants access here. Do not merge or start source acquisition on behalf of consumers without review. Imported private/offline synthetic device scripts are still only source candidates; they do not include external weights/data hydration, pose models, real media or video QA sources.

The new-native code intentionally retains the old `latent-kaggle-result/v1` scientific receipt schema and `latent_kaggle_result.json` filename while the source remains *byte-identical* for traceability. The new `mm-kaggle-control/v1` outer schema and `mech-b4-` slug distinguish future candidate runs. A separate reviewed contract version would be required to rename scientific receipts.

## Source-only execution

```bash
python3 -m compileall -q adapters/providers/kaggle
python3 -m unittest discover -s tests -p 'test_kaggle_direct_port.py' -v
python3 adapters/providers/kaggle/direct.py --action plan --workload gpu-cuda-v1 --out-dir /tmp/mm-b4-gpu
python3 adapters/providers/kaggle/direct.py --action plan --workload tpu-bridge-v1 --out-dir /tmp/mm-b4-tpu
```

**Never run `--action submit` or `--action observe` from this draft as a credentialed provider operation.** Keep privileged authorizations and user specific quotas behind an explicitly approved future executor. This is a provider-adapter **migration**, not a concurrent second scheduler or enabled ungoverned actuator.

## Exit gate

Obtain exact-head source-only CI PASS and reject hostile cases. Independently review scope and original source attribution, then request owner approval for any new-native privileged environment, fixed project consumer workloads, model rights/weights and actual one-shot provider submission. Preserve legacy authority and do not archive the old project during migration.
