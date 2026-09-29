"""Elo rating features: dynamic ratings updated after each completed match.

Each competition is a separate rating pool, because clubs in different leagues
never meet in this data and their ratings are not comparable. Ratings carry
over between seasons: at each new season, continuing teams regress a third of
the way back to the starting rating, and promoted teams inherit the average
end-of-season rating of the teams they replaced.
"""

from __future__ import annotations

import pandas as pd

from feature_engineering.base import BaseFeature

_K = 32
_START_ELO = 1500.0
_SEASON_REGRESSION = 1.0 / 3.0

_ACTUAL_SCORES: dict[str, tuple[float, float]] = {
    "H": (1.0, 0.0),
    "D": (0.5, 0.5),
    "A": (0.0, 1.0),
}

RatingKey = tuple[str, str]


class EloRatingFeature(BaseFeature):
    """Computes dynamic Elo ratings, recording each team's rating before the match."""

    @property
    def name(self) -> str:
        return "elo_rating"

    @property
    def version(self) -> str:
        return "1.1.0"

    @property
    def output_columns(self) -> list[str]:
        return ["home_elo_before", "away_elo_before"]

    def _expected_score(self, rating_a: float, rating_b: float) -> float:
        """Compute expected score for team A against team B."""
        return float(1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0)))

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute Elo ratings iteratively, recording pre-match ratings.

        Teams start at 1500 and are updated after each match with K=32.
        """
        before, _ = self._run(df)
        return pd.DataFrame(before, index=df.index, columns=self.output_columns)

    def final_ratings(self, df: pd.DataFrame) -> dict[RatingKey, float]:
        """Return each (competition, team) rating after the last match in ``df``."""
        _, ratings = self._run(df)
        return ratings

    def _run(
        self, df: pd.DataFrame
    ) -> tuple[list[tuple[float, float]], dict[RatingKey, float]]:
        """Replay every match in order, returning pre-match pairs and final ratings."""
        season_teams = _teams_by_season(df)
        ratings: dict[RatingKey, float] = {}
        current_season: dict[str, str] = {}
        before: list[tuple[float, float]] = []

        for row in df.itertuples(index=False):
            comp, season = str(row.competition), str(row.season)
            previous = current_season.get(comp)
            if previous is not None and previous != season:
                _start_new_season(
                    ratings,
                    comp,
                    season_teams[(comp, previous)],
                    season_teams[(comp, season)],
                )
            current_season[comp] = season

            home, away = (comp, str(row.home_team)), (comp, str(row.away_team))
            home_elo = ratings.setdefault(home, _START_ELO)
            away_elo = ratings.setdefault(away, _START_ELO)
            before.append((home_elo, away_elo))

            expected_home = self._expected_score(home_elo, away_elo)
            actual_home, actual_away = _ACTUAL_SCORES[str(row.result)]
            ratings[home] = home_elo + _K * (actual_home - expected_home)
            ratings[away] = away_elo + _K * (actual_away - (1.0 - expected_home))
        return before, ratings


def _teams_by_season(df: pd.DataFrame) -> dict[RatingKey, set[str]]:
    """Return the set of teams in each (competition, season)."""
    teams: dict[RatingKey, set[str]] = {}
    for side in ("home_team", "away_team"):
        for row in df[["competition", "season", side]].itertuples(index=False):
            key = (str(row[0]), str(row[1]))
            teams.setdefault(key, set()).add(str(row[2]))
    return teams


def _start_new_season(
    ratings: dict[RatingKey, float],
    comp: str,
    old_teams: set[str],
    new_teams: set[str],
) -> None:
    """Regress continuing teams and seed promoted teams for a new season."""
    departed = [
        ratings[(comp, t)] for t in old_teams - new_teams if (comp, t) in ratings
    ]
    promoted_start = sum(departed) / len(departed) if departed else _START_ELO
    for team in old_teams & new_teams:
        key = (comp, team)
        ratings[key] = _START_ELO + (ratings[key] - _START_ELO) * (
            1.0 - _SEASON_REGRESSION
        )
    for team in new_teams - old_teams:
        ratings[(comp, team)] = promoted_start
