from __future__ import annotations
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton,
    QSplitter, QVBoxLayout, QWidget,
)
from yt_downloader_gui.core.downloader import DownloadWorker
from yt_downloader_gui.core.models import ItemStatus
from yt_downloader_gui.core.settings import AppSettings
from yt_downloader_gui.core.thumbnail import ThumbnailWorker
from yt_downloader_gui.core.updater import UpdaterWorker
from yt_downloader_gui.ui.detail_panel import DetailPanel
from yt_downloader_gui.ui.queue_panel import QueueListItem, QueuePanel


class MainWindow(QMainWindow):
    def __init__(
        self,
        settings_org: str = "YTDownloader",
        settings_app: str = "YTDownloaderGUI",
        parent=None,
    ):
        super().__init__(parent)
        self._settings = AppSettings(org=settings_org, app=settings_app)
        self._worker: DownloadWorker | None = None
        self._updater: UpdaterWorker | None = None
        self._thumbnail_workers: list[ThumbnailWorker] = []
        self._queue_paused: bool = False
        self._build_ui()
        self._restore_geometry()
        self.setWindowTitle("YT Downloader")

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # URL bar
        url_bar = QHBoxLayout()
        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("Paste YouTube / video URL here…")
        self._url_input.returnPressed.connect(self._on_add)
        url_bar.addWidget(self._url_input)
        self._add_btn = QPushButton("Add")
        self._add_btn.clicked.connect(self._on_add)
        url_bar.addWidget(self._add_btn)
        self._paste_btn = QPushButton("Paste from Clipboard")
        self._paste_btn.clicked.connect(self._on_paste)
        url_bar.addWidget(self._paste_btn)
        root.addLayout(url_bar)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self._queue_panel = QueuePanel()
        self._queue_panel.setMinimumWidth(200)
        self._queue_panel.currentItemChanged.connect(self._on_item_selected)
        splitter.addWidget(self._queue_panel)

        self._detail_panel = DetailPanel()
        splitter.addWidget(self._detail_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, stretch=1)

        # Bottom bar
        bottom = QHBoxLayout()
        bottom.addWidget(QLabel("Output folder:"))
        self._folder_label = QLabel(self._settings.output_dir)
        self._folder_label.setMinimumWidth(200)
        bottom.addWidget(self._folder_label, stretch=1)
        self._browse_btn = QPushButton("Browse…")
        self._browse_btn.clicked.connect(self._on_browse)
        bottom.addWidget(self._browse_btn)

        bottom.addStretch()

        self._start_btn = QPushButton("Start Queue")
        self._start_btn.clicked.connect(self._on_start_queue)
        bottom.addWidget(self._start_btn)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._on_stop)
        bottom.addWidget(self._stop_btn)

        self._update_btn = QPushButton("Update yt-dlp")
        self._update_btn.clicked.connect(self._on_update_ytdlp)
        bottom.addWidget(self._update_btn)

        self._update_status_label = QLabel("")
        bottom.addWidget(self._update_status_label)

        root.addLayout(bottom)

        self.resize(1000, 640)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_add(self) -> None:
        url = self._url_input.text().strip()
        if not url:
            return
        self._add_url(url)
        self._url_input.clear()

    def _on_paste(self) -> None:
        text = QApplication.clipboard().text().strip()
        if text.startswith("http://") or text.startswith("https://"):
            self._add_url(text)

    def _add_url(self, url: str) -> None:
        # Duplicate check
        for i in range(self._queue_panel.count()):
            if self._queue_panel.item(i).queue_item.url == url:
                reply = QMessageBox.warning(
                    self,
                    "Duplicate URL",
                    f"This URL is already in the queue:\n{url}\n\nAdd it anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
                break

        list_item = self._queue_panel.add_item(url)
        # Show loading state immediately if this item is selected
        if self._queue_panel.currentItem() is list_item:
            self._detail_panel.set_loading()
        self._start_thumbnail_fetch(list_item)

    def _start_thumbnail_fetch(self, list_item: QueueListItem) -> None:
        worker = ThumbnailWorker(list_item.queue_item.url)
        self._thumbnail_workers.append(worker)

        def on_fetched(title: str, pixmap, media_info: dict) -> None:
            list_item.queue_item.title = title
            list_item.queue_item.thumbnail = pixmap
            list_item.queue_item.resolutions = media_info.get("resolutions", [])
            list_item.queue_item.formats_by_resolution = media_info.get("formats_by_resolution", {})
            list_item.queue_item.audio_tracks = media_info.get("audio_tracks", [])
            list_item.queue_item.subtitle_langs = media_info.get("subtitle_langs", [])
            list_item.refresh()
            current = self._queue_panel.currentItem()
            if current is list_item:
                self._detail_panel.load_item(list_item.queue_item)
            self._remove_thumbnail_worker(worker)

        def on_failed(reason: str) -> None:
            list_item.queue_item.status = ItemStatus.ERROR
            list_item.setToolTip(reason)
            list_item.refresh()
            current = self._queue_panel.currentItem()
            if current is list_item:
                self._detail_panel.load_item(list_item.queue_item)
            self._remove_thumbnail_worker(worker)

        worker.fetched.connect(on_fetched)
        worker.failed.connect(on_failed)
        worker.start()

    def _remove_thumbnail_worker(self, worker: ThumbnailWorker) -> None:
        try:
            self._thumbnail_workers.remove(worker)
        except ValueError:
            pass

    def _on_item_selected(self, current: QueueListItem | None, _previous) -> None:
        if current is None:
            self._detail_panel.load_item(None)
        else:
            self._detail_panel.load_item(current.queue_item)

    def _on_start_queue(self) -> None:
        if self._worker is not None:
            return  # already running
        self._queue_paused = False
        next_item = self._queue_panel.next_pending()
        if next_item is None:
            return
        self._run_item(next_item)

    def _run_item(self, list_item: QueueListItem) -> None:
        list_item.queue_item.status = ItemStatus.ACTIVE
        list_item.queue_item.log = ""
        list_item.refresh()

        current = self._queue_panel.currentItem()
        if current is list_item:
            self._detail_panel.load_item(list_item.queue_item)

        self._worker = DownloadWorker(list_item.queue_item, self._settings.output_dir)

        def on_progress(pct: int) -> None:
            if self._queue_panel.currentItem() is list_item:
                self._detail_panel.update_progress(pct)

        def on_log_line(line: str) -> None:
            list_item.queue_item.log += line + "\n"
            if self._queue_panel.currentItem() is list_item:
                self._detail_panel.append_log(line)

        def on_finished() -> None:
            list_item.queue_item.status = ItemStatus.DONE
            list_item.refresh()
            self._worker = None
            self._stop_btn.setEnabled(False)
            self._start_btn.setEnabled(True)
            self._advance_queue()

        def on_error(msg: str) -> None:
            list_item.queue_item.status = ItemStatus.ERROR
            list_item.queue_item.log += f"\nERROR: {msg}\n"
            list_item.refresh()
            if self._queue_panel.currentItem() is list_item:
                self._detail_panel.append_log(f"ERROR: {msg}")
            self._worker = None
            self._stop_btn.setEnabled(False)
            self._start_btn.setEnabled(True)
            self._advance_queue()

        self._worker.progress.connect(on_progress)
        self._worker.log_line.connect(on_log_line)
        self._worker.finished.connect(on_finished)
        self._worker.error.connect(on_error)

        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._worker.start()

    def _advance_queue(self) -> None:
        if self._queue_paused:
            return
        next_item = self._queue_panel.next_pending()
        if next_item is not None:
            self._run_item(next_item)

    def _on_stop(self) -> None:
        self._queue_paused = True
        if self._worker is not None:
            self._worker.stop()
        for i in range(self._queue_panel.count()):
            item = self._queue_panel.item(i)
            if item.queue_item.status == ItemStatus.ACTIVE:
                item.queue_item.status = ItemStatus.STOPPED
                item.refresh()
        self._stop_btn.setEnabled(False)
        self._start_btn.setEnabled(True)

    def _on_browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", self._settings.output_dir
        )
        if folder:
            self._settings.output_dir = folder
            self._folder_label.setText(folder)

    def _on_update_ytdlp(self) -> None:
        self._update_btn.setEnabled(False)
        self._update_btn.setText("Updating…")
        self._updater = UpdaterWorker()

        def on_result(msg: str) -> None:
            self._update_status_label.setText(msg)
            self._update_btn.setEnabled(True)
            self._update_btn.setText("Update yt-dlp")

        self._updater.result.connect(on_result)
        self._updater.start()

    # ------------------------------------------------------------------
    # Geometry persistence
    # ------------------------------------------------------------------

    def _restore_geometry(self) -> None:
        geo = self._settings.load_geometry()
        if geo:
            self.restoreGeometry(geo)

    def closeEvent(self, event) -> None:
        self._settings.save_geometry(bytes(self.saveGeometry()))
        for worker in list(self._thumbnail_workers):
            worker.quit()
            worker.wait(500)
        if self._worker is not None:
            self._worker.stop()
            self._worker.wait(1000)
        super().closeEvent(event)
