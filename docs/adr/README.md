# Architectural Decision Records

This directory contains all Architectural Decision Records (ADRs) for the Football Intelligence Platform.

---

## What is an ADR

An ADR documents a significant technical decision: what was decided, why, and what the consequences are. It is written before implementation begins, not after.

---

## When to Write an ADR

An ADR is required before implementing:

- A new ML model or algorithm.
- A new external dependency or service.
- A change to the data schema.
- A change to the API contract.
- A structural change to any layer of the system.
- A technology choice (language, framework, database).

If in doubt, write the ADR. The cost of writing one is low. The cost of undocumented decisions compounds over time.

---

## Naming Convention

```
NNN-short-title.md
```

Examples:
- `001-use-xgboost-for-match-prediction.md`
- `002-use-sqlite-for-local-development.md`
- `003-use-ollama-for-local-llm.md`

Numbers are sequential and never reused.

---

## ADR Format

```markdown
# NNN — Title

**Status:** Proposed | Accepted | Deprecated

**Supersedes:** (ADR number if this replaces a prior decision)
**Superseded by:** (ADR number if this decision has been replaced)

## Context

What problem or situation prompted this decision?
What constraints apply?

## Decision

What was decided?
State it as a single clear sentence, then elaborate if needed.

## Consequences

What becomes easier because of this decision?
What becomes harder?
What must change in the codebase as a result?
```

---

## Lifecycle

- **Proposed:** Written and under discussion.
- **Accepted:** Decision made and recorded. Implementation may begin.
- **Deprecated:** Superseded by a newer ADR. The old ADR remains for historical context.

ADRs are never deleted.

---

## Index

| Number | Title | Status |
|---|---|---|
| [001](001-use-xgboost-for-predictions.md) | Use XGBoost for match outcome prediction | Accepted |
| [002](002-joblib-model-serialization.md) | Use joblib for model serialisation | Accepted |
| [003](003-chronological-train-val-test-split.md) | Use chronological train/validation/test split | Deprecated (see 007) |
| [004](004-shap-for-explainability.md) | Use SHAP TreeExplainer for model explainability | Accepted |
| [005](005-top-five-leagues-multi-source-data.md) | Expand training data to the top five leagues from multiple sources | Accepted |
| [006](006-team-canonicalisation-and-match-dedup.md) | Canonical team names and match deduplication | Accepted |
| [007](007-season-based-split-and-evaluation.md) | Season-based split and evaluation protocol | Accepted |
| [008](008-server-side-match-features.md) | Compute match features on the server | Accepted |
| [009](009-dixon-coles-goals-model.md) | Add a Dixon-Coles goals model for scoreline predictions | Accepted |
| [010](010-compose-resources-for-ui-text.md) | Keep UI text in Compose Multiplatform resources | Accepted |
| [011](011-draw-possible-tag.md) | Flag possible draws without changing the pick | Accepted |
