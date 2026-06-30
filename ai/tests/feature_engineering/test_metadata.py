"""Tests for feature engineering metadata models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from feature_engineering.metadata import (
    PIPELINE_VERSION,
    FeatureExecutionRecord,
    FeatureMetadata,
    FeatureReport,
)


def test_feature_metadata_constructs_correctly() -> None:
    """FeatureMetadata stores all fields and exposes them correctly."""
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    meta = FeatureMetadata(
        pipeline_version="1.0.0",
        generation_timestamp=now,
        source_dataset_version="20240101_120000",
        feature_names=["rolling_form", "goal_statistics"],
        feature_versions={"rolling_form": "1.0.0", "goal_statistics": "1.0.0"},
        row_count=380,
        column_count=25,
    )
    assert meta.pipeline_version == "1.0.0"
    assert meta.source_dataset_version == "20240101_120000"
    assert meta.row_count == 380
    assert meta.column_count == 25
    assert "rolling_form" in meta.feature_names
    assert meta.feature_versions["goal_statistics"] == "1.0.0"


def test_feature_metadata_is_frozen() -> None:
    """FeatureMetadata raises on attempted mutation (frozen Pydantic model)."""
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    meta = FeatureMetadata(
        pipeline_version="1.0.0",
        generation_timestamp=now,
        source_dataset_version="v1",
        feature_names=[],
        feature_versions={},
        row_count=0,
        column_count=0,
    )
    with pytest.raises(Exception):  # noqa: B017
        meta.row_count = 999  # type: ignore[misc]


def test_feature_report_constructs_correctly() -> None:
    """FeatureReport stores all fields correctly."""
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    record = FeatureExecutionRecord(
        name="rolling_form",
        version="1.0.0",
        columns_produced=["home_form_wins_last5"],
        duration_seconds=0.05,
    )
    report = FeatureReport(
        pipeline_version="1.0.0",
        generation_timestamp=now,
        features_generated=[record],
        total_duration_seconds=0.5,
        input_row_count=380,
        output_row_count=380,
        output_column_count=25,
        validation_passed=True,
        validation_errors=[],
        validation_warnings=[],
        dataset_statistics={"mean_home_goals": 1.5},
    )
    assert report.input_row_count == 380
    assert report.validation_passed is True
    assert len(report.features_generated) == 1
    assert report.features_generated[0].name == "rolling_form"


def test_pipeline_version_is_non_empty_string() -> None:
    """PIPELINE_VERSION is a non-empty string constant."""
    assert isinstance(PIPELINE_VERSION, str)
    assert len(PIPELINE_VERSION) > 0
