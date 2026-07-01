"""Validation for canonical input and generated feature matrices."""

from __future__ import annotations

import pandas as pd

from validation.dataset_validator import (
    DatasetValidator,
    NullConstraintRule,
    RequiredColumnsRule,
    RowCountRule,
    ValidationResult,
)

_REQUIRED_CANONICAL_COLUMNS: list[str] = [
    "match_date",
    "season",
    "competition",
    "home_team",
    "away_team",
    "full_time_home_goals",
    "full_time_away_goals",
    "result",
]

_VALID_RESULT_VALUES: set[str] = {"H", "D", "A"}


def validate_canonical_input(df: pd.DataFrame) -> ValidationResult:
    """Validate a canonical match DataFrame before feature engineering.

    Checks:
    - All required columns are present.
    - Required columns contain no null values.
    - At least 1 row is present.
    - ``result`` values are all in {"H", "D", "A"}.

    Args:
        df: DataFrame produced by the Stage 1 data pipeline.

    Returns:
        ``ValidationResult`` with errors and/or warnings.
    """
    validator = DatasetValidator()
    result = validator.validate(
        df,
        [
            RequiredColumnsRule(_REQUIRED_CANONICAL_COLUMNS),
            NullConstraintRule(_REQUIRED_CANONICAL_COLUMNS),
            RowCountRule(min_rows=1),
        ],
    )

    if "result" in df.columns and len(df) > 0:
        invalid_mask = ~df["result"].isin(_VALID_RESULT_VALUES)
        invalid_count = int(invalid_mask.sum())
        if invalid_count > 0:
            invalid_values = df.loc[invalid_mask, "result"].unique().tolist()
            result.add_error(
                f"Column 'result' has {invalid_count} invalid value(s): "
                f"{invalid_values}. Expected one of {sorted(_VALID_RESULT_VALUES)}."
            )

    return result


def validate_feature_matrix(
    df: pd.DataFrame,
    required_features: list[str],
) -> ValidationResult:
    """Validate a generated feature matrix DataFrame.

    Checks:
    - All required feature columns are present.
    - At least 1 row is present.
    - Warns for any feature column that is entirely NaN.

    Args:
        df: DataFrame output from the feature engineering pipeline.
        required_features: List of column names expected in the feature matrix.

    Returns:
        ``ValidationResult`` with errors and/or warnings.
    """
    validator = DatasetValidator()
    result = validator.validate(
        df,
        [
            RequiredColumnsRule(required_features),
            RowCountRule(min_rows=1),
        ],
    )

    for col in required_features:
        if col in df.columns and df[col].isna().all():
            result.add_warning(
                f"Feature column '{col}' is entirely NaN — "
                "check the feature implementation for this column."
            )

    return result
