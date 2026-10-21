"""Application configuration loaded from environment / .env file."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Tuned on 2022/23 in docs/reports/draw-handling.md (ADR 011).
DEFAULT_DRAW_POSSIBLE_THRESHOLD = 0.28
DEV_TELEMETRY_SALT = "local-dev-salt"
DEV_HISTORY_KEY = "local-dev-history-key"


class Settings(BaseSettings):
    """Runtime configuration for the Football Intelligence backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Lets LIVE_REFRESH_HOUR=off and RATE_LIMIT_PER_MINUTE=off turn those off.
        env_parse_none_str="off",
        # ai/.env is shared by all three settings classes, so each ignores the
        # keys that belong to the others.
        extra="ignore",
    )

    model_path: Path = Path("../ai/models/latest/model.joblib")
    registry_path: Path = Path("../ai/models/registry.json")
    # The original model behind API v1 and unversioned paths (ADR 014).
    v1_model_path: Path = Path("../ai/models/runs/20260630_132617/model.joblib")
    v1_model_version: str = "20260630_132617"
    # Public name of the match prediction model shown to users (ADR 033).
    prediction_model_name: str = "Drishti"
    # Requests per client per minute; `off` turns rate limiting off (ADR 014).
    rate_limit_per_minute: int | None = Field(default=120, ge=1)
    # Proxies in front of the server that append to X-Forwarded-For: 0 locally,
    # 1 on Cloud Run, whose front end appends the address it saw.
    trusted_proxy_hops: int = Field(default=0, ge=0)
    # Largest request body accepted; every body is a small JSON object.
    max_body_bytes: int = Field(default=24_576, ge=1)
    matches_dir: Path = Path("../datasets/processed/football_data")
    datasets_dir: Path = Path("../datasets")
    # Upcoming fixtures, rebuilt by the daily refresh (ADR 015).
    fixtures_dir: Path = Path("../datasets/processed/openfootball")
    # Team and league name → crest URL (ADR 020).
    team_crests_path: Path = Path("../datasets/schemas/team_crests.csv")
    league_emblems_path: Path = Path("../datasets/schemas/league_emblems.csv")
    # Local hour of the daily data refresh (ADR 013); set to `off` to turn it off.
    live_refresh_hour: int | None = Field(default=6, ge=0, le=23)
    # Leagues the API serves (ADR 012); requests naming no league get the default.
    served_competitions: list[str] = [
        "Premier League",
        "Bundesliga",
        "La Liga",
        "Serie A",
        "Ligue 1",
    ]
    default_competition: str = "Premier League"
    draw_possible_threshold: float = DEFAULT_DRAW_POSSIBLE_THRESHOLD
    api_version: str = "2.6.3"
    log_level: str = "INFO"
    # `json` writes the telemetry contract's log lines (ADR 024); `text` is for
    # reading logs by eye locally.
    log_format: Literal["text", "json"] = "text"
    gcp_project_id: str | None = None
    # Key for the user_ref and client_ref hashes in logs; a secret in the cloud.
    telemetry_salt: str = DEV_TELEMETRY_SALT
    # Cloud Run sets K_REVISION; it is null locally.
    revision: str | None = Field(default=None, validation_alias="K_REVISION")
    # Where request traces go (ADR 024): nowhere, a local OTLP collector, or
    # Cloud Trace (needs gcp_project_id).
    trace_exporter: Literal["none", "otlp", "gcp"] = "none"
    otlp_endpoint: str = "http://localhost:4318/v1/traces"
    trace_sample_ratio: float = Field(default=1.0, ge=0.0, le=1.0)

    # Who answers chat (ADR 025): local Ollama, Cloudflare Workers AI, or nobody.
    # `off` reads as None (env_parse_none_str above) and loads no assistant.
    assistant_provider: Literal["ollama", "workers_ai"] | None = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen2.5:7b-instruct"
    ollama_embed_model: str = "nomic-embed-text"
    workers_ai_account_id: str | None = None
    workers_ai_api_token: SecretStr | None = None
    workers_ai_chat_model: str = "@cf/google/gemma-4-26b-a4b-it"
    workers_ai_embed_model: str = "@cf/qwen/qwen3-embedding-0.6b"
    # Deadline for each Workers AI attempt; one retry at most.
    workers_ai_timeout_s: float = Field(default=20.0, gt=0)
    # Reasoning models think before answering unless told not to; off keeps
    # answers inside the app's 30-second request budget.
    workers_ai_thinking: bool = False
    # Llama Guard checks each question before anything else, and three
    # harmful questions ban the user (ADR 027); required on Cloud Run.
    assistant_safety: bool = False
    ollama_guard_model: str = "llama-guard3:1b"
    workers_ai_guard_model: str = "@cf/meta/llama-guard-3-8b"
    # Signs the assistant's answers so the app can send them back as chat
    # history (ADR 030); a secret in the cloud.
    history_key: SecretStr = SecretStr(DEV_HISTORY_KEY)
    assistant_vector_store_path: Path = Path("assistant/vector_store")
    assistant_knowledge_root: Path = Path(".")
    assistant_top_k: int = 5

    # Invite-only sign-in for every /v2 data route (ADR 022); on in the cloud.
    auth_required: bool = False
    # Where accounts live (ADR 026): a local JSON file, or Firestore in the
    # cloud, where the disk is wiped on every restart.
    account_store: Literal["json", "firestore"] = "json"
    accounts_path: Path = Path("accounts/accounts.json")
    firestore_database: str = "(default)"
    # Prefixed to each collection name, so staging and prod can share a database.
    firestore_collection_prefix: str = ""

    @model_validator(mode="after")
    def _refuse_unsafe_cloud_defaults(self) -> Settings:
        """On Cloud Run, refuse to start open, with the dev salt or unguarded chat."""
        if self.revision is None:
            return self
        if not self.auth_required:
            raise ValueError("AUTH_REQUIRED must be true on Cloud Run (ADR 025).")
        if self.telemetry_salt == DEV_TELEMETRY_SALT:
            raise ValueError("TELEMETRY_SALT must be a secret on Cloud Run (ADR 025).")
        if self.assistant_provider is not None and not self.assistant_safety:
            raise ValueError(
                "ASSISTANT_SAFETY must be true on Cloud Run when the assistant "
                "is on (ADR 027)."
            )
        if (
            self.assistant_provider is not None
            and self.history_key.get_secret_value() == DEV_HISTORY_KEY
        ):
            raise ValueError("HISTORY_KEY must be a secret on Cloud Run (ADR 030).")
        return self


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the singleton Settings instance (cached after first call)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
