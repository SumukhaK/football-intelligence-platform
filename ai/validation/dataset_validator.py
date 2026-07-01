"""DataFrame-level validation rules and orchestrator.

Rules are small, composable objects. Each rule inspects a DataFrame and
returns a list of error strings. An empty list means the rule passed.

Usage:
    validator = DatasetValidator()
    result = validator.validate(df, [
        RequiredColumnsRule(["date", "home_team", "away_team"]),
        NullConstraintRule(["date", "home_team", "away_team"]),
        DuplicateRowRule(max_ratio=0.01),
    ])
    if not result.passed:
        raise ValidationError("match_results", str(result.errors))
"""

from dataclasses import dataclass, field
from typing import Protocol

import pandas as pd

from shared.constants import MAX_DUPLICATE_RATIO


class ValidationRule(Protocol):
    """Protocol for DataFrame validation rules."""

    def apply(self, df: pd.DataFrame) -> list[str]:
        """Inspect ``df`` and return a list of error messages.

        An empty list means this rule passed.
        """
        ...


@dataclass
class ValidationResult:
    """Aggregate result of running a set of validation rules against a DataFrame."""

    passed: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Record a validation error and mark the result as failed."""
        self.errors.append(message)
        self.passed = False

    def add_warning(self, message: str) -> None:
        """Record a non-fatal warning (does not affect ``passed``)."""
        self.warnings.append(message)

    def __str__(self) -> str:
        lines = [f"ValidationResult(passed={self.passed})"]
        for e in self.errors:
            lines.append(f"  ERROR: {e}")
        for w in self.warnings:
            lines.append(f"  WARN:  {w}")
        return "\n".join(lines)


@dataclass(frozen=True)
class RequiredColumnsRule:
    """Fail if any required column is absent from the DataFrame."""

    required: list[str]

    def apply(self, df: pd.DataFrame) -> list[str]:
        missing = [c for c in self.required if c not in df.columns]
        if missing:
            return [f"Required columns missing: {missing}"]
        return []


@dataclass(frozen=True)
class NullConstraintRule:
    """Fail if any non-nullable column contains null values."""

    non_nullable: list[str]

    def apply(self, df: pd.DataFrame) -> list[str]:
        errors: list[str] = []
        for col in self.non_nullable:
            if col not in df.columns:
                continue
            null_count = int(df[col].isna().sum())
            if null_count > 0:
                errors.append(
                    f"Column '{col}' has {null_count} null value(s) "
                    f"({null_count / len(df):.1%} of rows)."
                )
        return errors


@dataclass(frozen=True)
class DuplicateRowRule:
    """Fail if the proportion of duplicate rows exceeds ``max_ratio``."""

    subset: list[str] | None = None
    max_ratio: float = MAX_DUPLICATE_RATIO

    def apply(self, df: pd.DataFrame) -> list[str]:
        if len(df) == 0:
            return []
        duplicate_mask = df.duplicated(subset=self.subset, keep="first")
        duplicate_count = int(duplicate_mask.sum())
        ratio = duplicate_count / len(df)
        if ratio > self.max_ratio:
            return [
                f"Duplicate rows: {duplicate_count} ({ratio:.1%}) exceeds "
                f"the allowed maximum of {self.max_ratio:.1%}."
            ]
        return []


@dataclass(frozen=True)
class RowCountRule:
    """Fail if the DataFrame has fewer rows than ``min_rows``."""

    min_rows: int

    def apply(self, df: pd.DataFrame) -> list[str]:
        if len(df) < self.min_rows:
            return [f"Dataset has {len(df)} row(s); expected at least {self.min_rows}."]
        return []


class DatasetValidator:
    """Orchestrates a list of validation rules against a DataFrame.

    Each rule is applied independently. All errors are collected before
    returning so the caller sees the full picture of what failed.
    """

    def validate(
        self, df: pd.DataFrame, rules: list[ValidationRule]
    ) -> ValidationResult:
        """Run ``rules`` against ``df`` and return an aggregate result.

        Args:
            df: DataFrame to validate.
            rules: Ordered list of rules to apply.

        Returns:
            ``ValidationResult`` with ``passed=True`` only if every rule passed.
        """
        result = ValidationResult()
        for rule in rules:
            for error in rule.apply(df):
                result.add_error(error)
        return result
