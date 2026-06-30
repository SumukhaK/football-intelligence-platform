"""SHAP TreeExplainer wrapper for the XGBoost match outcome model."""

from __future__ import annotations

import numpy as np
import pandas as pd
import shap

from training.trainer import TrainedModel


class SHAPExplainer:
    """Wraps shap.TreeExplainer for the XGBoost multi-class classifier.

    SHAP values have shape (n_samples, n_features, n_classes).
    The imputer is applied before every SHAP computation.
    """

    def __init__(self, model: TrainedModel) -> None:
        """Initialise with a TrainedModel; builds the TreeExplainer eagerly."""
        self._model = model
        self._explainer: shap.TreeExplainer = shap.TreeExplainer(model.booster)

    def imputed_array(self, X: pd.DataFrame) -> np.ndarray:
        """Return the imputed numpy array for X after column validation."""
        missing = [c for c in self._model.feature_names if c not in X.columns]
        if missing:
            raise ValueError(f"Missing feature columns: {missing}")
        X_ordered = X[self._model.feature_names]
        result: np.ndarray = self._model.imputer.transform(X_ordered)
        return result

    def shap_values(self, X: pd.DataFrame) -> np.ndarray:
        """Compute SHAP values; returns array shaped (n_samples, n_features, n_classes).

        Raises ValueError for an empty DataFrame or missing columns.
        """
        if len(X) == 0:
            raise ValueError("Cannot compute SHAP values for an empty DataFrame.")
        X_imp = self.imputed_array(X)
        raw = self._explainer.shap_values(X_imp)
        return _normalise_shap_output(raw, n_classes=len(self._model.classes))

    def expected_value(self) -> np.ndarray:
        """Return the base value array, shaped (n_classes,)."""
        ev = self._explainer.expected_value
        if isinstance(ev, (int, float)):
            return np.array([float(ev)] * len(self._model.classes))
        arr: np.ndarray = np.asarray(ev, dtype=np.float64)
        return arr


def _normalise_shap_output(raw: object, n_classes: int) -> np.ndarray:
    """Convert raw SHAP output to a uniform (n_samples, n_features, n_classes) array.

    shap.TreeExplainer may return:
    - list of (n_samples, n_features) arrays, one per class
    - 3D array (n_samples, n_features, n_classes)
    """
    if isinstance(raw, list):
        # Stack along the last axis: each element is (n_samples, n_features)
        stacked: np.ndarray = np.stack(raw, axis=-1)
        return stacked.astype(np.float64)
    arr = np.asarray(raw, dtype=np.float64)
    if arr.ndim == 2:
        # Single class or binary case — expand to 3D
        return arr[:, :, np.newaxis]
    return arr
