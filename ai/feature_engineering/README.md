# feature_engineering

Transforms preprocessed data into model-ready feature sets.

## Responsibility

Computes derived features from clean data: rolling averages, head-to-head records, form indicators, and any other engineered signals. Outputs a feature matrix ready for XGBoost training or inference.

## Contracts

- Reads only from `datasets/processed/`. Never from raw.
- Feature definitions are explicit Python functions, not implicit DataFrame mutations.
- Every feature has a name, a description, and a unit test.
- The feature set is versioned alongside the model that was trained on it.

## Future Contents

- `match_features.py` — match-level feature computation.
- `team_features.py` — team rolling statistics.
- `pipeline.py` — feature pipeline that composes individual feature functions.
