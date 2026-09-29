# Plan: Serve All Five Leagues (W8)

**Status:** Draft, awaiting acceptance of [ADR 012](../adr/012-serve-all-five-leagues.md)
**Date:** 2026-09-29
**Builds on:** PRs #24–#38 (stacked; merged to main together at the end)

## Impact analysis

| Area | Files | Change | Risk |
|---|---|---|---|
| Settings | `ai/backend/app/config.py` | `served_competitions` list and `default_competition` replace `served_competition` | Low |
| Request schemas | `ai/backend/app/schemas/prediction.py`, `insights.py` | Optional `competition`, validated against served leagues | Low; additive |
| Response schemas | `prediction.py`, `explainability.py`, `insights.py` | `competition` field | Low; additive |
| New endpoint | `ai/backend/app/routers/competitions.py`, `schemas/competitions.py` | `GET /competitions` | Low |
| Teams | `ai/backend/app/routers/teams.py` | `?competition=` query parameter | Low |
| Features | `ai/backend/app/services/fixture_feature_service.py` | Competition per call instead of fixed at construction | Medium; ADR 008 parity tests must cover a second league |
| Goals model | `ai/backend/app/services/insights_service.py`, `main.py` | One fit per league; per-league team validation | Medium; five fits at startup and refresh |
| Errors | `ai/backend/app/exceptions/__init__.py` | `UnknownCompetitionError`, 422 handler | Low |
| Health | `ai/backend/app/routers/health.py` | `matches_through` stays the default league; per-league detail moves to `/competitions` | Low |
| API docs | `docs/api.md` | New endpoint, new fields, examples | Low |
| App models | `frontend/core-model` | `Competition`, `CompetitionsResponse`; `competition` on request and responses | Low |
| App network | `frontend/core-network/FootballApiService.kt` | `getCompetitions()`, `getTeams(competition)` | Low |
| App feature | `feature-prediction` ViewModel, repository, `PredictionScreen.kt`, result and explanation screens | League picker, per-league teams, league shown on results | Medium; the ViewModel gains state |
| App text | `feature-prediction` and `feature-home` `strings.xml` | Season note without a hard-coded league; home card says "Europe's top five leagues" | Low |
| Unchanged | XGBoost model, features, SHAP, draw threshold, goals-model maths | — | — |

## Tests

- **Backend services:**
  - features and insights for a non-Premier League fixture;
  - an unknown competition;
  - a team from another league (422);
  - the default competition when the field is omitted.
- **Backend endpoints:**
  - `/competitions` lists all five with seasons;
  - `/teams?competition=Serie A`;
  - `/predict` and `/insights` with and without `competition`;
  - the unknown-competition 422 body.
- **Parity:** the ADR 008 feature-equality test repeated for a second league.
- **App, written first:**
  - the ViewModel loads competitions, then the default league's teams;
  - switching league reloads teams and clears the selection;
  - requests carry the chosen league;
  - a competitions-load failure shows an error with retry;
  - the repository delegates each new call.
- **Previews:** the league picker, and team selection showing a non-Premier League league.
- **End to end:** an emulator run predicting a Bundesliga fixture through to insights and the explanation.

## Delivery

| PR | Content | Done when |
|---|---|---|
| 1 | ADR 012 and this plan | ADR accepted |
| 2 | Backend: settings, schemas, `/competitions`, `/teams?competition=`, multi-league services, docs | Endpoint and service tests pass; manual call for each league |
| 3 | App: models, network, repository, ViewModel (tests first), league picker, strings, previews | ViewModel tests, previews, emulator run |
