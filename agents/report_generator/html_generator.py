"""
The HTML report of a run: the report app (frontend/report), built once by `npm run build` in
frontend/, with the data of the run (report_data.py) written into a copy of it.

The build is a single HTML file with its code, styles, fonts and logo inside: the report opens
offline, from any folder. The report of a past run can be made again, for a new version of the app,
from its saved files and without asking Gemini again:

    python -m agents.report_generator.html_generator <run_id> [--answers <answers file>]
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.report_generator.report_data import language_of, report_data
from quiz.logic import load_questions
from utils.paths import ANALYSIS, ANSWERS, REPORT_BUILD, REPORTS

REPORT_DIR = REPORTS
TEMPLATE = REPORT_BUILD / "index.html"
# The text of <script id="report-data"> in frontend/report/index.html: where the data go
PLACEHOLDER = "__KINDYNOS_REPORT_DATA__"
BUILD_COMMAND = "cd frontend && npm ci && npm run build"


class ReportTemplateMissing(RuntimeError):
    """The report app is not built, or its build has no place for the data."""


def template() -> str:
    """The built report app, with its place for the data."""
    try:
        html = TEMPLATE.read_text(encoding="utf-8")
    except OSError:
        raise ReportTemplateMissing(f"The report app is not built ({TEMPLATE} is missing): run `{BUILD_COMMAND}`") from None
    if html.count(PLACEHOLDER) != 1:
        raise ReportTemplateMissing(f"{TEMPLATE} has no place for the data of the report: build it again with `{BUILD_COMMAND}`")
    return html


def script_json(data: Any) -> str:
    """The data as JSON that can sit in <script type="application/json">: without "<", no "</script>"
    or "<!--" in a text ends the element early. JSON.parse reads the escapes back as they were."""
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def render(data: Dict[str, Any]) -> str:
    """The report app with the data in it."""
    return template().replace(PLACEHOLDER, script_json(data), 1)


def _questions(metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The questions of the run, for the text of the follow-ups; none if they cannot be read."""
    try:
        return load_questions(language_of(metadata))
    except (OSError, ValueError, KeyError):
        return []


def generate_html_report(
    metadata: Dict[str, Any],
    heuristic: Dict[str, Any],
    analysis: Dict[str, Any],
    questionnaire: Optional[Dict[str, Any]] = None,
    created: Optional[str] = None,
) -> Path:
    """
    Write the HTML report of a run in files/reports/.

    Args:
        metadata: The metadata of the run, with its run_id.
        heuristic: The output of the expert rules.
        analysis: The risks by subdomain, with their causality.
        questionnaire: The answers of the run, shown next to the risks.
        created: When the report was made (ISO 8601); now, by default.

    Returns:
        The path of the report: files/reports/ai_risk_report_<run_id>.html.
    """
    run_id = metadata.get("run_id")
    if not run_id:
        raise RuntimeError("Missing run_id in metadata; report generation requires run_id produced by domain analyzer")
    data = report_data(metadata, heuristic, analysis, questionnaire, _questions(metadata), created)
    html = render(data)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"ai_risk_report_{run_id}.html"
    path.write_text(html, encoding="utf-8")
    return path


def _read(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _when(timestamp: Any) -> Optional[str]:
    """A timestamp of the pipeline (20251227_160656) in ISO 8601."""
    try:
        return datetime.strptime(str(timestamp), "%Y%m%d_%H%M%S").isoformat()
    except ValueError:
        return None


def saved_run(run_id: str, answers: Optional[Path] = None) -> Dict[str, Any]:
    """
    What the report of a past run is made of, from its saved files: the analyses, the answers, and
    the summary that Gemini wrote for it.

    Args:
        run_id: The run.
        answers: Its answers file, if not files/answers/answers_<run_id>.json.

    Returns:
        The arguments of generate_html_report.
    """
    saved = _read(ANALYSIS / "heuristic" / f"heuristic_analysis_{run_id}.json")
    metadata = dict(saved.get("metadata") or {})
    created = None
    report_metadata = REPORTS / f"report_metadata_{run_id}.json"
    if report_metadata.exists():
        written = _read(report_metadata)
        metadata.update(written)
        created = _when(written.get("timestamp"))
    answers = answers or ANSWERS / f"answers_{run_id}.json"
    questionnaire = _read(answers) if answers.exists() else {}
    metadata.setdefault("system_name", (questionnaire.get("metadata") or {}).get("system_name"))
    metadata["run_id"] = run_id
    return {
        "metadata": metadata,
        "heuristic": saved.get("heuristic") or {},
        "analysis": saved.get("analysis") or {},
        "questionnaire": questionnaire,
        "created": created,
    }


def rebuild(run_id: str, answers: Optional[Path] = None) -> Path:
    """The report of a past run, made again from its saved files: nothing is sent to Gemini."""
    return generate_html_report(**saved_run(run_id, answers))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make the HTML report of a past run again, from its saved files.")
    parser.add_argument("run_id", help="the id of the run, as in files/analysis/heuristic/heuristic_analysis_<run_id>.json")
    parser.add_argument("--answers", type=Path, help="its answers file, if not files/answers/answers_<run_id>.json")
    parser.add_argument("--data", action="store_true", help="print the data of the report instead, as JSON")
    args = parser.parse_args()
    try:
        if args.data:
            run = saved_run(args.run_id, args.answers)
            data = report_data(
                run["metadata"], run["heuristic"], run["analysis"], run["questionnaire"],
                _questions(run["metadata"]), run["created"],
            )
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(rebuild(args.run_id, args.answers))
    except (OSError, ReportTemplateMissing) as e:
        sys.exit(str(e))
