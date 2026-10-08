"""Insights service: scorelines and goal markets from the goals model."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from backend.app.exceptions import InsightsNotAvailableError, UnknownTeamError
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

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LeagueGoalsModel:
    """One league's fitted goals model and its latest season's teams."""

    params: DixonColesParams
    season: str
    teams: frozenset[str]

    @property
    def model_version(self) -> str:
        """Version tag of the fitted goals model."""
        return f"dc-{self.params.fitted_before}"


class InsightsService:
    """Answers POST /insights for every league with a fitted goals model."""

    def __init__(self, leagues: dict[str, LeagueGoalsModel]) -> None:
        """Initialise with a fitted goals model per league name."""
        self._leagues = leagues

    def has(self, competition: str) -> bool:
        """True when ``competition`` has a fitted goals model."""
        return competition in self._leagues

    def params(self, competition: str) -> DixonColesParams | None:
        """The league's fitted goals model, or None when it has none."""
        league = self._leagues.get(competition)
        return league.params if league else None

    @property
    def model_versions(self) -> dict[str, str]:
        """Goals-model version per league."""
        return {name: m.model_version for name, m in self._leagues.items()}

    def insights(self, request: InsightsRequest, competition: str) -> InsightsResponse:
        """Return the goals-model view of one fixture in ``competition``.

        Raises:
            InsightsNotAvailableError: If the league has no fitted model.
            UnknownTeamError: If a team did not play in the league's latest season.
        """
        league = self._leagues.get(competition)
        if league is None:
            raise InsightsNotAvailableError(f"No goals model fitted for {competition}.")
        for team in (request.home_team, request.away_team):
            if team not in league.teams:
                raise UnknownTeamError(team, competition, league.season)
        params = league.params
        insight = fixture_insight(params, request.home_team, request.away_team)
        return InsightsResponse(
            competition=competition,
            home_team=insight.home_team,
            away_team=insight.away_team,
            model_version=league.model_version,
            fitted_before=params.fitted_before,
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
    directory: Path, competitions: list[str], today: date | None = None
) -> InsightsService:
    """Fit one goals model per league on the newest dataset, before ``today``.

    Fitting takes well under a second per league, so the server refits at every
    start and refresh (ADR 009, ADR 012). Leagues absent from the data are
    skipped with a warning.

    Raises:
        FileNotFoundError: If ``directory`` holds no match dataset.
        KeyError: If none of the leagues are in the data.
    """
    matches = pd.read_csv(find_latest_dataset(directory), parse_dates=["match_date"])
    cutoff = pd.Timestamp(today or date.today())
    leagues = {}
    for name in competitions:
        league = matches[matches["competition"] == name]
        if league.empty:
            logger.warning("No matches for %s; no goals model fitted.", name)
            continue
        season = str(league["season"].max())
        current = league[league["season"] == season]
        teams = frozenset(current["home_team"]) | frozenset(current["away_team"])
        params = fit_dixon_coles(league, cutoff, competition=name)
        leagues[name] = LeagueGoalsModel(params, season, teams)
    if not leagues:
        raise KeyError(", ".join(competitions))
    return InsightsService(leagues)
