"""Runs apply.sh and remove.sh in dry-run mode against a fake gcloud (M6)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
MONITORING = ROOT / "infrastructure" / "monitoring"
METRICS = len(list((MONITORING / "metrics").glob("*.yaml")))
ALERTS = len(list((MONITORING / "alerts").glob("*.json")))

pytestmark = pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("bash") is None,
    reason="the scripts are bash; Windows paths and bash shims make the run unreliable",
)


def _dry_run(script: str, tmp_path: Path) -> list[str]:
    """Run ``script --dry-run`` with a gcloud that records any real call."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "gcloud"
    fake.write_text(f'#!/bin/sh\necho "$@" >> "{tmp_path}/called"\n', "utf-8")
    fake.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "PROJECT_ID": "demo-project",
        "NOTIFICATION_CHANNEL": "demo-channel",
    }
    result = subprocess.run(
        ["bash", str(MONITORING / script), "--dry-run"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert not (tmp_path / "called").exists(), "a dry run must not call gcloud"
    return result.stdout.splitlines()


def test_apply_dry_run_prints_one_command_per_metric_and_policy(
    tmp_path: Path,
) -> None:
    lines = _dry_run("apply.sh", tmp_path)
    metrics = [line for line in lines if line.startswith("gcloud logging metrics ")]
    policies = [line for line in lines if "monitoring policies create" in line]
    assert len(metrics) == METRICS
    assert len(policies) == ALERTS
    assert len(lines) == METRICS + ALERTS
    assert all("--project=demo-project" in line for line in lines)
    assert all("--notification-channels=demo-channel" in line for line in policies)


def test_remove_dry_run_deletes_what_apply_creates(tmp_path: Path) -> None:
    lines = _dry_run("remove.sh", tmp_path)
    assert len([line for line in lines if "metrics delete" in line]) == METRICS
    assert len([line for line in lines if "policies delete" in line]) == ALERTS
    assert len(lines) == METRICS + ALERTS


def test_apply_refuses_to_run_without_a_project(tmp_path: Path) -> None:
    env = {k: v for k, v in os.environ.items() if k != "PROJECT_ID"}
    result = subprocess.run(
        ["bash", str(MONITORING / "apply.sh"), "--dry-run"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "PROJECT_ID" in result.stderr
