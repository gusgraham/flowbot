"""CSO Assets Tab - Define which links represent each CSO."""

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
    QDialog,
    QDialogButtonBox,
    QListWidget,
)

from plato.refactored import CSOAsset
import pandas as pd


class EffectiveLinkDialog(QDialog):
    """Dialog to build an effective link from multiple component links."""

    def __init__(self, available_links: List[str], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.available_links = available_links
        self.selected_links: List[str] = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Build Effective Link")
        self.setModal(True)
        self.resize(400, 400)

        layout = QVBoxLayout(self)

        # Info label
        info = QLabel(
            "Select 2 or more links to combine into a single effective link.\n"
            "The effective link will use the combined (summed) flow from all selected links."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # List of available links
        self.link_list = QListWidget()
        self.link_list.addItems(self.available_links)
        self.link_list.setSelectionMode(
            QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(QLabel("Available Links:"))
        layout.addWidget(self.link_list)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        """Validate and accept selection."""
        selected_items = self.link_list.selectedItems()
        self.selected_links = [item.text() for item in selected_items]

        if len(self.selected_links) < 2:
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "Please select at least 2 links to create an effective link.",
            )
            return

        super().accept()

    def get_selected_links(self) -> List[str]:
        """Get the selected link names."""
        return self.selected_links


class CSOAssetsTab(QWidget):
    """Tab for defining CSO assets (link groupings)."""

    assets_changed = pyqtSignal()  # Emitted when assets are added/removed/modified

    COLUMNS = [
        'CSO Name',
        'Overflow Link(s)',
        'Continuation Link',
    ]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.available_links: List[str] = []
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Info label
        info_label = QLabel(
            "Define CSO assets by specifying which overflow and continuation links represent each CSO. "
            "Links are imported from the Data Import tab. "
            "Use 'Build Effective Link' to combine multiple links into a single effective link "
            "(works for both overflow and continuation links)."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "QLabel { color: #666; font-style: italic; margin: 5px; }")
        layout.addWidget(info_label)

        # Button toolbar
        button_layout = QHBoxLayout()

        self.add_asset_btn = QPushButton("Add CSO")
        self.add_asset_btn.clicked.connect(self.add_asset)
        self.add_asset_btn.setEnabled(False)  # Disabled until links available
        button_layout.addWidget(self.add_asset_btn)

        self.duplicate_btn = QPushButton("Duplicate Selected")
        self.duplicate_btn.clicked.connect(self.duplicate_selected)
        button_layout.addWidget(self.duplicate_btn)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected)
        button_layout.addWidget(self.delete_btn)

        button_layout.addStretch()

        # self.import_csv_btn = QPushButton("Import from CSV...")
        # self.import_csv_btn.clicked.connect(self.import_from_csv)
        # button_layout.addWidget(self.import_csv_btn)

        # self.export_csv_btn = QPushButton("Export to CSV...")
        # self.export_csv_btn.clicked.connect(self.export_to_csv)
        # button_layout.addWidget(self.export_csv_btn)

        # self.validate_btn = QPushButton("Validate CSOs")
        # self.validate_btn.clicked.connect(self.validate_assets)
        # self.validate_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        # button_layout.addWidget(self.validate_btn)

        layout.addLayout(button_layout)

        # Assets table
        table_group = QGroupBox("CSO Asset Definitions")
        table_layout = QVBoxLayout()

        self.assets_table = QTableWidget()
        self.assets_table.setColumnCount(len(self.COLUMNS))
        self.assets_table.setHorizontalHeaderLabels(self.COLUMNS)
        self.assets_table.setAlternatingRowColors(True)
        self.assets_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.assets_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.assets_table.itemChanged.connect(self.on_item_changed)

        table_layout.addWidget(self.assets_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # Status label
        self.status_label = QLabel("No CSO assets defined. Import data first.")
        self.status_label.setStyleSheet(
            "QLabel { color: gray; font-style: italic; }")
        layout.addWidget(self.status_label)

    def set_available_links(self, links: List[str]) -> None:
        """Update available links from Data Import tab."""
        self.available_links = sorted(links)  # Already sorted alphabetically
        self.add_asset_btn.setEnabled(len(links) > 0)

        if len(links) > 0:
            self.status_label.setText(
                f"{len(links)} links available from data import")
        else:
            self.status_label.setText("No links available. Import data first.")

        # Update existing dropdowns
        for row in range(self.assets_table.rowCount()):
            overflow_widget = self.assets_table.cellWidget(row, 1)
            cont_widget = self.assets_table.cellWidget(row, 2)

            if isinstance(overflow_widget, QComboBox):
                current = overflow_widget.currentText()
                overflow_widget.clear()
                overflow_widget.setEditable(True)  # Enable type-to-search
                overflow_widget.setInsertPolicy(
                    QComboBox.InsertPolicy.NoInsert)
                overflow_widget.addItem("(select link)")
                overflow_widget.addItem("📊 Build Effective Link...")
                overflow_widget.addItems(self.available_links)
                if current in self.available_links:
                    overflow_widget.setCurrentText(current)

            if isinstance(cont_widget, QComboBox):
                current = cont_widget.currentText()
                cont_widget.clear()
                cont_widget.setEditable(True)  # Enable type-to-search
                cont_widget.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
                cont_widget.addItem("(select link)")
                cont_widget.addItem("📊 Build Effective Link...")
                cont_widget.addItems(self.available_links)
                if current in self.available_links or current.startswith("Effective("):
                    cont_widget.setCurrentText(current)

    def add_asset(self) -> None:
        """Add a new CSO asset row."""
        if not self.available_links:
            QMessageBox.warning(
                self, "No Links Available",
                "Please import data in the Data Import tab first."
            )
            return

        row = self.assets_table.rowCount()
        self.assets_table.insertRow(row)

        # CSO Name
        name_item = QTableWidgetItem(f"CSO_{row + 1}")
        self.assets_table.setItem(row, 0, name_item)

        # Overflow Link dropdown with search capability
        overflow_combo = QComboBox()
        overflow_combo.setEditable(True)  # Enable type-to-search
        overflow_combo.setInsertPolicy(
            QComboBox.InsertPolicy.NoInsert)  # Don't allow new items
        overflow_combo.addItem("(select link)")
        overflow_combo.addItem("📊 Build Effective Link...")
        overflow_combo.addItems(self.available_links)
        overflow_combo.currentTextChanged.connect(
            lambda text, r=row: self.on_overflow_link_changed(r, text))
        self.assets_table.setCellWidget(row, 1, overflow_combo)

        # Continuation Link dropdown with search capability
        cont_combo = QComboBox()
        cont_combo.setEditable(True)  # Enable type-to-search
        cont_combo.setInsertPolicy(
            QComboBox.InsertPolicy.NoInsert)  # Don't allow new items
        cont_combo.addItem("(select link)")
        cont_combo.addItem("📊 Build Effective Link...")
        cont_combo.addItems(self.available_links)
        cont_combo.currentTextChanged.connect(
            lambda text, r=row: self.on_continuation_link_changed(r, text))
        self.assets_table.setCellWidget(row, 2, cont_combo)

        self.update_status()
        self.assets_changed.emit()

    def on_overflow_link_changed(self, row: int, link_text: str) -> None:
        """Handle overflow link selection - show effective link dialog if needed."""
        if link_text == "📊 Build Effective Link...":
            dialog = EffectiveLinkDialog(self.available_links, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected = dialog.get_selected_links()
                combo = self.assets_table.cellWidget(row, 1)
                if combo and isinstance(combo, QComboBox):
                    # Update combo to show effective link
                    effective_name = f"Effective({', '.join(selected)})"
                    combo.blockSignals(True)
                    combo.clear()
                    combo.addItem(effective_name)
                    combo.addItem("📊 Build Effective Link...")
                    combo.addItems(self.available_links)
                    combo.setCurrentText(effective_name)
                    combo.blockSignals(False)

                    # Store component links in item data
                    combo.setProperty("effective_components", selected)
            else:
                # User cancelled - reset to first item
                combo = self.assets_table.cellWidget(row, 1)
                if combo:
                    combo.setCurrentIndex(0)

        self.assets_changed.emit()

    def on_continuation_link_changed(self, row: int, link_text: str) -> None:
        """Handle continuation link selection - show effective link dialog if needed."""
        if link_text == "📊 Build Effective Link...":
            dialog = EffectiveLinkDialog(self.available_links, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected = dialog.get_selected_links()
                combo = self.assets_table.cellWidget(row, 2)
                if combo and isinstance(combo, QComboBox):
                    # Update combo to show effective link
                    effective_name = f"Effective({', '.join(selected)})"
                    combo.blockSignals(True)
                    combo.clear()
                    combo.addItem(effective_name)
                    combo.addItem("📊 Build Effective Link...")
                    combo.addItems(self.available_links)
                    combo.setCurrentText(effective_name)
                    combo.blockSignals(False)

                    # Store component links in item data
                    combo.setProperty("effective_components", selected)
            else:
                # User cancelled - reset to first item
                combo = self.assets_table.cellWidget(row, 2)
                if combo:
                    combo.setCurrentIndex(0)

        self.assets_changed.emit()

    def add_asset_to_table(self, asset: CSOAsset) -> None:
        """Add a pre-populated asset to the table (for loading from file)."""
        row = self.assets_table.rowCount()
        self.assets_table.insertRow(row)

        # CSO Name
        name_item = QTableWidgetItem(asset.name)
        self.assets_table.setItem(row, 0, name_item)

        # Overflow Link dropdown
        overflow_combo = QComboBox()
        overflow_combo.setEditable(True)
        overflow_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        if asset.is_effective_link and asset.effective_link_components:
            # Create effective link display
            effective_name = f"Effective({', '.join(asset.effective_link_components)})"
            overflow_combo.addItem(effective_name)
            overflow_combo.addItem("📊 Build Effective Link...")
            overflow_combo.addItems(self.available_links)
            overflow_combo.setCurrentText(effective_name)
            overflow_combo.setProperty(
                "effective_components", asset.effective_link_components)
        else:
            overflow_combo.addItem("(select link)")
            overflow_combo.addItem("📊 Build Effective Link...")
            overflow_combo.addItems(self.available_links)
            if asset.overflow_links:
                overflow_combo.setCurrentText(asset.overflow_links[0])

        overflow_combo.currentTextChanged.connect(
            lambda text, r=row: self.on_overflow_link_changed(r, text))
        self.assets_table.setCellWidget(row, 1, overflow_combo)

        # Continuation Link dropdown
        cont_combo = QComboBox()
        cont_combo.setEditable(True)
        cont_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        # Check if continuation link is effective
        if asset.continuation_link.startswith("Effective(") and asset.continuation_link.endswith(")"):
            # Parse component links from "Effective(link1, link2, ...)"
            components_str = asset.continuation_link[10:-1]
            cont_components = [c.strip() for c in components_str.split(',')]

            cont_combo.addItem(asset.continuation_link)
            cont_combo.addItem("📊 Build Effective Link...")
            cont_combo.addItems(self.available_links)
            cont_combo.setCurrentText(asset.continuation_link)
            cont_combo.setProperty("effective_components", cont_components)
        else:
            cont_combo.addItem("(select link)")
            cont_combo.addItem("📊 Build Effective Link...")
            cont_combo.addItems(self.available_links)
            cont_combo.setCurrentText(asset.continuation_link)

        cont_combo.currentTextChanged.connect(
            lambda text, r=row: self.on_continuation_link_changed(r, text))
        self.assets_table.setCellWidget(row, 2, cont_combo)

        self.update_status()

    def duplicate_selected(self) -> None:
        """Duplicate selected CSO asset rows."""
        selected_rows = set(item.row()
                            for item in self.assets_table.selectedItems())
        if not selected_rows:
            QMessageBox.warning(self, "No Selection",
                                "Please select a CSO to duplicate.")
            return

        for row in sorted(selected_rows):
            self.add_asset()
            new_row = self.assets_table.rowCount() - 1

            # Copy name with _copy suffix
            name_item = self.assets_table.item(row, 0)
            if name_item:
                new_name_item = self.assets_table.item(new_row, 0)
                if new_name_item:
                    new_name_item.setText(f"{name_item.text()}_copy")

            # Copy overflow link
            overflow_widget = self.assets_table.cellWidget(row, 1)
            new_overflow = self.assets_table.cellWidget(new_row, 1)
            if overflow_widget and new_overflow and isinstance(overflow_widget, QComboBox):
                new_overflow.setCurrentText(overflow_widget.currentText())
                # Copy effective components if any
                components = overflow_widget.property("effective_components")
                if components:
                    new_overflow.setProperty(
                        "effective_components", components)

            # Copy continuation link
            cont_widget = self.assets_table.cellWidget(row, 2)
            new_cont = self.assets_table.cellWidget(new_row, 2)
            if cont_widget and new_cont and isinstance(cont_widget, QComboBox):
                new_cont.setCurrentText(cont_widget.currentText())
                # Copy effective components if any
                components = cont_widget.property("effective_components")
                if components:
                    new_cont.setProperty("effective_components", components)

        self.assets_changed.emit()

    def delete_selected(self) -> None:
        """Delete selected CSO asset rows."""
        selected_rows = set(item.row()
                            for item in self.assets_table.selectedItems())
        if not selected_rows:
            QMessageBox.warning(self, "No Selection",
                                "Please select CSOs to delete.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete {len(selected_rows)} selected CSO(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            for row in sorted(selected_rows, reverse=True):
                self.assets_table.removeRow(row)
            self.update_status()
            self.assets_changed.emit()

    def get_assets(self) -> List[CSOAsset]:
        """Get all CSO assets from the table."""
        assets = []
        for row in range(self.assets_table.rowCount()):
            try:
                asset = self.get_asset_from_row(row)
                if asset:
                    assets.append(asset)
            except Exception:
                continue  # Skip invalid rows
        return assets

    def get_asset_from_row(self, row: int) -> Optional[CSOAsset]:
        """Extract CSOAsset from a table row."""
        name_item = self.assets_table.item(row, 0)
        overflow_combo = self.assets_table.cellWidget(row, 1)
        cont_combo = self.assets_table.cellWidget(row, 2)

        if not all([name_item, overflow_combo, cont_combo]):
            return None

        cso_name = name_item.text().strip()
        overflow_text = overflow_combo.currentText() if isinstance(
            overflow_combo, QComboBox) else ""
        cont_text = cont_combo.currentText() if isinstance(cont_combo, QComboBox) else ""

        if not cso_name or overflow_text in ["(select link)", ""] or cont_text in ["(select link)", ""]:
            return None

        # Check if overflow is effective link
        is_overflow_effective = overflow_text.startswith("Effective(")
        overflow_effective_components = overflow_combo.property(
            "effective_components") if is_overflow_effective else None
        overflow_links = overflow_effective_components if is_overflow_effective else [
            overflow_text]

        # Check if continuation is effective link
        is_cont_effective = cont_text.startswith("Effective(")
        cont_effective_components = cont_combo.property(
            "effective_components") if is_cont_effective else None
        # Use the text directly if it's effective, otherwise use cont_text
        continuation_link = cont_text

        try:
            return CSOAsset(
                name=cso_name,
                overflow_links=overflow_links,
                continuation_link=continuation_link,
                is_effective_link=is_overflow_effective,
                effective_link_components=overflow_effective_components,
            )
        except Exception:
            return None

    def get_asset_names(self) -> List[str]:
        """Get list of CSO names (including incomplete assets)."""
        names = []
        for row in range(self.assets_table.rowCount()):
            name_item = self.assets_table.item(row, 0)
            if name_item:
                name = name_item.text().strip()
                if name:
                    names.append(name)
        return names

    def validate_assets(self) -> bool:
        """Validate all CSO assets."""
        if self.assets_table.rowCount() == 0:
            QMessageBox.warning(self, "No Assets", "No CSO assets defined.")
            return False

        errors = []
        valid_count = 0

        for row in range(self.assets_table.rowCount()):
            try:
                asset = self.get_asset_from_row(row)
                if asset:
                    valid_count += 1
                else:
                    errors.append(f"Row {row + 1}: Incomplete data")
            except ValueError as e:
                errors.append(f"Row {row + 1}: {str(e)}")
            except Exception as e:
                errors.append(f"Row {row + 1}: {str(e)}")

        if errors:
            error_msg = "Validation errors found:\n\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                error_msg += f"\n\n...and {len(errors) - 10} more errors"
            QMessageBox.warning(self, "Validation Failed", error_msg)
            return False
        else:
            QMessageBox.information(
                self, "Validation Successful",
                f"All {valid_count} CSO asset(s) are valid!"
            )
            return True

    def import_from_csv(self) -> None:
        """Import CSO assets from CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import CSO Assets", "", "CSV Files (*.csv)"
        )
        if not file_path:
            return

        try:
            df = pd.read_csv(file_path)
            self.assets_table.setRowCount(0)

            for _, row_data in df.iterrows():
                try:
                    asset = CSOAsset.from_dict(row_data.to_dict())
                    # Add to table (would need implementation)
                    # self.add_asset_to_table(asset)
                except Exception:
                    continue

            self.update_status()
            self.assets_changed.emit()
            QMessageBox.information(
                self, "Import Complete",
                f"Imported {self.assets_table.rowCount()} CSO asset(s)"
            )

        except Exception as e:
            QMessageBox.critical(self, "Import Failed",
                                 f"Failed to import CSV:\n{str(e)}")

    def export_to_csv(self) -> None:
        """Export CSO assets to CSV file."""
        if self.assets_table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "No CSO assets to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export CSO Assets", "cso_assets.csv", "CSV Files (*.csv)"
        )
        if not file_path:
            return

        try:
            assets = self.get_assets()
            if not assets:
                QMessageBox.warning(self, "No Valid Data",
                                    "No valid CSO assets to export.")
                return

            data = [asset.to_dict() for asset in assets]
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)

            QMessageBox.information(
                self, "Export Complete",
                f"Exported {len(assets)} CSO asset(s) to {file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Export Failed",
                                 f"Failed to export CSV:\n{str(e)}")

    def update_status(self) -> None:
        """Update the status label."""
        count = self.assets_table.rowCount()
        if count == 0:
            self.status_label.setText("No CSO assets defined")
        elif count == 1:
            self.status_label.setText("1 CSO asset defined")
        else:
            self.status_label.setText(f"{count} CSO assets defined")

    def on_item_changed(self, item: QTableWidgetItem) -> None:
        """Handle item changes in table."""
        self.assets_changed.emit()

    def validate_assets_against_data(self, available_links: List[str]) -> None:
        """Validate existing assets against new data and mark invalid ones."""
        if not available_links:
            return

        available_set = set(available_links)

        for row in range(self.assets_table.rowCount()):
            overflow_combo = self.assets_table.cellWidget(row, 1)
            cont_combo = self.assets_table.cellWidget(row, 2)
            name_item = self.assets_table.item(row, 0)

            if not all([overflow_combo, cont_combo, name_item]):
                continue

            # Check overflow links
            overflow_text = overflow_combo.currentText()
            is_valid = True

            # Check if it's an effective link
            if overflow_text.startswith("Effective("):
                effective_components = overflow_combo.property(
                    "effective_components")
                if effective_components:
                    # Check all components exist in new data
                    for link in effective_components:
                        if link not in available_set:
                            is_valid = False
                            break
            elif overflow_text and overflow_text not in ["(select link)"]:
                # Check single overflow link
                if overflow_text not in available_set:
                    is_valid = False

            # Check continuation link
            cont_link = cont_combo.currentText()
            if cont_link and cont_link not in ["(select link)", "📊 Build Effective Link..."]:
                # Check if it's an effective continuation link
                if cont_link.startswith("Effective("):
                    cont_components = cont_combo.property(
                        "effective_components")
                    if cont_components:
                        # Check all components exist in new data
                        for link in cont_components:
                            if link not in available_set:
                                is_valid = False
                                break
                else:
                    # Check single continuation link
                    if cont_link not in available_set:
                        is_valid = False

            # Mark row as invalid if links don't exist
            if not is_valid:
                name_item.setBackground(Qt.GlobalColor.red)
                name_item.setToolTip(
                    "⚠️ Warning: Some links in this asset do not exist in the imported data")
            else:
                name_item.setBackground(Qt.GlobalColor.white)
                name_item.setToolTip("")

    def is_asset_valid(self, asset: CSOAsset) -> bool:
        """Check if an asset references valid links from current data."""
        if not self.available_links:
            return False

        available_set = set(self.available_links)

        # Check overflow links
        for link in asset.overflow_links:
            if link not in available_set:
                return False

        # Check continuation link
        if asset.continuation_link not in available_set:
            return False

        return True

    def get_state(self) -> dict:
        """Get current state for saving to project file."""
        assets = self.get_assets()
        return {
            'assets': [
                {
                    'name': asset.name,
                    'overflow_links': asset.overflow_links,
                    'continuation_link': asset.continuation_link,
                    'is_effective_link': asset.is_effective_link,
                    'effective_link_components': asset.effective_link_components,
                }
                for asset in assets
            ],
            'available_links': self.available_links,
        }

    def load_state(self, state: dict) -> None:
        """Load state from project file."""
        # Clear existing assets
        self.assets_table.setRowCount(0)

        # Restore available links
        if 'available_links' in state:
            self.set_available_links(state['available_links'])

        # Restore assets
        if 'assets' in state:
            for asset_data in state['assets']:
                try:
                    asset = CSOAsset(
                        name=asset_data['name'],
                        overflow_links=asset_data['overflow_links'],
                        continuation_link=asset_data['continuation_link'],
                        is_effective_link=asset_data.get(
                            'is_effective_link', False),
                        effective_link_components=asset_data.get(
                            'effective_link_components'),
                    )
                    self.add_asset_to_table(asset)
                except Exception as e:
                    print(f"Error loading asset: {e}")
                    continue

        self.assets_changed.emit()
