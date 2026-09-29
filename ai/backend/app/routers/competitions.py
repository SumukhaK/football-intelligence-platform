"""Competitions endpoint: the leagues the API serves (ADR 012)."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.dependencies import (
    FixtureFeatureServiceDep,
    OptionalInsightsServiceDep,
    ServedCompetitionsDep,
)
from backend.app.exceptions import FixtureFeaturesNotAvailableError
from backend.app.schemas.competitions import CompetitionsResponse, CompetitionSummary

router = APIRouter(tags=["Teams"])


@router.get(
    "/competitions",
    response_model=CompetitionsResponse,
    summary="List the served leagues",
    description=(
        "Returns every league the API serves with its latest season, team count "
        "and latest result date, and whether scoreline insights are available. "
        "Leagues without loaded history are left out."
    ),
    responses={503: {"description": "Match history not loaded."}},
)
def competitions(
    fixtures: FixtureFeatureServiceDep,
    insights: OptionalInsightsServiceDep,
    served: ServedCompetitionsDep,
) -> CompetitionsResponse:
    """Return the served leagues and how current each one is."""
    summaries = []
    for name in served.names:
        try:
            teams = fixtures.teams(name)
            through = fixtures.matches_through(name)
        except FixtureFeaturesNotAvailableError:
            continue
        summaries.append(
            CompetitionSummary(
                name=name,
                season=teams.season,
                team_count=len(teams.teams),
                matches_through=through,
                insights_available=insights is not None and insights.has(name),
            )
        )
    return CompetitionsResponse(default=served.default, competitions=summaries)
