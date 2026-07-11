"""Tests for app_settings persistence, per Iteration 2 §8.3."""

from pathlib import Path

import pytest
from src.infrastructure.config import app_settings


def test_returns_none_when_never_saved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_settings, "_SETTINGS_FILE", tmp_path / "app_settings.json")

    assert app_settings.load_last_output_dir() is None


def test_round_trips_a_saved_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_settings, "_SETTINGS_DIR", tmp_path)
    monkeypatch.setattr(app_settings, "_SETTINGS_FILE", tmp_path / "app_settings.json")
    saved_path = tmp_path / "GIS_Output"

    app_settings.save_last_output_dir(saved_path)

    assert app_settings.load_last_output_dir() == saved_path


def test_returns_none_for_corrupt_settings_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings_file = tmp_path / "app_settings.json"
    settings_file.write_text("not valid json", encoding="utf-8")
    monkeypatch.setattr(app_settings, "_SETTINGS_FILE", settings_file)

    assert app_settings.load_last_output_dir() is None
