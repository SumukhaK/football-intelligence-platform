# :feature-prediction

Match outcome prediction screen with XGBoost result and SHAP explanation display.

## Ownership

Presentation layer. The most AI-forward feature module.

## Future Contents

- `PredictionViewModel` — owns `PredictionUiState`. TDD required.
- `PredictionScreen` — displays predicted outcome and SHAP feature bar chart.
- `ShapExplanationCard` — renders feature importance values from the backend response.
- `PredictionRepository` interface and implementation.

## Constraints

- SHAP values must always be displayed alongside a prediction. No prediction without explanation.
- The ViewModel must not interpret SHAP values — it passes them through for the UI to display.
- TDD: write tests for the ViewModel before writing the ViewModel.
