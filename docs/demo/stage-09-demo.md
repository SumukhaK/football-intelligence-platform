# Stage 9 Demo — Prediction and Explainability API

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
  "version": "0.1.0"
}
```

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

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "home_team": "Arsenal",
    "away_team": "Chelsea",
    "features": {
      "home_elo": 1550.0,
      "away_elo": 1480.0,
      "elo_diff": 70.0,
      "home_form_wins_last5": 3.0,
      "home_form_points_last5": 9.0,
      ...
    }
  }'
```

```json
{
  "home_team": "Arsenal",
  "away_team": "Chelsea",
  "predicted_result": "H",
  "probability_home": 0.4275,
  "probability_draw": 0.1859,
  "probability_away": 0.3867,
  "confidence": 0.4275,
  "model_version": "20260630_132617"
}
```

---

## 4. Explain Prediction with SHAP

```bash
curl -X POST http://127.0.0.1:8000/explain \
  -H "Content-Type: application/json" \
  -d '{ "home_team": "Arsenal", "away_team": "Chelsea", "features": { ... } }'
```

```json
{
  "predicted_result": "H",
  "probability_home": 0.4275,
  "confidence": 0.4275,
  "top_positive_features": [
    { "feature_name": "elo_diff", "feature_value": 70.0, "shap_value": 0.082 },
    { "feature_name": "home_ppg", "feature_value": 1.8, "shap_value": 0.061 }
  ],
  "top_negative_features": [
    { "feature_name": "away_elo", "feature_value": 1480.0, "shap_value": -0.045 }
  ],
  "all_contributions": [ ... 42 features ... ],
  "model_version": "20260630_132617",
  "dataset_version": "20260630_090657",
  "explanation_timestamp": "2026-06-30T..."
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
