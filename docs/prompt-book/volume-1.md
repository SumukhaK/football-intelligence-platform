# Football Intelligence Platform
## Claude Prompt Book

**Version:** 1.0.0

**Author:** Sumukha

**Project:** Football Intelligence Platform

---

# Copyright

This document preserves the engineering prompts used during the design and implementation of the Football Intelligence Platform.

The intent of this book is not to document the source code itself, but to preserve the engineering decisions, implementation workflow, and project execution strategy that guided the development of the platform.

These prompts represent the canonical implementation process used to build the project from an idea into a complete AI Engineering portfolio application.

---

# Purpose of this Book

Modern software engineering increasingly relies on AI-assisted development.

Writing effective prompts is now an engineering skill.

This Prompt Book captures the prompts used to build the Football Intelligence Platform from the first repository commit through the final production release.

Unlike traditional documentation, this book records:

- implementation intent
- engineering constraints
- architecture decisions
- delivery strategy
- repository evolution
- release management
- documentation workflow

The objective is to make future maintenance, onboarding, and extension of the project significantly easier while also serving as a reusable template for future AI engineering projects.

---

# Intended Audience

This document is written for:

- the project author
- future maintainers
- recruiters
- hiring managers
- AI Engineers
- Android Engineers
- Backend Engineers
- Software Architects
- students learning AI Engineering workflows

---

# Engineering Philosophy

The Football Intelligence Platform was intentionally designed as an AI Engineering project rather than a traditional software engineering project.

The primary objective was never to build the largest football application.

Instead, the goal was to demonstrate an end-to-end AI Engineering workflow.

Every engineering decision was therefore evaluated against one question:

> "Does this improve the AI Engineering story of the project?"

If the answer was no, the feature was intentionally excluded.

This resulted in several important design decisions.

## Simplicity over complexity

Wherever possible, technologies that increased operational complexity without significantly improving the AI Engineering story were removed.

Examples include:

- Kubernetes
- Kafka
- distributed microservices
- cloud-specific infrastructure
- complex deployment pipelines

The resulting architecture is intentionally lightweight while remaining modular and production quality.

---

## AI First

The project emphasizes:

- data acquisition
- feature engineering
- machine learning
- explainability
- retrieval-augmented generation
- evaluation
- reproducibility

rather than infrastructure engineering.

---

## Android First

The application targets Android first.

Compose Multiplatform was selected to allow future expansion while keeping Android as the primary platform.

No Flutter code exists within the project.

---

## Test First

Where practical:

- unit tests are written before implementation
- implementation satisfies tests
- refactoring follows after passing tests

This philosophy keeps the repository maintainable while encouraging small, reviewable Pull Requests.

---

## Human Reviewable Code

AI-generated code should never be merged blindly.

Every implementation prompt requested:

- small commits
- reviewable code
- modular implementation
- meaningful commit messages
- Pull Requests instead of direct pushes

---

# Repository Workflow

The repository follows a simplified GitFlow strategy.

```
feature/*
        ↓

Pull Request

        ↓

develop

        ↓

Release

        ↓

main
```

The repository intentionally maintains:

- feature branches
- Pull Requests
- conventional commits
- semantic versioning
- GitHub Releases

rather than direct development on the default branch.

---

# Development Rules

Throughout every implementation stage the following rules were enforced.

## Rule 1

Never push directly to develop.

Every implementation must originate from a feature branch.

---

## Rule 2

Every implementation must open a Pull Request.

---

## Rule 3

Every Pull Request must include

- Summary
- Test Plan
- Verification
- Risks (if applicable)

---

## Rule 4

Commits must follow Conventional Commits.

Examples:

```
feat(ai): add feature engineering pipeline

fix(api): validate prediction payload

docs(showcase): improve repository documentation

test(android): add ViewModel tests
```

---

## Rule 5

Every implementation must remain modular.

Large Pull Requests should be avoided.

---

## Rule 6

Application code should always be easier for humans to review than for AI to generate.

Readable software is maintainable software.

---

# Definition of Done

A stage is considered complete only when all of the following are satisfied.

- implementation completed
- tests passing
- documentation updated
- README updated where required
- CI passing
- Pull Request created
- review completed
- merged into develop

Reaching "working code" is not sufficient.

Documentation and maintainability are considered first-class deliverables.

---

# Prompt Structure

Every implementation prompt within this book follows a consistent structure.

Each stage contains:

1. Objective

2. Background

3. Architecture Context

4. Constraints

5. Expected Deliverables

6. Repository Rules

7. Testing Requirements

8. Commit Convention

9. Pull Request Requirements

10. Completion Criteria

This consistency made long-running AI-assisted development significantly easier.

---

# Stage 1

# Repository Foundation

## Stage Objective

Create a clean, scalable repository foundation that will support every subsequent stage of the Football Intelligence Platform.

The purpose of this stage is not to implement business features.

Instead, this stage establishes the engineering standards that every later contribution must follow.

The repository should immediately communicate professionalism through its structure, tooling, documentation, and workflow.

The expected outcome is a repository that is ready for AI, Android, Backend, and documentation development without requiring structural changes later in the project.

---

## Background

The Football Intelligence Platform is intended to showcase AI Engineering skills rather than frontend or backend complexity.

From the very beginning, the repository should reflect the qualities of a production-quality engineering project:

- clear separation of concerns
- modular directory structure
- documentation-first mindset
- repeatable developer workflows
- scalable architecture
- review-friendly contribution model

Every subsequent stage assumes this foundation already exists.

---

## High-Level Goals

During Stage 1, implement only repository foundations.

Do **not** implement business logic.

Do **not** implement machine learning pipelines.

Do **not** implement Android UI.

Do **not** implement backend APIs.

Focus exclusively on establishing a clean engineering baseline that future stages can build upon.

---

## Deliverables

At the conclusion of Stage 1, the repository should include:

- standardized directory structure
- root README
- CONTRIBUTING guide
- CHANGELOG
- LICENSE
- .gitignore
- GitHub issue templates
- Pull Request template
- CODEOWNERS (optional for solo projects)
- Architecture Decision Record (ADR) directory
- documentation structure
- conventional commit guidance
- repository health checks

## Repository Structure

The repository should adopt a modular layout from the first commit.

The objective is to avoid large-scale restructuring later in the project.

The initial directory structure should resemble:

```
football-intelligence-platform/

├── android/
├── backend/
├── ai/
├── docs/
│   ├── adr/
│   ├── architecture/
│   ├── setup/
│   ├── api/
│   ├── reports/
│   └── releases/
│
├── .github/
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
│
├── scripts/
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
└── .gitignore
```

The structure should intentionally separate responsibilities rather than mixing frontend, backend and AI implementation together.

---

## Documentation Requirements

Repository documentation should exist before implementation begins.

Create documentation for:

- Project overview
- Local setup
- Repository workflow
- Branching strategy
- Commit conventions
- Pull Request process
- Release strategy
- Architecture Decision Records (ADR)
- Future documentation placeholders

Documentation should evolve with the project rather than being written only after implementation.

---

## Git Workflow

The repository follows a simplified GitFlow workflow.

Development should always occur on feature branches.

Feature branches are merged into `develop` through Pull Requests.

Stable releases are promoted from `develop` to `main`.

No feature work should be committed directly to `main`.

Example:

```
feature/repository-foundation
        ↓
Pull Request
        ↓
develop
        ↓
release/v1.0.0
        ↓
main
```

This approach keeps repository history clean and reviewable.

---

## Commit Convention

All commits must follow Conventional Commits.

Examples include:

```
feat(android): add prediction screen

feat(ai): create feature engineering pipeline

fix(api): validate request schema

test(ai): add preprocessing tests

docs(readme): improve quick start guide

chore(ci): configure GitHub Actions
```

Commit messages should be descriptive enough that the project history can be understood without opening the code.

---

## Pull Request Standards

Every Pull Request should include:

### Summary

Explain the purpose of the change.

### Motivation

Why was this change required?

### Implementation

Describe what was added or modified.

### Testing

List all verification steps performed.

### Risks

Document any known risks or limitations.

### Screenshots

Include screenshots where UI changes exist.

### Checklist

- Tests passing
- Documentation updated
- CI passing
- Ready for review

---

## Continuous Integration

Although application code does not yet exist, the repository should already prepare for CI.

Future stages will introduce workflows for:

- Android build verification
- Python linting
- Static analysis
- Unit testing
- Formatting
- Pull Request validation

Stage 1 should establish the directory structure that allows these workflows to be added without restructuring.

---

## Architecture Decision Records

Architecture decisions should be documented as ADRs.

The ADR directory should be created during Stage 1 even if only placeholder documents exist.

Typical ADRs include:

- Why Compose Multiplatform?
- Why FastAPI?
- Why XGBoost?
- Why SHAP?
- Why Ollama?
- Why local-first AI?

Recording these decisions ensures future contributors understand *why* technologies were selected.

---

## README Expectations

The initial README should communicate:

- What the project is
- Why it exists
- Planned architecture
- Repository structure
- Technology stack
- Planned AI workflow
- Planned Android application
- Planned backend
- Contribution workflow
- License

The README is expected to evolve throughout the project.

---

## Stage Constraints

During Stage 1:

Do NOT:

- build Android screens
- implement FastAPI endpoints
- create machine learning models
- collect football datasets
- write prediction logic
- integrate LLMs

Focus exclusively on repository quality.

---

## Acceptance Criteria

Stage 1 is complete only when:

✓ Repository structure created

✓ Documentation initialized

✓ GitHub templates added

✓ Conventional commit strategy documented

✓ Branch strategy documented

✓ ADR structure created

✓ Root README completed

✓ Repository ready for Stage 2

---

## Expected Commit

```
chore(repo): initialize repository foundation
```

---

## Pull Request Title

```
chore(repo): initialize repository foundation
```

---

## Pull Request Summary

This Pull Request establishes the foundational engineering structure for the Football Intelligence Platform.

It introduces the repository layout, documentation framework, contribution guidelines, and project conventions that all subsequent implementation stages will follow.

No application functionality is included in this stage.

The objective is to create a scalable, maintainable repository that supports Android, Backend, AI, and documentation development from a common engineering baseline.

---

# Stage 2

# Compose Multiplatform Foundation

## Stage Objective

Establish the Android-first application foundation using Compose Multiplatform.

This stage intentionally replaces every previous reference to Flutter.

The application should be designed as an Android-first product while preserving the option to expand to additional platforms in the future through Compose Multiplatform.

The emphasis of this stage is project structure, architecture, navigation, dependency injection, testing strategy, and maintainability—not feature completeness.

---

## Background

The Football Intelligence Platform is primarily an AI Engineering showcase. The mobile application exists to provide an intuitive interface for interacting with the prediction engine and the Football Intelligence Assistant.

Frontend complexity should therefore remain proportional to the goals of the project.

Compose Multiplatform offers modern Kotlin-based UI development, excellent Android support, and the possibility of future desktop or iOS expansion without introducing unnecessary architectural complexity.

---

## High-Level Goals

During Stage 2:

- Initialize the Compose Multiplatform project.
- Configure Gradle modules.
- Establish Clean Architecture layers.
- Configure dependency injection.
- Configure navigation.
- Configure Material 3.
- Configure ViewModel architecture.
- Add baseline unit testing support.
- Create placeholder screens for future features.

No backend communication or AI functionality should be implemented during this stage.

---

## Deliverables

At the conclusion of Stage 2, the Android project should include:

- Compose Multiplatform configuration
- Android target configured
- Modular project structure
- Navigation graph
- Dependency Injection setup
- Design system foundation
- Theme configuration
- ViewModel base classes
- Testing infrastructure
- Placeholder UI screens

## Android Architecture

The Android application should adopt Clean Architecture from the beginning.

Separate responsibilities into clearly defined layers.

Recommended modules:

```
android/

    app/

    core/

        designsystem/

        common/

        network/

        navigation/

        testing/

    feature/

        home/

        prediction/

        assistant/

        explainability/

        settings/

    domain/

    data/
```

The application should avoid tightly coupling UI with networking or business logic.

The architecture should encourage independent feature development and isolated testing.

---

## Design Principles

The frontend should prioritize:

- readability
- maintainability
- modularity
- testability

The application is not intended to showcase advanced UI animations or visual effects.

Instead, it should demonstrate professional Android engineering practices.

---

## Navigation

Configure Navigation Compose.

Define placeholder destinations for:

- Home
- Prediction
- Prediction Details
- Explainability
- Football Assistant
- Model Information
- Settings

Navigation should be centralized rather than scattered across feature modules.

---

## Dependency Injection

Configure dependency injection using Hilt.

Separate modules for:

- Network
- Repository
- ViewModels
- AI Services
- Configuration

Avoid creating large dependency graphs.

---

## UI Design System

Create a reusable design system.

Include:

- Typography
- Color palette
- Shapes
- Spacing
- Icons
- Reusable buttons
- Cards
- Loading components
- Error components

All future screens should consume components from the design system rather than implementing their own UI primitives.

---

## State Management

Adopt unidirectional data flow.

Recommended pattern:

```
UI

↓

ViewModel

↓

Use Case

↓

Repository

↓

Data Source
```

UI components should remain stateless wherever practical.

Business logic belongs outside composables.

---

## Testing Philosophy

Testing is a first-class requirement.

Every feature introduced in later stages should begin with unit tests where practical.

Testing infrastructure established during Stage 2 should support:

- ViewModel tests
- Repository tests
- Navigation tests
- Use Case tests
- UI tests (future)

---

## Stage Constraints

During Stage 2 do NOT:

- connect to FastAPI
- implement AI predictions
- integrate Ollama
- perform authentication
- create football datasets
- implement business logic

Focus only on Android project architecture.

---

## Acceptance Criteria

Stage 2 is complete only when:

✓ Compose Multiplatform project created

✓ Android application builds successfully

✓ Clean Architecture established

✓ Dependency Injection configured

✓ Navigation configured

✓ Material 3 configured

✓ Testing infrastructure added

✓ Placeholder screens created

✓ Documentation updated

---

## Expected Commit

```
feat(android): initialize compose multiplatform foundation
```

---

## Pull Request Title

```
feat(android): initialize compose multiplatform foundation
```

---

## Pull Request Summary

This Pull Request establishes the Android application foundation for the Football Intelligence Platform.

The project adopts Compose Multiplatform with Android as the primary platform.

It introduces modular project structure, dependency injection, navigation, Material 3, design system foundations, and testing infrastructure.

No backend communication or AI functionality is included.

The application is now ready for feature implementation in subsequent stages.

---

# Stage 3

# AI Workspace Bootstrap

## Stage Objective

Create the AI Engineering workspace that will support the complete machine learning lifecycle.

Unlike Stage 2, which focused on Android engineering, this stage establishes the Python development environment responsible for data acquisition, preprocessing, feature engineering, model training, evaluation, explainability, and Retrieval-Augmented Generation.

The objective is to build a maintainable AI workspace rather than immediately implementing machine learning models.

---

## Background

The Football Intelligence Platform showcases AI Engineering rather than pure machine learning research.

Accordingly, the AI workspace must support reproducibility, experimentation, testing, and long-term maintainability.

Every subsequent AI stage assumes that this workspace already exists.

The workspace should be lightweight enough to run locally while remaining compatible with free cloud execution environments when needed.

---

## High-Level Goals

During Stage 3:

- Initialize a standalone Python project.
- Manage dependencies using `uv`.
- Configure Ruff, Black, MyPy, and Pytest.
- Create the package structure for AI modules.
- Configure pre-commit hooks.
- Add GitHub Actions for AI quality checks.
- Establish testing conventions.
- Document development workflows.

No datasets should be collected yet.

No models should be trained yet.

---

## AI Workspace Structure

The AI project should follow a modular layout.

```
ai/

    ingestion/

    validation/

    preprocessing/

    feature_engineering/

    models/

    explainability/

    rag/

    evaluation/

    experiments/

    schemas/

    scripts/

    tests/
```

Each package should expose a clearly defined responsibility.

Avoid monolithic utility modules.

---

## Tooling

The AI workspace should standardize on:

- Python 3.12
- uv
- Ruff
- Black
- MyPy
- Pytest
- pre-commit

These tools establish code quality from the beginning of the project.

---

## Continuous Integration

Configure a dedicated GitHub Actions workflow for the AI workspace.

The workflow should:

- install dependencies
- run Ruff
- run Black (check mode)
- run MyPy
- run Pytest

Only the AI workspace should be evaluated by this workflow.

Android CI is handled independently.

---

## Testing Strategy

Every AI module should be independently testable.

Bootstrap tests should verify:

- package imports
- project structure
- configuration
- tooling
- development environment

Feature-specific tests will be added in later stages.

---

## Documentation

Each AI package should contain a short README describing:

- purpose
- responsibilities
- expected inputs
- expected outputs
- future implementation plans

These READMEs serve as contracts for future development.

## Repository Standards

The AI workspace should remain independent from the Android and Backend applications.

It should be possible to:

- develop AI components independently
- execute model training independently
- run evaluation independently
- regenerate datasets independently

The repository intentionally separates AI engineering from application engineering.

This separation reduces coupling and improves maintainability.

---

## Development Philosophy

The AI workspace should prioritize reproducibility.

Every pipeline introduced in future stages should satisfy the following principles:

- deterministic execution where practical
- reproducible experiments
- versioned datasets
- versioned models
- documented preprocessing
- documented feature engineering
- automated evaluation

Machine learning should never depend on undocumented manual steps.

---

## Coding Standards

The Python codebase should adopt the following standards.

### Style

Black formatting.

### Linting

Ruff.

### Static Typing

MyPy.

### Testing

Pytest.

### Dependency Management

uv.

### Imports

Absolute imports wherever practical.

Avoid wildcard imports.

Avoid circular dependencies.

---

## Package Responsibilities

Each package should have a single responsibility.

### ingestion

Responsible for acquiring football datasets from approved public sources.

---

### validation

Responsible for schema validation and data quality checks.

---

### preprocessing

Responsible for data cleaning and normalization.

---

### feature_engineering

Responsible for transforming raw football data into model features.

---

### models

Responsible for model definitions and training.

---

### explainability

Responsible for SHAP analysis and prediction explanations.

---

### rag

Responsible for Retrieval-Augmented Generation pipelines.

---

### evaluation

Responsible for model metrics and benchmarking.

---

### experiments

Responsible for experiment tracking.

---

### schemas

Responsible for Pydantic models and validation schemas.

---

### scripts

Utility scripts for running common development tasks.

---

### tests

Unit tests and integration tests for the AI workspace.

---

## Stage Constraints

During Stage 3 do NOT:

- download football datasets
- train XGBoost models
- implement SHAP
- implement Retrieval-Augmented Generation
- connect Ollama
- create FastAPI endpoints

This stage establishes the engineering workspace only.

---

## Acceptance Criteria

Stage 3 is complete only when:

✓ AI workspace initialized

✓ uv configured

✓ Ruff configured

✓ Black configured

✓ MyPy configured

✓ Pytest configured

✓ pre-commit configured

✓ GitHub Actions workflow created

✓ Package structure created

✓ Package documentation added

✓ Bootstrap tests passing

✓ Root documentation updated

---

## Expected Commit

```
chore(ai): bootstrap data engineering workspace
```

---

## Pull Request Title

```
chore(ai): bootstrap data engineering workspace
```

---

## Pull Request Summary

This Pull Request establishes the AI Engineering workspace for the Football Intelligence Platform.

It introduces a standalone Python project using uv together with Ruff, Black, MyPy, Pytest, pre-commit, and GitHub Actions.

The workspace defines the package structure that will support data acquisition, preprocessing, feature engineering, model training, explainability, Retrieval-Augmented Generation, evaluation, and experimentation throughout the remainder of the project.

No football datasets are collected and no machine learning models are implemented during this stage.

The purpose of this Pull Request is to create a reproducible, maintainable, and scalable AI engineering foundation.

---

# Volume 1 Summary

Volume 1 established the engineering foundation of the Football Intelligence Platform.

It documented the philosophy, conventions, and canonical implementation prompts that guided the first three stages of development.

The three stages covered in this volume are:

1. Repository Foundation

   Establishes repository structure, documentation standards, Git workflow, branching strategy, contribution guidelines, Architecture Decision Records, and project conventions.

2. Compose Multiplatform Foundation

   Establishes the Android-first application architecture using Compose Multiplatform, Material 3, Clean Architecture, dependency injection, navigation, testing infrastructure, and reusable UI foundations.

3. AI Workspace Bootstrap

   Establishes the standalone AI Engineering workspace using Python, uv, Ruff, Black, MyPy, Pytest, GitHub Actions, and a modular package structure to support the complete machine learning lifecycle.

These three stages intentionally contain no business functionality.

Instead, they create the engineering platform upon which the remainder of the Football Intelligence Platform is built.

---

# End of Volume 1

The next volume continues with:

- Stage 4 — Data Acquisition Framework
- Stage 5 — Canonical Dataset Pipeline
- Stage 6 — Feature Engineering Pipeline
