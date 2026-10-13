"""
Laya data files for the causal classification.

Each risk becomes one Laya row: the state is the risk's subdomain in the MIT Domain Taxonomy
(code and name), then its title and description; the three axes are typed `choice` questions
whose options carry the MIT Causal Taxonomy definitions (Slattery et al., 2025, CC BY 4.0), so the
encoder reads the state once for all three. Kindynos writes its risks per subdomain and the MIT
labelling conventions differ by subdomain: the most frequent label of each subdomain alone scores
about as well as the text-only model. Subdomain names come from the MIT database
(files/data/processed/full.jsonl) for both sources, so training and Kindynos use the same strings.
Writes training/data/:

- causal_train.jsonl: the MIT train split with its labels (`expected`);
- causal_fit.jsonl and causal_val.jsonl: the same split divided by group (paper and risk
  category, as in data_prep/extract_dataset.py), about 15% of the groups for validation: the
  variants are trained on the first, compared and calibrated on the second;
- area_fit.jsonl and area_val.jsonl: the Kindynos training risks (files/data/area_trainset/, labelled
  with the protocol of its README), split by whole runs: six runs (three per language, drawn with
  a fixed seed) for validation and calibration, the others for training. Entries in which the
  domain analyzer states there is no significant risk (their title says so) are left out: they are
  not risks, and their labels (`other` on every axis) would teach that `other` means no risk;
- mit_eval.jsonl and area_test.jsonl: the two test sets in the same format, with their gold
  labels; they are for evaluation only, never for training, selection or calibration.

Usage (from the project root):
    python -m training.build_laya_data
"""

import json
import random
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# The pipeline builds what Laya reads with the same definitions (agents/causality_analyzer/laya_classifier.py)
from agents.causality_analyzer.laya_classifier import AXES, QUESTIONS, state, subdomain_names  # noqa: F401

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "files" / "data" / "processed"
AREA = ROOT / "evaluation" / "area_testset"
AREA_TRAIN = ROOT / "files" / "data" / "area_trainset"
OUT = ROOT / "training" / "data"
VAL_FRAC = 0.15
VAL_SEED = 0
# Validation runs of the Kindynos training risks: three English and three Italian runs of the 28
# planned in data_prep/area_trainset.py, drawn with random.Random(0).sample(runs, 3) per language.
AREA_VAL_RUNS = ("t13", "t14", "t25", "t26", "t27", "t28")
# Titles of the domain analyzer's "no significant risk" entries (Italian or English)
NO_RISK = re.compile(r"^\s*(nessun rischio|no (significant |relevant )?risk)", re.IGNORECASE)


def laya_row(rid: str, title: str, text: str, labels: Dict[str, str], subdomain: Optional[Tuple[str, str]] = None) -> Dict[str, Any]:
    return {"id": rid, "state": state(title, text, subdomain), "questions": QUESTIONS, "expected": {ax: labels[ax] for ax in AXES}}


def split_by_group(rows: List[Dict[str, Any]], frac: float, seed: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """(fit, val): whole groups (first two parts of the Ev_ID) go to validation until it holds `frac` of the rows."""
    group = lambda r: ".".join(r["id"].split(".")[:2])
    groups = sorted({group(r) for r in rows})
    random.Random(seed).shuffle(groups)
    val_groups, n = set(), 0
    for g in groups:
        if n >= frac * len(rows):
            break
        val_groups.add(g)
        n += sum(group(r) == g for r in rows)
    return [r for r in rows if group(r) not in val_groups], [r for r in rows if group(r) in val_groups]


def _read(path: Path) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _write(path: Path, rows: Iterable[Dict[str, Any]]) -> int:
    rows = list(rows)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    return len(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    names = subdomain_names()
    # By Ev_ID and text: the source repeats a few Ev_IDs for different risks (62.31.01-03)
    mit_sub = {(r["ev_id"], r["description"]): r["subdomain_id"] for r in _read(PROCESSED / "full.jsonl") if r["subdomain_id"]}
    with_name = lambda code: (code, names[code]) if code else None
    mit = lambda split: [laya_row(ex["meta"]["ev_id"], ex.get("title") or "", ex["input"], ex["labels"], with_name(mit_sub.get((ex["meta"]["ev_id"], ex["input"]))))
                         for ex in _read(PROCESSED / f"causal_clf.{split}.jsonl")]
    gold = {g["id"]: g for g in _read(AREA / "labels.jsonl")}
    area = [laya_row(r["id"], r["title"], r["text"], gold[r["id"]], with_name(r["subdomain"])) for r in _read(AREA / "risks.jsonl") if r["id"] in gold]
    train = mit("train")
    fit, val = split_by_group(train, VAL_FRAC, VAL_SEED)
    files = [("causal_train", train), ("causal_fit", fit), ("causal_val", val), ("mit_eval", mit("eval")), ("area_test", area)]
    if (AREA_TRAIN / "labels.jsonl").exists():
        labels = {g["id"]: g for g in _read(AREA_TRAIN / "labels.jsonl")}
        risks = [r for r in _read(AREA_TRAIN / "risks.jsonl") if r["id"] in labels]
        no_risk = [r for r in risks if NO_RISK.match(r["title"])]
        risks = [r for r in risks if not NO_RISK.match(r["title"])]
        print(f"Kindynos training risks: {len(no_risk)} 'no significant risk' entries left out")
        area_rows = lambda keep: [laya_row(r["id"], r["title"], r["text"], labels[r["id"]], with_name(r["subdomain"])) for r in risks if keep(r["run"])]
        files += [("area_fit", area_rows(lambda run: run not in AREA_VAL_RUNS)), ("area_val", area_rows(lambda run: run in AREA_VAL_RUNS))]
    else:
        print(f"no {AREA_TRAIN / 'labels.jsonl'}: area_fit/area_val not written")
    for name, rows in files:
        known = sum(r["state"].startswith("Risk subdomain: ") for r in rows)
        print(f"{name}.jsonl: {_write(OUT / f'{name}.jsonl', rows)} rows, {known} with their subdomain")
    for ax in AXES:
        dist = lambda rows: ", ".join(f"{k} {v / len(rows):.0%}" for k, v in sorted(Counter(r["expected"][ax] for r in rows).items()))
        print(f"  {ax}: fit [{dist(fit)}] | val [{dist(val)}]")


if __name__ == "__main__":
    main()
