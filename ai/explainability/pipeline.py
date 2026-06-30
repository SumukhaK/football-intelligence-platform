"""Explainability pipeline: load model → compute SHAP → persist artifacts.

Run from the repository root:
    uv run python -m explainability.pipeline
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from explainability.cache import ExplainerCache
from explainability.configuration import ExplainabilityConfig
from explainability.plots.shap_plots import (
    save_dependence_plot,
    save_feature_importance_plot,
    save_force_plot,
    save_summary_plot,
    save_waterfall_plot,
)
from explainability.serializers import (
    build_local_explanation,
    global_summary_from_shap,
)
from training.persistence import load_json, load_model

_DEFAULT_MODEL_PATH = "models/latest/model.joblib"
_DEFAULT_FEATURE_MATRIX = "datasets/features/feature_matrix.parquet"
_DEFAULT_EXPLANATIONS_DIR = "explanations"


def _load_metadata(feature_matrix_path: Path) -> dict[str, str]:
    """Read version strings from the sibling feature_metadata.json if present."""
    meta_path = feature_matrix_path.parent / "feature_metadata.json"
    if meta_path.exists():
        meta = load_json(meta_path)
        return {
            "feature_version": str(meta.get("pipeline_version", "unknown")),
            "dataset_version": str(meta.get("source_dataset_version", "unknown")),
        }
    return {"feature_version": "unknown", "dataset_version": "unknown"}


def _save_json(data: list[Any] | dict[str, Any], path: Path) -> None:
    """Write data to a UTF-8 JSON file with two-space indentation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _resolve_paths(
    config: ExplainabilityConfig, cwd: Path, absolute: bool
) -> tuple[Path, Path, Path]:
    """Return (model_path, feature_matrix_path, explanations_dir)."""
    if absolute:
        return (
            Path(config.model_path),
            Path(config.feature_matrix_path),
            Path(config.explanations_dir),
        )
    return (
        cwd / config.model_path,
        cwd / config.feature_matrix_path,
        cwd / config.explanations_dir,
    )


def _get_team_columns(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Return home_team and away_team columns as lists (or placeholder lists)."""
    home_teams = (
        df["home_team"].tolist() if "home_team" in df.columns else ["Home"] * len(df)
    )
    away_teams = (
        df["away_team"].tolist() if "away_team" in df.columns else ["Away"] * len(df)
    )
    return home_teams, away_teams


def _generate_local_explanations(
    *,
    shap_values: np.ndarray,
    feature_matrix: np.ndarray,
    feature_names: list[str],
    classes: list[str],
    probs_matrix: np.ndarray,
    home_teams: list[str],
    away_teams: list[str],
    n_samples: int,
    n_top_features: int,
    model_version: str,
    feature_version: str,
    dataset_version: str,
) -> list[dict[str, Any]]:
    """Generate local explanations for n_samples rows; return as JSON-serialisable list."""
    class_to_idx = {c: i for i, c in enumerate(classes)}
    explanations = []
    for i in range(n_samples):
        probs = probs_matrix[i]
        pred_idx = int(np.argmax(probs))
        predicted_result = classes[pred_idx]
        prob_h = float(probs[class_to_idx.get("H", 0)])
        prob_d = float(probs[class_to_idx.get("D", 1)])
        prob_a = float(probs[class_to_idx.get("A", 2)])
        expl = build_local_explanation(
            match_index=i,
            home_team=str(home_teams[i]),
            away_team=str(away_teams[i]),
            predicted_result=predicted_result,
            probability_home=prob_h,
            probability_draw=prob_d,
            probability_away=prob_a,
            shap_values_row=shap_values[i],
            feature_values=feature_matrix[i].tolist(),
            feature_names=feature_names,
            classes=classes,
            n_top_features=n_top_features,
            model_version=model_version,
            feature_version=feature_version,
            dataset_version=dataset_version,
        )
        explanations.append(json.loads(expl.model_dump_json()))
    return explanations


def _generate_plots(
    *,
    shap_values: np.ndarray,
    feature_matrix: np.ndarray,
    base_values: np.ndarray,
    feature_names: list[str],
    classes: list[str],
    exp_dir: Path,
    n_local: int,
    n_dependence: int,
) -> None:
    """Write all SHAP plots to disk."""
    save_summary_plot(
        shap_values, feature_matrix, feature_names, exp_dir / "summary_plot.png"
    )
    save_feature_importance_plot(
        shap_values, feature_names, exp_dir / "feature_importance.png"
    )

    waterfall_dir = exp_dir / "waterfall"
    force_dir = exp_dir / "force"
    for i in range(min(n_local, len(feature_matrix))):
        for class_idx, cls in enumerate(classes):
            save_waterfall_plot(
                shap_values_row=shap_values[i, :, class_idx],
                base_value=float(base_values[class_idx]),
                feature_values=feature_matrix[i].tolist(),
                feature_names=feature_names,
                output_path=waterfall_dir / f"sample_{i:04d}_{cls}.png",
            )
            save_force_plot(
                shap_values_row=shap_values[i, :, class_idx],
                base_value=float(base_values[class_idx]),
                feature_values=feature_matrix[i].tolist(),
                feature_names=feature_names,
                output_path=force_dir / f"sample_{i:04d}_{cls}.png",
            )

    mean_abs = np.abs(shap_values).mean(axis=(0, 2))
    top_feature_names = [
        feature_names[j] for j in np.argsort(mean_abs)[-n_dependence:][::-1]
    ]
    dep_dir = exp_dir / "dependence"
    for feat in top_feature_names:
        save_dependence_plot(
            feature_name=feat,
            shap_values=shap_values,
            feature_values_matrix=feature_matrix,
            feature_names=feature_names,
            output_path=dep_dir / f"{feat}.png",
        )


class ExplainabilityPipeline:
    """Orchestrates the full SHAP explainability pipeline."""

    def __init__(self, config: ExplainabilityConfig | None = None) -> None:
        """Initialise with an optional config; defaults to ExplainabilityConfig()."""
        self._config = config or ExplainabilityConfig()

    def run(
        self, cwd: Path | None = None, use_absolute_paths: bool = False
    ) -> dict[str, Any]:
        """Execute the pipeline and return a summary dict."""
        root = cwd or Path.cwd()
        config = self._config
        model_path, fm_path, exp_dir = _resolve_paths(config, root, use_absolute_paths)

        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        if not fm_path.exists():
            raise FileNotFoundError(f"Feature matrix not found: {fm_path}")

        model = load_model(model_path)
        df = pd.read_parquet(fm_path)
        home_teams, away_teams = _get_team_columns(df)
        meta = _load_metadata(fm_path)
        model_version = (
            model_path.parent.name if model_path.parent.name != "." else "unknown"
        )

        feature_names = model.feature_names
        X = (
            df[feature_names]
            if all(c in df.columns for c in feature_names)
            else pd.DataFrame(
                {c: df[c] if c in df.columns else 0.0 for c in feature_names}
            )
        )
        X_imp: np.ndarray = model.imputer.transform(X)
        probs_matrix: np.ndarray = model.booster.predict_proba(X_imp)

        version = str(model_path.stat().st_mtime)
        explainer = ExplainerCache.get_or_create(model_path, version)
        shap_values = explainer.shap_values(X)
        base_values = explainer.expected_value()

        summary = global_summary_from_shap(
            shap_values=shap_values,
            feature_names=feature_names,
            classes=model.classes,
            model_version=model_version,
            feature_version=meta["feature_version"],
            dataset_version=meta["dataset_version"],
        )

        n_local = min(config.n_local_samples, len(df))
        local_explanations = _generate_local_explanations(
            shap_values=shap_values[:n_local],
            feature_matrix=X_imp[:n_local],
            feature_names=feature_names,
            classes=model.classes,
            probs_matrix=probs_matrix[:n_local],
            home_teams=home_teams[:n_local],
            away_teams=away_teams[:n_local],
            n_samples=n_local,
            n_top_features=config.n_top_features,
            model_version=model_version,
            feature_version=meta["feature_version"],
            dataset_version=meta["dataset_version"],
        )

        exp_dir.mkdir(parents=True, exist_ok=True)
        _save_json(
            json.loads(summary.model_dump_json()), exp_dir / "global_summary.json"
        )
        _save_json(local_explanations, exp_dir / "local_explanations.json")

        _generate_plots(
            shap_values=shap_values,
            feature_matrix=X_imp,
            base_values=base_values,
            feature_names=feature_names,
            classes=model.classes,
            exp_dir=exp_dir,
            n_local=n_local,
            n_dependence=config.n_dependence_plots,
        )

        return {
            "status": "ok",
            "n_samples": len(df),
            "n_features": len(feature_names),
            "n_local_explanations": n_local,
            "explanations_dir": str(exp_dir),
            "timestamp": datetime.now(tz=UTC).isoformat(),
        }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the explainability pipeline."""
    parser = argparse.ArgumentParser(
        description="Generate SHAP explanations for the XGBoost match outcome model.",
        prog="explainability.pipeline",
    )
    parser.add_argument(
        "--model-path",
        metavar="PATH",
        default=_DEFAULT_MODEL_PATH,
        help="Path to model.joblib. Defaults to models/latest/model.joblib.",
    )
    parser.add_argument(
        "--feature-matrix",
        metavar="PATH",
        default=_DEFAULT_FEATURE_MATRIX,
        help="Path to feature_matrix.parquet.",
    )
    parser.add_argument(
        "--explanations-dir",
        metavar="DIR",
        default=_DEFAULT_EXPLANATIONS_DIR,
        help="Output directory for explanation artifacts.",
    )
    parser.add_argument("--n-top-features", type=int, default=10)
    parser.add_argument("--n-local-samples", type=int, default=10)
    parser.add_argument("--n-dependence-plots", type=int, default=5)
    args = parser.parse_args(argv)

    config = ExplainabilityConfig(
        model_path=args.model_path,
        feature_matrix_path=args.feature_matrix,
        explanations_dir=args.explanations_dir,
        n_top_features=args.n_top_features,
        n_local_samples=args.n_local_samples,
        n_dependence_plots=args.n_dependence_plots,
    )

    cwd = Path.cwd()
    print(f"Model:          {cwd / config.model_path}")
    print(f"Feature matrix: {cwd / config.feature_matrix_path}")
    print(f"Output:         {cwd / config.explanations_dir}")
    print()

    try:
        pipeline = ExplainabilityPipeline(config)
        result = pipeline.run(cwd)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Samples:        {result['n_samples']}")
    print(f"Features:       {result['n_features']}")
    print(f"Local explanations: {result['n_local_explanations']}")
    print(f"Artifacts:      {result['explanations_dir']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
