"""Explanation service — bridges API requests to the AI SHAP layer."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from backend.app.exceptions import FeatureMissingError
from backend.app.schemas.explainability import (
    ExplanationResponse,
    FeatureContributionSchema,
)
from explainability.feature_labels import describe_feature


class ExplanationService:
    """Wraps the AI ExplanationService for use in FastAPI route handlers."""

    def __init__(
        self,
        ai_service: object,
        model_version: str,
        dataset_version: str,
    ) -> None:
        """Initialise with the AI explanation service and version metadata."""
        self._ai_service = ai_service
        self._model_version = model_version
        self._dataset_version = dataset_version

    def explain(
        self,
        home_team: str,
        away_team: str,
        features: dict[str, float],
    ) -> ExplanationResponse:
        """Compute a SHAP explanation and return a structured response.

        Raises FeatureMissingError if required feature columns are absent.
        """
        feature_df = pd.DataFrame([features])
        try:
            result = self._ai_service.explain(  # type: ignore[attr-defined]
                feature_df,
                home_team,
                away_team,
                model_version=self._model_version,
                dataset_version=self._dataset_version,
            )
        except ValueError as exc:
            missing = _extract_missing(str(exc))
            raise FeatureMissingError(missing) from exc

        return ExplanationResponse(
            home_team=result.home_team,
            away_team=result.away_team,
            predicted_result=result.predicted_result,
            probability_home=result.probability_home,
            probability_draw=result.probability_draw,
            probability_away=result.probability_away,
            confidence=result.confidence,
            top_positive_features=_contributions(
                result.top_positive_features, home_team, away_team
            ),
            top_negative_features=_contributions(
                result.top_negative_features, home_team, away_team
            ),
            all_contributions=_contributions(
                result.all_contributions, home_team, away_team
            ),
            model_version=result.model_version,
            feature_version=result.feature_version,
            dataset_version=result.dataset_version,
            explanation_timestamp=result.explanation_timestamp,
        )


def _contributions(
    features: Iterable[Any], home_team: str, away_team: str
) -> list[FeatureContributionSchema]:
    """Build contributions with fan-friendly labels for a list of features."""
    return [_contribution(f, home_team, away_team) for f in features]


def _contribution(
    feature: Any, home_team: str, away_team: str
) -> FeatureContributionSchema:
    """Build one contribution with its fan-friendly label and value."""
    name = str(feature.feature_name)
    value = float(feature.feature_value)
    display_name, display_value = describe_feature(name, value, home_team, away_team)
    return FeatureContributionSchema(
        feature_name=name,
        feature_value=value,
        shap_value=float(feature.shap_value),
        display_name=display_name,
        display_value=display_value,
    )


def _extract_missing(error_message: str) -> list[str]:
    """Parse missing feature names from a ValueError message."""
    if "Missing feature columns:" in error_message:
        rest = error_message.split("Missing feature columns:")[1].strip()
        return [c.strip(" []'\"") for c in rest.split(",") if c.strip(" []'\"")]
    return [error_message]
