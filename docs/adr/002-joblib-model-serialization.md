# ADR 002 — Use joblib for Model Serialisation

**Status:** Accepted

## Context

The trained `TrainedModel` dataclass contains:
- An `xgb.XGBClassifier` booster
- A `sklearn.preprocessing.LabelEncoder`
- A `sklearn.impute.SimpleImputer`
- Feature names and class labels

These objects must be persisted together so the inference layer can load a complete, ready-to-predict bundle from disk.

Options considered:

| Format | Pros | Cons |
|---|---|---|
| **joblib** | Supports any Python object, efficient for NumPy arrays, already a project dependency | Not human-readable; version-sensitive |
| pickle | Standard library | Slower for NumPy arrays than joblib; same version sensitivity |
| XGBoost native (`.json`/`.ubj`) | Portable booster format | Cannot serialise sklearn objects alongside the booster |
| ONNX | Portable, language-agnostic | Complex conversion pipeline; adds dependency; overkill for local use |

## Decision

Use **joblib** to serialise the complete `TrainedModel` dataclass as a single `.joblib` file.

Rationale:
1. `joblib` is already in `pyproject.toml` (required by scikit-learn).
2. A single file contains the booster, imputer, and label encoder — the inference layer loads one file and is immediately ready to predict.
3. `joblib.dump` / `joblib.load` are idiomatic for scikit-learn pipelines.
4. The framework versions used during serialisation are recorded in `model_metadata.json` and `registry.json`, making deserialization failures diagnosable.

## Consequences

- Model files are Python-version and library-version sensitive. The `model_metadata.json` records exact dependency versions to assist debugging.
- The `TrainedModel` dataclass must remain stable. Adding fields is safe; removing or renaming fields breaks existing serialised models.
- If portability across languages is ever required, write a new ADR and export the booster via `booster.save_model("model.json")` alongside the `.joblib`.
- Model files are excluded from git via `.gitignore` (`models/*.joblib`).
