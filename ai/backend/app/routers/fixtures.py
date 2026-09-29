"""Fixtures endpoint: upcoming matches per league (ADR 015)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.app.dependencies import FixturesServiceDep, ServedCompetitionsDep
from backend.app.schemas.fixtures import FixturesResponse

router = APIRouter(tags=["Fixtures"])


@router.get(
    "/fixtures",
    response_model=FixturesResponse,
    summary="List a league's upcoming fixtures",
    description=(
        "Returns the league's scheduled matches from today on, earliest first, "
        "with team names POST /predict accepts. Kick-off times carry a UTC "
        "offset and are null until the league confirms them. Defaults to the "
        "Premier League."
    ),
    responses={
        422: {"description": "Unknown league."},
        503: {"description": "No fixtures loaded yet."},
    },
)
def fixtures(
    service: FixturesServiceDep,
    competitions: ServedCompetitionsDep,
    competition: str | None = Query(
        default=None, description="League name, as listed by GET /competitions."
    ),
    limit: int = Query(
        default=50, ge=1, le=400, description="Most fixtures to return."
    ),
) -> FixturesResponse:
    """Return the league's next fixtures."""
    return service.upcoming(competitions.resolve(competition), limit)
