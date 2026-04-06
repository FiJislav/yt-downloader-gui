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
        if h and vc != "none" and h not in seen_heights:  # h=0 and h=None are falsy: intentionally excluded
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
            fps = int(float(f.get("fps") or 0))
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
    # Manual subtitles: always include all
    manual_langs = set(data.get("subtitles", {}).keys())
    subtitle_langs: list[str] = sorted(manual_langs)

    # Auto-generated: only include if relevant to this video —
    # i.e. the language matches the video's primary language (base code)
    # or there is also a manual subtitle in that language.
    vid_lang = (data.get("language") or "").lower()
    vid_lang_base = vid_lang.split("-")[0]  # "en-US" → "en"
    manual_bases = {l.split("-")[0].lower() for l in manual_langs}

    for lang in data.get("automatic_captions", {}).keys():
        lang_base = lang.split("-")[0].lower()
        relevant = (
            (vid_lang_base and lang_base == vid_lang_base)
            or lang_base in manual_bases
        )
        if relevant:
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


class PlaylistFetcher(QThread):
    """Fetch all video URLs from a playlist URL using --flat-playlist."""
    fetched = pyqtSignal(list)   # list[str] of video URLs
    failed = pyqtSignal(str)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self._url = url

    def run(self) -> None:
        try:
            result = subprocess.run(
                ["yt-dlp", "--flat-playlist", "--print", "webpage_url", self._url],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                self.failed.emit(result.stderr.strip() or "Failed to fetch playlist")
                return
            urls = [u.strip() for u in result.stdout.splitlines() if u.strip()]
            self.fetched.emit(urls)
        except Exception as exc:
            self.failed.emit(str(exc))


class ThumbnailWorker(QThread):
    fetched = pyqtSignal(str, QPixmap, dict)   # title, pixmap, media_info
    failed = pyqtSignal(str)

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

            media_info = parse_media_info(data)
            self.fetched.emit(title, pixmap, media_info)
        except Exception as exc:
            self.failed.emit(str(exc))
