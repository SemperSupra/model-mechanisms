# Public repository hygiene and boundary

**Purpose:** prevent accidental Git tracking of credentials, temporary Kaggle receipts, large downloaded model weights, generated build wheels or symlinked external files during Model Mechanisms migrations.

## Source-only policy

- `.gitignore` excludes routine disposable Python caches and environments, cloud provider receipts, common credential paths and large model checkpoint formats. These can still be force-added, so ignore patterns alone are not a control.
- `tools/validate_public_tree.py` reads only `git ls-files -z` and basic file metadata. It rejects common secret filenames and directories, model/binary artifact extensions, Git symlinks, missing tracked files and files over 2 MB. A public source repository should point to digest-pinned Model Artifact Foundry objects rather than commit large weights.
- `tests/test_public_tree_hygiene.py` covers intended allowed/blocked cases and the *actual current tracked tree* with no model source, credential, secret, dataset or subprocess execution.
- `.github/workflows/public-source-hygiene.yml` runs on free standard public Ubuntu with read-only checkout permissions, bounded tests and an allowlisted small JSON receipt.

## Limits

**This is not secret-value scanning**: a developer could paste a secret into a normally named source file. Keep native GitHub secret scanning, code review, branch rules, and protected environments in force; do not paste credentials into source or workflow inputs. The scanner also does not establish legal model/data licenses or catch every binary format. Public PR review should inspect actual changed source and license grants.

**Artifact distribution** is handled by Model Artifact Foundry, not ad-hoc Git LFS or GitHub binary attachments. Cloud execution receipts are exported through approved GitHub Actions artifacts with retention and native version/digests, not committed as files.

**No infrastructure mutation:** this PR only adds source hygiene tests and ignore patterns. It does not alter any legacy project, new repo secret, branch setting, Kaggle account, model or scientific result.

## DLE

Durable: tracked source policy, signed/hashed run provenance at CI level. Legible: precise violations and limitations. Executable: one stdlib CLI and ordinary public CI tests. This guard must be revisited alongside new data/backends so intentional source fixtures are admitted via review without silently weakening the policy.
