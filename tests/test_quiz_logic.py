"""The questionnaire logic (quiz/logic.py): the shared cases, and the answers the pipeline reads."""

import json

import pytest

import agents.domain_analyzer.domain_risk_analyzer_agent as domain
from quiz.logic import answer_errors, load_questions, responses, save_answers, validate_assessment, visible_followups
from utils.paths import ROOT

CASES = json.loads((ROOT / "tests" / "fixtures" / "questionnaire_cases.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES["followups"], ids=lambda case: case["name"])
def test_the_follow_ups_that_an_answer_opens(case):
    assert visible_followups(case["question"], case["answer"]) == case["visible"]


@pytest.mark.parametrize("case", CASES["validation"], ids=lambda case: case["name"])
def test_the_checks_on_an_answer(case):
    assert answer_errors(case["question"], case["answer"]) == case["errors"]


def test_every_question_of_both_questionnaires_has_follow_ups_the_rules_know():
    for lang in ("en", "it"):
        for question in load_questions(lang):
            for followup in question["follow_ups"]:
                assert followup["condition"]["type"] in ("always", "option_index", "option_index_in")


def test_the_two_questionnaires_ask_the_same_questions():
    english, italian = load_questions("en"), load_questions("it")
    shape = lambda q: (q["id"], q["type"], len(q.get("options", [])), [f["condition"] for f in q["follow_ups"]])
    assert [shape(q) for q in english] == [shape(q) for q in italian]


QUESTIONS = [
    {"id": "1.1", "question": "What data?", "type": "free_text", "required": True,
     "follow_ups": [{"text": "How is it used?", "required": False, "condition": {"type": "always"}}]},
    {"id": "1.2", "question": "What content?", "type": "checkbox", "required": True, "options": ["Text", "Code", "Images"],
     "allow_other": True, "follow_ups": [{"text": "Filters?", "required": True, "condition": {"type": "always"}}]},
    {"id": "1.3", "question": "Differences?", "type": "multiple_choice", "required": True, "options": ["Yes", "No"],
     "follow_ups": [{"text": "Which groups?", "required": True, "condition": {"type": "option_index", "value": 0}}]},
]


def test_the_pipeline_reads_the_answers_in_words_with_the_follow_ups_they_opened():
    answers = {
        "1.1": {"text": " Logs of the queries ", "followups": {"0": ""}},
        "1.2": {"choices": [1, 0], "other": " Tables ", "followups": {"0": "A safety classifier."}},
        # A follow-up written before the answer changed, and no longer open: left out
        "1.3": {"choice": 1, "followups": {"0": "Users of niche languages."}},
    }
    assert validate_assessment(QUESTIONS, answers) == {}
    assert responses(QUESTIONS, answers) == {
        "1.1": {"question": "What data?", "answer": "Logs of the queries", "followups": {}},
        "1.2": {"question": "What content?", "answer": {"selected": ["Text", "Code"], "other": "Tables"},
                "followups": {"0": "A safety classifier."}},
        "1.3": {"question": "Differences?", "answer": "No", "followups": {}},
    }


def test_an_assessment_lists_the_errors_of_each_question():
    assert validate_assessment(QUESTIONS, {"1.1": {"text": "Logs"}}) == {
        "1.2": [{"code": "min_selections", "min": 1}],
        "1.3": [{"code": "required"}],
    }


def test_the_name_of_the_system_stays_out_of_the_prompt(monkeypatch, tmp_path):
    monkeypatch.setattr("quiz.logic.ANSWERS", tmp_path)
    path = save_answers(responses(QUESTIONS, {"1.1": {"text": "Logs"}}), "en", 3, run_id="abcd1234",
                        system_name="Project Nightingale")
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["metadata"]["system_name"] == "Project Nightingale"

    sent = []

    class FakeLLM:
        def with_structured_output(self, **_):
            return self

        def invoke(self, messages):
            sent.extend(messages)
            return {}

    monkeypatch.setattr(domain, "get_llm_instance", lambda **_: FakeLLM())
    monkeypatch.setattr(domain, "apply_retry", lambda runnable: runnable)
    domain.node_analyze({"questionnaire": saved, "metadata": saved["metadata"], "messages": [], "errors": []})
    prompt = json.dumps(sent, default=str)
    assert "Logs" in prompt and "Nightingale" not in prompt
