"""WwTW Assets Tab - Define wastewater treatment works assets."""

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
    QMessageBox,
    QHeaderView,
    QAbstractItemView,
    QFileDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QListWidget,
)

from plato.refactored import WWTWAsset
import pandas as pd


class MultiLinkSelectorDialog(QDialog):
    """Dialog to select multiple links for spill/pump links."""

    def __init__(self, available_links: List[str], title: str = "Select Links",
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.available_links = available_links
        self.selected_links: List[str] = []
        self.dialog_title = title
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.dialog_title)
        self.setModal(True)
        self.resize(400, 400)

        layout = QVBoxLayout(self)

        # Info label
        info = QLabel("Select one or more links from the list below:")
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

        if not self.selected_links:
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "Please select at least one link.",
            )
            return

        super().accept()

    def get_selected_links(self) -> List[str]:
        """Get the selected link names."""
        return self.selected_links


class WWTWAssetsTab(QWidget):
    """Tab for defining WwTW (Wastewater Treatment Works) assets."""

    assets_changed = pyqtSignal()  # Emitted when assets are added/removed/modified

    COLUMNS = [
        'WwTW Name',
        'Spill Links',
        'FFT Link',
        'Pump Links (Optional)',
    ]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.available_links: List[str] = []
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Info label
        info_label = QLabel(
            "Define WwTW assets by specifying spill links, FFT (pass-forward) link, "
            "and optional pump links. Links are imported from the Data Import tab."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "QLabel { color: #666; font-style: italic; margin: 5px; }")
        layout.addWidget(info_label)

        # Button toolbar
        button_layout = QHBoxLayout()

        self.add_asset_btn = QPushButton("Add WwTW")
        self.add_asset_btn.clicked.connect(self.add_asset)
        self.add_asset_btn.setEnabled(False)  # Disabled until links available
        button_layout.addWidget(self.add_asset_btn)

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

        # self.validate_btn = QPushButton("Validate WwTWs")
        # self.validate_btn.clicked.connect(self.validate_assets)
        # self.validate_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        # button_layout.addWidget(self.validate_btn)

        layout.addLayout(button_layout)

        # Assets table
        self.assets_table = QTableWidget()
        self.assets_table.setColumnCount(len(self.COLUMNS))
        self.assets_table.setHorizontalHeaderLabels(self.COLUMNS)
        self.assets_table.horizontalHeader().setStretchLastSection(True)
        self.assets_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive)
        self.assets_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.assets_table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        layout.addWidget(self.assets_table)

        # Status label
        self.status_label = QLabel("No WwTW assets defined")
        self.status_label.setStyleSheet("QLabel { color: #666; margin: 5px; }")
        layout.addWidget(self.status_label)

        self.update_status()

    def set_available_links(self, links: List[str]) -> None:
        """Update available links from data import tab."""
        self.available_links = links
        self.add_asset_btn.setEnabled(bool(links))
        self.update_status()

    def add_asset(self) -> None:
        """Add a new WwTW asset row."""
        if not self.available_links:
            QMessageBox.warning(
                self, "No Links Available",
                "Please import data in the Data Import tab first."
            )
            return

        row = self.assets_table.rowCount()
        self.assets_table.insertRow(row)

        # WwTW Name
        name_item = QTableWidgetItem(f"WwTW_{row + 1}")
        self.assets_table.setItem(row, 0, name_item)

        # Spill Links (clickable button to select multiple)
        spill_label = QLabel("(click to select)")
        spill_label.setStyleSheet(
            "QLabel { color: blue; text-decoration: underline; }")
        spill_label.setCursor(Qt.CursorShape.PointingHandCursor)
        spill_label.mousePressEvent = lambda event, r=row: self.select_spill_links(
            r)
        self.assets_table.setCellWidget(row, 1, spill_label)

        # FFT Link dropdown
        fft_combo = QComboBox()
        fft_combo.setEditable(True)
        fft_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        fft_combo.addItem("(select link)")
        fft_combo.addItems(self.available_links)
        fft_combo.currentTextChanged.connect(
            lambda: self.assets_changed.emit())
        self.assets_table.setCellWidget(row, 2, fft_combo)

        # Pump Links (optional, clickable button)
        pump_label = QLabel("(optional - click to select)")
        pump_label.setStyleSheet(
            "QLabel { color: blue; text-decoration: underline; }")
        pump_label.setCursor(Qt.CursorShape.PointingHandCursor)
        pump_label.mousePressEvent = lambda event, r=row: self.select_pump_links(
            r)
        self.assets_table.setCellWidget(row, 3, pump_label)

        self.update_status()
        self.assets_changed.emit()

    def select_spill_links(self, row: int) -> None:
        """Show dialog to select spill links."""
        dialog = MultiLinkSelectorDialog(
            self.available_links, "Select Spill Links", self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected_links()
            if selected:
                label = self.assets_table.cellWidget(row, 1)
                if isinstance(label, QLabel):
                    label.setText(', '.join(selected))
                    label.setProperty("selected_links", selected)
                self.assets_changed.emit()

    def select_pump_links(self, row: int) -> None:
        """Show dialog to select pump links (optional)."""
        dialog = MultiLinkSelectorDialog(
            self.available_links, "Select Pump Links (Optional)", self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected_links()
            label = self.assets_table.cellWidget(row, 3)
            if isinstance(label, QLabel):
                if selected:
                    label.setText(', '.join(selected))
                    label.setProperty("selected_links", selected)
                else:
                    label.setText("(none)")
                    label.setProperty("selected_links", [])
            self.assets_changed.emit()

    def delete_selected(self) -> None:
        """Delete selected asset rows."""
        selected_rows = set(index.row()
                            for index in self.assets_table.selectedIndexes())
        for row in sorted(selected_rows, reverse=True):
            self.assets_table.removeRow(row)

        self.update_status()
        self.assets_changed.emit()

    def update_status(self) -> None:
        """Update status label."""
        count = self.assets_table.rowCount()
        links_available = len(self.available_links)

        if count == 0:
            self.status_label.setText("No WwTW assets defined")
        else:
            self.status_label.setText(
                f"{count} WwTW asset(s) defined | {links_available} link(s) available from data import")

    def get_assets(self) -> List[WWTWAsset]:
        """Get all defined WwTW assets."""
        assets = []

        for row in range(self.assets_table.rowCount()):
            try:
                # Get name
                name_item = self.assets_table.item(row, 0)
                if not name_item or not name_item.text().strip():
                    continue
                name = name_item.text().strip()

                # Get spill links
                spill_widget = self.assets_table.cellWidget(row, 1)
                spill_links = []
                if isinstance(spill_widget, QLabel):
                    spill_links = spill_widget.property("selected_links") or []

                if not spill_links:
                    continue

                # Get FFT link
                fft_widget = self.assets_table.cellWidget(row, 2)
                fft_link = ""
                if isinstance(fft_widget, QComboBox):
                    fft_link = fft_widget.currentText()

                if not fft_link or fft_link == "(select link)":
                    continue

                # Get pump links (optional)
                pump_widget = self.assets_table.cellWidget(row, 3)
                pump_links = []
                if isinstance(pump_widget, QLabel):
                    pump_links = pump_widget.property("selected_links") or []

                # Create asset
                asset = WWTWAsset(
                    name=name,
                    spill_links=spill_links,
                    fft_link=fft_link,
                    pump_links=pump_links
                )
                assets.append(asset)

            except (ValueError, AttributeError) as e:
                print(f"Error parsing WwTW asset at row {row}: {e}")
                continue

        return assets

    def validate_assets(self) -> None:
        """Validate all defined assets."""
        assets = self.get_assets()

        if not assets:
            QMessageBox.warning(
                self,
                "No Assets",
                "No valid WwTW assets defined. Please add at least one WwTW asset."
            )
            return

        # Check for valid links
        invalid_assets = []
        available_set = set(self.available_links)

        for asset in assets:
            # Check spill links
            for link in asset.spill_links:
                if link not in available_set:
                    invalid_assets.append(
                        f"{asset.name}: Spill link '{link}' not found in imported data")
                    break

            # Check FFT link
            if asset.fft_link not in available_set:
                invalid_assets.append(
                    f"{asset.name}: FFT link '{asset.fft_link}' not found in imported data")

            # Check pump links
            for link in asset.pump_links:
                if link not in available_set:
                    invalid_assets.append(
                        f"{asset.name}: Pump link '{link}' not found in imported data")
                    break

        if invalid_assets:
            QMessageBox.warning(
                self,
                "Invalid Assets",
                f"Found {len(invalid_assets)} issue(s):\n\n" +
                "\n".join(invalid_assets[:10])
            )
        else:
            QMessageBox.information(
                self,
                "Validation Success",
                f"All {len(assets)} WwTW asset(s) are valid!"
            )

    def export_to_csv(self) -> None:
        """Export assets to CSV file."""
        assets = self.get_assets()

        if not assets:
            QMessageBox.warning(
                self, "No Assets", "No WwTW assets to export.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export WwTW Assets", "", "CSV Files (*.csv)")

        if filename:
            try:
                df = pd.DataFrame([asset.to_dict() for asset in assets])
                df.to_csv(filename, index=False)
                QMessageBox.information(
                    self, "Export Success", f"Exported {len(assets)} WwTW asset(s) to {filename}")
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Failed", f"Failed to export assets:\n{str(e)}")

    def import_from_csv(self) -> None:
        """Import assets from CSV file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import WwTW Assets", "", "CSV Files (*.csv)")

        if not filename:
            return

        try:
            df = pd.read_csv(filename)
            self.assets_table.setRowCount(0)  # Clear existing

            for _, row in df.iterrows():
                asset = WWTWAsset.from_dict(row.to_dict())
                self.add_asset_from_object(asset)

            self.assets_changed.emit()
            QMessageBox.information(
                self, "Import Success", f"Imported {len(df)} WwTW asset(s)")

        except Exception as e:
            QMessageBox.critical(
                self, "Import Failed", f"Failed to import assets:\n{str(e)}")

    def add_asset_from_object(self, asset: WWTWAsset) -> None:
        """Add an asset from a WWTWAsset object (for import/load)."""
        row = self.assets_table.rowCount()
        self.assets_table.insertRow(row)

        # Name
        name_item = QTableWidgetItem(asset.name)
        self.assets_table.setItem(row, 0, name_item)

        # Spill Links
        spill_label = QLabel(', '.join(asset.spill_links))
        spill_label.setStyleSheet(
            "QLabel { color: blue; text-decoration: underline; }")
        spill_label.setCursor(Qt.CursorShape.PointingHandCursor)
        spill_label.setProperty("selected_links", asset.spill_links)
        spill_label.mousePressEvent = lambda event, r=row: self.select_spill_links(
            r)
        self.assets_table.setCellWidget(row, 1, spill_label)

        # FFT Link
        fft_combo = QComboBox()
        fft_combo.setEditable(True)
        fft_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        fft_combo.addItem("(select link)")
        fft_combo.addItems(self.available_links)
        fft_combo.setCurrentText(asset.fft_link)
        fft_combo.currentTextChanged.connect(
            lambda: self.assets_changed.emit())
        self.assets_table.setCellWidget(row, 2, fft_combo)

        # Pump Links
        pump_text = ', '.join(
            asset.pump_links) if asset.pump_links else "(none)"
        pump_label = QLabel(pump_text)
        pump_label.setStyleSheet(
            "QLabel { color: blue; text-decoration: underline; }")
        pump_label.setCursor(Qt.CursorShape.PointingHandCursor)
        pump_label.setProperty("selected_links", asset.pump_links)
        pump_label.mousePressEvent = lambda event, r=row: self.select_pump_links(
            r)
        self.assets_table.setCellWidget(row, 3, pump_label)

        self.update_status()

    def get_state(self) -> dict:
        """Get current state for saving to project file."""
        assets = self.get_assets()
        return {
            'assets': [
                {
                    'name': asset.name,
                    'spill_links': asset.spill_links,
                    'fft_link': asset.fft_link,
                    'pump_links': asset.pump_links,
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
                    asset = WWTWAsset(
                        name=asset_data['name'],
                        spill_links=asset_data['spill_links'],
                        fft_link=asset_data['fft_link'],
                        pump_links=asset_data.get('pump_links', []),
                    )
                    self.add_asset_from_object(asset)
                except Exception as e:
                    print(f"Error loading WwTW asset: {e}")
                    continue

        self.assets_changed.emit()
