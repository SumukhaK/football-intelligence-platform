# ADR 033 — A Public Name for the Prediction Model: Drishti

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The app showed the match prediction model only by its registry version, such as `20260928_123224`. That tag is right for tracing a prediction back to a training run, but it means nothing to the friends using the app.

## Decision

- The match outcome model (XGBoost with SHAP, ADR 001 and ADR 004) is called **Drishti**, Sanskrit for "vision" or "far sight".
- `GET /model` (and `/v1/model`) returns it as `model_name`, read from the `PREDICTION_MODEL_NAME` setting, which defaults to `Drishti`. It is not hard-coded in a route.
- `model_version` stays the technical identifier. The name does not change when the model is retrained; the version does.
- The app shows the name as the heading of Model information, with the version underneath.

## Consequences

- Users see a name instead of a timestamp, and the version is still there for bug reports.
- `model_name` is a new field, so older apps ignore it. The app falls back to its own copy of the name when an older backend leaves it out.
- Prediction and explanation responses keep only `model_version`; the name is the same for every model the API serves.
