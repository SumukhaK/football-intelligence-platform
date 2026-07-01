"""Metadata and report models for the feature engineering pipeline."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

PIPELINE_VERSION = "1.0.0"


class FeatureMetadata(BaseModel, frozen=True):
    """Describes the feature matrix produced by a pipeline run."""

    pipeline_version: str
    generation_timestamp: datetime
    source_dataset_version: str
    feature_names: list[str]
    feature_versions: dict[str, str]
    row_count: int
    column_count: int


class FeatureExecutionRecord(BaseModel, frozen=True):
    """Timing and output record for a single feature computation."""

    name: str
    version: str
    columns_produced: list[str]
    duration_seconds: float


class FeatureReport(BaseModel, frozen=True):
    """Full execution report for a feature engineering pipeline run."""

    pipeline_version: str
    generation_timestamp: datetime
    features_generated: list[FeatureExecutionRecord]
    total_duration_seconds: float
    input_row_count: int
    output_row_count: int
    output_column_count: int
    validation_passed: bool
    validation_errors: list[str]
    validation_warnings: list[str]
    dataset_statistics: dict[str, float]
