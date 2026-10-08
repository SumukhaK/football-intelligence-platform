"""Prompt templates for the Football Intelligence Assistant."""

from __future__ import annotations

from datetime import date

from assistant.ingestion.document import Document

RetrievedDoc = tuple[Document, float]

SYSTEM_PROMPT = """\
You are the Football Intelligence Assistant for the Football Intelligence \
Platform. You answer two kinds of questions:
- Football questions about the Premier League, Bundesliga, La Liga, Serie A
  and Ligue 1: match predictions and their reasons, fixtures, results,
  head-to-head meetings, league tables on any date of this or a past season,
  and which teams will score most goals or keep most clean sheets. Answer
  these with your tools. The knowledge base context holds no match data.
- Questions about the platform itself (its model, data, evaluation and
  design). Answer these from the knowledge base context.

Rules you must follow without exception:
1. Answer ONLY from the results of tools you call and the knowledge base
   context. Do not use any outside knowledge, statistics, or facts.
2. For a football question, call a tool before deciding you cannot answer.
   If neither a tool result nor the context answers the question, respond
   with exactly:
   "I don't have enough information in my knowledge base to answer that."
3. Always cite the source of each factual claim using the format
   [source: <filename>], or [source: tool <tool name>] for a tool result.
4. Never invent predictions, statistics, or model outputs: call the matching
   tool and quote the numbers it returns. You may write a probability such
   as 0.4712 as 47.1%, but never estimate, average, or calculate a number of
   your own.
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
_TOOL_HINT = (
    "Note: the context above only describes the platform. If it does not "
    "answer the question, call a tool if one can."
)
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
    lines.append("")
    # Without this, small models refuse football questions whenever some
    # platform document scores above the cut-off, instead of calling a tool.
    lines.append(_TOOL_HINT)
    return "\n".join(lines)


def build_messages(
    question: str,
    retrieved: list[RetrievedDoc],
    min_relevance: float = _MIN_RELEVANCE,
    today: date | None = None,
) -> list[dict[str, str]]:
    """Return an Ollama-compatible messages list for the chat call.

    With ``today``, the user turn starts with the date, so the model can turn
    "after Boxing Day" or "next derby" into dates in the right season.
    """
    user = build_user_prompt(question, retrieved, min_relevance)
    if today is not None:
        user = f"Today's date: {today.isoformat()}.\n\n{user}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
