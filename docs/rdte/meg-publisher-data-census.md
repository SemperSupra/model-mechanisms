# MeG publisher dataset: 18-member source integrity and stage-one split census

Authority: [scientific replication #5](https://github.com/SemperSupra/model-mechanisms-private/issues/5), [Foundry intake #35](https://github.com/SemperSupra/model-artifact-foundry-private/issues/35). Stacked on [official ICLR archive inspection PR #13](https://github.com/SemperSupra/model-mechanisms/pull/13).

The official ICLR 2026 supplementary code/data bundle is publisher-associated source, not a free license to redistribute. The prior 18-member audit verified exact file hashes but not the JSON record structures. This workcell performs a **source-only schema census**: retrieves the original ZIP to a disposable public Ubuntu Actions runner; checks all 18 pinned member SHA-256 and byte sizes, parses JSON **only as data**, and records record counts and field *names* without printing record contents, questions or answers.

The author-released Stage 1 `train_bert.py` selects **last 2,000** dataset records for contrastive training, and **first 1,024** for within-run validation. Its stated `phi2_zsre.yaml` specifies a 4,000-example batch and 30,000 epochs; compare these counts against the actual publisher `new_split_data/zsre_for_bert_train.json` to establish any **positional** overlap. No claim about entity-level/semantic leakage follows solely from a positional check; that requires a separately reviewed subject-identity policy.

Key acceptance:
- all 18 official member filenames, sizes and SHA256 match the publisher archive;
- every JSON parses as the expected top-level list of objects, with counts/key names only recorded;
- training-validation overlap is computed mathematically from exact publisher records, not guessed;
- CI uploads only a bounded JSON receipt, never source archives or data contents;
- no author code is imported, executed, republished or unpickled; no secret/Kaggle/MLX or model execution.

This is an independent data integrity workcell, NOT Stage 1 BERT training, paper evaluation or Foundry acquisition/approval. The source request is bounded and license review remains a separate Foundry gate. If any checksum or structure differs, abort and reconcile the source before scientific launch.
