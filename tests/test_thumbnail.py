import json
import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QPixmap
from yt_downloader_gui.core.thumbnail import ThumbnailWorker
from yt_downloader_gui.core.thumbnail import parse_media_info


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


def _sample_formats():
    return [
        # video streams
        {"height": 1080, "ext": "mp4", "vcodec": "avc1.64002a", "acodec": "none", "fps": 30},
        {"height": 1080, "ext": "mp4", "vcodec": "avc1.64002a", "acodec": "none", "fps": 60},
        {"height": 720,  "ext": "mp4", "vcodec": "avc1.640028", "acodec": "none", "fps": 30},
        {"height": 720,  "ext": "webm","vcodec": "vp9",         "acodec": "none", "fps": 30},
        # audio streams
        {"height": None, "ext": "m4a", "vcodec": "none", "acodec": "mp4a.40.2", "language": "en", "fps": None},
        {"height": None, "ext": "m4a", "vcodec": "none", "acodec": "mp4a.40.2", "language": "ja", "fps": None},
        {"height": None, "ext": "m4a", "vcodec": "none", "acodec": "mp4a.40.2", "language": None, "fps": None},
    ]


def test_parse_resolutions():
    data = {"formats": _sample_formats(), "subtitles": {}, "automatic_captions": {}}
    info = parse_media_info(data)
    assert info["resolutions"] == ["Best available", "1080p", "720p"]


def test_parse_codecs_per_resolution():
    data = {"formats": _sample_formats(), "subtitles": {}, "automatic_captions": {}}
    info = parse_media_info(data)
    codecs_1080 = info["formats_by_resolution"]["1080p"]
    assert codecs_1080[0] == "Best available"
    assert "mp4 (avc1, 30fps)" in codecs_1080
    assert "mp4 (avc1, 60fps)" in codecs_1080
    codecs_720 = info["formats_by_resolution"]["720p"]
    assert "mp4 (avc1, 30fps)" in codecs_720
    assert "webm (vp9, 30fps)" in codecs_720


def test_parse_audio_tracks_skips_none_language():
    data = {"formats": _sample_formats(), "subtitles": {}, "automatic_captions": {}}
    info = parse_media_info(data)
    assert info["audio_tracks"] == ["(best)", "en", "ja"]


def test_parse_subtitle_langs():
    data = {
        "formats": [],
        "subtitles": {"en": [], "fr": []},
        "automatic_captions": {"en": [], "de": []},
    }
    info = parse_media_info(data)
    assert "en" in info["subtitle_langs"]
    assert "fr" in info["subtitle_langs"]
    assert "en-auto" in info["subtitle_langs"]
    assert "de-auto" in info["subtitle_langs"]


def test_parse_media_info_empty_formats():
    data = {"formats": [], "subtitles": {}, "automatic_captions": {}}
    info = parse_media_info(data)
    assert info["resolutions"] == ["Best available"]
    assert info["formats_by_resolution"] == {}
    assert info["audio_tracks"] == ["(best)"]
    assert info["subtitle_langs"] == []


def test_parse_media_info_missing_keys():
    info = parse_media_info({})
    assert info["resolutions"] == ["Best available"]
    assert info["audio_tracks"] == ["(best)"]
    assert info["subtitle_langs"] == []
