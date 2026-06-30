"""Reusable explanation service — FastAPI-agnostic.

Input:  a pd.DataFrame of pre-match features (one row per prediction request).
Output: a LocalExplanation Pydantic model with SHAP attributions.

The service caches the SHAP explainer by model file mtime to avoid
rebuilding it on every call within the same process.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from explainability.cache import ExplainerCache
from explainability.serializers import LocalExplanation, build_local_explanation
from training.persistence import load_model


class ExplanationService:
    """Loads a TrainedModel and provides per-prediction SHAP explanations."""

    def __init__(self, model_path: Path) -> None:
        """Initialise with path to a saved model.joblib file."""
        self._model_path = model_path
        self._model = load_model(model_path)
        version = str(model_path.stat().st_mtime)
        self._explainer = ExplainerCache.get_or_create(model_path, version)

    def explain(
        self,
        features: pd.DataFrame,
        home_team: str,
        away_team: str,
        match_index: int = 0,
        model_version: str = "unknown",
        feature_version: str = "unknown",
        dataset_version: str = "unknown",
    ) -> LocalExplanation:
        """Return a LocalExplanation for a single match row.

        Raises ValueError if required feature columns are missing.
        """
        missing = [c for c in self._model.feature_names if c not in features.columns]
        if missing:
            raise ValueError(f"Missing feature columns: {missing}")

        X = features[self._model.feature_names]
        X_imp = self._explainer.imputed_array(X)
        shap_values = self._explainer.shap_values(X)

        probs: np.ndarray = self._model.booster.predict_proba(X_imp)[0]
        pred_idx = int(np.argmax(probs))
        predicted_result = self._model.classes[pred_idx]

        class_to_idx = {c: i for i, c in enumerate(self._model.classes)}
        probability_home = float(probs[class_to_idx.get("H", 0)])
        probability_draw = float(probs[class_to_idx.get("D", 1)])
        probability_away = float(probs[class_to_idx.get("A", 2)])

        feature_values = X_imp[0].tolist()
        shap_row = shap_values[0]

        return build_local_explanation(
            match_index=match_index,
            home_team=home_team,
            away_team=away_team,
            predicted_result=predicted_result,
            probability_home=probability_home,
            probability_draw=probability_draw,
            probability_away=probability_away,
            shap_values_row=shap_row,
            feature_values=feature_values,
            feature_names=self._model.feature_names,
            classes=self._model.classes,
            n_top_features=10,
            model_version=model_version,
            feature_version=feature_version,
            dataset_version=dataset_version,
        )
