# Backend, Assistant and Android Commands

Run from `ai/` unless a section says otherwise. [CLI index](cli.md). Shell examples use POSIX syntax; on Windows set environment variables with `$env:NAME="value"` before running the command.

## Backend API

### `uvicorn backend.app.main:app`

Starts the FastAPI backend server.

**Usage:**
```sh
# Development (auto-reload on file changes)
uv run uvicorn backend.app.main:app --reload

# Production
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

**Environment variables:**

Set them in `ai/.env` (copy `ai/.env.example`). The table summarizes selected `Settings` defaults. `.env.example` still contains `API_VERSION=2.0.0`; remove that override or set it to `2.6.0` when copying. Paths are relative to `ai/`.

| Variable | Default | Description |
|---|---|---|
| `MODEL_PATH` | `../ai/models/latest/model.joblib` | Model served by `/v2` |
| `REGISTRY_PATH` | `../ai/models/registry.json` | Model registry |
| `V1_MODEL_PATH` | `../ai/models/runs/20260630_132617/model.joblib` | Original Premier League model served by `/v1` and the unversioned paths (ADR 014) |
| `V1_MODEL_VERSION` | `20260630_132617` | Registry version of that model |
| `MATCHES_DIR` | `../datasets/processed/football_data` | Match history; the newest live or five-league dataset is loaded (ADR 008) |
| `DATASETS_DIR` | `../datasets` | Root of raw and processed data, used by the daily refresh |
| `FIXTURES_DIR` | `../datasets/processed/openfootball` | Upcoming fixtures (ADR 015) |
| `SERVED_COMPETITIONS` | `["Premier League","Bundesliga","La Liga","Serie A","Ligue 1"]` | JSON list of served leagues (ADR 012) |
| `DEFAULT_COMPETITION` | `Premier League` | League used when a request names none |
| `LIVE_REFRESH_HOUR` | `6` | Local hour (0–23) of the daily refresh; `off` turns it off (ADR 013) |
| `DRAW_POSSIBLE_THRESHOLD` | `0.28` | Draw probability at or above which `draw_possible` is true (ADR 011) |
| `API_VERSION` | `2.6.0` | API version string returned in `/health` |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FORMAT` | `text` | `json` writes one JSON object per log line in the telemetry contract's format (ADR 024) |
| `GCP_PROJECT_ID` | unset | Google Cloud project, used for the trace field on JSON log lines and by `TRACE_EXPORTER=gcp` |
| `TRACE_EXPORTER` | `none` | Where request traces go: `none`, `otlp` (a local collector) or `gcp` (Cloud Trace, needs `GCP_PROJECT_ID`) (ADR 024) |
| `OTLP_ENDPOINT` | `http://localhost:4318/v1/traces` | OTLP/HTTP traces endpoint used when `TRACE_EXPORTER=otlp` |
| `TRACE_SAMPLE_RATIO` | `1.0` | Share of requests traced, 0 to 1; logs and errors stay complete when lowered |
| `K_REVISION` | unset | Set by Cloud Run; logged as `revision` on JSON log lines |
| `TELEMETRY_SALT` | `local-dev-salt` | Key for the `user_ref` and `client_ref` hashes in logs; a secret in the cloud |
| `RATE_LIMIT_PER_MINUTE` | `120` | Requests per minute per client before a 429; `off` turns it off (ADR 014) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_CHAT_MODEL` | `qwen2.5:7b-instruct` | Chat generation model |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `ASSISTANT_VECTOR_STORE_PATH` | `assistant/vector_store` | Persisted index path |
| `ASSISTANT_KNOWLEDGE_ROOT` | `.` | Root folder of the assistant's knowledge documents |
| `ASSISTANT_TOP_K` | `5` | Top-K chunks to retrieve per query |
| `AUTH_REQUIRED` | `false` | Require invite-only sign-in and consent on every `/v2` data route, and drop `/v1` (ADR 022) |
| `ACCOUNTS_PATH` | `accounts/accounts.json` | Local accounts file (hashes only; gitignored) |
| `TEAM_CRESTS_PATH` | `../datasets/schemas/team_crests.csv` | Team name → crest URL (ADR 020) |
| `LEAGUE_EMBLEMS_PATH` | `../datasets/schemas/league_emblems.csv` | League name → emblem URL (ADR 020) |

**Endpoints:**

`/v2` is the current API (application version 2.6.0). `/v1` and the unversioned paths keep the frozen v1.0.0 contract: the original Premier League model and the original response fields. The full contract is in [`docs/api.md`](../api.md).

| Method | Path | Description |
|---|---|---|
| `GET` | `/v2/health` | Service health: model, explainability, assistant, match features and insights availability, latest result date, last refresh |
| `GET` | `/v2/model` | Served model version, training metrics, git commit |
| `GET` | `/v2/competitions` | The five served leagues and how current each one is |
| `GET` | `/v2/teams/{team}/outlook` | A team's season projection and history (ADR 023) |
| `GET` | `/v2/teams` | A league's current teams (`?competition=`) |
| `GET` | `/v2/fixtures` | A league's upcoming fixtures |
| `POST` | `/v2/predict` | Match outcome prediction (H/D/A) with probabilities |
| `POST` | `/v2/explain` | Prediction + full SHAP feature contributions |
| `POST` | `/v2/insights` | Likely scores, expected goals and goal markets from the goals model |
| `POST` | `/v2/assistant/chat` | RAG assistant chat (needs a built index and its provider: Ollama, or Workers AI with `ASSISTANT_PROVIDER=workers_ai`) |
| `GET` | `/v2/teams/{team}/crest` | Redirect to the team's crest image (ADR 020) |
| `GET` | `/v2/competitions/{competition}/emblem` | Redirect to the league's emblem image (ADR 020) |
| `POST` | `/v2/auth/redeem-invite`, `/v2/auth/login`, `/v2/auth/logout` | Invite-only sign-in (ADR 022) |
| `GET` / `POST` | `/v2/me`, `/v2/me/consent` | The signed-in user, and accepting the notice |
| `GET` | `/v2/live`, `/v2/ready` | Liveness and readiness probes (ADR 025) |
| `GET` | `/docs` | Swagger UI — interactive API documentation |
| `GET` | `/redoc` | ReDoc — alternative API documentation |

With `AUTH_REQUIRED=true`, every `/v2` data route needs `Authorization: Bearer <token>`, and `/v1` and the unversioned paths are not mounted. Health, sign-in and the crest redirects stay open.

Each client may make 120 requests a minute (`RATE_LIMIT_PER_MINUTE`). Beyond that the server answers `429` with a `Retry-After` header. Health checks and the docs are never limited.

**Sample health check:**
```sh
curl http://localhost:8000/v2/health
```

The response has `status`, `model_loaded`, `explainability_available`, `assistant_available`, `fixture_features_available`, `insights_available`, `matches_through`, `last_refresh_at`, `last_refresh_error` and `version` (see [`docs/api.md`](../api.md#get-health) for an example).

**Sample prediction:**

Only the team names are needed; the server computes the features from match history (ADR 008). `competition` is optional and defaults to the Premier League. Do not send `"features": {}`: an empty object counts as supplied features and fails with 422.

```sh
curl -s -X POST http://localhost:8000/v2/predict \
  -H "Content-Type: application/json" \
  -d '{"home_team": "Arsenal", "away_team": "Man City", "competition": "Premier League"}' \
  | python -m json.tool
```

`POST /v2/explain` takes the same body and adds SHAP feature contributions. Team names must match `/v2/teams?competition=<league>`.

### `python -m scripts.manage_accounts`

Invites people and bans or unbans accounts in `ACCOUNTS_PATH`, or in Firestore with `ACCOUNT_STORE=firestore` and `GCP_PROJECT_ID` (ADR 022, ADR 026). For Firestore, sign in first with `gcloud auth application-default login`.

```sh
uv run python -m scripts.manage_accounts invite --email sam@example.com
uv run python -m scripts.manage_accounts ban --email sam@example.com
uv run python -m scripts.manage_accounts unban --email sam@example.com
```

`invite` prints a one-time code valid for 7 days, such as `K7QM-3XWD` (8 characters without the lookalikes I, L, O, U, 0 and 1; case, spaces and dashes don't matter when it is typed); send it to the person privately. They redeem it in the app with a password of at least 10 characters. Inviting an existing account again lets them reset their password. `ban` and `unban` print the account's new status, or exit with code 1 when there is no account for the email.

### `python -m scripts.build_snapshot`

Builds or verifies the serving snapshot the container image is made from (ADR 025).

```sh
# A new snapshot of the files the API loads, with the hosted index
ASSISTANT_VECTOR_STORE_PATH=assistant/vector_store_workers_ai   uv run python -m scripts.build_snapshot --out ../snapshot

# Leave the assistant index out
uv run python -m scripts.build_snapshot --out ../snapshot --no-index

# Check a snapshot against its manifest; exits 1 on any difference
uv run python -m scripts.build_snapshot --verify ../snapshot
```

It copies both models, the registry, the newest results and fixtures datasets and the index into a new folder laid out like the repository, and writes `manifest.json` with each file's size and SHA-256 and a snapshot ID derived from them. It never writes into a folder that isn't empty. The Dockerfile verifies the snapshot during the build.

---

## AI Assistant Index

### `python -m assistant.pipeline`

Builds the RAG knowledge index with the provider `ASSISTANT_PROVIDER` names: Ollama (the default, needs `nomic-embed-text` pulled) or Workers AI (needs `WORKERS_AI_ACCOUNT_ID` and `WORKERS_AI_API_TOKEN`).

**Usage:**
```sh
# Build a fresh index from the knowledge base, replacing any existing one
uv run python -m assistant.pipeline --rebuild

# Build the index only if it does not exist yet; otherwise load it
uv run python -m assistant.pipeline

# A Workers AI index in its own folder, with its measured cut-off
ASSISTANT_PROVIDER=workers_ai VECTOR_STORE_PATH=assistant/vector_store_workers_ai \
  uv run python -m assistant.pipeline --rebuild --min-relevance 0.77
```

`--min-relevance` (default 0.81, measured for `nomic-embed-text`) is saved with the embedding model in the index's `index.json`; the backend uses that cut-off and refuses an index whose embedding model doesn't match its own.

Both print `Index built: <N> chunks in <vector store path>`. Without `--rebuild`, an existing index is loaded and its chunk count is printed; nothing is re-embedded.

**Prerequisites:**
```sh
ollama pull nomic-embed-text
ollama pull qwen2.5:7b-instruct
```

**Environment variables:** `assistant.pipeline` reads `OLLAMA_BASE_URL`, `OLLAMA_CHAT_MODEL` and `OLLAMA_EMBED_MODEL` like the backend, plus `VECTOR_STORE_PATH` (default `assistant/vector_store`) and `KNOWLEDGE_BASE_ROOT` (default `.`). The backend names those two `ASSISTANT_VECTOR_STORE_PATH` and `ASSISTANT_KNOWLEDGE_ROOT`; keep them pointing at the same place.

**Outputs:**
- `assistant/vector_store/` — persisted numpy vector store (embeddings, documents and `index.json`)

The chat model must support tool calling (`qwen2.5:7b-instruct` and the hosted default both do; see ADR 019 and the [hosted evals](../reports/hosted-assistant-evals.md)), because the assistant calls the prediction, explanation and fixtures services (ADR 018).

### `python -m evaluation.relevance_cutoff`

Embeds the abstention eval's questions with the configured provider and prints each one's best retrieval score against the configured index, then suggests a cut-off midway between the in-scope and out-of-scope groups. Exits 1 if no cut-off separates them.

```sh
ASSISTANT_PROVIDER=workers_ai VECTOR_STORE_PATH=assistant/vector_store_workers_ai \
  uv run python -m evaluation.relevance_cutoff
```

### `python -m evaluation.assistant_grounding`

Asks the assistant for the model's prediction of upcoming fixtures in every league, calls `/v2/predict` and `/v2/explain` for the same matches, and checks each answer quotes the predicted outcome's probability and contains no number those responses or the question don't account for. One extra question names a team that doesn't exist. Exits non-zero if any case fails.

```sh
LIVE_REFRESH_HOUR=off uv run python -m evaluation.assistant_grounding --per-league 2
```

### `python -m evaluation.assistant_abstention`

Asks 10 questions the knowledge base answers and 10 it doesn't, and checks the assistant answers the first set and replies "I don't have enough information in my knowledge base to answer that." to the second. Exits non-zero if any case fails.

```sh
LIVE_REFRESH_HOUR=off uv run python -m evaluation.assistant_abstention
```

### `python -m evaluation.assistant_season`

Asks seven season questions (a projected table after Boxing Day, a past champion, the next Manchester derby, most clean sheets and most goals this season, next season, a top scorer). For each it runs the season tool the answer should come from and checks the answer names the expected team and contains no number the tool, the question or today's date don't account for; the last two must be refused (ADR 021).

```sh
LIVE_REFRESH_HOUR=off uv run python -m evaluation.assistant_season
```

### `python -m evaluation.assistant_conversation`

Runs nine short scripted chats with signed history, as the app sends them (ADR 030): two "and the draw?" follow-ups that must quote the draw probability, two "why?" follow-ups that must name a team without inventing numbers, a switch to another match, an edited earlier answer that must be ignored, instructions planted in the history, a "where will we finish?" question with a favourite team set, and (with `ASSISTANT_SAFETY=true`) a harmful request split over two turns. Exits non-zero if any case fails.

```sh
LIVE_REFRESH_HOUR=off uv run python -m evaluation.assistant_conversation
```

These live assistant evaluations need the trained model, match history, fixtures, an index and its configured provider (Ollama or Workers AI); they are separate from CI scoring/unit tests. `LIVE_REFRESH_HOUR=off` stops the app from downloading new data during the run.

---

## Android Build

Run from the `frontend/` directory.

```sh
# Build the local debug APK
./gradlew assembleLocalDebug         # macOS/Linux
.\gradlew.bat assembleLocalDebug     # Windows PowerShell

# Build the staging app (needs staging.baseUrl in local.properties)
./gradlew assembleStagingDebug

# Run unit tests
./gradlew testDebugUnitTest

# Static analysis
./gradlew detekt
./gradlew spotlessCheck

# Fix formatting
./gradlew spotlessApply

# All checks, as CI runs them
./gradlew detekt testDebugUnitTest assembleDebug spotlessCheck
```

The `local` app calls the backend at `http://10.0.2.2:8000/v2` (the Android emulator's address for your computer). The `staging` app, Football Intelligence -stg, calls the address in `staging.baseUrl`.

---
