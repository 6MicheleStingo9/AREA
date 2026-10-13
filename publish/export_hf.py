"""
Build the two Hugging Face repositories of Kindynos in publish/build/.

- model/ (MicheleStingo/laya-kindynos-causal): the laya-causal-v4 checkpoint
  (training/checkpoints/, not versioned), its card and Apache-2.0 license (publish/huggingface/model/),
  the root config.json the Hub uses to recognise a Laya model, and eval/kindynos_test.json, the
  scored predictions on the test risks.
- dataset/ (MicheleStingo/kindynos-causal-risks): its card (publish/huggingface/dataset/), the
  `kindynos` and `mit` configs split exactly as in training (training/build_laya_data.py), the
  labeling guidelines, the raw annotations and the quality check. As in the cards, these copies call
  the annotators LLM annotators.

The rows are checked against the Laya training files (training/data/, when present): every exported
risk must give the same text and labels Laya was trained, selected or tested on.

Usage (from the project root):
    python -m publish.export_hf [--out publish/build]
"""

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List

from agents.causality_analyzer.laya_classifier import AXES, state, subdomain_names
from training.build_laya_data import AREA_VAL_RUNS, NO_RISK, VAL_FRAC, VAL_SEED, split_by_group

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "publish" / "huggingface"
CHECKPOINT = ROOT / "training" / "checkpoints" / "laya-causal-v4"
TRAIN_DATA = ROOT / "training" / "data"
AREA_TEST = ROOT / "evaluation" / "area_testset"
AREA_TRAIN = ROOT / "files" / "data" / "area_trainset"
PROCESSED = ROOT / "files" / "data" / "processed"
TEST_RESULTS = ROOT / "evaluation" / "results" / "area_testset__laya-causal-v4__2026-10-12.json"
CHECKPOINT_FILES = ("model.safetensors", "rl_agent_config.json", "questions.json", "training_run.json",
                    "encoder/config.json", "tokenizer/tokenizer.json", "tokenizer/tokenizer_config.json")
# Laya training file of each exported split
TRAINING_FILES = {("kindynos", "train"): "area_fit", ("kindynos", "validation"): "area_val", ("kindynos", "test"): "area_test",
                  ("mit", "train"): "causal_fit", ("mit", "validation"): "causal_val", ("mit", "test"): "mit_eval"}

QUALITY_README = """# Quality check

The labeling protocol of the train and validation splits (two independent LLM annotators and an
adjudicator), run once on 60 random risks of the test split and scored against their human-verified
labels. `labels.jsonl` holds the protocol's labels (by test `id`), `annotations/` the two annotators'.

| Axis | Accuracy % | Macro-F1 % |
|---|---|---|
| entity | 95.0 | 90.5 |
| intent | 85.0 | 75.9 |
| timing | 100.0 | 66.7 (no pre-deployment risk in the sample) |
"""


def _read(path: Path) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _write(path: Path, rows: Iterable[Dict[str, Any]]) -> int:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    return len(rows)


def _replace(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, f"expected once: {old[:60]!r}"
    return text.replace(old, new)


def kindynos_splits(names: Dict[str, str]) -> Dict[str, List[Dict[str, Any]]]:
    """The risks written by Kindynos: train and validation by run, as in training; the test risks."""
    def row(r, labels, **extra):
        code = r["subdomain"]
        return {
            "id": r["id"], "language": r["language"], "run": extra.pop("run"), "profile": r.get("profile"),
            "system": extra.pop("system", None), "text_model": r.get("model"), "severity": r.get("severity"),
            "subdomain_id": code, "subdomain_name": names.get(code), "title": r["title"], "text": r["text"],
            **{ax: labels[ax] for ax in AXES},
            "label_source": None, "source": None, "changed_in_review": None, "harmonized": None, **extra,
        }

    labels = {g["id"]: g for g in _read(AREA_TRAIN / "labels.jsonl")}
    splits: Dict[str, List[Dict[str, Any]]] = {"train": [], "validation": [], "test": []}
    for r in _read(AREA_TRAIN / "risks.jsonl"):
        if NO_RISK.match(r["title"]):
            continue  # "no significant risk" entries are not risks (left out of training too)
        g = labels[r["id"]]
        split = "validation" if r["run"] in AREA_VAL_RUNS else "train"
        splits[split].append(row(r, g, run=r["run"], system=r["system"], label_source=g["source"]))
    gold = {g["id"]: g for g in _read(AREA_TEST / "labels.jsonl")}
    for r in _read(AREA_TEST / "risks.jsonl"):
        g = gold[r["id"]]
        harmonized = [{"axis": ax, "reviewed": h["reviewed"], "reason": h["reason"]} for ax, h in (g.get("harmonized") or {}).items()]
        splits["test"].append(row(r, g, run=r["run_id"][:8], source=r["source"], changed_in_review=g.get("changed") or [], harmonized=harmonized))
    return splits


def mit_splits(names: Dict[str, str]) -> Dict[str, List[Dict[str, Any]]]:
    """The causally coded MIT risks: the train split divided by group as in training, the eval split."""
    # By Ev_ID and text, as training/build_laya_data.py: the source repeats a few Ev_IDs for different risks
    subdomain = {(r["ev_id"], r["description"]): r["subdomain_id"] for r in _read(PROCESSED / "full.jsonl") if r["subdomain_id"]}

    def row(ex):
        code = subdomain.get((ex["meta"]["ev_id"], ex["input"]))
        return {"id": ex["meta"]["ev_id"], "paper_id": ex["meta"]["paper_id"], "subdomain_id": code,
                "subdomain_name": names[code] if code else None, "title": ex.get("title") or "", "text": ex["input"],
                **{ax: ex["labels"][ax] for ax in AXES}}

    fit, val = split_by_group([row(ex) for ex in _read(PROCESSED / "causal_clf.train.jsonl")], VAL_FRAC, VAL_SEED)
    return {"train": fit, "validation": val, "test": [row(ex) for ex in _read(PROCESSED / "causal_clf.eval.jsonl")]}


def check_against_training(configs: Dict[str, Dict[str, List[Dict[str, Any]]]]) -> None:
    """Each exported split must rebuild its Laya training file: same ids, texts and labels."""
    if not TRAIN_DATA.is_dir():
        print("training/data/ missing: rows not checked against the training files")
        return
    for (config, split), name in TRAINING_FILES.items():
        # Lists in order, not dicts: a few MIT Ev_IDs repeat in the source
        trained = [(r["id"], r["state"], tuple(r["expected"][ax] for ax in AXES)) for r in _read(TRAIN_DATA / f"{name}.jsonl")]
        rows = configs[config][split]
        rebuilt = [(r["id"], state(r["title"], r["text"], (r["subdomain_id"], r["subdomain_name"]) if r["subdomain_id"] else None),
                    tuple(r[ax] for ax in AXES)) for r in rows]
        assert rebuilt == trained, f"{config}/{split} differs from {name}.jsonl"
        print(f"{config}/{split}: {len(rows)} risks, identical to training/data/{name}.jsonl")


def build_dataset(out: Path) -> None:
    names = subdomain_names()
    configs = {"kindynos": kindynos_splits(names), "mit": mit_splits(names)}
    check_against_training(configs)
    for config, splits in configs.items():
        for split, rows in splits.items():
            _write(out / config / f"{split}.jsonl", rows)
    shutil.copy(CARDS / "dataset" / "README.md", out / "README.md")

    labeling = (AREA_TEST / "LABELING.md").read_text(encoding="utf-8")
    labeling = _replace(labeling, "# Labeling guidelines — Kindynos causal test set", "# Labeling guidelines — Kindynos causal risks")
    labeling = _replace(labeling, "Gold labels for `risks.jsonl` follow", "The labels of the Kindynos risks follow")
    workflow = labeling[labeling.index("## Workflow"):labeling.index("## Known differences")]
    labeling = _replace(labeling, workflow, (
        "## Workflow\n\n"
        "The test labels were proposed by an LLM with these rules, blind to the pipeline labels, then reviewed by\n"
        "a human annotator, who decided each final value (`changed_in_review` in the test split).\n\n"
        "After the review, groups of near-duplicate risks (same subdomain, near-identical wording) with mixed\n"
        "labels were harmonized: to the MIT training convention for that subdomain where it is clear, and by\n"
        "rule 1 where the MIT annotators are split. Each harmonized label keeps the reviewed value and the\n"
        "reason (`harmonized` in the test split).\n\n"))
    (out / "LABELING.md").write_text(labeling, encoding="utf-8")

    prompts = (AREA_TRAIN / "annotations" / "PROMPTS.md").read_text(encoding="utf-8")
    prompts = _replace(prompts, (
        "The exact instructions given to the Claude subagents (Opus 5.5) of the protocol in\n"
        "[../README.md](../README.md), each to a fresh subagent; `{...}` are filled per batch with absolute\n"
        "paths and counts."), (
        "The exact instructions given to the LLM annotators of the labeling protocol (see the dataset card),\n"
        "each in a fresh session; `{...}` are filled per batch with file paths and counts."))
    (out / "annotations").mkdir(parents=True, exist_ok=True)
    (out / "annotations" / "PROMPTS.md").write_text(prompts, encoding="utf-8")
    for who in ("a", "b", "adjudication"):
        shutil.copytree(AREA_TRAIN / "annotations" / who, out / "annotations" / who, dirs_exist_ok=True)

    check = AREA_TEST / "annotator_check"
    (out / "quality_check").mkdir(parents=True, exist_ok=True)
    (out / "quality_check" / "README.md").write_text(QUALITY_README, encoding="utf-8")
    shutil.copy(check / "labels.jsonl", out / "quality_check" / "labels.jsonl")
    for who in ("a", "b"):
        shutil.copytree(check / "annotations" / who, out / "quality_check" / "annotations" / who, dirs_exist_ok=True)


def build_model(out: Path) -> None:
    if not CHECKPOINT.is_dir():
        raise SystemExit(f"No checkpoint at {CHECKPOINT}")
    for name in CHECKPOINT_FILES:
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(CHECKPOINT / name, out / name)
    for name in ("README.md", "LICENSE", "config.json"):
        shutil.copy(CARDS / "model" / name, out / name)
    (out / "eval").mkdir(exist_ok=True)
    shutil.copy(TEST_RESULTS, out / "eval" / "kindynos_test.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Hugging Face model and dataset repositories")
    parser.add_argument("--out", default=str(ROOT / "publish" / "build"), help="Output folder")
    out = Path(parser.parse_args().out)
    for name in ("dataset", "model"):
        shutil.rmtree(out / name, ignore_errors=True)
    build_dataset(out / "dataset")
    build_model(out / "model")
    for name in ("dataset", "model"):
        files = [p for p in (out / name).rglob("*") if p.is_file()]
        print(f"{name}/: {len(files)} files, {sum(p.stat().st_size for p in files) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
