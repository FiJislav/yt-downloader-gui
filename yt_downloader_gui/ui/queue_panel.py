from __future__ import annotations
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QMenu
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
        title = self.queue_item.title
        url = self.queue_item.url
        display = title if title else url
        short = display[:45] + "…" if len(display) > 45 else display
        icon = _STATUS_ICONS[self.queue_item.status]
        self.setText(f"{icon}  {short}")
        self.setToolTip(title if title else url)


class QueuePanel(QListWidget):
    item_removed = pyqtSignal(object)  # emits QueueListItem

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos) -> None:
        item = self.itemAt(pos)
        if item is None:
            return
        menu = QMenu(self)
        remove_action = menu.addAction("Remove")
        action = menu.exec(self.mapToGlobal(pos))
        if action is remove_action:
            self._remove_item(item)

    def _remove_item(self, list_item: QueueListItem) -> None:
        row = self.row(list_item)
        if row >= 0:
            self.takeItem(row)
            self.item_removed.emit(list_item)

    def clear_all(self) -> None:
        items = [self.item(i) for i in range(self.count())]
        self.clear()
        for item in items:
            self.item_removed.emit(item)

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
