"""Fan-friendly names and values for model features.

SHAP explanations name features the way the pipeline does
(``home_elo_before``). This module turns each into a sentence a football fan
understands ("Arsenal team strength rating") and formats its value ("1618",
"68%", "9 of 10"), so every client shows the same wording.
"""

from __future__ import annotations

import math
from collections.abc import Callable

Formatter = Callable[[float], str]


def _whole(value: float) -> str:
    return f"{round(value):d}"


def _one_decimal(value: float) -> str:
    return f"{value:.1f}"


def _signed(value: float) -> str:
    return f"{value:+.1f}" if round(value, 1) != 0 else "0.0"


def _percent(value: float) -> str:
    return f"{round(value * 100):d}%"


def _days(value: float) -> str:
    days = round(value)
    return f"{days} day" if days == 1 else f"{days} days"


def _ordinal(value: float) -> str:
    n = round(value)
    suffix = (
        "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    )
    return f"{n}{suffix}"


def _out_of(total: int) -> Formatter:
    return lambda value: f"{round(value):d} of {total}"


def _per_side(
    side_labels: dict[str, tuple[str, Formatter]],
) -> dict[str, tuple[str, Formatter]]:
    """Expand ``{team}`` templates into home_ and away_ feature entries."""
    labels: dict[str, tuple[str, Formatter]] = {}
    for suffix, (template, fmt) in side_labels.items():
        labels[f"home_{suffix}"] = (template.replace("{team}", "{home}"), fmt)
        labels[f"away_{suffix}"] = (template.replace("{team}", "{away}"), fmt)
    return labels


_SIDE_LABELS: dict[str, tuple[str, Formatter]] = {
    "form_wins_last5": ("{team} wins in last 5 games", _out_of(5)),
    "form_wins_last10": ("{team} wins in last 10 games", _out_of(10)),
    "form_points_last5": ("{team} points from last 5 games", _out_of(15)),
    "form_points_last10": ("{team} points from last 10 games", _out_of(30)),
    "goals_scored_last5": ("{team} goals scored per game, last 5", _one_decimal),
    "goals_scored_last10": ("{team} goals scored per game, last 10", _one_decimal),
    "goals_conceded_last5": ("{team} goals conceded per game, last 5", _one_decimal),
    "goals_conceded_last10": (
        "{team} goals conceded per game, last 10",
        _one_decimal,
    ),
    "goal_diff_last5": ("{team} goal difference per game, last 5", _signed),
    "goal_diff_last10": ("{team} goal difference per game, last 10", _signed),
    "rest_days": ("{team} days of rest before the match", _days),
    "league_position": ("{team} league position", _ordinal),
    "league_points": ("{team} league points this season", _whole),
    "matches_played": ("{team} league games played this season", _whole),
    "elo_before": ("{team} team strength rating", _whole),
    "avg_opp_elo_last5": ("Strength of {team}'s last 5 opponents", _whole),
    "avg_opp_elo_last10": ("Strength of {team}'s last 10 opponents", _whole),
}

_LABELS: dict[str, tuple[str, Formatter]] = {
    **_per_side(_SIDE_LABELS),
    "home_win_pct": ("{home} win rate at home", _percent),
    "home_ppg": ("{home} points per home game", _one_decimal),
    "away_win_pct": ("{away} win rate away from home", _percent),
    "away_ppg": ("{away} points per away game", _one_decimal),
    "h2h_meetings": ("Previous meetings between the teams", _whole),
    "h2h_home_wins": ("{home} wins in previous meetings", _whole),
    "h2h_away_wins": ("{away} wins in previous meetings", _whole),
    "h2h_draws": ("Draws in previous meetings", _whole),
}


def describe_feature(
    name: str, value: float, home_team: str, away_team: str
) -> tuple[str, str]:
    """Return a fan-friendly (label, value) for one model feature."""
    template, fmt = _LABELS.get(name, (_fallback_label(name), _three_significant))
    label = template.format(home=home_team, away=away_team)
    if value is None or math.isnan(value):
        return label, "n/a"
    return label, fmt(value)


def _fallback_label(name: str) -> str:
    """Readable name for a feature without a curated label."""
    words = name.replace("_", " ").strip()
    return words[:1].upper() + words[1:]


def _three_significant(value: float) -> str:
    return f"{value:.3g}"
