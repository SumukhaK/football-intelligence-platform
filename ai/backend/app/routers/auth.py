"""Sign-in and consent endpoints (ADR 022)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header

from backend.app.consent import CONSENT_TEXT, CONSENT_VERSION
from backend.app.dependencies import AccountServiceDep, SignedInUserDep, bearer_token
from backend.app.schemas.auth import (
    ConsentRequest,
    LoginRequest,
    MeResponse,
    RedeemInviteRequest,
    SessionResponse,
)
from backend.app.services.account_service import NewSession
from backend.app.services.account_store import User

router = APIRouter(tags=["Accounts"])
_ERRORS = {
    400: {"description": "Invite code wrong, used or expired."},
    401: {"description": "Not signed in, or wrong email or password."},
    403: {"description": "Account blocked."},
    429: {"description": "Too many failed sign-ins for this email."},
}


@router.post(
    "/auth/redeem-invite",
    response_model=SessionResponse,
    summary="Redeem an invite",
    description=(
        "Sets the password for an invited email with the one-time code from "
        "the owner, and signs in. Redeeming a new code resets the password."
    ),
    responses={400: _ERRORS[400], 422: {"description": "Password too short."}},
)
def redeem_invite(
    body: RedeemInviteRequest, accounts: AccountServiceDep
) -> SessionResponse:
    """Create or reset the account and return a session token."""
    return _session(accounts.redeem_invite(body.email, body.code, body.password))


@router.post(
    "/auth/login",
    response_model=SessionResponse,
    summary="Sign in",
    description="Returns a session token valid for 30 days.",
    responses={401: _ERRORS[401], 403: _ERRORS[403], 429: _ERRORS[429]},
)
def login(body: LoginRequest, accounts: AccountServiceDep) -> SessionResponse:
    """Check the password and return a session token."""
    return _session(accounts.login(body.email, body.password))


@router.post(
    "/auth/logout",
    status_code=204,
    summary="Sign out",
    description="Ends the session behind the bearer token.",
)
def logout(
    accounts: AccountServiceDep,
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Revoke the current session."""
    accounts.logout(bearer_token(authorization))


@router.get(
    "/me",
    response_model=MeResponse,
    summary="The signed-in user",
    description=(
        "Email, whether the current notice still needs accepting, and the "
        "notice itself."
    ),
    responses={401: _ERRORS[401], 403: _ERRORS[403]},
)
def me(user: SignedInUserDep) -> MeResponse:
    """Describe the signed-in user."""
    return _me(user)


@router.post(
    "/me/consent",
    response_model=MeResponse,
    summary="Accept the notice",
    description="Records that the user accepted the current notice version.",
    responses={401: _ERRORS[401], 403: {"description": "Outdated version."}},
)
def consent(
    body: ConsentRequest, user: SignedInUserDep, accounts: AccountServiceDep
) -> MeResponse:
    """Record consent to the current notice."""
    return _me(accounts.record_consent(user, body.version, body.store_questions))


def _session(session: NewSession) -> SessionResponse:
    return SessionResponse(token=session.token, expires_at=session.expires_at)


def _me(user: User) -> MeResponse:
    return MeResponse(
        email=user.email,
        consent_required=user.consent_version != CONSENT_VERSION,
        consent_version=CONSENT_VERSION,
        consent_text=CONSENT_TEXT,
        store_questions=user.store_questions,
    )
