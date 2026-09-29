# ADR 012 — Serve All Five Leagues in the API and App

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The match model is trained on all five leagues (ADR 005) and has no
competition feature, so it already predicts Bundesliga, La Liga, Serie A and
Ligue 1 fixtures as well as Premier League ones. The live dataset and the daily
refresh (ADR 013) cover all five. Serving is the only part limited to one league:

- The backend has a single `served_competition` setting (default Premier
  League). `FixtureFeatureService`, `InsightsService` and `/teams` are built
  for that one competition only.
- Requests (`POST /predict`, `/explain`, `/insights`) name only the two teams,
  and the league is implied.
- The app's team picker, its season note ("Premier League 2026/27") and its home
  card assume the Premier League.

`FixtureFeatureBuilder` already indexes history by competition, and the goals
model is fitted per league. Most of the work is in the contract and the app.

## Decision

1. **League names are the identifier.** A league is named by the canonical
   competition string already in the data: `Premier League`, `Bundesliga`,
   `La Liga`, `Serie A`, `Ligue 1`. They are readable, already used in
   responses, and stable across seasons.
2. **Requests carry an optional `competition`.** `POST /predict`, `/explain`
   and `/insights` accept `competition`, which defaults to the Premier League.
   Existing clients keep working unchanged. An unsupported value returns
   422 `{"error": "Unknown competition", "detail": ..., "competition": ...,
   "supported": [...]}`.
3. **Responses echo the league.** Prediction, explanation and insights
   responses gain a `competition` field. The change is additive.
4. **A new `GET /competitions` endpoint.** It lists the served leagues with
   each one's current season, team count and `matches_through`. The app builds
   its league picker from it, so adding or removing a league needs no app
   release.
5. **`GET /teams` takes `?competition=`,** defaulting to the Premier League.
   Its response shape is unchanged; it already includes `competition`.
6. **Settings.** `served_competition` becomes `served_competitions` (a list,
   all five by default) plus `default_competition` (Premier League).
7. **Server-side features.** One `FixtureFeatureService` serves every league,
   with the competition passed per call. Team validation uses that league's
   latest season, so a team name is only checked against its own league.
8. **Goals model.** It is fitted once per served league at startup and after
   each refresh: five fits, well under a second in total. `InsightsService`
   holds a model per league.
9. **Draw tag and labels unchanged.** The `draw_possible` threshold (ADR 011)
   was tuned on all five leagues pooled and stays global. Explanation labels
   are already league-neutral. Per-league thresholds are revisited only if
   `evaluation.draw_analysis` shows a league's flagged draw rate falling below
   its unflagged rate.
10. **App.** The team-selection screen gets a league picker above the two team
    pickers. It is filled from `/competitions` and defaults to the Premier
    League. Changing league reloads that league's teams and clears the
    selection. The chosen league is sent with every request and shown on the
    result and explanation screens. League names come from the server. All
    other text lives in `strings.xml`, and every new composable gets a preview
    (CLAUDE.md §7).

## Alternatives rejected

- **Division codes (`E0`, `D1`, ...).** They are opaque to users and clients,
  and would need a lookup table in the app.
- **Inferring the league from the team names.** Names can collide across
  leagues and seasons, and a missing name would give a confusing error.
- **One backend instance per league.** It multiplies processes and data loads
  for no gain; the builders are already per league inside one process.
- **Hard-coding the five leagues in the app.** The app would need a release
  whenever the served set changes.

## Consequences

- Clients that send no `competition` see no change. The app gains league
  choice for all five leagues with one extra startup request.
- Every competition-aware service needs tests for each league path, and for
  unknown competitions and unknown teams within a league.
- The README accuracy table (per league, 2026/27 so far) becomes directly
  relevant to users. Model quality varies by league, and the app should not
  imply otherwise.
- Startup and the daily refresh fit five goals models instead of one. That is
  negligible, but `/health` should report insights as available when any
  league is fitted, and `/competitions` should report per-league availability.
