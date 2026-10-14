"""
Paired comparison of two causal classifiers on the same test set.

Resamples the risks (2000 bootstrap draws, seed 0, the same draws for both models) and reports,
per axis, the difference A - B in accuracy and in macro-F1 with its 95% interval and a verdict:
"better" when the whole interval is above zero, "worse" when it is below, "on par" otherwise.
This is the success criterion fixed before the third Laya run: Laya should be at least on par
with Gemini on every axis and metric of the Kindynos risks. A missing prediction counts as wrong.

A and B are results files in evaluation/results/ (a Laya run, or run N of the Gemini baseline
with --run-a / --run-b), or `pipeline` for the labels the Kindynos pipeline gave the Kindynos risks.

Usage (from the project root):
    python -m evaluation.paired <results A | pipeline> <results B | pipeline> [--run-a N] [--run-b N]
"""

import argparse
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from agents.causality_analyzer.prompts import CAUSALITY_JSON_SCHEMA
from evaluation.metrics import accuracy, macro_f1, paired_bootstrap_ci
from utils.paths import DATA, ROOT

RESULTS = ROOT / "evaluation" / "results"
AREA = ROOT / "evaluation" / "area_testset"
MIT_EVAL = DATA / "processed" / "causal_clf.eval.jsonl"
AXES = ("entity", "intent", "timing")
TEST_SETS = {"area": "Kindynos risks", "mit": "MIT eval split"}

_RISK_PROPS = CAUSALITY_JSON_SCHEMA["additionalProperties"]["properties"]["risks"]["items"]["properties"]
LABELS: Dict[str, List[str]] = {ax: _RISK_PROPS[ax]["enum"] for ax in AXES}

Labels = Dict[str, Dict[str, Optional[str]]]


def _read(path: Path) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load(source: str, run: int) -> Tuple[str, str, Labels]:
    """(name, test set, {risk id: {axis: label}}) for a results file or `pipeline`."""
    if source == "pipeline":
        return "Kindynos pipeline (Gemini)", "area", {r["id"]: r["pipeline"] for r in _read(AREA / "risks.jsonl")}
    path = Path(source) if Path(source).exists() else RESULTS / source
    res = json.loads(path.read_text(encoding="utf-8"))
    test_set = "area" if "area" in res["task"] else "mit"
    name = path.stem.split("__")[1]
    if "runs" in res:
        preds, name = res["runs"][run - 1]["predictions"], f"{name}, run {run}"
    elif isinstance(res.get("predictions"), dict):
        preds = res["predictions"]
    else:
        raise SystemExit(f"{path.name} has no predictions (for the Kindynos pipeline labels pass `pipeline`)")
    choice = lambda p: p["choice"] if isinstance(p, dict) else p
    return name, test_set, {i: {ax: choice(p.get(ax)) for ax in AXES} for i, p in preds.items()}


def gold(test_set: str) -> Dict[str, Dict[str, str]]:
    if test_set == "area":
        return {g["id"]: {ax: g[ax] for ax in AXES} for g in _read(AREA / "labels.jsonl")}
    return {ex["meta"]["ev_id"]: ex["labels"] for ex in _read(MIT_EVAL)}


def compare(truth: Dict[str, Dict[str, str]], a: Labels, b: Labels, n_boot: int = 2000, seed: int = 0) -> Dict[str, Dict[str, Any]]:
    """{"<axis> <metric>": {a, b, diff, ci95, verdict}} over the risks of `truth`."""
    ids = sorted(truth)
    out = {}
    for ax in AXES:
        y = [truth[i][ax] for i in ids]
        pa = [a.get(i, {}).get(ax) for i in ids]
        pb = [b.get(i, {}).get(ax) for i in ids]
        metrics: Dict[str, Callable[[List[str], List[Optional[str]]], float]] = {
            "accuracy": accuracy,
            "macro-F1": lambda t, p, ax=ax: macro_f1(t, p, LABELS[ax]),
        }
        for name, metric in metrics.items():
            lo, hi = paired_bootstrap_ci(y, pa, pb, metric, n_boot, seed)
            out[f"{ax} {name}"] = {
                "a": metric(y, pa),
                "b": metric(y, pb),
                "diff": metric(y, pa) - metric(y, pb),
                "ci95": [lo, hi],
                "verdict": "better" if lo > 0 else "worse" if hi < 0 else "on par",
            }
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Paired bootstrap comparison of two causal classifiers")
    parser.add_argument("a", help="Results file (name in evaluation/results/ or path) or `pipeline`")
    parser.add_argument("b", help="Results file (name in evaluation/results/ or path) or `pipeline`")
    parser.add_argument("--run-a", type=int, default=1, help="Run of A, for results files with several runs")
    parser.add_argument("--run-b", type=int, default=1, help="Run of B, for results files with several runs")
    args = parser.parse_args()

    name_a, set_a, a = load(args.a, args.run_a)
    name_b, set_b, b = load(args.b, args.run_b)
    if set_a != set_b:
        raise SystemExit(f"A is on the {TEST_SETS[set_a]}, B on the {TEST_SETS[set_b]}")
    truth = gold(set_a)
    res = compare(truth, a, b)

    pct = lambda v: f"{v * 100:.1f}"
    signed = lambda v: f"{v * 100:+.1f}"
    print(f"A = {name_a}, B = {name_b} | {TEST_SETS[set_a]}, {len(truth)} risks, 2000 paired bootstrap draws\n")
    print("| Axis, metric | A % | B % | A - B [95% CI] | Verdict |")
    print("|---|---|---|---|---|")
    for key, r in res.items():
        print(f"| {key} | {pct(r['a'])} | {pct(r['b'])} | {signed(r['diff'])} [{signed(r['ci95'][0])}, {signed(r['ci95'][1])}] | {r['verdict']} |")
    worse = [k for k, r in res.items() if r["verdict"] == "worse"]
    print(f"\nA at least on par with B everywhere: {'yes' if not worse else 'no (worse on ' + ', '.join(worse) + ')'}")


if __name__ == "__main__":
    main()
