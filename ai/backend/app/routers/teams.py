"""Teams endpoint: the teams the prediction endpoints accept."""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.app.dependencies import FixtureFeatureServiceDep, ServedCompetitionsDep
from backend.app.schemas.teams import TeamsResponse

router = APIRouter(tags=["Teams"])


@router.get(
    "/teams",
    response_model=TeamsResponse,
    summary="List teams in a served league",
    description=(
        "Returns the teams of the league's latest season the server has results "
        "for. These are the names POST /predict, /explain and /insights accept "
        "for that league. Defaults to the Premier League (ADR 012)."
    ),
    responses={
        422: {"description": "Unknown league."},
        503: {"description": "Match history not loaded."},
    },
)
def teams(
    service: FixtureFeatureServiceDep,
    competitions: ServedCompetitionsDep,
    competition: str | None = Query(
        default=None, description="League name, as listed by GET /competitions."
    ),
) -> TeamsResponse:
    """Return the league's latest season and teams."""
    return service.teams(competitions.resolve(competition))
