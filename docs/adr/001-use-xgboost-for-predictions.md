# ADR 001 — Use XGBoost for Match Outcome Prediction

**Status:** Accepted

## Context

The Football Intelligence Platform requires a match outcome classifier (Home/Draw/Away) trained on the engineered feature matrix produced in Stage 6. The model must:

- Handle missing values (first-match NaN for rolling features)
- Support multiclass classification (3 classes)
- Produce calibrated class probabilities for use with SHAP
- Train on a small dataset (~266 training rows) without overfitting
- Be interpretable through feature importance

Candidate models considered:

| Model | Pros | Cons |
|---|---|---|
| Logistic Regression | Fast, interpretable, stable on small data | Linear decision boundary; underfits complex patterns |
| Random Forest | Handles NaN via imputation, low overfitting | Slower inference; weaker probability calibration |
| **XGBoost** | Handles NaN natively, strong on tabular data, excellent feature importance, well-supported SHAP integration | Requires hyperparameter tuning |
| Neural Network | High capacity | Needs far more data; black-box without extra tooling |

## Decision

Use **XGBoost** (`xgboost>=2.0.0`) with the `multi:softprob` objective.

Rationale:
1. XGBoost is the de-facto standard for tabular ML and performs well on small datasets with proper regularisation.
2. `multi:softprob` produces calibrated probability estimates required by downstream SHAP analysis (Stage 8).
3. The `feature_importances_` attribute integrates directly with Stage 8's explainability layer.
4. Early stopping on a held-out validation set prevents overfitting on the 380-row dataset.
5. `SimpleImputer(strategy="median")` is applied before XGBoost to handle NaN values from rolling features.

## Consequences

- `xgboost>=2.0.0` added to `pyproject.toml`.
- The model is serialised with `joblib` to `models/latest/model.joblib` (see ADR 002).
- Hyperparameters are externalised in `TrainingConfig` — no hardcoded values.
- SHAP integration in Stage 8 will use `shap.TreeExplainer(booster.get_booster())`.
- If the dataset grows to 10k+ rows, XGBoost may be replaced by LightGBM (write a new ADR at that point).
