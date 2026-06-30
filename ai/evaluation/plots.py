"""Matplotlib plots for model evaluation — always uses the Agg backend."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # non-interactive, safe for headless environments
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import ConfusionMatrixDisplay


def save_confusion_matrix(
    y_true: pd.Series | np.ndarray,
    y_pred: np.ndarray,
    classes: list[str],
    output_path: Path,
) -> None:
    """Save a confusion matrix PNG to output_path."""
    fig, ax = plt.subplots(figsize=(7, 6))
    ConfusionMatrixDisplay.from_predictions(
        y_true,
        y_pred,
        labels=classes,
        display_labels=classes,
        ax=ax,
        colorbar=False,
    )
    ax.set_title("Confusion Matrix — Match Outcome Prediction")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def save_feature_importance(
    booster: xgb.XGBClassifier,
    feature_names: list[str],
    output_path: Path,
    top_n: int = 20,
) -> None:
    """Save a horizontal bar chart of the top-N XGBoost feature importances."""
    importances = booster.feature_importances_
    importance_df = (
        pd.DataFrame({"feature": feature_names, "importance": importances})
        .sort_values("importance", ascending=False)
        .head(top_n)
    )

    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(
        importance_df["feature"].tolist()[::-1],
        importance_df["importance"].tolist()[::-1],
    )
    ax.set_xlabel("Feature Importance (weight)")
    ax.set_title(f"Top {top_n} Feature Importances — XGBoost")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
