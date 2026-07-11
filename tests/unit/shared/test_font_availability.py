"""Tests for has_bundled_font, per Iteration 2 Task B."""

from pathlib import Path

import pytest
from src.shared import font_availability


def test_returns_false_when_fonts_dir_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(font_availability, "get_app_root", lambda: tmp_path)

    assert font_availability.has_bundled_font("cairo") is False


def test_returns_true_when_matching_font_file_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fonts_dir = tmp_path / "resources" / "fonts"
    fonts_dir.mkdir(parents=True)
    (fonts_dir / "Cairo-Regular.ttf").write_bytes(b"")
    monkeypatch.setattr(font_availability, "get_app_root", lambda: tmp_path)

    assert font_availability.has_bundled_font("cairo") is True


def test_returns_false_when_no_matching_font_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fonts_dir = tmp_path / "resources" / "fonts"
    fonts_dir.mkdir(parents=True)
    (fonts_dir / "Tajawal-Regular.ttf").write_bytes(b"")
    monkeypatch.setattr(font_availability, "get_app_root", lambda: tmp_path)

    assert font_availability.has_bundled_font("cairo") is False
