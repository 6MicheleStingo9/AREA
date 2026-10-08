"""
Gemini baseline on the causal classification eval split (Entity / Intent / Timing).

The model gets the production causality system prompt (MIT causal taxonomy
definitions, agents/causality_analyzer/prompts.py) and a classification-only user
prompt, with risks sent in batches as the pipeline does. Each risk is its title
plus its description. Predictions, metrics (with 95% bootstrap intervals), a
majority-class reference and provenance are written to evaluation/results/.
Progress is checkpointed after every call: rerunning an interrupted command
(e.g. after the daily quota is exhausted) resumes it.

Usage (from the project root):
    python -m evaluation.causal_baseline [--batch-size 20] [--repeat 1] [--limit N]
"""

import argparse
import hashlib
import json
import os
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from agents.causality_analyzer.prompts import CAUSALITY_JSON_SCHEMA, CAUSALITY_SYSTEM_PROMPT
from evaluation.metrics import accuracy, macro_f1, summarize
from utils.utils import apply_retry, create_logger, get_llm_instance

_logger = create_logger("causal_baseline")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "files" / "data" / "processed"
AXES = ("entity", "intent", "timing")

# Allowed values, taken from the production causality schema
_RISK_PROPS = CAUSALITY_JSON_SCHEMA["additionalProperties"]["properties"]["risks"]["items"]["properties"]
LABELS: Dict[str, List[str]] = {ax: _RISK_PROPS[ax]["enum"] for ax in AXES}

USER_PROMPT = """Classify each risk below along the three dimensions of the MIT Causal Taxonomy
(Entity, Intent, Timing), following the definitions and guidelines in the system prompt.

Risks (JSON list; each item has an "id", a "title" and a "description"):
{risks_json}

Return ONLY a JSON object {{"items": [{{"id": "...", "entity": "...", "intent": "...", "timing": "..."}}]}}
with exactly one item per input risk, using only the allowed lowercase values.
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "string"}, **{ax: {"type": "string", "enum": LABELS[ax]} for ax in AXES}},
                "required": ["id", *AXES],
            },
        }
    },
    "required": ["items"],
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_commit() -> Optional[str]:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "-uno"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        return sha + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return None


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def classify_batch(llm, batch: List[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
    """One LLM call: returns {id: {axis: label}} for the items the model answered."""
    risks = [{"id": ex["meta"]["ev_id"], "title": ex.get("title") or "", "description": ex["input"]} for ex in batch]
    messages = [
        {"role": "system", "content": CAUSALITY_SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT.format(risks_json=json.dumps(risks, ensure_ascii=False, indent=1))},
    ]
    resp = llm.invoke(messages)
    parsed = resp.parsed if hasattr(resp, "parsed") else resp
    wanted = {r["id"] for r in risks}
    return {it["id"]: {ax: it[ax] for ax in AXES} for it in parsed.get("items", []) if it.get("id") in wanted}


def new_run_state() -> Dict[str, Any]:
    return {"preds": {}, "calls": 0, "elapsed_s": 0.0, "done": [], "complete": False}


def predict(llm, examples: List[Dict[str, Any]], batch_size: int, state: Dict[str, Any], save: Callable[[], None]) -> None:
    """Classify all examples in batches, saving `state` after every call.

    Batches already in state["done"] are skipped, so a run stopped by an error
    (e.g. the daily quota) resumes where it left off. Risks missing from the
    replies are retried once.
    """
    if state["complete"]:
        return

    def call(batch: List[Dict[str, Any]]) -> None:
        t0 = time.time()
        state["preds"].update(classify_batch(llm, batch))
        state["calls"] += 1
        state["elapsed_s"] += time.time() - t0

    batches = [examples[i : i + batch_size] for i in range(0, len(examples), batch_size)]
    for i, batch in enumerate(batches):
        if i in state["done"]:
            continue
        call(batch)
        state["done"].append(i)
        save()
        _logger.info("Batch classified", batch=f"{i + 1}/{len(batches)}", answered=len(state["preds"]))
    missing = [ex for ex in examples if ex["meta"]["ev_id"] not in state["preds"]]
    if missing:
        _logger.warning("Retrying risks missing from the replies", count=len(missing))
        for i in range(0, len(missing), batch_size):
            call(missing[i : i + batch_size])
            save()
    state["complete"] = True
    save()


def evaluate(examples: List[Dict[str, Any]], preds: Dict[str, Dict[str, str]], seed: int) -> Dict[str, Any]:
    ids = [ex["meta"]["ev_id"] for ex in examples]
    out: Dict[str, Any] = {}
    for ax in AXES:
        y_true = [ex["labels"][ax] for ex in examples]
        y_pred = [preds.get(i, {}).get(ax) for i in ids]
        out[ax] = summarize(y_true, y_pred, LABELS[ax], seed=seed)
    all_true = [tuple(ex["labels"][ax] for ax in AXES) for ex in examples]
    all_pred = [tuple(preds.get(i, {}).get(ax) for ax in AXES) for i in ids]
    out["all_three"] = {"accuracy": accuracy(all_true, all_pred)}
    return out


def majority_reference(train: List[Dict[str, Any]], examples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Predict the most frequent train label for every eval item."""
    out = {}
    for ax in AXES:
        label = Counter(ex["labels"][ax] for ex in train).most_common(1)[0][0]
        y_true = [ex["labels"][ax] for ex in examples]
        y_pred = [label] * len(y_true)
        out[ax] = {"label": label, "accuracy": accuracy(y_true, y_pred), "macro_f1": macro_f1(y_true, y_pred, LABELS[ax])}
    return out


def write_markdown(path: Path, res: Dict[str, Any]) -> None:
    pct = lambda v: f"{v * 100:.1f}"
    ci = lambda c: f"[{pct(c[0])}–{pct(c[1])}]"
    run = res["runs"][0]["metrics"]
    lines = [
        f"# Causal classification — {res['model']['resolved']} baseline",
        "",
        f"Eval: `{res['data']['file']}` ({res['data']['rows']} risks, frozen split). "
        f"Run {res['run']['date']} · batch {res['run']['batch_size']} · repeats {len(res['runs'])} · "
        f"{res['run']['calls']} calls, {res['run']['elapsed_s'] / max(res['run']['calls'], 1):.1f} s per call · "
        f"commit `{res['run']['git_commit']}`.",
        "",
        "| Axis | Accuracy % [95% CI] | Macro-F1 % [95% CI] | Majority class: acc / macro-F1 % |",
        "|---|---|---|---|",
    ]
    for ax in AXES:
        m, b = run[ax], res["majority_reference"][ax]
        lines.append(
            f"| {ax} | {pct(m['accuracy'])} {ci(m['accuracy_ci95'])} | {pct(m['macro_f1'])} {ci(m['macro_f1_ci95'])} "
            f"| {pct(b['accuracy'])} / {pct(b['macro_f1'])} (`{b['label']}`) |"
        )
    lines += ["", f"All three axes correct: {pct(run['all_three']['accuracy'])}%.", "", "Per-class F1 %:", ""]
    for ax in AXES:
        cells = ", ".join(f"{c} {pct(s['f1'])} (n={s['support']})" for c, s in run[ax]["per_class"].items())
        lines.append(f"- **{ax}**: {cells}")
    if res.get("stability"):
        lines += ["", "Agreement between repeated runs %: " + ", ".join(f"{ax} {pct(v)}" for ax, v in res["stability"].items())]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gemini baseline on causal_clf.eval")
    parser.add_argument("--eval", default=str(DATA_DIR / "causal_clf.eval.jsonl"))
    parser.add_argument("--train", default=str(DATA_DIR / "causal_clf.train.jsonl"))
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--repeat", type=int, default=1, help="Independent runs, to measure run-to-run agreement")
    parser.add_argument("--limit", type=int, default=None, help="Only the first N eval items (smoke test)")
    parser.add_argument("--seed", type=int, default=0, help="Bootstrap seed")
    parser.add_argument("--out-dir", default=str(ROOT / "evaluation" / "results"))
    args = parser.parse_args()

    eval_path = Path(args.eval)
    examples = load_jsonl(eval_path)[: args.limit]
    train = load_jsonl(Path(args.train))

    base = get_llm_instance(t=0)
    llm = apply_retry(base.with_structured_output(schema=SCHEMA, method="json_schema"))
    model_name = str(getattr(base, "model", ""))

    data_sha256 = _sha256(eval_path.read_bytes())
    prompt = {
        "system": "agents/causality_analyzer/prompts.py:CAUSALITY_SYSTEM_PROMPT",
        "system_sha256": _sha256(CAUSALITY_SYSTEM_PROMPT.encode()),
        "user_template_sha256": _sha256(USER_PROMPT.encode()),
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = model_name.split("/")[-1] or "model"
    name = f"causal_clf__{slug}" + (f"__limit{args.limit}" if args.limit else "")

    # Predictions are checkpointed after every call; a checkpoint from another
    # setup (model, data, prompts, batching) is not reused.
    ckpt_path = out_dir / f"{name}.checkpoint.json"
    key = {"model": model_name, "data_sha256": data_sha256, "prompt": prompt, "batch_size": args.batch_size, "limit": args.limit}
    ckpt = json.loads(ckpt_path.read_text(encoding="utf-8")) if ckpt_path.exists() else None
    if ckpt is not None and ckpt["key"] != key:
        _logger.warning("Ignoring a checkpoint from a different setup", path=str(ckpt_path))
        ckpt = None
    ckpt = ckpt or {"key": key, "runs": []}
    ckpt["runs"] += [new_run_state() for _ in range(args.repeat - len(ckpt["runs"]))]
    save = lambda: ckpt_path.write_text(json.dumps(ckpt, ensure_ascii=False), encoding="utf-8")
    save()

    try:
        for r, state in enumerate(ckpt["runs"][: args.repeat], 1):
            if not state["complete"]:
                _logger.info("Run start", run=r, items=len(examples), model=model_name, batches_done=len(state["done"]))
            predict(llm, examples, args.batch_size, state, save)
    except Exception:
        _logger.error("Run interrupted: progress saved, rerun the same command to resume", checkpoint=str(ckpt_path))
        raise
    runs = [
        {
            "calls": s["calls"],
            "elapsed_s": round(s["elapsed_s"], 1),
            "metrics": evaluate(examples, s["preds"], args.seed),
            "predictions": s["preds"],
        }
        for s in ckpt["runs"][: args.repeat]
    ]

    stability = None
    if len(runs) > 1:
        ids = [ex["meta"]["ev_id"] for ex in examples]
        first = runs[0]["predictions"]
        stability = {
            ax: sum(first.get(i, {}).get(ax) == run["predictions"].get(i, {}).get(ax) for run in runs[1:] for i in ids)
            / (len(ids) * (len(runs) - 1))
            for ax in AXES
        }

    manifest_path = eval_path.parent / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    res = {
        "task": "causal_clf",
        "model": {"provider": "google", "env_GEMINI_MODEL": os.getenv("GEMINI_MODEL"), "resolved": model_name, "temperature": 0},
        "run": {
            "date": date,
            "batch_size": args.batch_size,
            "calls": sum(r["calls"] for r in runs),
            "elapsed_s": round(sum(r["elapsed_s"] for r in runs), 1),
            "git_commit": _git_commit(),
        },
        "data": {
            "file": str(eval_path.relative_to(ROOT)) if eval_path.is_relative_to(ROOT) else str(eval_path),
            "sha256": data_sha256,
            "rows": len(examples),
            "extraction_script_sha256": manifest.get("script", {}).get("sha256"),
        },
        "prompt": prompt,
        "majority_reference": majority_reference(train, examples),
        "stability": stability,
        "runs": runs,
    }

    stem = f"{name}__{date}"
    (out_dir / f"{stem}.json").write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(out_dir / f"{stem}.md", res)
    ckpt_path.unlink()
    _logger.info("Results written", path=str(out_dir / f"{stem}.json"))
    print((out_dir / f"{stem}.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
