"""The JSON API of the web interface (api/assessments.py, api/reports.py), with a fake pipeline."""

import io
import json
import zipfile

import pytest
from fastapi.testclient import TestClient

import api.assessments as assessments
import api.reports as reports
from api import jobs
from api.main import app
from quiz.logic import load_questions, visible_followups
from utils import progress

HEURISTIC = {
    "executive_summary": {
        "global_risk_score": 61.47,
        "overall_risk_level": "high",
        "primary_concern": "active_threats",
        "recommended_action": "immediate_mitigation",
        "most_critical_domain": {"domain": "4", "domain_name": "Malicious actors", "high_count": 4},
    },
    "counting": {"total_risks": 34, "by_severity": {"low": 4, "medium": 19, "high": 11},
                 "by_domain": {"1": 4, "2": 3, "3": 0, "4": 6, "5": 3, "6": 8, "7": 10}},
}


@pytest.fixture
def files(tmp_path, monkeypatch):
    """Every file of a run in tmp_path, and no job from earlier tests."""
    monkeypatch.setattr(jobs, "JOBS", tmp_path / "jobs")
    monkeypatch.setattr(jobs, "_jobs", {})
    monkeypatch.setattr("quiz.logic.ANSWERS", tmp_path / "answers")
    for name, path in (("REPORTS", tmp_path / "reports"), ("ANALYSIS", tmp_path / "analysis"), ("ANSWERS", tmp_path / "answers")):
        monkeypatch.setattr(reports, name, path)
    return tmp_path


def complete_answers(lang="en"):
    """An answer to every question of the questionnaire, follow-ups included where required."""
    answers = {}
    for question in load_questions(lang):
        kind = question["type"]
        answer = {"text": "An answer long enough."} if kind == "free_text" else {"choice": 0} if kind == "multiple_choice" else {"choices": [0]}
        answer["followups"] = {str(i): "Some detail." for i in visible_followups(question, answer)}
        answers[question["id"]] = answer
    return answers


def fake_pipeline(files, seen=None, fail=None):
    """Stand-in for run_orchestrator: reports its steps, writes a report and a heuristic analysis."""

    def run(answers_path):
        run_id = json.loads(open(answers_path, encoding="utf-8").read())["metadata"]["run_id"]
        if seen is not None:
            seen.append(dict(jobs.get_job(run_id)))
        progress.report(run_id, "causes", risks=2, labelled=1)
        if seen is not None:
            seen.append(dict(jobs.get_job(run_id)))
        if fail:
            raise fail
        (files / "analysis" / "heuristic").mkdir(parents=True)
        (files / "analysis" / "heuristic" / f"heuristic_analysis_{run_id}.json").write_text(json.dumps({"heuristic": HEURISTIC}))
        (files / "reports").mkdir()
        report = files / "reports" / f"ai_risk_report_{run_id}.html"
        report.write_text("<h1>Report</h1>", encoding="utf-8")
        return {"report_state": {"html_path": str(report)}}

    return run


def test_the_questionnaire_in_each_language():
    client = TestClient(app)
    italian = client.get("/api/questionnaire", params={"lang": "it"}).json()
    assert italian["lang"] == "it" and len(italian["questions"]) == 24
    assert italian["questions"][0]["id"] == "1.1"
    assert client.get("/api/questionnaire", params={"lang": "fr"}).status_code == 422


def test_incomplete_answers_come_back_with_the_errors_of_each_question(files):
    answers = complete_answers()
    answers["1.3"] = {"choice": 0}  # the follow-up of "Yes" is required
    del answers["2.1"]
    response = TestClient(app).post("/api/assessments", json={"lang": "en", "answers": answers})
    assert response.status_code == 422
    assert response.json()["errors"] == {"1.3": [{"code": "followup_required", "followup": 0}], "2.1": [{"code": "min_selections", "min": 1}]}
    assert not (files / "answers").exists()


def test_an_assessment_runs_and_reports_its_steps_then_its_results(files, monkeypatch):
    seen = []
    monkeypatch.setattr(assessments, "run_orchestrator", fake_pipeline(files, seen))
    client = TestClient(app)
    response = client.post("/api/assessments", json={"lang": "it", "system_name": "  Assistente  ", "answers": complete_answers("it")})
    assert response.status_code == 201
    run_id = response.json()["id"]
    assert response.headers["location"] == f"/api/assessments/{run_id}"

    saved = json.loads((files / "answers" / f"answers_{run_id}.json").read_text(encoding="utf-8"))
    assert saved["metadata"]["language"] == "it" and saved["metadata"]["system_name"] == "Assistente"
    assert saved["responses"]["1.3"]["answer"] == load_questions("it")[2]["options"][0]  # the option in words

    # The background task ran within the request: the job went through the steps
    assert [(job["status"], job.get("step"), job.get("labelled")) for job in seen] == [("running", "domain", None), ("running", "causes", 1)]
    status = client.get(f"/api/assessments/{run_id}").json()
    assert status["status"] == "done" and status["system_name"] == "Assistente" and status["lang"] == "it"
    assert status["result"] == {
        "score": 61.47, "level": "high", "concern": "active_threats", "action": "immediate_mitigation",
        "critical_domain": {"id": "4", "high": 4}, "risks": 34, "domains": 6,
        "severity": {"low": 4, "medium": 19, "high": 11},
    }
    assert client.get(status["report_url"]).text == "<h1>Report</h1>"

    archive = zipfile.ZipFile(io.BytesIO(client.get(status["archive_url"]).content))
    assert sorted(archive.namelist()) == ["analysis/heuristic.json", "answers.json", "report.html"]


def test_a_refusal_for_the_quota_says_so(files, monkeypatch):
    monkeypatch.setattr(assessments, "run_orchestrator", fake_pipeline(files, fail=Exception("429 RESOURCE_EXHAUSTED: quota")))
    client = TestClient(app)
    run_id = client.post("/api/assessments", json={"lang": "en", "answers": complete_answers()}).json()["id"]
    status = client.get(f"/api/assessments/{run_id}").json()
    assert status["status"] == "error" and status["error_code"] == "quota" and "RESOURCE_EXHAUSTED" in status["error"]
    assert "result" not in status


def test_an_unknown_assessment(files):
    client = TestClient(app)
    assert client.get("/api/assessments/abc123").status_code == 404
    assert client.get("/api/assessments/abc123/archive").status_code == 404
    assert client.get("/report/abc123").status_code == 404
    # A path never reaches the disk (an HTTP client would turn /report/.. into / before sending it)
    assert reports.report_path("..") is None and reports.report_path("a/b") is None


def test_an_assessment_cut_short_by_a_restart_is_interrupted(files):
    jobs.create_job("abc123")
    jobs._jobs.clear()  # a new process knows only what is on disk
    jobs.mark_interrupted()
    assert TestClient(app).get("/api/assessments/abc123").json()["status"] == "interrupted"
