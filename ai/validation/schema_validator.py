"""Pydantic-schema-based column validation for DataFrames.

SchemaValidator checks that a DataFrame's column set is compatible with a
Pydantic model: every required field in the model must appear as a column.

This is intentionally separate from ``DatasetValidator`` — schema validation
answers "does this DataFrame match our contract?" while dataset validation
answers "does this data obey our quality rules?".
"""

import pandas as pd
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefinedType  # noqa: F401 (used in isinstance)

from validation.dataset_validator import ValidationResult


def _field_is_required(field_info: object) -> bool:
    """Return True if a Pydantic v2 FieldInfo has no default value."""
    if not isinstance(field_info, FieldInfo):
        return False
    return isinstance(field_info.default, PydanticUndefinedType)


class SchemaValidator:
    """Validates DataFrame columns against a Pydantic model schema.

    Checks:
    1. All required schema fields are present as DataFrame columns.
    2. Columns present in the DataFrame but absent from the schema produce
       warnings — they do not cause the result to fail.
    """

    def validate(
        self,
        df: pd.DataFrame,
        schema: type[BaseModel],
    ) -> ValidationResult:
        """Validate ``df`` columns against ``schema``.

        Args:
            df: DataFrame to validate.
            schema: Pydantic model whose fields define the expected columns.

        Returns:
            ``ValidationResult`` — fails if any required field is missing.
            Unknown columns produce warnings only.
        """
        result = ValidationResult()
        schema_fields = schema.model_fields
        schema_column_names = set(schema_fields)
        df_columns = set(df.columns)

        required = [
            name for name, info in schema_fields.items() if _field_is_required(info)
        ]
        missing_required = [f for f in required if f not in df_columns]
        if missing_required:
            result.add_error(
                f"Schema '{schema.__name__}' requires columns that are absent: "
                f"{missing_required}"
            )

        extra_columns = df_columns - schema_column_names
        if extra_columns:
            result.add_warning(
                f"DataFrame has columns not defined in schema '{schema.__name__}': "
                f"{sorted(extra_columns)}"
            )

        return result

    def validate_strict(
        self,
        df: pd.DataFrame,
        schema: type[BaseModel],
    ) -> ValidationResult:
        """Like ``validate`` but treats unknown columns as errors, not warnings."""
        result = self.validate(df, schema)
        if result.warnings:
            for warning in result.warnings:
                result.add_error(warning)
            result.warnings.clear()
        return result
