# goals

Dixon-Coles goals model for scorelines, expected goals and goal markets
(ADR 009). XGBoost keeps the headline home/draw/away pick; this model feeds the
extras and the assistant's league table projections.

## Modules

| Module | Responsibility |
|---|---|
| `dixon_coles.py` | `fit_dixon_coles` fits one league on matches strictly before a date: time-weighted Poisson goals with the Dixon-Coles low-score correction and L2 shrinkage. `DixonColesParams` holds the result and gives expected goals for a fixture. |
| `score_grid.py` | `score_grid` turns expected goals into an 11×11 score grid; `outcome_probabilities`, `goal_markets`, `top_scores` and `expected_goals` read everything else from it. |
| `insights.py` | `fixture_insight` bundles everything the app shows about a fixture's goals; `team_strengths` and `strength_reasons` explain them. |
| `season_table.py` | `standings` builds a league table from played matches; `project_table` simulates the remaining fixtures with the goals model (10,000 runs, fixed seed) for expected points, likely position and title, top-four and bottom-three chances (ADR 021). |

## Conventions

- A higher `attack` means more goals scored; a higher `defence` means fewer
  conceded. Team strength is `attack + defence`.
- Teams with little recent data (promoted sides) are shrunk toward the average
  of the league's three weakest established teams, mirroring the Elo rule in
  ADR 008. Teams the model has never seen use that same newcomer prior.
- The model is its parameters, so it must be refit whenever results are
  refreshed. Evaluation mirrors this with a weekly rolling-origin backtest
  (`evaluation.goals_backtest`).

## Evaluation

```bash
uv run python -m evaluation.goals_evaluation_cli
```

Tunes the time decay and shrinkage on 2022/23, then scores 2023/24, the
2024/25–2025/26 holdout and 2026/27 so far. Results are in
[docs/reports/goals-model.md](../../docs/reports/goals-model.md).
