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
        self.setText(f"{icon}  {short_url}")
        self.setToolTip(self.queue_item.title if self.queue_item.title else "")


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
