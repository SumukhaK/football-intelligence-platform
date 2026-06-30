"""Tests for OpenAPI schema generation."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_openapi_schema_accessible(client: TestClient) -> None:
    """GET /openapi.json returns 200."""
    response = client.get("/openapi.json")
    assert response.status_code == 200


def test_openapi_schema_has_paths(client: TestClient) -> None:
    """OpenAPI schema lists all expected endpoint paths."""
    schema = client.get("/openapi.json").json()
    paths = schema.get("paths", {})
    for expected in ("/health", "/model", "/predict", "/explain"):
        assert expected in paths, f"Missing path: {expected}"


def test_openapi_schema_has_title(client: TestClient) -> None:
    """OpenAPI schema includes the API title."""
    schema = client.get("/openapi.json").json()
    assert "Football Intelligence" in schema["info"]["title"]


def test_docs_accessible(client: TestClient) -> None:
    """GET /docs returns 200 (Swagger UI HTML)."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_accessible(client: TestClient) -> None:
    """GET /redoc returns 200 (ReDoc HTML)."""
    response = client.get("/redoc")
    assert response.status_code == 200
