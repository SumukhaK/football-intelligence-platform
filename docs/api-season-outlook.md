# Season Outlook API

Current v2.6.0 contract. Paths use the `/v2` prefix. [API reference](api.md).

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
