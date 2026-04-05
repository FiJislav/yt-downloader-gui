from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ItemStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DONE = "done"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class QueueItem:
    url: str
    # Fetched metadata (populated by ThumbnailWorker)
    resolutions: list[str] = field(default_factory=list)
    formats_by_resolution: dict[str, list[str]] = field(default_factory=dict)
    audio_tracks: list[str] = field(default_factory=list)
    subtitle_langs: list[str] = field(default_factory=list)
    # User selections
    resolution: str = "Best available"
    codec: str = "Best available"
    audio_track: str = "(best)"
    subtitle_lang: str = ""
    embed_subs: bool = False
    audio_only: bool = False
    audio_fmt: str = "mp3"
    audio_quality: str = "(best quality)"
    # Status and display
    status: ItemStatus = field(default=ItemStatus.PENDING)
    title: str = ""
    thumbnail: Optional[object] = None  # QPixmap at runtime
    log: str = ""
