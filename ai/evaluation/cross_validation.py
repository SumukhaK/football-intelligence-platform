"""Time-series cross-validation for the match outcome model.

``run_cross_validation`` uses row-based ``TimeSeriesSplit`` (ADR 003);
``run_season_cross_validation`` walks forward one season at a time (ADR 007).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score
from sklearn.metrics import log_loss as _log_loss
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import LabelEncoder

from training.configuration import TrainingConfig


@dataclass(frozen=True)
class CVFoldResult:
    """Metrics for a single cross-validation fold."""

    fold: int
    train_size: int
    val_size: int
    accuracy: float
    f1_weighted: float
    log_loss: float


@dataclass(frozen=True)
class CVSummary:
    """Aggregated metrics across all cross-validation folds."""

    n_folds: int
    fold_results: list[CVFoldResult]
    mean_accuracy: float
    std_accuracy: float
    mean_f1: float
    std_f1: float
    mean_log_loss: float
    std_log_loss: float


def run_cross_validation(
    X: pd.DataFrame,
    y: pd.Series,
    config: TrainingConfig,
) -> CVSummary:
    """Run TimeSeriesSplit CV and return aggregated metrics."""
    label_encoder = LabelEncoder()
    y_enc: np.ndarray = label_encoder.fit_transform(y)
    n_classes = len(label_encoder.classes_)
    tscv = TimeSeriesSplit(n_splits=config.cv_folds)
    folds = [
        _fit_fold(i + 1, X, y_enc, tr, vl, n_classes, config)
        for i, (tr, vl) in enumerate(tscv.split(X))
    ]
    return _summarise(folds, config.cv_folds)


def run_season_cross_validation(
    X: pd.DataFrame,
    y: pd.Series,
    seasons: pd.Series,
    config: TrainingConfig,
) -> CVSummary:
    """Walk-forward CV by season: fold k trains on all earlier seasons.

    The last ``config.cv_folds`` seasons each serve once as the validation
    season. Rows must be in date order.

    Raises:
        ValueError: If there are not more seasons than folds.
    """
    ordered = list(dict.fromkeys(seasons))
    if len(ordered) <= config.cv_folds:
        raise ValueError(
            f"Need more than {config.cv_folds} seasons for season CV, "
            f"got {len(ordered)}"
        )
    label_encoder = LabelEncoder()
    y_enc: np.ndarray = label_encoder.fit_transform(y)
    n_classes = len(label_encoder.classes_)
    season_values = seasons.to_numpy()
    folds = []
    for i, val_season in enumerate(ordered[-config.cv_folds :]):
        earlier = ordered[: ordered.index(val_season)]
        tr = np.flatnonzero(np.isin(season_values, earlier))
        vl = np.flatnonzero(season_values == val_season)
        folds.append(_fit_fold(i + 1, X, y_enc, tr, vl, n_classes, config))
    return _summarise(folds, config.cv_folds)


def _fit_fold(
    fold: int,
    X: pd.DataFrame,
    y_enc: np.ndarray,
    train_idx: np.ndarray,
    val_idx: np.ndarray,
    n_classes: int,
    config: TrainingConfig,
) -> CVFoldResult:
    """Train on one fold's training rows and score its validation rows."""
    imputer = SimpleImputer(strategy="median")
    X_tr_imp = imputer.fit_transform(X.iloc[train_idx])
    X_vl_imp = imputer.transform(X.iloc[val_idx])
    y_tr, y_vl = y_enc[train_idx], y_enc[val_idx]
    booster = xgb.XGBClassifier(
        objective="multi:softprob",
        num_class=n_classes,
        learning_rate=config.learning_rate,
        max_depth=config.max_depth,
        n_estimators=config.n_estimators,
        subsample=config.subsample,
        colsample_bytree=config.colsample_bytree,
        random_state=config.random_seed,
        verbosity=0,
    )
    booster.fit(X_tr_imp, y_tr, verbose=False)
    y_pred = booster.predict(X_vl_imp)
    y_prob = booster.predict_proba(X_vl_imp)
    return CVFoldResult(
        fold=fold,
        train_size=len(train_idx),
        val_size=len(val_idx),
        accuracy=float(accuracy_score(y_vl, y_pred)),
        f1_weighted=float(f1_score(y_vl, y_pred, average="weighted", zero_division=0)),
        log_loss=float(_log_loss(y_vl, y_prob, labels=list(range(n_classes)))),
    )


def _summarise(fold_results: list[CVFoldResult], n_folds: int) -> CVSummary:
    """Aggregate fold metrics into a CVSummary."""
    accs = np.array([r.accuracy for r in fold_results])
    f1s = np.array([r.f1_weighted for r in fold_results])
    lls = np.array([r.log_loss for r in fold_results])
    return CVSummary(
        n_folds=n_folds,
        fold_results=fold_results,
        mean_accuracy=float(accs.mean()),
        std_accuracy=float(accs.std()),
        mean_f1=float(f1s.mean()),
        std_f1=float(f1s.std()),
        mean_log_loss=float(lls.mean()),
        std_log_loss=float(lls.std()),
    )
