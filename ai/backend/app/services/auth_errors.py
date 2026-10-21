"""Account errors the API reports as ``{"error", "detail"}`` (ADR 022)."""

from __future__ import annotations


class AuthError(Exception):
    """An account problem the API reports as ``{"error", "detail"}``."""

    status_code = 400
    error = "Bad request"
    # The auth.event outcome this error is logged as (telemetry contract).
    outcome = "failed"


class NotSignedInError(AuthError):
    """No valid session token was sent."""

    status_code, error = 401, "Not signed in"
    outcome = "not_signed_in"


class InvalidCredentialsError(AuthError):
    """Wrong email or password; the message never says which."""

    status_code, error = 401, "Invalid credentials"


class InvalidInviteError(AuthError):
    """The invite code is wrong, used or expired."""

    status_code, error = 400, "Invalid invite"
    outcome = "invalid_invite"


class InviteAlreadyUsedError(AuthError):
    """The right code, already used: the account exists, so sign in instead."""

    status_code, error = 409, "Invite already used"
    outcome = "invite_used"


class InviteExpiredError(AuthError):
    """The right code, past its 7 days."""

    status_code, error = 410, "Invite expired"
    outcome = "invite_expired"


class WeakPasswordError(AuthError):
    """The chosen password is too short."""

    status_code, error = 422, "Password too short"
    outcome = "weak_password"


class ConsentRequiredError(AuthError):
    """The user has not accepted the current notice."""

    status_code, error = 403, "Consent required"
    outcome = "consent_required"


class AccountBlockedError(AuthError):
    """The user is banned."""

    status_code, error = 403, "Account blocked"
    outcome = "blocked"


class TooManyAttemptsError(AuthError):
    """Too many failed logins; try again later."""

    status_code, error = 429, "Too many attempts"
    outcome = "locked_out"
