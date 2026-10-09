"""
Evaluate a Laya checkpoint on the two causal test sets: the MIT eval split and the AREA risks.

Runs in the training environment (requirements-train.txt). The checkpoint answers the three
typed questions for every risk (training/data/*.jsonl, built by training.build_laya_data); the
prediction is the most probable option. Scores use the same metrics as the Gemini results
(accuracy and macro-F1 with 95% bootstrap intervals, per-class F1, the MIT-train majority class
as reference) plus the calibration of the probabilities: expected calibration error of the
top-1 confidence and the multiclass Brier score. Results go to evaluation/results/.

Usage (from the project root):
    python -m training.evaluate_laya --model <checkpoint dir or hub id> --name <results slug> [--revision R]
"""

import argparse
import hashlib
import json
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import laya

from evaluation.metrics import accuracy, brier, ece, macro_f1, summarize

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "training" / "data"
RESULTS = ROOT / "evaluation" / "results"
AXES = ("entity", "intent", "timing")
TEST_SETS = {"causal_clf": "mit_eval.jsonl", "area_testset": "area_test.jsonl"}


def _read(path: Path) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _git_commit() -> str:
    run = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return run("rev-parse", "--short", "HEAD") + ("-dirty" if run("status", "--porcelain", "-uno") else "")


def predict(agent, rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """{id: {axis: {"choice", "probabilities"}}}. One call per risk: on CPU, predict_batch was
    about 5x slower per risk than single calls (3.8 s against 0.4-0.8 s)."""
    out = {}
    for r in rows:
        res = agent.predict(r["state"], r["questions"])
        out[r["id"]] = {ax: {"choice": res["answers"][ax]["choice"], "probabilities": res["answers"][ax]["probabilities"]} for ax in AXES}
    return out


def score(rows: List[Dict[str, Any]], preds: Dict[str, Any], labels: Dict[str, List[str]], seed: int) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for ax in AXES:
        y_true = [r["expected"][ax] for r in rows]
        y_pred = [preds[r["id"]][ax]["choice"] for r in rows]
        probs = [preds[r["id"]][ax]["probabilities"] for r in rows]
        conf = [max(p.values()) for p in probs]
        out[ax] = summarize(y_true, y_pred, labels[ax], seed=seed)
        out[ax]["calibration"] = {
            "ece": ece(conf, [t == p for t, p in zip(y_true, y_pred)]),
            "brier": brier(probs, y_true, labels[ax]),
            "mean_confidence": sum(conf) / len(conf),
        }
    out["all_three"] = {
        "accuracy": accuracy(
            [tuple(r["expected"][ax] for ax in AXES) for r in rows], [tuple(preds[r["id"]][ax]["choice"] for ax in AXES) for r in rows]
        )
    }
    return out


def majority_reference(train: List[Dict[str, Any]], rows: List[Dict[str, Any]], labels: Dict[str, List[str]]) -> Dict[str, Any]:
    out = {}
    for ax in AXES:
        label = Counter(r["expected"][ax] for r in train).most_common(1)[0][0]
        y_true = [r["expected"][ax] for r in rows]
        out[ax] = {"label": label, "accuracy": accuracy(y_true, [label] * len(rows)), "macro_f1": macro_f1(y_true, [label] * len(rows), labels[ax])}
    return out


def subsets(rows: List[Dict[str, Any]], preds: Dict[str, Any], labels: Dict[str, List[str]]) -> Dict[str, Any]:
    """AREA only: scores by language and by source (generated runs or the example run)."""
    meta = {r["id"]: r for r in _read(ROOT / "evaluation" / "area_testset" / "risks.jsonl")}
    out = {}
    for key in ("language", "source"):
        for value in sorted({meta[r["id"]][key] for r in rows}):
            sel = [r for r in rows if meta[r["id"]][key] == value]
            out[f"{key}={value}"] = {"n": len(sel)}
            for ax in AXES:
                y_true = [r["expected"][ax] for r in sel]
                y_pred = [preds[r["id"]][ax]["choice"] for r in sel]
                out[f"{key}={value}"][ax] = {"accuracy": accuracy(y_true, y_pred), "macro_f1": macro_f1(y_true, y_pred, labels[ax])}
    return out


def write_markdown(path: Path, res: Dict[str, Any]) -> None:
    pct = lambda v: f"{v * 100:.1f}"
    ci = lambda c: f"[{pct(c[0])}–{pct(c[1])}]"
    m = res["metrics"]
    lines = [
        f"# {res['task']} — {res['model']['name']}",
        "",
        f"Test set: `{res['data']['file']}` ({res['data']['rows']} risks). Checkpoint `{res['model']['path']}`"
        + (f" @ {res['model']['revision'][:10]}" if res["model"].get("revision") else "")
        + f". Run {res['run']['date']} on {res['run']['device']} · {res['run']['seconds_per_risk']:.2f} s per risk (3 questions) · commit `{res['run']['git_commit']}`.",
        "",
        "| Axis | Accuracy % [95% CI] | Macro-F1 % [95% CI] | ECE % | Brier | Majority class (MIT train): acc / macro-F1 % |",
        "|---|---|---|---|---|---|",
    ]
    for ax in AXES:
        a, c, b = m[ax], m[ax]["calibration"], res["majority_reference"][ax]
        lines.append(
            f"| {ax} | {pct(a['accuracy'])} {ci(a['accuracy_ci95'])} | {pct(a['macro_f1'])} {ci(a['macro_f1_ci95'])} "
            f"| {pct(c['ece'])} | {c['brier']:.3f} | {pct(b['accuracy'])} / {pct(b['macro_f1'])} (`{b['label']}`) |"
        )
    lines += ["", f"All three axes correct: {pct(m['all_three']['accuracy'])}%.", "", "Per-class F1 % (gold support):", ""]
    for ax in AXES:
        lines.append(f"- **{ax}**: " + ", ".join(f"{k} {pct(s['f1'])} (n={s['support']})" for k, s in m[ax]["per_class"].items()))
    if res.get("subsets"):
        lines += ["", "| Subset | n | " + " | ".join(f"{ax} acc / macro-F1 %" for ax in AXES) + " |", "|---|---|" + "---|" * len(AXES)]
        for name, sub in res["subsets"].items():
            lines.append(f"| {name} | {sub['n']} | " + " | ".join(f"{pct(sub[ax]['accuracy'])} / {pct(sub[ax]['macro_f1'])}" for ax in AXES) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a Laya checkpoint on the causal test sets")
    parser.add_argument("--model", required=True, help="Checkpoint directory or Hugging Face id")
    parser.add_argument("--revision", default=None, help="Hub revision (for a Hugging Face id)")
    parser.add_argument("--name", required=True, help="Slug for the results files, e.g. laya-multilingual-zeroshot")
    parser.add_argument("--seed", type=int, default=0, help="Bootstrap seed")
    args = parser.parse_args()

    agent = laya.load(args.model, revision=args.revision) if args.revision else laya.load(args.model)
    train = _read(DATA / "causal_train.jsonl")
    labels = {ax: list(train[0]["questions"][ax]["criteria"]) for ax in AXES}
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    RESULTS.mkdir(parents=True, exist_ok=True)
    for task, fname in TEST_SETS.items():
        rows = _read(DATA / fname)
        t0 = time.time()
        preds = predict(agent, rows)
        elapsed = time.time() - t0
        res = {
            "task": task,
            "model": {"name": args.name, "path": args.model, "revision": args.revision},
            "run": {"date": date, "device": str(getattr(agent, "device", "cpu")), "seconds_per_risk": elapsed / len(rows), "git_commit": _git_commit()},
            "data": {"file": f"training/data/{fname}", "sha256": hashlib.sha256((DATA / fname).read_bytes()).hexdigest(), "rows": len(rows)},
            "majority_reference": majority_reference(train, rows, labels),
            "metrics": score(rows, preds, labels, args.seed),
            "subsets": subsets(rows, preds, labels) if task == "area_testset" else None,
            "predictions": preds,
        }
        stem = f"{task}__{args.name}__{date}"
        (RESULTS / f"{stem}.json").write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        write_markdown(RESULTS / f"{stem}.md", res)
        print((RESULTS / f"{stem}.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
