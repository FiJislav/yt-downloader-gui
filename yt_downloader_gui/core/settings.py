from pathlib import Path
from PyQt6.QtCore import QSettings


class AppSettings:
    def __init__(self, org: str = "YTDownloader", app: str = "YTDownloaderGUI"):
        self._qs = QSettings(org, app)

    @property
    def output_dir(self) -> str:
        default = str(Path.home() / "Downloads")
        return self._qs.value("output_dir", default)

    @output_dir.setter
    def output_dir(self, value: str) -> None:
        self._qs.setValue("output_dir", value)

    @property
    def cookies_browser(self) -> str:
        """Browser to pull cookies from, e.g. 'chrome', 'firefox', 'edge', or '' for none."""
        return self._qs.value("cookies_browser", "")

    @cookies_browser.setter
    def cookies_browser(self, value: str) -> None:
        self._qs.setValue("cookies_browser", value)

    def save_geometry(self, geometry: bytes) -> None:
        self._qs.setValue("geometry", geometry)

    def load_geometry(self) -> bytes | None:
        if not self._qs.contains("geometry"):
            return None
        return self._qs.value("geometry", type=bytes)
