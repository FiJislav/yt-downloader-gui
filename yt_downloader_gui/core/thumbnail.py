import json
import subprocess
import urllib.request

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage


def parse_media_info(data: dict) -> dict:
    """Parse yt-dlp --dump-json output into structured media info."""
    formats = data.get("formats", [])

    # --- Resolutions ---
    seen_heights: list[int] = []
    for f in formats:
        h = f.get("height")
        vc = f.get("vcodec", "none")
        if h and vc != "none" and h not in seen_heights:
            seen_heights.append(h)
    seen_heights.sort(reverse=True)
    resolutions = ["Best available"] + [f"{h}p" for h in seen_heights]

    # --- Codecs per resolution ---
    formats_by_resolution: dict[str, list[str]] = {}
    for h in seen_heights:
        key = f"{h}p"
        entries = []
        for f in formats:
            if f.get("height") != h:
                continue
            if f.get("vcodec", "none") == "none":
                continue
            ext = f.get("ext", "?")
            vc_full = f.get("vcodec", "?")
            vc_short = vc_full.split(".")[0]
            fps = int(f.get("fps") or 0)
            label = f"{ext} ({vc_short}, {fps}fps)"
            if label not in entries:
                entries.append(label)
        formats_by_resolution[key] = ["Best available"] + entries

    # --- Audio tracks ---
    seen_langs: list[str] = []
    for f in formats:
        ac = f.get("acodec", "none")
        vc = f.get("vcodec", "none")
        lang = f.get("language")
        if ac != "none" and vc == "none" and lang and lang not in seen_langs:
            seen_langs.append(lang)
    audio_tracks = ["(best)"] + sorted(seen_langs)

    # --- Subtitle languages ---
    subtitle_langs: list[str] = []
    for lang in data.get("subtitles", {}).keys():
        if lang not in subtitle_langs:
            subtitle_langs.append(lang)
    for lang in data.get("automatic_captions", {}).keys():
        auto_label = f"{lang}-auto"
        if auto_label not in subtitle_langs:
            subtitle_langs.append(auto_label)
    subtitle_langs.sort()

    return {
        "resolutions": resolutions,
        "formats_by_resolution": formats_by_resolution,
        "audio_tracks": audio_tracks,
        "subtitle_langs": subtitle_langs,
    }


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
