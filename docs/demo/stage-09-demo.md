# Stage 9 Demo — Prediction and Explainability API

> Historical walkthrough of Stage 9 (v1.0.0 era). For the current system, use the root README Quick Start and [docs/demo/README.md](README.md).
>
> Today `/v2/...` is the current API. `/v1/...` and the unversioned paths used below keep the frozen v1.0.0 contract and the original Premier League model (ADR 014). The prediction and explanation steps now use `/v2`, where requests need only team names. The full contract is in [docs/api.md](../api.md).

## Prerequisites

```bash
cd ai
uv run uvicorn backend.app.main:app --reload
```

Server starts on `http://127.0.0.1:8000`. Swagger UI at `/docs`.

---

## 1. Health Check

```bash
curl http://127.0.0.1:8000/health
```

```json
{
  "status": "ok",
  "model_loaded": true,
  "explainability_available": true,
  "assistant_available": false,
  "fixture_features_available": true,
  "insights_available": true,
  "matches_through": "2026-09-20",
  "last_refresh_at": "2026-09-29T07:01:31+05:30",
  "last_refresh_error": null,
  "version": "2.0.0"
}
```

`assistant_available` is true only when Ollama is running and the assistant index is built (Stage 10). The dates depend on when your data was last refreshed.

---

## 2. Model Metadata

```bash
curl http://127.0.0.1:8000/model
```

```json
{
  "model_version": "20260630_132617",
  "dataset_version": "20260630_090657",
  "training_timestamp": "2026-06-30T13:26:20.336786+00:00",
  "git_commit": "db80506eb9a63ac8b3dd460962ff43d1e196a680",
  "metrics": {
    "accuracy": 0.561,
    "f1_weighted": 0.518,
    "roc_auc_ovr": 0.625
  }
}
```

---

## 3. Predict Match Outcome

The server builds all 42 model features from match history (ADR 008), so the request names only the teams and, optionally, the league.

```bash
curl -X POST http://127.0.0.1:8000/v2/predict \
  -H "Content-Type: application/json" \
  -d '{"home_team": "Arsenal", "away_team": "Man City", "competition": "Premier League"}'
```

Example response (the numbers depend on your data and model):

```json
{
  "competition": "Premier League",
  "home_team": "Arsenal",
  "away_team": "Man City",
  "predicted_result": "H",
  "probability_home": 0.393,
  "probability_draw": 0.277,
  "probability_away": 0.330,
  "confidence": 0.393,
  "draw_possible": false,
  "model_version": "20260928_123224"
}
```

---

## 4. Explain Prediction with SHAP

```bash
curl -X POST http://127.0.0.1:8000/v2/explain \
  -H "Content-Type: application/json" \
  -d '{"home_team": "Arsenal", "away_team": "Man City", "competition": "Premier League"}'
```

The response holds the prediction plus SHAP attributions in `top_positive_features`, `top_negative_features` and `all_contributions` (all 42 features), and `model_version`, `feature_version`, `dataset_version` and `explanation_timestamp`. Each attribution looks like this:

```json
{
  "feature_name": "home_elo_before",
  "feature_value": 1617.748,
  "shap_value": 0.337,
  "display_name": "Arsenal team strength rating",
  "display_value": "1618"
}
```

---

## 5. Error Cases

### Missing model (503)

If the model path does not exist at startup, all prediction endpoints return:

```json
{ "error": "Model not available", "detail": "Prediction model is not loaded." }
```

### Missing feature columns (422)

Only when a request supplies its own optional `features` object and it lacks model columns:

```json
{
  "error": "Missing feature columns",
  "detail": "Missing feature columns: ['home_form_wins_last10', ...]",
  "missing": ["home_form_wins_last10", "home_form_points_last10", "..."]
}
```

### Pydantic validation (422)

```json
{
  "detail": [{ "type": "missing", "loc": ["body", "home_team"], "msg": "Field required" }]
}
```

---

## 6. Interactive Docs

Open `http://127.0.0.1:8000/docs` in a browser to explore all endpoints with the built-in Swagger UI.
