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

Usage (from the project root):
    python -m evaluation.area_testset generate [--languages en it] [--profiles expert intermediate beginner]
    python -m evaluation.area_testset collect
"""

import argparse
import json
import tempfile
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
from utils.utils import create_logger

_logger = create_logger("area_testset")

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "evaluation" / "area_testset"
RUNS_DIR = OUT_DIR / "runs"
EXAMPLE_RUN_ID = "23d095a19c9c45c89af5c66b5ffcea63"  # example run tracked in files/
AXES = ("entity", "intent", "timing")


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
            run = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"language": language, "profile": profile}
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


def main() -> None:
    parser = argparse.ArgumentParser(description="AREA in-distribution test set")
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate", help="Generate answers and analyses (calls the LLM)")
    gen.add_argument("--languages", nargs="+", default=["en", "it"], choices=["en", "it"])
    gen.add_argument("--profiles", nargs="+", default=list(DEFAULT_PROFILE_TEMPS), choices=list(DEFAULT_PROFILE_TEMPS))
    sub.add_parser("collect", help="Flatten the runs into risks.jsonl")
    args = parser.parse_args()
    if args.command == "generate":
        generate(args.languages, args.profiles)
    else:
        collect()


if __name__ == "__main__":
    main()
