"""Tests for evaluation.metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from evaluation.metrics import compute_confusion_matrix, compute_metrics

_CLASSES = ["A", "D", "H"]


def _perfect_probs(labels: list[str], classes: list[str]) -> np.ndarray:
    """Return one-hot probability rows for given labels."""
    idx = {c: i for i, c in enumerate(classes)}
    probs = np.zeros((len(labels), len(classes)))
    for row, lbl in enumerate(labels):
        probs[row, idx[lbl]] = 1.0
    return probs


def test_perfect_predictions_give_accuracy_one() -> None:
    """Identical y_true and y_pred should yield accuracy 1.0."""
    y_true = pd.Series(["H", "H", "D", "A"])
    y_pred = np.array(["H", "H", "D", "A"])
    y_prob = _perfect_probs(list(y_pred), _CLASSES)
    m = compute_metrics(y_true, y_pred, y_prob, _CLASSES)
    assert m["accuracy"] == pytest.approx(1.0)


def test_metrics_keys_present() -> None:
    """compute_metrics returns all required metric keys."""
    y_true = pd.Series(["H", "D", "A", "H"])
    y_pred = np.array(["H", "D", "D", "H"])
    y_prob = _perfect_probs(list(y_pred), _CLASSES)
    m = compute_metrics(y_true, y_pred, y_prob, _CLASSES)
    required = {
        "accuracy",
        "precision_weighted",
        "recall_weighted",
        "f1_weighted",
        "log_loss",
        "roc_auc_ovr",
    }
    assert required.issubset(m.keys())


def test_confusion_matrix_shape() -> None:
    """Confusion matrix must be n_classes x n_classes."""
    y_true = pd.Series(["H", "D", "A", "H", "D"])
    y_pred = np.array(["H", "D", "A", "D", "D"])
    cm = compute_confusion_matrix(y_true, y_pred, _CLASSES)
    assert len(cm) == 3
    assert all(len(row) == 3 for row in cm)


def test_confusion_matrix_diagonal_on_perfect() -> None:
    """Perfect predictions produce a diagonal confusion matrix."""
    labels = ["H", "D", "A", "H", "D", "A"]
    y_true = pd.Series(labels)
    y_pred = np.array(labels)
    cm = compute_confusion_matrix(y_true, y_pred, _CLASSES)
    total = sum(cm[i][i] for i in range(3))
    assert total == len(labels)


def test_confusion_matrix_entries_are_ints() -> None:
    """All confusion matrix entries must be plain ints."""
    y_true = pd.Series(["H", "D", "A"])
    y_pred = np.array(["D", "D", "A"])
    cm = compute_confusion_matrix(y_true, y_pred, _CLASSES)
    for row in cm:
        for val in row:
            assert isinstance(val, int)
