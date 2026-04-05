import pytest
from PyQt6.QtWidgets import QApplication
from yt_downloader_gui.ui.queue_panel import QueuePanel
from yt_downloader_gui.core.models import ItemStatus


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def panel(qapp, qtbot):
    p = QueuePanel()
    qtbot.addWidget(p)
    return p


def test_add_item_creates_list_entry(panel):
    panel.add_item("https://example.com/watch?v=abc")
    assert panel.count() == 1


def test_added_item_has_correct_url(panel):
    panel.add_item("https://example.com/watch?v=xyz")
    item = panel.item(panel.count() - 1)
    assert item.queue_item.url == "https://example.com/watch?v=xyz"


def test_added_item_default_status_is_pending(panel):
    panel.add_item("https://example.com/watch?v=def")
    item = panel.item(panel.count() - 1)
    assert item.queue_item.status == ItemStatus.PENDING


def test_next_pending_returns_first_pending(panel):
    panel.clear()
    panel.add_item("https://example.com/1")
    panel.add_item("https://example.com/2")
    result = panel.next_pending()
    assert result is not None
    assert result.queue_item.url == "https://example.com/1"


def test_next_pending_skips_non_pending(panel):
    panel.clear()
    panel.add_item("https://example.com/done")
    panel.item(0).queue_item.status = ItemStatus.DONE
    panel.item(0).refresh()
    panel.add_item("https://example.com/pending")
    result = panel.next_pending()
    assert result.queue_item.url == "https://example.com/pending"


def test_next_pending_returns_none_when_all_done(panel):
    panel.clear()
    panel.add_item("https://example.com/done")
    panel.item(0).queue_item.status = ItemStatus.DONE
    panel.item(0).refresh()
    assert panel.next_pending() is None


def test_item_display_text_shows_status_icon(panel):
    panel.clear()
    panel.add_item("https://example.com/watch?v=abc")
    text = panel.item(0).text()
    assert "○" in text


def test_item_display_text_shows_format(panel):
    panel.clear()
    panel.add_item("https://example.com/watch?v=abc")
    assert "mp4" in panel.item(0).text()
