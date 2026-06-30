"""Configuration for the SHAP explainability pipeline."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExplainabilityConfig(BaseModel):
    """Frozen configuration for a single explainability pipeline run."""

    model_config = {"frozen": True}

    # Paths (relative to the cwd, or absolute when use_absolute_paths=True)
    model_path: str = "models/latest/model.joblib"
    feature_matrix_path: str = "datasets/features/feature_matrix.parquet"
    explanations_dir: str = "explanations"

    # Explanation depth
    n_top_features: int = Field(default=10, ge=1)
    n_local_samples: int = Field(default=10, ge=1)
    n_dependence_plots: int = Field(default=5, ge=1)
