"""
Compare fine-tuned Laya variants on the validation split and pick one.

Scores each checkpoint on training/data/causal_val.jsonl with the metrics of
training.evaluate_laya and picks the highest macro-F1 averaged over the three axes (the
prediction is the most probable option, so the fitted temperatures do not change it). Writes
training/checkpoints/selection.json; the test sets are not touched.

Usage (from the project root, training environment):
    python -m training.select_laya <checkpoint name> [<checkpoint name> ...] [--limit N]
"""

import argparse
import json

import laya

from training.evaluate_laya import AXES, DATA, predict, score, _read
from training.finetune_laya import CHECKPOINTS


def main() -> None:
    parser = argparse.ArgumentParser(description="Pick a Laya variant on the validation split")
    parser.add_argument("names", nargs="+", help="Checkpoint directories under training/checkpoints/")
    parser.add_argument("--limit", type=int, default=None, help="Only the first N validation rows (smoke runs)")
    args = parser.parse_args()

    rows = _read(DATA / "causal_val.jsonl")[: args.limit]
    labels = {ax: list(rows[0]["questions"][ax]["criteria"]) for ax in AXES}
    variants = {}
    for name in args.names:
        m = score(rows, predict(laya.load(str(CHECKPOINTS / name)), rows), labels, seed=0)
        run = json.loads((CHECKPOINTS / name / "training_run.json").read_text(encoding="utf-8"))
        variants[name] = {
            "epochs": run["config"]["epochs"],
            "oversample": run.get("oversample", False),
            "mean_macro_f1": sum(m[ax]["macro_f1"] for ax in AXES) / len(AXES),
            "all_three": m["all_three"]["accuracy"],
            **{ax: {"accuracy": m[ax]["accuracy"], "macro_f1": m[ax]["macro_f1"], "ece": m[ax]["calibration"]["ece"]} for ax in AXES},
        }
    best = max(variants, key=lambda n: variants[n]["mean_macro_f1"])
    selection = {"best": best, "criterion": "mean macro-F1 over the axes", "data": "training/data/causal_val.jsonl", "rows": len(rows), "variants": variants}
    (CHECKPOINTS / "selection.json").write_text(json.dumps(selection, indent=2) + "\n", encoding="utf-8")

    pct = lambda v: f"{v * 100:5.1f}"
    print(f"validation: {len(rows)} rows | accuracy / macro-F1 % per axis")
    for name, v in variants.items():
        cells = "  ".join(f"{ax} {pct(v[ax]['accuracy'])} / {pct(v[ax]['macro_f1'])}" for ax in AXES)
        print(f"{'*' if name == best else ' '} {name:12} {cells}  | mean macro-F1 {pct(v['mean_macro_f1'])} | all three {pct(v['all_three'])}")
    print(f"best: {best}")


if __name__ == "__main__":
    main()
