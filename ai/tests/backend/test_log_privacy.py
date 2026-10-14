"""No chat question or email ever reaches a log line (telemetry contract section 1)."""

from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient

from shared.telemetry.json_formatter import JsonFormatter

QUESTION_MARKER = "quokka-question-5521"
EMAIL_MARKER = "quokka-5521@example.org"
FORMATTER = JsonFormatter(
    service="football-api", api_version="2.0.0", revision=None, gcp_project_id=None
)


def _everything_logged(caplog: pytest.LogCaptureFixture) -> str:
    """Every captured record as its JSON line, attributes included."""
    return "\n".join(FORMATTER.format(record) for record in caplog.records)


def test_chat_questions_are_never_logged(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    client.post("/v2/assistant/chat", json={"message": f"Who wins? {QUESTION_MARKER}"})
    logged = _everything_logged(caplog)
    assert "assistant/chat" in logged
    assert QUESTION_MARKER not in logged


def test_sign_in_emails_are_never_logged(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    response = client.post(
        "/v2/auth/login", json={"email": EMAIL_MARKER, "password": "not the password"}
    )
    assert response.status_code == 401
    logged = _everything_logged(caplog)
    assert "auth.event" in logged
    assert "quokka" not in logged
