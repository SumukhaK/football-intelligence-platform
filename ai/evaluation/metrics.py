"""Pure functions for computing multiclass evaluation metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_metrics(
    y_true: pd.Series | np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    classes: list[str],
) -> dict[str, float]:
    """Compute accuracy, precision, recall, F1, log-loss, and ROC-AUC."""
    metrics: dict[str, float] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_weighted": float(
            precision_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
        "recall_weighted": float(
            recall_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
        "f1_weighted": float(
            f1_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
        "log_loss": float(log_loss(y_true, y_prob, labels=classes)),
    }
    try:
        metrics["roc_auc_ovr"] = float(
            roc_auc_score(y_true, y_prob, multi_class="ovr", labels=classes)
        )
    except ValueError:
        metrics["roc_auc_ovr"] = float("nan")
    return metrics


def compute_confusion_matrix(
    y_true: pd.Series | np.ndarray,
    y_pred: np.ndarray,
    classes: list[str],
) -> list[list[int]]:
    """Return the confusion matrix as a nested list of ints."""
    cm: np.ndarray = confusion_matrix(y_true, y_pred, labels=classes)
    result: list[list[int]] = [list(row) for row in cm.tolist()]
    return result
