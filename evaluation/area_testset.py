"""
In-distribution test set for the causal classification: risks written by AREA itself.

The MIT eval split holds risk descriptions from papers, while in AREA the causal labels
are assigned to the risks that the domain analyzer derives from questionnaire answers.

- `generate` answers the questionnaire with each simulated profile (questionnaire
  generator) and language, then runs the domain and causality analyzers on the answers.
  The heuristic and report steps are skipped: they add no causal labels. Each run is
  stored in evaluation/area_testset/runs/<language>_<profile>.json (answers and both
  analyses); rerunning the command skips the steps already stored.
- `collect` flattens those runs, plus the example run tracked in files/, into
  evaluation/area_testset/risks.jsonl: one row per risk with its text (title +
  explanation) and the causal labels assigned by the pipeline (Gemini). Gold labels are
  kept apart, in labels.jsonl.
- `evaluate` scores the pipeline labels against the gold labels (no LLM calls), overall
  and by language and source, and writes the results to evaluation/results/.

Usage (from the project root):
    python -m evaluation.area_testset generate [--languages en it] [--profiles expert intermediate beginner]
    python -m evaluation.area_testset collect
    python -m evaluation.area_testset evaluate
"""

import argparse
import json
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from agents.causality_analyzer.causality_risk_analyzer_agent import CAUSALITY_DIR
from agents.domain_analyzer.domain_risk_analyzer_agent import DOMAIN_DIR
from agents.orchestrator import causality_step, domain_step
from agents.questionnaire_generator.question_generator_agent import (
    DEFAULT_PROFILE_TEMPS,
    generate_responses,
    load_questions,
    save_responses_with_metadata,
)
from evaluation.causal_baseline import AXES, DATA_DIR, LABELS, _git_commit, _sha256, load_jsonl, majority_reference
from evaluation.metrics import accuracy, macro_f1, summarize
from utils.utils import create_logger, get_llm_instance

_logger = create_logger("area_testset")

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "evaluation" / "area_testset"
RUNS_DIR = OUT_DIR / "runs"
EXAMPLE_RUN_ID = "23d095a19c9c45c89af5c66b5ffcea63"  # example run tracked in files/
RESULTS_DIR = ROOT / "evaluation" / "results"


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _answer(language: str, profile: str) -> Dict[str, Any]:
    """Questionnaire generator: one LLM call; returns the answers file content."""
    questions = load_questions(str(ROOT / "files" / f"questions_{language}.json"))
    response = generate_responses(questions, profile, language)
    _, answers_file = save_responses_with_metadata(response, profile, language, "files/answers/")
    answers_path = Path(answers_file)
    answers = json.loads(answers_path.read_text(encoding="utf-8"))
    answers_path.unlink()  # kept in the run file instead
    return answers


def _analyze(answers: Dict[str, Any]) -> Dict[str, Any]:
    """Domain + causality analyzers (two LLM calls) as in the pipeline; returns both outputs."""
    run_id = answers["metadata"]["run_id"]
    with tempfile.TemporaryDirectory() as tmp:
        input_file = Path(tmp) / f"answers_{run_id}.json"
        _write_json(input_file, answers)
        state = {
            "input_file": str(input_file),
            "domain_state": {"metadata": {}, "questionnaire": {}, "analysis": {}, "messages": [], "errors": []},
        }
        causality_step(domain_step(state))
    out = {}
    for key, path in (
        ("domain", DOMAIN_DIR / f"domain_analysis_{run_id}.json"),
        ("causality", CAUSALITY_DIR / f"causality_analysis_{run_id}.json"),
    ):
        out[key] = json.loads(path.read_text(encoding="utf-8"))
        path.unlink()
    return out


def generate(languages: List[str], profiles: List[str]) -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    for language in languages:
        for profile in profiles:
            path = RUNS_DIR / f"{language}_{profile}.json"
            if path.exists():
                run = json.loads(path.read_text(encoding="utf-8"))
            else:
                run = {"language": language, "profile": profile, "model": str(get_llm_instance().model)}
            if "causality" in run:
                _logger.info("Run already complete", run=path.name)
                continue
            if "answers" not in run:
                _logger.info("Answering the questionnaire", language=language, profile=profile)
                run["answers"] = _answer(language, profile)
                _write_json(path, run)
            _logger.info("Domain and causality analysis", run=path.name)
            run.update(_analyze(run["answers"]))
            _write_json(path, run)
            risks = sum(len(block["risks"]) for block in run["causality"]["analysis"].values())
            _logger.info("Run complete", run=path.name, risks=risks)


def collect() -> None:
    example = {
        "profile": None,
        "source": "example",
        "causality": json.loads((CAUSALITY_DIR / f"causality_analysis_{EXAMPLE_RUN_ID}.json").read_text(encoding="utf-8")),
    }
    runs = [example] + [
        {**json.loads(p.read_text(encoding="utf-8")), "source": "generated"} for p in sorted(RUNS_DIR.glob("*.json"))
    ]
    rows = []
    for run in runs:
        if "causality" not in run:
            continue
        meta = run["causality"]["metadata"]
        for subdomain, block in run["causality"]["analysis"].items():
            for i, risk in enumerate(block["risks"], 1):
                rows.append(
                    {
                        "id": f"{meta['run_id'][:8]}-{subdomain}-{i}",
                        "run_id": meta["run_id"],
                        "source": run["source"],
                        "language": meta["language"],
                        "profile": run["profile"],
                        "model": run.get("model"),
                        "subdomain": subdomain,
                        "title": risk["title"],
                        "text": risk["explanation"],
                        "severity": risk.get("severity"),
                        "pipeline": {ax: risk["causality"][ax]["value"] for ax in AXES},
                    }
                )
    with open(OUT_DIR / "risks.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    _logger.info("Risks collected", rows=len(rows), path=str(OUT_DIR / "risks.jsonl"))


def _scores(ids: List[str], risks: Dict[str, Any], gold: Dict[str, Any], seed: int) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for ax in AXES:
        y_true = [gold[i][ax] for i in ids]
        y_pred = [risks[i]["pipeline"][ax] for i in ids]
        out[ax] = summarize(y_true, y_pred, LABELS[ax], seed=seed)
    out["all_three"] = {
        "accuracy": accuracy(
            [tuple(gold[i][ax] for ax in AXES) for i in ids], [tuple(risks[i]["pipeline"][ax] for ax in AXES) for i in ids]
        )
    }
    return out


def evaluate(seed: int = 0) -> None:
    """Pipeline labels (risks.jsonl) against the reviewed gold labels (labels.jsonl)."""
    risks = {r["id"]: r for r in load_jsonl(OUT_DIR / "risks.jsonl")}
    gold = {g["id"]: g for g in load_jsonl(OUT_DIR / "labels.jsonl")}
    ids = [i for i in risks if i in gold]
    subsets = {f"{key}={value}": [i for i in ids if risks[i][key] == value] for key in ("language", "source") for value in sorted({risks[i][key] for i in ids})}
    examples = [{"labels": {ax: gold[i][ax] for ax in AXES}} for i in ids]
    models = sorted({risks[i].get("model") or "unknown" for i in ids})
    res = {
        "task": "causal_clf_area",
        "predictions": "causal labels assigned by the AREA pipeline (causality agent)",
        "models": {src: sorted({risks[i].get("model") or "unknown" for i in sel}) for src, sel in subsets.items() if src.startswith("source=")},
        "run": {"date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "git_commit": _git_commit()},
        "data": {
            "risks": "evaluation/area_testset/risks.jsonl",
            "risks_sha256": _sha256((OUT_DIR / "risks.jsonl").read_bytes()),
            "labels": "evaluation/area_testset/labels.jsonl",
            "labels_sha256": _sha256((OUT_DIR / "labels.jsonl").read_bytes()),
            "rows": len(ids),
        },
        "gold_distribution": {ax: dict(Counter(gold[i][ax] for i in ids)) for ax in AXES},
        "review": {ax: sum(ax in gold[i].get("changed", []) for i in ids) / len(ids) for ax in AXES},
        "harmonized": {ax: sum(ax in gold[i].get("harmonized", {}) for i in ids) for ax in AXES},
        "majority_reference": majority_reference(load_jsonl(DATA_DIR / "causal_clf.train.jsonl"), examples),
        "metrics": _scores(ids, risks, gold, seed),
        "subsets": {
            name: {
                "n": len(sel),
                **{
                    ax: {
                        "accuracy": accuracy([gold[i][ax] for i in sel], [risks[i]["pipeline"][ax] for i in sel]),
                        "macro_f1": macro_f1([gold[i][ax] for i in sel], [risks[i]["pipeline"][ax] for i in sel], LABELS[ax]),
                    }
                    for ax in AXES
                },
            }
            for name, sel in subsets.items()
        },
    }
    slug = models[0] if len(models) == 1 else "pipeline"
    stem = f"area_testset__{slug}__{res['run']['date']}"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    _write_json(RESULTS_DIR / f"{stem}.json", res)
    _write_markdown(RESULTS_DIR / f"{stem}.md", res)
    print((RESULTS_DIR / f"{stem}.md").read_text(encoding="utf-8"))


def _write_markdown(path: Path, res: Dict[str, Any]) -> None:
    pct = lambda v: f"{v * 100:.1f}"
    ci = lambda c: f"[{pct(c[0])}–{pct(c[1])}]"
    m = res["metrics"]
    langs = {k.split("=")[1]: v["n"] for k, v in res["subsets"].items() if k.startswith("language=")}
    models = "; ".join(f"{k.split('=')[1]}: {', '.join(v)}" for k, v in res["models"].items())
    lines = [
        "# Causal classification on AREA risks — pipeline labels vs gold",
        "",
        f"Test set: `{res['data']['risks']}` ({res['data']['rows']} risks: "
        + ", ".join(f"{n} {lang.upper()}" for lang, n in langs.items())
        + f"); gold: `{res['data']['labels']}` (reviewed by hand, see LABELING.md). "
        f"Pipeline model by source: {models}. Run {res['run']['date']} · commit `{res['run']['git_commit']}`.",
        "",
        "| Axis | Accuracy % [95% CI] | Macro-F1 % [95% CI] | Majority class (MIT train): acc / macro-F1 % |",
        "|---|---|---|---|",
    ]
    for ax in AXES:
        a, b = m[ax], res["majority_reference"][ax]
        lines.append(
            f"| {ax} | {pct(a['accuracy'])} {ci(a['accuracy_ci95'])} | {pct(a['macro_f1'])} {ci(a['macro_f1_ci95'])} "
            f"| {pct(b['accuracy'])} / {pct(b['macro_f1'])} (`{b['label']}`) |"
        )
    lines += ["", f"All three axes correct: {pct(m['all_three']['accuracy'])}%.", "", "Per-class F1 % (gold support):", ""]
    for ax in AXES:
        lines.append(f"- **{ax}**: " + ", ".join(f"{c} {pct(s['f1'])} (n={s['support']})" for c, s in m[ax]["per_class"].items()))
    lines += ["", "| Subset | n | " + " | ".join(f"{ax} acc / macro-F1 %" for ax in AXES) + " |", "|---|---|" + "---|" * len(AXES)]
    for name, sub in res["subsets"].items():
        lines.append(f"| {name} | {sub['n']} | " + " | ".join(f"{pct(sub[ax]['accuracy'])} / {pct(sub[ax]['macro_f1'])}" for ax in AXES) + " |")
    lines += [
        "",
        "Gold labels that differ from the proposals they were reviewed from: "
        + ", ".join(f"{ax} {pct(v)}%" for ax, v in res["review"].items())
        + ". Harmonized after the review (near-duplicate risks, see LABELING.md): "
        + ", ".join(f"{ax} {n}" for ax, n in res["harmonized"].items())
        + ".",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="AREA in-distribution test set")
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate", help="Generate answers and analyses (calls the LLM)")
    gen.add_argument("--languages", nargs="+", default=["en", "it"], choices=["en", "it"])
    gen.add_argument("--profiles", nargs="+", default=list(DEFAULT_PROFILE_TEMPS), choices=list(DEFAULT_PROFILE_TEMPS))
    sub.add_parser("collect", help="Flatten the runs into risks.jsonl")
    sub.add_parser("evaluate", help="Score the pipeline labels against labels.jsonl (no LLM calls)")
    args = parser.parse_args()
    if args.command == "generate":
        generate(args.languages, args.profiles)
    elif args.command == "collect":
        collect()
    else:
        evaluate()


if __name__ == "__main__":
    main()
