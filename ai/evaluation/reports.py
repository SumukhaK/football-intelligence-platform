"""Pydantic models for structured evaluation reports."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class FoldResult(BaseModel):
    """Metrics for a single cross-validation fold."""

    model_config = {"frozen": True}

    fold: int
    train_size: int
    val_size: int
    accuracy: float
    f1_weighted: float
    log_loss: float


class CVReport(BaseModel):
    """Aggregated cross-validation metrics."""

    model_config = {"frozen": True}

    n_folds: int
    fold_results: list[FoldResult]
    mean_accuracy: float
    std_accuracy: float
    mean_f1: float
    std_f1: float
    mean_log_loss: float
    std_log_loss: float


class SplitMetrics(BaseModel):
    """Evaluation metrics for a single data split (train/val/test)."""

    model_config = {"frozen": True}

    accuracy: float
    precision_weighted: float
    recall_weighted: float
    f1_weighted: float
    log_loss: float
    roc_auc_ovr: float
    confusion_matrix: list[list[int]]


class EvaluationReport(BaseModel):
    """Full evaluation report covering all splits and cross-validation."""

    model_config = {"frozen": True}

    model_version: str
    evaluation_timestamp: datetime
    train_metrics: SplitMetrics
    val_metrics: SplitMetrics
    test_metrics: SplitMetrics
    cv_report: CVReport
    classes: list[str]
    n_features: int
    n_train: int
    n_val: int
    n_test: int
