"""Catchments Tab - Define named catchment groups for multi-tank analysis."""

from typing import List, Optional

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QMessageBox,
    QHeaderView,
    QAbstractItemView,
    QFileDialog,
    QComboBox,
    QDoubleSpinBox,
    QListWidget,
    QDialog,
    QDialogButtonBox,
    QInputDialog,
    QLineEdit,
)

from plato.refactored.asset_models import Catchment, CatchmentRelationship, CSOAsset
import pandas as pd


class MultiSelectDialog(QDialog):
    """Dialog to select multiple upstream CSOs."""

    def __init__(self, available_csos: List[str], current_selection: List[str] = None, parent=None):
        super().__init__(parent)
        self.available_csos = available_csos
        self.selected_csos = current_selection or []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Select Upstream CSOs")
        self.setModal(True)
        self.resize(400, 400)

        layout = QVBoxLayout(self)

        info = QLabel(
            "Select one or more CSOs that feed into this CSO.\n"
            "Leave empty if this is an independent/headwater CSO."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.list_widget = QListWidget()
        self.list_widget.addItems(self.available_csos)
        self.list_widget.setSelectionMode(
            QListWidget.SelectionMode.MultiSelection)

        # Pre-select current items
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.text() in self.selected_csos:
                item.setSelected(True)

        layout.addWidget(QLabel("Available CSOs:"))
        layout.addWidget(self.list_widget)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_selected_csos(self) -> List[str]:
        """Get the selected CSO names."""
        return [item.text() for item in self.list_widget.selectedItems()]


class CatchmentEditorDialog(QDialog):
    """Dialog to create/edit a catchment group."""

    COLUMNS = [
        'CSO Name',
        'Upstream CSOs',
        'Downstream CSO',
        'Max PFF (m3/s)',
        'Distance (m)',
        'Velocity (m/s)',
    ]

    def __init__(self, available_csos: List[str], catchment: Optional[Catchment] = None, parent=None):
        super().__init__(parent)
        self.available_csos = available_csos
        self.catchment = catchment
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Create/Edit Catchment")
        self.setModal(True)
        self.resize(900, 600)

        layout = QVBoxLayout(self)

        # Catchment name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Catchment Name:"))
        self.name_edit = QLineEdit()
        if self.catchment:
            self.name_edit.setText(self.catchment.name)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # Info label
        info = QLabel(
            "Define CSO relationships within this catchment. "
            "A catchment must contain at least 2 CSOs."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "QLabel { color: #666; font-style: italic; margin: 5px; }")
        layout.addWidget(info)

        # Buttons for CSO management
        btn_layout = QHBoxLayout()
        self.add_cso_btn = QPushButton("Add CSO")
        self.add_cso_btn.clicked.connect(self.add_cso)
        btn_layout.addWidget(self.add_cso_btn)

        self.remove_cso_btn = QPushButton("Remove Selected")
        self.remove_cso_btn.clicked.connect(self.remove_selected_csos)
        btn_layout.addWidget(self.remove_cso_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # CSO relationships table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 150)  # CSO Name
        self.table.setColumnWidth(1, 200)  # Upstream
        self.table.setColumnWidth(2, 150)  # Downstream
        self.table.setColumnWidth(3, 120)  # Max PFF
        self.table.setColumnWidth(4, 100)  # Distance
        self.table.setColumnWidth(5, 100)  # Velocity

        layout.addWidget(self.table)

        # Load existing catchment data
        if self.catchment:
            for rel in self.catchment.cso_relationships:
                self.add_relationship_row(rel)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def add_cso(self):
        """Add a CSO to this catchment."""
        # Get CSOs already in table
        used_csos = set()
        for row in range(self.table.rowCount()):
            cso_item = self.table.item(row, 0)
            if cso_item:
                used_csos.add(cso_item.text())

        # Get available CSOs
        available = [
            cso for cso in self.available_csos if cso not in used_csos]

        if not available:
            QMessageBox.warning(
                self, "No CSOs Available",
                "All CSOs are already in this catchment or no CSOs are defined."
            )
            return

        # Select CSO
        cso_name, ok = QInputDialog.getItem(
            self, "Add CSO", "Select CSO to add:", available, 0, False
        )

        if ok and cso_name:
            rel = CatchmentRelationship(cso_name=cso_name)
            self.add_relationship_row(rel)

    def add_relationship_row(self, rel: CatchmentRelationship):
        """Add a row for a CSO relationship."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # CSO Name (read-only)
        name_item = QTableWidgetItem(rel.cso_name)
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 0, name_item)

        # Upstream CSOs (button to edit)
        upstream_label = QLabel(
            "(none)" if not rel.upstream_csos else ", ".join(rel.upstream_csos))
        upstream_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upstream_label.setStyleSheet(
            "QLabel { color: #999; }" if not rel.upstream_csos else "QLabel { color: black; }")
        upstream_container = QWidget()
        upstream_layout = QHBoxLayout(upstream_container)
        upstream_layout.setContentsMargins(2, 2, 2, 2)

        edit_upstream_btn = QPushButton("Edit...")
        edit_upstream_btn.clicked.connect(
            lambda checked, r=row: self.edit_upstream_csos(r))
        upstream_layout.addWidget(upstream_label)
        upstream_layout.addWidget(edit_upstream_btn)

        self.table.setCellWidget(row, 1, upstream_container)
        upstream_container.setProperty("upstream_label", upstream_label)
        upstream_container.setProperty("upstream_csos", rel.upstream_csos)

        # Downstream CSO (dropdown)
        downstream_combo = QComboBox()
        downstream_combo.addItem("(none)")
        other_csos = [
            name for name in self.available_csos if name != rel.cso_name]
        downstream_combo.addItems(other_csos)
        if rel.downstream_cso:
            idx = downstream_combo.findText(rel.downstream_cso)
            if idx >= 0:
                downstream_combo.setCurrentIndex(idx)
        self.table.setCellWidget(row, 2, downstream_combo)

        # Max PFF
        max_pff_spin = QDoubleSpinBox()
        max_pff_spin.setRange(0, 1000)
        max_pff_spin.setDecimals(5)
        max_pff_spin.setValue(rel.max_pff if rel.max_pff else 0.0)
        max_pff_spin.setSpecialValueText("Unknown")
        self.table.setCellWidget(row, 3, max_pff_spin)

        # Distance
        distance_spin = QDoubleSpinBox()
        distance_spin.setRange(0, 100000)
        distance_spin.setDecimals(1)
        distance_spin.setValue(
            rel.distance_to_downstream if rel.distance_to_downstream else 0.0)
        distance_spin.setSuffix(" m")
        self.table.setCellWidget(row, 4, distance_spin)

        # Velocity
        velocity_spin = QDoubleSpinBox()
        velocity_spin.setRange(0, 10)
        velocity_spin.setDecimals(3)
        velocity_spin.setValue(
            rel.average_velocity if rel.average_velocity else 0.0)
        velocity_spin.setSuffix(" m/s")
        self.table.setCellWidget(row, 5, velocity_spin)

    def edit_upstream_csos(self, row: int):
        """Edit upstream CSOs for a row."""
        cso_name = self.table.item(row, 0).text()

        # Get available CSOs (exclude self and CSOs not in catchment)
        csos_in_catchment = set()
        for r in range(self.table.rowCount()):
            csos_in_catchment.add(self.table.item(r, 0).text())

        available = [name for name in csos_in_catchment if name != cso_name]

        upstream_container = self.table.cellWidget(row, 1)
        current_upstream = upstream_container.property("upstream_csos")

        dialog = MultiSelectDialog(available, current_upstream, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected_csos()
            upstream_container.setProperty("upstream_csos", selected)

            upstream_label = upstream_container.property("upstream_label")
            if selected:
                upstream_label.setText(", ".join(selected))
                upstream_label.setStyleSheet("QLabel { color: black; }")
            else:
                upstream_label.setText("(none)")
                upstream_label.setStyleSheet("QLabel { color: #999; }")

    def remove_selected_csos(self):
        """Remove selected CSOs from the catchment."""
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if not selected_rows:
            return

        for row in sorted(selected_rows, reverse=True):
            self.table.removeRow(row)

    def get_catchment(self) -> Catchment:
        """Extract catchment from dialog."""
        name = self.name_edit.text().strip()
        if not name:
            raise ValueError("Catchment name cannot be empty")

        relationships = []
        for row in range(self.table.rowCount()):
            cso_name = self.table.item(row, 0).text()

            upstream_container = self.table.cellWidget(row, 1)
            upstream_csos = upstream_container.property("upstream_csos")

            downstream_combo = self.table.cellWidget(row, 2)
            downstream_text = downstream_combo.currentText()
            downstream_cso = downstream_text if downstream_text != "(none)" else None

            max_pff_spin = self.table.cellWidget(row, 3)
            max_pff = max_pff_spin.value() if max_pff_spin.value() > 0 else None

            distance_spin = self.table.cellWidget(row, 4)
            distance = distance_spin.value() if distance_spin.value() > 0 else None

            velocity_spin = self.table.cellWidget(row, 5)
            velocity = velocity_spin.value() if velocity_spin.value() > 0 else None

            rel = CatchmentRelationship(
                cso_name=cso_name,
                upstream_csos=upstream_csos,
                downstream_cso=downstream_cso,
                max_pff=max_pff,
                distance_to_downstream=distance,
                average_velocity=velocity,
            )
            relationships.append(rel)

        return Catchment(name=name, cso_relationships=relationships)


class CatchmentsTab(QWidget):
    """Tab for defining catchment groups for multi-tank analysis."""

    catchments_changed = pyqtSignal()

    COLUMNS = [
        'Catchment Name',
        'Number of CSOs',
        'CSOs in Catchment',
    ]

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.available_csos: List[str] = []
        self.cso_assets: List[CSOAsset] = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Info label
        info_label = QLabel(
            "Define catchment groups containing multiple CSOs for multi-tank analysis. "
            "Each catchment represents a hydraulic network that will be analyzed together "
            "in Catchment Based Mode. A catchment must contain at least 2 CSOs."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "QLabel { color: #666; font-style: italic; margin: 5px; }")
        layout.addWidget(info_label)

        # Button toolbar
        button_layout = QHBoxLayout()

        self.create_btn = QPushButton("Create Catchment")
        self.create_btn.clicked.connect(self.create_catchment)
        button_layout.addWidget(self.create_btn)

        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self.edit_selected)
        button_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected)
        button_layout.addWidget(self.delete_btn)

        button_layout.addStretch()

        # self.validate_btn = QPushButton("Validate Catchments")
        # self.validate_btn.clicked.connect(self.validate_catchments)
        # self.validate_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        # button_layout.addWidget(self.validate_btn)

        # self.import_csv_btn = QPushButton("Import from CSV...")
        # self.import_csv_btn.clicked.connect(self.import_from_csv)
        # button_layout.addWidget(self.import_csv_btn)

        # self.export_csv_btn = QPushButton("Export to CSV...")
        # self.export_csv_btn.clicked.connect(self.export_to_csv)
        # button_layout.addWidget(self.export_csv_btn)

        layout.addLayout(button_layout)

        # Catchments table
        table_group = QGroupBox("Defined Catchments")
        table_layout = QVBoxLayout()

        self.catchments_table = QTableWidget()
        self.catchments_table.setColumnCount(len(self.COLUMNS))
        self.catchments_table.setHorizontalHeaderLabels(self.COLUMNS)
        self.catchments_table.setAlternatingRowColors(True)
        self.catchments_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.catchments_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.catchments_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection)

        # Double-click to edit
        self.catchments_table.doubleClicked.connect(self.edit_selected)

        table_layout.addWidget(self.catchments_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

    def set_cso_assets(self, assets: List[CSOAsset]):
        """Update available CSO assets."""
        self.cso_assets = assets
        self.available_csos = [asset.name for asset in assets]

    def create_catchment(self):
        """Create a new catchment."""
        if not self.available_csos:
            QMessageBox.warning(
                self, "No CSO Assets",
                "Please define CSO assets in the CSO Assets tab first."
            )
            return

        dialog = CatchmentEditorDialog(self.available_csos, None, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                catchment = dialog.get_catchment()

                # Check for duplicate name
                existing_names = [
                    self.catchments_table.item(row, 0).text()
                    for row in range(self.catchments_table.rowCount())
                ]
                if catchment.name in existing_names:
                    QMessageBox.warning(
                        self, "Duplicate Name",
                        f"A catchment named '{catchment.name}' already exists."
                    )
                    return

                self.add_catchment_row(catchment)
                self.catchments_changed.emit()

            except Exception as e:
                QMessageBox.critical(
                    self, "Error Creating Catchment",
                    f"Failed to create catchment:\n{str(e)}"
                )

    def add_catchment_row(self, catchment: Catchment):
        """Add a catchment to the table."""
        row = self.catchments_table.rowCount()
        self.catchments_table.insertRow(row)

        # Store catchment object
        name_item = QTableWidgetItem(catchment.name)
        name_item.setData(Qt.ItemDataRole.UserRole, catchment)
        self.catchments_table.setItem(row, 0, name_item)

        # CSO count
        count_item = QTableWidgetItem(str(len(catchment.cso_relationships)))
        count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.catchments_table.setItem(row, 1, count_item)

        # CSO names
        cso_names = ", ".join(catchment.get_cso_names())
        self.catchments_table.setItem(row, 2, QTableWidgetItem(cso_names))

    def edit_selected(self):
        """Edit the selected catchment."""
        selected_rows = self.catchments_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection",
                                "Please select a catchment to edit.")
            return

        row = selected_rows[0].row()
        catchment = self.catchments_table.item(
            row, 0).data(Qt.ItemDataRole.UserRole)

        dialog = CatchmentEditorDialog(self.available_csos, catchment, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                updated_catchment = dialog.get_catchment()

                # Update the row
                self.catchments_table.removeRow(row)
                self.catchments_table.insertRow(row)

                name_item = QTableWidgetItem(updated_catchment.name)
                name_item.setData(Qt.ItemDataRole.UserRole, updated_catchment)
                self.catchments_table.setItem(row, 0, name_item)

                count_item = QTableWidgetItem(
                    str(len(updated_catchment.cso_relationships)))
                count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.catchments_table.setItem(row, 1, count_item)

                cso_names = ", ".join(updated_catchment.get_cso_names())
                self.catchments_table.setItem(
                    row, 2, QTableWidgetItem(cso_names))

                self.catchments_changed.emit()

            except Exception as e:
                QMessageBox.critical(
                    self, "Error Updating Catchment",
                    f"Failed to update catchment:\n{str(e)}"
                )

    def delete_selected(self):
        """Delete the selected catchment."""
        selected_rows = self.catchments_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection",
                                "Please select a catchment to delete.")
            return

        row = selected_rows[0].row()
        catchment_name = self.catchments_table.item(row, 0).text()

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete catchment '{catchment_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.catchments_table.removeRow(row)
            self.catchments_changed.emit()

    def validate_catchments(self):
        """Validate all catchments."""
        if self.catchments_table.rowCount() == 0:
            QMessageBox.information(
                self, "No Catchments", "No catchments defined.")
            return

        errors = []
        for row in range(self.catchments_table.rowCount()):
            catchment = self.catchments_table.item(
                row, 0).data(Qt.ItemDataRole.UserRole)
            catchment_errors = catchment.validate_network()
            if catchment_errors:
                errors.append(f"\n{catchment.name}:")
                errors.extend([f"  • {err}" for err in catchment_errors])

        if errors:
            QMessageBox.warning(
                self, "Validation Errors",
                "The following errors were found:\n" + "\n".join(errors)
            )
        else:
            QMessageBox.information(
                self, "Validation Passed",
                "All catchments are valid."
            )

    def get_catchments(self) -> List[Catchment]:
        """Get all defined catchments."""
        catchments = []
        for row in range(self.catchments_table.rowCount()):
            catchment = self.catchments_table.item(
                row, 0).data(Qt.ItemDataRole.UserRole)
            catchments.append(catchment)
        return catchments

    def get_catchment_names(self) -> List[str]:
        """Get list of catchment names."""
        return [c.name for c in self.get_catchments()]

    def set_catchments(self, catchments: List[Catchment]):
        """Load catchments into table."""
        self.catchments_table.setRowCount(0)
        for catchment in catchments:
            self.add_catchment_row(catchment)

    def import_from_csv(self):
        """Import catchments from CSV."""
        QMessageBox.information(
            self, "Not Implemented",
            "CSV import for catchments is not yet implemented. Use project files instead."
        )

    def export_to_csv(self):
        """Export catchments to CSV."""
        QMessageBox.information(
            self, "Not Implemented",
            "CSV export for catchments is not yet implemented. Use project files instead."
        )

    def get_state(self) -> dict:
        """Get current state for project save."""
        catchments = self.get_catchments()
        return {
            'catchments': [c.to_dict() for c in catchments]
        }

    def load_state(self, state: dict):
        """Load state from project file."""
        if 'catchments' in state:
            catchments = [
                Catchment.from_dict(c_dict)
                for c_dict in state['catchments']
            ]
            self.set_catchments(catchments)
