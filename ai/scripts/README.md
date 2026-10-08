# scripts

Standalone shell and Python scripts for setup, pipeline execution, and maintenance tasks.

## Responsibility

One-shot scripts that are run from the command line rather than imported as library code. These are operational tools: environment setup, data pipeline triggers, artefact cleanup.

## Contracts

- Scripts are run with `uv run python -m scripts.<name>`; nothing imports them.
- Each script has a `--help` flag and a usage example at the top.
- Scripts must be idempotent where possible.
- No script downloads data or modifies `datasets/raw/` without user confirmation.

## Contents

- `backfill_football_data.py` — download every season of the five leagues and build the canonical dataset (ADR 005).
- `ingest_football_data.py` — ingest a single football-data.co.uk file.
- `refresh_live_dataset.py` — add the season so far to the served dataset by hand (the backend also does this daily).
- `refresh_fixtures.py` — download upcoming fixtures by hand (ADR 015).
- `build_team_crests.py` — rebuild `datasets/schemas/team_crests.csv`, the crest URL per team (ADR 020).

- `draw_feature_experiment.py` — retrains with six candidate draw features and reports the log-loss change; the features were not adopted (`docs/reports/draw-handling.md`).

- `kaggle_extras_experiment.py` — tests Champions League rest days, rolling xG and FIFA ratings against the served model; none was adopted (`docs/reports/kaggle-extras.md`).
