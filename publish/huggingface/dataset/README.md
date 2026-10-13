---
license: cc-by-4.0
language:
- en
- it
task_categories:
- text-classification
task_ids:
- multi-class-classification
pretty_name: Kindynos causal risks
size_categories:
- 1K<n<10K
tags:
- ai-risk
- ai-safety
- mit-ai-risk-repository
- synthetic
dataset_info:
- config_name: kindynos
  features:
  - name: id
    dtype: string
  - name: language
    dtype: string
  - name: run
    dtype: string
  - name: profile
    dtype: string
  - name: system
    dtype: string
  - name: text_model
    dtype: string
  - name: severity
    dtype: string
  - name: subdomain_id
    dtype: string
  - name: subdomain_name
    dtype: string
  - name: title
    dtype: string
  - name: text
    dtype: string
  - name: entity
    dtype: string
  - name: intent
    dtype: string
  - name: timing
    dtype: string
  - name: label_source
    struct:
    - name: entity
      dtype: string
    - name: intent
      dtype: string
    - name: timing
      dtype: string
  - name: source
    dtype: string
  - name: changed_in_review
    list: string
  - name: harmonized
    list:
    - name: axis
      dtype: string
    - name: reviewed
      dtype: string
    - name: reason
      dtype: string
- config_name: mit
  features:
  - name: id
    dtype: string
  - name: paper_id
    dtype: string
  - name: subdomain_id
    dtype: string
  - name: subdomain_name
    dtype: string
  - name: title
    dtype: string
  - name: text
    dtype: string
  - name: entity
    dtype: string
  - name: intent
    dtype: string
  - name: timing
    dtype: string
configs:
- config_name: kindynos
  default: true
  data_files:
  - split: train
    path: kindynos/train.jsonl
  - split: validation
    path: kindynos/validation.jsonl
  - split: test
    path: kindynos/test.jsonl
- config_name: mit
  data_files:
  - split: train
    path: mit/train.jsonl
  - split: validation
    path: mit/validation.jsonl
  - split: test
    path: mit/test.jsonl
---

# Kindynos causal risks

AI risk descriptions labeled with the three axes of the [MIT Causal Taxonomy of AI Risks](https://airisk.mit.edu/):
who or what causes the risk (entity), whether the harm is intended (intent) and when it occurs (timing).
Two sources, with the same core fields:

- **`kindynos`**: 605 risks in English and Italian written by [Kindynos](https://github.com/6MicheleStingo9/kindynos),
  an open-source AI risk assessment tool, from simulated questionnaires about AI systems. The texts were
  generated with Gemini 2.5 Flash. The train and validation labels are LLM-annotated (two independent
  annotators and an adjudicator, following written guidelines); the test labels were verified by a human
  annotator.
- **`mit`**: the 1,473 risks of the MIT AI Risk Repository v4 that carry causal labels: excerpts of research
  papers, labeled by the repository's annotators (CC BY 4.0).

These are the data of [laya-kindynos-causal](https://huggingface.co/MicheleStingo/laya-kindynos-causal), split exactly as
they were used for training, model selection and testing.

| Config | Split | Risks | Languages | Labels |
|---|---|---|---|---|
| `kindynos` | train | 363 | 174 EN, 189 IT | LLM-annotated: two independent annotators and an adjudicator |
| `kindynos` | validation | 97 | 45 EN, 52 IT | LLM-annotated: two independent annotators and an adjudicator |
| `kindynos` | test | 145 | 85 EN, 60 IT | verified by a human annotator |
| `mit` | train | 1,116 | EN | MIT AI Risk Repository annotators |
| `mit` | validation | 197 | EN | MIT AI Risk Repository annotators |
| `mit` | test | 160 | EN | MIT AI Risk Repository annotators |

```python
from datasets import load_dataset

area = load_dataset("MicheleStingo/kindynos-causal-risks", "kindynos")
mit = load_dataset("MicheleStingo/kindynos-causal-risks", "mit")
```

## Fields

Both configs:

- `id`: for Kindynos `<run>-<subdomain>-<n>`; for MIT the repository's Ev_ID, which the source repeats for
  a few different risks (62.31.01–03 each mark two).
- `subdomain_id`, `subdomain_name`: the risk's subdomain in the MIT Domain Taxonomy, named as in the MIT
  AI Risk Repository.
- `title`, `text`: the risk's title and description.
- `entity` (`ai`, `human`, `other`), `intent` (`intentional`, `unintentional`, `other`), `timing`
  (`pre-deployment`, `post-deployment`, `other`).

`kindynos` only; every split has every column, empty where it does not apply:

- `language` (`en`, `it`), `run`, `severity` (the severity Kindynos gave the risk: `low`, `medium`, `high`).
- `profile`: the simulated user, `beginner`, `intermediate` or `expert`; empty for the Kindynos example
  assessment.
- `system`: the AI system the simulated user was asked to describe (train and validation).
- `text_model`: the LLM that wrote the text, `gemini-2.5-flash`; empty for the Kindynos example assessment,
  whose model was not recorded.
- `label_source` (train and validation): for each axis, `agreed` when both annotators gave the label,
  `adjudicated` when the adjudicator chose it.
- `source` (test): `generated` for the six simulated assessments, `example` for the Kindynos example assessment.
- `changed_in_review` and `harmonized` (test): the axes the human annotator corrected, and those
  harmonized across near-identical risks, with the reason.

`mit` only: `paper_id`.

## How the Kindynos risks were made

1. **Questionnaire.** Kindynos asks 24 questions about an AI system. Gemini 2.5 Flash answered them in the role
   of a beginner, intermediate or expert user. Each of the 28 train and validation runs describes a given
   fictional system, for example *a CV screening and candidate ranking system used by a recruitment
   agency* or *un sistema di gestione adattiva dei semafori per il traffico di una città*, in English and
   Italian alternately. In the six test runs (two languages, three profiles) the simulated user chose the
   system to describe; the 28 train and validation systems were chosen to differ from those. The seventh
   test run is the Kindynos example assessment.
2. **Risks.** The Kindynos domain analyzer (Gemini) turned each set of answers into risks, grouped by MIT
   subdomain, each with a title, a description, a severity and a mitigation. The dataset keeps all but the
   mitigation.
3. **Splits.** Whole runs go to one split: 22 runs to train, 6 to validation (three per language, drawn at
   random with a fixed seed), 7 to test. Six entries in which the analyzer states that a subdomain carries
   no significant risk were removed, because they are not risks.

## Labeling

The labels follow the MIT definitions and the decision rules in [LABELING.md](LABELING.md), written for the Kindynos
texts: label what the text states, and use `other` when it does not settle an axis; entity is whose
decision or action produces the harm, as the text frames it; intent is about the harm, not the action;
timing is when the harm occurs, so the harms of a system in use are post-deployment even when introduced
earlier.

- **Train and validation** (460 risks): two LLM annotators labeled each risk independently, following the
  written guidelines; an adjudicator resolved their disagreements (49 labels on 42 risks), with a reason for
  each. Agreement between the annotators: Cohen's κ 0.93 / 0.89 / 0.97 (entity / intent / timing). The
  prompts and the raw annotations are in [`annotations/`](annotations/).
- **Quality check**: on a sample of 60 risks with human-verified labels, the protocol's labels matched
  95 / 85 / 100% of them ([`quality_check/`](quality_check/)).
- **Test** (145 risks): pre-annotated by a model with the same guidelines, then verified one by one by a
  human annotator, who corrected 25 of the 435 labels; then 17 labels of near-identical risks were
  harmonized, to the MIT annotators' convention for the subdomain where it is clear.

| Split | Entity: `ai` / `human` / `other` | Intent: `intentional` / `unintentional` / `other` | Timing: `pre` / `post` / `other` |
|---|---|---|---|
| `kindynos` train | 48 / 39 / 13% | 20 / 67 / 13% | 0 / 93 / 7% |
| `kindynos` validation | 45 / 46 / 8% | 24 / 61 / 15% | 0 / 93 / 7% |
| `kindynos` test | 54 / 35 / 10% | 23 / 58 / 19% | 1 / 91 / 8% |
| `mit` train | 44 / 36 / 20% | 32 / 37 / 31% | 12 / 61 / 27% |

## The `mit` config

The rows of the [MIT AI Risk Repository](https://airisk.mit.edu/) v4 (December 2025) with causal labels,
extracted by [`data_prep/extract_dataset.py`](https://github.com/6MicheleStingo9/kindynos/blob/main/data_prep/extract_dataset.py) of Kindynos:
classifiable rows only, labels normalized to the values above, title and description kept, subdomain
added from the repository's domain coding. The split keeps each risk category with its subcategories:
the test split holds 160 rows from groups not used for training; the validation split holds whole groups
making up 15% of the remaining rows, which laya-kindynos-causal left out of its training data.

## Uses

- Training and evaluating classifiers for the MIT Causal Taxonomy, especially on short risk statements in
  English and Italian.
- Studying labeling protocols with LLM annotators against human-verified labels.

## Provenance and license

CC BY 4.0. The `mit` config and the taxonomy definitions come from the MIT AI Risk Repository
(Slattery et al., 2025, CC BY 4.0). The Kindynos texts were generated with Gemini 2.5 Flash by the Kindynos pipeline.
The train and validation labels are LLM-annotated (two independent annotators and an adjudicator), with the
protocol checked against human-verified labels on a sample; the test labels were verified by a human
annotator.

## Citation

```bibtex
@misc{stingo2026kindynoscausalrisks,
  title  = {Kindynos causal risks: AI risk descriptions labeled with the MIT Causal Taxonomy},
  author = {Stingo, Michele},
  year   = {2026},
  url    = {https://huggingface.co/datasets/MicheleStingo/kindynos-causal-risks}
}

@article{slattery2025airisk,
  title   = {The AI Risk Repository: A Comprehensive Meta-Review, Database, and Taxonomy of Risks From Artificial Intelligence},
  author  = {Slattery, Peter and Saeri, Alexander K. and Grundy, Emily A. C. and Graham, Jess and Noetel, Michael and Uuk, Risto and Dao, James and Pour, Soroush and Casper, Stephen and Thompson, Neil},
  journal = {arXiv preprint arXiv:2408.12622},
  year    = {2025}
}
```
