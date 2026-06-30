# Stage 12 — End-to-End Demo Guide

## Objective

Demonstrate the complete Football Intelligence Platform: data pipeline → ML model → FastAPI backend → Android app → AI assistant — all running locally without cloud services.

**Estimated demo time:** 10–15 minutes

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.12 | Managed by uv |
| uv | Latest | `pip install uv` |
| JDK | 17+ | For Android build |
| Android emulator | API 26+ | Via Android Studio |
| Ollama | Latest | Optional — assistant only |

---

## Environment Setup

### 1. Install Python dependencies

```bash
cd ai
uv sync --extra dev
```

### 2. Verify model artifacts exist

```bash
ls models/latest/model.joblib    # must exist
ls models/registry.json          # must exist
```

If they do not exist, run the full pipeline:

```bash
uv run python -m scripts.ingest_football_data
uv run python -m feature_engineering.pipeline
uv run python -m training.pipeline
uv run python -m explainability.pipeline
```

### 3. (Optional) Set up the AI assistant

Requires Ollama installed and running.

```bash
ollama pull nomic-embed-text
ollama pull llama3.2
uv run python -m assistant.pipeline --rebuild
```

---

## Backend Startup

```bash
cd ai
uv run uvicorn backend.app.main:app --reload
```

Expected log output:

```
INFO: Prediction model loaded: version=<version> path=models/latest/model.joblib
INFO: Explanation service loaded.
INFO: Assistant service loaded: <N> chunks in index.   ← only if Ollama is running
INFO: Application startup complete.
INFO: Uvicorn running on http://127.0.0.1:8000
```

Verify in browser: http://127.0.0.1:8000/docs

---

## Android Startup

### Build and install

```bash
cd frontend
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

The app connects to `http://10.0.2.2:8000` (Android emulator's alias for localhost).

---

## End-to-End Demo Flow

### Step 1 — Application Startup & Health Check

1. Launch the app on the Android emulator.
2. The **Home** screen loads immediately and polls `GET /health`.
3. Observe three status chips:
   - **Model** — green (XGBoost loaded)
   - **Explainability** — green (SHAP available)
   - **Assistant** — green if Ollama is running; amber/red otherwise
4. This confirms the app can reach the backend and the backend has its AI services loaded.

**Expected result:** All three chips green (or two if Ollama is not running).

---

### Step 2 — Match Prediction Flow

1. Tap **Predict Match** from the Home screen.
2. Select **Home Team** from the dropdown (e.g. Arsenal).
3. Select **Away Team** (e.g. Chelsea).
4. Tap **Predict**.
5. The app sends `POST /predict` with 44 neutral feature values.
6. The **Prediction Result** screen displays:
   - Predicted outcome (Home Win / Draw / Away Win)
   - Three probability bars (home / draw / away)
   - Confidence percentage

**Expected result:** A prediction result with three probabilities that sum to 100%.

---

### Step 3 — SHAP Explanation Flow

1. From the Prediction Result screen, tap **Explain This Prediction**.
2. The app sends `POST /explain` with the same features.
3. The **Explain Prediction** screen displays:
   - **Top positive features** — pushed the prediction toward this outcome (green values)
   - **Top negative features** — pulled against this outcome (red values)

**Expected result:** Two sections of SHAP feature contributions, labelled with feature names and numeric SHAP values.

---

### Step 4 — AI Assistant Chat

1. From the Home screen, tap **AI Assistant** (or use the bottom nav).
2. Type a question: *"What is the model's accuracy on the test set?"*
3. The assistant responds with a grounded answer from the knowledge base.
4. Source citations appear below the answer.

**Expected result (with Ollama):** A factual answer citing `model_card.md` or similar source. Confidence score shown below the answer.

**Expected result (without Ollama):** An unavailability message is displayed. The chat input is hidden. No crash.

---

### Step 5 — Model Information

1. Navigate to **Settings → Model Information**.
2. The screen calls `GET /model` and displays:
   - Model version
   - Dataset version
   - Training timestamp
   - Evaluation metrics (accuracy, F1, log-loss, ROC AUC)

**Expected result:** All fields populated from the live backend.

---

### Step 6 — Graceful Shutdown

1. Stop the backend (`Ctrl+C` in the terminal).
2. On the Android app, navigate to Home and tap the Retry button.
3. The app shows an error state with a meaningful message.
4. No crash occurs.

**Expected result:** Error card with "Could not reach the server" (or similar). App remains interactive.

---

## Expected Results Summary

| Step | Endpoint | Expected Status | Expected Outcome |
|---|---|---|---|
| Home load | `GET /health` | 200 | model_loaded=true |
| Predict | `POST /predict` | 200 | H/D/A + probabilities |
| Explain | `POST /explain` | 200 | 42 SHAP contributions |
| Assistant (with Ollama) | `POST /assistant/chat` | 200 | Grounded answer |
| Assistant (no Ollama) | `POST /assistant/chat` | 503 | Unavailability message |
| Model info | `GET /model` | 200 | Metrics + version |

---

## Verification Checklist

- [ ] Backend starts and logs `Prediction model loaded`
- [ ] `/health` returns `model_loaded: true`
- [ ] `/docs` (Swagger UI) shows all 5 endpoints
- [ ] Android app Home screen shows green status chips
- [ ] Prediction flow produces H/D/A result with probabilities summing to ~100%
- [ ] Explain flow shows positive and negative SHAP features
- [ ] Assistant responds (or shows unavailability message — both are correct)
- [ ] Model Information screen shows version and metrics
- [ ] Backend shutdown → app shows error card, no crash

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Backend fails to start | Model missing | Run `uv run python -m training.pipeline` |
| App cannot connect | Backend not running or wrong URL | Confirm backend on `:8000`; emulator uses `10.0.2.2` |
| Assistant always 503 | Ollama not running | `ollama serve` then rebuild index |
| App crashes on launch | Koin DI error | Check `logcat` for missing module |
| Prediction returns 422 | Feature mismatch | App uses neutral features — always 44 keys |

---

## Running Integration Tests

To verify end-to-end correctness programmatically:

```bash
cd ai
uv run pytest tests/integration/ -v
```

Expected output: **36 passed**.

Full test suite (unit + integration):

```bash
uv run pytest
```

Expected output: **462 passed**.
