# AI

Data engineering, machine learning, explainability, and retrieval-augmented generation for the Football Intelligence Platform.

---

## Ownership

AI and data engineering implementation. Follows `.claude/CLAUDE.md` sections 5 and 6.

---

## Responsibilities

This directory owns:

- Raw data ingestion and schema validation.
- Feature engineering for model training.
- XGBoost model training and serialisation.
- SHAP explainability — every prediction includes a SHAP explanation.
- Retrieval-augmented generation pipeline using Ollama.
- The Dixon-Coles goals model behind scoreline insights and league table projections.
- The FastAPI backend (`backend/`), which serves all of the above.
- Prompt templates and retrieval configuration.
- Evaluation scripts for the match and goals models: season-split comparisons,
  bookmaker benchmarks and in-season backtests. For the assistant: a grounding
  check that it quotes the API's predictions without inventing numbers, a season
  check for table, projection, result and derby answers, and an abstention check
  that it says "I don't know" when it should.

---

## Directory Structure

```
ai/
  config/               # Settings (pydantic-settings) and path layout
  shared/               # Common types, exceptions, and constants
    telemetry/          # Request IDs, JSON log lines and the event catalogue (ADR 024)
  providers/            # Data provider adapters (football-data.co.uk used; FBref, Understat adapters)
  ingestion/            # Downloader, storage, season backfill, daily live refresh, fixtures (openfootball)
  validation/           # DataFrame-level rules and schema compatibility checks
  preprocessing/        # Cleans validated data into datasets/processed/
  feature_engineering/  # Computes model-ready features from preprocessed data
  schemas/              # Pydantic schema definitions for all datasets
  metadata/             # DatasetMetadata model and MetadataBuilder
  scripts/              # Operational CLI scripts (setup, pipeline triggers)
  tests/                # Unit and integration tests mirroring source structure
  training/             # XGBoost training, season split, tuning
  evaluation/           # Model evaluation, backtests and in-season accuracy
  inference/            # Predictor and server-side match features used by the backend
  explainability/       # SHAP explainability pipeline and fan-friendly feature labels
  goals/                # Dixon-Coles goals model: likely scores, goal markets, league table projections
  model_registry/       # JSON model registry with git commit traceability
  assistant/            # RAG assistant: ingestion, chunking, embeddings, retrieval, generation
  backend/              # FastAPI application (see backend/README.md at the repo root)
  docs/                 # Stage 8 and 10 demo guides and reports
  rag/, prompts/, datasets/  # Empty; the RAG code lives in assistant/, prompts in assistant/prompting/templates.py
  models/               # Serialised model artefacts (gitignored)
```

---

## Provider Architecture

The ingestion pipeline is built around a provider abstraction:

```
DatasetDownloader
  │
  ├─ provider.get_descriptor(dataset_name)   → DatasetDescriptor
  ├─ provider.build_url(dataset_name)        → str (download URL)
  ├─ transport.get(url)                      → bytes (raw content)
  ├─ provider.parse(content, dataset_name)   → DataFrame (native columns)
  ├─ provider.normalise_columns(df)          → DataFrame (platform columns)
  ├─ MetadataBuilder.build(...)              → DatasetMetadata
  ├─ DatasetStorage.save_raw(...)            → Path
  ├─ DatasetStorage.save_dataframe(...)      → Path
  └─ DatasetStorage.save_metadata(...)       → Path
```

The HTTP transport (`HttpTransport` protocol) is injected, so tests use a `FakeTransport` without network access.

**Supported providers:**

| Provider | ID | Datasets | Format |
|---|---|---|---|
| football-data.co.uk | `football_data` | `match_results` (used for all training and serving data) | CSV |
| FBref | `fbref` | `scores_and_fixtures`, `squad_standard_stats` | CSV |
| Understat | `understat` | `match_results` | JSON |

Upcoming fixtures come from openfootball's season schedules through
`ingestion/fixtures.py` rather than a provider class (ADR 015).

---

## Validation Architecture

```
DatasetValidator            — orchestrates rules against a DataFrame
  ├─ RequiredColumnsRule    — fails if any required column is absent
  ├─ NullConstraintRule     — fails if non-nullable columns contain nulls
  ├─ DuplicateRowRule       — fails if duplicate ratio exceeds threshold
  └─ RowCountRule           — fails if row count is below minimum

SchemaValidator             — validates column compatibility with a Pydantic schema
  ├─ validate()             — warns on extra columns, errors on missing required ones
  └─ validate_strict()      — extra columns are errors, not warnings
```

---

## Metadata Lifecycle

Every ingested dataset produces a `DatasetMetadata` record:

| Field | Description |
|---|---|
| `provider_id` | Provider that supplied the data |
| `dataset_name` | Dataset name as declared by the provider |
| `source_url` | Exact URL the content was fetched from |
| `downloaded_at` | UTC timestamp of the download |
| `checksum` | SHA-256 hex digest of raw bytes |
| `schema_version` | Data contract version at time of ingest |
| `dataset_version` | Timestamp-derived sortable version string |
| `license` | Data license from the provider |
| `row_count` | Rows in the normalised DataFrame |
| `column_count` | Columns in the normalised DataFrame |
| `columns` | Ordered list of column names |

Metadata is stored as a JSON sidecar alongside the raw file:
`datasets/raw/{provider_id}/{dataset_name}_v{version}_metadata.json`

---

## Getting Started

Requires Python 3.12. Managed with [uv](https://github.com/astral-sh/uv).

```sh
cd ai

# Install all dependencies (including dev tools)
uv sync --extra dev

# Run linting
uv run ruff check .

# Check formatting
uv run black --check .

# Run type checking
uv run mypy .

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov --cov-report=term-missing
```

---

## AI Philosophy

- The assistant never invents facts. Every response is grounded in retrieved data or model output.
- SHAP values accompany every prediction.
- Prompt templates are version-controlled and tested.
- Model selection favours the smallest Ollama model that meets quality thresholds.
- Fine-tuning and LoRA are out of scope. Improve quality through better retrieval and better prompts.
- No model is merged without a passing evaluation run.

---

## Feature Engineering Pipeline

The feature engineering pipeline transforms a canonical `ProcessedMatch` CSV into a model-ready feature matrix.

```sh
# Run with auto-detected latest canonical dataset
uv run python -m feature_engineering.pipeline

# Run with an explicit input file
uv run python -m feature_engineering.pipeline --input ../datasets/processed/football_data/match_results_top5_v<version>.csv --output-dir ../datasets/features/top5
```

**Output artefacts** written to the output directory:

| File | Contents |
|---|---|
| `feature_matrix.parquet` | Full feature matrix (canonical columns + 42 engineered features) |
| `feature_metadata.json` | Feature versions, row/column counts, pipeline version |
| `feature_generation_report.json` | Per-feature timing, validation results, dataset statistics |

**Feature modules** (9 total, executed in dependency order):

| Feature | Output Columns | Method |
|---|---|---|
| `rolling_form` | 8 | Rolling win/point counts over last 5 and 10 matches |
| `goal_statistics` | 12 | Rolling mean goals scored/conceded/diff |
| `home_advantage` | 2 | Expanding home win % and points-per-game |
| `away_form` | 2 | Expanding away win % and points-per-game |
| `rest_days` | 2 | Days since each team's prior match |
| `head_to_head` | 4 | Historical meetings, wins, draws between the two teams |
| `league_position` | 6 | Position, points, and matches played at kick-off |
| `elo_rating` | 2 | Dynamic Elo ratings (K=32, start=1500) recorded before each match |
| `strength_of_schedule` | 4 | Rolling average opponent Elo (requires `elo_rating`) |

All rolling features use `.shift(1)` before `.rolling()` to prevent data leakage.

---

## Assistant Package

The `assistant/` package implements the RAG pipeline for the Football Intelligence
Assistant. Besides retrieved documents, the chat model can call tools that run the
backend's prediction, SHAP and fixtures services, so it quotes the served model's
numbers (ADR 018; the tools are built in `backend/app/services/assistant_tools.py`).
Season questions (tables, projections, results, derbies) use two more tools,
`team_matches` and `league_table`, and a rule-based router picks the tool calls
before the model answers (ADR 021; `backend/app/services/season_tools.py` and
`season_router.py`). It is structured as a series of composable stages:

```
assistant/
  ingestion/      # DocumentLoader — loads .md and .json knowledge files
  chunking/       # TextChunker — splits documents into overlapping chunks
  embeddings/     # Embedder protocol + OllamaEmbedder
  retrieval/      # VectorStore (numpy, file-persisted) + cosine retrieve()
  prompting/      # System prompt + build_messages()
  generation/     # Generator protocols + OllamaGenerator (plain and tool-calling chat)
  tools/          # Tool definition, run_tool() and the Router protocol (routing.py)
  services/       # AssistantService — retrieve, prompt, run tool calls, answer
  pipeline.py     # AssistantPipeline facade: build_index / load_index / query
  configuration.py  # AssistantSettings (pydantic-settings)
```

### Building the index

```sh
ollama pull nomic-embed-text
ollama pull qwen2.5:7b-instruct
uv run python -m assistant.pipeline --rebuild
```

The default chat model is `qwen2.5:7b-instruct` (ADR 019); set
`OLLAMA_CHAT_MODEL` to use another.

### Knowledge sources loaded

- `ai/models/**/*.md` — model cards
- `docs/adr/*.md` — architecture decision records
- `docs/reports/*.md` — stage summaries and evaluation reports
- `docs/*.md` — project documentation
- `ai/models/latest/evaluation_report.json`, `metrics.json`, `config.json` — served model evaluation and settings
- `ai/explanations/global_summary.json` — SHAP global explanations
- `datasets/features/feature_metadata.json`, `feature_generation_report.json` — feature descriptions
