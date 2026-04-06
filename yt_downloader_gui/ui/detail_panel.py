from __future__ import annotations
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel,
    QPlainTextEdit, QProgressBar, QSizePolicy,
    QVBoxLayout, QFormLayout, QWidget,
)
from yt_downloader_gui.core.models import QueueItem, ItemStatus

_PLACEHOLDER_TEXT = "No item selected"
_THUMB_WIDTH = 320
_THUMB_HEIGHT = 180
_AUDIO_FORMATS = ["mp3", "m4a", "opus", "best"]
_AUDIO_QUALITIES = ["(best quality)", "320k", "256k", "192k", "128k"]


class DetailPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_item: QueueItem | None = None
        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_loading(self) -> None:
        """Show Loading… in all metadata dropdowns and disable them."""
        for combo in (self._resolution_combo, self._codec_combo,
                      self._audio_track_combo, self._subtitle_combo):
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("Loading…")
            combo.setEnabled(False)
            combo.blockSignals(False)

    def load_item(self, item: QueueItem | None) -> None:
        self._current_item = item
        if item is None:
            self._title_label.setText("")
            self._thumbnail_label.clear()
            self._thumbnail_label.setText(_PLACEHOLDER_TEXT)
            self._progress_bar.setValue(0)
            self._log_output.setPlainText("")
            self._reset_combos_to_default()
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

        self._populate_from_item(item)
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
        for w in self._all_controls():
            w.setEnabled(False)

    def unlock_controls(self) -> None:
        # Re-enable all, then re-apply audio-only state
        for w in self._all_controls():
            w.setEnabled(True)
        self._apply_audio_only_state(self._audio_only_check.isChecked())
        self._apply_subtitle_state(self._subtitle_combo.currentText())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _all_controls(self):
        return [
            self._audio_only_check,
            self._audio_fmt_combo,
            self._audio_quality_combo,
            self._resolution_combo,
            self._codec_combo,
            self._audio_track_combo,
            self._subtitle_combo,
            self._embed_subs_check,
        ]

    def _reset_combos_to_default(self) -> None:
        for combo, default in [
            (self._resolution_combo, "Best available"),
            (self._codec_combo, "Best available"),
            (self._audio_track_combo, "(best)"),
            (self._subtitle_combo, "none"),
            (self._audio_fmt_combo, "mp3"),
            (self._audio_quality_combo, "(best quality)"),
        ]:
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(default)
            combo.blockSignals(False)
        self._audio_only_check.setChecked(False)
        self._embed_subs_check.setChecked(False)

    def _populate_from_item(self, item: QueueItem) -> None:
        # Resolution
        self._resolution_combo.blockSignals(True)
        self._resolution_combo.clear()
        resolutions = item.resolutions if item.resolutions else ["Best available"]
        self._resolution_combo.addItems(resolutions)
        idx = self._resolution_combo.findText(item.resolution)
        self._resolution_combo.setCurrentIndex(max(0, idx))
        self._resolution_combo.blockSignals(False)

        # Codec (filtered by current resolution)
        self._refresh_codec_combo(item.resolution, item.formats_by_resolution, item.codec)

        # Audio track
        self._audio_track_combo.blockSignals(True)
        self._audio_track_combo.clear()
        tracks = item.audio_tracks if item.audio_tracks else ["(best)"]
        self._audio_track_combo.addItems(tracks)
        idx = self._audio_track_combo.findText(item.audio_track)
        self._audio_track_combo.setCurrentIndex(max(0, idx))
        self._audio_track_combo.blockSignals(False)

        # Subtitles
        self._subtitle_combo.blockSignals(True)
        self._subtitle_combo.clear()
        self._subtitle_combo.addItem("none")
        self._subtitle_combo.addItems(item.subtitle_langs)
        idx = self._subtitle_combo.findText(item.subtitle_lang if item.subtitle_lang else "none")
        self._subtitle_combo.setCurrentIndex(max(0, idx))
        self._subtitle_combo.blockSignals(False)

        # Audio-only / audio fmt / quality
        self._audio_only_check.blockSignals(True)
        self._audio_only_check.setChecked(item.audio_only)
        self._audio_only_check.blockSignals(False)

        self._audio_fmt_combo.blockSignals(True)
        self._audio_fmt_combo.setCurrentText(item.audio_fmt)
        self._audio_fmt_combo.blockSignals(False)

        self._audio_quality_combo.blockSignals(True)
        self._audio_quality_combo.setCurrentText(item.audio_quality)
        self._audio_quality_combo.blockSignals(False)

        self._embed_subs_check.blockSignals(True)
        self._embed_subs_check.setChecked(item.embed_subs)
        self._embed_subs_check.blockSignals(False)

        self._apply_audio_only_state(item.audio_only)
        self._apply_subtitle_state(self._subtitle_combo.currentText())

    def _refresh_codec_combo(self, resolution: str, formats_by_resolution: dict, current_codec: str) -> None:
        self._codec_combo.blockSignals(True)
        self._codec_combo.clear()
        codecs = formats_by_resolution.get(resolution, ["Best available"])
        self._codec_combo.addItems(codecs)
        idx = self._codec_combo.findText(current_codec)
        self._codec_combo.setCurrentIndex(max(0, idx))
        self._codec_combo.blockSignals(False)

    def _apply_audio_only_state(self, audio_only: bool) -> None:
        self._resolution_combo.setEnabled(not audio_only)
        self._codec_combo.setEnabled(not audio_only)
        self._audio_track_combo.setEnabled(not audio_only)
        self._subtitle_combo.setEnabled(not audio_only)
        self._embed_subs_check.setEnabled(not audio_only)
        self._audio_fmt_combo.setEnabled(audio_only)
        self._audio_quality_combo.setEnabled(audio_only)

    def _apply_subtitle_state(self, subtitle_text: str) -> None:
        has_sub = subtitle_text != "none" and subtitle_text != ""
        # Only enable embed if we're not in audio-only and subtitle is selected
        if not self._audio_only_check.isChecked():
            self._embed_subs_check.setEnabled(has_sub)

    # ------------------------------------------------------------------
    # UI Construction
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

        # Audio-only row
        audio_only_row = QHBoxLayout()
        self._audio_only_check = QCheckBox("Audio only")
        self._audio_only_check.toggled.connect(self._on_audio_only_toggled)
        audio_only_row.addWidget(self._audio_only_check)
        audio_only_row.addWidget(QLabel("Format:"))
        self._audio_fmt_combo = QComboBox()
        self._audio_fmt_combo.addItems(_AUDIO_FORMATS)
        self._audio_fmt_combo.setEnabled(False)
        self._audio_fmt_combo.currentTextChanged.connect(self._on_audio_fmt_changed)
        audio_only_row.addWidget(self._audio_fmt_combo)
        audio_only_row.addWidget(QLabel("Quality:"))
        self._audio_quality_combo = QComboBox()
        self._audio_quality_combo.addItems(_AUDIO_QUALITIES)
        self._audio_quality_combo.setEnabled(False)
        self._audio_quality_combo.currentTextChanged.connect(self._on_audio_quality_changed)
        audio_only_row.addWidget(self._audio_quality_combo)
        audio_only_row.addStretch()
        layout.addLayout(audio_only_row)

        # Controls form
        form = QFormLayout()

        self._resolution_combo = QComboBox()
        self._resolution_combo.addItem("Best available")
        self._resolution_combo.currentTextChanged.connect(self._on_resolution_changed)
        form.addRow("Resolution:", self._resolution_combo)

        self._codec_combo = QComboBox()
        self._codec_combo.addItem("Best available")
        self._codec_combo.currentTextChanged.connect(self._on_codec_changed)
        form.addRow("Codec:", self._codec_combo)

        self._audio_track_combo = QComboBox()
        self._audio_track_combo.addItem("(best)")
        self._audio_track_combo.currentTextChanged.connect(self._on_audio_track_changed)
        form.addRow("Audio track:", self._audio_track_combo)

        self._subtitle_combo = QComboBox()
        self._subtitle_combo.addItem("none")
        self._subtitle_combo.currentTextChanged.connect(self._on_subtitle_changed)
        form.addRow("Subtitles:", self._subtitle_combo)

        self._embed_subs_check = QCheckBox("Embed subtitles")
        self._embed_subs_check.setEnabled(False)
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

    # ------------------------------------------------------------------
    # Slots — write back to current item
    # ------------------------------------------------------------------

    def _on_audio_only_toggled(self, checked: bool) -> None:
        if self._current_item:
            self._current_item.audio_only = checked
        self._apply_audio_only_state(checked)

    def _on_audio_fmt_changed(self, text: str) -> None:
        if self._current_item:
            self._current_item.audio_fmt = text

    def _on_audio_quality_changed(self, text: str) -> None:
        if self._current_item:
            self._current_item.audio_quality = text

    def _on_resolution_changed(self, text: str) -> None:
        if self._current_item:
            self._current_item.resolution = text
            self._refresh_codec_combo(
                text,
                self._current_item.formats_by_resolution,
                "Best available",
            )
            self._current_item.codec = "Best available"

    def _on_codec_changed(self, text: str) -> None:
        if self._current_item:
            self._current_item.codec = text

    def _on_audio_track_changed(self, text: str) -> None:
        if self._current_item:
            self._current_item.audio_track = text

    def _on_subtitle_changed(self, text: str) -> None:
        if self._current_item:
            self._current_item.subtitle_lang = "" if text == "none" else text
        self._apply_subtitle_state(text)

    def _on_embed_subs_changed(self, checked: bool) -> None:
        if self._current_item:
            self._current_item.embed_subs = checked
