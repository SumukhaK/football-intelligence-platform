"""Authenticated account preference endpoints (ADR 035)."""

from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from starlette.responses import Response

from backend.app.dependencies import (
    OptionalFixtureFeatureServiceDep,
    ServedCompetitionsDep,
    SignedInUserDep,
)
from backend.app.schemas.account_preferences import (
    AccountPreferencesError,
    AccountPreferencesResponse,
    SaveFavouriteRequest,
)
from backend.app.services.account_preferences_service import (
    AccountPreferencesService,
    InvalidFavouriteError,
)


class PreferencesRoute(APIRoute):
    """Keep validation failures in the account API's structured error format."""

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        """Convert invalid preference bodies without changing older endpoints."""
        handler = super().get_route_handler()

        async def validated(request: Request) -> Response:
            try:
                return await handler(request)
            except RequestValidationError as exc:
                raise InvalidFavouriteError(
                    "Provide a valid favourite league and team."
                ) from exc

        return validated


router = APIRouter(tags=["Accounts"], route_class=PreferencesRoute)
ERRORS: dict[int | str, dict[str, Any]] = {
    401: {
        "description": "Missing, expired or revoked session.",
        "model": AccountPreferencesError,
    },
    403: {"description": "Account blocked.", "model": AccountPreferencesError},
    503: {
        "description": "Account store, preference or team catalog unavailable; retry.",
        "model": AccountPreferencesError,
    },
}


def get_preferences_service(
    request: Request,
    competitions: ServedCompetitionsDep,
    catalog: OptionalFixtureFeatureServiceDep,
) -> AccountPreferencesService:
    """Use the account store already owned by this application."""
    return AccountPreferencesService(
        request.app.state.account_store, competitions, catalog
    )


ServiceDep = Annotated[AccountPreferencesService, Depends(get_preferences_service)]


@router.get(
    "/me/preferences",
    response_model=AccountPreferencesResponse,
    responses=ERRORS,
    summary="Read the signed-in account's favourite",
)
def preferences(
    user: SignedInUserDep, service: ServiceDep
) -> AccountPreferencesResponse:
    """Return canonical preferences; successful null alone means no favourite."""
    return service.read(user)


@router.put(
    "/me/preferences",
    response_model=AccountPreferencesResponse,
    responses={
        **ERRORS,
        422: {
            "description": "Invalid canonical league/team pair or body.",
            "model": AccountPreferencesError,
        },
    },
    summary="Save the signed-in account's favourite",
)
def save_preferences(
    body: SaveFavouriteRequest,
    user: SignedInUserDep,
    service: ServiceDep,
) -> AccountPreferencesResponse:
    """Validate against /teams and patch only the bearer account's favourite."""
    return service.save(user, body.favourite)
