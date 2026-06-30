# Tools

Shared CLI utilities for the Football Intelligence Platform.

---

## Ownership

Shared. Tools are reviewed before merge and must meet the same coding standards as application code.

---

## Purpose

Tools are reusable command-line utilities that multiple parts of the project depend on. Unlike scripts, tools are designed to be called repeatedly in different contexts.

Examples:
- Dataset schema validator CLI.
- Model evaluation runner.
- Prompt template tester.
- API smoke test runner.

---

## Rules

- Every tool is a standalone executable with a `--help` flag.
- Tools are typed (Python type annotations) and tested.
- Tools do not import from `backend/` or `ai/` application code. If shared logic is needed, extract it to a shared library.
- Tools read configuration from environment variables or explicit arguments. No hardcoded paths.

---

## Future Responsibilities

- Schema validation CLI: validate a dataset file against its schema definition.
- Evaluation CLI: run the full evaluation suite and print a summary report.
- Prompt test CLI: run a prompt template against a test case and display the output.
