"""
Compare fine-tuned Laya variants on a validation split and pick one.

Scores each checkpoint on training/data/causal_val.jsonl (the MIT validation groups) or, with
`--val area`, on area_val.jsonl (the Kindynos validation runs) with the metrics of
training.evaluate_laya and picks the highest macro-F1 averaged over the three axes (the
prediction is the most probable option, so the fitted temperatures do not change it), among the
variants Laya can calibrate: a fitted temperature at Laya's upper bound (laya.common.TEMP_MAX)
means the probabilities stay overconfident, which rules out confidence thresholds. Only if no
variant qualifies does the choice fall back to macro-F1 alone, with a warning. Writes
training/checkpoints/selection.json; the test sets are not touched.

Usage (from the project root, training environment):
    python -m training.select_laya <checkpoint name> [<checkpoint name> ...] [--val mit|area] [--limit N]
"""

import argparse
import json
from typing import Any, Dict, Optional

import laya
from laya.common import QTYPES, TEMP_MAX

from training.evaluate_laya import AXES, DATA, predict, score, _read
from training.finetune_laya import CHECKPOINTS


def calibratable(calibration: Optional[Dict[str, Any]]) -> bool:
    """Whether the temperatures fitted on validation for `choice` questions stay below Laya's cap."""
    if not calibration:
        return False
    temps = [calibration["temperature"][QTYPES["choice"]]]
    temps += [t for k, t in (calibration.get("temperature_by_options") or {}).items() if k.startswith("choice")]
    return all(t < TEMP_MAX for t in temps)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pick a Laya variant on the validation split")
    parser.add_argument("names", nargs="+", help="Checkpoint directories under training/checkpoints/")
    parser.add_argument("--val", choices=["mit", "area"], default="mit", help="mit: causal_val.jsonl; area: area_val.jsonl")
    parser.add_argument("--limit", type=int, default=None, help="Only the first N validation rows (smoke runs)")
    args = parser.parse_args()

    val = "area_val.jsonl" if args.val == "area" else "causal_val.jsonl"
    rows = _read(DATA / val)[: args.limit]
    labels = {ax: list(rows[0]["questions"][ax]["criteria"]) for ax in AXES}
    variants = {}
    for name in args.names:
        m = score(rows, predict(laya.load(str(CHECKPOINTS / name)), rows), labels, seed=0)
        run = json.loads((CHECKPOINTS / name / "training_run.json").read_text(encoding="utf-8"))
        cal = run.get("calibration")
        variants[name] = {
            "epochs": run["config"]["epochs"],
            "oversample": run.get("oversample", False),
            "area": run.get("area"),
            "label_smoothing": run["config"].get("label_smoothing", 0.0),
            "temperature": cal["temperature"][QTYPES["choice"]] if cal else None,
            "calibratable": calibratable(cal),
            "mean_macro_f1": sum(m[ax]["macro_f1"] for ax in AXES) / len(AXES),
            "mean_brier": sum(m[ax]["calibration"]["brier"] for ax in AXES) / len(AXES),
            "all_three": m["all_three"]["accuracy"],
            **{ax: {"accuracy": m[ax]["accuracy"], "macro_f1": m[ax]["macro_f1"], "ece": m[ax]["calibration"]["ece"],
                    "brier": m[ax]["calibration"]["brier"]} for ax in AXES},
        }
    pool = [n for n in variants if variants[n]["calibratable"]]
    best = max(pool or variants, key=lambda n: variants[n]["mean_macro_f1"])
    selection = {
        "best": best,
        "criterion": f"mean macro-F1 over the axes, among the variants whose fitted temperature stays below {TEMP_MAX}",
        "data": f"training/data/{val}",
        "rows": len(rows),
        "variants": variants,
    }
    if not pool:
        selection["warning"] = "no variant could be calibrated: picked on macro-F1 alone"
    (CHECKPOINTS / "selection.json").write_text(json.dumps(selection, indent=2) + "\n", encoding="utf-8")

    pct = lambda v: f"{v * 100:5.1f}"
    print(f"validation: {len(rows)} rows | accuracy / macro-F1 % per axis")
    for name, v in variants.items():
        cells = "  ".join(f"{ax} {pct(v[ax]['accuracy'])} / {pct(v[ax]['macro_f1'])}" for ax in AXES)
        cal = f"T {v['temperature']:.2f}" if v["temperature"] is not None else "not calibrated"
        flag = "" if v["calibratable"] else "  (excluded: temperature at the cap or missing)"
        print(f"{'*' if name == best else ' '} {name:12} {cells}  | mean macro-F1 {pct(v['mean_macro_f1'])} | {cal}{flag}")
    print(f"best: {best}" + (f"  WARNING: {selection['warning']}" if not pool else ""))


if __name__ == "__main__":
    main()
