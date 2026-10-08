"""Which routers are mounted where (ADR 014, ADR 022)."""

from __future__ import annotations

from fastapi import Depends, FastAPI

from backend.app.dependencies import require_consented_user
from backend.app.routers import (
    assistant,
    auth,
    competitions,
    crests,
    explainability,
    fixtures,
    health,
    insights,
    model,
    outlook,
    prediction,
    teams,
    v1,
)

_V2_DATA = [
    assistant.router,
    model.router,
    prediction.router,
    explainability.router,
    teams.router,
    competitions.router,
    insights.router,
    fixtures.router,
    outlook.router,
]


def include_routers(app: FastAPI, auth_required: bool) -> None:
    """Mount v2 under /v2, and v1 under /v1 and the unversioned paths.

    Unversioned paths stay on v1 so clients built for release v1.0.0 keep
    working; they are hidden from the docs. With ``auth_required``, every v2
    data route needs a signed-in, consenting user, and v1 is not mounted at
    all, since it would bypass sign-in. Health, sign-in and crest images stay
    open.
    """
    guard = [Depends(require_consented_user)] if auth_required else []
    app.include_router(health.router, prefix="/v2")
    app.include_router(auth.router, prefix="/v2")
    app.include_router(crests.router, prefix="/v2")
    for router in _V2_DATA:
        app.include_router(router, prefix="/v2", dependencies=guard)
    if auth_required:
        return
    for router in [health.router, assistant.router, v1.router]:
        app.include_router(router, prefix="/v1")
        app.include_router(router, include_in_schema=False)
