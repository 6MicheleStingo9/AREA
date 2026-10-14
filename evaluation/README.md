# Evaluation

Two test sets measure how well a classifier labels the causes of AI risks:

- **the MIT eval split**: the [MIT AI Risk Repository](../files/data/README.md) (CC BY 4.0) provides expert
  labels for both taxonomies, and `files/data/processed/` holds the extracted datasets with a frozen
  train/eval split;
- **the Kindynos test set**: risks written by Kindynos itself, from simulated questionnaires for each
  profile and language, labelled by hand following [area_testset/LABELING.md](area_testset/LABELING.md).

Every run is saved in [results/](results/), and [results/comparison.md](results/comparison.md) puts them side
by side. The causal model of Kindynos is evaluated with `training.evaluate_laya` ([training](../training/README.md)).

## The LLM on the MIT eval split

The causal classification baseline measures how well the LLM assigns entity, intent and timing to the eval
risks (accuracy and macro-F1 with 95% bootstrap intervals):

```bash
python data_prep/extract_dataset.py        # rebuild files/data/processed/ (+ manifest.json)
python -m evaluation.causal_baseline       # results in evaluation/results/ (calls the LLM)
```

Progress is saved after every LLM call: if a run stops, for example on the daily quota of the Gemini free
tier, rerunning the same command resumes it.

## The Kindynos test set

```bash
python -m evaluation.area_testset generate   # questionnaires + domain/causality analyses (calls the LLM)
python -m evaluation.area_testset collect    # one row per risk in evaluation/area_testset/risks.jsonl
python -m evaluation.area_testset evaluate   # pipeline labels vs labels.jsonl, results in evaluation/results/
```

## Comparing classifiers

Two classifiers are compared on the same risks with a paired bootstrap: per axis, the difference in
accuracy and in macro-F1 with its 95% interval, and a verdict (better, on par, worse):

```bash
python -m evaluation.paired <results file> pipeline   # e.g. a Laya run against the Kindynos pipeline labels
python -m evaluation.compare                          # every run side by side, in evaluation/results/comparison.md
```
