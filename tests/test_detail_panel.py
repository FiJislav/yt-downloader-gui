import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap
from yt_downloader_gui.ui.detail_panel import DetailPanel
from yt_downloader_gui.core.models import QueueItem, ItemStatus


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def panel(qapp, qtbot):
    p = DetailPanel()
    qtbot.addWidget(p)
    return p


def test_panel_loads_item_url_as_title(panel):
    item = QueueItem(url="https://example.com/watch?v=abc", title="My Video")
    panel.load_item(item)
    assert panel._title_label.text() == "My Video"


def test_panel_loads_item_format(panel):
    item = QueueItem(url="https://example.com/watch?v=abc", fmt="mp3")
    panel.load_item(item)
    assert panel._fmt_combo.currentText() == "mp3"


def test_panel_loads_item_sub_lang(panel):
    item = QueueItem(url="https://example.com/watch?v=abc", sub_lang="fr")
    panel.load_item(item)
    assert panel._sub_lang_edit.text() == "fr"


def test_panel_loads_embed_subs_checkbox(panel):
    item = QueueItem(url="https://example.com/watch?v=abc", embed_subs=True)
    panel.load_item(item)
    assert panel._embed_subs_check.isChecked() is True


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


def test_lock_controls_disables_widgets(panel):
    item = QueueItem(url="https://example.com/watch?v=abc")
    panel.load_item(item)
    panel.lock_controls()
    assert panel._fmt_combo.isEnabled() is False
    assert panel._audio_lang_edit.isEnabled() is False
    assert panel._sub_lang_edit.isEnabled() is False
    assert panel._embed_subs_check.isEnabled() is False


def test_unlock_controls_enables_widgets(panel):
    item = QueueItem(url="https://example.com/watch?v=abc")
    panel.load_item(item)
    panel.lock_controls()
    panel.unlock_controls()
    assert panel._fmt_combo.isEnabled() is True


def test_load_none_clears_panel(panel):
    panel.load_item(None)
    assert panel._title_label.text() == ""
    assert panel._progress_bar.value() == 0
