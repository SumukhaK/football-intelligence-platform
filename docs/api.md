# API Reference

FastAPI backend in `ai/backend/`. The OpenAPI docs are served at `/docs`, and
this page summarises the contract.

Errors return JSON `{ "error": "...", "detail": "..." }` with extra fields
where noted.

## Versions

The API has two versions (ADR 014). Every endpoint below is described as it
works in **v2**, under the `/v2` prefix, for example `POST /v2/predict`.

| Version | Paths | Model | Leagues |
|---|---|---|---|
| v2 (current) | `/v2/...` | Latest five-league model | All five (ADR 012) |
| v1 (frozen) | `/v1/...` and unversioned paths | Original model `20260630_132617` | Premier League only |

v1 keeps the release v1.0.0 contract so older clients keep working. It serves
`/health`, `/model`, `/teams`, `/predict`, `/explain` and `/assistant/chat`.
Its responses have no `competition` or `draw_possible` field, and its
explanations have no `display_name` or `display_value`. Naming any league
other than the Premier League returns 422 `Unknown competition`.
`/competitions`, `/fixtures`, `/insights` and `/teams/{team}/outlook` exist only in v2. The unversioned paths
behave exactly like `/v1` and are left out of the docs page.

## Rate limit

Each client address may make `RATE_LIMIT_PER_MINUTE` requests in any
one-minute window (default 120; `off` turns it off). Beyond that the server
answers 429 `{ "error": "Too many requests", "detail": "..." }` with a
`Retry-After` header in seconds. Health checks and the docs are never limited.

Behind a proxy, set `TRUSTED_PROXY_HOPS` to the number of proxies that append
to `X-Forwarded-For` (1 on Cloud Run). The limiter then counts the address the
outermost trusted proxy saw, so a client cannot dodge it by sending its own
`X-Forwarded-For`. With the default 0 the header is ignored.

## Request size

A request body may be at most `MAX_BODY_BYTES` (default 24576, enough for a question with its chat history, ADR 030). A larger
`Content-Length` gets 413 `Request too large`, and a chunked body with no
`Content-Length` gets 411 `Length required`. A chat `message` may be at most
1000 characters; a longer one gets 422. Every response carries
`X-Content-Type-Options: nosniff`.

## Request IDs

Every response, including 429 and 500 responses, carries an `X-Request-ID`
header. If the request sent `X-Request-ID` and its value is 8 to 64 characters
from `A-Z a-z 0-9 . _ -`, the same value is returned; otherwise the server
creates one (32 lowercase hex characters). The server's log lines for that
request carry the same ID, so quote it when reporting a problem
([telemetry contract](observability/telemetry-contract.md), ADR 024).

---

## Sign-in and consent

With `AUTH_REQUIRED=true` (staging and production), every `/v2` data route needs `Authorization: Bearer <token>` from a signed-in user who has accepted the current notice. `/v2/health`, `/docs`, `/redoc`, `/openapi.json`, the crest and emblem redirects (image loaders send no token) and the routes below stay open. `/v1` and unversioned paths are not mounted, because they would bypass sign-in. `AUTH_REQUIRED` is off by default, so local development needs no token (ADR 022).

Accounts are invite-only. The owner creates an invite with `uv run python -m scripts.manage_accounts invite --email <email>`.

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/v2/auth/redeem-invite` | `email`, `code` (as `XXXX-XXXX`; case, spaces and dashes are ignored), `password` (10+ characters) | `{ "token", "expires_at" }`. Creates the account, or resets its password with a new invite, and ends older sessions. |
| POST | `/v2/auth/login` | `email`, `password` | `{ "token", "expires_at" }`. Sessions last 30 days. |
| POST | `/v2/auth/logout` | none | 204; ends the session behind the token. |
| GET | `/v2/me` | none | `email`, `consent_required`, `consent_version`, `consent_text`, `store_questions` |
| POST | `/v2/me/consent` | `version`, `store_questions` (default false) | The updated `/v2/me` body. With `store_questions` true, each later chat question's text is kept for 90 days (not the answer, ADR 034); false stops it. |

Errors:

| Status | `error` | When |
|---|---|---|
| 400 | `Invalid invite` | No invite for this email, or the code is wrong. |
| 409 | `Invite already used` | The right code, already redeemed: the account exists, so sign in. Only the code's holder gets this answer. |
| 410 | `Invite expired` | The right code, older than 7 days: ask for a new one. |
| 401 | `Not signed in` | No token, or an unknown, expired or revoked one. |
| 401 | `Invalid credentials` | Wrong email or password; the message never says which. |
| 403 | `Consent required` | The current notice has not been accepted, or `version` is not the current one. |
| 403 | `Account blocked` | The account is banned. |
| 422 | `Password too short` | Fewer than 10 characters. |
| 429 | `Too many attempts` | 5 failed sign-ins for the email within 15 minutes; it is locked for 15 minutes. |

---

## GET /health

Service status.

```json
{
  "status": "ok",
  "model_loaded": true,
  "explainability_available": true,
  "assistant_available": false,
  "fixture_features_available": true,
  "insights_available": true,
  "matches_through": "2026-09-20",
  "last_refresh_at": "2026-09-29T07:01:31+05:30",
  "last_refresh_error": null,
  "version": "2.6.0"
}
```

`matches_through` is the date of the latest result the server holds.
`last_refresh_at` and `last_refresh_error` describe the most recent daily
refresh (ADR 013); both are null until one has run.

`fixture_features_available` is true when match history is loaded, so
requests may omit `features` (ADR 008). `insights_available` is true when the
goals model was fitted at startup, so `POST /insights` works.

## GET /v2/live and GET /v2/ready

Probes for the hosting platform (ADR 025). Both exist only under `/v2`, stay
open when `AUTH_REQUIRED` is on, and are never rate limited.

`/v2/live` answers `{"status": "alive"}` whenever the process serves requests.

`/v2/ready` answers `{"status": "ready"}` when every component predictions
need loaded at startup: the prediction model, the explainer, the match
history, the goals models, the fixtures and the season outlook. Otherwise it
answers 503:

```json
{"error": "Not ready", "detail": "Components not loaded: prediction_model"}
```

Neither probe calls the assistant's model provider, so a provider outage
never marks the API unready. `/health` stays the place for diagnostics.

## GET /model

Registry entry of the served model: `model_name`, `model_version`,
`dataset_version`, `training_timestamp`, `git_commit` and `metrics`.
`model_name` is the model's public name, `Drishti` by default
(`PREDICTION_MODEL_NAME`, ADR 033); `model_version` stays the technical
identifier. Returns 503 when no
model is registered. A model trained with a test season reports its test
metrics (`accuracy`, `log_loss`, ...). The served refit (ADR 017) has no test
season, so it reports its scores on the current season so far, named by season
(`accuracy_2026_27`, `log_loss_2026_27`, `rps_2026_27`, `brier_2026_27`).

## GET /competitions

The leagues the API serves (ADR 012): the Premier League, Bundesliga, La Liga,
Serie A and Ligue 1. Each comes with its latest season, team count, latest
result date and whether scoreline insights are available. Leagues without
loaded history are left out. Returns 503 when match history is not loaded.

```json
{
  "default": "Premier League",
  "competitions": [
    {
      "name": "Bundesliga",
      "season": "2026/27",
      "team_count": 18,
      "matches_through": "2026-09-20",
      "insights_available": true
    }
  ]
}
```

## GET /teams

Teams of a league's latest season. These are the names `/predict`, `/explain`
and `/insights` accept for that league. Pass `?competition=Bundesliga` to
choose the league; the default is the Premier League. An unknown league returns
422 `Unknown competition`.

```json
{
  "competition": "Premier League",
  "season": "2026/27",
  "teams": ["Arsenal", "Aston Villa", "..."]
}
```

Returns 503 when match history is not loaded.

## GET /teams/{team}/crest

Redirects (307) to the team's crest PNG on `crests.football-data.org`
(ADR 020). `team` is a name as `/teams` or `/fixtures` returns it, URL-encoded
(`/v2/teams/Nott'm%20Forest/crest`). A team without a known crest returns 404:

```json
{ "error": "No crest", "detail": "No crest is known for 'Atlantis'." }
```

## GET /teams/{team}/outlook

A team's projected season finish and how its chances have moved (ADR 023).
Pass `?competition=` for the league (default the Premier League). `team` is a
name from `/teams`.

The current projection plays every remaining fixture 10,000 times with the
league's goals model, the one `/insights` uses, and adds the simulated points
to today's table. `history` starts with one point before the first match,
then adds one per week of the season with matches. Each point uses only the
results before its date, and a goals model refitted on those results, so no
later information leaks in. History points use 2,000 simulations. A league's
history is computed on its first request and then cached.

```json
{
  "competition": "Premier League",
  "season": "2026/27",
  "team": "Arsenal",
  "as_of": "2026-10-08",
  "model_version": "dc-2026-10-08",
  "fitted_before": "2026-10-08",
  "simulations": 10000,
  "history_simulations": 2000,
  "projection": {
    "team": "Arsenal",
    "current_points": 13,
    "expected_points": 74.2,
    "most_likely_position": 2,
    "chance_first": 0.231,
    "chance_top_four": 0.792,
    "chance_bottom_three": 0.0
  },
  "strengths": { "attack": 1.23, "defence": 0.69 },
  "table": [ { "team": "Man City", "...": "..." } ],
  "history": [
    {
      "as_of": "2026-08-14",
      "played": 0,
      "most_likely_position": 3,
      "chance_first": 0.18,
      "chance_top_four": 0.71,
      "chance_bottom_three": 0.0
    }
  ]
}
```

- `table` holds every team's projection, highest expected points first.
- `strengths` are multiples of a league-average side, as in `/insights`. An
  attack above 1 scores more than average; a defence below 1 concedes fewer.
- `played` is the team's matches up to that point's `as_of`.
- `chance_bottom_three` is the relegation zone as three places. Some leagues
  relegate fewer directly or add a play-off.

Errors:

| Status | `error` | When |
|---|---|---|
| 422 | `Unknown competition` | The league is not served. |
| 422 | `Unknown team` | The team is not in the league this season. |
| 503 | `Season outlook not available` | No match history is loaded. |
| 503 | `Insights not available` | The league has no fitted goals model. |
| 503 | `Fixtures not available` | No fixtures dataset is loaded yet. |

## GET /competitions/{competition}/emblem

Redirects (307) to the league's emblem PNG on `crests.football-data.org`
(ADR 020). `competition` is a name as `/competitions` returns it, URL-encoded
(`/v2/competitions/Serie%20A/emblem`). A league without a known emblem returns
the same 404 `No crest` body as `/teams/{team}/crest`.

## GET /fixtures

A league's scheduled matches from today on, earliest first (ADR 015). Pass
`?competition=` to choose the league (default the Premier League) and
`?limit=` for how many to return (default 50, at most 400). Team names are the
ones `/predict` accepts. `kickoff` carries the league's UTC offset and is null
until the league confirms the time; `match_date` is always set.

```json
{
  "competition": "Premier League",
  "fixtures": [
    {
      "match_date": "2026-10-10",
      "kickoff": "2026-10-10T12:30:00+01:00",
      "home_team": "Arsenal",
      "away_team": "Leeds",
      "round": "Matchday 6"
    }
  ],
  "updated_at": "2026-09-29T07:06:38Z"
}
```

Schedules come from openfootball and are downloaded with the daily refresh,
or by hand with `uv run python -m scripts.refresh_fixtures --confirm`.
Returns 422 `Unknown competition` for an unserved league and 503
`Fixtures not available` before the first download.

## POST /predict

Predicts home win (H), draw (D) or away win (A).

Request:

| Field | Type | Required | Description |
|---|---|---|---|
| `home_team` | string | yes | A name from `/teams`. |
| `away_team` | string | yes | A name from `/teams`. |
| `competition` | string | no | A league from `/competitions`. Defaults to the Premier League. Teams must belong to it. |
| `match_date` | date | no | Only matches before this date are used. Defaults to today. |
| `features` | object | no | Pre-computed feature vector. When omitted, the server computes all 42 model features from match history with the training feature pipeline. |

```json
{ "home_team": "Arsenal", "away_team": "Man City", "match_date": "2026-10-03" }
```

Response:

```json
{
  "competition": "Premier League",
  "home_team": "Arsenal",
  "away_team": "Man City",
  "predicted_result": "H",
  "probability_home": 0.410,
  "probability_draw": 0.251,
  "probability_away": 0.340,
  "confidence": 0.410,
  "draw_possible": false,
  "model_version": "20261007_154105"
}
```

`draw_possible` is true when `probability_draw` is at least 0.28, the
`DRAW_POSSIBLE_THRESHOLD` setting. About 3 in 10 matches are flagged, and those
end level more often than the rest. It does not change `predicted_result`
(ADR 011, [draw report](reports/draw-handling.md)).

Errors:

| Status | `error` | When |
|---|---|---|
| 422 | `Unknown competition` | The league is not served. Includes `competition` and `supported`. |
| 422 | `Unknown team` | A team did not play in the league's latest season. Includes `team`. |
| 422 | `Missing feature columns` | Supplied `features` lack model columns. Includes `missing`. |
| 503 | `Model not available` | No model loaded. |
| 503 | `Match features not available` | `features` omitted and no match history loaded. |

## POST /explain

Same request and errors as `/predict`. Adds SHAP attributions in
`top_positive_features`, `top_negative_features` and `all_contributions`, plus
`model_version`, `feature_version`, `dataset_version` and
`explanation_timestamp`. Each item has:

| Field | Example | Description |
|---|---|---|
| `feature_name` | `home_elo_before` | Model feature identifier |
| `feature_value` | `1617.748` | Value used by the model, after imputation |
| `shap_value` | `0.337` | Push toward (positive) or away from the predicted outcome |
| `display_name` | `Arsenal team strength rating` | Fan-friendly label with team names filled in |
| `display_value` | `1618` | Fan-friendly value: counts ("9 of 10"), rates ("68%"), positions ("10th"), days ("7 days") |

Labels live in `ai/explainability/feature_labels.py`; every model feature has
one, and a test enforces it.

The request is the same as `/predict`, including the optional `competition`. The response echoes `competition`.

## POST /insights

The goals model's view of a fixture (ADR 009): the five most likely scores,
expected goals, goal markets, team strengths and plain-language reasons. The
server fits a Dixon-Coles model on its match history at startup, using matches
before that day. Probabilities are likelihoods, not betting advice. The headline
home/draw/away pick still comes from `POST /predict`.

Request:

```json
{ "home_team": "Arsenal", "away_team": "Chelsea", "competition": "Premier League" }
```

`competition` is optional and defaults to the Premier League. The server fits a
goals model for each served league.

Response (abridged):

```json
{
  "home_team": "Arsenal",
  "away_team": "Chelsea",
  "model_version": "dc-2026-09-28",
  "fitted_before": "2026-09-28",
  "expected_goals": { "home": 1.95, "away": 0.98 },
  "top_scores": [
    { "home": 1, "away": 1, "probability": 0.112 },
    { "home": 2, "away": 0, "probability": 0.102 }
  ],
  "markets": {
    "btts": 0.544, "over_1_5": 0.799, "over_2_5": 0.560, "over_3_5": 0.336,
    "home_clean_sheet": 0.376, "away_clean_sheet": 0.143
  },
  "outcome": { "home": 0.590, "draw": 0.235, "away": 0.175 },
  "strengths": {
    "home_attack": 1.23, "home_defence": 0.69,
    "away_attack": 1.13, "away_defence": 1.06
  },
  "reasons": [
    "Arsenal concede 31% fewer goals than an average side in this league",
    "Arsenal score 23% more goals than an average side in this league",
    "Chelsea score 13% more goals than an average side in this league"
  ]
}
```

`strengths` are multiples of a league-average side: attack above 1 scores
more, and defence below 1 concedes fewer. `home_clean_sheet` is the chance the
away side does not score.

Errors:

| Status | `error` | When |
|---|---|---|
| 422 | `Unknown team` | A team did not play in the latest season. Includes `team`. |
| 503 | `Insights not available` | The goals model could not be fitted at startup. |

## POST /assistant/chat

Retrieval-augmented answers about the project's data and models. Returns 503
when the assistant is turned off, its vector store is missing, or its model
provider is unreachable, out of quota or too slow. Predictions keep working.

`ASSISTANT_PROVIDER` chooses who answers (ADR 025): `ollama` (the default),
`workers_ai` (Cloudflare Workers AI, using `WORKERS_AI_ACCOUNT_ID`,
`WORKERS_AI_API_TOKEN`, `WORKERS_AI_CHAT_MODEL` and `WORKERS_AI_EMBED_MODEL`)
or `off`. `model` in the response names the chat model that wrote the answer.
`sources` is always empty and the answer carries no `[source: ...]` markers:
the model still cites, but the server logs its sources and citations in
`assistant.answer` instead of sending them (ADR 029).

**Chat memory (ADR 030).** To ask a follow-up, send the chat so far:

```json
{
  "message": "And the draw?",
  "conversation_id": "a1b2c3d4e5f6",
  "history": [
    {"role": "user", "content": "Who wins Everton v Chelsea?"},
    {"role": "assistant", "content": "Everton are slight favourites at 41%.",
     "signature": "<the signature that answer came with>"}
  ]
}
```

- `conversation_id` (8–64 letters, digits, `_` or `-`) is made by the app and
  is needed whenever `history` is sent. Every answer to a request with one
  carries a `signature`.
- `history` holds at most 8 messages, oldest first, each at most 1,500
  characters. Every `assistant` item must carry the `signature` its answer
  came with, signed for this user and conversation.
- If any signature is missing or wrong, the whole history is ignored, and the
  question is answered on its own; this is logged as a `guardrail.event` with
  kind `history`. History over 1,200 tokens (about 4,800 characters) is trimmed,
  oldest first, never rejected.
- The safety check reads the user's earlier questions with the new one; only the
  new one can add a strike. Numbers in the answer always come from tools called
  for this question, never from the history.
- Without `conversation_id` and `history`, the endpoint behaves as before.

**Favourite team (ADR 031).** `"favourite_team": {"team": "Man United", "competition": "Premier League"}` tells the assistant who "we" and "my team" are. Each field is at most 60 characters of letters, digits, spaces and `.'&()-`. The team is added to the question for the model and the season router, but not to the safety check or the history.

For a match prediction, its SHAP explanation or a league's upcoming fixtures,
the assistant calls tools that run the same services as `/v2/predict`,
`/v2/explain` and `/v2/fixtures`, so it quotes the latest model's numbers
(ADR 018). The chat model must support tool calling.

It can also answer season questions through internal tools: a team's results
and next meetings, and the league table on any date of a season in the data,
projected with the goals model when the date is still ahead (ADR 021). A
rule-based router reads each question first. Questions about individual
players or seasons that have not started get a fixed reply without calling
the model; those responses have `"model": "router"`, `"sources": []` and
`"confidence": 0.0`.

With `ASSISTANT_SAFETY=true` (required on Cloud Run when the assistant is on),
Llama Guard 3 checks every question before anything else (ADR 027). A harmful
question gets a fixed refusal with `"model": "safety"`, `"sources": []` and
`"confidence": 0.0`, and adds a strike to the signed-in user; the answer says
how many strikes they have. The third strike bans the account and ends its
sessions, so the next request gets `403 Account blocked`. Swearing about
football is not harmful. If the safety model can't be reached, chat returns
`503` and no strike is added.

---

## Keeping match history current

The server loads the newest `match_results_live_v*.csv` from
`datasets/processed/football_data/` at startup, falling back to the newest
`match_results_top5_v*.csv`.

It then keeps it current itself (ADR 013). Every day at `LIVE_REFRESH_HOUR`:00
local time (default 6), it downloads the season in progress and writes a new
live dataset. It then rebuilds server-side features and the goals model without
restarting. If the data is older than the last scheduled time when the server
starts, it refreshes straight away. Set `LIVE_REFRESH_HOUR=off` to turn this off, for example when working offline.

To refresh by hand instead:

```sh
uv run python -m scripts.refresh_live_dataset --confirm
```

Then restart the backend. Configure the directories with `MATCHES_DIR` and
`DATASETS_DIR`, and the leagues with `SERVED_COMPETITIONS`.
