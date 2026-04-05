# YT Downloader GUI — Design Spec
**Date:** 2026-04-05  
**Stack:** Python, PyQt6, yt-dlp

---

## Overview

A desktop GUI application that wraps `yt-dlp`, replacing the existing `yt_download.ps1` PowerShell script. Users can build a download queue of URLs, configure per-item format/language/subtitle options, and monitor downloads in real time via a progress bar and live log output.

---

## Layout & Structure

Split-panel layout inside a `QMainWindow`:

```
┌─────────────────────────────────────────────────────────┐
│  [URL input bar]  [Add]  [Paste from clipboard]         │
├──────────────────────┬──────────────────────────────────┤
│  Queue list          │  Thumbnail (fetched on add)      │
│  ─────────────────   │  ─────────────────────────────   │
│  ○ https://...  mp4  │  Format:  [mp4 ▼]               │
│  ● https://... mp3   │  Audio:   [en  ▼]  (optional)   │
│  ✓ https://... done  │  Subs:    [en  ▼]  [embed ☐]    │
│                      │  ─────────────────────────────   │
│                      │  Progress: [=========>  72%]     │
│                      │  ─────────────────────────────   │
│                      │  Log output (scrollable)         │
│                      │  > [yt-dlp output lines...]      │
├──────────────────────┴──────────────────────────────────┤
│  Output folder: C:\Users\...\Downloads  [Browse]        │
│  [Start Queue]  [Stop]  [Update yt-dlp]                 │
└─────────────────────────────────────────────────────────┘
```

**Left panel** (`QListWidget`): each item shows truncated URL, chosen format, and a status icon:
- `○` pending
- `●` active (currently downloading)
- `✓` completed
- `✗` error / stopped

**Right panel**: updates on queue item selection. Shows:
- Thumbnail image (fetched in background when URL is added)
- Video title
- Per-item controls: Format, Audio language, Subtitle language, Embed subs checkbox
- Progress bar (active only during download)
- Scrollable log output (`QPlainTextEdit`, read-only)

**Bottom bar** (persistent):
- Output folder path + Browse button
- Start Queue, Stop, Update yt-dlp buttons

---

## Features

### URL Input
- Manual entry in the URL bar + Add button
- **Clipboard auto-detect**: Paste from Clipboard button reads clipboard; only acts if content starts with `http://` or `https://`

### Per-Item Configuration (right panel)
- **Format**: dropdown — `mp4`, `mp3`, `mkv`, `4k`, `4k-no-av1`, `embed-subs`, `subs`
- **Audio language**: free-text or dropdown (e.g. `en`, `ja`) — optional, maps to `bestaudio[lang=X]`
- **Subtitle language**: free-text (e.g. `en`) — defaults to `en`
- **Embed subs**: checkbox — when checked uses `--embed-subs`
- Settings are editable only when item is `pending`; locked during/after download

### Thumbnail & Title Fetch
- On URL add, a background `QThread` runs `yt-dlp --dump-json <url>` and extracts `thumbnail` and `title`
- Thumbnail is displayed as a scaled `QLabel` image in the right panel
- If fetch fails, a placeholder image is shown

### Download Queue
- Downloads execute one at a time, in order
- Start Queue begins from the first pending item
- Queue continues automatically to the next pending item after each completes or errors
- Completed and errored items remain in the list (with their logs)

### Real-Time Progress
- `yt-dlp` stdout is read line-by-line in a `QThread`
- Progress percentage extracted via regex: `\[download\]\s+(\d+(?:\.\d+)?)%`
- Progress bar and log update via Qt signals/slots (thread-safe)

### Output Folder
- Defaults to `~/Downloads`
- User can change via Browse button (folder picker dialog)
- Persisted across sessions via `QSettings`

### yt-dlp Updater
- Update yt-dlp button runs `yt-dlp -U` in a background thread
- Button shows "Updating..." and is disabled while running
- Result (success/failure message) shown in a status label next to the button
- Does not interrupt an active download

---

## Architecture

```
yt_downloader_gui/
├── main.py                  # QApplication entry point
├── ui/
│   ├── main_window.py       # QMainWindow, QSplitter, URL bar, bottom bar
│   ├── queue_panel.py       # Left panel: QListWidget + QueueItem model
│   └── detail_panel.py      # Right panel: thumbnail, controls, progress, log
└── core/
    ├── downloader.py        # QThread: runs yt-dlp, emits progress/log/done signals
    ├── thumbnail.py         # QThread: runs yt-dlp --dump-json, emits title+thumbnail
    ├── updater.py           # QThread: runs yt-dlp -U, emits result signal
    └── settings.py          # QSettings wrapper: output folder, window geometry
```

**Signal flow:**
- `thumbnail.py` → emits `fetched(title, thumbnail_pixmap)` → `detail_panel.py` updates display
- `downloader.py` → emits `progress(int)`, `log_line(str)`, `finished()`, `error(str)` → `detail_panel.py` + queue item status
- `updater.py` → emits `result(str)` → bottom bar status label

---

## Error Handling

| Scenario | Behavior |
|---|---|
| `yt-dlp` not in PATH | Error dialog on startup with install instructions |
| Invalid / unsupported URL | Thumbnail fetch fails → item marked error, tooltip shows reason |
| Download failure | Item marked red/error, log shows full yt-dlp output, queue continues |
| Duplicate URL | Warning dialog, user can allow or cancel |
| Stop mid-queue | `process.terminate()` on active download, item marked "stopped", queue paused |
| yt-dlp update failure | Status label shows error message, no crash |
| Clipboard has no URL | Paste button does nothing silently |

---

## Out of Scope
- Playlist expansion UI (yt-dlp handles playlists internally)
- Download history persistence across sessions
- Scheduling / scheduled downloads
- Authentication / cookies UI
