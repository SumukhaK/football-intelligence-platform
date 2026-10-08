"""Team season outlook endpoint (ADR 023)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query

from backend.app.dependencies import (
    FixturesServiceDep,
    InsightsServiceDep,
    OutlookServiceDep,
    ServedCompetitionsDep,
)
from backend.app.exceptions import InsightsNotAvailableError
from backend.app.schemas.outlook import TeamOutlookResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Teams"])


@router.get(
    "/teams/{team}/outlook",
    response_model=TeamOutlookResponse,
    summary="A team's projected season finish and how its chances moved",
    description=(
        "Plays every remaining fixture of the league 10,000 times with its goals "
        "model and returns the team's most likely position, expected points and "
        "chances of finishing first, in the top four and in the bottom three, the "
        "projected table, and the team's attack and defence strengths. `history` "
        "has one point before the first match and one per week played; each uses "
        "only results before its date and a goals model fitted on them (ADR 023). "
        "`team` is a name as GET /teams returns it. Probabilities are "
        "likelihoods, not betting advice."
    ),
    responses={
        422: {"description": "Unknown league, or a team not in its latest season."},
        503: {"description": "Match history, fixtures or goals model not available."},
    },
)
def team_outlook(
    team: str,
    service: OutlookServiceDep,
    insights: InsightsServiceDep,
    fixtures: FixturesServiceDep,
    competitions: ServedCompetitionsDep,
    competition: str | None = Query(
        None, description="League; default Premier League."
    ),
) -> TeamOutlookResponse:
    """Return the team's season outlook."""
    league = competitions.resolve(competition)
    params = insights.params(league)
    if params is None:
        raise InsightsNotAvailableError(f"No goals model fitted for {league}.")
    response = service.outlook(
        team, league, fixtures.schedule(league), params, insights.model_versions[league]
    )
    logger.info(
        "outlook: %s team=%s position=%d title=%.3f",
        league,
        team,
        response.projection.most_likely_position,
        response.projection.chance_first,
    )
    return response
