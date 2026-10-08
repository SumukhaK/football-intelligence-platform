"""Checks the assistant says "I don't know" when its knowledge base can't answer.

Asks the assistant two fixed sets of questions through the real app: ones the
indexed docs answer, which it must answer, and football or general questions
they don't, which it must refuse with the exact phrase from the system prompt.
The retrieval cut-off in ``assistant/prompting/templates.py`` was set from
these questions.

Needs the assistant index and a running Ollama. Run from ``ai/``:

    LIVE_REFRESH_HOUR=off uv run python -m evaluation.assistant_abstention
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.services.season_router import FUTURE_SEASON_REPLY, PLAYER_REPLY

REFUSAL = "I don't have enough information in my knowledge base to answer that."

ANSWERABLE = (
    "What was the model's test accuracy?",
    "Why was XGBoost chosen?",
    "What is the draw possible tag?",
    "Which features matter most according to SHAP?",
    "How is the train/test split done?",
    "Which leagues does the platform cover?",
    "What is the Dixon-Coles goals model used for?",
    "How often is the data refreshed?",
    "Where do the upcoming fixtures come from?",
    "How are team names matched across sources?",
)

UNANSWERABLE = (
    "Who won the 1966 World Cup?",
    "What is the capital of France?",
    "How many goals did Messi score in 2012?",
    "Who is Arsenal's manager?",
    "Which player has the most Ballon d'Or awards?",
    "How much did Chelsea pay for Enzo Fernandez?",
    "Who is the top scorer in the Premier League this season?",
    "What formation does Barcelona play?",
    "Is Mbappe injured?",
    "What stadium does Juventus play in?",
)


@dataclass(frozen=True)
class CaseResult:
    """Whether the assistant answered or refused as it should have."""

    question: str
    answer: str
    should_refuse: bool

    @property
    def passed(self) -> bool:
        """True when the answer refuses exactly when it should."""
        return is_refusal(self.answer) == self.should_refuse


def is_refusal(answer: str) -> bool:
    """True for the prompt's "I don't know" reply or a router's fixed refusal."""
    fixed = (PLAYER_REPLY, FUTURE_SEASON_REPLY.split("{", 1)[0])
    return REFUSAL.rstrip(".") in answer or answer.startswith(fixed)


def _ask(client: Any, question: str) -> str:
    response = client.post("/v2/assistant/chat", json={"message": question})
    response.raise_for_status()
    return str(response.json()["answer"])


def run_cases(client: Any) -> list[CaseResult]:
    """Ask every question and record whether each answer behaved."""
    cases = [(q, False) for q in ANSWERABLE] + [(q, True) for q in UNANSWERABLE]
    return [CaseResult(q, _ask(client, q), refuse) for q, refuse in cases]


def main() -> int:
    """Run the cases against the real app; non-zero if any fail."""
    from fastapi.testclient import TestClient  # noqa: PLC0415

    from backend.app.main import create_app  # noqa: PLC0415

    with TestClient(create_app()) as client:
        if not client.get("/v2/health").json().get("assistant_available"):
            raise SystemExit("Assistant unavailable: start Ollama, build the index.")
        results = run_cases(client)
    for result in results:
        expected = "refuse" if result.should_refuse else "answer"
        print(f"{'PASS' if result.passed else 'FAIL'}  [{expected}] {result.question}")
        print(f"      {result.answer.strip()[:200]}\n")
    for should_refuse, label in ((True, "refused"), (False, "answered")):
        group = [r for r in results if r.should_refuse == should_refuse]
        print(f"{label}: {sum(r.passed for r in group)}/{len(group)}")
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
