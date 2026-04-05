import json
import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QPixmap
from yt_downloader_gui.core.thumbnail import ThumbnailWorker


@pytest.fixture(scope="session")
def qapp():
    return QCoreApplication.instance() or QCoreApplication([])


def _make_mock_result(title="Test Video", thumbnail_url="http://example.com/thumb.jpg", returncode=0):
    mock = MagicMock()
    mock.returncode = returncode
    mock.stdout = json.dumps({"title": title, "thumbnail": thumbnail_url})
    mock.stderr = ""
    return mock


def test_thumbnail_worker_emits_fetched_on_success(qapp, qtbot):
    worker = ThumbnailWorker("https://example.com/watch?v=abc")
    mock_result = _make_mock_result()
    # Fake 1x1 PNG bytes
    fake_img = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
        b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    mock_resp = MagicMock()
    mock_resp.read.return_value = fake_img
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("yt_downloader_gui.core.thumbnail.subprocess.run", return_value=mock_result), \
         patch("yt_downloader_gui.core.thumbnail.urllib.request.urlopen", return_value=mock_resp):
        titles = []
        pixmaps = []

        def on_fetched(t, p):
            titles.append(t)
            pixmaps.append(p)

        with qtbot.waitSignal(worker.fetched, timeout=3000):
            worker.fetched.connect(on_fetched)
            worker.start()

    assert titles == ["Test Video"]
    assert isinstance(pixmaps[0], QPixmap)


def test_thumbnail_worker_emits_failed_on_nonzero_exit(qapp, qtbot):
    worker = ThumbnailWorker("https://example.com/watch?v=bad")
    mock_result = _make_mock_result(returncode=1)
    mock_result.stderr = "ERROR: Unsupported URL"

    with patch("yt_downloader_gui.core.thumbnail.subprocess.run", return_value=mock_result):
        reasons = []
        worker.failed.connect(reasons.append)
        with qtbot.waitSignal(worker.failed, timeout=3000):
            worker.start()

    assert len(reasons) == 1
    assert "ERROR: Unsupported URL" in reasons[0]


def test_thumbnail_worker_emits_failed_on_exception(qapp, qtbot):
    worker = ThumbnailWorker("https://example.com/watch?v=exc")

    with patch("yt_downloader_gui.core.thumbnail.subprocess.run", side_effect=Exception("network error")):
        reasons = []
        worker.failed.connect(reasons.append)
        with qtbot.waitSignal(worker.failed, timeout=3000):
            worker.start()

    assert "network error" in reasons[0]
