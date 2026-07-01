# Football Intelligence Platform
# Claude Prompt Book

# Volume 2

---

# Overview

Volume 2 marks the transition from repository setup into real AI Engineering.

The first three stages established the engineering foundations required to build a maintainable AI system.

Beginning with Stage 4, the project starts working with football data.

The emphasis of this volume is not model training.

Instead, the emphasis is on building a reliable, reproducible, and legally compliant data engineering pipeline.

The philosophy followed throughout this volume is:

> Good models begin with good data.

Accordingly, significant effort is invested into ensuring the data pipeline is modular, testable, reproducible, and extensible.

---

# Stage 4

# Data Acquisition Framework

## Stage Objective

Design and implement the data acquisition framework that will power every downstream AI component.

The purpose of this stage is not to create the final training dataset.

Instead, this stage establishes a reusable ingestion framework capable of collecting football information from multiple approved public sources.

The framework should be designed so that adding or removing data providers requires minimal code changes.

---

## Background

Machine learning systems are only as reliable as the data they consume.

Rather than depending on a single provider, the Football Intelligence Platform intentionally adopts a provider abstraction layer.

This architecture enables:

- easier testing
- better fault tolerance
- future extensibility
- provider replacement without affecting downstream pipelines

The ingestion framework therefore becomes a reusable engineering component rather than a collection of scripts.

---

## Guiding Principles

The ingestion framework should satisfy the following principles.

### Provider Independence

Each provider should implement a common interface.

No downstream pipeline should depend on provider-specific implementations.

---

### Reproducibility

Running the same ingestion job with identical parameters should produce identical outputs wherever practical.

---

### Idempotency

Running the same ingestion task multiple times should not create duplicate records.

---

### Traceability

Every dataset should include metadata describing:

- source
- collection date
- ingestion version
- provider
- schema version

---

### Testability

Every provider should be independently unit tested.

Network calls should be mockable.

---

## Approved Public Data Sources

The project intentionally limits itself to publicly available football information.

Examples include:

- FBref
- Understat
- StatsBomb Open Data
- Kaggle football datasets
- FiveThirtyEight historical datasets
- FIFA open datasets where licensing permits

Where APIs require authentication, the implementation should support environment-based configuration.

Hardcoded credentials are prohibited.

---

## Explicitly Excluded Sources

The following should not be scraped or collected:

- private APIs
- copyrighted datasets without permission
- leaked databases
- paid datasets redistributed without license
- restricted social media content

The project must remain legally distributable.

---

## Repository Structure

Recommended layout:

```
ai/

    ingestion/

        providers/

        clients/

        models/

        cache/

        metadata/

        orchestration/

        tests/
```

Each directory should have a clearly defined responsibility.

Avoid large utility modules.

---

## Provider Interface

Every provider should expose a consistent interface.

Example responsibilities include:

- discover available seasons
- discover competitions
- download fixtures
- download player statistics
- download team statistics
- validate responses
- emit normalized records

The remainder of the system should consume normalized domain objects rather than provider-specific payloads.

---

## Caching Strategy

Repeated downloads should be avoided.

The ingestion layer should support optional local caching.

Cache metadata should record:

- provider
- request
- timestamp
- expiration

Caching improves both development speed and provider friendliness.

---

## Error Handling

Failures should be isolated.

A single provider failure should not terminate the entire ingestion pipeline.

Instead:

- log the error
- record provider status
- continue processing remaining providers where appropriate

---

## Configuration

Provider configuration should be externalized.

Examples include:

- API keys
- cache duration
- retry count
- timeout
- concurrency

Configuration should be environment driven rather than hardcoded.

---

## Logging

Every ingestion job should emit structured logs.

Include:

- provider
- dataset
- records processed
- duration
- warnings
- failures

Structured logging simplifies debugging and operational monitoring.

---

## Stage Constraints

During Stage 4 do NOT:

- clean datasets
- engineer features
- train machine learning models
- build prediction APIs
- implement SHAP
- implement Retrieval-Augmented Generation

Only establish the ingestion framework.

---

## Deliverables

At the completion of Stage 4 the repository should include:

- provider abstraction
- provider interfaces
- provider implementations
- caching layer
- configuration management
- logging
- ingestion orchestration
- provider unit tests
- documentation

## Acceptance Criteria

Stage 4 is complete only when all of the following conditions are satisfied.

✓ Provider abstraction implemented

✓ Provider interface documented

✓ At least one provider implementation completed

✓ Configuration system implemented

✓ Local caching supported

✓ Structured logging enabled

✓ Error handling implemented

✓ Unit tests added

✓ Documentation updated

✓ CI passes successfully

The implementation should be capable of supporting additional providers without requiring changes to downstream components.

---

## Testing Strategy

The ingestion framework should include automated tests covering:

- provider interface compliance
- response parsing
- configuration loading
- cache behavior
- retry logic
- timeout handling
- failure scenarios
- metadata generation

External services should be mocked wherever practical.

Unit tests should execute without requiring network connectivity.

---

## Documentation Requirements

Update documentation describing:

- supported providers
- ingestion workflow
- configuration
- local development
- cache management
- adding a new provider
- testing providers

Future contributors should be able to implement an additional provider by following documented conventions.

---

## Expected Commit

```
feat(ai): implement modular data acquisition framework
```

---

## Pull Request Title

```
feat(ai): implement modular data acquisition framework
```

---

## Pull Request Summary

This Pull Request introduces the modular data acquisition framework for the Football Intelligence Platform.

The implementation establishes a provider abstraction layer capable of collecting football information from multiple approved public sources.

The framework includes configuration management, structured logging, caching, provider isolation, unit testing, and documentation.

No feature engineering or model training is performed during this stage.

The objective is to establish a scalable ingestion layer that will support all downstream AI pipelines.

---

# Stage 5

# Canonical Dataset Pipeline

## Stage Objective

Create the canonical dataset pipeline that transforms heterogeneous football datasets into a single standardized representation.

The objective is not to maximize the number of collected datasets.

Instead, the goal is to ensure that every downstream model consumes data with a consistent schema regardless of the original provider.

---

## Background

Different football data providers expose different schemas.

Examples include:

- different player identifiers
- different team identifiers
- different competition names
- different timestamp formats
- different statistical definitions

Without normalization, downstream machine learning pipelines become tightly coupled to individual providers.

The canonical dataset pipeline removes this coupling.

---

## Design Principles

The canonical dataset should satisfy the following principles.

### Provider Agnostic

Models should never know where the data originated.

---

### Deterministic

The same raw data should always produce the same canonical dataset.

---

### Versioned

Canonical schemas should evolve using explicit schema versions.

Breaking changes should never silently overwrite previous datasets.

---

### Auditable

Every transformed record should retain metadata describing its original source.

---

### Extensible

New providers should require minimal transformation code.

---

## Canonical Schema

The canonical schema should define common representations for:

### Fixtures

- fixture identifier
- competition
- season
- date
- home team
- away team
- score
- venue

---

### Teams

- team identifier
- canonical name
- aliases
- country

---

### Players

- player identifier
- canonical name
- nationality
- primary position
- current club

---

### Match Statistics

- possession
- shots
- shots on target
- expected goals
- passes
- tackles
- interceptions
- fouls
- cards
- corners

---

### Metadata

Each record should contain:

- provider
- ingestion timestamp
- schema version
- transformation version
- dataset version

---

## Transformation Pipeline

The canonical transformation should execute in clearly defined stages.

Recommended pipeline:

```
Raw Provider Data

↓

Validation

↓

Normalization

↓

Canonical Mapping

↓

Deduplication

↓

Quality Checks

↓

Canonical Dataset
```

Each stage should be independently testable.

---

## Identifier Resolution

Different providers frequently use different identifiers.

The pipeline should include mapping strategies for:

- clubs
- players
- competitions
- seasons

Identifier mapping should remain isolated from business logic.

---

## Duplicate Detection

Duplicate fixtures and duplicate player records should be detected before the canonical dataset is generated.

Where duplicates cannot be resolved automatically, they should be flagged for manual review.

---

## Quality Validation

The pipeline should validate:

- missing values
- impossible scores
- invalid timestamps
- duplicate identifiers
- inconsistent competitions
- malformed statistics

Invalid records should be reported rather than silently discarded.

---

## Repository Structure

Recommended layout:

```
ai/

    preprocessing/

        validation/

        normalization/

        mapping/

        deduplication/

        quality/

        export/
```

Each module should implement a single responsibility.

## Export Strategy

The canonical dataset should be exportable in standardized formats suitable for downstream processing.

Supported export formats should include:

- Parquet
- CSV
- Feather (optional for experimentation)

Parquet should be considered the default storage format due to its compression efficiency and compatibility with analytical workflows.

---

## Stage Constraints

During Stage 5 do NOT:

- engineer machine learning features
- train prediction models
- calculate SHAP values
- implement Retrieval-Augmented Generation
- expose FastAPI endpoints

The purpose of this stage is to produce a clean, reliable, and reusable canonical dataset.

---

## Acceptance Criteria

Stage 5 is complete only when:

✓ Canonical schema defined

✓ Transformation pipeline implemented

✓ Identifier mapping implemented

✓ Duplicate detection implemented

✓ Quality validation implemented

✓ Dataset versioning supported

✓ Export pipeline completed

✓ Unit tests passing

✓ Documentation updated

✓ CI passing

---

## Testing Strategy

The canonical dataset pipeline should include automated tests covering:

- schema validation
- identifier mapping
- normalization
- duplicate removal
- invalid record detection
- export generation
- metadata preservation

Golden datasets should be introduced wherever practical to ensure deterministic transformations.

---

## Documentation Requirements

Update documentation describing:

- canonical schema
- transformation pipeline
- identifier mapping strategy
- dataset versioning
- export formats
- quality validation
- troubleshooting guide

Future contributors should understand how raw provider data becomes the canonical dataset.

---

## Expected Commit

```
feat(ai): implement canonical dataset pipeline
```

---

## Pull Request Title

```
feat(ai): implement canonical dataset pipeline
```

---

## Pull Request Summary

This Pull Request introduces the canonical dataset pipeline for the Football Intelligence Platform.

The implementation standardizes heterogeneous football datasets into a provider-independent canonical representation.

It includes schema normalization, identifier mapping, duplicate detection, quality validation, export support, automated testing, and documentation.

No feature engineering or machine learning models are introduced during this stage.

The resulting canonical dataset becomes the single source of truth for every downstream AI pipeline.

---

# Stage 6

# Feature Engineering Pipeline

## Stage Objective

Build the feature engineering pipeline that converts canonical football datasets into machine-learning-ready features suitable for predictive modeling.

The emphasis of this stage is not model training.

Instead, the objective is to establish a deterministic, reproducible, and extensible feature generation framework capable of supporting multiple models throughout the project.

---

## Background

Raw football statistics rarely provide optimal predictive performance.

Machine learning models typically perform better when supplied with engineered features that capture recent form, historical trends, contextual information, and domain-specific knowledge.

Accordingly, feature engineering becomes one of the most valuable engineering investments within the project.

The generated features should be reusable across future experiments and model iterations.

---

## Guiding Principles

The feature engineering pipeline should satisfy the following principles.

### Deterministic

The same canonical dataset should always produce identical features.

---

### Modular

Each feature family should exist independently.

New feature groups should be added without modifying existing implementations.

---

### Explainable

Every engineered feature should have a documented business meaning.

Opaque or undocumented transformations should be avoided.

---

### Versioned

Feature definitions should be versioned independently from datasets and models.

This ensures reproducibility across experiments.

---

### Testable

Every feature transformation should have dedicated unit tests.

---

## Feature Categories

The pipeline should support multiple categories of football features.

### Team Form Features

Examples include:

- last 5 matches
- last 10 matches
- rolling win percentage
- rolling goals scored
- rolling goals conceded
- home form
- away form

---

### Player Features

Examples include:

- recent appearances
- recent goals
- recent assists
- expected goals contribution
- expected assists contribution
- minutes played
- disciplinary history

---

### Match Context Features

Examples include:

- home advantage
- competition
- season
- fixture congestion
- travel considerations (where available)
- days of rest

---

### Historical Performance

Examples include:

- head-to-head record
- historical goal difference
- historical expected goals
- historical possession averages

---

### Team Strength Indicators

Examples include:

- ELO rating
- rolling xG differential
- rolling expected points
- defensive efficiency
- attacking efficiency

---

## Feature Pipeline

Recommended execution order:

```
Canonical Dataset

↓

Validation

↓

Rolling Statistics

↓

Historical Aggregation

↓

Derived Metrics

↓

Encoding

↓

Scaling (where required)

↓

Feature Store
```

Each stage should be independently testable and documented.

---

## Feature Store

Generated features should be stored independently from the canonical dataset.

The feature store should:

- preserve feature versions
- preserve dataset versions
- preserve generation metadata
- support reproducibility
- support incremental regeneration

The feature store becomes the primary input for future model training stages.

---

## Feature Metadata

Every generated feature should include metadata describing:

- feature name
- description
- source columns
- transformation applied
- feature version
- generation timestamp

Documenting feature lineage improves explainability and simplifies future maintenance.

