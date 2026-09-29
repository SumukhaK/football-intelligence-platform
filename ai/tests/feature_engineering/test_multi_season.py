"""Multi-season and multi-league behaviour of the feature modules (plan §5.1)."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from feature_engineering.features.elo_rating import EloRatingFeature
from feature_engineering.features.head_to_head import HeadToHeadFeature
from feature_engineering.features.league_position import LeaguePositionFeature
from feature_engineering.features.rest_days import RestDaysFeature


def _match(
    day: str, season: str, home: str, away: str, result: str, comp: str = "EPL"
) -> dict[str, object]:
    goals = {"H": (1, 0), "D": (1, 1), "A": (0, 1)}[result]
    return {
        "match_date": day,
        "season": season,
        "competition": comp,
        "home_team": home,
        "away_team": away,
        "full_time_home_goals": goals[0],
        "full_time_away_goals": goals[1],
        "result": result,
    }


@pytest.fixture()
def two_seasons() -> pd.DataFrame:
    """Season 1: A beats B twice, C draws D. Season 2: D is replaced by E."""
    return pd.DataFrame(
        [
            _match("2022-08-06", "2022/23", "A", "B", "H"),
            _match("2022-08-06", "2022/23", "C", "D", "D"),
            _match("2023-05-20", "2022/23", "B", "A", "A"),
            _match("2023-05-20", "2022/23", "D", "C", "D"),
            _match("2023-08-12", "2023/24", "A", "E", "H"),
            _match("2023-08-12", "2023/24", "B", "C", "H"),
        ]
    )


class TestLeaguePositionPerSeason:
    def test_table_resets_at_new_season(self, two_seasons: pd.DataFrame) -> None:
        result = LeaguePositionFeature().compute(two_seasons)
        assert result.loc[4, "home_league_points"] == 0
        assert result.loc[4, "home_matches_played"] == 0
        assert result.loc[4, "home_league_position"] == 1

    def test_competitions_keep_separate_tables(self) -> None:
        df = pd.DataFrame(
            [
                _match("2023-08-12", "2023/24", "A", "B", "H", comp="EPL"),
                _match("2023-08-13", "2023/24", "X", "Y", "D", comp="BL"),
            ]
        )
        result = LeaguePositionFeature().compute(df)
        assert result.loc[1, "home_league_points"] == 0
        assert result.loc[1, "home_league_position"] == 1

    def test_same_day_matches_do_not_see_each_other(self) -> None:
        rows = [
            _match("2023-08-12", "2023/24", "A", "B", "H"),
            _match("2023-08-12", "2023/24", "C", "D", "H"),
        ]
        forward = LeaguePositionFeature().compute(pd.DataFrame(rows))
        backward = LeaguePositionFeature().compute(pd.DataFrame(rows[::-1]))
        assert forward["home_league_position"].tolist() == [1, 1]
        assert backward["home_league_position"].tolist() == [1, 1]


class TestRestDaysPerSeason:
    def test_first_match_of_new_season_is_nan(self, two_seasons: pd.DataFrame) -> None:
        result = RestDaysFeature().compute(two_seasons)
        rest = result["home_rest_days"]
        assert math.isnan(float(rest.iloc[4]))
        assert math.isnan(float(rest.iloc[5]))

    def test_rest_days_within_season_unchanged(self, two_seasons: pd.DataFrame) -> None:
        result = RestDaysFeature().compute(two_seasons)
        assert result.loc[2, "home_rest_days"] == 287.0


class TestEloAcrossSeasons:
    def test_ratings_regress_a_third_towards_1500(
        self, two_seasons: pd.DataFrame
    ) -> None:
        feature = EloRatingFeature()
        season_one = feature.compute(two_seasons.iloc[:4])
        end_ratings = feature.final_ratings(two_seasons.iloc[:4])
        assert float(season_one["away_elo_before"].iloc[2]) > 1500
        a_end = end_ratings[("EPL", "A")]
        result = feature.compute(two_seasons)
        expected = 1500 + (a_end - 1500) * (2 / 3)
        assert result.loc[4, "home_elo_before"] == pytest.approx(expected)

    def test_promoted_team_starts_at_mean_of_three_lowest_ratings(
        self, two_seasons: pd.DataFrame
    ) -> None:
        feature = EloRatingFeature()
        ends = feature.final_ratings(two_seasons.iloc[:4])
        lowest = sorted(ends.values())[:3]
        result = feature.compute(two_seasons)
        assert result.loc[4, "away_elo_before"] == pytest.approx(sum(lowest) / 3)

    def test_promoted_rating_does_not_need_the_rest_of_the_season(
        self, two_seasons: pd.DataFrame
    ) -> None:
        feature = EloRatingFeature()
        full = feature.compute(two_seasons)
        first_fixture_only = feature.compute(two_seasons.iloc[:5])
        assert first_fixture_only.iloc[4].to_list() == full.iloc[4].to_list()

    def test_competitions_are_separate_pools(self) -> None:
        df = pd.DataFrame(
            [
                _match("2023-08-12", "2023/24", "A", "B", "H", comp="EPL"),
                _match("2023-08-19", "2023/24", "A", "B", "H", comp="BL"),
            ]
        )
        result = EloRatingFeature().compute(df)
        assert result.loc[1, "home_elo_before"] == 1500.0

    def test_single_season_matches_plain_elo(
        self, sample_matches: pd.DataFrame
    ) -> None:
        feature = EloRatingFeature()
        result = feature.compute(sample_matches)
        assert result.loc[0, "home_elo_before"] == 1500.0
        assert result.loc[1, "home_elo_before"] == 1500.0
        assert result.loc[2, "home_elo_before"] == pytest.approx(1484.0)


class TestHeadToHeadAcrossSeasons:
    def test_meetings_span_seasons(self, two_seasons: pd.DataFrame) -> None:
        df = pd.concat(
            [
                two_seasons,
                pd.DataFrame([_match("2024-01-01", "2023/24", "B", "A", "D")]),
            ],
            ignore_index=True,
        )
        result = HeadToHeadFeature().compute(df)
        last = result.iloc[-1]
        assert last["h2h_meetings"] == 2
        assert last["h2h_home_wins"] == 0
        assert last["h2h_away_wins"] == 2
        assert last["h2h_draws"] == 0

    def test_first_meeting_has_no_history(self, two_seasons: pd.DataFrame) -> None:
        result = HeadToHeadFeature().compute(two_seasons)
        assert result.iloc[4].to_list() == [0, 0, 0, 0]
