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
`/competitions`, `/fixtures` and `/insights` exist only in v2. The unversioned paths
behave exactly like `/v1` and are left out of the docs page.

## Rate limit

Each client address may make `RATE_LIMIT_PER_MINUTE` requests in any
one-minute window (default 120; `off` turns it off). Beyond that the server
answers 429 `{ "error": "Too many requests", "detail": "..." }` with a
`Retry-After` header in seconds. Health checks and the docs are never limited.

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
  "version": "2.0.0"
}
```

`matches_through` is the date of the latest result the server holds.
`last_refresh_at` and `last_refresh_error` describe the most recent daily
refresh (ADR 013); both are null until one has run.

`fixture_features_available` is true when match history is loaded, so
requests may omit `features` (ADR 008). `insights_available` is true when the
goals model was fitted at startup, so `POST /insights` works.

## GET /model

Registry entry of the served model: `model_version`, `dataset_version`,
`training_timestamp`, `git_commit` and `metrics`. Returns 503 when no
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
when the assistant's vector store or Ollama is unavailable.

For a match prediction, its SHAP explanation or a league's upcoming fixtures,
the assistant calls tools that run the same services as `/v2/predict`,
`/v2/explain` and `/v2/fixtures`, so it quotes the latest model's numbers
(ADR 018). `OLLAMA_CHAT_MODEL` must name a model that supports tool calling.
The request and response bodies are unchanged.

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
