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

    def save_geometry(self, geometry: bytes) -> None:
        self._qs.setValue("geometry", geometry)

    def load_geometry(self) -> bytes | None:
        return self._qs.value("geometry", None)
