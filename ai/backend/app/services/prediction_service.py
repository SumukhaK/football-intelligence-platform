"""Prediction service — bridges API requests to the AI inference layer."""

from __future__ import annotations

import pandas as pd

from backend.app.exceptions import FeatureMissingError
from backend.app.schemas.prediction import PredictionRequest, PredictionResponse


class PredictionService:
    """Wraps the AI MatchPredictor for use in FastAPI route handlers."""

    def __init__(self, predictor: object, model_version: str) -> None:
        """Initialise with an AI MatchPredictor and the active model version tag."""
        self._predictor = predictor
        self._model_version = model_version

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        """Run inference and return a structured prediction response.

        Raises FeatureMissingError if the request is missing required columns.
        """
        features = pd.DataFrame([request.features])
        try:
            # MatchPredictor.predict raises ValueError on missing columns.
            result = self._predictor.predict(  # type: ignore[attr-defined]
                features, request.home_team, request.away_team
            )
        except ValueError as exc:
            missing = _extract_missing(str(exc))
            raise FeatureMissingError(missing) from exc

        confidence = max(
            result.probability_home,
            result.probability_draw,
            result.probability_away,
        )
        return PredictionResponse(
            home_team=result.home_team,
            away_team=result.away_team,
            predicted_result=result.predicted_result,
            probability_home=result.probability_home,
            probability_draw=result.probability_draw,
            probability_away=result.probability_away,
            confidence=confidence,
            model_version=self._model_version,
        )


def _extract_missing(error_message: str) -> list[str]:
    """Parse missing feature names from a ValueError message."""
    if "Missing feature columns:" in error_message:
        rest = error_message.split("Missing feature columns:")[1].strip()
        return [c.strip(" []'\"") for c in rest.split(",") if c.strip(" []'\"")]
    return [error_message]
