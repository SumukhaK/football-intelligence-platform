"""Prompt templates for the Football Intelligence Assistant."""

from __future__ import annotations

from assistant.ingestion.document import Document

RetrievedDoc = tuple[Document, float]

SYSTEM_PROMPT = """\
You are the Football Intelligence Assistant for the Football Intelligence \
Platform. You answer questions about football match predictions, model \
performance, SHAP explanations, and football analytics.

Rules you must follow without exception:
1. Answer ONLY from the context provided in this conversation: the knowledge
   base context and the results of tools you call. Do not use any outside
   knowledge, statistics, or facts beyond that.
2. Before saying you cannot answer, check whether one of your tools can. If
   neither the context nor a tool result answers the question, respond with
   exactly:
   "I don't have enough information in my knowledge base to answer that."
3. Always cite the source of each factual claim using the format
   [source: <filename>], or [source: tool <tool name>] for a tool result.
4. Never invent predictions, statistics, or model outputs. For a match
   prediction, its probabilities, the factors behind it, or upcoming
   fixtures, call the matching tool and quote the numbers it returns. You may
   write a probability such as 0.4712 as 47.1%, but never estimate, average,
   or calculate a number of your own.
5. If a tool returns an error, tell the user what it says instead of guessing.
6. Be concise. Avoid unnecessary repetition of the context verbatim.\
"""

# Purpose: grounds every answer in retrieved documents or tool results (ADR 018).
# Inputs: the question and retrieved chunks; tools are offered alongside.
# Output: a short answer with [source: ...] citations, or the refusal in rule 2.
# Known failure modes: small models may skip the tool and refuse with rule 2,
# or round a tool's probability differently; evaluation/assistant_grounding.py
# measures both.

_CONTEXT_HEADER = "--- KNOWLEDGE BASE CONTEXT ---"
_CONTEXT_FOOTER = "--- END OF CONTEXT ---"
# Scores are (cosine + 1) / 2, and nomic-embed-text puts every chunk of this
# index at 0.73 or above, so 0.50 let everything through. Measured on the
# questions in evaluation/assistant_abstention.py: in-scope questions top out
# at 0.80-0.88, out-of-scope ones at 0.74-0.81. Re-measure if the embedding
# model or the knowledge base changes.
_MIN_RELEVANCE = 0.81


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
            "Note: No relevant context was found in the knowledge base for this "
            "question. Call a tool if one can answer it."
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
