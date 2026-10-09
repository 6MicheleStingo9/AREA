"""
Laya data files for the causal classification.

Each risk becomes one Laya row: the state is the risk text (title, then description) and the
three axes are typed `choice` questions whose options carry the MIT Causal Taxonomy definitions
(Slattery et al., 2025, CC BY 4.0), so the encoder reads the state once for all three. Writes
training/data/:

- causal_train.jsonl: the MIT train split with its labels (`expected`);
- causal_fit.jsonl and causal_val.jsonl: the same split divided by group (paper and risk
  category, as in data_prep/extract_dataset.py), about 15% of the groups for validation: the
  variants are trained on the first, compared and calibrated on the second;
- mit_eval.jsonl and area_test.jsonl: the two test sets in the same format, with their gold
  labels; they are for evaluation only, never for training, selection or calibration.

Usage (from the project root):
    python -m training.build_laya_data
"""

import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "files" / "data" / "processed"
AREA = ROOT / "evaluation" / "area_testset"
OUT = ROOT / "training" / "data"
AXES = ("entity", "intent", "timing")
VAL_FRAC = 0.15
VAL_SEED = 0

QUESTIONS: Dict[str, Dict[str, Any]] = {
    "entity": {
        "type": "choice",
        "instructions": "Who or what causes the risk, as the text frames it?",
        "criteria": {
            "ai": "The risk is caused by a decision or action made by an AI system",
            "human": "The risk is caused by a decision or action made by humans",
            "other": "The risk is caused by some other reason or is ambiguous",
        },
    },
    "intent": {
        "type": "choice",
        "instructions": "Does the risk come from an expected or an unexpected outcome of pursuing a goal?",
        "criteria": {
            "intentional": "The risk occurs due to an expected outcome from pursuing a goal",
            "unintentional": "The risk occurs due to an unexpected outcome from pursuing a goal",
            "other": "The risk is presented as occurring without clearly specifying the intentionality",
        },
    },
    "timing": {
        "type": "choice",
        "instructions": "When does the risk occur?",
        "criteria": {
            "pre-deployment": "The risk occurs before the AI is deployed",
            "post-deployment": "The risk occurs after the AI model has been trained and deployed",
            "other": "The risk is presented without a clearly specified time of occurrence",
        },
    },
}


def state(title: str, text: str) -> str:
    return f"{title}\n{text}" if title else text


def laya_row(rid: str, title: str, text: str, labels: Dict[str, str]) -> Dict[str, Any]:
    return {"id": rid, "state": state(title, text), "questions": QUESTIONS, "expected": {ax: labels[ax] for ax in AXES}}


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
    mit = lambda split: (laya_row(ex["meta"]["ev_id"], ex.get("title") or "", ex["input"], ex["labels"])
                         for ex in _read(PROCESSED / f"causal_clf.{split}.jsonl"))
    gold = {g["id"]: g for g in _read(AREA / "labels.jsonl")}
    area = (laya_row(r["id"], r["title"], r["text"], gold[r["id"]]) for r in _read(AREA / "risks.jsonl") if r["id"] in gold)
    train = list(mit("train"))
    fit, val = split_by_group(train, VAL_FRAC, VAL_SEED)
    for name, rows in (("causal_train", train), ("causal_fit", fit), ("causal_val", val), ("mit_eval", mit("eval")), ("area_test", area)):
        print(f"{name}.jsonl: {_write(OUT / f'{name}.jsonl', rows)} rows")
    for ax in AXES:
        dist = lambda rows: ", ".join(f"{k} {v / len(rows):.0%}" for k, v in sorted(Counter(r["expected"][ax] for r in rows).items()))
        print(f"  {ax}: fit [{dist(fit)}] | val [{dist(val)}]")


if __name__ == "__main__":
    main()
