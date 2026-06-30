# Documentation

This directory contains all project documentation except code-level docstrings.

---

## Ownership

Maintained by the project architect. The implementation engineer updates documentation when architecture or behaviour changes, in the same commit as the change.

---

## Hierarchy

```
docs/
  constitution/   # Immutable project principles and constraints
  adr/            # Architectural Decision Records
  architecture/   # System diagrams and layer descriptions
  ai/             # AI system design: RAG, evaluation, prompt strategy
  backend/        # API contracts, service design, data models
  frontend/       # Screen designs, navigation, ViewModel contracts
  prompts/        # Prompt design notes (templates live in playbook/)
  testing/        # Testing strategy and evaluation framework
  roadmap/        # Stage plans and milestone definitions
  decisions/      # Lightweight decision notes below ADR threshold
```

---

## Rules

- Every document reflects the current state of the system. Outdated documents are updated, not left to drift.
- Documents that define a contract (API spec, data schema) are updated in the same commit as the implementation.
- ADRs are never deleted. Superseded ADRs are marked Deprecated and a new ADR is written.
- No design document should be written in isolation. Every document is associated with a stage or an ADR.
