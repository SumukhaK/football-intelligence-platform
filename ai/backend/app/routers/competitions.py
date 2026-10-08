"""Competitions endpoint: the leagues the API serves (ADR 012)."""

from __future__ import annotations

from fastapi import APIRouter, Response
from fastapi.responses import RedirectResponse

from backend.app.dependencies import (
    FixtureFeatureServiceDep,
    LeagueEmblemsDep,
    OptionalInsightsServiceDep,
    ServedCompetitionsDep,
)
from backend.app.exceptions import FixtureFeaturesNotAvailableError
from backend.app.routers.teams import crest_redirect
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


@router.get(
    "/competitions/{competition}/emblem",
    response_class=RedirectResponse,
    status_code=307,
    summary="Redirect to a league's emblem image",
    description=(
        "Redirects to the league's emblem PNG, hosted by football-data.org "
        "(ADR 020). `competition` is a name as GET /competitions returns it."
    ),
    responses={
        307: {"description": "Redirect to the emblem image."},
        404: {"description": "No emblem is known for this league."},
    },
)
def league_emblem(competition: str, emblems: LeagueEmblemsDep) -> Response:
    """Redirect to the league's emblem, or 404 when it has none."""
    return crest_redirect(emblems.url(competition), competition)
