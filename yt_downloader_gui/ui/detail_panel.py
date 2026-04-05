from __future__ import annotations
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QLabel, QLineEdit,
    QPlainTextEdit, QProgressBar, QSizePolicy,
    QVBoxLayout, QFormLayout, QWidget, QFrame,
)
from yt_downloader_gui.core.models import QueueItem, ItemStatus
from yt_downloader_gui.core.downloader import FORMATS

_PLACEHOLDER_TEXT = "No item selected"
_THUMB_WIDTH = 320
_THUMB_HEIGHT = 180


class DetailPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_item: QueueItem | None = None
        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_item(self, item: QueueItem | None) -> None:
        self._current_item = item
        if item is None:
            self._title_label.setText("")
            self._thumbnail_label.clear()
            self._fmt_combo.setCurrentText("mp4")
            self._audio_lang_edit.clear()
            self._sub_lang_edit.setText("en")
            self._embed_subs_check.setChecked(False)
            self._progress_bar.setValue(0)
            self._log_output.setPlainText("")
            self.unlock_controls()
            return

        self._title_label.setText(item.title or item.url)
        if item.thumbnail and not item.thumbnail.isNull():
            self._thumbnail_label.setPixmap(
                item.thumbnail.scaled(
                    _THUMB_WIDTH, _THUMB_HEIGHT,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self._thumbnail_label.setText("No thumbnail")

        self._fmt_combo.setCurrentText(item.fmt)
        self._audio_lang_edit.setText(item.audio_lang)
        self._sub_lang_edit.setText(item.sub_lang)
        self._embed_subs_check.setChecked(item.embed_subs)
        self._log_output.setPlainText(item.log)
        self._progress_bar.setValue(0)

        if item.status == ItemStatus.PENDING:
            self.unlock_controls()
        else:
            self.lock_controls()

    def update_progress(self, pct: int) -> None:
        self._progress_bar.setValue(pct)

    def append_log(self, line: str) -> None:
        self._log_output.appendPlainText(line)
        self._log_output.verticalScrollBar().setValue(
            self._log_output.verticalScrollBar().maximum()
        )

    def lock_controls(self) -> None:
        for w in (self._fmt_combo, self._audio_lang_edit, self._sub_lang_edit, self._embed_subs_check):
            w.setEnabled(False)

    def unlock_controls(self) -> None:
        for w in (self._fmt_combo, self._audio_lang_edit, self._sub_lang_edit, self._embed_subs_check):
            w.setEnabled(True)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Thumbnail
        self._thumbnail_label = QLabel(_PLACEHOLDER_TEXT)
        self._thumbnail_label.setFixedSize(_THUMB_WIDTH, _THUMB_HEIGHT)
        self._thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumbnail_label.setFrameShape(QFrame.Shape.Box)
        layout.addWidget(self._thumbnail_label)

        # Title
        self._title_label = QLabel("")
        self._title_label.setWordWrap(True)
        layout.addWidget(self._title_label)

        # Controls form
        form = QFormLayout()
        self._fmt_combo = QComboBox()
        self._fmt_combo.addItems(FORMATS)
        self._fmt_combo.currentTextChanged.connect(self._on_fmt_changed)
        form.addRow("Format:", self._fmt_combo)

        self._audio_lang_edit = QLineEdit()
        self._audio_lang_edit.setPlaceholderText("e.g. en, ja  (optional)")
        self._audio_lang_edit.textChanged.connect(self._on_audio_lang_changed)
        form.addRow("Audio lang:", self._audio_lang_edit)

        self._sub_lang_edit = QLineEdit("en")
        self._sub_lang_edit.textChanged.connect(self._on_sub_lang_changed)
        form.addRow("Subtitle lang:", self._sub_lang_edit)

        self._embed_subs_check = QCheckBox("Embed subtitles")
        self._embed_subs_check.toggled.connect(self._on_embed_subs_changed)
        form.addRow("", self._embed_subs_check)

        layout.addLayout(form)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)

        # Log output
        self._log_output = QPlainTextEdit()
        self._log_output.setReadOnly(True)
        self._log_output.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._log_output)

    def _on_fmt_changed(self, text: str) -> None:
        if self._current_item:
            self._current_item.fmt = text

    def _on_audio_lang_changed(self, text: str) -> None:
        if self._current_item:
            self._current_item.audio_lang = text

    def _on_sub_lang_changed(self, text: str) -> None:
        if self._current_item:
            self._current_item.sub_lang = text

    def _on_embed_subs_changed(self, checked: bool) -> None:
        if self._current_item:
            self._current_item.embed_subs = checked
