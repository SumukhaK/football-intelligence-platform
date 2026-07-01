"""Integration tests for the end-to-end prediction pipeline.

Verifies: real model load → feature ingestion → prediction → structured output.
Requires model artifacts at models/latest/model.joblib.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from tests.integration.conftest import NEUTRAL_FEATURES


@pytest.mark.integration
def test_predictor_loads_from_disk(model_path: Path) -> None:
    """MatchPredictor.from_path loads without error."""
    from inference.predictor import MatchPredictor

    predictor = MatchPredictor.from_path(model_path)
    assert predictor is not None


@pytest.mark.integration
def test_predictor_returns_structured_result(real_predictor: Any) -> None:
    """predict() returns a MatchPrediction with all required fields."""
    from inference.predictor import MatchPrediction

    df = pd.DataFrame([NEUTRAL_FEATURES])
    result = real_predictor.predict(df, "Arsenal", "Chelsea")

    assert isinstance(result, MatchPrediction)
    assert result.home_team == "Arsenal"
    assert result.away_team == "Chelsea"
    assert result.predicted_result in ("H", "D", "A")
    assert 0.0 <= result.probability_home <= 1.0
    assert 0.0 <= result.probability_draw <= 1.0
    assert 0.0 <= result.probability_away <= 1.0


@pytest.mark.integration
def test_probabilities_sum_to_one(real_predictor: Any) -> None:
    """Predicted probabilities sum to approximately 1.0."""
    df = pd.DataFrame([NEUTRAL_FEATURES])
    result = real_predictor.predict(df, "Arsenal", "Chelsea")

    total = result.probability_home + result.probability_draw + result.probability_away
    assert abs(total - 1.0) < 0.001, f"Probabilities sum to {total}, expected ~1.0"


@pytest.mark.integration
def test_strong_home_team_favoured(real_predictor: Any) -> None:
    """Model assigns higher home-win probability when home Elo is much higher."""
    strong_home = dict(NEUTRAL_FEATURES)
    strong_home["home_elo_before"] = 1700.0
    strong_home["away_elo_before"] = 1300.0
    strong_home["home_form_wins_last5"] = 0.9
    strong_home["away_form_wins_last5"] = 0.1

    df = pd.DataFrame([strong_home])
    result = real_predictor.predict(df, "City", "Bottom")

    assert result.probability_home > result.probability_away, (
        f"Expected home to be favoured: home={result.probability_home:.3f}, "
        f"away={result.probability_away:.3f}"
    )


@pytest.mark.integration
def test_prediction_latency_under_500ms(real_predictor: Any) -> None:
    """Single prediction completes in under 500 ms."""
    df = pd.DataFrame([NEUTRAL_FEATURES])

    start = time.perf_counter()
    real_predictor.predict(df, "Arsenal", "Chelsea")
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 500, f"Prediction took {elapsed_ms:.1f} ms (limit 500 ms)"


@pytest.mark.integration
def test_missing_feature_raises(real_predictor: Any) -> None:
    """predict() raises ValueError when required features are absent."""
    df = pd.DataFrame([{"home_elo_before": 1500.0}])

    with pytest.raises(ValueError, match="Missing feature columns"):
        real_predictor.predict(df, "Arsenal", "Chelsea")
