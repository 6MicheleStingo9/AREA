"""Unit tests for the AREA training runs (data_prep/area_trainset.py), without LLM calls."""

import json
import logging

from agents.questionnaire_generator.question_generator_agent import build_chat_messages
from data_prep.area_trainset import PROFILES, SYSTEMS, batches, disagreements, is_quota_error, kappa, merge, planned_runs, risk_rows

QUESTIONS = [{"id": "q1", "question": "What data is collected?", "type": "free_text"}]


def test_plan_alternates_languages_and_balances_profiles():
    plan = planned_runs()
    assert [p["run"] for p in plan[:3]] == ["t01", "t02", "t03"] and len(plan) == len(SYSTEMS) == 28
    assert [p["language"] for p in plan[:4]] == ["en", "it", "en", "it"]
    for language in ("en", "it"):
        counts = {pr: sum(p["language"] == language and p["profile"] == pr for p in plan) for pr in PROFILES}
        assert max(counts.values()) - min(counts.values()) <= 1


def test_the_questionnaire_describes_the_given_system_only_when_one_is_given():
    logging.disable(logging.CRITICAL)
    free = "".join(m.content for m in build_chat_messages(QUESTIONS, "expert", "en"))
    given = "".join(m.content for m in build_chat_messages(QUESTIONS, "expert", "en", "a credit scoring model"))
    assert "Decide autonomously" in free and "credit scoring" not in free
    assert "a credit scoring model" in given and "Decide autonomously" not in given


def test_quota_errors_are_told_apart():
    assert is_quota_error(Exception("Domain analysis failed: ['[DOMAIN][FATAL] 429 RESOURCE_EXHAUSTED ...']"))
    assert is_quota_error(Exception("429 You exceeded your current quota"))
    assert not is_quota_error(Exception("503 UNAVAILABLE: the model is overloaded"))


def test_risk_rows_flatten_a_run():
    run = {
        "run": "t01", "language": "en", "profile": "expert", "system": "a credit scoring model", "model": "m",
        "answers": {"metadata": {"run_id": "abc"}},
        "domain": {"analysis": {"1.1": {"risks": [{"title": "T", "explanation": "E", "severity": "high"}]}, "1.2": {"risks": []}}},
    }
    assert risk_rows(run) == [{
        "id": "t01-1.1-1", "run": "t01", "run_id": "abc", "language": "en", "profile": "expert",
        "system": "a credit scoring model", "model": "m", "subdomain": "1.1", "title": "T", "text": "E", "severity": "high",
    }]


def test_kappa_is_one_on_full_agreement_and_zero_at_chance():
    assert kappa(["a", "b", "a", "b"], ["a", "b", "a", "b"]) == 1.0
    assert abs(kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"])) < 1e-9


def _jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def test_protocol_merges_agreed_and_adjudicated_labels(tmp_path, capsys):
    ids = ["t01-1.1-1", "t01-1.1-2"]
    _jsonl(tmp_path / "risks.jsonl", [{"id": i, "run": "t01", "language": "en", "subdomain": "1.1", "title": "T", "text": "E"} for i in ids])
    label = {"entity": "ai", "intent": "unintentional", "timing": "post-deployment"}
    _jsonl(tmp_path / "annotations" / "a" / "t01.jsonl", [{"id": i, **label, "note": ""} for i in ids])
    _jsonl(tmp_path / "annotations" / "b" / "t01.jsonl", [{"id": ids[0], **label}, {"id": ids[1], **label, "intent": "other", "note": "unclear"}])

    batches(tmp_path, 5)
    batch = [json.loads(line) for line in (tmp_path / "annotations" / "batches" / "t01.jsonl").read_text().splitlines()]
    assert [r["id"] for r in batch] == ids and "entity" not in batch[0]

    disagreements(tmp_path)
    disputed = [json.loads(line) for line in (tmp_path / "annotations" / "disputed.jsonl").read_text().splitlines()]
    assert [(r["id"], r["disputed"], r["notes"]["B"]) for r in disputed] == [(ids[1], ["intent"], "unclear")]

    merge(tmp_path)
    assert len((tmp_path / "labels.jsonl").read_text().splitlines()) == 1  # the disputed risk waits for the adjudicator
    _jsonl(tmp_path / "annotations" / "adjudication" / "x.jsonl", [{"id": ids[1], "final": {"intent": "unintentional"}, "reason": {}}])
    merge(tmp_path)
    rows = [json.loads(line) for line in (tmp_path / "labels.jsonl").read_text().splitlines()]
    assert [r["intent"] for r in rows] == ["unintentional", "unintentional"]
    assert rows[1]["source"] == {"entity": "agreed", "intent": "adjudicated", "timing": "agreed"}
    assert "2 risks (1 with an adjudicated axis)" in capsys.readouterr().out


def test_a_questionnaire_reply_in_content_blocks_is_parsed(tmp_path, monkeypatch):
    from langchain_core.messages import AIMessage

    from agents.questionnaire_generator.question_generator_agent import save_responses_with_metadata

    monkeypatch.chdir(tmp_path)
    (tmp_path / "files" / "answers").mkdir(parents=True)
    reply = AIMessage(content=[{"type": "text", "text": '{"1.1": {"question": "Q", '}, {"type": "text", "text": '"answer": "A"}}'}])
    _, path = save_responses_with_metadata({"messages": [reply]}, "expert", "en", "files/answers/", run_id="r1")
    assert json.loads((tmp_path / path).read_text())["responses"] == {"1.1": {"question": "Q", "answer": "A"}}
