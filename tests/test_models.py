from yt_downloader_gui.core.models import QueueItem, ItemStatus


def test_queue_item_defaults():
    item = QueueItem(url="https://example.com/watch?v=abc")
    # old fields removed
    assert not hasattr(item, "fmt")
    assert not hasattr(item, "audio_lang")
    assert not hasattr(item, "sub_lang")
    # new metadata fields
    assert item.resolutions == []
    assert item.formats_by_resolution == {}
    assert item.audio_tracks == []
    assert item.subtitle_langs == []
    # new selection fields
    assert item.resolution == "Best available"
    assert item.codec == "Best available"
    assert item.audio_track == "(best)"
    assert item.subtitle_lang == ""
    assert item.embed_subs is False
    assert item.audio_only is False
    assert item.audio_fmt == "mp3"
    assert item.audio_quality == "(best quality)"
    # unchanged fields
    assert item.status == ItemStatus.PENDING
    assert item.title == ""
    assert item.thumbnail is None
    assert item.log == ""


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


def test_queue_item_resolution_selection():
    item = QueueItem(url="https://example.com/watch?v=abc", resolution="1080p")
    assert item.resolution == "1080p"


def test_queue_item_audio_only():
    item = QueueItem(url="https://example.com/watch?v=abc", audio_only=True, audio_fmt="m4a")
    assert item.audio_only is True
    assert item.audio_fmt == "m4a"
