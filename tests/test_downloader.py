import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtCore import QCoreApplication

from yt_downloader_gui.core.models import QueueItem
from yt_downloader_gui.core.downloader import build_args, DownloadWorker


def _item(**kwargs) -> QueueItem:
    return QueueItem(url="https://example.com/watch?v=abc", **kwargs)


# ---------------------------------------------------------------------------
# build_args — audio-only mode
# ---------------------------------------------------------------------------

def test_audio_only_mp3_best_quality():
    item = _item(audio_only=True, audio_fmt="mp3", audio_quality="(best quality)")
    args = build_args(item, output_dir="")
    assert "--extract-audio" in args
    assert "--audio-format" in args
    assert "mp3" in args
    assert "--audio-quality" in args
    assert "0" in args


def test_audio_only_m4a_320k():
    item = _item(audio_only=True, audio_fmt="m4a", audio_quality="320k")
    args = build_args(item, output_dir="")
    assert "--audio-format" in args
    assert "m4a" in args
    assert "320k" in args


def test_audio_only_best_omits_audio_format_flag():
    item = _item(audio_only=True, audio_fmt="best", audio_quality="(best quality)")
    args = build_args(item, output_dir="")
    assert "--extract-audio" in args
    assert "--audio-format" not in args
    assert "--audio-quality" in args
    assert "0" in args


def test_audio_only_url_is_last():
    item = _item(audio_only=True, audio_fmt="mp3")
    args = build_args(item, output_dir="")
    assert args[-1] == "https://example.com/watch?v=abc"


# ---------------------------------------------------------------------------
# build_args — video mode resolutions
# ---------------------------------------------------------------------------

def test_video_best_available():
    item = _item(resolution="Best available", codec="Best available")
    args = build_args(item, output_dir="")
    assert "-f" in args
    f_val = args[args.index("-f") + 1]
    assert "bestvideo" in f_val
    assert "bestaudio" in f_val
    assert "height" not in f_val


def test_video_resolution_no_codec():
    item = _item(resolution="1080p", codec="Best available")
    args = build_args(item, output_dir="")
    f_val = args[args.index("-f") + 1]
    assert "height<=1080" in f_val
    assert "bestaudio" in f_val


def test_video_resolution_and_codec():
    item = _item(resolution="1080p", codec="mp4 (avc1, 30fps)")
    args = build_args(item, output_dir="")
    f_val = args[args.index("-f") + 1]
    assert "height<=1080" in f_val
    assert "ext=mp4" in f_val
    assert "avc1" in f_val


def test_video_mp4_merge_format():
    item = _item(resolution="1080p", codec="mp4 (avc1, 30fps)")
    args = build_args(item, output_dir="")
    assert "--merge-output-format" in args
    assert args[args.index("--merge-output-format") + 1] == "mp4"


def test_video_webm_merge_format_is_mkv():
    item = _item(resolution="720p", codec="webm (vp9, 30fps)")
    args = build_args(item, output_dir="")
    assert "--merge-output-format" in args
    assert args[args.index("--merge-output-format") + 1] == "mkv"


def test_video_best_available_merge_format_is_mp4():
    item = _item(resolution="Best available", codec="Best available")
    args = build_args(item, output_dir="")
    assert "--merge-output-format" in args
    assert args[args.index("--merge-output-format") + 1] == "mp4"


def test_video_resolution_only_merge_format_is_mp4():
    item = _item(resolution="1080p", codec="Best available")
    args = build_args(item, output_dir="")
    assert "--merge-output-format" in args
    assert args[args.index("--merge-output-format") + 1] == "mp4"


# ---------------------------------------------------------------------------
# build_args — subtitles
# ---------------------------------------------------------------------------

def test_no_subtitles_when_subtitle_lang_empty():
    item = _item(subtitle_lang="")
    args = build_args(item, output_dir="")
    assert "--write-subs" not in args
    assert "--write-auto-subs" not in args


def test_regular_subtitle():
    item = _item(subtitle_lang="fr")
    args = build_args(item, output_dir="")
    assert "--write-subs" in args
    assert "--sub-lang" in args
    assert "fr" in args
    assert "--write-auto-subs" not in args


def test_auto_subtitle_strips_suffix():
    item = _item(subtitle_lang="en-auto")
    args = build_args(item, output_dir="")
    assert "--write-auto-subs" in args
    assert "--sub-lang" in args
    assert "en" in args
    assert "en-auto" not in args


def test_embed_subs():
    item = _item(subtitle_lang="en", embed_subs=True)
    args = build_args(item, output_dir="")
    assert "--embed-subs" in args


def test_no_embed_subs_without_subtitle_lang():
    item = _item(subtitle_lang="", embed_subs=True)
    args = build_args(item, output_dir="")
    assert "--embed-subs" not in args


# ---------------------------------------------------------------------------
# build_args — audio track selection
# ---------------------------------------------------------------------------

def test_audio_track_best_not_added_to_format():
    item = _item(resolution="1080p", codec="Best available", audio_track="(best)")
    args = build_args(item, output_dir="")
    f_val = args[args.index("-f") + 1]
    assert "language" not in f_val


def test_audio_track_specific_lang():
    item = _item(resolution="1080p", codec="Best available", audio_track="ja")
    args = build_args(item, output_dir="")
    f_val = args[args.index("-f") + 1]
    assert "language=ja" in f_val


# ---------------------------------------------------------------------------
# build_args — output dir
# ---------------------------------------------------------------------------

def test_output_dir_added():
    item = _item()
    args = build_args(item, output_dir="C:/Videos")
    assert "-o" in args
    assert "C:/Videos/%(uploader)s - %(title)s.%(ext)s" in args


def test_url_is_last():
    item = _item()
    args = build_args(item, output_dir="")
    assert args[-1] == "https://example.com/watch?v=abc"


# ---------------------------------------------------------------------------
# DownloadWorker tests (unchanged logic, new QueueItem fields)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def qapp():
    return QCoreApplication.instance() or QCoreApplication([])


def test_download_worker_emits_progress(qapp, qtbot):
    item = _item()
    worker = DownloadWorker(item, output_dir="")

    mock_proc = MagicMock()
    mock_proc.stdout = iter([
        "[download]  50.0% of  10.00MiB\n",
        "[download] 100% of  10.00MiB\n",
    ])
    mock_proc.wait.return_value = None
    mock_proc.returncode = 0

    with patch("yt_downloader_gui.core.downloader.subprocess.Popen", return_value=mock_proc):
        progress_values = []
        worker.progress.connect(progress_values.append)
        with qtbot.waitSignal(worker.finished, timeout=3000):
            worker.start()

    assert 50 in progress_values
    assert 100 in progress_values


def test_download_worker_emits_log_lines(qapp, qtbot):
    item = _item()
    worker = DownloadWorker(item, output_dir="")

    mock_proc = MagicMock()
    mock_proc.stdout = iter(["[youtube] Fetching...\n", "[download] Destination: foo.mp4\n"])
    mock_proc.wait.return_value = None
    mock_proc.returncode = 0

    with patch("yt_downloader_gui.core.downloader.subprocess.Popen", return_value=mock_proc):
        lines = []
        worker.log_line.connect(lines.append)
        with qtbot.waitSignal(worker.finished, timeout=3000):
            worker.start()

    assert "[youtube] Fetching..." in lines


def test_download_worker_emits_error_on_nonzero_exit(qapp, qtbot):
    item = _item()
    worker = DownloadWorker(item, output_dir="")

    mock_proc = MagicMock()
    mock_proc.stdout = iter([])
    mock_proc.wait.return_value = None
    mock_proc.returncode = 1

    with patch("yt_downloader_gui.core.downloader.subprocess.Popen", return_value=mock_proc):
        errors = []
        worker.error.connect(errors.append)
        with qtbot.waitSignal(worker.error, timeout=3000):
            worker.start()

    assert len(errors) == 1
    assert "1" in errors[0]


def test_download_worker_stop_terminates_process(qapp, qtbot):
    item = _item()
    worker = DownloadWorker(item, output_dir="")

    mock_proc = MagicMock()
    mock_proc.stdout = iter([])
    mock_proc.wait.return_value = None
    mock_proc.returncode = 0

    with patch("yt_downloader_gui.core.downloader.subprocess.Popen", return_value=mock_proc):
        with qtbot.waitSignal(worker.finished, timeout=3000):
            worker.start()
        worker.stop()

    mock_proc.terminate.assert_called_once()
