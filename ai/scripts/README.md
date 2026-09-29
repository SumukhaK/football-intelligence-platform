# scripts

Standalone shell and Python scripts for setup, pipeline execution, and maintenance tasks.

## Responsibility

One-shot scripts that are run from the command line rather than imported as library code. These are operational tools: environment setup, data pipeline triggers, artefact cleanup.

## Contracts

- Scripts are not imported as modules. They have no `__init__.py`.
- Each script has a `--help` flag and a usage example at the top.
- Scripts must be idempotent where possible.
- No script downloads data or modifies `datasets/raw/` without user confirmation.

## Contents

- `draw_feature_experiment.py` — retrains with six candidate draw features and reports the log-loss change; the features were not adopted (`docs/reports/draw-handling.md`).

- `kaggle_extras_experiment.py` — tests Champions League rest days, rolling xG and FIFA ratings against the served model; none was adopted (`docs/reports/kaggle-extras.md`).

## Future Contents

- `setup_env.sh` — installs Python dependencies and configures pre-commit hooks.
- `run_pipeline.py` — triggers a full ingestion → validation → preprocessing run.
- `export_schema.py` — regenerates JSON Schema files from Pydantic models.
