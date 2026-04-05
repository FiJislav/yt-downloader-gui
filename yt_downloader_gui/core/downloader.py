import re
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

from yt_downloader_gui.core.models import QueueItem

PROGRESS_RE = re.compile(r"\[download\]\s+(\d+(?:\.\d+)?)%")

FORMATS = ["mp4", "mp3", "mkv", "4k", "4k-no-av1", "subs", "embed-subs"]


def build_args(item: QueueItem, output_dir: str) -> list[str]:
    """Build the yt-dlp CLI argument list for a QueueItem."""
    audio_sel = f"bestaudio[lang={item.audio_lang}]" if item.audio_lang else "bestaudio"
    args = ["yt-dlp"]

    if item.fmt == "mp3":
        args += ["-f", audio_sel, "--extract-audio", "--audio-format", "mp3", "--audio-quality", "0"]
    elif item.fmt == "mp4":
        args += ["-f", "best"]
    elif item.fmt == "mkv":
        args += ["-f", f"bestvideo+{audio_sel}", "--merge-output-format", "mkv"]
    elif item.fmt == "4k":
        args += ["-f", f"bestvideo[height<=2160]+{audio_sel}/best", "--merge-output-format", "mp4"]
    elif item.fmt == "4k-no-av1":
        args += ["-f", f"bestvideo[height>=2160][vcodec!=av01]+{audio_sel}/best", "--merge-output-format", "mkv"]
    elif item.fmt == "subs":
        args += ["--write-subs", "--sub-lang", item.sub_lang, "--convert-subs", "srt"]
    elif item.fmt == "embed-subs":
        args += [
            "-f", f"bestvideo+{audio_sel}", "--merge-output-format", "mp4",
            "--embed-subs", "--sub-lang", item.sub_lang, "--convert-subs", "srt",
        ]

    # Embed subs checkbox applies to formats that don't already handle subs
    if item.embed_subs and item.fmt not in ("subs", "embed-subs"):
        args += ["--embed-subs", "--sub-lang", item.sub_lang, "--convert-subs", "srt"]

    if output_dir:
        args += ["-o", f"{output_dir}/%(title)s.%(ext)s"]

    args.append(item.url)
    return args


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
