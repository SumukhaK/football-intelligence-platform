"""Prompt templates for the Football Intelligence Assistant."""

from __future__ import annotations

from assistant.ingestion.document import Document

RetrievedDoc = tuple[Document, float]

SYSTEM_PROMPT = """\
You are the Football Intelligence Assistant for the Football Intelligence \
Platform. You answer questions about football match predictions, model \
performance, SHAP explanations, and football analytics.

Rules you must follow without exception:
1. Answer ONLY from the context provided in this conversation. Do not use
   any outside knowledge, statistics, or facts beyond what is in the context.
2. If the provided context does not contain enough information to answer the
   question, respond with exactly:
   "I don't have enough information in my knowledge base to answer that."
3. Always cite the source of each factual claim using the format [source: <filename>].
4. Never invent predictions, statistics, or model outputs.
5. Be concise. Avoid unnecessary repetition of the context verbatim.\
"""

_CONTEXT_HEADER = "--- KNOWLEDGE BASE CONTEXT ---"
_CONTEXT_FOOTER = "--- END OF CONTEXT ---"
_MIN_RELEVANCE = 0.50


def build_user_prompt(
    question: str,
    retrieved: list[RetrievedDoc],
    min_relevance: float = _MIN_RELEVANCE,
) -> str:
    """Assemble the user-turn prompt from the question and retrieved chunks.

    Chunks below *min_relevance* are excluded. If no chunks meet the
    threshold, the context section is omitted entirely so the model can
    apply rule #2.
    """
    relevant = [(doc, score) for doc, score in retrieved if score >= min_relevance]

    if not relevant:
        return (
            f"Question: {question}\n\n"
            "Note: No relevant context was found for this question."
        )

    lines: list[str] = [_CONTEXT_HEADER, ""]
    for doc, score in relevant:
        filename = doc.metadata.get("filename", doc.source)
        lines.append(f"[source: {filename}] (relevance: {score:.2f})")
        lines.append(doc.text.strip())
        lines.append("")
    lines.append(_CONTEXT_FOOTER)
    lines.append("")
    lines.append(f"Question: {question}")
    return "\n".join(lines)


def build_messages(
    question: str,
    retrieved: list[RetrievedDoc],
    min_relevance: float = _MIN_RELEVANCE,
) -> list[dict[str, str]]:
    """Return an Ollama-compatible messages list for the chat call."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_user_prompt(question, retrieved, min_relevance),
        },
    ]
