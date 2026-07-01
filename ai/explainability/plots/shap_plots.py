"""Headless SHAP plot generation — all functions write PNG files via Matplotlib Agg.

Every function takes precomputed arrays and a file path.
No interactive display is ever shown.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # non-interactive, safe for headless environments
import matplotlib.pyplot as plt
import numpy as np
import shap


def save_summary_plot(
    shap_values: np.ndarray,
    feature_matrix: np.ndarray,
    feature_names: list[str],
    output_path: Path,
) -> None:
    """Write a SHAP beeswarm summary plot averaged over all classes."""
    mean_shap = shap_values.mean(axis=2)
    fig, ax = plt.subplots(figsize=(10, 8))
    shap.summary_plot(
        mean_shap,
        feature_matrix,
        feature_names=feature_names,
        show=False,
        plot_type="dot",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close("all")


def save_feature_importance_plot(
    shap_values: np.ndarray,
    feature_names: list[str],
    output_path: Path,
    top_n: int = 20,
) -> None:
    """Write a bar chart of mean absolute SHAP values averaged over all classes."""
    mean_abs = np.abs(shap_values).mean(axis=(0, 2))
    idx = np.argsort(mean_abs)[-top_n:]
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(
        [feature_names[i] for i in idx],
        mean_abs[idx],
    )
    ax.set_xlabel("Mean |SHAP value|")
    ax.set_title(f"Top {top_n} Features by Mean |SHAP| (all classes)")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def save_waterfall_plot(
    shap_values_row: np.ndarray,
    base_value: float,
    feature_values: list[float],
    feature_names: list[str],
    output_path: Path,
) -> None:
    """Write a SHAP waterfall plot for a single sample and class."""
    explanation = shap.Explanation(
        values=shap_values_row,
        base_values=base_value,
        data=np.array(feature_values),
        feature_names=feature_names,
    )
    fig, ax = plt.subplots(figsize=(10, 8))
    shap.waterfall_plot(explanation, show=False, max_display=15)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close("all")


def save_force_plot(
    shap_values_row: np.ndarray,
    base_value: float,
    feature_values: list[float],
    feature_names: list[str],
    output_path: Path,
) -> None:
    """Write a SHAP force plot for a single sample and class as a static PNG."""
    fig, ax = plt.subplots(figsize=(20, 3))
    shap.force_plot(
        base_value,
        shap_values_row,
        np.array(feature_values),
        feature_names=feature_names,
        matplotlib=True,
        show=False,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=100, bbox_inches="tight")
    plt.close("all")


def save_dependence_plot(
    feature_name: str,
    shap_values: np.ndarray,
    feature_values_matrix: np.ndarray,
    feature_names: list[str],
    output_path: Path,
) -> None:
    """Write a SHAP dependence plot for one feature averaged over all classes."""
    feat_idx = feature_names.index(feature_name)
    mean_shap = shap_values.mean(axis=2)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(
        feature_values_matrix[:, feat_idx],
        mean_shap[:, feat_idx],
        alpha=0.7,
        s=30,
    )
    ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    ax.set_xlabel(feature_name)
    ax.set_ylabel(f"SHAP value for {feature_name}")
    ax.set_title(f"SHAP Dependence: {feature_name}")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
