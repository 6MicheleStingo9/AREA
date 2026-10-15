"""The causality step with Laya (agents/causality_analyzer): what Laya reads, the labels, the backends."""

import importlib.util
import json

import pytest

import agents.causality_analyzer.causality_risk_analyzer_agent as causality
from agents.causality_analyzer import laya_classifier
from utils import progress
from utils.paths import ROOT

EVALUATED = ROOT / "evaluation" / "results" / "area_testset__laya-causal-v4__2026-10-12.json"


def _risk(title, explanation="Explanation.", mitigation="Mitigation."):
    return {"title": title, "explanation": explanation, "severity": "high", "severity_rationale": "Why.", "mitigation": mitigation}


class FakeLaya:
    """Answers every risk with the same probabilities and records what it read."""

    def __init__(self, probabilities):
        self.probabilities, self.states = probabilities, []

    def predict(self, state, questions):
        self.states.append(state)
        assert questions is laya_classifier.QUESTIONS
        return {"answers": {ax: {"choice": max(p, key=p.get), "probabilities": p} for ax, p in self.probabilities.items()}}


CONFIDENT = {
    "entity": {"ai": 0.9333, "human": 0.0334, "other": 0.0333},
    "intent": {"intentional": 0.0333, "unintentional": 0.9334, "other": 0.0333},
    "timing": {"pre-deployment": 0.0333, "post-deployment": 0.9334, "other": 0.0333},
}


@pytest.fixture
def fake_laya(monkeypatch):
    def install(probabilities=CONFIDENT):
        fake = FakeLaya(probabilities)
        monkeypatch.setattr(laya_classifier, "load", lambda: fake)
        return fake

    return install


def test_laya_reads_the_mit_subdomain_title_and_explanation(fake_laya):
    fake = fake_laya()
    causality._analyze_with_laya({"2.1": {"risks": [_risk("Data leak", "Logs keep personal data.", "Purge the logs.")]}}, "en")
    name = laya_classifier.subdomain_names()["2.1"]
    assert fake.states == [f"Risk subdomain: 2.1 {name}\nData leak\nLogs keep personal data."]


def test_laya_reports_each_risk_it_labels(fake_laya):
    fake_laya()
    seen = []
    progress.listen("run1", lambda step, **counts: seen.append((step, counts)))
    try:
        causality._analyze_with_laya({"2.1": {"risks": [_risk("A"), _risk("B")]}}, "en", run_id="run1")
    finally:
        progress.forget("run1")
    assert seen == [("causes", {"risks": 2, "labelled": 1}), ("causes", {"risks": 2, "labelled": 2})]


def test_an_unknown_subdomain_leaves_the_subdomain_line_out(fake_laya):
    fake = fake_laya()
    causality._analyze_with_laya({"9.9": {"risks": [_risk("Title")]}}, "en")
    assert fake.states == ["Title\nExplanation."]


def test_laya_keeps_subdomains_risks_and_their_fields(fake_laya):
    fake_laya()
    analysis = {"1.1": {"risks": [_risk("A"), _risk("B")]}, "6.5": {"risks": []}, "2.2": {"risks": [_risk("C")]}}
    out = causality._analyze_with_laya(analysis, "en")
    assert list(out) == ["1.1", "6.5", "2.2"] and out["6.5"] == {"risks": []}
    assert [r["title"] for r in out["1.1"]["risks"]] == ["A", "B"]
    risk = out["2.2"]["risks"][0]
    assert {k: v for k, v in risk.items() if k != "causality"} == _risk("C")
    assert {ax: f["value"] for ax, f in risk["causality"].items()} == {"entity": "ai", "intent": "unintentional", "timing": "post-deployment"}
    entity = risk["causality"]["entity"]
    assert entity["confidence"] == 0.9333 and entity["probabilities"] == CONFIDENT["entity"] and entity["review"] is False
    assert entity["rationale"] == "The risk is caused by a decision or action made by an AI system. Label assigned by the local Laya model with 93% confidence."


def test_low_confidence_labels_are_flagged_with_the_next_most_likely_value(fake_laya):
    fake_laya(dict(CONFIDENT, entity={"ai": 0.5, "human": 0.3, "other": 0.2}))
    out = causality._analyze_with_laya({"7.3": {"risks": [_risk("A")]}}, "it")
    fields = out["7.3"]["risks"][0]["causality"]
    assert fields["entity"]["review"] is True and fields["intent"]["review"] is False
    assert fields["entity"]["rationale"] == (
        "Il rischio è causato da una decisione o da un'azione di un sistema di IA. Etichetta assegnata dal modello "
        "locale Laya con confidenza 50%. Sotto la soglia di revisione del 90%: da verificare. Seconda ipotesi: Umano (30%)."
    )
    assert "Seconda ipotesi" not in fields["intent"]["rationale"]


def test_a_confidence_just_below_the_threshold_is_not_shown_as_the_threshold(fake_laya):
    fake_laya(dict(CONFIDENT, timing={"pre-deployment": 0.0501, "post-deployment": 0.8999, "other": 0.05}))
    field = causality._analyze_with_laya({"7.3": {"risks": [_risk("A")]}}, "en")["7.3"]["risks"][0]["causality"]["timing"]
    assert field["review"] is True and "with 89% confidence" in field["rationale"]


def test_the_review_threshold_can_be_configured(fake_laya, monkeypatch):
    fake_laya()
    monkeypatch.setenv("LAYA_REVIEW_THRESHOLD", "0.95")
    field = causality._analyze_with_laya({"7.3": {"risks": [_risk("A")]}}, "en")["7.3"]["risks"][0]["causality"]["entity"]
    assert field["review"] is True and "Below the 95% review threshold" in field["rationale"]


def _state(analysis, language="en"):
    return {"metadata": {"language": language, "run_id": "pytest"}, "analysis": analysis, "messages": [], "errors": []}


def test_node_analyze_records_the_backend_and_leaves_the_input_metadata_alone(fake_laya, monkeypatch):
    fake_laya()
    monkeypatch.delenv("CAUSALITY_BACKEND", raising=False)
    state = _state({"1.1": {"risks": [_risk("A")]}})
    metadata = state["metadata"]
    out = causality.node_analyze(state)
    assert out["errors"] == []
    assert out["metadata"]["causality_model"] == {"backend": "laya", "model": laya_classifier.model_name(), "review_threshold": 0.9}
    assert "causality_model" not in metadata


def test_the_model_is_the_local_checkpoint_else_the_published_one(monkeypatch, tmp_path):
    monkeypatch.delenv("LAYA_MODEL", raising=False)
    monkeypatch.delenv("LAYA_REVISION", raising=False)
    monkeypatch.setattr(laya_classifier, "DEFAULT_MODEL", tmp_path)
    assert laya_classifier.model_spec() == (str(tmp_path), None)
    monkeypatch.setattr(laya_classifier, "DEFAULT_MODEL", tmp_path / "missing")
    assert laya_classifier.model_spec() == ("MicheleStingo/laya-kindynos-causal", "v1.0")
    assert laya_classifier.model_name() == "MicheleStingo/laya-kindynos-causal"
    assert laya_classifier.problem() in (None, laya_classifier._NO_PACKAGES)  # a Hub id needs no local directory
    monkeypatch.setenv("LAYA_MODEL", "someone/another-laya")
    assert laya_classifier.model_spec() == ("someone/another-laya", None)


def test_an_unknown_backend_is_an_error(monkeypatch):
    monkeypatch.setenv("CAUSALITY_BACKEND", "gpt")
    out = causality.node_analyze(_state({"1.1": {"risks": [_risk("A")]}}))
    assert out["errors"] == ["CAUSALITY_BACKEND must be one of laya, llm, got 'gpt'"]
    monkeypatch.setenv("CAUSALITY_BACKEND", " LLM ")
    assert causality.causality_backend() == "llm"


def test_a_missing_checkpoint_says_how_to_fix_it(monkeypatch, tmp_path):
    monkeypatch.delenv("CAUSALITY_BACKEND", raising=False)
    monkeypatch.setenv("LAYA_MODEL", str(tmp_path / "missing"))
    monkeypatch.setattr(laya_classifier, "_agent", None)
    out = causality.node_analyze(_state({"1.1": {"risks": [_risk("A")]}}))
    assert len(out["errors"]) == 1
    assert out["errors"][0].startswith(f"No Laya checkpoint at {tmp_path / 'missing'}") and "CAUSALITY_BACKEND=llm" in out["errors"][0]


def test_the_llm_prompts_carry_the_language():
    # Criticality #26: the system prompt kept a literal {{language}}
    messages = causality._build_messages({"1.1": {"risks": []}}, "it")
    assert all("{{language}}" not in m["content"] for m in messages)
    assert '"language": "it"' in messages[0]["content"]


@pytest.mark.skipif(
    importlib.util.find_spec("laya") is None or not laya_classifier.DEFAULT_MODEL.is_dir() or not EVALUATED.exists(),
    reason="needs the laya packages and the laya-causal-v4 checkpoint",
)
def test_the_pipeline_gives_the_evaluated_labels(monkeypatch):
    # The causality step reproduces the predictions scored in evaluation/results (on a GPU there)
    monkeypatch.delenv("LAYA_MODEL", raising=False)
    evaluated = json.loads(EVALUATED.read_text(encoding="utf-8"))["predictions"]
    rows = [json.loads(line) for line in (ROOT / "evaluation" / "area_testset" / "risks.jsonl").open(encoding="utf-8")][:3]
    analysis = {}
    for r in rows:
        analysis.setdefault(r["subdomain"], {"risks": []})["risks"].append(_risk(r["title"], r["text"]))
    out = causality._analyze_with_laya(analysis, "en")
    labelled = [risk for block in out.values() for risk in block["risks"]]
    for r, risk in zip([r for code in analysis for r in rows if r["subdomain"] == code], labelled):
        for ax in laya_classifier.AXES:
            assert risk["causality"][ax]["value"] == evaluated[r["id"]][ax]["choice"]
            for value, p in evaluated[r["id"]][ax]["probabilities"].items():
                assert abs(risk["causality"][ax]["probabilities"][value] - p) < 0.02
