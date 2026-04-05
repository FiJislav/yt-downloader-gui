# YT Downloader GUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a PyQt6 desktop GUI that wraps yt-dlp with a download queue, per-item format/language/subtitle settings, real-time progress, thumbnail preview, clipboard paste, and a yt-dlp updater.

**Architecture:** Split-panel `QMainWindow` — left panel is a `QListWidget` queue, right panel shows per-item controls + progress + log. Core workers run in `QThread` subclasses and communicate via Qt signals. Shared state is a `QueueItem` dataclass stored inside each `QListWidgetItem`.

**Tech Stack:** Python 3.11+, PyQt6, yt-dlp (CLI tool), pytest, pytest-qt, unittest.mock

---

## File Map

| File | Responsibility |
|---|---|
| `yt_downloader_gui/main.py` | Entry point: yt-dlp PATH check, QApplication, show MainWindow |
| `yt_downloader_gui/core/models.py` | `QueueItem` dataclass, `ItemStatus` enum |
| `yt_downloader_gui/core/settings.py` | `AppSettings`: QSettings wrapper for output dir + window geometry |
| `yt_downloader_gui/core/downloader.py` | `build_args()` pure function + `DownloadWorker(QThread)` |
| `yt_downloader_gui/core/thumbnail.py` | `ThumbnailWorker(QThread)`: fetch title + thumbnail via yt-dlp --dump-json |
| `yt_downloader_gui/core/updater.py` | `UpdaterWorker(QThread)`: run yt-dlp -U |
| `yt_downloader_gui/ui/queue_panel.py` | `QueueListItem(QListWidgetItem)` + `QueuePanel(QListWidget)` |
| `yt_downloader_gui/ui/detail_panel.py` | `DetailPanel(QWidget)`: thumbnail, controls, progress bar, log |
| `yt_downloader_gui/ui/main_window.py` | `MainWindow(QMainWindow)`: URL bar, splitter, bottom bar, wires all signals |
| `tests/test_models.py` | Unit tests for QueueItem defaults and mutations |
| `tests/test_settings.py` | Unit tests for AppSettings read/write |
| `tests/test_downloader.py` | Unit tests for build_args + mocked DownloadWorker signals |
| `tests/test_thumbnail.py` | Mocked ThumbnailWorker signal tests |
| `tests/test_updater.py` | Mocked UpdaterWorker signal tests |
| `tests/test_queue_panel.py` | pytest-qt tests for QueuePanel |
| `tests/test_detail_panel.py` | pytest-qt tests for DetailPanel |
| `tests/test_main_window.py` | pytest-qt smoke tests for MainWindow |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `yt_downloader_gui/__init__.py`
- Create: `yt_downloader_gui/core/__init__.py`
- Create: `yt_downloader_gui/ui/__init__.py`
- Create: `tests/__init__.py`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`

- [ ] **Step 1: Create the directory structure**

```bash
mkdir -p yt_downloader_gui/core yt_downloader_gui/ui tests
```

- [ ] **Step 2: Create empty `__init__.py` files**

Create `yt_downloader_gui/__init__.py`, `yt_downloader_gui/core/__init__.py`, `yt_downloader_gui/ui/__init__.py`, `tests/__init__.py` — all empty.

- [ ] **Step 3: Create `requirements.txt`**

```
PyQt6>=6.4.0
yt-dlp>=2023.1.1
```

- [ ] **Step 4: Create `requirements-dev.txt`**

```
-r requirements.txt
pytest>=7.0
pytest-qt>=4.0
```

- [ ] **Step 5: Install dependencies**

```bash
pip install -r requirements-dev.txt
```

Expected: packages install without error.

- [ ] **Step 6: Verify pytest-qt works**

```bash
python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 OK')"
```

Expected: `PyQt6 OK`

- [ ] **Step 7: Commit**

```bash
git add yt_downloader_gui/ tests/ requirements.txt requirements-dev.txt
git commit -m "chore: scaffold project structure"
```

---

## Task 2: `core/models.py` — QueueItem & ItemStatus

**Files:**
- Create: `yt_downloader_gui/core/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_models.py`:

```python
from yt_downloader_gui.core.models import QueueItem, ItemStatus


def test_queue_item_defaults():
    item = QueueItem(url="https://example.com/watch?v=abc")
    assert item.fmt == "mp4"
    assert item.audio_lang == ""
    assert item.sub_lang == "en"
    assert item.embed_subs is False
    assert item.status == ItemStatus.PENDING
    assert item.title == ""
    assert item.thumbnail is None
    assert item.log == ""


def test_queue_item_custom_format():
    item = QueueItem(url="https://example.com/watch?v=abc", fmt="mp3")
    assert item.fmt == "mp3"


def test_item_status_values():
    assert ItemStatus.PENDING.value == "pending"
    assert ItemStatus.ACTIVE.value == "active"
    assert ItemStatus.DONE.value == "done"
    assert ItemStatus.ERROR.value == "error"
    assert ItemStatus.STOPPED.value == "stopped"


def test_queue_item_log_accumulation():
    item = QueueItem(url="https://example.com/watch?v=abc")
    item.log += "line1\n"
    item.log += "line2\n"
    assert item.log == "line1\nline2\n"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_models.py -v
```

Expected: `ModuleNotFoundError` or `ImportError`

- [ ] **Step 3: Implement `core/models.py`**

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# QPixmap import is deferred to avoid requiring a QApplication at module load time.
# Type hint uses string to avoid circular import issues in tests.


class ItemStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DONE = "done"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class QueueItem:
    url: str
    fmt: str = "mp4"
    audio_lang: str = ""
    sub_lang: str = "en"
    embed_subs: bool = False
    status: ItemStatus = field(default=ItemStatus.PENDING)
    title: str = ""
    thumbnail: Optional[object] = None  # QPixmap at runtime, None in tests
    log: str = ""
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_models.py -v
```

Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add yt_downloader_gui/core/models.py tests/test_models.py
git commit -m "feat: add QueueItem dataclass and ItemStatus enum"
```

---

## Task 3: `core/settings.py` — AppSettings

**Files:**
- Create: `yt_downloader_gui/core/settings.py`
- Create: `tests/test_settings.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_settings.py`:

```python
import pytest
from PyQt6.QtCore import QSettings
from yt_downloader_gui.core.settings import AppSettings


@pytest.fixture(autouse=True)
def clean_settings():
    # Use a test-specific org/app name so tests don't pollute real settings
    qs = QSettings("YTDownloaderTest", "YTDownloaderGUITest")
    qs.clear()
    yield
    qs.clear()


@pytest.fixture
def settings():
    return AppSettings(org="YTDownloaderTest", app="YTDownloaderGUITest")


def test_default_output_dir(settings, tmp_path, monkeypatch):
    from pathlib import Path
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    s = AppSettings(org="YTDownloaderTest", app="YTDownloaderGUITest")
    assert s.output_dir == str(tmp_path / "Downloads")


def test_set_and_get_output_dir(settings):
    settings.output_dir = "C:/Videos"
    assert settings.output_dir == "C:/Videos"


def test_save_and_load_geometry(settings):
    data = b"\x01\x02\x03\x04"
    settings.save_geometry(data)
    assert settings.load_geometry() == data


def test_load_geometry_returns_none_when_unset(settings):
    assert settings.load_geometry() is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_settings.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `core/settings.py`**

```python
from pathlib import Path
from PyQt6.QtCore import QSettings


class AppSettings:
    def __init__(self, org: str = "YTDownloader", app: str = "YTDownloaderGUI"):
        self._qs = QSettings(org, app)

    @property
    def output_dir(self) -> str:
        default = str(Path.home() / "Downloads")
        return self._qs.value("output_dir", default)

    @output_dir.setter
    def output_dir(self, value: str) -> None:
        self._qs.setValue("output_dir", value)

    def save_geometry(self, geometry: bytes) -> None:
        self._qs.setValue("geometry", geometry)

    def load_geometry(self) -> bytes | None:
        return self._qs.value("geometry", None)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_settings.py -v
```

Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add yt_downloader_gui/core/settings.py tests/test_settings.py
git commit -m "feat: add AppSettings QSettings wrapper"
```

---

## Task 4: `core/downloader.py` — `build_args` function

**Files:**
- Create: `yt_downloader_gui/core/downloader.py` (partial — build_args only)
- Create: `tests/test_downloader.py` (partial)

- [ ] **Step 1: Write the failing tests**

Create `tests/test_downloader.py`:

```python
from yt_downloader_gui.core.models import QueueItem
from yt_downloader_gui.core.downloader import build_args


def _item(**kwargs) -> QueueItem:
    return QueueItem(url="https://example.com/watch?v=abc", **kwargs)


def test_mp4_args():
    args = build_args(_item(fmt="mp4"), output_dir="")
    assert args == ["yt-dlp", "-f", "best", "https://example.com/watch?v=abc"]


def test_mp3_args():
    args = build_args(_item(fmt="mp3"), output_dir="")
    assert args == [
        "yt-dlp", "-f", "bestaudio",
        "--extract-audio", "--audio-format", "mp3", "--audio-quality", "0",
        "https://example.com/watch?v=abc",
    ]


def test_mp3_with_audio_lang():
    args = build_args(_item(fmt="mp3", audio_lang="ja"), output_dir="")
    assert "-f" in args
    assert "bestaudio[lang=ja]" in args


def test_mkv_args():
    args = build_args(_item(fmt="mkv"), output_dir="")
    assert "--merge-output-format" in args
    assert "mkv" in args
    assert "bestvideo+bestaudio" in args


def test_4k_args():
    args = build_args(_item(fmt="4k"), output_dir="")
    assert "--merge-output-format" in args
    assert "mp4" in args
    assert any("height<=2160" in a for a in args)


def test_4k_no_av1_args():
    args = build_args(_item(fmt="4k-no-av1"), output_dir="")
    assert any("vcodec!=av01" in a for a in args)


def test_subs_args():
    args = build_args(_item(fmt="subs", sub_lang="fr"), output_dir="")
    assert "--write-subs" in args
    assert "--sub-lang" in args
    assert "fr" in args


def test_embed_subs_format_args():
    args = build_args(_item(fmt="embed-subs", sub_lang="en"), output_dir="")
    assert "--embed-subs" in args
    assert "--merge-output-format" in args
    assert "mp4" in args


def test_embed_subs_checkbox_on_mp4():
    args = build_args(_item(fmt="mp4", embed_subs=True, sub_lang="de"), output_dir="")
    assert "--embed-subs" in args
    assert "de" in args


def test_embed_subs_checkbox_not_duplicated_on_embed_subs_format():
    args = build_args(_item(fmt="embed-subs", embed_subs=True), output_dir="")
    assert args.count("--embed-subs") == 1


def test_output_dir_added():
    args = build_args(_item(fmt="mp4"), output_dir="C:/Videos")
    assert "-o" in args
    assert "C:/Videos/%(title)s.%(ext)s" in args


def test_url_is_last_arg():
    args = build_args(_item(fmt="mp4"), output_dir="")
    assert args[-1] == "https://example.com/watch?v=abc"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_downloader.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `build_args` in `core/downloader.py`**

```python
import re
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

from yt_downloader_gui.core.models import QueueItem

PROGRESS_RE = re.compile(r"\[download\]\s+(\d+(?:\.\d+)?)%")

FORMATS = ["mp4", "mp3", "mkv", "4k", "4k-no-av1", "subs", "embed-subs"]


def build_args(item: QueueItem, output_dir: str) -> list[str]:
    """Build the yt-dlp CLI argument list for a QueueItem."""
    audio_sel = f"bestaudio[lang={item.audio_lang}]" if item.audio_lang else "bestaudio"
    args = ["yt-dlp"]

    if item.fmt == "mp3":
        args += ["-f", audio_sel, "--extract-audio", "--audio-format", "mp3", "--audio-quality", "0"]
    elif item.fmt == "mp4":
        args += ["-f", "best"]
    elif item.fmt == "mkv":
        args += ["-f", f"bestvideo+{audio_sel}", "--merge-output-format", "mkv"]
    elif item.fmt == "4k":
        args += ["-f", f"bestvideo[height<=2160]+{audio_sel}/best", "--merge-output-format", "mp4"]
    elif item.fmt == "4k-no-av1":
        args += ["-f", f"bestvideo[height>=2160][vcodec!=av01]+{audio_sel}/best", "--merge-output-format", "mkv"]
    elif item.fmt == "subs":
        args += ["--write-subs", "--sub-lang", item.sub_lang, "--convert-subs", "srt"]
    elif item.fmt == "embed-subs":
        args += [
            "-f", f"bestvideo+{audio_sel}", "--merge-output-format", "mp4",
            "--embed-subs", "--sub-lang", item.sub_lang, "--convert-subs", "srt",
        ]

    # Embed subs checkbox applies to formats that don't already handle subs
    if item.embed_subs and item.fmt not in ("subs", "embed-subs"):
        args += ["--embed-subs", "--sub-lang", item.sub_lang, "--convert-subs", "srt"]

    if output_dir:
        args += ["-o", f"{output_dir}/%(title)s.%(ext)s"]

    args.append(item.url)
    return args
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_downloader.py -v
```

Expected: 13 tests PASS

- [ ] **Step 5: Commit**

```bash
git add yt_downloader_gui/core/downloader.py tests/test_downloader.py
git commit -m "feat: add build_args function with full format support"
```

---

## Task 5: `core/downloader.py` — `DownloadWorker`

**Files:**
- Modify: `yt_downloader_gui/core/downloader.py` (add DownloadWorker class)
- Modify: `tests/test_downloader.py` (add worker tests)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_downloader.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtCore import QCoreApplication
from yt_downloader_gui.core.downloader import DownloadWorker


@pytest.fixture(scope="session")
def qapp():
    app = QCoreApplication.instance() or QCoreApplication([])
    return app


def test_download_worker_emits_progress(qapp, qtbot):
    item = _item(fmt="mp4")
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
    item = _item(fmt="mp4")
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
    item = _item(fmt="mp4")
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
    item = _item(fmt="mp4")
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_downloader.py::test_download_worker_emits_progress -v
```

Expected: `AttributeError: module has no attribute 'DownloadWorker'`

- [ ] **Step 3: Implement `DownloadWorker` in `core/downloader.py`**

Append to `yt_downloader_gui/core/downloader.py` (after `build_args`):

```python
class DownloadWorker(QThread):
    progress = pyqtSignal(int)
    log_line = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, item: QueueItem, output_dir: str, parent=None):
        super().__init__(parent)
        self._item = item
        self._output_dir = output_dir
        self._process: subprocess.Popen | None = None

    def run(self) -> None:
        args = build_args(self._item, self._output_dir)
        try:
            self._process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            for line in self._process.stdout:
                line = line.rstrip()
                self.log_line.emit(line)
                m = PROGRESS_RE.search(line)
                if m:
                    self.progress.emit(int(float(m.group(1))))
            self._process.wait()
            if self._process.returncode == 0:
                self.finished.emit()
            else:
                self.error.emit(f"yt-dlp exited with code {self._process.returncode}")
        except Exception as exc:
            self.error.emit(str(exc))

    def stop(self) -> None:
        if self._process is not None:
            self._process.terminate()
```

- [ ] **Step 4: Run all downloader tests**

```bash
pytest tests/test_downloader.py -v
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add yt_downloader_gui/core/downloader.py tests/test_downloader.py
git commit -m "feat: add DownloadWorker QThread with progress/log/error signals"
```

---

## Task 6: `core/thumbnail.py` — ThumbnailWorker

**Files:**
- Create: `yt_downloader_gui/core/thumbnail.py`
- Create: `tests/test_thumbnail.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_thumbnail.py`:

```python
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
        worker.fetched.connect(lambda t, p: (titles.append(t), pixmaps.append(p)))
        with qtbot.waitSignal(worker.fetched, timeout=3000):
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


def test_thumbnail_worker_emits_failed_on_exception(qapp, qtbot):
    worker = ThumbnailWorker("https://example.com/watch?v=exc")

    with patch("yt_downloader_gui.core.thumbnail.subprocess.run", side_effect=Exception("network error")):
        reasons = []
        worker.failed.connect(reasons.append)
        with qtbot.waitSignal(worker.failed, timeout=3000):
            worker.start()

    assert "network error" in reasons[0]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_thumbnail.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `core/thumbnail.py`**

```python
import json
import subprocess
import urllib.request

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QPixmap


class ThumbnailWorker(QThread):
    fetched = pyqtSignal(str, QPixmap)   # title, pixmap
    failed = pyqtSignal(str)             # error reason

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self._url = url

    def run(self) -> None:
        try:
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-playlist", self._url],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                self.failed.emit(result.stderr.strip() or "yt-dlp --dump-json failed")
                return

            data = json.loads(result.stdout)
            title = data.get("title", self._url)
            thumb_url = data.get("thumbnail", "")

            pixmap = QPixmap()
            if thumb_url:
                with urllib.request.urlopen(thumb_url, timeout=10) as resp:
                    img_data = resp.read()
                pixmap.loadFromData(img_data)

            self.fetched.emit(title, pixmap)
        except Exception as exc:
            self.failed.emit(str(exc))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_thumbnail.py -v
```

Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add yt_downloader_gui/core/thumbnail.py tests/test_thumbnail.py
git commit -m "feat: add ThumbnailWorker for background title/thumbnail fetch"
```

---

## Task 7: `core/updater.py` — UpdaterWorker

**Files:**
- Create: `yt_downloader_gui/core/updater.py`
- Create: `tests/test_updater.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_updater.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_updater.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `core/updater.py`**

```python
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal


class UpdaterWorker(QThread):
    result = pyqtSignal(str)

    def run(self) -> None:
        try:
            proc = subprocess.run(
                ["yt-dlp", "-U"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = (proc.stdout + proc.stderr).strip()
            self.result.emit(output or "Update complete.")
        except Exception as exc:
            self.result.emit(f"Error: {exc}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_updater.py -v
```

Expected: 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add yt_downloader_gui/core/updater.py tests/test_updater.py
git commit -m "feat: add UpdaterWorker for yt-dlp self-update"
```

---

## Task 8: `ui/queue_panel.py` — Queue List

**Files:**
- Create: `yt_downloader_gui/ui/queue_panel.py`
- Create: `tests/test_queue_panel.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_queue_panel.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_queue_panel.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `ui/queue_panel.py`**

```python
from __future__ import annotations
from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from yt_downloader_gui.core.models import QueueItem, ItemStatus

_STATUS_ICONS = {
    ItemStatus.PENDING: "○",
    ItemStatus.ACTIVE: "●",
    ItemStatus.DONE: "✓",
    ItemStatus.ERROR: "✗",
    ItemStatus.STOPPED: "✗",
}


class QueueListItem(QListWidgetItem):
    def __init__(self, queue_item: QueueItem):
        super().__init__()
        self.queue_item = queue_item
        self.refresh()

    def refresh(self) -> None:
        url = self.queue_item.url
        short_url = url[:45] + "…" if len(url) > 45 else url
        icon = _STATUS_ICONS[self.queue_item.status]
        self.setText(f"{icon}  {short_url}  [{self.queue_item.fmt}]")
        if self.queue_item.title:
            self.setToolTip(self.queue_item.title)


class QueuePanel(QListWidget):
    def add_item(self, url: str) -> QueueListItem:
        queue_item = QueueItem(url=url)
        list_item = QueueListItem(queue_item)
        self.addItem(list_item)
        return list_item

    def next_pending(self) -> QueueListItem | None:
        for i in range(self.count()):
            item = self.item(i)
            if item.queue_item.status == ItemStatus.PENDING:
                return item
        return None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_queue_panel.py -v
```

Expected: 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add yt_downloader_gui/ui/queue_panel.py tests/test_queue_panel.py
git commit -m "feat: add QueuePanel and QueueListItem with status icons"
```

---

## Task 9: `ui/detail_panel.py` — Detail Panel

**Files:**
- Create: `yt_downloader_gui/ui/detail_panel.py`
- Create: `tests/test_detail_panel.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_detail_panel.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_detail_panel.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `ui/detail_panel.py`**

```python
from __future__ import annotations
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QLabel, QLineEdit,
    QPlainTextEdit, QProgressBar, QSizePolicy,
    QVBoxLayout, QFormLayout, QWidget, QFrame,
)
from yt_downloader_gui.core.models import QueueItem
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

        from yt_downloader_gui.core.models import ItemStatus
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_detail_panel.py -v
```

Expected: 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add yt_downloader_gui/ui/detail_panel.py tests/test_detail_panel.py
git commit -m "feat: add DetailPanel with thumbnail, controls, progress, and log"
```

---

## Task 10: `ui/main_window.py` — MainWindow

**Files:**
- Create: `yt_downloader_gui/ui/main_window.py`
- Create: `tests/test_main_window.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_main_window.py`:

```python
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
    assert window._queue_panel.count() == 1


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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_main_window.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `ui/main_window.py`**

```python
from __future__ import annotations
import shutil
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton,
    QSplitter, QVBoxLayout, QWidget,
)
from yt_downloader_gui.core.downloader import DownloadWorker
from yt_downloader_gui.core.models import ItemStatus
from yt_downloader_gui.core.settings import AppSettings
from yt_downloader_gui.core.thumbnail import ThumbnailWorker
from yt_downloader_gui.core.updater import UpdaterWorker
from yt_downloader_gui.ui.detail_panel import DetailPanel
from yt_downloader_gui.ui.queue_panel import QueueListItem, QueuePanel


class MainWindow(QMainWindow):
    def __init__(
        self,
        settings_org: str = "YTDownloader",
        settings_app: str = "YTDownloaderGUI",
        parent=None,
    ):
        super().__init__(parent)
        self._settings = AppSettings(org=settings_org, app=settings_app)
        self._worker: DownloadWorker | None = None
        self._updater: UpdaterWorker | None = None
        self._thumbnail_workers: list[ThumbnailWorker] = []
        self._build_ui()
        self._restore_geometry()
        self.setWindowTitle("YT Downloader")

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # URL bar
        url_bar = QHBoxLayout()
        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("Paste YouTube / video URL here…")
        self._url_input.returnPressed.connect(self._on_add)
        url_bar.addWidget(self._url_input)
        self._add_btn = QPushButton("Add")
        self._add_btn.clicked.connect(self._on_add)
        url_bar.addWidget(self._add_btn)
        self._paste_btn = QPushButton("Paste from Clipboard")
        self._paste_btn.clicked.connect(self._on_paste)
        url_bar.addWidget(self._paste_btn)
        root.addLayout(url_bar)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self._queue_panel = QueuePanel()
        self._queue_panel.setMinimumWidth(200)
        self._queue_panel.currentItemChanged.connect(self._on_item_selected)
        splitter.addWidget(self._queue_panel)

        self._detail_panel = DetailPanel()
        splitter.addWidget(self._detail_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, stretch=1)

        # Bottom bar
        bottom = QHBoxLayout()
        bottom.addWidget(QLabel("Output folder:"))
        self._folder_label = QLabel(self._settings.output_dir)
        self._folder_label.setMinimumWidth(200)
        bottom.addWidget(self._folder_label, stretch=1)
        self._browse_btn = QPushButton("Browse…")
        self._browse_btn.clicked.connect(self._on_browse)
        bottom.addWidget(self._browse_btn)

        bottom.addStretch()

        self._start_btn = QPushButton("Start Queue")
        self._start_btn.clicked.connect(self._on_start_queue)
        bottom.addWidget(self._start_btn)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._on_stop)
        bottom.addWidget(self._stop_btn)

        self._update_btn = QPushButton("Update yt-dlp")
        self._update_btn.clicked.connect(self._on_update_ytdlp)
        bottom.addWidget(self._update_btn)

        self._update_status_label = QLabel("")
        bottom.addWidget(self._update_status_label)

        root.addLayout(bottom)

        self.resize(1000, 640)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_add(self) -> None:
        url = self._url_input.text().strip()
        if not url:
            return
        self._add_url(url)
        self._url_input.clear()

    def _on_paste(self) -> None:
        from PyQt6.QtWidgets import QApplication
        text = QApplication.clipboard().text().strip()
        if text.startswith("http://") or text.startswith("https://"):
            self._add_url(text)

    def _add_url(self, url: str) -> None:
        # Duplicate check
        for i in range(self._queue_panel.count()):
            if self._queue_panel.item(i).queue_item.url == url:
                reply = QMessageBox.warning(
                    self,
                    "Duplicate URL",
                    f"This URL is already in the queue:\n{url}\n\nAdd it anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
                break

        list_item = self._queue_panel.add_item(url)
        self._start_thumbnail_fetch(list_item)

    def _start_thumbnail_fetch(self, list_item: QueueListItem) -> None:
        worker = ThumbnailWorker(list_item.queue_item.url)
        self._thumbnail_workers.append(worker)

        def on_fetched(title: str, pixmap) -> None:
            list_item.queue_item.title = title
            list_item.queue_item.thumbnail = pixmap
            list_item.refresh()
            current = self._queue_panel.currentItem()
            if current is list_item:
                self._detail_panel.load_item(list_item.queue_item)
            self._thumbnail_workers.discard_if_present(worker)

        def on_failed(reason: str) -> None:
            list_item.queue_item.status = ItemStatus.ERROR
            list_item.setToolTip(reason)
            list_item.refresh()
            self._thumbnail_workers.discard_if_present(worker)

        worker.fetched.connect(on_fetched)
        worker.failed.connect(on_failed)
        worker.start()

    def _on_item_selected(self, current: QueueListItem | None, _previous) -> None:
        if current is None:
            self._detail_panel.load_item(None)
        else:
            self._detail_panel.load_item(current.queue_item)

    def _on_start_queue(self) -> None:
        next_item = self._queue_panel.next_pending()
        if next_item is None:
            return
        self._run_item(next_item)

    def _run_item(self, list_item: QueueListItem) -> None:
        list_item.queue_item.status = ItemStatus.ACTIVE
        list_item.queue_item.log = ""
        list_item.refresh()

        current = self._queue_panel.currentItem()
        if current is list_item:
            self._detail_panel.load_item(list_item.queue_item)

        self._worker = DownloadWorker(list_item.queue_item, self._settings.output_dir)

        def on_progress(pct: int) -> None:
            list_item.queue_item.log  # already accumulating via log_line
            if self._queue_panel.currentItem() is list_item:
                self._detail_panel.update_progress(pct)

        def on_log_line(line: str) -> None:
            list_item.queue_item.log += line + "\n"
            if self._queue_panel.currentItem() is list_item:
                self._detail_panel.append_log(line)

        def on_finished() -> None:
            list_item.queue_item.status = ItemStatus.DONE
            list_item.refresh()
            self._worker = None
            self._stop_btn.setEnabled(False)
            self._start_btn.setEnabled(True)
            self._advance_queue()

        def on_error(msg: str) -> None:
            list_item.queue_item.status = ItemStatus.ERROR
            list_item.queue_item.log += f"\nERROR: {msg}\n"
            list_item.refresh()
            if self._queue_panel.currentItem() is list_item:
                self._detail_panel.append_log(f"ERROR: {msg}")
            self._worker = None
            self._stop_btn.setEnabled(False)
            self._start_btn.setEnabled(True)
            self._advance_queue()

        self._worker.progress.connect(on_progress)
        self._worker.log_line.connect(on_log_line)
        self._worker.finished.connect(on_finished)
        self._worker.error.connect(on_error)

        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._worker.start()

    def _advance_queue(self) -> None:
        next_item = self._queue_panel.next_pending()
        if next_item is not None:
            self._run_item(next_item)

    def _on_stop(self) -> None:
        if self._worker is not None:
            self._worker.stop()
            # The worker's process.terminate() triggers process exit →
            # on_error fires → item marked STOPPED manually below
        for i in range(self._queue_panel.count()):
            item = self._queue_panel.item(i)
            if item.queue_item.status == ItemStatus.ACTIVE:
                item.queue_item.status = ItemStatus.STOPPED
                item.refresh()
        self._stop_btn.setEnabled(False)
        self._start_btn.setEnabled(True)

    def _on_browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", self._settings.output_dir
        )
        if folder:
            self._settings.output_dir = folder
            self._folder_label.setText(folder)

    def _on_update_ytdlp(self) -> None:
        self._update_btn.setEnabled(False)
        self._update_btn.setText("Updating…")
        self._updater = UpdaterWorker()

        def on_result(msg: str) -> None:
            self._update_status_label.setText(msg)
            self._update_btn.setEnabled(True)
            self._update_btn.setText("Update yt-dlp")

        self._updater.result.connect(on_result)
        self._updater.start()

    # ------------------------------------------------------------------
    # Geometry persistence
    # ------------------------------------------------------------------

    def _restore_geometry(self) -> None:
        geo = self._settings.load_geometry()
        if geo:
            self.restoreGeometry(geo)

    def closeEvent(self, event) -> None:
        self._settings.save_geometry(bytes(self.saveGeometry()))
        super().closeEvent(event)
```

- [ ] **Step 4: Fix the `discard_if_present` helper** — `list` has no `discard_if_present`. Replace with a try/remove:

In `_start_thumbnail_fetch`, change both occurrences of:
```python
self._thumbnail_workers.discard_if_present(worker)
```
to:
```python
try:
    self._thumbnail_workers.remove(worker)
except ValueError:
    pass
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_main_window.py -v
```

Expected: 8 tests PASS

- [ ] **Step 6: Run full test suite**

```bash
pytest -v
```

Expected: all tests PASS

- [ ] **Step 7: Commit**

```bash
git add yt_downloader_gui/ui/main_window.py tests/test_main_window.py
git commit -m "feat: add MainWindow wiring all panels and workers together"
```

---

## Task 11: `main.py` — Entry Point

**Files:**
- Create: `yt_downloader_gui/main.py`

- [ ] **Step 1: Implement `main.py`**

```python
import shutil
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from yt_downloader_gui.ui.main_window import MainWindow


def _check_ytdlp() -> bool:
    if shutil.which("yt-dlp") is None:
        app = QApplication.instance() or QApplication(sys.argv)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("yt-dlp not found")
        msg.setText(
            "yt-dlp is not installed or not in PATH.\n\n"
            "Install it with:\n"
            "  pip install yt-dlp\n\n"
            "Or download from: https://github.com/yt-dlp/yt-dlp"
        )
        msg.exec()
        return False
    return True


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("YT Downloader")
    app.setOrganizationName("YTDownloader")

    if not _check_ytdlp():
        sys.exit(1)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the app to verify it launches**

```bash
python -m yt_downloader_gui.main
```

Expected: window opens with URL bar, split panels, and bottom bar visible.

- [ ] **Step 3: Run full test suite one final time**

```bash
pytest -v
```

Expected: all tests PASS

- [ ] **Step 4: Commit**

```bash
git add yt_downloader_gui/main.py
git commit -m "feat: add entry point with yt-dlp PATH check"
```

---

## Self-Review Checklist

After writing, verifying spec coverage:

| Spec requirement | Covered by |
|---|---|
| Split-panel layout | Task 10 (MainWindow splitter) |
| URL input + Add button | Task 10 |
| Paste from clipboard (http/https only) | Task 10 `_on_paste` |
| Per-item format dropdown (all 7 modes) | Tasks 4 + 9 |
| Audio language input | Task 9 |
| Subtitle language input | Task 9 |
| Embed subs checkbox | Task 9 |
| Controls locked during/after download | Task 9 `lock_controls` |
| Thumbnail + title fetch in background | Task 6 |
| Placeholder shown on fetch failure | Task 9 `load_item` |
| Download queue (one at a time) | Task 10 `_run_item` + `_advance_queue` |
| Real-time progress bar | Tasks 5 + 10 |
| Live log output | Tasks 5 + 10 |
| Log preserved for completed items | Task 10 (stored in `queue_item.log`) |
| Output folder default ~/Downloads | Task 3 |
| Output folder persisted via QSettings | Task 3 |
| Browse folder button | Task 10 |
| yt-dlp updater button | Tasks 7 + 10 |
| yt-dlp not in PATH error dialog | Task 11 |
| Invalid URL → item marked error | Task 10 `_start_thumbnail_fetch` |
| Download failure → error + continue | Task 10 `on_error` |
| Duplicate URL warning | Task 10 `_add_url` |
| Stop button terminates process | Tasks 5 + 10 |
