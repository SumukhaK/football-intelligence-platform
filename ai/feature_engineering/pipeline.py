"""Feature engineering pipeline: canonical dataset → feature matrix."""

from __future__ import annotations

import argparse
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from feature_engineering.base import BaseFeature
from feature_engineering.features import (
    AwayFormFeature,
    EloRatingFeature,
    GoalStatisticsFeature,
    HeadToHeadFeature,
    HomeAdvantageFeature,
    LeaguePositionFeature,
    RestDaysFeature,
    RollingFormFeature,
    StrengthOfScheduleFeature,
)
from feature_engineering.metadata import (
    PIPELINE_VERSION,
    FeatureExecutionRecord,
    FeatureMetadata,
    FeatureReport,
)
from feature_engineering.registry import FeatureRegistry
from feature_engineering.validators import (
    validate_canonical_input,
    validate_feature_matrix,
)

_VERSION_RE = re.compile(r"match_results_v([^.]+)\.csv$")
_DEFAULT_INPUT_GLOB = "datasets/processed/football_data/match_results_v*.csv"
_DEFAULT_OUTPUT_DIR = "datasets/features"


def build_default_registry() -> FeatureRegistry:
    """Create a FeatureRegistry pre-loaded with all 9 standard features."""
    registry = FeatureRegistry()
    registry.register(RollingFormFeature())
    registry.register(GoalStatisticsFeature())
    registry.register(HomeAdvantageFeature())
    registry.register(AwayFormFeature())
    registry.register(RestDaysFeature())
    registry.register(HeadToHeadFeature())
    registry.register(LeaguePositionFeature())
    registry.register(EloRatingFeature())
    registry.register(StrengthOfScheduleFeature())
    return registry


def _extract_source_version(input_path: Path) -> str:
    """Extract version string from a canonical CSV filename.

    For example: ``match_results_v20260630_090657.csv`` → ``"20260630_090657"``.
    Falls back to ``"unknown"`` if the filename does not match the expected pattern.
    """
    match = _VERSION_RE.search(input_path.name)
    return match.group(1) if match else "unknown"


def _find_latest_input(cwd: Path) -> Path:
    """Find the most recently modified canonical CSV in the default location."""
    candidates = sorted(
        cwd.glob(_DEFAULT_INPUT_GLOB),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(
            f"No canonical CSV found matching '{_DEFAULT_INPUT_GLOB}' "
            f"relative to '{cwd}'."
        )
    return candidates[0]


def _compute_dataset_statistics(df: pd.DataFrame) -> dict[str, float]:
    """Compute summary statistics over numeric columns of the feature matrix."""
    numeric = df.select_dtypes(include="number")
    stats: dict[str, float] = {}
    if numeric.empty:
        return stats
    stats["total_nan_pct"] = float(numeric.isna().mean().mean())
    stats["row_count"] = float(len(df))
    stats["column_count"] = float(len(df.columns))
    return stats


class FeaturePipeline:
    """Orchestrates feature computation from a canonical CSV to a feature matrix."""

    def __init__(self, registry: FeatureRegistry | None = None) -> None:
        self._registry = registry or build_default_registry()

    def run(self, input_path: Path, output_dir: Path) -> FeatureReport:
        """Execute the full feature engineering pipeline.

        Steps:
        1. Load and sort the canonical CSV.
        2. Validate canonical input.
        3. Run each feature in dependency order, merging columns into the df.
        4. Validate the final feature matrix.
        5. Persist outputs: parquet, metadata JSON, report JSON.

        Args:
            input_path: Path to the canonical match results CSV.
            output_dir: Directory to write pipeline outputs.

        Returns:
            ``FeatureReport`` describing the pipeline run.
        """
        pipeline_start = time.monotonic()
        generation_timestamp = datetime.now(tz=UTC)
        source_version = _extract_source_version(input_path)

        # Step 1: Load and sort
        df = pd.read_csv(input_path)
        df = df.sort_values("match_date", ascending=True).reset_index(drop=True)
        input_row_count = len(df)

        # Step 2: Validate input
        input_validation = validate_canonical_input(df)
        if not input_validation.passed:
            raise ValueError(f"Canonical input validation failed:\n{input_validation}")

        # Step 3: Execute features
        ordered_features: list[BaseFeature] = self._registry.get_ordered()
        execution_records: list[FeatureExecutionRecord] = []
        all_output_columns: list[str] = []

        for feature in ordered_features:
            feature_start = time.monotonic()
            feature_df = feature.compute(df)
            duration = time.monotonic() - feature_start

            new_cols = [c for c in feature_df.columns if c not in df.columns]
            df = pd.concat([df, feature_df[new_cols]], axis=1)

            execution_records.append(
                FeatureExecutionRecord(
                    name=feature.name,
                    version=feature.version,
                    columns_produced=feature.output_columns,
                    duration_seconds=round(duration, 4),
                )
            )
            all_output_columns.extend(feature.output_columns)

        # Step 4: Validate feature matrix
        matrix_validation = validate_feature_matrix(df, all_output_columns)

        # Step 5: Persist outputs
        output_dir.mkdir(parents=True, exist_ok=True)

        parquet_path = output_dir / "feature_matrix.parquet"
        df.to_parquet(parquet_path, index=True)

        feature_versions = {f.name: f.version for f in ordered_features}
        metadata = FeatureMetadata(
            pipeline_version=PIPELINE_VERSION,
            generation_timestamp=generation_timestamp,
            source_dataset_version=source_version,
            feature_names=all_output_columns,
            feature_versions=feature_versions,
            row_count=len(df),
            column_count=len(df.columns),
        )
        metadata_path = output_dir / "feature_metadata.json"
        metadata_path.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")

        total_duration = time.monotonic() - pipeline_start
        report = FeatureReport(
            pipeline_version=PIPELINE_VERSION,
            generation_timestamp=generation_timestamp,
            features_generated=execution_records,
            total_duration_seconds=round(total_duration, 4),
            input_row_count=input_row_count,
            output_row_count=len(df),
            output_column_count=len(df.columns),
            validation_passed=matrix_validation.passed,
            validation_errors=matrix_validation.errors,
            validation_warnings=matrix_validation.warnings,
            dataset_statistics=_compute_dataset_statistics(df),
        )
        report_path = output_dir / "feature_generation_report.json"
        report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

        return report


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the feature engineering pipeline.

    Usage:
        python -m feature_engineering.pipeline [--input PATH] [--output-dir DIR]
    """
    parser = argparse.ArgumentParser(
        description="Run the football feature engineering pipeline.",
        prog="feature_engineering.pipeline",
    )
    parser.add_argument(
        "--input",
        metavar="PATH",
        help=(
            "Path to the canonical match results CSV. "
            f"Defaults to the latest file matching '{_DEFAULT_INPUT_GLOB}'."
        ),
    )
    parser.add_argument(
        "--output-dir",
        metavar="DIR",
        default=_DEFAULT_OUTPUT_DIR,
        help=f"Output directory. Defaults to '{_DEFAULT_OUTPUT_DIR}'.",
    )
    args = parser.parse_args(argv)

    cwd = Path.cwd()

    if args.input:
        input_path = Path(args.input)
    else:
        try:
            input_path = _find_latest_input(cwd)
        except FileNotFoundError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = cwd / output_dir

    print(f"Input:      {input_path}")
    print(f"Output dir: {output_dir}")

    try:
        pipeline = FeaturePipeline()
        report = pipeline.run(input_path, output_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    status = "PASSED" if report.validation_passed else "FAILED"
    print(f"\nPipeline complete in {report.total_duration_seconds:.2f}s")
    print(f"Rows: {report.input_row_count} in -> {report.output_row_count} out")
    print(f"Feature columns: {report.output_column_count}")
    print(f"Validation: {status}")

    if report.validation_errors:
        for err in report.validation_errors:
            print(f"  ERROR: {err}", file=sys.stderr)

    if report.validation_warnings:
        for warn in report.validation_warnings:
            print(f"  WARN:  {warn}")

    print(f"\nOutputs written to: {output_dir}")
    return 0 if report.validation_passed else 1


if __name__ == "__main__":
    sys.exit(main())
