"""Tests for get_app_root, per Phase 10 packaging support."""

import sys
from pathlib import Path

import pytest
from src.shared.paths import get_app_root


def test_resolves_to_project_root_when_not_frozen() -> None:
    root = get_app_root()

    assert (root / "pyproject.toml").exists()
    assert (root / "src").is_dir()


def test_resolves_to_meipass_when_frozen(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "_MEIPASS", "/fake/bundle/root", raising=False)

    root = get_app_root()

    assert root == Path("/fake/bundle/root")
