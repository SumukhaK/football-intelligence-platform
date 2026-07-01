"""Tests for assistant.prompting.templates."""

from __future__ import annotations

from assistant.ingestion.document import Document
from assistant.prompting.templates import (
    SYSTEM_PROMPT,
    build_messages,
    build_user_prompt,
)

_DOC = Document(
    id="d1",
    text="XGBoost model accuracy is 56%.",
    source="model_card.md",
    doc_type="model_card",
    metadata={"filename": "model_card.md"},
)


def test_system_prompt_is_nonempty() -> None:
    """SYSTEM_PROMPT contains the key grounding rule."""
    assert "ONLY from the context" in SYSTEM_PROMPT
    assert len(SYSTEM_PROMPT) > 100


def test_build_user_prompt_contains_question() -> None:
    """build_user_prompt includes the user's question verbatim."""
    prompt = build_user_prompt("What is the accuracy?", [(_DOC, 0.85)])
    assert "What is the accuracy?" in prompt


def test_build_user_prompt_includes_source_citation() -> None:
    """build_user_prompt cites the source filename."""
    prompt = build_user_prompt("Q?", [(_DOC, 0.85)])
    assert "model_card.md" in prompt


def test_build_user_prompt_filters_low_relevance() -> None:
    """Chunks below min_relevance are excluded from the context block."""
    low_doc = Document(id="low", text="irrelevant", source="x.md")
    prompt = build_user_prompt("Q?", [(low_doc, 0.20)], min_relevance=0.50)
    assert "irrelevant" not in prompt


def test_build_user_prompt_no_relevant_chunks() -> None:
    """When no chunks meet the threshold, a note about missing context is added."""
    prompt = build_user_prompt("Q?", [], min_relevance=0.50)
    assert "No relevant context" in prompt


def test_build_messages_returns_two_messages() -> None:
    """build_messages returns system and user messages."""
    msgs = build_messages("Tell me about the model.", [(_DOC, 0.9)])
    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"


def test_build_messages_system_content_matches_prompt() -> None:
    """System message content matches SYSTEM_PROMPT."""
    msgs = build_messages("Q?", [(_DOC, 0.9)])
    assert msgs[0]["content"] == SYSTEM_PROMPT
