import subprocess
from PyQt6.QtCore import QThread, pyqtSignal


class UpdaterWorker(QThread):
    result = pyqtSignal(str)

    def run(self) -> None:
        try:
            proc = subprocess.run(
                ["yt-dlp", "-U"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = (proc.stdout + proc.stderr).strip()
            self.result.emit(output or "Update complete.")
        except Exception as exc:
            self.result.emit(f"Error: {exc}")
