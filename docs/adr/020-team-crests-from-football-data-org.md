# ADR 020 — Team Crests from football-data.org

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The app shows team names as plain text on the fixtures list, the prediction
form and the prediction result. Showing each club's crest beside its name makes
those screens quicker to scan.

The repository already holds crest URLs in two raw sources, both from the
Kaggle downloads in ADR 005 (not committed):

| Source | Crest URLs | Coverage |
|---|---|---|
| `adrianjuliusaluoch_live_results` (football-data.org snapshot) | `homeTeam.crest`, `awayTeam.crest`, e.g. `https://crests.football-data.org/57.png` | 2023/24 to 2026/27, including this season's fixtures and the second tiers' promoted teams |
| `enricocattaneo_match_prediction` (Sportmonks) | `localTeam_logo_path`, `visitorTeam_logo_path` on `cdn.sportmonks.com` | 2015/16 to 2021/22 only |

Club crests are trademarks and copyright of the clubs. Neither source grants a
licence to redistribute them. This is a private portfolio app (not published),
so that is acceptable here, but the images should not be copied into the
repository or the app bundle.

## Decision

1. Crest URLs come from the football-data.org snapshot. Sportmonks is a
   commercial API whose CDN we have no subscription for, and its data stops in
   2022, so it misses newer and promoted teams.
2. `datasets/schemas/team_crests.csv` maps each canonical team name (ADR 006)
   to a crest URL. It holds URLs only, never images. It is rebuilt with
   `uv run python -m scripts.build_team_crests`, which matches teams by the games
   they played (league, date ±1 day and score) rather than by spelling, so no
   alias table is needed. Only PNG crests are kept because the Android image
   loader has no SVG decoder.
3. `GET /v2/teams/{team}/crest` redirects (307) to the team's crest, or returns
   404 `{"error": "No crest", ...}` when the table has none. The app builds that
   URL from its network config and never needs a crest field in other
   responses.
4. The app shows crests with Coil (already a dependency of `core-ui`) through a
   `TeamCrest` composable. A plain shield icon shows while loading and for
   teams without a crest. Crests are decorative; the team name stays as the
   text and the accessible label.

## Consequences

- No response schema changes; one new endpoint.
- The images are hot-linked from `crests.football-data.org`. If that host
  changes its URLs or blocks hot-linking, the app falls back to the shield and
  `team_crests.csv` needs rebuilding from a fresh snapshot.
- 129 teams have a crest. Ajaccio, Hertha, Sampdoria and Spezia (2022/23 only)
  have none because the snapshot starts in 2023.
- A newly promoted team has no crest until the table is rebuilt from a snapshot
  that includes it.
- Publishing the app would need permission from the clubs, or a switch to
  neutral badges such as team initials.
