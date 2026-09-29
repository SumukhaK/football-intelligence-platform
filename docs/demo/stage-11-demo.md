# Stage 11 — Demo Guide

> Historical walkthrough of Stage 11 (v1.0.0 era). For the current system, use the root README Quick Start and [docs/demo/README.md](README.md). The steps below describe the current app.

## Prerequisites

1. Backend running on `localhost:8000`:
   ```bash
   cd ai && uv run uvicorn backend.app.main:app --reload
   ```

2. Android emulator running (API 26+ recommended).

3. Install the debug APK:
   ```bash
   adb install frontend/app/build/outputs/apk/debug/app-debug.apk
   ```

---

## Demo Flow

### 1. Fixtures Home

Launch the app. It opens on **Fixtures**: upcoming matches by date, with one tab per league. Pull down to refresh. A bottom bar leads to **Fixtures**, **Predict**, **Assistant** and **Settings**.

If the backend is unreachable, the app shows data it saved earlier under an offline banner, or an error card with a Retry button when nothing is saved yet.

### 2. Backend Status

Open **Settings**. The **Backend Status** card calls `GET /v2/health` and shows whether the Prediction API, SHAP Explainer and AI Assistant are online.

### 3. Match Prediction

Tap **Predict** in the bottom bar. Pick a league, then a home team and an away team (they must differ). Tap **Predict Match Outcome**.

The app sends `POST /v2/predict` with only the two team names and the league. The server computes the match features from history (ADR 008).

### 4. Prediction Result

The result shows:

- The predicted outcome (for example "Arsenal Win" or "Draw"), with a **Draw possible** tag when the draw chance is at least 28%
- Home / draw / away probabilities and the confidence
- The most likely scores, expected goals and goal markets from the goals model

Tap **Explain** to continue.

### 5. Explain Prediction

The explain screen calls `POST /v2/explain` and shows SHAP contributions in plain language:

- **Why the model leans this way**: factors that pushed toward the prediction
- **What counts against it**: factors that pushed away from it

Each row has a fan-friendly label and value, such as a team's home win rate, and a **Big**, **Medium** or **Small impact** tag.

### 6. AI Assistant Chat

Tap **Assistant** in the bottom bar. Type a question such as:

- "Which team has the best home record this season?"
- "What is Manchester City's expected goals per game?"
- "How accurate is the prediction model?"

The assistant responds with a grounded answer from the retrieved dataset. Source citations appear below the answer if available.

If Ollama is not running, the screen shows an unavailability message instead of a chat input.

### 7. Model Information

Navigate to **Settings → Model Information**. The screen shows:

- Model version and dataset version
- Training timestamp
- Git commit (if available)
- Evaluation metrics (accuracy, F1, log-loss, etc.)

### 8. About Screen

Navigate to **Settings → About**. Shows app version, technology stack summary, and dataset metadata.

---

## Note on Earlier Versions

At Stage 11 the app sent neutral average feature values, so predictions did not reflect real team strength. Since v2.0.0 the server computes every feature from match history (ADR 008), and that limitation no longer applies.
