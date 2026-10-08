# Backend

FastAPI application serving match predictions, SHAP explanations, goals-model
insights, upcoming fixtures and the grounded assistant through a versioned,
documented REST API.

This folder is a placeholder: the code lives in the `ai/` Python workspace at
`ai/backend/`, so it can import the model, feature and assistant packages
directly.

---

## Ownership

Backend implementation. Follows the standards defined in `.claude/CLAUDE.md` section 8.

---

## Architecture

Clean Architecture with strict layer separation.

- **Schemas:** Pydantic request/response models with field-level validation.
- **Services:** Thin adapters that convert API types to AI-layer types and back.
- **Routers:** FastAPI route handlers — no business logic, only HTTP concerns.
- **Dependencies:** FastAPI `Depends` functions that read from `app.state`.
- **Lifespan:** Both models, the match history, goals models and fixtures load once at startup; the daily refresh reloads the data without a restart (ADR 013).
- **Middleware:** A per-client sliding-window rate limiter (ADR 014).
- **Sign-in:** Invite-only accounts in a JSON file; with `AUTH_REQUIRED=true` every `/v2` data route needs a signed-in user who accepted the notice (ADR 022).

---

## Directory Structure

```
ai/backend/
  app/
    config.py           # pydantic-settings configuration
    consent.py          # The notice users accept, and its version (ADR 022)
    dependencies.py     # Depends functions reading services from app.state
    main.py             # App factory and lifespan
    routing.py          # Which routers are mounted under /v2, /v1 and unversioned
    exceptions/         # Domain errors and structured JSON handlers
    middleware/
      rate_limit.py     # Sliding-window rate limiter, 429 with Retry-After
    routers/
      health.py         # GET /health
      model.py          # GET /model
      competitions.py   # GET /competitions
      teams.py          # GET /teams
      fixtures.py       # GET /fixtures
      prediction.py     # POST /predict
      explainability.py # POST /explain
      insights.py       # POST /insights
      assistant.py      # POST /assistant/chat
      auth.py           # /auth/redeem-invite, /auth/login, /auth/logout, /me
      crests.py         # Crest and emblem redirects (ADR 020)
      v1.py             # The frozen v1 contract on the original model
    schemas/            # Request and response models, one file per area
    services/           # Prediction, explanation, insights, fixtures,
                        # match features, chat, season, assistant tools,
                        # crests, accounts and daily refresh services
```

---

## Running Locally

```bash
cd ai
uv run uvicorn backend.app.main:app --reload
```

The server starts on `http://127.0.0.1:8000`. Interactive docs at `/docs`.

---

## API Versions and Endpoints

`/v2/...` is current: five leagues and the latest model. `/v1/...` and the
unversioned paths keep the release v1.0.0 contract with the original Premier
League model (ADR 014). The full contract is in [docs/api.md](../docs/api.md).

| Method | Path (under `/v2`)   | Description                                         |
|--------|----------------------|-----------------------------------------------------|
| GET    | /health              | Service health, data freshness, last refresh        |
| GET    | /model               | Model version and training metrics                  |
| GET    | /competitions        | The five served leagues                             |
| GET    | /teams               | A league's current teams                            |
| GET    | /fixtures            | A league's upcoming fixtures (ADR 015)              |
| POST   | /predict             | Win/draw/loss probabilities and the draw tag        |
| POST   | /explain             | Prediction plus SHAP feature contributions          |
| POST   | /insights            | Likely scores and goal markets (goals model)        |
| POST   | /assistant/chat      | Retrieval-grounded answers                          |
| GET    | /teams/{team}/crest  | Redirect to the team's crest (ADR 020)              |
| GET    | /competitions/{competition}/emblem | Redirect to the league's emblem       |
| POST   | /auth/redeem-invite  | Set a password with an invite code, sign in         |
| POST   | /auth/login          | Sign in, returns a session token                    |
| POST   | /auth/logout         | End the session                                     |
| GET    | /me                  | The signed-in user and the notice                   |
| POST   | /me/consent          | Accept the notice                                   |

With `AUTH_REQUIRED=true`, the data routes need a bearer token and `/v1` and
the unversioned paths are not mounted. Health, sign-in and the crest
redirects stay open (ADR 022).

### Error Responses

All errors return structured JSON:
```json
{ "error": "...", "detail": "..." }
```

| HTTP | Condition                                         |
|------|---------------------------------------------------|
| 400  | Invite code wrong, used or expired                |
| 401  | Not signed in, or wrong email or password         |
| 403  | Notice not accepted, or account blocked           |
| 404  | No crest or emblem known for the name             |
| 422  | Validation failure, unknown league or team, password too short |
| 429  | Rate limit reached (`Retry-After` gives seconds), or too many failed sign-ins |
| 503  | Model, match history, fixtures or assistant not loaded |
| 500  | Unexpected server error                           |

---

## Configuration

Set via environment variables or `ai/.env`. The settings, with their defaults and
comments, are listed in [`ai/.env.example`](../ai/.env.example): model paths
for both API versions, data directories, served leagues, the daily refresh
hour, the draw threshold, the rate limit, the assistant, and sign-in
(`AUTH_REQUIRED`, default `false`; `ACCOUNTS_PATH`, default
`accounts/accounts.json`), and the crest tables (`TEAM_CRESTS_PATH`,
`LEAGUE_EMBLEMS_PATH`).

---

## Testing

Tests live at `ai/tests/backend/`, with end-to-end tests in
`ai/tests/integration/`. Run from the `ai/` directory:

```bash
cd ai
uv run pytest tests/backend/ -v
```

224 backend tests cover every endpoint in both versions, the rate limiter,
fixtures, sign-in, crests, the assistant's tools and season router, startup,
error paths and the service units.

---

## Development Standards

- One router per domain area. Routers contain no business logic.
- Service classes adapt AI types to API types. No ML logic in services.
- All request and response bodies are Pydantic models with field-level validation.
- Errors return structured JSON: `{ "error": "...", "detail": "..." }`.
- All endpoints have OpenAPI docstrings.
- Environment config via `pydantic-settings`. No `os.environ` in code.
