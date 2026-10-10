"""Tests for choosing the assistant's model provider (ADR 025)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from assistant.ingestion.document import Document
from assistant.retrieval.vector_store import IndexInfo, VectorStore
from backend.app.config import Settings
from backend.app.loaders import load_assistant


def _index(tmp_path: Path, info: IndexInfo | None = None) -> Path:
    import numpy as np

    store = VectorStore()
    store.add([Document(id="d1", text="t", source="s.md")], np.ones((1, 2), np.float32))
    store.info = info
    store.save(tmp_path / "index")
    return tmp_path / "index"


HOSTED = IndexInfo("@cf/qwen/qwen3-embedding-0.6b", 0.6)


def _generator_of(chat_service: object) -> object:
    return chat_service._service._generator  # type: ignore[attr-defined]


def test_ollama_is_the_default_provider(tmp_path: Path) -> None:
    from assistant.generation.generator import OllamaGenerator

    settings = Settings(assistant_vector_store_path=_index(tmp_path))
    service = load_assistant(settings, SimpleNamespace())
    assert isinstance(_generator_of(service), OllamaGenerator)


def test_workers_ai_provider_uses_the_hosted_model(tmp_path: Path) -> None:
    from assistant.workers_ai import WorkersAIEmbedder, WorkersAIGenerator

    settings = Settings(
        assistant_vector_store_path=_index(tmp_path, HOSTED),
        assistant_provider="workers_ai",
        workers_ai_account_id="acc",
        workers_ai_api_token=SecretStr("token"),
    )
    service = load_assistant(settings, SimpleNamespace())
    assistant: Any = service._service
    assert isinstance(assistant._generator, WorkersAIGenerator)
    assert isinstance(assistant._embedder, WorkersAIEmbedder)
    assert assistant._model_name == settings.workers_ai_chat_model


def test_workers_ai_without_credentials_fails_to_load(tmp_path: Path) -> None:
    settings = Settings(
        assistant_vector_store_path=_index(tmp_path), assistant_provider="workers_ai"
    )
    with pytest.raises(ValueError, match="WORKERS_AI_API_TOKEN"):
        load_assistant(settings, SimpleNamespace())


def test_the_token_is_never_shown(tmp_path: Path) -> None:
    settings = Settings(workers_ai_api_token=SecretStr("secret-token"))
    assert "secret-token" not in repr(settings)


def test_provider_off_loads_no_assistant(tmp_path: Path) -> None:
    from backend.app.main import create_app

    settings = Settings(
        assistant_provider=None,
        model_path=tmp_path / "none.joblib",
        registry_path=tmp_path / "none.json",
        live_refresh_hour=None,
    )
    with patch("backend.app.config._settings", settings):
        with patch("backend.app.main.get_settings", return_value=settings):
            application = create_app()
            with patch("backend.app.main.load_assistant") as loader:
                with TestClient(application):
                    assert application.state.chat_service is None
            loader.assert_not_called()


def test_a_trailing_newline_on_the_token_is_dropped(tmp_path: Path) -> None:
    settings = Settings(
        assistant_vector_store_path=_index(tmp_path, HOSTED),
        assistant_provider="workers_ai",
        workers_ai_account_id="acc",
        workers_ai_api_token=SecretStr("token\n"),
    )
    service = load_assistant(settings, SimpleNamespace())
    client = service._service._generator._client  # type: ignore[attr-defined]
    assert client._headers == {"Authorization": "Bearer token"}


def test_the_index_cut_off_reaches_the_assistant(tmp_path: Path) -> None:
    settings = Settings(
        assistant_vector_store_path=_index(tmp_path, HOSTED),
        assistant_provider="workers_ai",
        workers_ai_account_id="acc",
        workers_ai_api_token=SecretStr("token"),
    )
    service: Any = load_assistant(settings, SimpleNamespace())
    assert service._service._min_relevance == 0.6


def test_a_local_index_is_refused_for_hosted_queries(tmp_path: Path) -> None:
    settings = Settings(
        assistant_vector_store_path=_index(tmp_path),
        assistant_provider="workers_ai",
        workers_ai_account_id="acc",
        workers_ai_api_token=SecretStr("token"),
    )
    with pytest.raises(ValueError, match="built with nomic-embed-text"):
        load_assistant(settings, SimpleNamespace())


def test_a_hosted_index_is_refused_for_local_queries(tmp_path: Path) -> None:
    settings = Settings(assistant_vector_store_path=_index(tmp_path, HOSTED))
    with pytest.raises(ValueError, match="queries would use nomic-embed-text"):
        load_assistant(settings, SimpleNamespace())


def test_off_in_the_environment_turns_the_assistant_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ASSISTANT_PROVIDER", "off")
    assert Settings().assistant_provider is None
