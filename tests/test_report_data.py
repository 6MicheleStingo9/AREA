"""The data of the HTML report (agents/report_generator/report_data.py), and how they reach the page
(html_generator.py)."""

import json

import pytest

import agents.report_generator.html_generator as html_generator
from agents.report_generator.report_data import alerts, answers, flow, language_of, patterns, profile, report_data, risks
from utils.paths import ANSWERS, ROOT

EXAMPLE = "23d095a19c9c45c89af5c66b5ffcea63"  # the example run, in files/
EXAMPLE_ANSWERS = ANSWERS / "answers_20251227_160418.json"  # saved before the answers took the id of the run
FIXTURE = ROOT / "frontend" / "report" / "src" / "test" / "example.json"


def _example():
    run = html_generator.saved_run(EXAMPLE, EXAMPLE_ANSWERS)
    questions = html_generator._questions(run["metadata"])
    return report_data(run["metadata"], run["heuristic"], run["analysis"], run["questionnaire"], questions, run["created"])


def test_the_app_is_tested_on_the_example_run_as_python_prepares_it():
    command = (
        f"python -m agents.report_generator.html_generator {EXAMPLE} "
        f"--answers {EXAMPLE_ANSWERS.relative_to(ROOT)} --data > {FIXTURE.relative_to(ROOT)}"
    )
    assert json.loads(FIXTURE.read_text(encoding="utf-8")) == _example(), f"The fixture is out of date: {command}"


def test_the_charts_of_the_example_count_as_the_report_before_them():
    # The numbers of the Plotly report of the example run (chart_data_builder.py, until October 2026)
    data = _example()
    assert data["profile"] == [
        {"axis": "severity", "criticality": 32.4, "safety": 67.6},  # risk concentration, impact control
        {"axis": "exposure", "criticality": 91.2, "safety": None},  # operational exposure
        {"axis": "prevention", "criticality": 100.0, "safety": 0.0},  # prevention deficit, preventability
        {"axis": "intent", "criticality": 32.4, "safety": 67.6},  # threat intensity, safety culture
        {"axis": "entity", "criticality": None, "safety": 41.2},  # human-caused share, once human oversight
    ]
    assert [(d["high"], d["medium"], d["low"]) for d in data["domains"]] == [
        (1, 3, 0), (1, 1, 1), (1, 2, 0), (4, 2, 0), (1, 1, 1), (1, 6, 1), (2, 4, 1),
    ]
    links = {(link["from"], link["to"]): link["count"] for name in ("entity_intent", "intent_timing") for link in data["flow"][name]}
    assert links == {
        ("ai", "intentional"): 1, ("ai", "unintentional"): 18, ("human", "intentional"): 10,
        ("human", "unintentional"): 4, ("other", "unintentional"): 1,
        ("intentional", "post-deployment"): 9, ("intentional", "other"): 2,
        ("unintentional", "post-deployment"): 22, ("unintentional", "other"): 1,
    }
    counted = {p["id"]: p["count"] for p in data["patterns"] if p["count"]}
    assert counted == {
        "critical_ai_risks": 4, "malicious_human_risks": 10, "high_threat_attacks": 6, "unintended_ai_failures": 18,
        "human_error_risks": 4, "intentional_ai_risks": 1, "critical_human_errors": 1,
        "moderate_operational_risks": 17, "moderate_ai_risks": 12, "moderate_human_risks": 6,
        "moderate_intentional_ai_risks": 1, "moderate_human_intentional_risks": 3, "low_operational_risks": 4,
    }
    assert len(data["patterns"]) == 18


def test_the_example_report_has_the_verdict_of_the_rules_and_every_risk():
    data = _example()
    assert data["results"] == {
        "score": 61.47, "level": "high", "concern": "active_threats", "action": "immediate_mitigation",
        "critical_domains": [{"id": "4", "high": 4}, {"id": "7", "high": 2}, {"id": "6", "high": 1}],
    }
    assert [a["id"] for a in data["alerts"]] == [
        "intentional_threats", "operational_risks", "low_preventable_ratio", "medium_risk_accumulation",
        "high_risk_fragmentation",
    ]
    assert data["counts"]["risks"] == len(data["risks"]) == 34
    assert (data["counts"]["domains"], data["counts"]["subdomains"]) == (7, 21)
    assert data["risks"][0]["id"] == "1.1-1" and data["created"] == "2025-12-27T16:06:56"
    # Labelled by Gemini before Laya: a rationale, no confidence
    assert data["risks"][0]["causes"]["entity"] == {
        "value": "ai",
        "rationale": "The risk is caused by biases in the AI system's training data or its tailoring logic.",
        "confidence": None,
        "probabilities": None,
    }


def test_a_risk_without_its_severity_rationale_has_none():
    analysis = {"1.1": {"risks": [{"title": "T", "explanation": "E", "severity": "high", "severity_rationale": " ", "mitigation": "M"}]}}
    assert risks(analysis)[0]["severity_rationale"] is None


def test_a_label_of_laya_keeps_its_confidence_and_probabilities():
    causality = {
        "entity": {"value": "human", "rationale": "...", "confidence": 0.71, "probabilities": {"ai": 0.2, "human": 0.71, "other": 0.09}},
        "intent": {"value": "something else", "rationale": "..."},
    }
    analysis = {"2.1": {"risks": [{"title": "T", "severity": "low", "causality": causality}]}}
    causes = risks(analysis)[0]["causes"]
    assert causes["entity"]["confidence"] == 0.71 and causes["entity"]["probabilities"]["ai"] == 0.2
    # A value out of the taxonomy, or a missing axis, reads as "other"
    assert causes["intent"]["value"] == "other" and causes["timing"]["value"] == "other"


def test_the_profile_of_risks_with_no_preventable_one():
    counting = {
        "total_risks": 20,
        "by_severity": {"high": 5, "medium": 10, "low": 5},
        "by_timing": {"pre-deployment": 4, "post-deployment": 14, "other": 2},
        "by_intent": {"intentional": 6, "unintentional": 13, "other": 1},
        "by_entity": {"ai": 9, "human": 8, "other": 3},
    }
    assert profile({"counting": counting}) == [
        {"axis": "severity", "criticality": 25.0, "safety": 75.0},
        {"axis": "exposure", "criticality": 70.0, "safety": None},
        {"axis": "prevention", "criticality": 80.0, "safety": 20.0},
        {"axis": "intent", "criticality": 30.0, "safety": 65.0},
        {"axis": "entity", "criticality": None, "safety": 40.0},
    ]


def test_only_the_alerts_that_the_rules_raised():
    heuristic = {"patterns": {"alerts": {"ai_dominance": {"alert": False, "value": 40}, "intentional_threats": {"alert": True, "value": 5}, "broken": None}}}
    assert alerts(heuristic) == [{"id": "intentional_threats", "value": 5}]


def test_a_pattern_that_the_rules_add_later_comes_last_in_its_group():
    found = patterns({"patterns": {"low_patterns": {"low_operational_risks": 2, "low_new_pattern": 1}}})
    assert found[-2:] == [
        {"id": "low_operational_risks", "category": "low", "cause": "any", "count": 2},
        {"id": "low_new_pattern", "category": "low", "cause": "any", "count": 1},
    ]


def test_the_flow_keeps_the_order_of_the_taxonomy():
    analysis = {"1.1": {"risks": [
        {"causality": {"entity": {"value": "human"}, "intent": {"value": "intentional"}, "timing": {"value": "pre-deployment"}}},
        {"causality": {"entity": {"value": "ai"}, "intent": {"value": "intentional"}, "timing": {"value": "pre-deployment"}}},
    ]}}
    assert flow(analysis)["entity_intent"] == [
        {"from": "ai", "to": "intentional", "count": 1},
        {"from": "human", "to": "intentional", "count": 1},
    ]


def test_the_answers_give_the_text_of_their_follow_ups():
    questions = [{"id": "1.3", "question": "Differences?", "follow_ups": [{"text": "Which groups?"}, {"text": "How measured?"}]}]
    questionnaire = {"metadata": {}, "responses": {
        "1.3": {"question": "Differences?", "answer": "Yes", "followups": {"0": " Users of niche languages. ", "1": "", "7": "lost"}},
        "1.2": {"question": "What content?", "answer": {"selected": ["Text"], "other": " "}, "followups": {}},
        "2.1": {"question": "What data?", "answer": "  "},
    }}
    assert answers(questionnaire, questions) == {
        "1.3": {"question": "Differences?", "answer": "Yes", "followups": [{"question": "Which groups?", "answer": "Users of niche languages."}]},
        "1.2": {"question": "What content?", "answer": {"selected": ["Text"], "other": None}, "followups": []},
        "2.1": {"question": "What data?", "answer": None, "followups": []},
    }


def test_a_summary_that_gemini_could_not_write_is_none():
    data = report_data({"run_id": "r", "executive_summary_text": "Executive summary not available due to generation error."}, {}, {})
    assert data["summary"] is None
    assert data["language"] == "en" and language_of({"language": "it-IT"}) == "it" and language_of({"language": "fr"}) == "en"


@pytest.fixture
def built(tmp_path, monkeypatch):
    """A build of the report app with its place for the data, and a folder for the reports."""
    template = tmp_path / "index.html"
    template.write_text(
        f'<!doctype html><html><body><script id="report-data" type="application/json">{html_generator.PLACEHOLDER}</script></body></html>',
        encoding="utf-8",
    )
    monkeypatch.setattr(html_generator, "TEMPLATE", template)
    monkeypatch.setattr(html_generator, "REPORT_DIR", tmp_path / "reports")
    return template


def _data_in(html: str):
    start = html.index('type="application/json">') + len('type="application/json">')
    return json.loads(html[start:html.index("</script>", start)])


def test_no_text_of_the_data_can_end_the_script_that_holds_them(built):
    data = {"summary": "</script><script>alert(1)</script> <!-- & ok >"}
    html = html_generator.render(data)
    assert html.count("</script>") == 1 and "<!--" not in html
    assert _data_in(html) == data


def test_the_report_of_a_run_goes_to_files_reports(built):
    path = html_generator.generate_html_report({"run_id": "abcd1234", "language": "it", "system_name": "Assistente"}, {}, {}, {})
    assert path.name == "ai_risk_report_abcd1234.html"
    data = _data_in(path.read_text(encoding="utf-8"))
    assert (data["run_id"], data["language"], data["system_name"]) == ("abcd1234", "it", "Assistente")


def test_without_the_build_the_report_says_how_to_build_it(built, tmp_path):
    built.unlink()
    with pytest.raises(html_generator.ReportTemplateMissing, match="npm run build"):
        html_generator.generate_html_report({"run_id": "abcd1234"}, {}, {})
    built.write_text("<html>no place for the data</html>", encoding="utf-8")
    with pytest.raises(html_generator.ReportTemplateMissing, match="no place"):
        html_generator.render({})


def test_a_past_run_is_made_again_from_its_files(built):
    path = html_generator.rebuild(EXAMPLE, EXAMPLE_ANSWERS)
    data = _data_in(path.read_text(encoding="utf-8"))
    assert data == _example()
    assert data["summary"].startswith("An in-depth AI risk analysis")
