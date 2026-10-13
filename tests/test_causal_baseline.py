"""Checkpoint/resume of the causal baseline (a fake model answers, no API calls)."""

import re

import pytest

from evaluation.causal_baseline import new_run_state, predict

EXAMPLES = [{"meta": {"ev_id": f"1.{i}"}, "title": "", "input": "risk"} for i in range(5)]


class FakeLLM:
    """Labels every risk of the prompt except `skip`; raises on call number `fail_on`."""

    def __init__(self, fail_on=None, skip=()):
        self.calls, self.fail_on, self.skip = 0, fail_on, set(skip)

    def invoke(self, messages):
        self.calls += 1
        if self.calls == self.fail_on:
            raise RuntimeError("429 RESOURCE_EXHAUSTED")
        ids = re.findall(r'"id": "([^"]+)"', messages[-1]["content"])
        return {"items": [{"id": i, "entity": "ai", "intent": "other", "timing": "other"} for i in ids if i not in self.skip]}


def test_interrupted_run_resumes_without_repeating_calls():
    state, saved = new_run_state(), []
    with pytest.raises(RuntimeError):
        predict(FakeLLM(fail_on=2), EXAMPLES, 2, state, lambda: saved.append(len(state["preds"])))
    assert state["done"] == [0] and saved == [2] and not state["complete"]

    llm = FakeLLM()
    predict(llm, EXAMPLES, 2, state, lambda: None)
    assert llm.calls == 2 and state["calls"] == 3 and len(state["preds"]) == 5 and state["complete"]

    predict(llm, EXAMPLES, 2, state, lambda: None)  # a complete run makes no further calls
    assert llm.calls == 2


def test_missing_answers_are_retried_once():
    state, llm = new_run_state(), FakeLLM(skip={"1.3"})
    predict(llm, EXAMPLES, 2, state, lambda: None)
    assert llm.calls == 4 and "1.3" not in state["preds"] and state["complete"]
