"""Tests for inference.predictor."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from inference.predictor import MatchPrediction, MatchPredictor
from training.configuration import TrainingConfig
from training.persistence import save_model
from training.splitter import ChronologicalSplitter, get_feature_columns
from training.trainer import ModelTrainer, TrainedModel


def _make_feature_matrix(n: int = 80, seed: int = 0) -> pd.DataFrame:
    """Minimal feature matrix for inference tests."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2023-08-01", periods=n, freq="7D")
    return pd.DataFrame(
        {
            "match_date": dates,
            "season": "2023/24",
            "competition": "Premier League",
            "home_team": rng.choice(["Arsenal", "Chelsea"], size=n),
            "away_team": rng.choice(["Liverpool", "City"], size=n),
            "result": rng.choice(["H", "D", "A"], size=n),
            "feat_a": rng.random(n),
            "feat_b": rng.random(n),
        }
    )


@pytest.fixture()
def _trained() -> TrainedModel:
    """Trained model for inference tests."""
    df = _make_feature_matrix()
    config = TrainingConfig(n_estimators=10, cv_folds=3, early_stopping_rounds=3)
    cols = get_feature_columns(df, config)
    split = ChronologicalSplitter().split(df, cols, config)
    return ModelTrainer().train(split, config)


@pytest.fixture()
def _predictor(_trained: TrainedModel) -> MatchPredictor:
    """MatchPredictor wrapping the trained model."""
    return MatchPredictor(_trained)


def _one_row_features(model: TrainedModel) -> pd.DataFrame:
    """Return a single-row DataFrame with correct feature columns (all zeros)."""
    return pd.DataFrame([dict.fromkeys(model.feature_names, 0.0)])


def test_predict_returns_match_prediction(
    _predictor: MatchPredictor, _trained: TrainedModel
) -> None:
    """predict() must return a MatchPrediction dataclass."""
    features = _one_row_features(_trained)
    result = _predictor.predict(features, "Arsenal", "Chelsea")
    assert isinstance(result, MatchPrediction)


def test_predict_team_names_preserved(
    _predictor: MatchPredictor, _trained: TrainedModel
) -> None:
    """home_team and away_team must be passed through unchanged."""
    features = _one_row_features(_trained)
    result = _predictor.predict(features, "Arsenal", "Chelsea")
    assert result.home_team == "Arsenal"
    assert result.away_team == "Chelsea"


def test_predict_probabilities_sum_to_one(
    _predictor: MatchPredictor, _trained: TrainedModel
) -> None:
    """Home + draw + away probabilities must sum to 1."""
    features = _one_row_features(_trained)
    result = _predictor.predict(features, "Arsenal", "Chelsea")
    total = result.probability_home + result.probability_draw + result.probability_away
    assert abs(total - 1.0) < 1e-5


def test_predict_result_is_valid_class(
    _predictor: MatchPredictor, _trained: TrainedModel
) -> None:
    """predicted_result must be one of the known classes."""
    features = _one_row_features(_trained)
    result = _predictor.predict(features, "Arsenal", "Chelsea")
    assert result.predicted_result in {"H", "D", "A"}


def test_predict_missing_column_raises(
    _predictor: MatchPredictor, _trained: TrainedModel
) -> None:
    """Missing feature columns must raise ValueError."""
    features = pd.DataFrame([{"wrong_col": 0.0}])
    with pytest.raises(ValueError, match="Missing feature columns"):
        _predictor.predict(features, "Arsenal", "Chelsea")


def test_from_path_roundtrip(_trained: TrainedModel, tmp_path: Path) -> None:
    """from_path must load a saved model and produce the same prediction."""
    model_path = tmp_path / "model.joblib"
    save_model(_trained, model_path)

    predictor_a = MatchPredictor(_trained)
    predictor_b = MatchPredictor.from_path(model_path)

    features = _one_row_features(_trained)
    result_a = predictor_a.predict(features, "A", "B")
    result_b = predictor_b.predict(features, "A", "B")
    assert result_a.predicted_result == result_b.predicted_result
