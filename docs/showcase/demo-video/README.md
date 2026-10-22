# Demo Video

A 2½-minute, narrated walk-through of the whole system, recorded on
22 October 2026 from `develop` at release v2.6.3.

**▶ [Watch the video](https://fip-ai.dev/demo.mp4)** (MP4, 1080p, about
4 MB, served with the [project website](../../site/README.md) from
`docs/site/demo.mp4`). English subtitles are burned into the video and also
provided as [`demo.srt`](demo.srt).

The 14 October recording is in the Git history of `docs/site/demo.mp4`
(PR #111). The earlier 3-minute recording of release v2.0.0 is still attached
to the [v2.0.0 release](https://github.com/SumukhaK/football-intelligence-platform/releases/tag/v2.0.0).

---

## Scenes

| Time | Scene | What you see |
|---|---|---|
| 0:00 | Title | What the project is, and the version recorded |
| 0:14 | Architecture | Data, Drishti and the goals model, FastAPI and the clients |
| 0:30 | App: Sign-in | Redeeming a one-time invite code, then the consent notice |
| 0:43 | App: My Team | The favourite team's next match, the pick and why on one outcome bar, the season outlook and the projected table |
| 1:01 | App: Fixtures and prediction | League tabs with the favourite team's match marked, then probabilities and the likeliest scores |
| 1:13 | App: Explanation | SHAP factors for and against the pick in plain football language |
| 1:21 | App: Assistant | "Where will my team finish?" answered for Arsenal, two follow-ups that use "they" and "their", and "About N questions left today" |
| 1:48 | App: Model information | Drishti, its version and its season metrics |
| 1:56 | Backend | The FastAPI `/docs` page: accounts, preferences, the assistant and the probes |
| 2:05 | Telemetry | One chat request's JSON log events: the tool call, two model calls, tokens, cost and the history turns carried |
| 2:15 | Close | Runs on a laptop, ready for Cloud Run |

---

## How It Was Made

- **Everything on screen is real.** The app scenes are screen recordings
  (`adb screenrecord`) from a Pixel 7 emulator running the `local` debug
  build against the local backend. The backend ran with the hosted settings
  switched on: invite-only sign-in, the Llama Guard check, daily token budgets
  and JSON logs, with the assistant on Cloudflare Workers AI
  (`gemma-4-26b-a4b-it`, thinking off) and its Workers AI index. The `/docs`
  page was captured with headless Microsoft Edge. The telemetry scene lists the
  real JSON log events the backend wrote for the last chat question, with its
  `X-Request-ID`, trimmed to their key fields.
- **Edits.** App recordings are sped up or slowed to match the narration, and
  the waits between questions in the assistant scene are cut. The Explanation
  scene is a still screenshot. The invite code shown belongs to a local demo
  account.
- **Narration.** An AI voice (`en-GB-RyanNeural` via `edge-tts`) reads the
  script. Each subtitle is one narrated sentence, timed to its audio.
- **Assembly.** ffmpeg (from the `imageio-ffmpeg` package) cut and joined the
  scenes and burned in the subtitles; title, diagram and telemetry cards and
  the README thumbnail were drawn with Pillow.
