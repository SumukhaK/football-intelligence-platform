# ADR 023 — Team Season Outlook Endpoint

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The app's My Team tab shows the favourite team's next match. Fans also want
to know how the season will end for their team: where it will finish, and its
chances of winning the league, finishing in the top four or going down, plus
how those chances have moved since the season started.

ADR 021 added a season projection for the assistant: `project_table` plays
every remaining fixture 10,000 times with a league's Dixon-Coles goals model
(ADR 009) and adds the simulated points to the real table. Only the assistant
can call it, and it projects only from today, using the model fitted at
startup. A history of chances needs a projection *as it stood* on earlier
dates. Reusing today's model for those dates would leak later results into
them, so the history would look wiser than it was.

## Decision

1. **Endpoint.** `GET /v2/teams/{team}/outlook?competition=` returns:
   - the team's projected finish: most likely position, current and expected
     points, and the chance of finishing first, in the top four and in the
     bottom three;
   - the projected league table those numbers come from;
   - the team's attack and defence strengths from the league's goals model,
     as `/insights` reports them;
   - a history of the same chances through the season.

   It is v2 only, behind the same sign-in guard as the other data routes
   (ADR 022).
2. **Current projection.** This is `project_table` over today's table and
   every unplayed fixture, using the goals model `/insights` uses
   (`fitted_before` in the response), with 10,000 simulations, as in ADR 021.
3. **History without look-ahead.** History has one point per week of the
   season in which the league played, plus one before the first match:
   - Each point's cutoff is the Monday after that week. Monday matches count
     towards the following week.
   - The table holds only matches played before the cutoff.
   - The goals model is refitted on matches before the cutoff, the same way
     `/insights` uses `fitted_before`.
   - The remaining fixtures are this season's matches played on or after the
     cutoff, plus scheduled fixtures not yet played.

   Only the fixture list, which was known at the time, comes from later data.
4. **Cost and caching.** A refit takes about 0.09 s and a full-season
   projection about 0.16 s at 2,000 simulations (0.68 s at 10,000), measured
   on the Premier League 2026/27 data. History points therefore use 2,000
   simulations. At that count, a 30% chance carries a standard error of about
   1 point. A league's points are computed on its first request and cached
   in memory, shared by every team in the league. Past points never change,
   and the daily refresh (ADR 013) builds a new service, which starts an
   empty cache. A full season is about 40 points, roughly 10 s for the first
   request.
5. **Relegation is the bottom three.** "Relegation" means finishing in the
   bottom three, the same column the assistant uses. Ligue 1 relegates two
   teams directly, and the Bundesliga and Ligue 1 add a play-off for 16th.
   The field is named `chance_bottom_three` so the API does not claim more
   than it computes. The same applies to "top four", which is not every
   league's Champions League line.

## Consequences

- The My Team tab can show a season outlook that is honest about its past
  points: each one used only what was known on its date.
- The first request per league after a start or refresh is slow, up to about
  10 s late in the season. Later requests come from the cache in well under a
  second.
- 2,000-simulation history points are slightly noisier than the
  10,000-simulation current projection. The response states both counts.
- Postponed matches are treated as remaining fixtures until they are played,
  which is how the table stood at the time.
