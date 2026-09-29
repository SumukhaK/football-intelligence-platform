# ADR 008 — Compute Match Features on the Server

**Status:** Accepted

**Supersedes:** —
**Superseded by:** [012](012-serve-all-five-leagues.md) (item 6, Premier League-only scope, only)

## Context

`POST /predict` and `POST /explain` require the caller to send all 42 pre-match
features. The Android app cannot compute them, so it sends a fixed map from
`buildNeutralFeatures()` in `frontend/core-model/.../Team.kt`.

That map is not merely neutral, it is wrong: its names do not match the model's
(`home_elo` instead of `home_elo_before`, `h2h_matches` instead of
`h2h_meetings`, `home_position` instead of `home_league_position`, and so on).
`MatchPredictor` rejects requests with missing columns
(`ai/inference/predictor.py:46`), so app predictions fail with a
missing-features error. The app's team list is also hardcoded to the 2023/24
Premier League.

Since ADR 005 the server holds 26 seasons of results and a feature pipeline
that computes exactly the features the model was trained on.

## Decision

The backend computes features for a requested fixture from match history, using
the same feature pipeline as training.

1. **Feature service.** A backend service loads the latest processed
   `match_results_top5` dataset once at startup. For a fixture (home team, away
   team, date) it appends one row after the last completed match and runs the
   registered feature modules, then returns that row's 42 features. Every
   feature already ignores the current row's result, so training and serving
   compute identical values.
2. **API, backwards compatible.** `features` becomes optional on
   `PredictionRequest`. When absent, the server computes them; when present,
   behaviour is unchanged. An optional `match_date` defaults to today.
3. **Teams endpoint.** `GET /teams?competition=Premier League` returns the teams
   of the latest season in the data, so the app stops hardcoding them.
4. **Unknown teams** return a structured 422 error naming the team, not a
   prediction from imputed values.
5. **Android.** The ViewModel stops sending features and loads teams from
   `GET /teams`. `buildNeutralFeatures()` is deleted.
6. **Scope.** Premier League only, as ADR 005 requires; other leagues need their
   own ADR.

## Decisions made during implementation

- **In-progress season included.** `scripts.refresh_live_dataset` appends the
  current season's played matches (partial-season checks, ADR 006) to the
  completed history as `match_results_live_v<timestamp>.csv`. The backend loads
  the newest live dataset, falling back to the completed history.
- **Per-request computation, benchmarked first.** Baseline for the full
  pipeline on 46,959 matches was 31 s, 26 s of it in league position. After
  rewriting league position and rest days (identical output), the full
  pipeline takes about 3.8 s. One Premier League fixture takes about 0.9 s,
  and repeat requests are served from a per-fixture cache.
- **Elo season rules made backward-looking.** An equivalence test showed that
  promoted teams' ratings differed between training and serving, because the
  old rule needed the new season's full team list. Promoted teams now start
  at the mean final rating of the previous season's three lowest-rated teams.
  The model was retrained and re-evaluated (log loss 0.976 on 2023/24, 0.996
  on the holdout, previously 0.975 and 0.995) and promoted as
  `20260928_123224`.

## Consequences

- App predictions work and reflect real team strength.
- The server needs the processed dataset at startup; a missing dataset disables
  server-side features with a clear health flag, not a crash.
- Feature computation per request reruns the pipeline over the history. A
  benchmark is required first (CLAUDE.md §20); caching the state as of the last
  match is the expected optimisation if latency is too high.
- `docs/api.md` documents the new optional fields and `GET /teams`.
