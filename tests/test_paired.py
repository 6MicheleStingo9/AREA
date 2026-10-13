"""Unit tests for the paired comparison of causal classifiers (evaluation/paired.py)."""

from evaluation.paired import AXES, compare

GOLD = {f"r{i}": {"entity": "ai", "intent": "intentional", "timing": "post-deployment"} for i in range(40)}
WRONG = {i: {"entity": "human", "intent": "other", "timing": "other"} for i in GOLD}


def test_verdicts_follow_the_interval():
    assert {r["verdict"] for r in compare(GOLD, GOLD, WRONG, n_boot=200).values()} == {"better"}
    assert {r["verdict"] for r in compare(GOLD, WRONG, GOLD, n_boot=200).values()} == {"worse"}
    assert {r["verdict"] for r in compare(GOLD, GOLD, GOLD, n_boot=200).values()} == {"on par"}


def test_one_row_per_axis_and_metric_and_missing_predictions_count_as_wrong():
    res = compare(GOLD, {}, GOLD, n_boot=50)
    assert list(res) == [f"{ax} {m}" for ax in AXES for m in ("accuracy", "macro-F1")]
    assert res["entity accuracy"]["a"] == 0.0 and res["entity accuracy"]["b"] == 1.0
