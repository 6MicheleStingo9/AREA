"""The progress of a run (utils/progress.py), as the orchestrator reports it."""

import agents.orchestrator as orchestrator
from utils import progress


def test_a_report_reaches_the_listener_of_its_run_only():
    seen = []
    progress.listen("a", lambda step, **counts: seen.append((step, counts)))
    try:
        progress.report("a", "rules")
        progress.report("b", "rules")
        progress.report(None, "rules")
    finally:
        progress.forget("a")
    progress.report("a", "report")
    assert seen == [("rules", {})]


class FakeGraph:
    def invoke(self, state):
        return {"errors": []}


def test_the_orchestrator_reports_each_step_with_the_number_of_risks(monkeypatch):
    for name in ("create_causality_analyzer_graph", "create_heuristic_analyzer_graph", "create_report_generator_graph"):
        monkeypatch.setattr(orchestrator, name, FakeGraph)
    analysis = {"1.1": {"risks": [{}, {}]}, "4.2": {"risks": [{}]}}
    state = {"domain_state": {"metadata": {"run_id": "r1"}, "analysis": analysis}}
    seen = []
    progress.listen("r1", lambda step, **counts: seen.append((step, counts)))
    try:
        for step in (orchestrator.causality_step, orchestrator.heuristic_step, orchestrator.report_step):
            state = step(state)
    finally:
        progress.forget("r1")
    assert seen == [("causes", {"risks": 3, "labelled": 0}), ("rules", {}), ("report", {})]
