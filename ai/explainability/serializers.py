"""Pydantic models and helper functions for serialising SHAP explanations."""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
from pydantic import BaseModel


class FeatureContribution(BaseModel):
    """SHAP contribution of a single feature to a single prediction."""

    model_config = {"frozen": True}

    feature_name: str
    feature_value: float
    shap_value: float


class LocalExplanation(BaseModel):
    """Full SHAP explanation for one match prediction."""

    model_config = {"frozen": True}

    match_index: int
    home_team: str
    away_team: str
    predicted_result: str
    probability_home: float
    probability_draw: float
    probability_away: float
    confidence: float
    top_positive_features: list[FeatureContribution]
    top_negative_features: list[FeatureContribution]
    all_contributions: list[FeatureContribution]
    model_version: str
    feature_version: str
    dataset_version: str
    explanation_timestamp: datetime


class GlobalSummary(BaseModel):
    """Aggregated SHAP summary across all samples."""

    model_config = {"frozen": True}

    model_version: str
    feature_version: str
    dataset_version: str
    n_samples: int
    n_features: int
    classes: list[str]
    mean_abs_shap_per_feature: dict[str, float]
    top_features_by_class: dict[str, list[FeatureContribution]]
    explanation_timestamp: datetime


def contributions_for_class(
    shap_values_for_class: np.ndarray,
    feature_values: list[float],
    feature_names: list[str],
) -> list[FeatureContribution]:
    """Build FeatureContribution list sorted by |SHAP| descending for one class."""
    contribs = [
        FeatureContribution(
            feature_name=name,
            feature_value=float(fv),
            shap_value=float(sv),
        )
        for name, fv, sv in zip(
            feature_names, feature_values, shap_values_for_class, strict=True
        )
    ]
    return sorted(contribs, key=lambda c: abs(c.shap_value), reverse=True)


def build_local_explanation(
    *,
    match_index: int,
    home_team: str,
    away_team: str,
    predicted_result: str,
    probability_home: float,
    probability_draw: float,
    probability_away: float,
    shap_values_row: np.ndarray,
    feature_values: list[float],
    feature_names: list[str],
    classes: list[str],
    n_top_features: int,
    model_version: str,
    feature_version: str,
    dataset_version: str,
) -> LocalExplanation:
    """Construct a LocalExplanation from a SHAP values row (n_features, n_classes)."""
    class_to_idx = {c: i for i, c in enumerate(classes)}
    pred_idx = class_to_idx.get(predicted_result, 0)
    shap_for_pred = shap_values_row[:, pred_idx]
    all_contribs = contributions_for_class(shap_for_pred, feature_values, feature_names)
    top_pos = [c for c in all_contribs if c.shap_value >= 0][:n_top_features]
    top_neg = [c for c in all_contribs if c.shap_value < 0][:n_top_features]
    confidence = max(probability_home, probability_draw, probability_away)
    return LocalExplanation(
        match_index=match_index,
        home_team=home_team,
        away_team=away_team,
        predicted_result=predicted_result,
        probability_home=probability_home,
        probability_draw=probability_draw,
        probability_away=probability_away,
        confidence=confidence,
        top_positive_features=top_pos,
        top_negative_features=top_neg,
        all_contributions=all_contribs,
        model_version=model_version,
        feature_version=feature_version,
        dataset_version=dataset_version,
        explanation_timestamp=datetime.now(tz=UTC),
    )


def global_summary_from_shap(
    *,
    shap_values: np.ndarray,
    feature_names: list[str],
    classes: list[str],
    model_version: str,
    feature_version: str,
    dataset_version: str,
) -> GlobalSummary:
    """Build a GlobalSummary from full SHAP values (n_samples, n_features, n_classes)."""
    mean_abs = np.abs(shap_values).mean(axis=(0, 2))
    mean_abs_dict = {
        name: float(v) for name, v in zip(feature_names, mean_abs, strict=True)
    }

    top_by_class: dict[str, list[FeatureContribution]] = {}
    for i, cls in enumerate(classes):
        per_class_mean = np.abs(shap_values[:, :, i]).mean(axis=0)
        dummy_fv = [0.0] * len(feature_names)
        contribs = contributions_for_class(per_class_mean, dummy_fv, feature_names)
        top_by_class[cls] = contribs

    return GlobalSummary(
        model_version=model_version,
        feature_version=feature_version,
        dataset_version=dataset_version,
        n_samples=int(shap_values.shape[0]),
        n_features=len(feature_names),
        classes=classes,
        mean_abs_shap_per_feature=mean_abs_dict,
        top_features_by_class=top_by_class,
        explanation_timestamp=datetime.now(tz=UTC),
    )
