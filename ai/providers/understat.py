"""Provider adapter for Understat (https://understat.com).

Understat embeds match data as JSON within their HTML pages.
The data is accessed by parsing the JavaScript variable assignments in the page
source. This provider expects pre-extracted JSON bytes — the downloader is
responsible for the HTML-to-JSON extraction step.

License: Data is publicly accessible. Understat does not publish a formal
         data license. Use responsibly and in accordance with their terms of
         service.
"""

import json

import pandas as pd

from providers.base import BaseProvider, DatasetDescriptor
from shared.exceptions import IngestionError
from shared.types import DatasetName, ProviderId

# Mapping from Understat JSON keys to platform-standard column names.
# Understat embeds nested team objects; parse() flattens them before mapping.
_COLUMN_MAP: dict[str, str] = {
    "id": "match_id",
    "isResult": "is_result",
    "datetime": "date",
    "h_title": "home_team",
    "a_title": "away_team",
    "h_goals": "home_goals_ft",
    "a_goals": "away_goals_ft",
    "h_xg": "home_xg",
    "a_xg": "away_xg",
    "h_w": "home_win_prob",
    "h_d": "draw_prob",
    "h_l": "away_win_prob",
    "season": "season",
}

_BASE_URL = "https://understat.com"

_MATCH_RESULTS_DATASET = DatasetName("match_results")


class UnderstatProvider(BaseProvider):
    """Adapter for Understat xG and match data."""

    @property
    def provider_id(self) -> ProviderId:
        return ProviderId("understat")

    @property
    def provider_name(self) -> str:
        return "Understat"

    @property
    def base_url(self) -> str:
        return _BASE_URL

    @property
    def license(self) -> str:
        return "Public access; no formal license published"

    def available_datasets(self) -> list[DatasetDescriptor]:
        return [
            DatasetDescriptor(
                name=_MATCH_RESULTS_DATASET,
                description=(
                    "Season match results with expected goals (xG), win probabilities, "
                    "and final scores per league and season."
                ),
                url_template=f"{_BASE_URL}/league/{{league}}/{{season}}",
                license=self.license,
                default_params={"league": "EPL", "season": "2023"},
            )
        ]

    def build_url(self, dataset_name: DatasetName, **params: str) -> str:
        """Build the Understat league page URL.

        The downloader extracts the embedded JSON from the HTML response.

        Required params:
            league: Understat league code, e.g. ``"EPL"``, ``"La_liga"``.
            season: Four-digit season start year, e.g. ``"2023"``.
        """
        descriptor = self.get_descriptor(dataset_name)
        league = params.get("league", "EPL")
        season = params.get("season", "2023")
        return descriptor.url_template.format(league=league, season=season)

    def parse(self, content: bytes, dataset_name: DatasetName) -> pd.DataFrame:
        """Parse pre-extracted Understat JSON bytes into a DataFrame.

        Understat stores nested team objects under ``h`` (home) and ``a`` (away).
        This method flattens them into top-level columns before returning.

        Args:
            content: JSON bytes — a list of match objects.
            dataset_name: Dataset name (validated against available_datasets).

        Returns:
            Flattened DataFrame with Understat-native column names.
        """
        self.get_descriptor(dataset_name)
        try:
            records: list[dict[str, object]] = json.loads(content)
        except json.JSONDecodeError as exc:
            raise IngestionError(
                dataset_name, f"Failed to parse Understat JSON: {exc}"
            ) from exc

        if not isinstance(records, list):
            raise IngestionError(
                dataset_name,
                "Expected a JSON array of match objects, got "
                f"{type(records).__name__}",
            )

        flat: list[dict[str, object]] = []
        for record in records:
            if not isinstance(record, dict):
                continue
            row: dict[str, object] = {
                k: v for k, v in record.items() if k not in ("h", "a")
            }
            h_val = record.get("h")
            if isinstance(h_val, dict):
                for k, v in h_val.items():
                    row[f"h_{k}"] = v
            a_val = record.get("a")
            if isinstance(a_val, dict):
                for k, v in a_val.items():
                    row[f"a_{k}"] = v
            flat.append(row)

        return pd.DataFrame(flat)

    def normalise_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename Understat columns to platform-standard names."""
        present = {k: v for k, v in _COLUMN_MAP.items() if k in df.columns}
        return df[list(present)].rename(columns=present)
