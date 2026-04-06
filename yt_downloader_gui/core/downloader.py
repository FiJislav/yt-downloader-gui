import re
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

from yt_downloader_gui.core.models import QueueItem

PROGRESS_RE = re.compile(r"\[download\]\s+(\d+(?:\.\d+)?)%")

_QUALITY_MAP = {
    "(best quality)": "0",
    "320k": "320k",
    "256k": "256k",
    "192k": "192k",
    "128k": "128k",
}


def build_args(item: QueueItem, output_dir: str) -> list[str]:
    """Build the yt-dlp CLI argument list for a QueueItem."""
    args = ["yt-dlp"]

    if item.audio_only:
        # Audio-only mode
        fmt_sel = (
            f"bestaudio[ext={item.audio_fmt}]/bestaudio"
            if item.audio_fmt != "best"
            else "bestaudio"
        )
        args += ["-f", fmt_sel, "--extract-audio"]
        if item.audio_fmt != "best":
            args += ["--audio-format", item.audio_fmt]
        quality = _QUALITY_MAP.get(item.audio_quality, "0")
        args += ["--audio-quality", quality]
    else:
        # Video mode — build format selector
        height = _parse_height(item.resolution)
        lang = item.audio_track if item.audio_track != "(best)" else None

        if height is None:
            # Best available resolution
            audio_part = f"bestaudio[language={lang}]/bestaudio" if lang else "bestaudio"
            fmt_sel = f"bestvideo+{audio_part}/best"
        elif item.codec == "Best available":
            audio_part = f"bestaudio[language={lang}]/bestaudio" if lang else "bestaudio"
            fmt_sel = f"bestvideo[height<={height}]+{audio_part}/best"
        else:
            ext, vcodec_short = _parse_codec(item.codec)
            audio_part = f"bestaudio[language={lang}]/bestaudio" if lang else "bestaudio"
            fmt_sel = f"bestvideo[height<={height}][ext={ext}][vcodec~={vcodec_short}]+{audio_part}/best"

        args += ["-f", fmt_sel]

        # Merge format
        merge_fmt = _merge_format(item.codec, item.resolution)
        args += ["--merge-output-format", merge_fmt]

        # Subtitles
        if item.subtitle_lang:
            if item.subtitle_lang.endswith("-auto"):
                lang_code = item.subtitle_lang[:-5]
                args += ["--write-auto-subs", "--sub-lang", lang_code, "--convert-subs", "srt"]
            else:
                args += ["--write-subs", "--sub-lang", item.subtitle_lang, "--convert-subs", "srt"]
            if item.embed_subs:
                args += ["--embed-subs"]

    if output_dir:
        args += ["-o", f"{output_dir}/%(title)s.%(ext)s"]

    args.append(item.url)
    return args


def _parse_height(resolution: str) -> int | None:
    """Return integer height from '1080p', or None for 'Best available'."""
    if resolution == "Best available":
        return None
    return int(resolution.rstrip("p"))


def _parse_codec(codec: str) -> tuple[str, str]:
    """Parse 'mp4 (avc1, 30fps)' -> ('mp4', 'avc1')."""
    ext = codec.split(" ")[0]
    vcodec_short = codec.split("(")[1].split(",")[0].strip()
    return ext, vcodec_short


def _merge_format(codec: str, resolution: str) -> str:
    """Determine --merge-output-format value."""
    if codec == "Best available":
        return "mp4"
    if codec.startswith("mp4"):
        return "mp4"
    return "mkv"


class DownloadWorker(QThread):
    progress = pyqtSignal(int)
    log_line = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, item: QueueItem, output_dir: str, parent=None):
        super().__init__(parent)
        self._item = item
        self._output_dir = output_dir
        self._process: subprocess.Popen | None = None

    def run(self) -> None:
        args = build_args(self._item, self._output_dir)
        try:
            self._process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            for line in self._process.stdout:
                line = line.rstrip()
                self.log_line.emit(line)
                m = PROGRESS_RE.search(line)
                if m:
                    self.progress.emit(int(float(m.group(1))))
            self._process.wait()
            if self._process.returncode == 0:
                self.finished.emit()
            else:
                self.error.emit(f"yt-dlp exited with code {self._process.returncode}")
        except Exception as exc:
            self.error.emit(str(exc))

    def stop(self) -> None:
        if self._process is not None:
            self._process.terminate()
