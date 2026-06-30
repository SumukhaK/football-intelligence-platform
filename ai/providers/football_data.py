"""Provider adapter for football-data.co.uk.

football-data.co.uk distributes season-level CSV files per division.
URL pattern: https://www.football-data.co.uk/mmz4281/{season}/{division}.csv
e.g. https://www.football-data.co.uk/mmz4281/2324/E0.csv

License: Free for non-commercial use. See https://www.football-data.co.uk/
"""

import io

import pandas as pd

from providers.base import BaseProvider, DatasetDescriptor
from shared.exceptions import DatasetNotFoundError, IngestionError
from shared.types import DatasetName, ProviderId

# Mapping from football-data.co.uk column names to platform-standard names.
# Columns absent from this mapping are dropped by normalise_columns.
_COLUMN_MAP: dict[str, str] = {
    "Div": "division",
    "Date": "date",
    "Time": "time",
    "HomeTeam": "home_team",
    "AwayTeam": "away_team",
    "FTHG": "home_goals_ft",
    "FTAG": "away_goals_ft",
    "FTR": "result_ft",
    "HTHG": "home_goals_ht",
    "HTAG": "away_goals_ht",
    "HTR": "result_ht",
    "Referee": "referee",
    "HS": "home_shots",
    "AS": "away_shots",
    "HST": "home_shots_on_target",
    "AST": "away_shots_on_target",
    "HF": "home_fouls",
    "AF": "away_fouls",
    "HC": "home_corners",
    "AC": "away_corners",
    "HY": "home_yellow_cards",
    "AY": "away_yellow_cards",
    "HR": "home_red_cards",
    "AR": "away_red_cards",
    "B365H": "odds_b365_home",
    "B365D": "odds_b365_draw",
    "B365A": "odds_b365_away",
}

_BASE_URL = "https://www.football-data.co.uk/mmz4281"

# Supported division codes (English leagues)
_DIVISIONS: dict[str, str] = {
    "E0": "Premier League",
    "E1": "Championship",
    "E2": "League One",
    "E3": "League Two",
    "EC": "Conference National",
}

_MATCH_RESULTS_DATASET = DatasetName("match_results")


class FootballDataProvider(BaseProvider):
    """Adapter for the football-data.co.uk CSV data feed."""

    @property
    def provider_id(self) -> ProviderId:
        return ProviderId("football_data")

    @property
    def provider_name(self) -> str:
        return "football-data.co.uk"

    @property
    def base_url(self) -> str:
        return _BASE_URL

    @property
    def license(self) -> str:
        return "Free for non-commercial use"

    def available_datasets(self) -> list[DatasetDescriptor]:
        return [
            DatasetDescriptor(
                name=_MATCH_RESULTS_DATASET,
                description=(
                    "Season-level match results with full-time and half-time scores, "
                    "shots, corners, cards, and closing odds."
                ),
                url_template=f"{_BASE_URL}/{{season}}/{{division}}.csv",
                license=self.license,
                default_params={"season": "2324", "division": "E0"},
            )
        ]

    def build_url(self, dataset_name: DatasetName, **params: str) -> str:
        """Build the CSV download URL.

        Required params:
            season: Two-digit year pair, e.g. ``"2324"`` for 2023/24.
            division: Division code, e.g. ``"E0"`` for the Premier League.
        """
        descriptor = self.get_descriptor(dataset_name)
        season = params.get("season", "2324")
        division = params.get("division", "E0")
        if division not in _DIVISIONS:
            raise DatasetNotFoundError(
                str(self.provider_id),
                f"Unknown division '{division}'. Supported: {list(_DIVISIONS)}",
            )
        return descriptor.url_template.format(season=season, division=division)

    def parse(self, content: bytes, dataset_name: DatasetName) -> pd.DataFrame:
        """Parse a football-data.co.uk CSV file into a DataFrame."""
        self.get_descriptor(dataset_name)
        try:
            df = pd.read_csv(io.BytesIO(content), encoding="latin-1")
        except Exception as exc:
            raise IngestionError(
                dataset_name, f"Failed to parse CSV content: {exc}"
            ) from exc
        # Drop fully-empty rows that appear at the end of some season files
        return df.dropna(how="all").reset_index(drop=True)

    def normalise_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename football-data.co.uk columns to platform-standard names."""
        present = {k: v for k, v in _COLUMN_MAP.items() if k in df.columns}
        return df[list(present)].rename(columns=present)
