"""Provider adapter for FBref (https://fbref.com).

FBref provides detailed advanced statistics exported as CSV via direct links.
URL pattern: https://fbref.com/en/comps/{comp_id}/{season}/schedule/
             scores-and-fixtures (CSV export from the HTML table)

License: Data is publicly accessible. Commercial use requires attribution.
         See https://fbref.com/en/about/
"""

import io

import pandas as pd

from providers.base import BaseProvider, DatasetDescriptor
from shared.exceptions import IngestionError
from shared.types import DatasetName, ProviderId

# FBref uses inconsistent header structures (multi-row headers in HTML exports).
# The mapping below targets the flattened single-header CSV export format.
_COLUMN_MAP: dict[str, str] = {
    "Wk": "matchweek",
    "Day": "day_of_week",
    "Date": "date",
    "Time": "time",
    "Home": "home_team",
    "xG": "home_xg",
    "Score": "score",
    "xG.1": "away_xg",
    "Away": "away_team",
    "Attendance": "attendance",
    "Venue": "venue",
    "Referee": "referee",
    "Match Report": "match_report_url",
    "Notes": "notes",
}

_BASE_URL = "https://fbref.com/en/comps"

_SCORES_DATASET = DatasetName("scores_and_fixtures")
_SQUAD_STATS_DATASET = DatasetName("squad_standard_stats")


class FBrefProvider(BaseProvider):
    """Adapter for FBref advanced football statistics."""

    @property
    def provider_id(self) -> ProviderId:
        return ProviderId("fbref")

    @property
    def provider_name(self) -> str:
        return "FBref"

    @property
    def base_url(self) -> str:
        return _BASE_URL

    @property
    def license(self) -> str:
        return "Public access; attribution required for commercial use"

    def available_datasets(self) -> list[DatasetDescriptor]:
        return [
            DatasetDescriptor(
                name=_SCORES_DATASET,
                description=(
                    "Season schedule with match scores, expected goals (xG), "
                    "attendance, venue, and referee."
                ),
                url_template=(
                    f"{_BASE_URL}/{{comp_id}}/{{season}}/schedule/"
                    "{season}-scores-and-fixtures.csv"
                ),
                license=self.license,
                default_params={"comp_id": "9", "season": "2023-2024"},
            ),
            DatasetDescriptor(
                name=_SQUAD_STATS_DATASET,
                description="Season-level squad standard statistics per team.",
                url_template=(
                    f"{_BASE_URL}/{{comp_id}}/{{season}}/stats/" "{season}-stats.csv"
                ),
                license=self.license,
                default_params={"comp_id": "9", "season": "2023-2024"},
            ),
        ]

    def build_url(self, dataset_name: DatasetName, **params: str) -> str:
        """Build the FBref CSV export URL.

        Required params:
            comp_id: FBref competition ID, e.g. ``"9"`` for Premier League.
            season: Season string, e.g. ``"2023-2024"``.
        """
        descriptor = self.get_descriptor(dataset_name)
        comp_id = params.get("comp_id", "9")
        season = params.get("season", "2023-2024")
        return descriptor.url_template.format(comp_id=comp_id, season=season)

    def parse(self, content: bytes, dataset_name: DatasetName) -> pd.DataFrame:
        """Parse an FBref CSV export into a DataFrame."""
        self.get_descriptor(dataset_name)
        try:
            df = pd.read_csv(io.BytesIO(content), encoding="utf-8")
        except Exception as exc:
            raise IngestionError(
                dataset_name, f"Failed to parse FBref CSV: {exc}"
            ) from exc
        return df.dropna(how="all").reset_index(drop=True)

    def normalise_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename FBref columns to platform-standard names."""
        present = {k: v for k, v in _COLUMN_MAP.items() if k in df.columns}
        return df[list(present)].rename(columns=present)
