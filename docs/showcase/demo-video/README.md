# Demo Video

A 3-minute, narrated walk-through of the whole system, recorded on
29 September 2026 against release v2.0.0.

**▶ [Watch the video](https://github.com/SumukhaK/football-intelligence-platform/releases/download/v2.0.0/football-intelligence-demo.mp4)**
(MP4, 1080p, 6 MB, attached to the [v2.0.0 release](https://github.com/SumukhaK/football-intelligence-platform/releases/tag/v2.0.0)).
English subtitles are burned into the video and also provided as
[`demo.srt`](demo.srt).

---

## Scenes

| Time | Scene | What you see |
|---|---|---|
| 0:00 | Title | What the project is |
| 0:12 | Architecture | The architecture diagram from the root README |
| 0:41 | Backend | The FastAPI `/docs` page listing `/v1` and `/v2` |
| 0:57 | Predict | `POST /v2/predict` for Arsenal against Chelsea |
| 1:13 | Explain | `POST /v2/explain`: the factors behind the pick, in plain language |
| 1:26 | API v1 | The same request to `/v1`, answered by the original June model |
| 1:35 | Fixtures API | `GET /v2/fixtures` for the Bundesliga |
| 1:43 | Assistant | `POST /v2/assistant/chat`, answered by local Ollama with sources |
| 1:52 | App: Fixtures | League tabs over upcoming fixtures |
| 2:08 | App: Predict | League and teams, result, likely scores, explanation |
| 2:27 | App: Offline | Server stopped, pull to refresh, saved data under the offline banner |
| 2:43 | App: Settings | Backend status card |
| 2:49 | Close | Runs on a laptop, no cloud |

---

## How It Was Made

- **Everything on screen is real.** The terminal scenes show real responses
  from the running backend. Long outputs are trimmed, and the video marks
  each cut with "…". The app scenes are screen recordings from an Android
  emulator. Browser views were captured with headless Microsoft Edge, so no
  browser toolbar or bookmarks appear.
- **Edits.** App recordings are sped up by at most 2.5 times to match the
  narration. In the offline scene, the app waits about 50 seconds for the
  request to time out; the video cuts from the pull to the result.
- **Narration.** An AI voice (`en-GB-RyanNeural` via `edge-tts`) reads the
  script. Each subtitle is one narrated sentence, timed to its audio.
- **Assistant.** In the video, the assistant runs `qwen2.5:7b-instruct` in
  Ollama, not the default `llama3.2`, because that is the model installed on
  the recording machine. It takes about 45 seconds per answer on that
  laptop's GPU, which is longer than the app's 30-second timeout. That is why
  the assistant is shown answering in the terminal.
