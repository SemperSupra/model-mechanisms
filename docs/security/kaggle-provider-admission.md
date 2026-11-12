# Kaggle provider admission — defense in depth (proposed)

**Private authority:** [B4 workset #3](https://github.com/SemperSupra/model-mechanisms-private/issues/3).  
**Stacked parent PR:** [public B4 PR #4](https://github.com/SemperSupra/model-mechanisms/pull/4).

The new repository's B4 PR exposes only a public, no-secret, no-provider `plan` workflow. Its Python adapter contains `submit` and `observe` methods for later reviewed admission, but **neither privileged operation is currently deployed as a GitHub workflow**.

## Red-team finding

A caller running the Python adapter manually with `KAGGLE_API_TOKEN` could previously attempt `submit` or `observe`, even though the repository's PR workflow did not supply a token. The actual credential is the decisive authority, but unreviewed CLI execution could still be an operational mistake.

## Implemented correction

Before importing the Kaggle SDK or calling any provider endpoint, the CLI now refuses credentialed operations unless all of the following exact process-context values match:

| Variable | Required value |
| --- | --- |
| `GITHUB_ACTIONS` | `true` |
| `GITHUB_REPOSITORY` | `SemperSupra/model-mechanisms` |
| `GITHUB_REF` | `refs/heads/main` |
| `GITHUB_EVENT_NAME` | `workflow_dispatch` |
| `GITHUB_WORKFLOW_REF` | `SemperSupra/model-mechanisms/.github/workflows/kaggle-provider.yml@refs/heads/main` |
| `MM_KAGGLE_EXECUTION_ADMITTED` | `true` |

The named `kaggle-provider.yml` workflow **does not exist yet**, so no workflow in the new repository currently satisfies this gate. Offline source validation and `--action plan` remain unaffected.

### Limits

Environment variables can be spoofed by a malicious local process and **are not an authentication mechanism**. They are accidental-use protection. Actual secret access must remain in a future, reviewed, main-only, environment-protected GitHub Actions job configured by the owner. The public untrusted pull-request workflow must never have access to that protected environment or its token.

The future credentialed workflow must be a separate approved PR after:
- verifying provider SDK semantics and account quota/identity;
- independently reviewing workload allowlists, source SHA attestation, existing active job scan and exact native version;
- configuring `kaggle-research` for the **new** repository with main-only deployment rules and explicit owner approval;
- ensuring no concurrency with legacy provider jobs or arbitrary user scripts;
- keeping all receipts sanitized and the model/data hydration path separately licensed and reviewed.

## Public regression tests

`tests/test_kaggle_direct_port.py` covers every required context field, rejects an injected dummy Kaggle token from pull-request execution, and verifies the resulting receipt records `PROVIDER_ACTION_NOT_ADMITTED` without importing the provider. No actual token or external API is required.

**Claim:** defense-in-depth source/contract security qualification only; not Kaggle provider access, GPU admission, model science, or permission to merge.
