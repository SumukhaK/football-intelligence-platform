# Stage 12 — End-to-End Demo Guide

> Historical walkthrough of Stage 12 (v1.0.0 era). For the current system, use the root README Quick Start and [docs/demo/README.md](README.md). The commands and app steps below have been updated to match release v2.0.1.

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

If they do not exist, run the five-league pipeline from the root README Quick Start (models are not committed):

```bash
uv run python -m scripts.backfill_football_data --base-dir ../datasets --confirm
uv run python -m feature_engineering.pipeline --input ../datasets/processed/football_data/match_results_top5_v<ts>.csv --output-dir ../datasets/features/top5
uv run python -m training.pipeline --feature-matrix ../datasets/features/top5/feature_matrix.parquet --split-strategy season --val-seasons 2022/23 --test-seasons 2023/24 --holdout-seasons 2024/25 2025/26 --max-depth 3 --learning-rate 0.03 --n-estimators 400
uv run python -m explainability.pipeline --feature-matrix ../datasets/features/top5/feature_matrix.parquet
```

Replace `<ts>` with the timestamp of the CSV the backfill wrote.

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
INFO: Explanation service loaded: version=<version>
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

The app calls API v2 at `http://10.0.2.2:8000/v2` (the Android emulator's alias for the host machine's localhost).

---

## End-to-End Demo Flow

### Step 1 — Application Startup & Health Check

1. Launch the app on the Android emulator. It opens on **Fixtures**, with one tab per league and upcoming matches by date (`GET /v2/fixtures`).
2. Tap **Settings** in the bottom bar. The **Backend Status** card calls `GET /v2/health`.
3. Observe three status rows:
   - **Prediction API** — online (model loaded)
   - **SHAP Explainer** — online (SHAP available)
   - **AI Assistant** — online only if Ollama is running
4. This confirms the app can reach the backend and the backend has its AI services loaded.

**Expected result:** All three online (or two if Ollama is not running).

---

### Step 2 — Match Prediction Flow

1. Tap **Predict** in the bottom bar.
2. Pick a **League** (e.g. Premier League).
3. Select **Home Team** (e.g. Arsenal) and **Away Team** (e.g. Chelsea).
4. Tap **Predict Match Outcome**.
5. The app sends `POST /v2/predict` with only the two team names and the league. The server computes the features from match history.
6. The **Prediction Result** screen displays:
   - Predicted outcome (for example "Arsenal Win" or "Draw"), with a **Draw possible** tag when the draw chance is at least 28%
   - Home / draw / away probabilities and the confidence
   - The most likely scores and goal markets from the goals model

**Expected result:** A prediction result with three probabilities that sum to 100%.

---

### Step 3 — SHAP Explanation Flow

1. From the Prediction Result screen, tap **Explain**.
2. The app sends `POST /v2/explain` with the same team names and league.
3. The **Explanation** screen displays:
   - **Why the model leans this way** — factors that pushed toward the prediction
   - **What counts against it** — factors that pushed away from it

**Expected result:** Two sections of factors in plain language (such as a team's home win rate), each with a **Big**, **Medium** or **Small impact** tag.

---

### Step 4 — AI Assistant Chat

1. Tap **Assistant** in the bottom bar.
2. Type a question: *"What is the model's accuracy on the test set?"*
3. The assistant responds with a grounded answer from the knowledge base.
4. Source citations appear below the answer.

**Expected result (with Ollama):** A factual answer citing `model_card.md` or similar source. Confidence score shown below the answer.

**Expected result (without Ollama):** An unavailability message is displayed. The chat input is hidden. No crash.

---

### Step 5 — Model Information

1. Navigate to **Settings → Model Information**.
2. The screen calls `GET /v2/model` and displays:
   - Model version
   - Dataset version
   - Training timestamp
   - Evaluation metrics (accuracy, F1, log-loss, ROC AUC)

**Expected result:** All fields populated from the live backend.

---

### Step 6 — Offline Behaviour

1. Stop the backend (`Ctrl+C` in the terminal).
2. On the Android app, pull down on **Fixtures** to refresh, or open another screen.
3. Within about 10 seconds the app shows the data it saved earlier under an offline banner ("You're offline. Showing data saved …").
4. No crash occurs.

**Expected result:** Saved data under the offline banner. If nothing was saved yet, an error card explains that the server can't be reached, with a Retry button. App remains interactive.

---

## Expected Results Summary

| Step | Endpoint | Expected Status | Expected Outcome |
|---|---|---|---|
| Fixtures home | `GET /v2/fixtures` | 200 | Upcoming matches per league |
| Settings status | `GET /v2/health` | 200 | model_loaded=true |
| Predict | `POST /v2/predict` | 200 | H/D/A + probabilities |
| Explain | `POST /v2/explain` | 200 | 42 SHAP contributions |
| Assistant (with Ollama) | `POST /v2/assistant/chat` | 200 | Grounded answer |
| Assistant (no Ollama) | `POST /v2/assistant/chat` | 503 | Unavailability message |
| Model info | `GET /v2/model` | 200 | Metrics + version |

---

## Verification Checklist

- [ ] Backend starts and logs `Prediction model loaded`
- [ ] `/health` returns `model_loaded: true`
- [ ] `/docs` (Swagger UI) lists the 9 `/v2` endpoints and the frozen `/v1` endpoints
- [ ] Android app opens on Fixtures, and the Settings status card shows the services online
- [ ] Prediction flow produces H/D/A result with probabilities summing to ~100%
- [ ] Explain flow shows plain-language factors with their impact
- [ ] Assistant responds (or shows unavailability message — both are correct)
- [ ] Model Information screen shows version and metrics
- [ ] Backend shutdown → app shows saved data under the offline banner within about 10 seconds, no crash

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Backend fails to start | Model missing | Run `uv run python -m training.pipeline` |
| App cannot connect | Backend not running or wrong URL | Confirm backend on `:8000`; emulator uses `10.0.2.2` |
| Assistant always 503 | Ollama not running | `ollama serve` then rebuild index |
| App crashes on launch | Koin DI error | Check `logcat` for missing module |
| Prediction returns 422 | Unknown league or team | Pick teams from the app's lists; they come from `GET /v2/teams` |

---

## Running Integration Tests

To verify end-to-end correctness programmatically:

```bash
cd ai
uv run pytest tests/integration/ -v
```

Expected output: **36 passed** (they need the trained model artifacts).

Full test suite (unit + integration):

```bash
uv run pytest
```

Expected output: **798 passed** (unit and integration).
