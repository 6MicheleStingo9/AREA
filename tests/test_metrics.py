"""Unit tests for the evaluation metrics (evaluation/metrics.py)."""

import pytest

from evaluation.metrics import accuracy, bootstrap_ci, brier, confusion, ece, macro_f1, per_class, summarize

LABELS = ["a", "b", "c"]
Y_TRUE = ["a", "a", "b", "b", "c", "c"]
Y_PRED = ["a", "b", "b", "b", "c", None]


def test_accuracy_counts_missing_predictions_as_wrong():
    assert accuracy(Y_TRUE, Y_PRED) == pytest.approx(4 / 6)


def test_per_class_and_macro_f1():
    scores = per_class(Y_TRUE, Y_PRED, LABELS)
    assert scores["a"] == {"precision": 1.0, "recall": 0.5, "f1": pytest.approx(2 / 3), "support": 2}
    assert scores["b"]["precision"] == pytest.approx(2 / 3) and scores["b"]["recall"] == 1.0
    assert scores["c"]["f1"] == pytest.approx(2 / 3)
    assert macro_f1(Y_TRUE, Y_PRED, LABELS) == pytest.approx((2 / 3 + 0.8 + 2 / 3) / 3)


def test_confusion_has_a_missing_column_only_when_needed():
    assert confusion(Y_TRUE, Y_PRED, LABELS)["c"] == {"a": 0, "b": 0, "c": 1, "None": 1}
    assert "None" not in confusion(Y_TRUE, Y_TRUE, LABELS)["a"]


def test_bootstrap_is_deterministic_and_brackets_the_estimate():
    lo, hi = bootstrap_ci(Y_TRUE, Y_PRED, accuracy, n_boot=500, seed=1)
    assert (lo, hi) == tuple(bootstrap_ci(Y_TRUE, Y_PRED, accuracy, n_boot=500, seed=1))
    assert lo <= accuracy(Y_TRUE, Y_PRED) <= hi


def test_summarize_reports_missing():
    assert summarize(Y_TRUE, Y_PRED, LABELS, n_boot=50)["missing"] == 1


def test_ece_is_zero_when_confidence_matches_accuracy():
    assert ece([0.75] * 4, [True, True, True, False]) == pytest.approx(0.0)
    assert ece([0.9, 0.9], [False, False]) == pytest.approx(0.9)


def test_brier_of_certain_and_uniform_predictions():
    assert brier([{"a": 1.0, "b": 0.0}], ["a"], ["a", "b"]) == 0.0
    assert brier([{"a": 0.5, "b": 0.5}], ["a"], ["a", "b"]) == pytest.approx(0.5)
