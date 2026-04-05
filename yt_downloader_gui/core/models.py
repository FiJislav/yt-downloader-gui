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
