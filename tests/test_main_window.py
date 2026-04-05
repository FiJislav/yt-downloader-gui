import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from yt_downloader_gui.ui.main_window import MainWindow
from yt_downloader_gui.core.models import ItemStatus


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(qapp, qtbot):
    w = MainWindow(settings_org="YTDownloaderTest", settings_app="MainWindowTest")
    qtbot.addWidget(w)
    w.show()
    return w


def test_window_title(window):
    assert "YT Downloader" in window.windowTitle()


def test_add_url_adds_to_queue(window, qtbot):
    window._url_input.setText("https://example.com/watch?v=test1")
    with patch("yt_downloader_gui.ui.main_window.ThumbnailWorker") as MockWorker:
        mock_instance = MagicMock()
        MockWorker.return_value = mock_instance
        qtbot.mouseClick(window._add_btn, Qt.MouseButton.LeftButton)
    assert window._queue_panel.count() >= 1


def test_paste_from_clipboard_adds_url(window, qtbot, qapp):
    clipboard = qapp.clipboard()
    clipboard.setText("https://youtube.com/watch?v=clip1")
    with patch("yt_downloader_gui.ui.main_window.ThumbnailWorker") as MockWorker:
        mock_instance = MagicMock()
        MockWorker.return_value = mock_instance
        qtbot.mouseClick(window._paste_btn, Qt.MouseButton.LeftButton)
    assert any(
        window._queue_panel.item(i).queue_item.url == "https://youtube.com/watch?v=clip1"
        for i in range(window._queue_panel.count())
    )


def test_paste_ignores_non_url_clipboard(window, qtbot, qapp):
    count_before = window._queue_panel.count()
    clipboard = qapp.clipboard()
    clipboard.setText("not a url")
    qtbot.mouseClick(window._paste_btn, Qt.MouseButton.LeftButton)
    assert window._queue_panel.count() == count_before


def test_start_queue_button_exists(window):
    assert window._start_btn is not None


def test_stop_button_exists(window):
    assert window._stop_btn is not None


def test_update_ytdlp_button_exists(window):
    assert window._update_btn is not None


def test_browse_button_exists(window):
    assert window._browse_btn is not None
