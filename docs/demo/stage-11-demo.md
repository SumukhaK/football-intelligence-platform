# Stage 11 — Demo Guide

## Prerequisites

1. Backend running on `localhost:8000`:
   ```bash
   cd backend && uvicorn main:app --reload
   ```

2. Android emulator running (API 26+ recommended).

3. Install the debug APK:
   ```bash
   adb install frontend/app/build/outputs/apk/debug/app-debug.apk
   ```

---

## Demo Flow

### 1. Home Screen

Launch the app. The Home screen polls `GET /health` and shows three status chips:

- **Model**: green if the XGBoost model is loaded
- **Explainability**: green if SHAP is available
- **Assistant**: green if the Ollama assistant is reachable

If the backend is unreachable, the screen shows an error card with a Retry button.

### 2. Match Prediction

Tap **Predict Match** from Home. Select two Premier League clubs from the dropdowns (home team and away team must differ). Tap **Predict**.

The app sends `POST /predict` with 44 neutral feature values and navigates to the Result screen.

### 3. Prediction Result

The result shows:

- Predicted outcome (Home Win / Draw / Away Win)
- Three probability bars: home / draw / away
- Confidence percentage

Tap **Explain This Prediction** to continue.

### 4. Explain Prediction

The explain screen calls `POST /explain` and displays SHAP feature contributions:

- **Top positive features** — pushed the prediction toward this outcome (green values)
- **Top negative features** — pulled against this outcome (red values)

Each row shows the feature name and its SHAP value.

### 5. AI Assistant Chat

Navigate to the Assistant from Home or the bottom nav. Type a question such as:

- "Which team has the best home record this season?"
- "What is Manchester City's expected goals per game?"
- "How accurate is the prediction model?"

The assistant responds with a grounded answer from the retrieved dataset. Source citations appear below the answer if available.

If Ollama is not running, the screen shows an unavailability message instead of a chat input.

### 6. Model Information

Navigate to **Settings → Model Information**. The screen shows:

- Model version and dataset version
- Training timestamp
- Git commit (if available)
- Evaluation metrics (accuracy, F1, log-loss, etc.)

### 7. About Screen

Navigate to **Settings → About**. Shows app version, technology stack summary, and dataset metadata.

---

## Known Limitation

The prediction feature uses neutral average feature values rather than live-computed pre-match statistics. In a production scenario, these 42 features would be computed from recent form, Elo ratings, and head-to-head history fetched from the backend. The prediction flow is fully functional but the probabilities reflect average-team assumptions, not actual team strength differences.
