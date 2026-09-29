# ADR 015 — Upcoming Fixtures from openfootball

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The app's home screen should list upcoming fixtures by date, with one tab
per served league (ADR 012). The server knows only played matches: every
dataset so far comes from football-data.co.uk results files.

football-data.co.uk also publishes `fixtures.csv`, but it only covers the
next few days. On 29 September 2026 it held 41 matches and none were in the
top five leagues, because of a midweek gap. A fixtures list built on it would
often be empty.

The openfootball project publishes each league's full season schedule as
JSON on GitHub (`football.json`, public domain). The 2026/27 files list every
remaining match for all five leagues. Dates are fixed for the whole season.
Kick-off times appear once a league confirms them, usually a few weeks ahead.

## Decision

1. **Source.** Download `{season}/{en,de,es,it,fr}.1.json` from openfootball's
   `football.json` repository, one raw partition per league per day (raw data
   stays immutable).
2. **Team names.** openfootball uses full club names ("Manchester City FC").
   A fixed table in `ai/config/team_names.py` maps each one to the
   football-data.co.uk name the rest of the system uses ("Man City"). An
   unmapped name fails the refresh loudly instead of showing a team the
   prediction endpoints would reject.
3. **Validation.** Each row is checked against `schemas/fixture.py`. A team
   never plays itself, and a home/away pairing appears once per season.
4. **Kick-off times.** openfootball times are local to the league. The server
   attaches the league's time zone and returns ISO 8601 times with an offset,
   so the app shows them in the phone's time zone. A match without a time
   has `kickoff: null` and keeps its date.
5. **Refresh.** The daily refresh (ADR 013) also rebuilds
   `processed/openfootball/fixtures_v<timestamp>.csv`. The server refreshes
   at startup when no fixtures file exists. A fixtures failure is logged and
   never blocks the results refresh.
6. **API.** `GET /v2/fixtures?competition=` returns the league's fixtures from
   today on, sorted by date. It exists in v2 only (ADR 014).

## Alternatives rejected

- **football-data.co.uk `fixtures.csv`.** It uses the same team names, but it
  covers only a few days ahead and is often empty for the five leagues.
- **A fixtures API (football-data.org, API-Football).** These need an API key,
  which breaks the rule that local development needs no accounts, and they add
  rate limits.
- **Fuzzy name matching.** It is silent when wrong. A fixed table is small
  (96 clubs) and a test proves it covers the current season.

## Consequences

- A second provider, `openfootball`, appears under `datasets/raw` and
  `datasets/processed`.
- Promoted clubs need a line in the name table each summer. The refresh fails
  with the missing names until they are added.
- Fixtures are for display. Predictions still come from `POST /v2/predict`.
