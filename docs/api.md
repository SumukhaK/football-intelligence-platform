# API Reference

FastAPI backend in `ai/backend/`. The OpenAPI docs are served at `/docs`, and
this page summarises the contract. The API serves the Premier League only
(ADR 005).

Errors return JSON `{ "error": "...", "detail": "..." }` with extra fields
where noted.

---

## GET /health

Service status.

```json
{
  "status": "ok",
  "model_loaded": true,
  "explainability_available": true,
  "assistant_available": false,
  "fixture_features_available": true,
  "version": "0.1.0"
}
```

`fixture_features_available` is true when match history is loaded, so
requests may omit `features` (ADR 008).

## GET /model

Registry entry of the served model: `model_version`, `dataset_version`,
`training_timestamp`, `git_commit` and test `metrics`. Returns 503 when no
model is registered.

## GET /teams

Teams of the latest season the server has results for. These are the names
`/predict` and `/explain` accept.

```json
{
  "competition": "Premier League",
  "season": "2026/27",
  "teams": ["Arsenal", "Aston Villa", "..."]
}
```

Returns 503 when match history is not loaded.

## POST /predict

Predicts home win (H), draw (D) or away win (A).

Request:

| Field | Type | Required | Description |
|---|---|---|---|
| `home_team` | string | yes | A name from `/teams`. |
| `away_team` | string | yes | A name from `/teams`. |
| `match_date` | date | no | Only matches before this date are used. Defaults to today. |
| `features` | object | no | Pre-computed feature vector. When omitted, the server computes all 42 model features from match history with the training feature pipeline. |

```json
{ "home_team": "Arsenal", "away_team": "Man City", "match_date": "2026-10-03" }
```

Response:

```json
{
  "home_team": "Arsenal",
  "away_team": "Man City",
  "predicted_result": "H",
  "probability_home": 0.393,
  "probability_draw": 0.277,
  "probability_away": 0.330,
  "confidence": 0.393,
  "model_version": "20260928_123224"
}
```

Errors:

| Status | `error` | When |
|---|---|---|
| 422 | `Unknown team` | A team did not play in the latest season. Includes `team`. |
| 422 | `Missing feature columns` | Supplied `features` lack model columns. Includes `missing`. |
| 503 | `Model not available` | No model loaded. |
| 503 | `Match features not available` | `features` omitted and no match history loaded. |

## POST /explain

Same request and errors as `/predict`. Adds SHAP attributions in
`top_positive_features`, `top_negative_features` and `all_contributions`, plus
`model_version`, `feature_version`, `dataset_version` and
`explanation_timestamp`. Each item has:

| Field | Example | Description |
|---|---|---|
| `feature_name` | `home_elo_before` | Model feature identifier |
| `feature_value` | `1617.748` | Value used by the model, after imputation |
| `shap_value` | `0.337` | Push toward (positive) or away from the predicted outcome |
| `display_name` | `Arsenal team strength rating` | Fan-friendly label with team names filled in |
| `display_value` | `1618` | Fan-friendly value: counts ("9 of 10"), rates ("68%"), positions ("10th"), days ("7 days") |

Labels live in `ai/explainability/feature_labels.py`; every model feature has
one, and a test enforces it.

## POST /assistant/chat

Retrieval-augmented answers about the project's data and models. Returns 503
when the assistant's vector store or Ollama is unavailable.

---

## Keeping match history current

The server loads the newest `match_results_live_v*.csv` from
`datasets/processed/football_data/` at startup, falling back to the newest
`match_results_top5_v*.csv`. To include the latest results, run:

```sh
uv run python -m scripts.refresh_live_dataset --confirm
```

Then restart the backend. Configure the directory with `MATCHES_DIR` and the
competition with `SERVED_COMPETITION`.
