"""Everything the app shows about a fixture's goals, from one fitted model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from goals.dixon_coles import DixonColesParams
from goals.score_grid import (
    GoalMarkets,
    ScoreProbability,
    expected_goals,
    goal_markets,
    outcome_probabilities,
    score_grid,
    top_scores,
)

TOP_SCORES = 5
MAX_REASONS = 3
# Effects smaller than this are not worth a sentence.
_MIN_EFFECT = 0.05


@dataclass(frozen=True)
class TeamStrengths:
    """Attack and defence of both sides, as multiples of a league-average side."""

    home_attack: float
    home_defence: float
    away_attack: float
    away_defence: float


@dataclass(frozen=True)
class FixtureInsight:
    """Goals-model view of one fixture."""

    home_team: str
    away_team: str
    expected_home_goals: float
    expected_away_goals: float
    top_scores: list[ScoreProbability]
    markets: GoalMarkets
    probability_home: float
    probability_draw: float
    probability_away: float
    strengths: TeamStrengths
    reasons: list[str]


def fixture_insight(
    params: DixonColesParams, home_team: str, away_team: str
) -> FixtureInsight:
    """Score grid, markets, strengths and reasons for ``home_team`` v ``away_team``."""
    lam, mu = params.expected_goals(home_team, away_team)
    grid = score_grid(lam, mu, params.rho)
    home_xg, away_xg = expected_goals(grid)
    p_home, p_draw, p_away = outcome_probabilities(grid)
    strengths = team_strengths(params, home_team, away_team)
    return FixtureInsight(
        home_team=home_team,
        away_team=away_team,
        expected_home_goals=home_xg,
        expected_away_goals=away_xg,
        top_scores=top_scores(grid, TOP_SCORES),
        markets=goal_markets(grid),
        probability_home=p_home,
        probability_draw=p_draw,
        probability_away=p_away,
        strengths=strengths,
        reasons=strength_reasons(strengths, home_team, away_team),
    )


def team_strengths(
    params: DixonColesParams, home_team: str, away_team: str
) -> TeamStrengths:
    """Goals scored and conceded relative to an average side (1.0 = average).

    Defence is expressed as goals conceded, so below 1.0 is a good defence.
    """

    def attack(team: str) -> float:
        return float(np.exp(params.attack.get(team, params.newcomer_attack)))

    def conceded(team: str) -> float:
        return float(np.exp(-params.defence.get(team, params.newcomer_defence)))

    return TeamStrengths(
        home_attack=attack(home_team),
        home_defence=conceded(home_team),
        away_attack=attack(away_team),
        away_defence=conceded(away_team),
    )


def strength_reasons(
    strengths: TeamStrengths, home_team: str, away_team: str
) -> list[str]:
    """Up to three plain-language reasons, strongest effect first."""
    effects = [
        (strengths.home_attack, home_team, "score"),
        (strengths.home_defence, home_team, "concede"),
        (strengths.away_attack, away_team, "score"),
        (strengths.away_defence, away_team, "concede"),
    ]
    ranked = sorted(effects, key=lambda e: abs(np.log(e[0])), reverse=True)
    reasons = []
    for multiple, team, verb in ranked:
        change = multiple - 1
        if abs(change) < _MIN_EFFECT:
            continue
        direction = "more" if change > 0 else "fewer"
        reasons.append(
            f"{team} {verb} {abs(change):.0%} {direction} goals "
            "than an average side in this league"
        )
    return reasons[:MAX_REASONS]
