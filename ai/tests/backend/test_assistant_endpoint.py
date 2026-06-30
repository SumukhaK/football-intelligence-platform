"""Tests for POST /assistant/chat."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def test_chat_returns_200(client: TestClient) -> None:
    """POST /assistant/chat returns 200 for a valid message."""
    response = client.post(
        "/assistant/chat", json={"message": "What is the model accuracy?"}
    )
    assert response.status_code == 200


def test_chat_response_fields(client: TestClient) -> None:
    """POST /assistant/chat response contains all required fields."""
    response = client.post("/assistant/chat", json={"message": "Explain SHAP values."})
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "confidence" in data
    assert "model" in data
    assert "retrieved_count" in data


def test_chat_answer_is_string(client: TestClient) -> None:
    """The answer field is a non-empty string."""
    data = client.post(
        "/assistant/chat", json={"message": "Tell me about the model."}
    ).json()
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0


def test_chat_sources_is_list(client: TestClient) -> None:
    """The sources field is a list."""
    data = client.post(
        "/assistant/chat", json={"message": "Who trained the model?"}
    ).json()
    assert isinstance(data["sources"], list)


def test_chat_source_citation_fields(client: TestClient) -> None:
    """Each source has source, excerpt, and relevance_score."""
    data = client.post(
        "/assistant/chat", json={"message": "Who trained the model?"}
    ).json()
    for src in data["sources"]:
        assert "source" in src
        assert "excerpt" in src
        assert "relevance_score" in src


def test_chat_confidence_in_unit_range(client: TestClient) -> None:
    """confidence is between 0 and 1."""
    data = client.post(
        "/assistant/chat", json={"message": "What features are used?"}
    ).json()
    assert 0.0 <= data["confidence"] <= 1.0


def test_chat_422_empty_message(client: TestClient) -> None:
    """POST /assistant/chat returns 422 when message is empty."""
    response = client.post("/assistant/chat", json={"message": ""})
    assert response.status_code == 422


def test_chat_422_missing_message(client: TestClient) -> None:
    """POST /assistant/chat returns 422 when message field is absent."""
    response = client.post("/assistant/chat", json={})
    assert response.status_code == 422


def test_chat_503_when_assistant_unavailable(tmp_path: Path) -> None:
    """POST /assistant/chat returns 503 when assistant is not loaded."""
    from backend.app.config import Settings
    from backend.app.main import create_app

    missing = Settings(
        model_path=tmp_path / "no_model.joblib",
        registry_path=tmp_path / "no_registry.json",
        assistant_vector_store_path=tmp_path / "no_store",
    )
    with patch("backend.app.config._settings", missing):
        with patch("backend.app.main.get_settings", return_value=missing):
            bare_app = create_app()
            with TestClient(bare_app, raise_server_exceptions=False) as c:
                response = c.post(
                    "/assistant/chat",
                    json={"message": "Who wins?"},
                )
    assert response.status_code == 503


def test_chat_service_error_returns_503(
    client: TestClient, mock_chat_service: MagicMock
) -> None:
    """When chat_service raises, the endpoint returns 503."""
    from backend.app.exceptions import AssistantNotAvailableError

    mock_chat_service.chat.side_effect = AssistantNotAvailableError("Ollama down")
    response = client.post("/assistant/chat", json={"message": "Tell me something."})
    assert response.status_code == 503
