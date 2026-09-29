"""Probability scoring, baselines and paired comparison for outcome models.

Implements the evaluation protocol in ADR 007: log loss and ranked
probability score (RPS) are primary, Brier score and accuracy secondary.
Bookmaker probabilities are a benchmark only and never a model input.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss

# RPS treats outcomes as ordered from the home side's point of view.
_ORDINAL = ["H", "D", "A"]
_ODDS_COLUMNS = {"H": "home_odds", "D": "draw_odds", "A": "away_odds"}

Labels = Sequence[str] | pd.Series | np.ndarray


@dataclass(frozen=True)
class BootstrapDelta:
    """Mean and 95% interval of metric(A) - metric(B) over paired resamples."""

    metric: str
    mean: float
    lower: float
    upper: float
    n_resamples: int


def ranked_probability_score(
    y_true: Labels, probs: np.ndarray, classes: list[str]
) -> float:
    """Return mean RPS over H, D, A, whatever order ``classes`` uses."""
    ordered = probs[:, [classes.index(c) for c in _ORDINAL]]
    outcome = _one_hot(y_true, _ORDINAL)
    diff = np.cumsum(ordered, axis=1) - np.cumsum(outcome, axis=1)
    return float(np.mean(np.sum(diff[:, :-1] ** 2, axis=1) / (len(_ORDINAL) - 1)))


def brier_score(y_true: Labels, probs: np.ndarray, classes: list[str]) -> float:
    """Return the mean multiclass Brier score."""
    return float(np.mean(np.sum((probs - _one_hot(y_true, classes)) ** 2, axis=1)))


def score_probabilities(
    y_true: Labels, probs: np.ndarray, classes: list[str]
) -> dict[str, float]:
    """Return n, log loss, RPS, Brier and accuracy for one set of forecasts."""
    labels = np.asarray(y_true)
    predicted = np.asarray(classes)[probs.argmax(axis=1)]
    return {
        "n": float(len(labels)),
        "log_loss": float(log_loss(labels, probs, labels=classes)),
        "rps": ranked_probability_score(labels, probs, classes),
        "brier": brier_score(labels, probs, classes),
        "accuracy": float(np.mean(predicted == labels)),
    }


def implied_probabilities(odds: pd.DataFrame, classes: list[str]) -> np.ndarray:
    """Convert decimal odds to probabilities, normalising away the overround.

    Raises:
        ValueError: If any odds are missing or not greater than 1.
    """
    raw = odds[[_ODDS_COLUMNS[c] for c in classes]].to_numpy(dtype=float)
    if np.isnan(raw).any():
        raise ValueError("Odds are missing for some rows; filter them first")
    if (raw <= 1.0).any():
        raise ValueError("Decimal odds must be greater than 1")
    inverse = 1.0 / raw
    return np.asarray(inverse / inverse.sum(axis=1, keepdims=True))


def class_prior_probabilities(
    y_train: pd.Series, n_rows: int, classes: list[str]
) -> np.ndarray:
    """Forecast every row with the training-set outcome frequencies."""
    freq = y_train.value_counts(normalize=True)
    row = np.array([float(freq.get(c, 0.0)) for c in classes])
    return np.tile(row, (n_rows, 1))


def paired_bootstrap_delta(
    y_true: Labels,
    probs_a: np.ndarray,
    probs_b: np.ndarray,
    classes: list[str],
    metric: str = "log_loss",
    n_resamples: int = 2000,
    seed: int = 42,
) -> BootstrapDelta:
    """Bootstrap metric(A) - metric(B) on the same resampled rows.

    A negative delta means forecast A scores better (lower) than B.
    """
    labels = np.asarray(y_true)
    score = _METRICS[metric]
    rng = np.random.default_rng(seed)
    n = len(labels)
    deltas = np.empty(n_resamples)
    for i in range(n_resamples):
        idx = rng.integers(0, n, n)
        deltas[i] = score(labels[idx], probs_a[idx], classes) - score(
            labels[idx], probs_b[idx], classes
        )
    lower, upper = np.percentile(deltas, [2.5, 97.5])
    return BootstrapDelta(
        metric=metric,
        mean=float(deltas.mean()),
        lower=float(lower),
        upper=float(upper),
        n_resamples=n_resamples,
    )


def _log_loss(y: Labels, probs: np.ndarray, classes: list[str]) -> float:
    """Log loss with explicit labels, so resamples missing a class still work."""
    return float(log_loss(np.asarray(y), probs, labels=classes))


_METRICS: dict[str, Callable[[Labels, np.ndarray, list[str]], float]] = {
    "log_loss": _log_loss,
    "rps": ranked_probability_score,
    "brier": brier_score,
}


def _one_hot(y_true: Labels, classes: list[str]) -> np.ndarray:
    """Return a one-hot matrix of ``y_true`` over ``classes``."""
    labels = np.asarray(y_true)
    matches: np.ndarray = labels[:, None] == np.asarray(classes)[None, :]
    return matches.astype(float)
