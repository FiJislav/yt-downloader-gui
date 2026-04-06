# YT Downloader GUI

A desktop YouTube / video downloader built with Python and PyQt6, wrapping [yt-dlp](https://github.com/yt-dlp/yt-dlp).

![screenshot placeholder](docs/screenshot.png)

## Features

- **Download queue** — add multiple URLs and download them one by one
- **Dynamic dropdowns** — resolution, codec, audio track, and subtitle options are populated from the actual video metadata after pasting a URL
- **Playlist support** — paste a playlist URL and choose to download all videos or just the first one
- **Audio-only mode** — extract audio in mp3, m4a, opus, or best quality with configurable bitrate
- **Subtitle download** — choose from available subtitle languages (manual or auto-generated in the video's language), with optional embedding
- **Real-time progress** — segmented progress bar with live log output from yt-dlp
- **Thumbnail preview** — video thumbnail shown in the detail panel
- **Output folder** — configurable with persistence between sessions
- **Queue counter** — shows `Video X / Y` while downloading a playlist
- **yt-dlp updater** — one-click update button

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.10+ |
| PyQt6 | 6.4+ |
| yt-dlp | installed and on PATH |

> **yt-dlp must be installed separately** and accessible as `yt-dlp` on the command line.
> Install it with: `pip install yt-dlp` or download from [yt-dlp releases](https://github.com/yt-dlp/yt-dlp/releases).

## Installation

### Option A — Pre-built executable (Windows)

Download `YT-Downloader.exe` from the [latest release](../../releases/latest) and run it.
yt-dlp still needs to be on PATH.

### Option B — Run from source

```bash
git clone https://github.com/FiJislav/yt-downloader-gui
cd yt-downloader-gui
pip install -r requirements.txt
python -m yt_downloader_gui.main
```

## Building the executable yourself

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "YT-Downloader" yt_downloader_gui/main.py
# Output: dist/YT-Downloader.exe
```

## Usage

1. **Paste a URL** into the input field and click **Add** (or press Enter / use **Paste from Clipboard**)
2. If it's a playlist URL you will be asked whether to add all videos or just the first
3. Wait for the thumbnail and metadata to load — dropdowns populate automatically
4. Choose your preferred **resolution**, **codec**, **audio track**, and **subtitles**
5. Set the **output folder** with the Browse button
6. Click **Start Queue** to begin downloading

### Download options

| Control | Description |
|---|---|
| Resolution | Video height (e.g. 1080p, 720p) or Best available |
| Codec | Container + codec per resolution (e.g. `mp4 (avc1, 60fps)`) |
| Audio track | Language of the audio stream |
| Subtitles | Available subtitle / auto-caption language |
| Embed subtitles | Mux subtitles into the video file |
| Audio only | Extract audio; choose format (mp3/m4a/opus) and quality |

### Filename format

Downloads are saved as:
```
<Channel Name> - <Video Title>.<ext>
```

## Development

```bash
pip install -r requirements-dev.txt
pytest
```

## License

MIT
