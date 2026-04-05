import shutil
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from yt_downloader_gui.ui.main_window import MainWindow


def _check_ytdlp() -> bool:
    if shutil.which("yt-dlp") is None:
        app = QApplication.instance() or QApplication(sys.argv)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("yt-dlp not found")
        msg.setText(
            "yt-dlp is not installed or not in PATH.\n\n"
            "Install it with:\n"
            "  pip install yt-dlp\n\n"
            "Or download from: https://github.com/yt-dlp/yt-dlp"
        )
        msg.exec()
        return False
    return True


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("YT Downloader")
    app.setOrganizationName("YTDownloader")

    if not _check_ytdlp():
        sys.exit(1)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
