# Screenshots — Capture Checklist

This directory holds screenshots referenced by the root [README.md](../../../README.md) and [project-showcase.md](../project-showcase.md). None have been captured yet. This file defines what to capture and how, so anyone can complete the set without guessing.

---

## Required Screenshots

| File | Source | What to capture |
|---|---|---|
| `fixtures-screen.png` | Android app | Home screen: Premier League fixtures by date, with the league tabs and bottom bar visible |
| `offline-banner.png` | Android app | Any screen with the backend stopped, showing the offline banner over saved data |
| `prediction-screen.png` | Android app | Match Prediction screen with a league chosen and both teams selected, ready to submit |
| `prediction-result.png` | Android app | Prediction Result screen showing the outcome, a single win/draw/loss probability bar and the likely scores |
| `explainability-screen.png` | Android app | Explain Prediction screen showing both positive and negative SHAP feature sections |
| `assistant-screen.png` | Android app | AI Assistant Chat screen mid-conversation, with a follow-up answer and the New chat action; sources are logged rather than displayed (ADR 029) |
| `settings-screen.png` | Android app | Settings screen with the backend status card, ideally all green |
| `model-info-screen.png` | Android app | Model Information screen showing version, dataset version, and evaluation metrics |
| `architecture-diagram.png` | Rendered Mermaid | The architecture diagram from the root README, rendered (e.g., via GitHub's native Mermaid rendering, exported as PNG) |
| `api-docs.png` | Browser | FastAPI's auto-generated `/docs` Swagger UI, showing the v1 and v2 endpoint groups |

---

## Capture Instructions

### Android Screens

1. Start the backend: `cd ai && uv run uvicorn backend.app.main:app --reload`
2. Launch the app on an emulator: `cd frontend && ./gradlew assembleLocalDebug && adb install app/build/outputs/apk/local/debug/app-local-debug.apk`
3. Use the emulator's built-in screenshot tool (or `adb exec-out screencap -p > screenshot.png`)
4. Crop to the device frame; no need to include emulator chrome

### API Docs

1. With the backend running, open `http://127.0.0.1:8000/docs` in a browser
2. Expand the v2 endpoints before capturing
3. Use a clean browser window (no extra tabs/bookmarks bar) for a professional look

### Architecture Diagram

1. The Mermaid diagram in the root README renders natively on GitHub — navigate to the README on GitHub and screenshot the rendered diagram
2. Alternatively, paste the Mermaid source into the [Mermaid Live Editor](https://mermaid.live) and export as PNG

---

## Naming Convention

All files lowercase, kebab-case, `.png` format, placed directly in this directory. Once captured, embed them in the root [README](../../../README.md) with `![Alt text](docs/showcase/screenshots/filename.png)`.
