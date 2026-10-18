"""Offline storage and authenticated API regression tests for ADR 035."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.consent import CONSENT_VERSION
from backend.app.main import create_app
from backend.app.schemas.teams import TeamsResponse
from backend.app.services.account_service import AccountService
from backend.app.services.account_store import (
    FirestoreAccountStore,
    JsonAccountStore,
    Session,
    User,
)
from tests.backend.fake_firestore import FakeFirestore

FAVOURITE = {"league": "Premier League", "team": "Arsenal"}
EMAIL = "a@example.com"
NOW = datetime(2026, 10, 19, tzinfo=UTC)


@pytest.fixture(params=["json", "firestore"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> Any:
    """Exercise real JSON writes and the existing offline Firestore fake."""
    if request.param == "json":
        return JsonAccountStore(tmp_path / "accounts.json")
    return FirestoreAccountStore(FakeFirestore(), "test_")


def add_account(store: Any, email: str = EMAIL, token: str = "token-a") -> None:
    """Create a consenting account and a deterministically valid session."""
    store.save_user(
        User(email, "hash", NOW.isoformat(), consent_version=CONSENT_VERSION)
    )
    store.save_session(
        Session(
            hashlib.sha256(token.encode()).hexdigest(),
            email,
            NOW.isoformat(),
            "2026-11-19T00:00:00+00:00",
        )
    )


@pytest.fixture
def app(store: Any, tmp_path: Path) -> FastAPI:
    """Use temporary stores, a local catalog and no startup cloud clients."""
    with patch(
        "backend.app.main.get_settings",
        return_value=Settings(
            auth_required=True,
            account_store="json",
            accounts_path=tmp_path / "unused.json",
        ),
    ):
        application = create_app()
    application.state.account_service = AccountService(store, clock=lambda: NOW)
    application.state.account_store = store
    catalog = MagicMock()
    catalog.teams.side_effect = lambda league: TeamsResponse(
        competition=league,
        season="2026/27",
        teams=(
            ["Arsenal", "Chelsea"] if league == "Premier League" else ["Inter", "Milan"]
        ),
    )
    application.state.fixture_feature_service = catalog
    add_account(store)
    return application


def headers(token: str = "token-a") -> dict[str, str]:
    """Send the session token, never an account ID."""
    return {"Authorization": f"Bearer {token}"}


def test_legacy_record_is_confirmed_empty(app: FastAPI) -> None:
    response = TestClient(app).get("/v2/me/preferences", headers=headers())
    assert response.status_code == 200
    assert response.json() == {"email": EMAIL, "favourite": None}


def test_save_survives_new_client_and_stale_auth_write(
    app: FastAPI, store: Any
) -> None:
    stale = store.get_user(EMAIL)
    client = TestClient(app)
    saved = client.put(
        "/v2/me/preferences", headers=headers(), json={"favourite": FAVOURITE}
    )
    assert saved.status_code == 200
    assert saved.json() == {"email": EMAIL, "favourite": FAVOURITE}
    stale.store_questions = True
    store.save_user(stale)
    # A new client has no local cache, as after reinstall or upgrade.
    restored = TestClient(app).get("/v2/me/preferences", headers=headers())
    assert restored.json() == saved.json()
    assert store.get_user(EMAIL).store_questions is True
    assert store.get_user(EMAIL).password_hash == "hash"


def test_account_isolation(app: FastAPI, store: Any) -> None:
    add_account(store, "b@example.com", "token-b")
    client = TestClient(app)
    assert (
        client.put(
            "/v2/me/preferences", headers=headers(), json={"favourite": FAVOURITE}
        ).status_code
        == 200
    )
    assert client.get("/v2/me/preferences", headers=headers("token-b")).json() == {
        "email": "b@example.com",
        "favourite": None,
    }
    spoofed = client.put(
        "/v2/me/preferences",
        headers=headers("token-b"),
        json={"email": EMAIL, "favourite": FAVOURITE},
    )
    assert spoofed.status_code == 422
    assert (
        client.get("/v2/me/preferences", headers=headers()).json()["favourite"]
        == FAVOURITE
    )


@pytest.mark.parametrize("method", ["get", "put"])
@pytest.mark.parametrize("token", [None, "unknown"])
def test_unauthorized(app: FastAPI, method: str, token: str | None) -> None:
    response = TestClient(app).request(
        method,
        "/v2/me/preferences",
        headers=headers(token) if token else {},
        json={"favourite": FAVOURITE},
    )
    assert response.status_code == 401
    assert response.json()["error"] == "Not signed in"


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"favourite": None},
        {"favourite": {"league": "", "team": "Arsenal"}},
        {"favourite": {"league": "Championship", "team": "Arsenal"}},
        {"favourite": {"league": "Serie A", "team": "Arsenal"}},
        {"favourite": {"league": "Premier League", "team": "arsenal"}},
        {"favourite": {"league": "Premier League", "team": "Arsenal", "extra": 1}},
        {"favourite": {"league": "Premier League", "team": 7}},
    ],
)
def test_invalid_writes_never_become_favourites(
    app: FastAPI, body: dict[str, Any]
) -> None:
    client = TestClient(app)
    result = client.put("/v2/me/preferences", headers=headers(), json=body)
    assert result.status_code == 422
    assert "error" in result.json() and "detail" in result.json()
    assert (
        client.get("/v2/me/preferences", headers=headers()).json()["favourite"] is None
    )


def test_storage_failure_is_not_empty(app: FastAPI, store: Any) -> None:
    with patch.object(
        store, "get_user", side_effect=RuntimeError("private provider detail")
    ):
        response = TestClient(app, raise_server_exceptions=False).get(
            "/v2/me/preferences", headers=headers()
        )
    assert response.status_code == 503
    assert set(response.json()) >= {"error", "detail"}
    assert "private provider detail" not in response.text


def test_write_failure_is_retryable(app: FastAPI, store: Any) -> None:
    with patch.object(
        store, "set_favourite", side_effect=RuntimeError("private detail")
    ):
        response = TestClient(app, raise_server_exceptions=False).put(
            "/v2/me/preferences", headers=headers(), json={"favourite": FAVOURITE}
        )
    assert response.status_code == 503
    assert "private detail" not in response.text


@pytest.mark.parametrize(
    "invalid",
    [{"league": "Serie A"}, "Arsenal", {"league": "Serie A", "team": "Arsenal"}],
)
def test_invalid_stored_preferences_are_not_confirmed_empty(
    app: FastAPI,
    store: Any,
    invalid: Any,
) -> None:
    store.set_favourite(EMAIL, invalid)
    response = TestClient(app, raise_server_exceptions=False).get(
        "/v2/me/preferences", headers=headers()
    )
    assert response.status_code == 503


def test_store_patch_preserves_unrelated_fields(store: Any) -> None:
    add_account(store)
    stale = store.get_user(EMAIL)
    store.set_favourite(EMAIL, FAVOURITE)
    stale.strikes = 2
    store.save_user(stale)
    assert store.get_user(EMAIL).favourite == FAVOURITE
    assert store.get_user(EMAIL).strikes == 2


def test_json_preserves_unknown_account_fields(tmp_path: Path) -> None:
    path = tmp_path / "accounts.json"
    store = JsonAccountStore(path)
    add_account(store)
    data = json.loads(path.read_text())
    data["users"][EMAIL]["future_field"] = {"keep": True}
    path.write_text(json.dumps(data))
    stale = store.get_user(EMAIL)
    store.set_favourite(EMAIL, FAVOURITE)
    store.save_user(stale)
    assert json.loads(path.read_text())["users"][EMAIL]["future_field"] == {
        "keep": True
    }


def test_firestore_preserves_unknown_account_fields() -> None:
    client = FakeFirestore()
    store = FirestoreAccountStore(client)
    add_account(store)
    client.collections["users"][EMAIL]["future_field"] = {"keep": True}
    stale = store.get_user(EMAIL)
    store.set_favourite(EMAIL, FAVOURITE)
    store.save_user(stale)
    assert client.collections["users"][EMAIL]["future_field"] == {"keep": True}


def test_missing_account_cannot_be_recreated_by_a_preference_patch(store: Any) -> None:
    with pytest.raises(KeyError):
        store.set_favourite(EMAIL, FAVOURITE)
    assert store.get_user(EMAIL) is None


def test_catalog_failure_is_not_an_empty_account(app: FastAPI, store: Any) -> None:
    store.set_favourite(EMAIL, FAVOURITE)
    app.state.fixture_feature_service.teams.side_effect = RuntimeError(
        "provider detail"
    )
    client = TestClient(app, raise_server_exceptions=False)
    assert client.get("/v2/me/preferences", headers=headers()).status_code == 503
    response = client.put(
        "/v2/me/preferences", headers=headers(), json={"favourite": FAVOURITE}
    )
    assert response.status_code == 503
    assert "provider detail" not in response.text


def test_blocked_account_cannot_read_or_save(app: FastAPI, store: Any) -> None:
    user = store.get_user(EMAIL)
    user.status = "banned"
    store.save_user(user)
    client = TestClient(app)
    assert client.get("/v2/me/preferences", headers=headers()).status_code == 403
    assert (
        client.put(
            "/v2/me/preferences", headers=headers(), json={"favourite": FAVOURITE}
        ).status_code
        == 403
    )


def test_new_login_restores_server_favourite_without_local_state(app: FastAPI) -> None:
    accounts = app.state.account_service
    email, password = "reinstall@example.com", "a sufficiently long password"
    code = accounts.create_invite(email)
    session = accounts.redeem_invite(email, code, password)
    client = TestClient(app)
    assert (
        client.put(
            "/v2/me/preferences",
            headers=headers(session.token),
            json={"favourite": FAVOURITE},
        ).status_code
        == 200
    )
    assert (
        client.post("/v2/auth/logout", headers=headers(session.token)).status_code
        == 204
    )
    new_install = TestClient(app)
    login = new_install.post(
        "/v2/auth/login", json={"email": email, "password": password}
    )
    assert login.status_code == 200
    restored = new_install.get(
        "/v2/me/preferences", headers=headers(login.json()["token"])
    )
    assert restored.json() == {"email": email, "favourite": FAVOURITE}


def test_preferences_require_credentials_even_in_local_mode(tmp_path: Path) -> None:
    with patch(
        "backend.app.main.get_settings",
        return_value=Settings(
            auth_required=False, accounts_path=tmp_path / "local.json"
        ),
    ):
        application = create_app()
    client = TestClient(application)
    assert client.get("/v2/me/preferences").status_code == 401
    assert (
        client.put("/v2/me/preferences", json={"favourite": FAVOURITE}).status_code
        == 401
    )
