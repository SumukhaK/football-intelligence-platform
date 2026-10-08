"""Checks the assistant answers season questions from its season tools.

Each case asks a question, runs the season tool the answer should come from
(``team_matches`` or ``league_table``, ADR 021) to get the expected team, and
checks the answer names that team and invents no number absent from the
tool's output, the question or today's date. Questions about next season or
individual players must be refused without numbers.

Needs the trained model, match history, fixtures, the assistant index and a
running Ollama. Run from ``ai/``:

    LIVE_REFRESH_HOUR=off uv run python -m evaluation.assistant_season
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

from evaluation.assistant_grounding import ungrounded_numbers

Expected = Callable[[Callable[..., dict[str, Any]]], tuple[str, dict[str, Any]]]


@dataclass(frozen=True)
class SeasonCase:
    """A question and how to find the answer it must contain."""

    question: str
    expected: Expected | None  # None: the answer must name no team or number


@dataclass(frozen=True)
class SeasonResult:
    """How one answer scored."""

    question: str
    answer: str
    expected_team: str | None
    named_team: bool
    ungrounded: list[str]

    @property
    def passed(self) -> bool:
        """True when the expected team is named and no number is invented."""
        return self.named_team and not self.ungrounded


def score_answer(
    question: str,
    answer: str,
    expected_team: str | None,
    tool_output: Mapping[str, Any] | None,
    today: date,
) -> SeasonResult:
    """Score ``answer`` against the tool output it should be grounded in."""
    sources = [question, today.isoformat()]
    if tool_output is not None:
        sources.append(json.dumps(tool_output))
    named = expected_team is None or expected_team.lower() in answer.lower()
    return SeasonResult(
        question=question,
        answer=answer,
        expected_team=expected_team,
        named_team=named,
        ungrounded=ungrounded_numbers(answer, sources),
    )


def _table_leader(column: str, competition: str, on: str | None) -> Expected:
    def expected(call: Callable[..., dict[str, Any]]) -> tuple[str, dict[str, Any]]:
        args = {"competition": competition, **({"date": on} if on else {})}
        output = call("league_table", **args)
        rows = output["table"]
        leader = max(rows, key=lambda row: row[column])
        return str(leader["team"]), output

    return expected


CASES = (
    SeasonCase(
        "Who will top the Premier League after the Boxing Day games?",
        _table_leader("chance_first", "Premier League", "2026-12-27"),
    ),
    SeasonCase(
        "Who won the Premier League in 2015/16?",
        lambda call: ("Leicester", call("league_table", season="2015/16")),
    ),
    SeasonCase(
        "When is the next Manchester derby?",
        # Either club name counts; the numbers must come from the tool.
        lambda call: (
            "Man",
            call("team_matches", team="Man City", opponent="Man United"),
        ),
    ),
    SeasonCase(
        "Which Bundesliga team will keep the most clean sheets this season?",
        _table_leader("chance_most_clean_sheets", "Bundesliga", "2027-06-30"),
    ),
    SeasonCase(
        "Which Serie A team will score the most goals this season?",
        _table_leader("chance_most_goals", "Serie A", "2027-06-30"),
    ),
    SeasonCase("Who will win La Liga next season?", None),
    SeasonCase("Who will be the Premier League's top scorer this season?", None),
)


def run_cases(
    ask: Callable[[str], str], call: Callable[..., dict[str, Any]], today: date
) -> list[SeasonResult]:
    """Ask every case and score it against its tool output."""
    results = []
    for case in CASES:
        team, output = case.expected(call) if case.expected else (None, None)
        results.append(
            score_answer(case.question, ask(case.question), team, output, today)
        )
    return results


def main() -> int:
    """Run the cases against the real app; non-zero if any fail."""
    from fastapi.testclient import TestClient  # noqa: PLC0415

    from assistant.tools.tool import run_tool  # noqa: PLC0415
    from backend.app.dependencies import get_served_competitions  # noqa: PLC0415
    from backend.app.main import create_app  # noqa: PLC0415
    from backend.app.services.season_tools import SeasonTools  # noqa: PLC0415

    app = create_app()
    with TestClient(app) as client:
        tools = SeasonTools(app.state, get_served_competitions()).tools()

        def call(name: str, **args: Any) -> dict[str, Any]:
            result: dict[str, Any] = json.loads(run_tool(tools, name, args))
            return result

        def ask(question: str) -> str:
            response = client.post("/v2/assistant/chat", json={"message": question})
            response.raise_for_status()
            return str(response.json()["answer"])

        results = run_cases(ask, call, date.today())
    for result in results:
        print(f"{'PASS' if result.passed else 'FAIL'}  {result.question}")
        print(f"      expected={result.expected_team} ungrounded={result.ungrounded}")
        print(f"      {result.answer.strip()[:300]}\n")
    passed = sum(result.passed for result in results)
    print(f"{passed}/{len(results)} season answers grounded in the tools.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
