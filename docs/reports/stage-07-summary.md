# Stage 7 — XGBoost Training & Evaluation Pipeline

## Status: Complete

## What was built

Four new packages under `ai/`:

| Package | Purpose |
|---|---|
| `training/` | Configuration, chronological splitter, XGBoost trainer, persistence, registry helper, pipeline CLI |
| `evaluation/` | Metrics, cross-validation, Matplotlib plots, Pydantic report models |
| `inference/` | `MatchPredictor` — loads model, returns `MatchPrediction` dataclass |
| `model_registry/` | JSON-backed local registry with `ModelEntry` versioned records |

## Pipeline steps

1. Load `datasets/features/feature_matrix.parquet`
2. Filter to 42 numeric pre-match features (post-match stats excluded)
3. Chronological split: 70% train / 15% val / 15% test
4. Fit `XGBClassifier(multi:softprob)` with early stopping on val log-loss
5. Cross-validate on train+val using `TimeSeriesSplit` (5 folds)
6. Compute metrics for all three splits
7. Persist run artifacts to `models/runs/<timestamp>/`
8. Copy artifacts to `models/latest/`
9. Write global `models/evaluation/evaluation_report.json`
10. Generate `model_card.md`
11. Register version in `models/registry.json`

## Results (2023/24 Premier League, 380 matches)

| Metric | Test |
|---|---|
| Accuracy | 0.5614 |
| F1 (weighted) | 0.5181 |
| Log Loss | 0.9493 |
| Best iteration | 10 (early stopping) |
| Features used | 42 |

## Architecture decisions

- ADR 001: XGBoost over alternatives (Logistic Regression, Random Forest, Neural Network)
- ADR 002: joblib serialisation — single file bundles booster + imputer + encoder
- ADR 003: chronological split — rejects random split to prevent temporal leakage

## Tests

48 new tests across 4 packages. 254 total tests passing (1 integration test deselected).

## Known limitations

- Single season of data (380 matches); model generalises to this one season only.
- First-match NaN values for rolling features are imputed with training-set medians.
- Elo ratings reset on each pipeline run; no cross-season persistence.
- SHAP explainability is planned for Stage 8.
