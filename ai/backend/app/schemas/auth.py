"""Request and response schemas for sign-in and consent (ADR 022)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RedeemInviteRequest(BaseModel):
    """Input for POST /v2/auth/redeem-invite."""

    email: str = Field(..., min_length=3, max_length=254, examples=["sam@example.com"])
    code: str = Field(..., min_length=1, max_length=200)
    password: str = Field(..., min_length=1, max_length=200)


class LoginRequest(BaseModel):
    """Input for POST /v2/auth/login."""

    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=1, max_length=200)


class SessionResponse(BaseModel):
    """A session token; send it as ``Authorization: Bearer <token>``."""

    token: str
    expires_at: datetime


class MeResponse(BaseModel):
    """The signed-in user and whether they still need to accept the notice."""

    email: str
    consent_required: bool
    consent_version: int = Field(..., description="Current notice version.")
    consent_text: str
    store_questions: bool


class ConsentRequest(BaseModel):
    """Input for POST /v2/me/consent."""

    version: int = Field(..., ge=1, description="The notice version shown.")
    store_questions: bool = Field(
        default=False, description="Allow storing the text of questions."
    )
