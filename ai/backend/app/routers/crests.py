"""Crest and emblem redirects (ADR 020).

Kept apart from the data routers so they stay open when sign-in is required
(ADR 022): image loaders don't send the session token, and the images are
public football-data.org files anyway.
"""

from __future__ import annotations

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse, RedirectResponse

from backend.app.dependencies import LeagueEmblemsDep, TeamCrestsDep

router = APIRouter(tags=["Teams"])


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
    return crest_redirect(crests.url(team), team)


def crest_redirect(url: str | None, name: str) -> Response:
    """A 307 to ``url``, or a structured 404 naming ``name`` when there is none."""
    if url is None:
        return JSONResponse(
            status_code=404,
            content={"error": "No crest", "detail": f"No crest is known for '{name}'."},
        )
    return RedirectResponse(url, status_code=307)


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
