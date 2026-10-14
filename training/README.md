# Training the causal model

The causal analysis of Kindynos uses laya-kindynos-causal:
[Laya-multilingual](https://huggingface.co/convaiinnovations/laya-multilingual) (Apache-2.0, 322M
parameters, typed decisions with calibrated probabilities) fine-tuned on the MIT training split and on
risks written by Kindynos. The checkpoint chosen, `laya-causal-v4`, is the published one: its card on
[Hugging Face](https://huggingface.co/MicheleStingo/laya-kindynos-causal) gives the results, and the data
are on [Hugging Face](https://huggingface.co/datasets/MicheleStingo/kindynos-causal-risks) and
[Kaggle](https://www.kaggle.com/datasets/michelestingo/kindynos-causal-risks).

## Environment and data

Training has its own environment:

```bash
python -m venv .venv-train
.venv-train/bin/pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.1
.venv-train/bin/pip install -r requirements-train.txt
.venv-train/bin/python -m training.build_laya_data     # training/data/: one row per risk (subdomain, title, text), three typed questions
```

Laya reads each risk with its subdomain in the MIT Domain Taxonomy: Kindynos writes its risks per
subdomain, and the MIT labels follow conventions that differ by subdomain. The rows come from two sources:

- the MIT training split ([files/data/](../files/data/README.md)), divided into training rows
  (`causal_fit.jsonl`) and validation groups (`causal_val.jsonl`);
- risks written by Kindynos for 28 simulated systems unlike those of the test set, labelled by Claude
  subagents with the rules of the test set ([files/data/area_trainset/](../files/data/area_trainset/README.md)),
  because MIT-only training does not learn how Kindynos frames its risks:

```bash
python -m data_prep.area_trainset generate   # questionnaire + domain analysis per run (calls the LLM, resumable)
python -m data_prep.area_trainset collect    # then batches / disagreements / merge for the labels
```

## Fine-tuning and selection

`training.finetune_laya` trains a variant and calibrates its probabilities on held-out risks;
`training.select_laya` compares the variants, keeps only those Laya can calibrate (fitted temperature below
its cap) and picks the best mean macro-F1. Only the chosen variant is evaluated on the test sets. With
`--area`, `training.finetune_laya` adds the Kindynos risks to the training rows and calibrates on six
Kindynos runs held out (`area_val.jsonl`), and `training.select_laya --val area` compares the variants on
those runs.

Fine-tuning needs a GPU (about 15 hours on a laptop CPU):

- [kaggle_finetune.ipynb](kaggle_finetune.ipynb) runs it on Kaggle (GPU, Internet on;
  [published run](https://www.kaggle.com/code/michelestingo/kindynos-fine-tuning-laya-to-label-ai-risks)):
  it trains the published configuration (about 35 minutes), or the three variants with
  `COMPARE_VARIANTS = True`, and evaluates the model on the test risks; `SMOKE_TEST = True` checks every
  step on a few risks, even on a CPU;
- or run `python -m training.finetune_laya --device cuda` per variant (`--limit` and `--val-limit` for
  smoke runs).

## Evaluation

```bash
.venv-train/bin/python -m training.evaluate_laya --model <checkpoint> --name <slug>   # both test sets
```

The results go to `evaluation/results/`, next to those of the other classifiers ([evaluation](../evaluation/README.md)).
