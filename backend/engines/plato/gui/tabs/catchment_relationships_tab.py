"""Catchment Relationships Tab - Define upstream/downstream CSO connections."""

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
)

from plato.refactored.asset_models import CatchmentRelationship, CSOAsset
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


class CatchmentRelationshipsTab(QWidget):
    """Tab for defining catchment CSO relationships for multi-tank analysis."""

    relationships_changed = pyqtSignal()

    COLUMNS = [
        'CSO Name',
        'Upstream CSOs',
        'Downstream CSO',
        'Maximum Pass Forward Flow (m3/s)',
        'Distance (m)',
        'Average Velocity (m/s)',
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
            "Define catchment relationships between CSOs for multi-tank analysis. "
            "Specify which CSOs are upstream/downstream and their hydraulic connections. "
            "Only needed for Catchment Based Mode analysis. By default, all CSOs are independent."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "QLabel { color: #666; font-style: italic; margin: 5px; }")
        layout.addWidget(info_label)

        # Button toolbar
        button_layout = QHBoxLayout()

        self.auto_populate_btn = QPushButton("Auto-Populate from CSO Assets")
        self.auto_populate_btn.clicked.connect(self.auto_populate_from_assets)
        self.auto_populate_btn.setToolTip(
            "Add any CSO assets that aren't already in the relationships table")
        button_layout.addWidget(self.auto_populate_btn)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected)
        button_layout.addWidget(self.delete_btn)

        button_layout.addStretch()

        # self.validate_btn = QPushButton("Validate Relationships")
        # self.validate_btn.clicked.connect(self.validate_relationships)
        # self.validate_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        # button_layout.addWidget(self.validate_btn)

        # self.import_csv_btn = QPushButton("Import from CSV...")
        # self.import_csv_btn.clicked.connect(self.import_from_csv)
        # button_layout.addWidget(self.import_csv_btn)

        # self.export_csv_btn = QPushButton("Export to CSV...")
        # self.export_csv_btn.clicked.connect(self.export_to_csv)
        # button_layout.addWidget(self.export_csv_btn)

        layout.addLayout(button_layout)

        # Relationships table
        table_group = QGroupBox("Catchment Relationships")
        table_layout = QVBoxLayout()

        self.relationships_table = QTableWidget()
        self.relationships_table.setColumnCount(len(self.COLUMNS))
        self.relationships_table.setHorizontalHeaderLabels(self.COLUMNS)
        self.relationships_table.setAlternatingRowColors(True)
        self.relationships_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.relationships_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive)
        self.relationships_table.horizontalHeader().setStretchLastSection(True)

        # Set column widths
        self.relationships_table.setColumnWidth(0, 150)  # CSO Name
        self.relationships_table.setColumnWidth(1, 200)  # Upstream CSOs
        self.relationships_table.setColumnWidth(2, 150)  # Downstream CSO
        self.relationships_table.setColumnWidth(3, 150)  # Max PFF
        self.relationships_table.setColumnWidth(4, 120)  # Distance
        self.relationships_table.setColumnWidth(5, 140)  # Velocity

        # Connect signal
        self.relationships_table.itemChanged.connect(self.on_item_changed)

        table_layout.addWidget(self.relationships_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

    def set_cso_assets(self, assets: List[CSOAsset]):
        """Update available CSO assets."""
        self.cso_assets = assets
        self.available_csos = [asset.name for asset in assets]

    def auto_populate_from_assets(self):
        """Populate table with all CSO assets that aren't already in the table."""
        if not self.available_csos:
            QMessageBox.warning(
                self,
                "No CSO Assets",
                "Please define CSO assets in the CSO Assets tab first."
            )
            return

        # Get existing CSO names in table
        existing_csos = set()
        for row in range(self.relationships_table.rowCount()):
            cso_name = self.relationships_table.item(row, 0)
            if cso_name:
                existing_csos.add(cso_name.text())

        # Add missing CSOs
        added_count = 0
        for cso_name in self.available_csos:
            if cso_name not in existing_csos:
                self.add_relationship_row(cso_name)
                added_count += 1

        if added_count > 0:
            QMessageBox.information(
                self,
                "Auto-Populate Complete",
                f"Added {added_count} CSO(s) to the catchment relationships table."
            )
            self.relationships_changed.emit()
        else:
            QMessageBox.information(
                self,
                "No Changes",
                "All CSO assets are already in the relationships table."
            )

    def add_relationship_row(self, cso_name: str):
        """Add a new relationship row with default values."""
        row = self.relationships_table.rowCount()
        self.relationships_table.insertRow(row)

        # CSO Name (read-only)
        name_item = QTableWidgetItem(cso_name)
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.relationships_table.setItem(row, 0, name_item)

        # Upstream CSOs (button to open multi-select dialog)
        upstream_label = QLabel("(none)")
        upstream_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upstream_label.setStyleSheet("QLabel { color: #999; }")
        upstream_container = QWidget()
        upstream_layout = QHBoxLayout(upstream_container)
        upstream_layout.setContentsMargins(2, 2, 2, 2)

        edit_upstream_btn = QPushButton("Edit...")
        edit_upstream_btn.clicked.connect(
            lambda checked, r=row: self.edit_upstream_csos(r))
        upstream_layout.addWidget(upstream_label)
        upstream_layout.addWidget(edit_upstream_btn)

        self.relationships_table.setCellWidget(row, 1, upstream_container)
        upstream_container.setProperty("upstream_label", upstream_label)
        upstream_container.setProperty("upstream_csos", [])

        # Downstream CSO (dropdown)
        downstream_combo = QComboBox()
        downstream_combo.addItem("(none)")
        other_csos = [name for name in self.available_csos if name != cso_name]
        downstream_combo.addItems(other_csos)
        downstream_combo.currentTextChanged.connect(
            lambda: self.relationships_changed.emit())
        self.relationships_table.setCellWidget(row, 2, downstream_combo)

        # Max PFF (spinbox)
        max_pff_spin = QDoubleSpinBox()
        max_pff_spin.setRange(0, 1000)
        max_pff_spin.setDecimals(5)
        max_pff_spin.setSingleStep(0.001)
        max_pff_spin.setValue(0.0)
        max_pff_spin.setSpecialValueText("Unknown")
        max_pff_spin.valueChanged.connect(
            lambda: self.relationships_changed.emit())
        self.relationships_table.setCellWidget(row, 3, max_pff_spin)

        # Distance (spinbox)
        distance_spin = QDoubleSpinBox()
        distance_spin.setRange(0, 100000)
        distance_spin.setDecimals(1)
        distance_spin.setSingleStep(10)
        distance_spin.setValue(0.0)
        distance_spin.setSuffix(" m")
        distance_spin.valueChanged.connect(
            lambda: self.relationships_changed.emit())
        self.relationships_table.setCellWidget(row, 4, distance_spin)

        # Average Velocity (spinbox)
        velocity_spin = QDoubleSpinBox()
        velocity_spin.setRange(0, 10)
        velocity_spin.setDecimals(3)
        velocity_spin.setSingleStep(0.1)
        velocity_spin.setValue(0.0)
        velocity_spin.setSuffix(" m/s")
        velocity_spin.valueChanged.connect(
            lambda: self.relationships_changed.emit())
        self.relationships_table.setCellWidget(row, 5, velocity_spin)

    def edit_upstream_csos(self, row: int):
        """Open dialog to edit upstream CSOs for a row."""
        # Get current CSO name
        cso_name = self.relationships_table.item(row, 0).text()

        # Get available CSOs (exclude self)
        available = [name for name in self.available_csos if name != cso_name]

        # Get current selection
        upstream_container = self.relationships_table.cellWidget(row, 1)
        current_upstream = upstream_container.property("upstream_csos")

        # Open dialog
        dialog = MultiSelectDialog(available, current_upstream, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected_csos()
            upstream_container.setProperty("upstream_csos", selected)

            # Update label
            upstream_label = upstream_container.property("upstream_label")
            if selected:
                upstream_label.setText(", ".join(selected))
                upstream_label.setStyleSheet("QLabel { color: black; }")
            else:
                upstream_label.setText("(none)")
                upstream_label.setStyleSheet("QLabel { color: #999; }")

            self.relationships_changed.emit()

    def delete_selected(self):
        """Delete selected relationship rows."""
        selected_rows = set()
        for item in self.relationships_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            QMessageBox.warning(
                self, "No Selection", "Please select rows to delete.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete {len(selected_rows)} relationship(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            for row in sorted(selected_rows, reverse=True):
                self.relationships_table.removeRow(row)
            self.relationships_changed.emit()

    def on_item_changed(self, item: QTableWidgetItem):
        """Emit signal when table data changes."""
        self.relationships_changed.emit()

    def validate_relationships(self):
        """Validate catchment relationships for circular dependencies and missing references."""
        try:
            relationships = self.get_relationships()

            if not relationships:
                QMessageBox.information(
                    self,
                    "No Relationships",
                    "No catchment relationships defined. All CSOs are independent."
                )
                return

            errors = []
            warnings = []

            # Check for circular dependencies
            for rel in relationships:
                if self._has_circular_dependency(rel, relationships):
                    errors.append(
                        f"Circular dependency detected involving '{rel.cso_name}'")

            # Check for missing CSO references
            all_cso_names = set(self.available_csos)
            for rel in relationships:
                # Check upstream CSOs exist
                for upstream in rel.upstream_csos:
                    if upstream not in all_cso_names:
                        errors.append(
                            f"'{rel.cso_name}' references unknown upstream CSO '{upstream}'")

                # Check downstream CSO exists
                if rel.downstream_cso and rel.downstream_cso not in all_cso_names:
                    errors.append(
                        f"'{rel.cso_name}' references unknown downstream CSO '{rel.downstream_cso}'")

                # Check for distance/velocity when downstream specified
                if rel.downstream_cso:
                    if not rel.distance_to_downstream or rel.distance_to_downstream <= 0:
                        warnings.append(
                            f"'{rel.cso_name}' has downstream CSO but no distance specified")
                    if not rel.average_velocity or rel.average_velocity <= 0:
                        warnings.append(
                            f"'{rel.cso_name}' has downstream CSO but no velocity specified")

                # Check for max PFF when upstream specified
                if rel.upstream_csos and not rel.max_pff:
                    warnings.append(
                        f"'{rel.cso_name}' has upstream CSOs but no Max PFF specified")

            if errors:
                QMessageBox.critical(
                    self,
                    "Validation Errors",
                    "The following errors were found:\n\n" + "\n".join(errors)
                )
            elif warnings:
                QMessageBox.warning(
                    self,
                    "Validation Warnings",
                    "The following warnings were found:\n\n" +
                    "\n".join(warnings)
                )
            else:
                QMessageBox.information(
                    self,
                    "Validation Passed",
                    "All catchment relationships are valid."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Validation Error",
                f"Error validating relationships: {str(e)}"
            )

    def _has_circular_dependency(
            self, rel: CatchmentRelationship,
            all_rels: List[CatchmentRelationship],
            visited: Optional[set] = None) -> bool:
        """Check if a relationship has circular dependencies."""
        if visited is None:
            visited = set()

        if rel.cso_name in visited:
            return True

        visited.add(rel.cso_name)

        # Check all upstream CSOs
        for upstream_name in rel.upstream_csos:
            upstream_rel = next(
                (r for r in all_rels if r.cso_name == upstream_name), None)
            if upstream_rel and self._has_circular_dependency(upstream_rel, all_rels, visited.copy()):
                return True

        return False

    def get_relationships(self) -> List[CatchmentRelationship]:
        """Extract catchment relationships from table."""
        relationships = []

        for row in range(self.relationships_table.rowCount()):
            cso_name = self.relationships_table.item(row, 0).text()

            # Get upstream CSOs
            upstream_container = self.relationships_table.cellWidget(row, 1)
            upstream_csos = upstream_container.property("upstream_csos")

            # Get downstream CSO
            downstream_combo = self.relationships_table.cellWidget(row, 2)
            downstream_text = downstream_combo.currentText()
            downstream_cso = downstream_text if downstream_text != "(none)" else None

            # Get numeric values
            max_pff_spin = self.relationships_table.cellWidget(row, 3)
            max_pff = max_pff_spin.value() if max_pff_spin.value() > 0 else None

            distance_spin = self.relationships_table.cellWidget(row, 4)
            distance = distance_spin.value() if distance_spin.value() > 0 else None

            velocity_spin = self.relationships_table.cellWidget(row, 5)
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

        return relationships

    def set_relationships(self, relationships: List[CatchmentRelationship]):
        """Load relationships into table."""
        self.relationships_table.setRowCount(0)

        for rel in relationships:
            self.add_relationship_row(rel.cso_name)
            row = self.relationships_table.rowCount() - 1

            # Set upstream CSOs
            upstream_container = self.relationships_table.cellWidget(row, 1)
            upstream_container.setProperty("upstream_csos", rel.upstream_csos)
            upstream_label = upstream_container.property("upstream_label")
            if rel.upstream_csos:
                upstream_label.setText(", ".join(rel.upstream_csos))
                upstream_label.setStyleSheet("QLabel { color: black; }")

            # Set downstream CSO
            if rel.downstream_cso:
                downstream_combo = self.relationships_table.cellWidget(row, 2)
                index = downstream_combo.findText(rel.downstream_cso)
                if index >= 0:
                    downstream_combo.setCurrentIndex(index)

            # Set numeric values
            if rel.max_pff:
                max_pff_spin = self.relationships_table.cellWidget(row, 3)
                max_pff_spin.setValue(rel.max_pff)

            if rel.distance_to_downstream:
                distance_spin = self.relationships_table.cellWidget(row, 4)
                distance_spin.setValue(rel.distance_to_downstream)

            if rel.average_velocity:
                velocity_spin = self.relationships_table.cellWidget(row, 5)
                velocity_spin.setValue(rel.average_velocity)

    def import_from_csv(self):
        """Import relationships from CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Catchment Relationships", "", "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            df = pd.read_csv(file_path)
            relationships = [CatchmentRelationship.from_dict(
                row) for _, row in df.iterrows()]
            self.set_relationships(relationships)
            self.relationships_changed.emit()

            QMessageBox.information(
                self,
                "Import Successful",
                f"Imported {len(relationships)} catchment relationship(s)."
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Import Failed", f"Failed to import relationships:\n{str(e)}"
            )

    def export_to_csv(self):
        """Export relationships to CSV file."""
        if self.relationships_table.rowCount() == 0:
            QMessageBox.warning(
                self, "No Data", "No relationships to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Catchment Relationships", "", "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            relationships = self.get_relationships()
            df = pd.DataFrame([rel.to_dict() for rel in relationships])
            df.to_csv(file_path, index=False)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {len(relationships)} catchment relationship(s) to {file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Export Failed", f"Failed to export relationships:\n{str(e)}"
            )

    def get_state(self) -> dict:
        """Get current state for project save."""
        relationships = self.get_relationships()
        return {
            'relationships': [rel.to_dict() for rel in relationships]
        }

    def load_state(self, state: dict):
        """Load state from project file."""
        if 'relationships' in state:
            relationships = [
                CatchmentRelationship.from_dict(rel_dict)
                for rel_dict in state['relationships']
            ]
            self.set_relationships(relationships)
