"""Tests for scripts.manage_accounts."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from backend.app.config import Settings
from scripts.manage_accounts import main


def test_invite_then_ban(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Invite prints a code; banning an email with no account exits with 1."""
    settings = Settings(accounts_path=tmp_path / "accounts.json")
    with patch("scripts.manage_accounts.get_settings", return_value=settings):
        assert main(["invite", "--email", "sam@example.com"]) == 0
        assert "Invite code for sam@example.com" in capsys.readouterr().out
        assert main(["ban", "--email", "sam@example.com"]) == 1
