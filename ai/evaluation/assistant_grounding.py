"""Checks the assistant quotes the API's prediction instead of inventing numbers.

For upcoming fixtures in each league it asks the assistant for the model's
prediction, calls POST /v2/predict and /v2/explain for the same match, and
checks that the answer quotes the predicted outcome's probability and that
every number in it appears in those responses or the question (ADR 018).
One extra case asks about a team that does not exist.

Needs the trained model, match history, fixtures, the assistant index and a
running Ollama. Run from ``ai/``:

    LIVE_REFRESH_HOUR=off uv run python -m evaluation.assistant_grounding
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

_NUMBER = re.compile(r"\d+(?:\.\d+)?")
_UNKNOWN_TEAM = "Atlantis FC"
_ENDPOINTS = ("/v2/predict", "/v2/explain")


@dataclass(frozen=True)
class CaseResult:
    """How one answer scored against the API's own output."""

    question: str
    answer: str
    quoted_prediction: bool
    ungrounded: list[str]

    @property
    def passed(self) -> bool:
        """True when the prediction is quoted and no number is invented."""
        return self.quoted_prediction and not self.ungrounded


def numbers_in(text: str) -> list[str]:
    """Every unsigned number written in ``text``, as written."""
    return _NUMBER.findall(text)


def matches(token: str, value: float) -> bool:
    """True when ``token`` is ``value`` (or ``value`` as a percentage) rounded.

    A probability such as 0.4712 matches "47", "47.1" or "0.47", but not "0"
    or "1": a bare integer only matches it as a percentage.
    """
    decimals = len(token.partition(".")[2])
    tolerance = 0.5 * 10**-decimals + 1e-9
    candidates = [abs(value) * 100]
    if decimals >= 2 or abs(value) >= 1:
        candidates.append(abs(value))
    return any(abs(float(token) - c) <= tolerance for c in candidates)


def ungrounded_numbers(answer: str, sources: Iterable[str]) -> list[str]:
    """Numbers in ``answer`` that no number in ``sources`` accounts for."""
    values = [float(t) for source in sources for t in numbers_in(source)]
    return [t for t in numbers_in(answer) if not any(matches(t, v) for v in values)]


def quotes_prediction(answer: str, prediction: Mapping[str, Any]) -> bool:
    """True when ``answer`` states the predicted outcome's probability."""
    confidence = float(prediction["confidence"])
    return any(matches(t, confidence) for t in numbers_in(answer))


def score_prediction_answer(
    question: str, answer: str, api_outputs: list[Mapping[str, Any]]
) -> CaseResult:
    """Score an answer to a prediction question against /predict and /explain."""
    sources = [question, *(json.dumps(output) for output in api_outputs)]
    return CaseResult(
        question=question,
        answer=answer,
        quoted_prediction=quotes_prediction(answer, api_outputs[0]),
        ungrounded=ungrounded_numbers(answer, sources),
    )


def score_unknown_team_answer(
    question: str, answer: str, api_error: Mapping[str, Any]
) -> CaseResult:
    """Score an answer about a team the API rejects: it must not invent numbers.

    Numbers in the API's error, such as the season it names, may be repeated.
    """
    return CaseResult(
        question=question,
        answer=answer,
        quoted_prediction=True,
        ungrounded=ungrounded_numbers(answer, [question, json.dumps(api_error)]),
    )


def _run(client: Any, per_league: int) -> list[CaseResult]:
    results = []
    for league in client.get("/v2/competitions").json()["competitions"]:
        name = league["name"]
        fixtures = client.get(
            "/v2/fixtures", params={"competition": name, "limit": per_league}
        ).json()["fixtures"]
        for fixture in fixtures:
            match = {
                "home_team": fixture["home_team"],
                "away_team": fixture["away_team"],
                "competition": name,
            }
            question = (
                f"What does the model predict for {match['home_team']} vs "
                f"{match['away_team']} in the {name}?"
            )
            outputs = [client.post(path, json=match).json() for path in _ENDPOINTS]
            answer = _ask(client, question)
            # The fixture itself (date, kick-off) is a fair source too.
            outputs.append(fixture)
            results.append(score_prediction_answer(question, answer, outputs))
    question = f"What does the model predict for {_UNKNOWN_TEAM} vs Arsenal?"
    error = client.post(
        _ENDPOINTS[0], json={"home_team": _UNKNOWN_TEAM, "away_team": "Arsenal"}
    ).json()
    results.append(score_unknown_team_answer(question, _ask(client, question), error))
    return results


def _ask(client: Any, question: str) -> str:
    response = client.post("/v2/assistant/chat", json={"message": question})
    response.raise_for_status()
    return str(response.json()["answer"])


def main() -> int:
    """Run the grounding cases against the real app; non-zero if any fail."""
    from fastapi.testclient import TestClient  # noqa: PLC0415

    from backend.app.main import create_app  # noqa: PLC0415

    parser = argparse.ArgumentParser(
        description="Check the assistant quotes the API's predictions."
    )
    parser.add_argument("--per-league", type=int, default=2)
    args = parser.parse_args()
    with TestClient(create_app()) as client:
        if not client.get("/v2/health").json().get("assistant_available"):
            raise SystemExit("Assistant unavailable: start Ollama, build the index.")
        results = _run(client, args.per_league)
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status}  {result.question}")
        print(f"      quoted={result.quoted_prediction} ungrounded={result.ungrounded}")
        print(f"      {result.answer.strip()}\n")
    passed = sum(result.passed for result in results)
    print(f"{passed}/{len(results)} answers grounded in the API's output.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
