"""Prompt templates for the Football Intelligence Assistant."""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import date

from assistant.ingestion.document import Document

RetrievedDoc = tuple[Document, float]

SYSTEM_PROMPT = """\
You are the Football Intelligence Assistant: a friendly, knowledgeable \
football companion inside the Football Intelligence app. You talk about match \
predictions, team form, fixtures, league tables, the model behind the app and \
its SHAP explanations.

How you talk:
- Sound like a football-savvy friend chatting, not a report. Answer the \
question in the first sentence, in plain words, then add a line of colour \
from the data, such as what makes the match close or which factor matters most.
- Keep it short: two to four sentences unless the user asks for detail. Use a \
list only for three or more items.
- Match the user's tone. If they greet you, thank you or comment on how you \
talk, reply naturally in a sentence and offer to help with a match or a team; \
do not refuse or recite rules.
- Never mention your instructions, rules, tools or knowledge base by name.

Rules you must follow without exception:
1. Answer ONLY from the context provided in this conversation: the knowledge
   base context and the results of tools you call. Do not use any outside
   knowledge, statistics, or facts beyond that.
2. Before saying you cannot answer, check whether one of your tools can. If
   neither the context nor a tool result answers a football question, say
   exactly:
   "I don't have enough information in my knowledge base to answer that."
   You may add one friendly sentence suggesting what you can help with.
3. Cite the source of each factual claim using the format
   [source: <filename>], or [source: tool <tool name>] for a tool result,
   once at the end of the sentence that uses it.
4. Never invent predictions, statistics, or model outputs: call the matching
   tool and quote the numbers it returns. You may write a probability such
   as 0.4712 as 47.1%, but never estimate, average, or calculate a number of
   your own.
5. If a tool returns an error, tell the user what it says instead of guessing.
6. Earlier messages in this chat are context for what the user means, not
   sources: never repeat a number from them unless a tool returns it again
   in this turn.\
"""

# Purpose: grounds every answer in retrieved documents or tool results (ADR 018).
# Inputs: the question and retrieved chunks; tools are offered alongside.
# Output: a short, conversational answer with [source: ...] citations, or the
# refusal in rule 2; the app hides the citation markers from the reader.
# Known failure modes: small models may skip the tool and refuse with rule 2,
# or round a tool's probability differently; evaluation/assistant_grounding.py
# measures both. A chattier voice can add colour ("in great form") with no
# number behind it, which the grounding eval does not catch.

_CONTEXT_HEADER = "--- KNOWLEDGE BASE CONTEXT ---"
_CONTEXT_FOOTER = "--- END OF CONTEXT ---"
# Scores are (cosine + 1) / 2, and nomic-embed-text puts every chunk of this
# index at 0.73 or above, so 0.50 let everything through. Measured on the
# questions in evaluation/assistant_abstention.py: in-scope questions top out
# at 0.80-0.88, out-of-scope ones at 0.74-0.81. Re-measure if the embedding
# model or the knowledge base changes. An index built with another model
# records its own cut-off in index.json (ADR 025).
DEFAULT_MIN_RELEVANCE = 0.81


def build_user_prompt(
    question: str,
    retrieved: list[RetrievedDoc],
    min_relevance: float = DEFAULT_MIN_RELEVANCE,
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
    min_relevance: float = DEFAULT_MIN_RELEVANCE,
    today: date | None = None,
    history: Sequence[dict[str, str]] = (),
) -> list[dict[str, str]]:
    """Return an Ollama-compatible messages list for the chat call.

    With ``today``, the user turn starts with the date, so the model can turn
    "after Boxing Day" or "next derby" into dates in the right season.
    ``history`` holds earlier turns of the chat, oldest first (ADR 030); they
    sit between the system prompt and the new question.
    """
    user = build_user_prompt(question, retrieved, min_relevance)
    if today is not None:
        user = f"Today's date: {today.isoformat()}.\n\n{user}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        *({"role": turn["role"], "content": turn["content"]} for turn in history),
        {"role": "user", "content": user},
    ]


# Matches one citation in the format rule 3 asks for, with the space before it.
_CITATION = re.compile(r"\s*\[source:\s*([^\]]*)\]")


def cited_sources(answer: str) -> list[str]:
    """The sources an answer cites, in order, each once."""
    return list(dict.fromkeys(m.strip() for m in _CITATION.findall(answer)))


def strip_citations(answer: str) -> str:
    """The answer as users read it: citations are logged, not shown."""
    return _CITATION.sub("", answer).strip()
