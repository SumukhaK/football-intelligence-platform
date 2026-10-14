"""Tests for the cloud safety checks and hardening settings (ADR 025)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from backend.app.config import Settings


def test_local_defaults_still_load() -> None:
    settings = Settings()
    assert settings.revision is None
    assert settings.auth_required is False


def test_cloud_refuses_to_start_with_sign_in_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("K_REVISION", "football-api-00001-abc")
    with pytest.raises(ValidationError, match="AUTH_REQUIRED"):
        Settings(auth_required=False, telemetry_salt="a-real-secret")


def test_cloud_refuses_to_start_with_the_dev_salt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("K_REVISION", "football-api-00001-abc")
    with pytest.raises(ValidationError, match="TELEMETRY_SALT"):
        Settings(auth_required=True)


def test_cloud_starts_with_sign_in_and_a_secret_salt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("K_REVISION", "football-api-00001-abc")
    settings = Settings(
        auth_required=True,
        telemetry_salt="a-real-secret",
        assistant_safety=True,
        history_key=SecretStr("a-real-history-key"),
    )
    assert settings.revision == "football-api-00001-abc"


def test_cloud_refuses_to_start_with_unguarded_chat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("K_REVISION", "football-api-00001-abc")
    with pytest.raises(ValidationError, match="ASSISTANT_SAFETY"):
        Settings(auth_required=True, telemetry_salt="a-real-secret")


def test_cloud_starts_with_the_assistant_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("K_REVISION", "football-api-00001-abc")
    monkeypatch.setenv("ASSISTANT_PROVIDER", "off")
    settings = Settings(auth_required=True, telemetry_salt="a-real-secret")
    assert settings.assistant_provider is None


def test_chat_messages_have_a_length_limit(client: TestClient) -> None:
    response = client.post("/v2/assistant/chat", json={"message": "x" * 1001})
    assert response.status_code == 422


def test_a_chat_message_at_the_limit_is_accepted(client: TestClient) -> None:
    response = client.post("/v2/assistant/chat", json={"message": "x" * 1000})
    assert response.status_code == 200


def test_responses_tell_browsers_not_to_sniff(client: TestClient) -> None:
    assert client.get("/v2/health").headers["X-Content-Type-Options"] == "nosniff"


def test_cloud_refuses_to_start_with_the_dev_history_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("K_REVISION", "football-api-00001-abc")
    with pytest.raises(ValidationError, match="HISTORY_KEY"):
        Settings(
            auth_required=True, telemetry_salt="a-real-secret", assistant_safety=True
        )
