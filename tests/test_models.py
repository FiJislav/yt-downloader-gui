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
