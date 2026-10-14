# Demo Video

A 2-minute, narrated walk-through of the whole system, recorded on
14 October 2026 from `develop` (after the hosting groundwork, PRs #93 to #110).

**▶ [Watch the video](https://fip-ai.dev/demo.mp4)** (MP4, 1080p, about
4 MB, served with the [project website](../../site/README.md) from
`docs/site/demo.mp4`). English subtitles are burned into the video and also
provided as [`demo.srt`](demo.srt).

The earlier 3-minute recording of release v2.0.0 is still attached to the
[v2.0.0 release](https://github.com/SumukhaK/football-intelligence-platform/releases/tag/v2.0.0).

---

## Scenes

| Time | Scene | What you see |
|---|---|---|
| 0:00 | Title | What the project is |
| 0:13 | Architecture | Data, pipeline, models, FastAPI and the two clients |
| 0:29 | App: Sign-in | Redeeming a one-time invite code, then the consent notice |
| 0:41 | App: My Team | The favourite team's next match, the pick and why, the season outlook |
| 0:56 | App: Fixtures | League tabs over upcoming fixtures with crests |
| 1:05 | App: Prediction | Probabilities and the most likely scores |
| 1:13 | App: Explanation | SHAP factors in plain football language |
| 1:22 | App: Assistant | A match question answered with the prediction tool, on Workers AI |
| 1:34 | App: Offline | Server stopped, pull to refresh, saved data under the offline banner |
| 1:42 | Backend | The FastAPI `/docs` page with `/v2/live` and `/v2/ready` |
| 1:52 | Telemetry | One chat request's JSON log events: tool calls, the model call, tokens and cost |
| 2:06 | Close | Runs on a laptop, ready for Cloud Run |

---

## How It Was Made

- **Everything on screen is real.** The app scenes are screen recordings from
  an Android emulator against the local backend, with the assistant on
  Cloudflare Workers AI (`gemma-4-26b-a4b-it`, thinking off). The `/docs`
  page was captured with headless Microsoft Edge. The telemetry scene lists
  the real JSON log events the backend wrote for one chat request, with its
  `X-Request-ID`, trimmed to their key fields.
- **Edits.** App recordings are sped up where the narration is shorter than
  the action, and the keyboard typing in the assistant scene is cut. The
  Explanation scene is a still screenshot. The invite code shown belongs to a
  local demo account.
- **Narration.** An AI voice (`en-GB-RyanNeural` via `edge-tts`) reads the
  script. Each subtitle is one narrated sentence, timed to its audio.
- **Assembly.** ffmpeg (from the `imageio-ffmpeg` package) cut and joined the
  scenes and burned in the subtitles; title and diagram cards were drawn with
  Pillow.
