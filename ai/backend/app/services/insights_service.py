"""Insights service: scorelines and goal markets from the goals model."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from pathlib import Path

import pandas as pd

from backend.app.exceptions import UnknownTeamError
from backend.app.schemas.insights import (
    ExpectedGoals,
    GoalMarketsSchema,
    InsightsRequest,
    InsightsResponse,
    OutcomeSchema,
    ScoreProbabilitySchema,
    StrengthsSchema,
)
from goals.dixon_coles import DixonColesParams, fit_dixon_coles
from goals.insights import fixture_insight
from inference.fixture_features import find_latest_dataset


class InsightsService:
    """Answers POST /insights for the served competition."""

    def __init__(self, params: DixonColesParams, season: str, teams: list[str]) -> None:
        """Initialise with a fitted model and the season's valid team names."""
        self._params = params
        self._season = season
        self._teams = frozenset(teams)

    @property
    def model_version(self) -> str:
        """Version tag of the fitted goals model."""
        return f"dc-{self._params.fitted_before}"

    def insights(self, request: InsightsRequest) -> InsightsResponse:
        """Return the goals-model view of one fixture.

        Raises:
            UnknownTeamError: If a team did not play in the latest season.
        """
        for team in (request.home_team, request.away_team):
            if team not in self._teams:
                raise UnknownTeamError(team, self._params.competition, self._season)
        insight = fixture_insight(self._params, request.home_team, request.away_team)
        return InsightsResponse(
            home_team=insight.home_team,
            away_team=insight.away_team,
            model_version=self.model_version,
            fitted_before=self._params.fitted_before,
            expected_goals=ExpectedGoals(
                home=insight.expected_home_goals, away=insight.expected_away_goals
            ),
            top_scores=[
                ScoreProbabilitySchema(**asdict(s)) for s in insight.top_scores
            ],
            markets=GoalMarketsSchema(**asdict(insight.markets)),
            outcome=OutcomeSchema(
                home=insight.probability_home,
                draw=insight.probability_draw,
                away=insight.probability_away,
            ),
            strengths=StrengthsSchema(**asdict(insight.strengths)),
            reasons=insight.reasons,
        )


def load_insights_service(
    directory: Path, competition: str, today: date | None = None
) -> InsightsService:
    """Fit the goals model on the newest dataset's matches before ``today``.

    Fitting takes well under a second, so the server refits at every start and
    picks up each data refresh (ADR 009).

    Raises:
        FileNotFoundError: If ``directory`` holds no match dataset.
        KeyError: If the competition is not in the data.
    """
    matches = pd.read_csv(find_latest_dataset(directory), parse_dates=["match_date"])
    league = matches[matches["competition"] == competition]
    if league.empty:
        raise KeyError(competition)
    season = str(league["season"].max())
    current = league[league["season"] == season]
    teams = sorted(set(current["home_team"]) | set(current["away_team"]))
    cutoff = pd.Timestamp(today or date.today())
    params = fit_dixon_coles(league, cutoff, competition=competition)
    return InsightsService(params, season, teams)
