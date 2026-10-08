"""Classification metrics with bootstrap confidence intervals (standard library only)."""

import random
from typing import Any, Callable, Dict, List, Optional, Sequence


def accuracy(y_true: Sequence[str], y_pred: Sequence[Optional[str]]) -> float:
    return sum(t == p for t, p in zip(y_true, y_pred)) / len(y_true)


def per_class(y_true: Sequence[str], y_pred: Sequence[Optional[str]], labels: Sequence[str]) -> Dict[str, Dict[str, float]]:
    """Precision, recall, F1 and support for each label (0.0 when undefined)."""
    out = {}
    for c in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == c and p == c)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != c and p == c)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == c and p != c)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        out[c] = {"precision": precision, "recall": recall, "f1": f1, "support": tp + fn}
    return out


def macro_f1(y_true: Sequence[str], y_pred: Sequence[Optional[str]], labels: Sequence[str]) -> float:
    scores = per_class(y_true, y_pred, labels)
    return sum(s["f1"] for s in scores.values()) / len(labels)


def confusion(y_true: Sequence[str], y_pred: Sequence[Optional[str]], labels: Sequence[str]) -> Dict[str, Dict[str, int]]:
    """Rows: true label; columns: predicted label (None = missing prediction)."""
    cols = list(labels) + ([None] if None in y_pred else [])
    return {t: {str(p): sum(1 for a, b in zip(y_true, y_pred) if a == t and b == p) for p in cols} for t in labels}


def bootstrap_ci(
    y_true: Sequence[str],
    y_pred: Sequence[Optional[str]],
    metric: Callable[[List[str], List[Optional[str]]], float],
    n_boot: int = 1000,
    seed: int = 0,
    alpha: float = 0.05,
) -> List[float]:
    """Percentile bootstrap interval of `metric`, resampling items with replacement."""
    rng = random.Random(seed)
    n = len(y_true)
    values = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        values.append(metric([y_true[i] for i in idx], [y_pred[i] for i in idx]))
    values.sort()
    lo = values[int((alpha / 2) * n_boot)]
    hi = values[int((1 - alpha / 2) * n_boot) - 1]
    return [lo, hi]


def summarize(
    y_true: Sequence[str],
    y_pred: Sequence[Optional[str]],
    labels: Sequence[str],
    n_boot: int = 1000,
    seed: int = 0,
) -> Dict[str, Any]:
    """Accuracy and macro-F1 with 95% bootstrap intervals, per-class scores, confusion matrix."""
    return {
        "n": len(y_true),
        "missing": sum(p is None for p in y_pred),
        "accuracy": accuracy(y_true, y_pred),
        "accuracy_ci95": bootstrap_ci(y_true, y_pred, accuracy, n_boot, seed),
        "macro_f1": macro_f1(y_true, y_pred, labels),
        "macro_f1_ci95": bootstrap_ci(y_true, y_pred, lambda t, p: macro_f1(t, p, labels), n_boot, seed),
        "per_class": per_class(y_true, y_pred, labels),
        "confusion": confusion(y_true, y_pred, labels),
    }
