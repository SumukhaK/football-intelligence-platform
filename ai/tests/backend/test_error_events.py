"""Tests for app.error, component.degraded, app.crash and http.request error codes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.app.exceptions import AssistantNotAvailableError

Events = Callable[[str], list[tuple[str, dict[str, Any]]]]


def _error_code(events: Events) -> Any:
    ((_, attributes),) = events("http.request")
    return attributes["error_code"]


def test_typed_error_logs_app_error(
    client: TestClient, valid_features: dict[str, Any], events: Events
) -> None:
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "competition": "Nowhere League",
        "features": valid_features,
    }
    response = client.post("/v2/predict", json=payload)
    assert response.status_code == 422
    assert events("app.error") == [
        (
            "WARNING",
            {
                "route": "/v2/predict",
                "status": 422,
                "error_code": "Unknown competition",
                "exception_type": "backend.app.exceptions.UnknownCompetitionError",
            },
        )
    ]
    assert _error_code(events) == "Unknown competition"
    assert events("component.degraded") == []


def test_missing_component_logs_degraded(client: TestClient, events: Events) -> None:
    client.app.state.fixtures_service = None  # type: ignore[attr-defined]
    response = client.get("/v2/fixtures")
    assert response.status_code == 503
    assert events("component.degraded") == [
        ("WARNING", {"component": "fixtures", "route": "/v2/fixtures"})
    ]
    ((severity, attributes),) = events("app.error")
    assert (severity, attributes["error_code"]) == ("ERROR", "Fixtures not available")
    assert _error_code(events) == "Fixtures not available"


def test_assistant_not_loaded_is_degraded(client: TestClient, events: Events) -> None:
    client.app.state.chat_service = None  # type: ignore[attr-defined]
    client.post("/v2/assistant/chat", json={"message": "Who wins?"})
    assert events("component.degraded") == [
        ("WARNING", {"component": "assistant", "route": "/v2/assistant/chat"})
    ]


def test_assistant_failing_while_loaded_is_not_degraded(
    client: TestClient, mock_chat_service: MagicMock, events: Events
) -> None:
    mock_chat_service.chat.side_effect = AssistantNotAvailableError("Ollama down")
    response = client.post("/v2/assistant/chat", json={"message": "Who wins?"})
    assert response.status_code == 503
    assert events("component.degraded") == []
    assert [a["status"] for _, a in events("app.error")] == [503]


def test_unhandled_error_logs_app_crash(
    client: TestClient,
    mock_prediction_service: MagicMock,
    valid_features: dict[str, Any],
    events: Events,
) -> None:
    mock_prediction_service.predict.side_effect = RuntimeError("boom")
    payload = {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "features": valid_features,
    }
    response = client.post("/v2/predict", json=payload)
    assert response.status_code == 500
    assert events("app.crash") == [
        ("ERROR", {"route": "/v2/predict", "exception_type": "builtins.RuntimeError"})
    ]
    assert _error_code(events) == "Internal server error"


def test_success_has_no_error_code(client: TestClient, events: Events) -> None:
    client.get("/v2/health")
    assert _error_code(events) is None
