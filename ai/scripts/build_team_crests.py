"""Build ``datasets/schemas/team_crests.csv``: canonical team name → crest URL.

Crest URLs come from the football-data.org snapshot in the Kaggle "live
results" download (ADR 020). That source names teams its own way, so each
canonical name is matched by the games it played rather than by spelling:

1. Results join on league, date (±1 day for time zones) and score. Each joined
   game is a vote for the crest of each side; a team's crest is its winning
   vote when it holds at least ``MIN_SHARE`` of them.
2. Fixtures (this season's promoted teams have no results yet) join on league
   and date, and only games where one side's crest is already known vote for
   the other side.

Teams left unmatched are printed; the app shows a placeholder for them.

Usage:
    uv run python -m scripts.build_team_crests
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from backend.app.services.fixtures_service import find_latest_fixtures

SNAPSHOT = Path(
    "../datasets/raw/kaggle/adrianjuliusaluoch_live_results/football_matches.parquet"
)
RESULTS_DIR = Path("../datasets/processed/football_data")
FIXTURES_DIR = Path("../datasets/processed/openfootball")
OUTPUT = Path("../datasets/schemas/team_crests.csv")
FIRST_SEASON = "2022/23"
MIN_SHARE = 0.6
LEAGUE_NAMES = {"Primera Division": "La Liga"}
DAY_OFFSETS = (0, 1, -1)


def load_snapshot(path: Path) -> pd.DataFrame:
    """The snapshot's games with our league names, UTC dates and PNG crests."""
    raw = pd.read_parquet(path)
    games = pd.DataFrame(
        {
            "competition": raw["competition.name"].replace(LEAGUE_NAMES),
            "date": pd.to_datetime(raw["utcDate"], utc=True).dt.strftime("%Y-%m-%d"),
            "home_goals": raw["score.fullTime.home"],
            "away_goals": raw["score.fullTime.away"],
            "home_crest": raw["homeTeam.crest"],
            "away_crest": raw["awayTeam.crest"],
        }
    )
    # The Android image loader has no SVG decoder; such teams get the placeholder.
    png = games["home_crest"].str.endswith(".png") & games["away_crest"].str.endswith(
        ".png"
    )
    return games[png].drop_duplicates()


def join_on_dates(
    ours: pd.DataFrame, games: pd.DataFrame, on: list[str]
) -> pd.DataFrame:
    """Our games joined to snapshot games on ``on`` plus a date ±1 day."""
    joined = []
    for offset in DAY_OFFSETS:
        shifted = pd.to_datetime(ours["match_date"]) + pd.Timedelta(days=offset)
        moved = ours.assign(date=shifted.dt.strftime("%Y-%m-%d"))
        joined.append(moved.merge(games, on=["competition", "date", *on]))
    return pd.concat(joined, ignore_index=True)


def tally(joined: pd.DataFrame) -> pd.DataFrame:
    """One vote per (team, crest) pair a joined game supports."""
    home = joined[["home_team", "home_crest"]].set_axis(["team", "crest"], axis=1)
    away = joined[["away_team", "away_crest"]].set_axis(["team", "crest"], axis=1)
    return pd.concat([home, away], ignore_index=True)


def winners(votes: pd.DataFrame) -> dict[str, str]:
    """Each team's most-voted crest, kept when it has ``MIN_SHARE`` of the votes."""
    counts = votes.value_counts(["team", "crest"]).reset_index(name="votes")
    counts["share"] = counts["votes"] / counts.groupby("team")["votes"].transform("sum")
    best = counts.sort_values("votes", ascending=False).drop_duplicates("team")
    best = best[best["share"] >= MIN_SHARE]
    return dict(zip(best["team"], best["crest"], strict=True))


def anchored_votes(joined: pd.DataFrame, known: dict[str, str]) -> pd.DataFrame:
    """Votes from joined games where the other side's crest is already known."""
    home_known = joined["home_team"].map(known) == joined["home_crest"]
    away_known = joined["away_team"].map(known) == joined["away_crest"]
    return pd.concat(
        [
            tally(joined[home_known & ~away_known]),
            tally(joined[away_known & ~home_known]),
        ]
    ).query("team not in @known")


def match_crests(
    results: pd.DataFrame, fixtures: pd.DataFrame, games: pd.DataFrame
) -> dict[str, str]:
    """Canonical team name → crest URL, from results first, then fixtures."""
    scored = join_on_dates(
        results.rename(
            columns={
                "full_time_home_goals": "home_goals",
                "full_time_away_goals": "away_goals",
            }
        ),
        games,
        ["home_goals", "away_goals"],
    )
    known = winners(tally(scored))
    by_date = join_on_dates(
        fixtures, games.drop(columns=["home_goals", "away_goals"]), []
    )
    return known | winners(anchored_votes(by_date, known))


def main() -> None:
    """Write the crest table and list the teams left without a crest."""
    results = pd.read_csv(sorted(RESULTS_DIR.glob("match_results_top5_v*.csv"))[-1])
    results = results[results["season"] >= FIRST_SEASON]
    fixtures = pd.read_csv(find_latest_fixtures(FIXTURES_DIR))
    crests = match_crests(results, fixtures, load_snapshot(SNAPSHOT))
    table = pd.DataFrame(
        sorted(crests.items()), columns=["canonical_name", "crest_url"]
    )
    table.to_csv(OUTPUT, index=False)
    teams = set(results["home_team"]) | set(fixtures["home_team"])
    teams |= set(fixtures["away_team"])
    print(f"Wrote {len(table)} crests to {OUTPUT}")
    print("No crest:", ", ".join(sorted(teams - crests.keys())) or "none")


if __name__ == "__main__":
    main()
