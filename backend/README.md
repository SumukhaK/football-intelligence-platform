# Backend

FastAPI monolith exposing predictions, AI assistant responses, and football data through a documented REST API.

---

## Ownership

Backend implementation. Follows the standards defined in `.claude/CLAUDE.md` section 8.

---

## Architecture

Clean Architecture with domain-driven organisation.

- **Domain layer:** Entities and business rules. No framework dependencies.
- **Application layer:** Use cases and service interfaces.
- **Infrastructure layer:** Database access, external APIs, ML model integration.
- **Presentation layer:** FastAPI routers. Routes are thin — no logic lives here.

---

## Directory Structure (planned)

```
backend/
  domain/           # Entities, value objects, domain events
  application/      # Use cases, service interfaces, DTOs
  infrastructure/   # SQLAlchemy queries, file I/O, ML model client
  routers/          # FastAPI route handlers — one file per domain area
  services/         # Business logic implementations
  config.py         # pydantic-settings configuration
  main.py           # FastAPI application factory
  tests/
    unit/
    integration/
```

---

## Development Standards

- One router per domain area. Routers contain no business logic.
- Service classes contain all business logic. Services are injected via `Depends`.
- All request and response bodies are Pydantic models with field-level validation.
- Database access via SQLAlchemy Core. No ORM magic, no lazy-loading.
- Errors return structured JSON: `{ "error": "...", "detail": "..." }`.
- All endpoints have OpenAPI docstrings. The auto-generated docs must be accurate.
- Environment config via `pydantic-settings`. No `os.environ` scattered in code.
- SQLite for local development. Schema must be PostgreSQL-compatible from day one.

---

## Future Responsibilities

- Match outcome prediction endpoint (delegates to AI layer).
- SHAP explanation endpoint.
- Football intelligence assistant endpoint (RAG via AI layer).
- Match, player, and competition data endpoints.
- Pipeline trigger endpoints (background tasks).
