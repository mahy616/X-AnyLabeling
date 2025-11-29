from PyQt5.QtWidgets import QWidget, QHBoxLayout, QComboBox


class GroupIDFilterComboBox(QWidget):
    def __init__(self, parent=None, items=[]):
        super(GroupIDFilterComboBox, self).__init__(parent)
        self.items = items
        self.gid_box = QComboBox()
        self.gid_box.setToolTip(self.tr("Group ID Filter"))
        self.gid_box.addItems(self.items)
        self.gid_box.currentIndexChanged.connect(parent.gid_selection_changed)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 2, 0, 2)
        layout.addWidget(self.gid_box)
        self.setLayout(layout)

    def update_items(self, items):
        self.items = items
        self.gid_box.clear()
        self.gid_box.addItems(self.items)


class LabelFilterComboBox(QWidget):
    def __init__(self, parent=None, items=[]):
        super(LabelFilterComboBox, self).__init__(parent)
        self.items = items
        self.text_box = QComboBox()
        self.text_box.setToolTip(self.tr("Label Filter"))
        self.text_box.addItems(self.items)
        self.text_box.currentIndexChanged.connect(
            parent.text_selection_changed
        )

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 2, 0, 2)
        layout.addWidget(self.text_box)
        self.setLayout(layout)

    def update_items(self, items):
        self.items = items
        self.text_box.clear()
        self.text_box.addItems(self.items)


class FileLabelFilterComboBox(QWidget):
    """Filter combobox for filtering file list by label"""
    def __init__(self, parent=None, items=[]):
        super(FileLabelFilterComboBox, self).__init__(parent)
        self.items = items
        self.text_box = QComboBox()
        self.text_box.setToolTip(self.tr("Filter Files by Label"))
        self.text_box.addItems(self.items)
        self.text_box.currentIndexChanged.connect(
            parent.file_label_filter_changed
        )

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 2, 0, 2)
        layout.addWidget(self.text_box)
        self.setLayout(layout)

    def update_items(self, items):
        # Save current selection
        current_text = self.text_box.currentText()

        # Block signals to prevent triggering filter change during update
        self.text_box.blockSignals(True)

        self.items = items
        self.text_box.clear()
        self.text_box.addItems(self.items)

        # Restore previous selection if it still exists in new items
        if current_text and current_text in items:
            index = self.text_box.findText(current_text)
            if index >= 0:
                self.text_box.setCurrentIndex(index)

        # Unblock signals
        self.text_box.blockSignals(False)
