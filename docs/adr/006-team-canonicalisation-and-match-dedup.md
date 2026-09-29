# ADR 006 — Canonical Team Names and Match Deduplication

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

ADR 005 brings in match data from up to four sources that name the same club differently:

| Source | Example |
|---|---|
| football-data.co.uk | `Man United` |
| armin2080 (FBref), `team` column | `Manchester United` |
| armin2080 (FBref), `opponent` column | `Manchester Utd` |
| adrianjuliusaluoch (football-data.org) | `Manchester United FC` |
| enricocattaneo (Sportmonks) | `Manchester United` |

Sources also disagree on dates: football-data.org uses UTC, Sportmonks stores Europe/Rome time,
and rescheduled fixtures move. A date-based match key would fail to join the same match across
sources, and the same match appearing twice would inflate training data and could put one match in
both train and test.

## Decision

Use a versioned alias table for team names and a date-free natural key for league matches.

1. **Alias table.** `datasets/schemas/team_aliases.csv` with columns
   `team_id, canonical_name, source, source_name`. The canonical name is the football-data.co.uk
   spelling, so the existing model, SHAP output and API inputs are unchanged.
2. **Unmapped names fail the run** with the source and the unmapped name. Fuzzy matching may be used
   offline to suggest new alias rows for review, never at runtime.
3. **Match key.** Within one league season, each ordered (home, away) pair plays exactly once:

   ```
   match_key = competition | season | home_team_canonical | away_team_canonical
   ```

4. **Deduplication order.**
   1. Drop exact duplicate rows within a source and count them.
   2. Duplicate `match_key` within a source is an error.
   3. Across sources, keep the row from the highest-precedence source (ADR 005) and compare the rest.
      Different goals or result: quarantine and fail. Dates more than one day apart: warn.
      Different match statistics: keep the preferred source and log the difference.
5. **Season integrity checks** after merging, per league and season: expected team count (from a
   config table, e.g. 18 for the Bundesliga), each team plays every other team home and away once,
   all dates inside the season window. Known exceptions such as 2019/20 are whitelisted explicitly.
6. **Cup and European matches** do not use this key. They go to a separate table used only for
   rest-day features and never become training rows.
7. Deduplication runs before any train/validation/test split.

## Consequences

- One source of truth for club identity across the data pipeline, features and API.
- New clubs or new sources need alias rows before ingestion succeeds. This is deliberate friction.
- A merge report (rows per source, overlaps, conflicts, rejects) is produced on every run.
- Matches with conflicting results never reach training silently.
- Replays or neutral-venue league matches would break the one-pair-per-season assumption; the
  integrity check surfaces them for an explicit whitelist entry.
