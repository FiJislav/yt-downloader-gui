import pytest
from PyQt6.QtCore import QSettings
from yt_downloader_gui.core.settings import AppSettings


@pytest.fixture(autouse=True)
def clean_settings():
    # Use a test-specific org/app name so tests don't pollute real settings
    qs = QSettings("YTDownloaderTest", "YTDownloaderGUITest")
    qs.clear()
    yield
    qs.clear()


@pytest.fixture
def settings():
    return AppSettings(org="YTDownloaderTest", app="YTDownloaderGUITest")


def test_default_output_dir(settings, tmp_path, monkeypatch):
    from pathlib import Path
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    s = AppSettings(org="YTDownloaderTest", app="YTDownloaderGUITest")
    assert s.output_dir == str(tmp_path / "Downloads")


def test_set_and_get_output_dir(settings):
    settings.output_dir = "C:/Videos"
    assert settings.output_dir == "C:/Videos"


def test_save_and_load_geometry(settings):
    data = b"\x01\x02\x03\x04"
    settings.save_geometry(data)
    assert settings.load_geometry() == data


def test_load_geometry_returns_none_when_unset(settings):
    assert settings.load_geometry() is None
