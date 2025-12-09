"""Dialog for assembling an effective CSO from imported links."""

from __future__ import annotations

from typing import List, Optional

from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
)

from plato.refactored.config import EffectiveCSODefinition


class EffectiveCSOBuildDialog(QDialog):
    """Collects user selections to define an effective CSO."""

    def __init__(self, available_links: List[str], parent=None) -> None:
        super().__init__(parent)
        self.available_links = sorted(available_links)
        self._continuation_widget: Optional[QListWidget] = None
        self._overflow_widget: Optional[QListWidget] = None
        self._definition: Optional[EffectiveCSODefinition] = None
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self.setWindowTitle("Build Effective CSO")
        self.setModal(True)
        layout = QVBoxLayout(self)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("CSO Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Market Street CSO")
        name_row.addWidget(self.name_edit)
        layout.addLayout(name_row)

        instructions = QLabel(
            "Select links that contribute to the continuation flow and overflow. "
            "Hold Ctrl or Shift to choose multiple entries."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        lists_row = QHBoxLayout()
        self.continuation_list = self._create_list_widget("Continuation Links")
        self.overflow_list = self._create_list_widget("Overflow Links")
        lists_row.addLayout(self.continuation_list)
        lists_row.addSpacing(12)
        lists_row.addLayout(self.overflow_list)
        layout.addLayout(lists_row)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._handle_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _create_list_widget(self, header: str) -> QVBoxLayout:
        column = QVBoxLayout()
        column.addWidget(QLabel(header))
        widget = QListWidget()
        widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for link in self.available_links:
            item = QListWidgetItem(link)
            widget.addItem(item)
        column.addWidget(widget)
        if header.startswith("Continuation"):
            self._continuation_widget = widget
        else:
            self._overflow_widget = widget
        return column

    # ------------------------------------------------------------------
    def _handle_accept(self) -> None:
        name = self.name_edit.text().strip()
        if self._continuation_widget is None or self._overflow_widget is None:
            QMessageBox.critical(self, "Internal Error", "Link widgets not initialised.")
            return
        continuation = [item.text() for item in self._continuation_widget.selectedItems()]
        overflow = [item.text() for item in self._overflow_widget.selectedItems()]

        if not name:
            QMessageBox.warning(self, "Missing Name", "Please provide a CSO name.")
            return

        if not continuation:
            QMessageBox.warning(
                self,
                "No Continuation Links",
                "Select at least one continuation link.",
            )
            return

        if not overflow:
            QMessageBox.warning(
                self,
                "No Overflow Links",
                "Select at least one overflow link.",
            )
            return

        self._definition = EffectiveCSODefinition(
            name=name,
            continuation_links=continuation,
            overflow_links=overflow,
        )
        self.accept()

    # ------------------------------------------------------------------
    def get_definition(self) -> Optional[EffectiveCSODefinition]:
        return self._definition
