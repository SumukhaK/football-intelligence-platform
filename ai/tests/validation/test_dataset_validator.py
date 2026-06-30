"""Tests for DatasetValidator and validation rules."""

import pandas as pd
import pytest

from validation.dataset_validator import (
    DatasetValidator,
    DuplicateRowRule,
    NullConstraintRule,
    RequiredColumnsRule,
    RowCountRule,
    ValidationResult,
)


@pytest.fixture()
def validator() -> DatasetValidator:
    return DatasetValidator()


@pytest.fixture()
def clean_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2023-08-12", "2023-08-19"],
            "home_team": ["Arsenal", "Chelsea"],
            "away_team": ["Nottm Forest", "Liverpool"],
            "home_goals_ft": [2, 1],
            "away_goals_ft": [1, 1],
        }
    )


class TestValidationResult:
    def test_starts_as_passed(self) -> None:
        result = ValidationResult()
        assert result.passed is True
        assert result.errors == []

    def test_add_error_marks_as_failed(self) -> None:
        result = ValidationResult()
        result.add_error("something broke")
        assert result.passed is False
        assert "something broke" in result.errors

    def test_add_warning_does_not_fail(self) -> None:
        result = ValidationResult()
        result.add_warning("heads up")
        assert result.passed is True
        assert "heads up" in result.warnings


class TestRequiredColumnsRule:
    def test_passes_when_all_columns_present(self, clean_df: pd.DataFrame) -> None:
        rule = RequiredColumnsRule(["date", "home_team", "away_team"])
        assert rule.apply(clean_df) == []

    def test_fails_when_column_missing(self, clean_df: pd.DataFrame) -> None:
        rule = RequiredColumnsRule(["date", "home_team", "missing_col"])
        errors = rule.apply(clean_df)
        assert len(errors) == 1
        assert "missing_col" in errors[0]

    def test_fails_for_multiple_missing_columns(self) -> None:
        df = pd.DataFrame({"date": ["2023-01-01"]})
        rule = RequiredColumnsRule(["date", "home_team", "away_team"])
        errors = rule.apply(df)
        assert len(errors) == 1
        assert "home_team" in errors[0]
        assert "away_team" in errors[0]


class TestNullConstraintRule:
    def test_passes_when_no_nulls(self, clean_df: pd.DataFrame) -> None:
        rule = NullConstraintRule(["date", "home_team"])
        assert rule.apply(clean_df) == []

    def test_fails_when_column_has_nulls(self) -> None:
        df = pd.DataFrame(
            {"date": ["2023-08-12", None], "home_team": ["Arsenal", "Chelsea"]}
        )
        rule = NullConstraintRule(["date"])
        errors = rule.apply(df)
        assert len(errors) == 1
        assert "date" in errors[0]
        assert "1 null" in errors[0]

    def test_skips_column_not_in_dataframe(self, clean_df: pd.DataFrame) -> None:
        rule = NullConstraintRule(["nonexistent_column"])
        assert rule.apply(clean_df) == []


class TestDuplicateRowRule:
    def test_passes_when_no_duplicates(self, clean_df: pd.DataFrame) -> None:
        rule = DuplicateRowRule()
        assert rule.apply(clean_df) == []

    def test_fails_when_duplicates_exceed_threshold(self) -> None:
        df = pd.DataFrame(
            {
                "date": ["2023-08-12"] * 10,
                "home_team": ["Arsenal"] * 10,
            }
        )
        # 9 duplicates / 10 rows = 90%, well above default 1% threshold
        rule = DuplicateRowRule()
        errors = rule.apply(df)
        assert len(errors) == 1
        assert "90%" in errors[0] or "9" in errors[0]

    def test_passes_on_empty_dataframe(self) -> None:
        rule = DuplicateRowRule()
        assert rule.apply(pd.DataFrame()) == []

    def test_respects_custom_threshold(self) -> None:
        df = pd.DataFrame({"date": ["2023-08-12", "2023-08-12", "2023-08-13"]})
        # 1 duplicate / 3 rows = 33% — fails at 20% threshold but not at 50%
        rule_strict = DuplicateRowRule(max_ratio=0.20)
        rule_lenient = DuplicateRowRule(max_ratio=0.50)
        assert len(rule_strict.apply(df)) == 1
        assert len(rule_lenient.apply(df)) == 0


class TestRowCountRule:
    def test_passes_when_sufficient_rows(self, clean_df: pd.DataFrame) -> None:
        rule = RowCountRule(min_rows=2)
        assert rule.apply(clean_df) == []

    def test_fails_when_too_few_rows(self, clean_df: pd.DataFrame) -> None:
        rule = RowCountRule(min_rows=100)
        errors = rule.apply(clean_df)
        assert len(errors) == 1
        assert "100" in errors[0]


class TestDatasetValidator:
    def test_passes_all_rules(
        self, validator: DatasetValidator, clean_df: pd.DataFrame
    ) -> None:
        result = validator.validate(
            clean_df,
            [
                RequiredColumnsRule(["date", "home_team"]),
                NullConstraintRule(["date"]),
                DuplicateRowRule(),
            ],
        )
        assert result.passed is True
        assert result.errors == []

    def test_collects_all_errors(self, validator: DatasetValidator) -> None:
        df = pd.DataFrame({"date": [None, None]})
        result = validator.validate(
            df,
            [
                RequiredColumnsRule(["date", "home_team"]),
                NullConstraintRule(["date"]),
            ],
        )
        assert result.passed is False
        assert len(result.errors) == 2

    def test_empty_rules_list_passes(
        self, validator: DatasetValidator, clean_df: pd.DataFrame
    ) -> None:
        result = validator.validate(clean_df, [])
        assert result.passed is True
