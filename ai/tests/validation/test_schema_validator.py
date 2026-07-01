"""Tests for SchemaValidator."""

import pandas as pd
import pytest
from pydantic import BaseModel

from validation.schema_validator import SchemaValidator


class MatchSchema(BaseModel):
    """Pydantic schema for testing — mirrors normalised match columns."""

    date: str
    home_team: str
    away_team: str
    home_goals_ft: int
    away_goals_ft: int
    result_ft: str | None = None


@pytest.fixture()
def validator() -> SchemaValidator:
    return SchemaValidator()


@pytest.fixture()
def valid_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2023-08-12"],
            "home_team": ["Arsenal"],
            "away_team": ["Nottm Forest"],
            "home_goals_ft": [2],
            "away_goals_ft": [1],
            "result_ft": ["H"],
        }
    )


class TestSchemaValidator:
    def test_passes_when_all_required_columns_present(
        self, validator: SchemaValidator, valid_df: pd.DataFrame
    ) -> None:
        result = validator.validate(valid_df, MatchSchema)
        assert result.passed is True

    def test_fails_when_required_column_missing(
        self, validator: SchemaValidator
    ) -> None:
        df = pd.DataFrame(
            {
                "date": ["2023-08-12"],
                "home_team": ["Arsenal"],
                # away_team and goals columns missing
            }
        )
        result = validator.validate(df, MatchSchema)
        assert result.passed is False
        assert any("away_team" in e for e in result.errors)

    def test_passes_when_optional_column_absent(
        self, validator: SchemaValidator
    ) -> None:
        df = pd.DataFrame(
            {
                "date": ["2023-08-12"],
                "home_team": ["Arsenal"],
                "away_team": ["Chelsea"],
                "home_goals_ft": [2],
                "away_goals_ft": [1],
                # result_ft is Optional — absence is acceptable
            }
        )
        result = validator.validate(df, MatchSchema)
        assert result.passed is True

    def test_warns_on_extra_columns(
        self, validator: SchemaValidator, valid_df: pd.DataFrame
    ) -> None:
        df = valid_df.copy()
        df["extra_column"] = "value"
        result = validator.validate(df, MatchSchema)
        assert result.passed is True
        assert any("extra_column" in w for w in result.warnings)

    def test_strict_mode_fails_on_extra_columns(
        self, validator: SchemaValidator, valid_df: pd.DataFrame
    ) -> None:
        df = valid_df.copy()
        df["extra_column"] = "value"
        result = validator.validate_strict(df, MatchSchema)
        assert result.passed is False
        assert any("extra_column" in e for e in result.errors)
