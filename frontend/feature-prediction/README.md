# :feature-prediction

Match outcome prediction screen with XGBoost result and SHAP explanation display.

## Ownership

Presentation layer. The most AI-forward feature module.

## Contents

- `PredictionViewModel` — league, teams, prediction, explanation and insights state.
- `PredictionScreen` — league picker and team selection.
- `PredictionResultScreen` — probabilities, draw tag and the goals model's insights (`InsightsSection`).
- `ExplainPredictionScreen` — SHAP contributions in plain football language.
- `PredictionRepository` — predict, explain, insights, teams and competitions calls.

## Constraints

- SHAP values must always be displayed alongside a prediction. No prediction without explanation.
- The ViewModel must not interpret SHAP values; it passes them through for the UI to display.
- TDD: write tests for the ViewModel before writing the ViewModel.
