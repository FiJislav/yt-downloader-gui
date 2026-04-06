import subprocess
import sys
from PyQt6.QtCore import QThread, pyqtSignal

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


class UpdaterWorker(QThread):
    result = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self) -> None:
        try:
            proc = subprocess.run(
                ["yt-dlp", "-U"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                creationflags=_NO_WINDOW,
            )
            output = (proc.stdout + proc.stderr).strip()
            self.result.emit(output or "Update complete.")
        except subprocess.TimeoutExpired:
            self.result.emit("Error: yt-dlp update timed out after 120 seconds.")
        except Exception as exc:
            self.result.emit(f"Error: {exc}")
