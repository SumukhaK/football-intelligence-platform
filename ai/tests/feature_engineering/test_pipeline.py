"""Tests for FeaturePipeline and build_default_registry."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from feature_engineering.pipeline import FeaturePipeline, build_default_registry

# ---------------------------------------------------------------------------
# build_default_registry tests
# ---------------------------------------------------------------------------


def test_build_default_registry_returns_all_nine_features() -> None:
    """build_default_registry() returns a registry with all 9 declared features."""
    registry = build_default_registry()
    expected_names = {
        "rolling_form",
        "goal_statistics",
        "home_advantage",
        "away_form",
        "rest_days",
        "head_to_head",
        "league_position",
        "elo_rating",
        "strength_of_schedule",
    }
    assert set(registry.names()) == expected_names


def test_build_default_registry_elo_before_strength_of_schedule() -> None:
    """Topological sort places elo_rating before strength_of_schedule."""
    registry = build_default_registry()
    ordered = registry.get_ordered()
    names = [f.name for f in ordered]
    assert names.index("elo_rating") < names.index("strength_of_schedule")


# ---------------------------------------------------------------------------
# FeaturePipeline.run() tests
# ---------------------------------------------------------------------------


def test_pipeline_run_creates_three_output_files(
    sample_matches: pd.DataFrame, tmp_path: Path
) -> None:
    """FeaturePipeline.run() creates the parquet, metadata json, and report json."""
    input_csv = tmp_path / "matches.csv"
    sample_matches.to_csv(input_csv, index=False)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    registry = build_default_registry()
    pipeline = FeaturePipeline(registry=registry)
    pipeline.run(input_path=input_csv, output_dir=output_dir)

    parquet_files = list(output_dir.glob("*.parquet"))
    metadata_files = list(output_dir.glob("*metadata*.json"))
    report_files = list(output_dir.glob("*report*.json"))

    assert len(parquet_files) >= 1, "Expected at least one parquet output file"
    assert len(metadata_files) >= 1, "Expected at least one metadata JSON file"
    assert len(report_files) >= 1, "Expected at least one report JSON file"


def test_pipeline_parquet_has_canonical_and_feature_columns(
    sample_matches: pd.DataFrame, tmp_path: Path
) -> None:
    """Output parquet includes both canonical columns and all feature columns."""
    input_csv = tmp_path / "matches.csv"
    sample_matches.to_csv(input_csv, index=False)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    registry = build_default_registry()
    pipeline = FeaturePipeline(registry=registry)
    pipeline.run(input_path=input_csv, output_dir=output_dir)

    parquet_file = next(output_dir.glob("*.parquet"))
    df_out = pd.read_parquet(parquet_file)

    # Canonical columns must be present
    canonical = [
        "match_date",
        "season",
        "competition",
        "home_team",
        "away_team",
        "full_time_home_goals",
        "full_time_away_goals",
        "result",
    ]
    for col in canonical:
        assert col in df_out.columns, f"Missing canonical column: {col}"

    # All declared feature columns must be present
    all_feature_cols: list[str] = []
    for feature in registry.get_ordered():
        all_feature_cols.extend(feature.output_columns)

    for col in all_feature_cols:
        assert col in df_out.columns, f"Missing feature column: {col}"


def test_pipeline_metadata_json_is_valid(
    sample_matches: pd.DataFrame, tmp_path: Path
) -> None:
    """Metadata JSON produced by the pipeline deserialises as a FeatureMetadata."""
    from feature_engineering.metadata import FeatureMetadata

    input_csv = tmp_path / "matches.csv"
    sample_matches.to_csv(input_csv, index=False)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    registry = build_default_registry()
    pipeline = FeaturePipeline(registry=registry)
    pipeline.run(input_path=input_csv, output_dir=output_dir)

    metadata_file = next(output_dir.glob("*metadata*.json"))
    raw = json.loads(metadata_file.read_text())
    meta = FeatureMetadata(**raw)
    assert meta.row_count > 0
    assert len(meta.feature_names) > 0


def test_pipeline_report_json_is_valid(
    sample_matches: pd.DataFrame, tmp_path: Path
) -> None:
    """Report JSON produced by the pipeline deserialises as a FeatureReport."""
    from feature_engineering.metadata import FeatureReport

    input_csv = tmp_path / "matches.csv"
    sample_matches.to_csv(input_csv, index=False)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    registry = build_default_registry()
    pipeline = FeaturePipeline(registry=registry)
    pipeline.run(input_path=input_csv, output_dir=output_dir)

    report_file = next(output_dir.glob("*report*.json"))
    raw = json.loads(report_file.read_text())
    report = FeatureReport(**raw)
    assert report.validation_passed


def test_pipeline_report_input_row_count_matches_input(
    sample_matches: pd.DataFrame, tmp_path: Path
) -> None:
    """Report's input_row_count equals the number of rows in the input CSV."""
    from feature_engineering.metadata import FeatureReport

    input_csv = tmp_path / "matches.csv"
    sample_matches.to_csv(input_csv, index=False)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    registry = build_default_registry()
    pipeline = FeaturePipeline(registry=registry)
    pipeline.run(input_path=input_csv, output_dir=output_dir)

    report_file = next(output_dir.glob("*report*.json"))
    raw = json.loads(report_file.read_text())
    report = FeatureReport(**raw)
    assert report.input_row_count == len(sample_matches)


def test_pipeline_run_on_empty_df_raises(tmp_path: Path) -> None:
    """Running the pipeline on an empty DataFrame raises a validation error."""
    import pandas as pd

    empty_df = pd.DataFrame(
        columns=[
            "match_date",
            "season",
            "competition",
            "home_team",
            "away_team",
            "full_time_home_goals",
            "full_time_away_goals",
            "result",
        ]
    )
    input_csv = tmp_path / "empty.csv"
    empty_df.to_csv(input_csv, index=False)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    registry = build_default_registry()
    pipeline = FeaturePipeline(registry=registry)
    with pytest.raises(ValueError):
        pipeline.run(input_path=input_csv, output_dir=output_dir)


def test_pipeline_feature_matrix_columns_match_all_output_columns(
    sample_matches: pd.DataFrame, tmp_path: Path
) -> None:
    """Parquet columns include every feature's output_columns — no gaps."""
    input_csv = tmp_path / "matches.csv"
    sample_matches.to_csv(input_csv, index=False)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    registry = build_default_registry()
    pipeline = FeaturePipeline(registry=registry)
    pipeline.run(input_path=input_csv, output_dir=output_dir)

    parquet_file = next(output_dir.glob("*.parquet"))
    df_out = pd.read_parquet(parquet_file)

    all_feature_cols: set[str] = set()
    for feature in registry.get_ordered():
        all_feature_cols.update(feature.output_columns)

    output_cols = set(df_out.columns)
    for col in all_feature_cols:
        assert col in output_cols, f"Feature column '{col}' missing from output parquet"
