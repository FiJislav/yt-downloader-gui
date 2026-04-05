import json
import subprocess
import urllib.request

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage


class ThumbnailWorker(QThread):
    fetched = pyqtSignal(str, QPixmap)   # title, pixmap
    failed = pyqtSignal(str)             # error reason

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self._url = url

    def run(self) -> None:
        try:
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-playlist", self._url],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                self.failed.emit(result.stderr.strip() or "yt-dlp --dump-json failed")
                return

            data = json.loads(result.stdout)
            title = data.get("title", self._url)
            thumb_url = data.get("thumbnail", "")

            pixmap = QPixmap()
            if thumb_url:
                with urllib.request.urlopen(thumb_url, timeout=10) as resp:
                    img_data = resp.read()
                image = QImage()
                if image.loadFromData(img_data):
                    pixmap = QPixmap.fromImage(image)

            self.fetched.emit(title, pixmap)
        except Exception as exc:
            self.failed.emit(str(exc))
