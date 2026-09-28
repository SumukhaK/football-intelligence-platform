"""Teams endpoint: the teams the prediction endpoints accept."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.dependencies import FixtureFeatureServiceDep
from backend.app.schemas.teams import TeamsResponse

router = APIRouter(tags=["Teams"])


@router.get(
    "/teams",
    response_model=TeamsResponse,
    summary="List teams in the served competition",
    description=(
        "Returns the teams of the latest season the server has results for. "
        "These are the names POST /predict and POST /explain accept."
    ),
    responses={503: {"description": "Match history not loaded."}},
)
def teams(service: FixtureFeatureServiceDep) -> TeamsResponse:
    """Return the latest season's teams."""
    return service.teams()
