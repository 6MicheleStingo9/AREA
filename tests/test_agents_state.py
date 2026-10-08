"""LangGraph state handling in the agents (no LLM calls)."""

import json
from pathlib import Path

import agents.report_generator.html_generator as html_generator
import agents.report_generator.report_generator_agent as report_agent

SAMPLE = (
    Path(__file__).resolve().parent.parent
    / "files/analysis/heuristic/heuristic_analysis_23d095a19c9c45c89af5c66b5ffcea63.json"
)


def test_report_error_is_recorded_once(tmp_path, monkeypatch):
    # Nodes return the whole state: with an `add` reducer on `errors` every
    # entry used to be appended again at each node (4 copies of one error).
    monkeypatch.setattr(report_agent, "generate_executive_summary_text", lambda *a, **k: "Summary.")
    monkeypatch.setattr(html_generator, "TEMPLATE_DIR", tmp_path)  # no report template here
    monkeypatch.setattr(html_generator, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(report_agent, "REPORT_DIR", tmp_path)

    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    state = {
        "metadata": dict(data["metadata"], run_id="pytest"),
        "analysis": data["analysis"],
        "heuristic": data["heuristic"],
        "questionnaire": {},
        "visualizations": {},
        "html_path": "",
        "messages": [],
        "errors": [],
    }
    final = report_agent.create_report_generator_graph().invoke(state)

    failures = [e for e in final["errors"] if e.startswith("HTML report generation failed")]
    assert len(failures) == 1
    assert len(final["errors"]) == 1
