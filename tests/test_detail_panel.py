import pytest
from PyQt6.QtWidgets import QApplication
from yt_downloader_gui.ui.detail_panel import DetailPanel
from yt_downloader_gui.core.models import QueueItem, ItemStatus

SAMPLE_MEDIA_INFO = {
    "resolutions": ["Best available", "1080p", "720p"],
    "formats_by_resolution": {
        "1080p": ["Best available", "mp4 (avc1, 30fps)"],
        "720p":  ["Best available", "webm (vp9, 30fps)"],
    },
    "audio_tracks": ["(best)", "en", "ja"],
    "subtitle_langs": ["en", "en-auto", "fr"],
}


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def panel(qapp, qtbot):
    p = DetailPanel()
    qtbot.addWidget(p)
    return p


def test_panel_shows_loading_state(panel):
    panel.set_loading()
    assert panel._resolution_combo.currentText() == "Loading…"
    assert not panel._resolution_combo.isEnabled()


def test_populate_media_info_fills_resolutions(panel):
    item = QueueItem(url="https://example.com/watch?v=abc")
    item.resolutions = SAMPLE_MEDIA_INFO["resolutions"]
    item.formats_by_resolution = SAMPLE_MEDIA_INFO["formats_by_resolution"]
    item.audio_tracks = SAMPLE_MEDIA_INFO["audio_tracks"]
    item.subtitle_langs = SAMPLE_MEDIA_INFO["subtitle_langs"]
    panel.load_item(item)
    texts = [panel._resolution_combo.itemText(i) for i in range(panel._resolution_combo.count())]
    assert "Best available" in texts
    assert "1080p" in texts
    assert "720p" in texts


def test_resolution_change_updates_codec_combo(panel):
    item = QueueItem(url="https://example.com/watch?v=abc")
    item.resolutions = SAMPLE_MEDIA_INFO["resolutions"]
    item.formats_by_resolution = SAMPLE_MEDIA_INFO["formats_by_resolution"]
    item.audio_tracks = SAMPLE_MEDIA_INFO["audio_tracks"]
    item.subtitle_langs = SAMPLE_MEDIA_INFO["subtitle_langs"]
    panel.load_item(item)
    panel._resolution_combo.setCurrentText("1080p")
    texts = [panel._codec_combo.itemText(i) for i in range(panel._codec_combo.count())]
    assert "mp4 (avc1, 30fps)" in texts
    assert "webm (vp9, 30fps)" not in texts


def test_audio_track_combo_populated(panel):
    item = QueueItem(url="https://example.com/watch?v=abc")
    item.audio_tracks = SAMPLE_MEDIA_INFO["audio_tracks"]
    item.resolutions = SAMPLE_MEDIA_INFO["resolutions"]
    item.formats_by_resolution = SAMPLE_MEDIA_INFO["formats_by_resolution"]
    item.subtitle_langs = SAMPLE_MEDIA_INFO["subtitle_langs"]
    panel.load_item(item)
    texts = [panel._audio_track_combo.itemText(i) for i in range(panel._audio_track_combo.count())]
    assert "(best)" in texts
    assert "en" in texts
    assert "ja" in texts


def test_subtitle_combo_has_none_and_langs(panel):
    item = QueueItem(url="https://example.com/watch?v=abc")
    item.subtitle_langs = SAMPLE_MEDIA_INFO["subtitle_langs"]
    item.resolutions = SAMPLE_MEDIA_INFO["resolutions"]
    item.formats_by_resolution = SAMPLE_MEDIA_INFO["formats_by_resolution"]
    item.audio_tracks = SAMPLE_MEDIA_INFO["audio_tracks"]
    panel.load_item(item)
    texts = [panel._subtitle_combo.itemText(i) for i in range(panel._subtitle_combo.count())]
    assert "none" in texts
    assert "en" in texts
    assert "en-auto" in texts


def test_embed_subs_disabled_when_subtitle_none(panel):
    item = QueueItem(url="https://example.com/watch?v=abc")
    item.subtitle_langs = ["en"]
    item.resolutions = []; item.formats_by_resolution = {}; item.audio_tracks = []
    panel.load_item(item)
    panel._subtitle_combo.setCurrentText("none")
    assert not panel._embed_subs_check.isEnabled()


def test_embed_subs_enabled_when_subtitle_selected(panel):
    item = QueueItem(url="https://example.com/watch?v=abc")
    item.subtitle_langs = ["en"]
    item.resolutions = []; item.formats_by_resolution = {}; item.audio_tracks = []
    panel.load_item(item)
    panel._subtitle_combo.setCurrentText("en")
    assert panel._embed_subs_check.isEnabled()


def test_audio_only_disables_video_controls(panel):
    item = QueueItem(url="https://example.com/watch?v=abc")
    item.resolutions = SAMPLE_MEDIA_INFO["resolutions"]
    item.formats_by_resolution = SAMPLE_MEDIA_INFO["formats_by_resolution"]
    item.audio_tracks = SAMPLE_MEDIA_INFO["audio_tracks"]
    item.subtitle_langs = SAMPLE_MEDIA_INFO["subtitle_langs"]
    panel.load_item(item)
    panel._audio_only_check.setChecked(True)
    assert not panel._resolution_combo.isEnabled()
    assert not panel._codec_combo.isEnabled()
    assert panel._audio_fmt_combo.isEnabled()
    assert panel._audio_quality_combo.isEnabled()


def test_audio_only_unchecked_enables_video_controls(panel):
    item = QueueItem(url="https://example.com/watch?v=abc")
    item.resolutions = SAMPLE_MEDIA_INFO["resolutions"]
    item.formats_by_resolution = SAMPLE_MEDIA_INFO["formats_by_resolution"]
    item.audio_tracks = SAMPLE_MEDIA_INFO["audio_tracks"]
    item.subtitle_langs = SAMPLE_MEDIA_INFO["subtitle_langs"]
    panel.load_item(item)
    panel._audio_only_check.setChecked(True)
    panel._audio_only_check.setChecked(False)
    assert panel._resolution_combo.isEnabled()


def test_embed_subs_stays_disabled_after_audio_only_uncheck_with_no_subtitle(panel):
    item = QueueItem(url="https://example.com/watch?v=abc")
    item.resolutions = []; item.formats_by_resolution = {}
    item.audio_tracks = []; item.subtitle_langs = ["en"]
    panel.load_item(item)
    # subtitle is "none" (default), check then uncheck audio-only
    panel._audio_only_check.setChecked(True)
    panel._audio_only_check.setChecked(False)
    assert not panel._embed_subs_check.isEnabled()


def test_lock_controls_disables_all_new_widgets(panel):
    item = QueueItem(url="https://example.com/watch?v=abc")
    item.resolutions = []; item.formats_by_resolution = {}
    item.audio_tracks = []; item.subtitle_langs = []
    panel.load_item(item)
    panel.lock_controls()
    assert not panel._resolution_combo.isEnabled()
    assert not panel._codec_combo.isEnabled()
    assert not panel._audio_track_combo.isEnabled()
    assert not panel._subtitle_combo.isEnabled()
    assert not panel._embed_subs_check.isEnabled()
    assert not panel._audio_only_check.isEnabled()


def test_update_progress_sets_progress_bar(panel):
    panel.update_progress(72)
    assert panel._progress_bar.value() == 72


def test_append_log_adds_text(panel):
    panel._log_output.clear()
    panel.append_log("line one")
    panel.append_log("line two")
    text = panel._log_output.toPlainText()
    assert "line one" in text
    assert "line two" in text


def test_load_none_clears_panel(panel):
    panel.load_item(None)
    assert panel._title_label.text() == ""
    assert panel._progress_bar.value() == 0
