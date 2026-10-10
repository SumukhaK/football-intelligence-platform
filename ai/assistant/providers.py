"""Builds the embedder and generator for the configured provider (ADR 025)."""

from __future__ import annotations

from dataclasses import dataclass

from assistant.configuration import AssistantSettings
from assistant.embeddings.embedder import Embedder, OllamaEmbedder
from assistant.generation.generator import Generator, OllamaGenerator


@dataclass(frozen=True)
class Provider:
    """One provider's embedder and generator, and the models they use."""

    embedder: Embedder
    generator: Generator
    chat_model: str
    embed_model: str


def make_provider(cfg: AssistantSettings) -> Provider:
    """The provider ``cfg.assistant_provider`` names: Ollama or Workers AI."""
    if cfg.assistant_provider == "workers_ai":
        return _workers_ai(cfg)
    return Provider(
        embedder=OllamaEmbedder(
            model=cfg.ollama_embed_model, base_url=cfg.ollama_base_url
        ),
        generator=OllamaGenerator(
            model=cfg.ollama_chat_model,
            base_url=cfg.ollama_base_url,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
        ),
        chat_model=cfg.ollama_chat_model,
        embed_model=cfg.ollama_embed_model,
    )


def _workers_ai(cfg: AssistantSettings) -> Provider:
    from assistant.workers_ai import (
        WorkersAIClient,
        WorkersAIEmbedder,
        WorkersAIGenerator,
    )

    token = cfg.workers_ai_api_token
    if not cfg.workers_ai_account_id or token is None:
        raise ValueError(
            "ASSISTANT_PROVIDER=workers_ai needs WORKERS_AI_ACCOUNT_ID and "
            "WORKERS_AI_API_TOKEN."
        )
    client = WorkersAIClient(
        cfg.workers_ai_account_id,
        # A secret mounted from a file can end in a newline.
        token.get_secret_value().strip(),
        cfg.workers_ai_timeout_s,
    )
    generator = WorkersAIGenerator(
        client,
        cfg.workers_ai_chat_model,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        thinking=cfg.workers_ai_thinking,
    )
    return Provider(
        embedder=WorkersAIEmbedder(client, cfg.workers_ai_embed_model),
        generator=generator,
        chat_model=cfg.workers_ai_chat_model,
        embed_model=cfg.workers_ai_embed_model,
    )
