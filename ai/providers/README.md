# providers

Data provider adapters for football data sources.

## Responsibility

Each provider implements `BaseProvider` and acts as an adapter between a specific
data source and the platform's uniform ingestion pipeline. Providers know how to:

1. Declare which datasets they supply (`available_datasets`).
2. Build download URLs (`build_url`).
3. Parse raw bytes into a DataFrame (`parse`).
4. Rename provider-native columns to platform-standard names (`normalise_columns`).

Providers do NOT perform HTTP requests directly. Transport is handled by
`DatasetDownloader` so providers remain testable without a network.

## Supported Providers

| Provider | ID | Source | Datasets |
|---|---|---|---|
| football-data.co.uk | `football_data` | CSV files | `match_results` |
| FBref | `fbref` | CSV exports | `scores_and_fixtures`, `squad_standard_stats` |
| Understat | `understat` | Embedded JSON | `match_results` |

## Adding a New Provider

1. Create `providers/{provider_name}.py`.
2. Subclass `BaseProvider` and implement all abstract methods.
3. Add the provider to `providers/__init__.py` exports.
4. Add tests in `tests/providers/test_{provider_name}.py`.
5. Write an ADR if the provider introduces a new data format or dependency.

## Column Naming Convention

Platform-standard column names use lowercase snake_case:

| Concept | Platform Name |
|---|---|
| Match date | `date` |
| Home team | `home_team` |
| Away team | `away_team` |
| Full-time home goals | `home_goals_ft` |
| Full-time away goals | `away_goals_ft` |
| Full-time result (H/D/A) | `result_ft` |
| Home expected goals | `home_xg` |
| Away expected goals | `away_xg` |
| Home shots | `home_shots` |
| Home shots on target | `home_shots_on_target` |
