import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtCore import QCoreApplication
from yt_downloader_gui.core.updater import UpdaterWorker


@pytest.fixture(scope="session")
def qapp():
    return QCoreApplication.instance() or QCoreApplication([])


def test_updater_emits_success_message(qapp, qtbot):
    worker = UpdaterWorker()
    mock_result = MagicMock()
    mock_result.stdout = "yt-dlp is up to date (2024.01.01)\n"
    mock_result.stderr = ""

    with patch("yt_downloader_gui.core.updater.subprocess.run", return_value=mock_result):
        results = []
        worker.result.connect(results.append)
        with qtbot.waitSignal(worker.result, timeout=3000):
            worker.start()

    assert "yt-dlp is up to date" in results[0]


def test_updater_emits_error_on_exception(qapp, qtbot):
    worker = UpdaterWorker()

    with patch("yt_downloader_gui.core.updater.subprocess.run", side_effect=Exception("not found")):
        results = []
        worker.result.connect(results.append)
        with qtbot.waitSignal(worker.result, timeout=3000):
            worker.start()

    assert "Error" in results[0]
