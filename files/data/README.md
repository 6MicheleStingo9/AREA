# Data

## MIT AI Risk Repository (v4)

`mit_ai_risk_repository_v4.xlsx` is version 4 of the
[MIT AI Risk Repository](https://airisk.mit.edu/) (sheet "Contents": updated 03 December 2025),
included unmodified. It is licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Cite as: Slattery, P., Saeri, A. K., Grundy, E. A. C., Graham, J., Noetel, M., Uuk, R., Dao, J.,
Pour, S., Casper, S., & Thompson, N. (2025). *The AI Risk Repository: A comprehensive meta-review,
database, and taxonomy of risks from artificial intelligence.* arXiv preprint arXiv:2408.12622.
https://arxiv.org/abs/2408.12622

## Processed datasets

`processed/` is derived from the spreadsheet by
[`data_prep/extract_dataset.py`](../../data_prep/extract_dataset.py): classifiable rows only, labels
normalized to the project schema, and a deterministic train/eval split by risk category (a
category and its sub-categories always share a split). `processed/manifest.json` records the
source and script checksums, the split rule and the label distributions. The derived files are
distributed under the same CC BY 4.0 license.

| File | Task | Rows |
|---|---|---|
| `full.jsonl` | all classifiable rows (RAG knowledge base) | 1617 |
| `causal_clf.{train,eval}.jsonl` | Entity / Intent / Timing | 1313 / 160 |
| `domain_clf.{train,eval}.jsonl` | Domain / Sub-domain | 1270 / 159 |
