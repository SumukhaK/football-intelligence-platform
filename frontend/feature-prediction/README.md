# :feature-prediction

Match outcome prediction screen with XGBoost result and SHAP explanation display.

## Ownership

Presentation layer. The most AI-forward feature module.

## Contents

- `PredictionViewModel` — league, teams, prediction, explanation and insights state. `predictFixture` predicts a fixture tapped on home.
- `PredictionScreen` — league picker with league emblems and team selection with crests.
- `PredictionResultScreen` — the winner's crest (both crests for a draw), probabilities, draw tag and the goals model's insights (`InsightsSection`). A predicted win plays a burst of confetti (`Confetti`).
- `InsightsSection` — likely scores, with a note on why a draw can top that list, and goal markets.
- `ExplainPredictionScreen` — SHAP contributions in plain football language.
- `PredictionRepository` — predict, explain, insights, teams and competitions calls.

## Constraints

- SHAP values must always be displayed alongside a prediction. No prediction without explanation.
- The ViewModel must not interpret SHAP values; it passes them through for the UI to display.
- TDD: write tests for the ViewModel before writing the ViewModel.
