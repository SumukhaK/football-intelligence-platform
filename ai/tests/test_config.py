"""Tests for settings and path configuration."""

from pathlib import Path

import pytest

from config.paths import DataPaths
from config.settings import Settings


class TestDataPaths:
    def test_all_paths_are_children_of_base_dir(self, tmp_path: Path) -> None:
        paths = DataPaths(base_dir=tmp_path / "datasets")
        for attr in ("raw", "processed", "cache", "temp", "models"):
            p = getattr(paths, attr)
            assert str(tmp_path) in str(p)

    def test_ensure_all_creates_directories(self, tmp_path: Path) -> None:
        paths = DataPaths(base_dir=tmp_path / "datasets")
        paths.ensure_all()
        assert paths.raw.exists()
        assert paths.processed.exists()
        assert paths.cache.exists()
        assert paths.temp.exists()
        assert paths.models.exists()

    def test_ensure_all_is_idempotent(self, tmp_path: Path) -> None:
        paths = DataPaths(base_dir=tmp_path / "datasets")
        paths.ensure_all()
        paths.ensure_all()  # Must not raise
        assert paths.raw.exists()

    def test_provider_raw_dir_scoped_to_provider(self, tmp_path: Path) -> None:
        paths = DataPaths(base_dir=tmp_path / "datasets")
        d = paths.provider_raw_dir("football_data")
        assert d == paths.raw / "football_data"

    def test_provider_cache_dir_scoped_to_provider(self, tmp_path: Path) -> None:
        paths = DataPaths(base_dir=tmp_path / "datasets")
        d = paths.provider_cache_dir("fbref")
        assert d == paths.cache / "fbref"


class TestSettings:
    def test_default_datasets_base_dir(self) -> None:
        settings = Settings()
        assert settings.datasets_base_dir == Path("datasets")

    def test_default_log_level(self) -> None:
        settings = Settings()
        assert settings.log_level == "INFO"

    def test_default_http_timeout(self) -> None:
        settings = Settings()
        assert settings.http_timeout_seconds > 0

    def test_paths_property_returns_data_paths(self) -> None:
        settings = Settings()
        paths = settings.paths
        assert isinstance(paths, DataPaths)
        assert paths.base_dir == settings.datasets_base_dir

    def test_env_prefix_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FOOTBALL_AI_LOG_LEVEL", "DEBUG")
        settings = Settings()
        assert settings.log_level == "DEBUG"


def test_every_settings_class_reads_a_shared_env_file(tmp_path: Path) -> None:
    """Keys meant for one settings class do not stop the others from loading."""
    from assistant.configuration import AssistantSettings
    from backend.app.config import Settings as BackendSettings

    env = tmp_path / ".env"
    env.write_text(
        "MODEL_PATH=m.joblib\n"
        "OLLAMA_CHAT_MODEL=qwen2.5:7b-instruct\n"
        "FOOTBALL_AI_LOG_LEVEL=DEBUG\n"
        "SOME_OTHER_TOOL_KEY=value\n",
        encoding="utf-8",
    )
    assert Settings(_env_file=env).log_level == "DEBUG"  # type: ignore[call-arg]
    assert BackendSettings(_env_file=env).model_path == Path("m.joblib")  # type: ignore[call-arg]
    assert (
        AssistantSettings(_env_file=env).ollama_chat_model  # type: ignore[call-arg]
        == "qwen2.5:7b-instruct"
    )
