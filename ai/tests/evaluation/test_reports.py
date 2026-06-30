"""Tests for evaluation.reports Pydantic models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from evaluation.reports import (
    CVReport,
    EvaluationReport,
    FoldResult,
    SplitMetrics,
)


def _make_split_metrics() -> SplitMetrics:
    """Return a valid SplitMetrics instance."""
    return SplitMetrics(
        accuracy=0.5,
        precision_weighted=0.5,
        recall_weighted=0.5,
        f1_weighted=0.5,
        log_loss=1.0,
        roc_auc_ovr=0.6,
        confusion_matrix=[[5, 2, 1], [1, 4, 2], [1, 1, 5]],
    )


def _make_cv_report() -> CVReport:
    """Return a valid CVReport instance."""
    return CVReport(
        n_folds=3,
        fold_results=[
            FoldResult(
                fold=i + 1,
                train_size=40,
                val_size=10,
                accuracy=0.5,
                f1_weighted=0.5,
                log_loss=1.0,
            )
            for i in range(3)
        ],
        mean_accuracy=0.5,
        std_accuracy=0.02,
        mean_f1=0.5,
        std_f1=0.02,
        mean_log_loss=1.0,
        std_log_loss=0.05,
    )


def test_split_metrics_constructs() -> None:
    """SplitMetrics must construct without error."""
    m = _make_split_metrics()
    assert m.accuracy == 0.5


def test_split_metrics_is_frozen() -> None:
    """SplitMetrics must be immutable."""
    m = _make_split_metrics()
    with pytest.raises(Exception):  # noqa: B017
        m.accuracy = 0.9


def test_evaluation_report_constructs() -> None:
    """EvaluationReport must construct with all required fields."""
    sm = _make_split_metrics()
    cv = _make_cv_report()
    report = EvaluationReport(
        model_version="20240101_120000",
        evaluation_timestamp=datetime.now(tz=UTC),
        train_metrics=sm,
        val_metrics=sm,
        test_metrics=sm,
        cv_report=cv,
        classes=["A", "D", "H"],
        n_features=8,
        n_train=60,
        n_val=15,
        n_test=15,
    )
    assert report.n_features == 8
    assert len(report.classes) == 3


def test_evaluation_report_serialises() -> None:
    """EvaluationReport.model_dump_json() produces valid JSON."""
    import json

    sm = _make_split_metrics()
    cv = _make_cv_report()
    report = EvaluationReport(
        model_version="v1",
        evaluation_timestamp=datetime.now(tz=UTC),
        train_metrics=sm,
        val_metrics=sm,
        test_metrics=sm,
        cv_report=cv,
        classes=["A", "D", "H"],
        n_features=4,
        n_train=40,
        n_val=10,
        n_test=10,
    )
    parsed = json.loads(report.model_dump_json())
    assert parsed["model_version"] == "v1"
    assert "test_metrics" in parsed
