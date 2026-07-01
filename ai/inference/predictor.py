"""Inference layer: load a trained model and return structured predictions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from training.persistence import load_model
from training.trainer import TrainedModel


@dataclass(frozen=True)
class MatchPrediction:
    """Structured prediction result for a single match."""

    home_team: str
    away_team: str
    predicted_result: str
    probability_home: float
    probability_draw: float
    probability_away: float


class MatchPredictor:
    """Wraps a TrainedModel and returns typed predictions."""

    def __init__(self, model: TrainedModel) -> None:
        """Initialise with a pre-loaded TrainedModel."""
        self._model = model

    @classmethod
    def from_path(cls, model_path: Path) -> MatchPredictor:
        """Load a TrainedModel from a joblib file and wrap it."""
        return cls(load_model(model_path))

    def predict(
        self,
        features: pd.DataFrame,
        home_team: str,
        away_team: str,
    ) -> MatchPrediction:
        """Return a structured prediction for one match row."""
        missing = [c for c in self._model.feature_names if c not in features.columns]
        if missing:
            raise ValueError(f"Missing feature columns: {missing}")

        X = features[self._model.feature_names]
        X_imp = self._model.imputer.transform(X)
        probs: np.ndarray = self._model.booster.predict_proba(X_imp)[0]
        pred_idx = int(np.argmax(probs))
        predicted_result = self._model.classes[pred_idx]

        class_to_idx = {c: i for i, c in enumerate(self._model.classes)}
        return MatchPrediction(
            home_team=home_team,
            away_team=away_team,
            predicted_result=predicted_result,
            probability_home=float(probs[class_to_idx.get("H", 0)]),
            probability_draw=float(probs[class_to_idx.get("D", 1)]),
            probability_away=float(probs[class_to_idx.get("A", 2)]),
        )
