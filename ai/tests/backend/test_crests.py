"""Tests for crest tables and the team crest and league emblem redirects."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.dependencies import get_league_emblems, get_team_crests
from backend.app.main import create_app
from backend.app.services.crest_table import CrestTable

ARSENAL = "https://crests.football-data.org/57.png"
PREMIER_LEAGUE = "https://crests.football-data.org/PL.png"


def write_table(tmp_path: Path, rows: str) -> Path:
    path = tmp_path / "team_crests.csv"
    path.write_text("name,crest_url\n" + rows, encoding="utf-8")
    return path


class TestCrestTable:
    def test_committed_table_loads(self) -> None:
        crests = CrestTable.from_csv(get_settings().team_crests_path)
        assert crests.url("Arsenal") == ARSENAL

    def test_committed_league_table_loads(self) -> None:
        emblems = CrestTable.from_csv(get_settings().league_emblems_path)
        assert emblems.url("Premier League") == PREMIER_LEAGUE

    def test_unknown_team_has_no_crest(self, tmp_path: Path) -> None:
        crests = CrestTable.from_csv(write_table(tmp_path, f"Arsenal,{ARSENAL}\n"))
        assert crests.url("Atlantis") is None

    def test_duplicate_team_is_rejected(self, tmp_path: Path) -> None:
        rows = f"Arsenal,{ARSENAL}\nArsenal,{ARSENAL}\n"
        with pytest.raises(ValueError, match="Duplicate"):
            CrestTable.from_csv(write_table(tmp_path, rows))

    def test_plain_http_url_is_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="https"):
            CrestTable.from_csv(write_table(tmp_path, "Arsenal,http://x/57.png\n"))


@pytest.fixture()
def crest_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_team_crests] = lambda: CrestTable({"Arsenal": ARSENAL})
    app.dependency_overrides[get_league_emblems] = lambda: CrestTable(
        {"Premier League": PREMIER_LEAGUE}
    )
    return TestClient(app, raise_server_exceptions=False, follow_redirects=False)


class TestCrestEndpoint:
    def test_known_team_redirects_to_its_crest(self, crest_client: TestClient) -> None:
        response = crest_client.get("/v2/teams/Arsenal/crest")
        assert response.status_code == 307
        assert response.headers["location"] == ARSENAL

    def test_name_with_an_apostrophe_and_space(self) -> None:
        app = create_app()
        crests = CrestTable(
            {"Nott'm Forest": "https://crests.football-data.org/351.png"}
        )
        app.dependency_overrides[get_team_crests] = lambda: crests
        client = TestClient(app, follow_redirects=False)
        assert client.get("/v2/teams/Nott'm%20Forest/crest").status_code == 307

    def test_unknown_team_is_a_structured_404(self, crest_client: TestClient) -> None:
        response = crest_client.get("/v2/teams/Atlantis/crest")
        assert response.status_code == 404
        assert response.json() == {
            "error": "No crest",
            "detail": "No crest is known for 'Atlantis'.",
        }

    def test_league_redirects_to_its_emblem(self, crest_client: TestClient) -> None:
        response = crest_client.get("/v2/competitions/Premier%20League/emblem")
        assert response.status_code == 307
        assert response.headers["location"] == PREMIER_LEAGUE

    def test_unknown_league_is_a_structured_404(self, crest_client: TestClient) -> None:
        response = crest_client.get("/v2/competitions/Eredivisie/emblem")
        assert response.status_code == 404
        assert response.json()["error"] == "No crest"
