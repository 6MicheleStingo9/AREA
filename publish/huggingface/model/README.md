---
license: apache-2.0
language:
- en
- it
library_name: laya
pipeline_tag: text-classification
base_model: convaiinnovations/laya-multilingual
base_model_relation: finetune
datasets:
- MicheleStingo/kindynos-causal-risks
metrics:
- accuracy
- f1
tags:
- ai-risk
- ai-safety
- risk-assessment
- mit-ai-risk-repository
- calibration
model-index:
- name: laya-kindynos-causal
  results:
  - task:
      type: text-classification
      name: MIT Causal Taxonomy, entity
    dataset:
      name: Kindynos causal risks
      type: MicheleStingo/kindynos-causal-risks
      config: kindynos
      split: test
    metrics:
    - type: accuracy
      value: 88.3
    - type: f1
      name: macro-F1
      value: 80.1
  - task:
      type: text-classification
      name: MIT Causal Taxonomy, intent
    dataset:
      name: Kindynos causal risks
      type: MicheleStingo/kindynos-causal-risks
      config: kindynos
      split: test
    metrics:
    - type: accuracy
      value: 77.2
    - type: f1
      name: macro-F1
      value: 67.1
  - task:
      type: text-classification
      name: MIT Causal Taxonomy, timing
    dataset:
      name: Kindynos causal risks
      type: MicheleStingo/kindynos-causal-risks
      config: kindynos
      split: test
    metrics:
    - type: accuracy
      value: 95.2
    - type: f1
      name: macro-F1
      value: 59.7
---

# laya-kindynos-causal

Who or what causes an AI risk, whether the harm is intended, and when it occurs: this model labels a
written AI risk along the three axes of the [MIT Causal Taxonomy of AI Risks](https://airisk.mit.edu/),
with a calibrated probability for each value. It is
[Laya-multilingual](https://huggingface.co/convaiinnovations/laya-multilingual) (322M parameters)
fine-tuned on the risks that [Kindynos](https://github.com/6MicheleStingo9/kindynos), an open-source AI risk
assessment tool, writes from a questionnaire about an AI system. It reads English and Italian and runs
on a CPU, in about 2 seconds per risk on a laptop.

Results on the Kindynos test set, 145 risks in English and Italian whose labels were verified by a human
annotator (95% bootstrap intervals):

| Axis | Accuracy % | Macro-F1 % |
|---|---|---|
| Entity | 88.3 [82.8–93.8] | 80.1 [70.1–88.3] |
| Intent | 77.2 [70.3–84.1] | 67.1 [60.0–74.1] |
| Timing | 95.2 [91.7–98.6] | 59.7 [51.8–65.3] |

All three axes are right on 71.7% of the risks.

## Quick start

```python
# pip install laya==0.4.1 huggingface_hub   (with PyTorch; a CPU is enough)
import json

import laya
from huggingface_hub import hf_hub_download

REPO, REVISION = "MicheleStingo/laya-kindynos-causal", "v1.0"
agent = laya.load(REPO, revision=REVISION)
with open(hf_hub_download(REPO, "questions.json", revision=REVISION)) as f:
    questions = json.load(f)  # the three axes, as typed questions with the MIT definitions

# What the model was trained on: MIT subdomain (code and name), title, description
state = "\n".join([
    "Risk subdomain: 4.3 Fraud, scams, and targeted manipulation",
    "Exploitation for fraud, scams, or targeted manipulation",
    "The system could be misused for generating convincing phishing messages, executing targeted scams, "
    "or engaging in manipulative conversational tactics directed at individual users or groups, "
    "potentially based on collected user data.",
])
answers = agent.predict(state, questions)["answers"]
for axis, answer in answers.items():
    print(axis, answer["choice"], round(max(answer["probabilities"].values()), 2))
# entity human 0.93
# intent intentional 0.93
# timing post-deployment 0.93
```

## Input and output

- **Input**: one risk in three lines. First `Risk subdomain:` with the code and name of the risk's
  subdomain in the [MIT Domain Taxonomy](https://airisk.mit.edu/), spelled as in the MIT AI Risk
  Repository (for example `6.5 Governance failure`); then the risk title; then its description. Kindynos
  writes its risks per subdomain, and the model was trained and evaluated with that first line: keep it.
- **Questions**: `questions.json` holds the three axes as Laya `choice` questions whose options carry the
  MIT definitions. Pass it unchanged.
- **Output**: for each axis, the chosen value and the probability of every value, calibrated on
  held-out Kindynos risks (temperature 1.025). Training used label smoothing 0.1, so a confident answer
  sits near 0.93, not 1.0.
- **Review threshold**: the confidence lets a pipeline send uncertain labels to a person. Kindynos marks the
  labels below 0.90 for review: on the validation risks, where the threshold was chosen, the labels
  below it were 59% correct and the others 94%.

## Labels

The MIT Causal Taxonomy of AI Risks (Slattery et al., 2025, CC BY 4.0):

| Axis | Value | Definition |
|---|---|---|
| Entity | `ai` | The risk is caused by a decision or action made by an AI system |
| | `human` | The risk is caused by a decision or action made by humans |
| | `other` | The risk is caused by some other reason or is ambiguous |
| Intent | `intentional` | The risk occurs due to an expected outcome from pursuing a goal |
| | `unintentional` | The risk occurs due to an unexpected outcome from pursuing a goal |
| | `other` | The risk is presented as occurring without clearly specifying the intentionality |
| Timing | `pre-deployment` | The risk occurs before the AI is deployed |
| | `post-deployment` | The risk occurs after the AI model has been trained and deployed |
| | `other` | The risk is presented without a clearly specified time of occurrence |

The labels of the Kindynos risks apply decision rules written for these texts
([LABELING.md](https://huggingface.co/datasets/MicheleStingo/kindynos-causal-risks/blob/main/LABELING.md)):
label what the text states, and use `other` when it does not settle an axis; entity is whose decision or
action produces the harm, as the text frames it; intent is about the harm, not the action; timing is when
the harm occurs, so the harms of a system in use are post-deployment even when introduced earlier. Two
choices differ from the MIT annotators' habits: intent of subdomains 7.1 and 7.2 follows the text, which
in Kindynos calls those outcomes unintended, and entity of 6.6 (environmental harm) is `other`.

## Intended use

The model is built for short AI risk statements organized by MIT subdomain, like those Kindynos writes:

- the causality step of Kindynos, where it is the default;
- other tools that describe AI risks in the same form; for texts of a different kind, check it first on
  a sample of your own labeled risks;
- research on small, calibrated classifiers that take the place of an LLM call in a pipeline.

## Training

- **Base model**: `convaiinnovations/laya-multilingual` at revision `1720e3e`, an mmBERT-base encoder with
  Laya's decision head (Apache-2.0).
- **Training data**, 1,842 rows ([dataset](https://huggingface.co/datasets/MicheleStingo/kindynos-causal-risks)):
  - 1,116 risks of the MIT AI Risk Repository v4 with their expert labels: English excerpts of papers,
    the training split without its validation groups;
  - 363 Kindynos risks from 22 simulated assessments, each seen twice. Their texts were generated with Gemini
    2.5 Flash through the Kindynos pipeline, for 22 fictional AI systems, in English and Italian. Their labels
    are LLM-annotated with the same written guidelines as the test set: two independent annotators labeled
    each risk, and an adjudicator resolved their disagreements (Cohen's κ 0.93 / 0.89 / 0.97 between the
    annotators). On a sample of 60 risks with human-verified labels, the protocol's labels matched
    95 / 85 / 100% of them.
- **Validation data**: 97 Kindynos risks from 6 other assessments and systems, used to choose the variant and
  to fit the temperature.
- **Procedure**: `laya.train.finetune` (laya 0.4.1), RLCD loss, 8 epochs, label smoothing 0.1, learning
  rate 2.5e-5 for the encoder and 1e-4 for the head, effective batch 64, seed 0: 27 minutes on one T4 GPU
  on Kaggle. Three variants were trained (4 epochs; 8 epochs with label smoothing; the same with the Kindynos
  risks twice). Among those Laya could calibrate, the one with the best mean macro-F1 on validation was
  kept: 76.0, against 71.8 and 68.2.
- **Reproduce**: [Kaggle notebook](<kaggle-notebook-url>), and the code in the Kindynos
  [`training/`](https://github.com/6MicheleStingo9/kindynos/tree/main/training) folder.

## Evaluation

The test set holds 145 risks that Kindynos wrote in 7 assessments: six simulated users (beginner,
intermediate and expert, in English and Italian) describing a system of their choice, plus the Kindynos example
assessment. The 28 systems of the training and validation data were chosen to differ from these. The
labels were pre-annotated by a model with the guidelines, then verified one by one by a human annotator,
who corrected 25 of the 435 and harmonized 17 across near-identical risks.

- **F1 per class** (risks in the test set): entity `ai` 91.8 (79), `human` 91.3 (51), `other` 57.1 (15);
  intent `intentional` 93.9 (33), `unintentional` 83.1 (84), `other` 24.4 (28); timing `pre-deployment`
  0.0 (2), `post-deployment` 97.4 (132), `other` 81.8 (11).
- **By language**, macro-F1 English / Italian: entity 82.9 / 76.8, intent 65.5 / 68.9, timing 60.5 / 58.8.
- **Calibration**: expected calibration error 3.8 / 15.7 / 3.2% (entity / intent / timing).
- **Per-risk predictions**: [`eval/kindynos_test.json`](eval/kindynos_test.json), with the probabilities of every
  value for each test risk.

## Provenance and licenses

- Weights: Apache-2.0, like the base model (`convaiinnovations/laya-multilingual`).
- MIT AI Risk Repository v4 data and the taxonomy definitions: CC BY 4.0, Slattery et al. (2025).
- Kindynos risk texts: generated with Gemini 2.5 Flash by the Kindynos pipeline.
- Labels of the Kindynos risks: LLM-annotated (two independent annotators and an adjudicator), protocol
  checked against human-verified labels on a sample (training and validation); verified by a human annotator
  (test).

## Citation

```bibtex
@misc{stingo2026layakindynoscausal,
  title  = {laya-kindynos-causal: a calibrated classifier for the MIT Causal Taxonomy of AI Risks},
  author = {Stingo, Michele},
  year   = {2026},
  url    = {https://huggingface.co/MicheleStingo/laya-kindynos-causal}
}

@article{slattery2025airisk,
  title   = {The AI Risk Repository: A Comprehensive Meta-Review, Database, and Taxonomy of Risks From Artificial Intelligence},
  author  = {Slattery, Peter and Saeri, Alexander K. and Grundy, Emily A. C. and Graham, Jess and Noetel, Michael and Uuk, Risto and Dao, James and Pour, Soroush and Casper, Stephen and Thompson, Neil},
  journal = {arXiv preprint arXiv:2408.12622},
  year    = {2025}
}
```
