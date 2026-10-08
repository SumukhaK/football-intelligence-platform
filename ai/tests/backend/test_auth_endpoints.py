"""Integration tests for sign-in, consent and the /v2 guard (ADR 022)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response

from backend.app.config import Settings
from backend.app.consent import CONSENT_VERSION
from backend.app.main import create_app

EMAIL = "sam@example.com"
PASSWORD = "correct horse battery"


@pytest.fixture()
def signed_app(tmp_path: Path, mock_prediction_service: MagicMock) -> FastAPI:
    """An app with sign-in required and a temporary account file."""
    settings = Settings(auth_required=True, accounts_path=tmp_path / "a.json")
    with patch("backend.app.main.get_settings", return_value=settings):
        application = create_app()
    application.state.prediction_service = mock_prediction_service
    return application


@pytest.fixture()
def app_client(signed_app: FastAPI) -> Iterator[TestClient]:
    """A client for ``signed_app`` that turns errors into responses."""
    yield TestClient(signed_app, raise_server_exceptions=False)


def _sign_up(app: FastAPI, client: TestClient) -> dict[str, str]:
    code = app.state.account_service.create_invite(EMAIL)
    response = client.post(
        "/v2/auth/redeem-invite",
        json={"email": EMAIL, "code": code, "password": PASSWORD},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def client_passes_guard(response: Response) -> bool:
    """True when sign-in let the request through (the data may still be absent)."""
    return response.status_code not in (401, 403)


def _consent(client: TestClient, headers: dict[str, str]) -> None:
    response = client.post(
        "/v2/me/consent", json={"version": CONSENT_VERSION}, headers=headers
    )
    assert response.status_code == 200


def test_data_routes_need_sign_in(app_client: TestClient) -> None:
    """Without a token, data routes answer 401 with the error shape."""
    response = app_client.get("/v2/competitions")
    assert response.status_code == 401
    assert response.json()["error"] == "Not signed in"


def test_health_stays_open(app_client: TestClient) -> None:
    """Health checks need no sign-in."""
    assert app_client.get("/v2/health").status_code == 200


def test_v1_is_not_mounted_when_sign_in_is_on(app_client: TestClient) -> None:
    """v1 and unversioned paths would bypass sign-in, so they are gone."""
    assert app_client.get("/v1/health").status_code == 404
    assert app_client.post("/predict", json={}).status_code == 404


def test_consent_is_needed_before_data(
    signed_app: FastAPI, app_client: TestClient
) -> None:
    """A signed-in user must accept the notice before using the app."""
    headers = _sign_up(signed_app, app_client)
    me = app_client.get("/v2/me", headers=headers).json()
    assert me["consent_required"] is True
    assert me["consent_text"]
    response = app_client.get("/v2/competitions", headers=headers)
    assert (response.status_code, response.json()["error"]) == (
        403,
        "Consent required",
    )
    _consent(app_client, headers)
    assert app_client.get("/v2/me", headers=headers).json()["consent_required"] is False
    assert client_passes_guard(app_client.get("/v2/competitions", headers=headers))


def test_outdated_consent_version_is_refused(
    signed_app: FastAPI, app_client: TestClient
) -> None:
    """Accepting another notice version does not count."""
    headers = _sign_up(signed_app, app_client)
    response = app_client.post(
        "/v2/me/consent", json={"version": CONSENT_VERSION + 1}, headers=headers
    )
    assert response.status_code == 403


def test_login_and_logout(signed_app: FastAPI, app_client: TestClient) -> None:
    """Sign in returns a working token; sign out ends it."""
    _sign_up(signed_app, app_client)
    response = app_client.post(
        "/v2/auth/login", json={"email": EMAIL, "password": PASSWORD}
    )
    headers = {"Authorization": f"Bearer {response.json()['token']}"}
    assert app_client.get("/v2/me", headers=headers).status_code == 200
    assert app_client.post("/v2/auth/logout", headers=headers).status_code == 204
    assert app_client.get("/v2/me", headers=headers).status_code == 401


def test_wrong_password_is_401(signed_app: FastAPI, app_client: TestClient) -> None:
    """A wrong password gets the same answer as an unknown email."""
    _sign_up(signed_app, app_client)
    for email in (EMAIL, "nobody@example.com"):
        response = app_client.post(
            "/v2/auth/login", json={"email": email, "password": "wrong password"}
        )
        assert (response.status_code, response.json()["error"]) == (
            401,
            "Invalid credentials",
        )


def test_banned_user_is_blocked(signed_app: FastAPI, app_client: TestClient) -> None:
    """After a ban the old token stops working and sign-in is refused."""
    headers = _sign_up(signed_app, app_client)
    signed_app.state.account_service.set_banned(EMAIL, banned=True)
    assert app_client.get("/v2/me", headers=headers).status_code == 401
    response = app_client.post(
        "/v2/auth/login", json={"email": EMAIL, "password": PASSWORD}
    )
    assert (response.status_code, response.json()["error"]) == (403, "Account blocked")


def test_sign_in_is_off_by_default(client: TestClient) -> None:
    """Locally (AUTH_REQUIRED unset) everything works without a token."""
    assert client_passes_guard(client.get("/v2/competitions"))
    assert client.get("/v1/health").status_code == 200
