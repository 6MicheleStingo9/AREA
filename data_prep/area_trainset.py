"""
Training risks written by Kindynos itself, to fine-tune Laya on how Kindynos frames its risks.

The causal labels of the Kindynos test set follow evaluation/area_testset/LABELING.md, whose
conventions (e.g. a harm of the system in use is post-deployment) the MIT training data do not
teach. These runs add risks written by Kindynos itself to the training data. Unlike the test set, where the
questionnaire generator picks the AI system, each run describes a given one: 28 systems, half in
English and half in Italian, none of the kinds in the test set, with the three simulated profiles
in rotation. A run is the simulated questionnaire and the domain analysis, one LLM call each (the
questionnaire is asked again, up to three times, when its JSON comes back malformed); the
causality step is skipped, since the labels come from the annotation protocol described in
files/data/area_trainset/README.md.

- `generate` works through the planned runs in order, storing each step in
  files/data/area_trainset/runs/<run>.json; rerunning skips what is stored. On the Gemini free
  tier (20 requests per day per project) it stops at an exhausted quota with exit code 3: rerun
  it the next day, or with another project's key in GOOGLE_API_KEY.
- `collect` flattens the complete runs into files/data/area_trainset/risks.jsonl, one row per risk.
- `batches`, `disagreements`, `merge` support the labelling protocol (two blind annotators and an
  adjudicator, see the README): batch files of unlabelled risks, the agreement of the annotators with
  the risks they disagree on, and labels.jsonl. With `--set quality` they work on a random sample of
  the test set instead (`quality-sample`), kept in evaluation/area_testset/annotator_check/, which
  `quality-score` compares with the reviewed gold labels.

Usage (from the project root):
    python -m data_prep.area_trainset generate [--max-runs N]
    python -m data_prep.area_trainset collect
    python -m data_prep.area_trainset batches [--runs-per-batch 5] [--set train|quality]
    python -m data_prep.area_trainset disagreements [--set train|quality]
    python -m data_prep.area_trainset merge [--set train|quality]
    python -m data_prep.area_trainset quality-sample [--n 60] [--seed 0]
    python -m data_prep.area_trainset quality-score
"""

import argparse
import json
import random
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from agents.domain_analyzer.domain_risk_analyzer_agent import DOMAIN_DIR
from agents.orchestrator import domain_step
from evaluation.area_testset import _answer, _write_json
from evaluation.causal_baseline import AXES, LABELS
from evaluation.metrics import accuracy, macro_f1
from utils.paths import DATA, ROOT
from utils.utils import create_logger, get_llm_instance

_logger = create_logger("area_trainset")

OUT_DIR = DATA / "area_trainset"
RUNS_DIR = OUT_DIR / "runs"
TEST_DIR = ROOT / "evaluation" / "area_testset"
# Where each labelling set keeps risks.jsonl, annotations/ and labels.jsonl
SETS = {"train": OUT_DIR, "quality": TEST_DIR / "annotator_check"}
RISK_FIELDS = ("id", "language", "subdomain", "title", "text")
PROFILES = ("expert", "intermediate", "beginner")
QUOTA_EXIT = 3
ANSWER_ATTEMPTS = 3

# (language, AI system to describe). The languages alternate, so a partial generation stays balanced.
SYSTEMS = [
    ("en", "a CV screening and candidate ranking system used by a recruitment agency"),
    ("it", "un assistente che revisiona i contratti per uno studio legale"),
    ("en", "a clinical decision support system for triage in a hospital emergency department"),
    ("it", "un sistema di gestione adattiva dei semafori per il traffico di una città"),
    ("en", "a credit scoring model for consumer loans at a retail bank"),
    ("it", "un sistema che stima i prezzi degli immobili per un portale di annunci"),
    ("en", "warehouse robots that pick and pack customer orders"),
    ("it", "un chatbot di supporto psicologico per gli studenti di un'università"),
    ("en", "a content moderation system for a social media platform"),
    ("it", "un sistema di previsione della domanda elettrica per un distributore di energia"),
    ("en", "facial recognition for access control in an office building"),
    ("it", "un assistente vocale domestico che controlla la casa intelligente"),
    ("en", "an adaptive learning platform for secondary-school students"),
    ("it", "un sistema di videosorveglianza che analizza i comportamenti in una stazione ferroviaria"),
    ("en", "a predictive maintenance system for wind turbines"),
    ("it", "un sistema di traduzione automatica dei documenti sanitari per i pazienti stranieri"),
    ("en", "real-time fraud detection for card payments"),
    ("it", "un sistema che pianifica i turni del personale di un ospedale"),
    ("en", "a driver-assistance system (lane keeping and emergency braking) for passenger cars"),
    ("it", "un assistente alla programmazione basato su LLM per sviluppatori software"),
    ("en", "a generative AI copywriter for e-commerce product pages"),
    ("it", "un sistema di correzione automatica dei compiti scritti in una scuola superiore"),
    ("en", "an eligibility assessment system for unemployment benefits at a public agency"),
    ("it", "un drone agricolo che rileva le malattie delle colture"),
    ("en", "AI-assisted triage of chest X-rays in a radiology department"),
    ("it", "un sistema che assegna la priorità alle chiamate del numero di emergenza 112"),
    ("en", "an automated assessment system for car insurance claims"),
    ("it", "un agente autonomo che gestisce gli acquisti di un'azienda manifatturiera"),
]


def planned_runs() -> List[Dict[str, str]]:
    """The runs in generation order: t01, t02, ... with their language, system and profile."""
    return [
        {"run": f"t{k:02d}", "language": language, "system": system, "profile": PROFILES[(k - 1) % len(PROFILES)]}
        for k, (language, system) in enumerate(SYSTEMS, 1)
    ]


def is_quota_error(exc: BaseException) -> bool:
    """Whether an LLM failure is Gemini's exhausted quota (the retries are already spent)."""
    text = f"{type(exc).__name__}: {exc}"
    return "RESOURCE_EXHAUSTED" in text or "ResourceExhausted" in text or ("429" in text and "quota" in text.lower())


def _domain(answers: Dict[str, Any]) -> Dict[str, Any]:
    """Domain analyzer on the answers (one LLM call); returns its output."""
    run_id = answers["metadata"]["run_id"]
    with tempfile.TemporaryDirectory() as tmp:
        input_file = Path(tmp) / f"answers_{run_id}.json"
        _write_json(input_file, answers)
        state = {
            "input_file": str(input_file),
            "domain_state": {"metadata": {}, "questionnaire": {}, "analysis": {}, "messages": [], "errors": []},
        }
        domain_step(state)
    path = DOMAIN_DIR / f"domain_analysis_{run_id}.json"
    out = json.loads(path.read_text(encoding="utf-8"))
    path.unlink()
    return out


def _answers(plan: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """The simulated questionnaire, asked again (up to ANSWER_ATTEMPTS calls) when the model returns
    malformed JSON despite JSON mode; None if it never parses, so the run is left for a later rerun."""
    for attempt in range(1, ANSWER_ATTEMPTS + 1):
        _logger.info("Answering the questionnaire", run=plan["run"], language=plan["language"], profile=plan["profile"], attempt=attempt)
        try:
            return _answer(plan["language"], plan["profile"], plan["system"])
        except json.JSONDecodeError as exc:
            _logger.warning("Malformed questionnaire JSON", run=plan["run"], attempt=attempt, error=str(exc))
    _logger.warning("Questionnaire still malformed: run left for a later rerun", run=plan["run"])
    return None


def generate(max_runs: Optional[int] = None) -> int:
    """Run the missing steps; returns 0 when every planned run is complete, QUOTA_EXIT on an exhausted quota."""
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    started = 0
    for plan in planned_runs():
        path = RUNS_DIR / f"{plan['run']}.json"
        run = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {**plan, "model": str(get_llm_instance().model)}
        if "domain" in run:
            continue
        if max_runs is not None and started >= max_runs:
            break
        started += 1
        try:
            if "answers" not in run:
                answers = _answers(plan)
                if answers is None:
                    continue
                run["answers"] = answers
                _write_json(path, run)
            _logger.info("Domain analysis", run=plan["run"])
            run["domain"] = _domain(run["answers"])
            _write_json(path, run)
        except Exception as exc:  # noqa: BLE001 - every failure stops the generation; the stored steps stay
            if is_quota_error(exc):
                _logger.warning("Quota exhausted: rerun tomorrow or with another project's key", run=plan["run"])
                return QUOTA_EXIT
            raise
        risks = sum(len(block["risks"]) for block in run["domain"]["analysis"].values())
        _logger.info("Run complete", run=plan["run"], risks=risks)
    done = sum("domain" in json.loads(p.read_text(encoding="utf-8")) for p in RUNS_DIR.glob("t*.json"))
    _logger.info("Runs complete", done=done, planned=len(SYSTEMS))
    return 0


def risk_rows(run: Dict[str, Any]) -> List[Dict[str, Any]]:
    """One row per risk of a complete run, without labels."""
    rows = []
    for subdomain, block in run["domain"]["analysis"].items():
        for i, risk in enumerate(block["risks"], 1):
            rows.append(
                {
                    "id": f"{run['run']}-{subdomain}-{i}",
                    "run": run["run"],
                    "run_id": run["answers"]["metadata"]["run_id"],
                    "language": run["language"],
                    "profile": run["profile"],
                    "system": run["system"],
                    "model": run.get("model"),
                    "subdomain": subdomain,
                    "title": risk["title"],
                    "text": risk["explanation"],
                    "severity": risk.get("severity"),
                }
            )
    return rows


def collect() -> None:
    runs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(RUNS_DIR.glob("t*.json"))]
    rows = [row for run in runs if "domain" in run for row in risk_rows(run)]
    with open(OUT_DIR / "risks.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    _logger.info("Risks collected", runs=sum("domain" in r for r in runs), rows=len(rows), path=str(OUT_DIR / "risks.jsonl"))


def _read(path: Path) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def annotations(base: Path, who: str) -> Dict[str, Dict[str, Any]]:
    """The rows of every file in annotations/<who>/, by risk id (who: a, b or adjudication)."""
    return {r["id"]: r for p in sorted((base / "annotations" / who).glob("*.jsonl")) for r in _read(p)}


def kappa(a: Sequence[str], b: Sequence[str]) -> float:
    """Cohen's kappa of two annotators' labels on the same items."""
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    expected = sum((list(a).count(c) / n) * (list(b).count(c) / n) for c in set(a) | set(b))
    return (observed - expected) / (1 - expected) if expected < 1 else 1.0


def batches(base: Path, runs_per_batch: int) -> None:
    """Batch files, for the annotators, of the risks not in a batch yet: ids and texts, no labels."""
    out = base / "annotations" / "batches"
    batched = {r["id"] for p in out.glob("*.jsonl") for r in _read(p)}
    rows = [r for r in _read(base / "risks.jsonl") if r["id"] not in batched]
    runs = list(dict.fromkeys(r.get("run", "sample") for r in rows))
    for k in range(0, len(runs), runs_per_batch):
        chunk = runs[k : k + runs_per_batch]
        name = chunk[0] if len(chunk) == 1 else f"{chunk[0]}-{chunk[-1]}"
        batch = [{f: r[f] for f in RISK_FIELDS} for r in rows if r.get("run", "sample") in chunk]
        _write_jsonl(out / f"{name}.jsonl", batch)
        print(f"{out / name}.jsonl: {len(batch)} risks")


def disagreements(base: Path) -> None:
    """Agreement of annotators A and B per axis; annotations/disputed.jsonl lists the risks they
    disagree on and the adjudicator has not settled yet, with both labels and notes."""
    risks = {r["id"]: r for r in _read(base / "risks.jsonl")}
    a, b = annotations(base, "a"), annotations(base, "b")
    for who, ann in (("A", a), ("B", b)):
        bad = [i for i, r in ann.items() if i not in risks or any(r.get(ax) not in LABELS[ax] for ax in AXES)]
        if bad:
            print(f"annotator {who}: {len(bad)} rows with an unknown id or value, e.g. {bad[:3]}")
    both = [i for i in risks if i in a and i in b]
    print(f"{len(both)} of {len(risks)} risks labelled by both annotators")
    for ax in AXES:
        x, y = [a[i][ax] for i in both], [b[i][ax] for i in both]
        if both:
            print(f"  {ax:7} agreement {accuracy(x, y) * 100:5.1f}%, Cohen's kappa {kappa(x, y):.2f}")
    settled = annotations(base, "adjudication")
    disputed = []
    for i in both:
        axes = [ax for ax in AXES if a[i][ax] != b[i][ax] and ax not in settled.get(i, {}).get("final", {})]
        if axes:
            disputed.append({
                **{f: risks[i][f] for f in RISK_FIELDS},
                "disputed": axes,
                "labels": {"A": {ax: a[i][ax] for ax in AXES}, "B": {ax: b[i][ax] for ax in AXES}},
                "notes": {"A": a[i].get("note", ""), "B": b[i].get("note", "")},
            })
    _write_jsonl(base / "annotations" / "disputed.jsonl", disputed)
    print(f"{len(disputed)} risks to adjudicate in {base / 'annotations' / 'disputed.jsonl'}")


def merge(base: Path) -> None:
    """labels.jsonl: per axis the value both annotators gave, or else the adjudicator's, with its source."""
    a, b, settled = annotations(base, "a"), annotations(base, "b"), annotations(base, "adjudication")
    rows, pending = [], 0
    for r in _read(base / "risks.jsonl"):
        i = r["id"]
        if i not in a or i not in b:
            continue
        label, source = {}, {}
        for ax in AXES:
            if a[i][ax] == b[i][ax]:
                label[ax], source[ax] = a[i][ax], "agreed"
            elif ax in settled.get(i, {}).get("final", {}):
                label[ax], source[ax] = settled[i]["final"][ax], "adjudicated"
        if len(label) < len(AXES):
            pending += 1
            continue
        rows.append({"id": i, **label, "source": source})
    _write_jsonl(base / "labels.jsonl", rows)
    adjudicated = sum("adjudicated" in r["source"].values() for r in rows)
    print(f"{base / 'labels.jsonl'}: {len(rows)} risks ({adjudicated} with an adjudicated axis); {pending} still to adjudicate")


def quality_sample(n: int, seed: int) -> None:
    """A random sample of the test-set risks, texts only, for the annotator check."""
    rows = random.Random(seed).sample(_read(TEST_DIR / "risks.jsonl"), n)
    _write_jsonl(SETS["quality"] / "risks.jsonl", [{f: r[f] for f in RISK_FIELDS} for r in rows])
    print(f"{SETS['quality'] / 'risks.jsonl'}: {n} risks")


def quality_score() -> None:
    """The labels of the protocol on the test sample against the reviewed gold labels."""
    base = SETS["quality"]
    gold = {g["id"]: g for g in _read(TEST_DIR / "labels.jsonl")}
    final = {r["id"]: r for r in _read(base / "labels.jsonl")}
    first = annotations(base, "a")
    print(f"{len(final)} risks of the test set, accuracy / macro-F1 % against the gold labels")
    for name, labels in (("protocol (A, B, adjudicator)", final), ("annotator A alone", first)):
        ids = [i for i in labels if i in gold]
        cells = []
        for ax in AXES:
            y, p = [gold[i][ax] for i in ids], [labels[i][ax] for i in ids]
            cells.append(f"{ax} {accuracy(y, p) * 100:.1f} / {macro_f1(y, p, LABELS[ax]) * 100:.1f}")
        print(f"  {name:28} " + " | ".join(cells))


def main() -> None:
    parser = argparse.ArgumentParser(description="Kindynos risks for the Laya training data")
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate", help="Simulated questionnaires + domain analyses (calls the LLM)")
    gen.add_argument("--max-runs", type=int, default=None, help="Start at most N runs")
    sub.add_parser("collect", help="One row per risk in files/data/area_trainset/risks.jsonl")
    for name, help_text in (("batches", "Batch files of unlabelled risks for the annotators"),
                            ("disagreements", "Agreement of the annotators and the risks to adjudicate"),
                            ("merge", "Final labels in labels.jsonl")):
        cmd = sub.add_parser(name, help=help_text)
        cmd.add_argument("--set", choices=list(SETS), default="train", help="train: the Kindynos training risks; quality: the test sample")
        if name == "batches":
            cmd.add_argument("--runs-per-batch", type=int, default=5)
    qs = sub.add_parser("quality-sample", help="Random test-set risks for the annotator check")
    qs.add_argument("--n", type=int, default=60)
    qs.add_argument("--seed", type=int, default=0)
    sub.add_parser("quality-score", help="Protocol labels on the test sample against the gold labels")
    args = parser.parse_args()
    if args.command == "generate":
        sys.exit(generate(args.max_runs))
    if args.command == "collect":
        collect()
    elif args.command == "batches":
        batches(SETS[args.set], args.runs_per_batch)
    elif args.command == "disagreements":
        disagreements(SETS[args.set])
    elif args.command == "merge":
        merge(SETS[args.set])
    elif args.command == "quality-sample":
        quality_sample(args.n, args.seed)
    else:
        quality_score()


if __name__ == "__main__":
    main()
