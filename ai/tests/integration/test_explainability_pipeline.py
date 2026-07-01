"""Integration tests for the end-to-end SHAP explainability pipeline.

Verifies: real model → ExplanationService → LocalExplanation with feature contributions.
Requires model artifacts at models/latest/model.joblib.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from tests.integration.conftest import NEUTRAL_FEATURES


@pytest.mark.integration
def test_explanation_service_loads(model_path: Path) -> None:
    """ExplanationService initialises without error using the real model."""
    from explainability.services.explanation_service import ExplanationService

    svc = ExplanationService(model_path)
    assert svc is not None


@pytest.mark.integration
def test_explanation_returns_feature_contributions(model_path: Path) -> None:
    """explain() returns a LocalExplanation with positive and negative features."""
    import pandas as pd

    from explainability.services.explanation_service import ExplanationService

    svc = ExplanationService(model_path)
    df = pd.DataFrame([NEUTRAL_FEATURES])
    result = svc.explain(df, home_team="Arsenal", away_team="Chelsea")

    assert result is not None
    assert len(result.top_positive_features) > 0
    assert len(result.top_negative_features) > 0
    assert len(result.all_contributions) == 42


@pytest.mark.integration
def test_shap_values_are_finite(model_path: Path) -> None:
    """All SHAP values in the explanation are finite floats."""
    import math

    import pandas as pd

    from explainability.services.explanation_service import ExplanationService

    svc = ExplanationService(model_path)
    df = pd.DataFrame([NEUTRAL_FEATURES])
    result = svc.explain(df, home_team="Arsenal", away_team="Chelsea")

    for contrib in result.all_contributions:
        assert math.isfinite(
            contrib.shap_value
        ), f"Non-finite SHAP value for {contrib.feature_name}: {contrib.shap_value}"


@pytest.mark.integration
def test_positive_features_have_positive_shap(model_path: Path) -> None:
    """top_positive_features all have shap_value > 0."""
    import pandas as pd

    from explainability.services.explanation_service import ExplanationService

    svc = ExplanationService(model_path)
    df = pd.DataFrame([NEUTRAL_FEATURES])
    result = svc.explain(df, home_team="Arsenal", away_team="Chelsea")

    for feat in result.top_positive_features:
        assert feat.shap_value > 0, (
            f"{feat.feature_name} in top_positive_features "
            f"has shap_value={feat.shap_value}"
        )


@pytest.mark.integration
def test_negative_features_have_negative_shap(model_path: Path) -> None:
    """top_negative_features all have shap_value < 0."""
    import pandas as pd

    from explainability.services.explanation_service import ExplanationService

    svc = ExplanationService(model_path)
    df = pd.DataFrame([NEUTRAL_FEATURES])
    result = svc.explain(df, home_team="Arsenal", away_team="Chelsea")

    for feat in result.top_negative_features:
        assert feat.shap_value < 0, (
            f"{feat.feature_name} in top_negative_features "
            f"has shap_value={feat.shap_value}"
        )


@pytest.mark.integration
def test_explainability_latency_under_3s(model_path: Path) -> None:
    """Full SHAP explanation completes in under 3 seconds."""
    import pandas as pd

    from explainability.services.explanation_service import ExplanationService

    svc = ExplanationService(model_path)
    df = pd.DataFrame([NEUTRAL_FEATURES])

    start = time.perf_counter()
    svc.explain(df, home_team="Arsenal", away_team="Chelsea")
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 3000, f"Explanation took {elapsed_ms:.1f} ms (limit 3000 ms)"
