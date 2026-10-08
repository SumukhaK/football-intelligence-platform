"""Teams endpoint: the teams the prediction endpoints accept."""

from __future__ import annotations

from fastapi import APIRouter, Query, Response
from fastapi.responses import JSONResponse, RedirectResponse

from backend.app.dependencies import (
    FixtureFeatureServiceDep,
    ServedCompetitionsDep,
    TeamCrestsDep,
)
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


@router.get(
    "/teams/{team}/crest",
    response_class=RedirectResponse,
    status_code=307,
    summary="Redirect to a team's crest image",
    description=(
        "Redirects to the team's crest PNG, hosted by football-data.org (ADR 020). "
        "`team` is a name as GET /teams or GET /fixtures returns it."
    ),
    responses={
        307: {"description": "Redirect to the crest image."},
        404: {"description": "No crest is known for this team."},
    },
)
def team_crest(team: str, crests: TeamCrestsDep) -> Response:
    """Redirect to the team's crest, or 404 when it has none."""
    url = crests.url(team)
    if url is None:
        return JSONResponse(
            status_code=404,
            content={"error": "No crest", "detail": f"No crest is known for '{team}'."},
        )
    return RedirectResponse(url, status_code=307)
