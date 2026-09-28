"""Elo rating features: dynamic ratings updated after each completed match.

Each competition is a separate rating pool, because clubs in different leagues
never meet in this data and their ratings are not comparable. Ratings carry
over between seasons. A team's first match of a new season uses its previous
season's final rating regressed a third of the way back to 1500; a team that
was not in the previous season (promoted) starts at the average final rating
of the previous season's three lowest-rated teams.

Both rules only look backwards, so the rating for a fixture is the same
whether or not the rest of the new season's teams are known yet (ADR 008).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from feature_engineering.base import BaseFeature

_K = 32
_START_ELO = 1500.0
_SEASON_REGRESSION = 1.0 / 3.0
# Promoted teams start at the mean final rating of this many lowest-rated teams.
_PROMOTED_REFERENCE_TEAMS = 3

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
        return "1.2.0"

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
        ratings: dict[RatingKey, float] = {}
        pools: dict[str, _Pool] = {}
        before: list[tuple[float, float]] = []

        for row in df.itertuples(index=False):
            comp, season = str(row.competition), str(row.season)
            pool = pools.setdefault(comp, _Pool(season=season))
            if season != pool.season:
                pool.start_season(season, ratings, comp)
            home, away = str(row.home_team), str(row.away_team)
            home_elo = pool.rating_for(home, ratings, comp)
            away_elo = pool.rating_for(away, ratings, comp)
            before.append((home_elo, away_elo))

            expected_home = self._expected_score(home_elo, away_elo)
            actual_home, actual_away = _ACTUAL_SCORES[str(row.result)]
            ratings[(comp, home)] = home_elo + _K * (actual_home - expected_home)
            ratings[(comp, away)] = away_elo + _K * (
                actual_away - (1.0 - expected_home)
            )
        return before, ratings


@dataclass
class _Pool:
    """Season state for one competition's rating pool."""

    season: str
    played: set[str] = field(default_factory=set)
    previous_end: dict[str, float] = field(default_factory=dict)
    promoted_start: float = _START_ELO

    def start_season(
        self, season: str, ratings: dict[RatingKey, float], comp: str
    ) -> None:
        """Freeze last season's final ratings and move to ``season``."""
        self.previous_end = {t: ratings[(comp, t)] for t in self.played}
        lowest = sorted(self.previous_end.values())[:_PROMOTED_REFERENCE_TEAMS]
        self.promoted_start = sum(lowest) / len(lowest) if lowest else _START_ELO
        self.season, self.played = season, set()

    def rating_for(
        self, team: str, ratings: dict[RatingKey, float], comp: str
    ) -> float:
        """Return a team's pre-match rating, seeding it on its first appearance."""
        key = (comp, team)
        if team not in self.played:
            self.played.add(team)
            if team in self.previous_end:
                end = self.previous_end[team]
                ratings[key] = _START_ELO + (end - _START_ELO) * (
                    1.0 - _SEASON_REGRESSION
                )
            elif self.previous_end:
                ratings[key] = self.promoted_start
            else:
                ratings.setdefault(key, _START_ELO)
        return ratings[key]
