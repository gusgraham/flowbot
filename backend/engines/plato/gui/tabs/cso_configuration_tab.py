"""CSO Configuration Tab - Configure overflow parameters with validation."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import asdict

from PyQt6.QtCore import QDateTime, Qt, pyqtSignal, QRegularExpression
from PyQt6.QtGui import QAction, QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QWidget,
    QDialog,
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
    QMenu,
    QFileDialog,
    QDateTimeEdit,
    QDoubleSpinBox,
    QComboBox,
    QLineEdit,
    QSpinBox,
)

from plato.gui.widgets.effective_cso_builder import EffectiveCSOBuildDialog
from plato.refactored.config import EffectiveCSODefinition


class CSOConfigurationTab(QWidget):
    """Tab for configuring CSO overflow parameters."""

    config_validated = pyqtSignal(bool)

    COLUMNS = [
        'CSO Name',
        'Continuation Link',
        'Run Suffix',
        'Start Date (dd/mm/yy hh:mm:ss)',
        'End Date (dd/mm/yy hh:mm:ss)',
        'Spill Target (Entire Period)',
        'Spill Target (Bathing Seasons)',
        'Bathing Season Start (dd/mm)',
        'Bathing Season End (dd/mm)',
        'PFF Increase (m3/s)',
        'Tank Volume (m3)',
        'Pumping Mode',
        'Pump Rate (m3/s)',
        'Flow Return Threshold (m3/s)',
        'Depth Return Threshold (m)',
        'Time Delay (hours)',
        'Spill Flow Threshold (m3/s)',
        'Spill Volume Threshold (m3)',
    ]

    DATE_COLUMNS = {
        'Start Date (dd/mm/yy hh:mm:ss)': 'dd/MM/yyyy HH:mm:ss',
        'End Date (dd/mm/yy hh:mm:ss)': 'dd/MM/yyyy HH:mm:ss',
    }

    DATE_FORMATS = [
        '%d/%m/%Y %H:%M:%S',
        '%d/%m/%Y %H:%M',
        '%d/%m/%y %H:%M:%S',
        '%d/%m/%y %H:%M',
    ]

    NUMERIC_COLUMN_CONFIG: Dict[str, Dict[str, Any]] = {
        'Spill Target (Entire Period)': {'decimals': 0, 'max': 1000, 'step': 1},
        'Spill Target (Bathing Seasons)': {'decimals': 0, 'max': 1000, 'step': 1},
        'PFF Increase (m3/s)': {'decimals': 5, 'step': 1e-5},
        'Tank Volume (m3)': {'decimals': 0, 'max': 100000, 'step': 10},
        'Pump Rate (m3/s)': {'decimals': 5, 'step': 1e-5},
        'Flow Return Threshold (m3/s)': {'decimals': 5, 'step': 1e-5},
        'Depth Return Threshold (m)': {'decimals': 3, 'step': 0.05},
        'Time Delay (hours)': {'decimals': 0, 'max': 168, 'step': 1},
        'Spill Flow Threshold (m3/s)': {'decimals': 5, 'step': 1e-5},
        'Spill Volume Threshold (m3)': {'decimals': 0, 'max': 100000, 'step': 10},
    }

    DEFAULTS = {
        'Run Suffix': '1',
        'Spill Target (Entire Period)': '10',
        # Empty = ignore bathing season (Method 1)
        'Spill Target (Bathing Seasons)': '',
        'Bathing Season Start (dd/mm)': '15/05',
        'Bathing Season End (dd/mm)': '30/09',
        'PFF Increase (m3/s)': '0.0',
        'Tank Volume (m3)': '0',
        'Pumping Mode': 'Fixed',
        'Pump Rate (m3/s)': '0.0',
        'Flow Return Threshold (m3/s)': '0.0',
        'Depth Return Threshold (m)': '0.0',
        'Time Delay (hours)': '0',
        'Spill Flow Threshold (m3/s)': '0.001',
        'Spill Volume Threshold (m3)': '0.0',
    }

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.imported_data: Dict[str, Any] = {}
        self.available_links: List[str] = []
        self.data_start: Optional[datetime] = None
        self.data_end: Optional[datetime] = None
        self.effective_csos: List[EffectiveCSODefinition] = []
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)

        button_layout = QHBoxLayout()
        self.add_row_btn = QPushButton("Add Row")
        self.add_row_btn.clicked.connect(self.add_row)
        button_layout.addWidget(self.add_row_btn)

        self.build_cso_btn = QPushButton("Build Effective CSO...")
        self.build_cso_btn.clicked.connect(self.open_cso_builder)
        button_layout.addWidget(self.build_cso_btn)

        self.duplicate_row_btn = QPushButton("Duplicate Selected")
        self.duplicate_row_btn.clicked.connect(self.duplicate_selected_row)
        button_layout.addWidget(self.duplicate_row_btn)

        self.delete_row_btn = QPushButton("Delete Selected")
        self.delete_row_btn.clicked.connect(self.delete_selected_rows)
        button_layout.addWidget(self.delete_row_btn)

        button_layout.addStretch()

        # self.import_csv_btn = QPushButton("Import from CSV...")
        # self.import_csv_btn.clicked.connect(self.import_from_csv)
        # button_layout.addWidget(self.import_csv_btn)

        # self.export_csv_btn = QPushButton("Export to CSV...")
        # self.export_csv_btn.clicked.connect(self.export_to_csv)
        # button_layout.addWidget(self.export_csv_btn)

        # self.validate_btn = QPushButton("Validate Configuration")
        # self.validate_btn.clicked.connect(self.validate_configuration)
        # self.validate_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        # button_layout.addWidget(self.validate_btn)

        layout.addLayout(button_layout)

        table_group = QGroupBox("CSO Configuration Parameters")
        table_layout = QVBoxLayout()

        self.config_table = QTableWidget()
        self.config_table.setColumnCount(len(self.COLUMNS))
        self.config_table.setHorizontalHeaderLabels(self.COLUMNS)
        self.config_table.setAlternatingRowColors(True)
        self.config_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.config_table.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.config_table.customContextMenuRequested.connect(
            self.show_context_menu)

        header = self.config_table.horizontalHeader()
        for index in range(len(self.COLUMNS)):
            resize_mode = QHeaderView.ResizeMode.Stretch if index < 2 else QHeaderView.ResizeMode.ResizeToContents
            header.setSectionResizeMode(index, resize_mode)

        table_layout.addWidget(self.config_table)

        self.status_label = QLabel("No configuration loaded")
        self.status_label.setStyleSheet(
            "QLabel { color: gray; font-style: italic; }")
        table_layout.addWidget(self.status_label)

        table_group.setLayout(table_layout)
        layout.addWidget(table_group, 1)

        effective_group = QGroupBox("Effective CSO Definitions")
        effective_layout = QVBoxLayout()

        self.effective_table = QTableWidget()
        self.effective_table.setColumnCount(3)
        self.effective_table.setHorizontalHeaderLabels([
            'Name',
            'Continuation Links',
            'Overflow Links',
        ])
        effective_header = self.effective_table.horizontalHeader()
        effective_header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)
        effective_header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        effective_header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch)
        self.effective_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.effective_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        effective_layout.addWidget(self.effective_table)

        effective_group.setLayout(effective_layout)
        layout.addWidget(effective_group)

        self._set_controls_enabled(False)
        self._refresh_effective_table()

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------
    def _set_controls_enabled(self, enabled: bool) -> None:
        for button in [
            self.add_row_btn,
            self.build_cso_btn,
            self.duplicate_row_btn,
            self.delete_row_btn,
            # self.import_csv_btn,
            # self.export_csv_btn,
            # self.validate_btn,
        ]:
            button.setEnabled(enabled)

        self.config_table.setEnabled(enabled)
        self.effective_table.setEnabled(enabled)

    def open_cso_builder(self) -> None:
        if not self.config_table.isEnabled():
            QMessageBox.warning(
                self,
                "Data Required",
                "Please import data before defining effective CSOs.",
            )
            return

        if not self.available_links:
            QMessageBox.warning(
                self,
                "No Links Available",
                "Imported data does not contain any links to assemble.",
            )
            return

        dialog = EffectiveCSOBuildDialog(self.available_links, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        definition = dialog.get_definition()
        if definition is None:
            return

        if any(cso.name == definition.name for cso in self.effective_csos):
            QMessageBox.warning(
                self,
                "Duplicate Name",
                "An effective CSO with this name already exists.",
            )
            return

        self.effective_csos.append(definition)
        self._refresh_effective_table()
        self.status_label.setText(
            f"Defined {len(self.effective_csos)} effective CSO(s)."
        )
        self.status_label.setStyleSheet("QLabel { color: green; }")

    def _refresh_effective_table(self) -> None:
        self.effective_table.setRowCount(len(self.effective_csos))
        for row, definition in enumerate(self.effective_csos):
            self.effective_table.setItem(
                row,
                0,
                QTableWidgetItem(definition.name),
            )
            self.effective_table.setItem(
                row,
                1,
                QTableWidgetItem(", ".join(definition.continuation_links)),
            )
            self.effective_table.setItem(
                row,
                2,
                QTableWidgetItem(", ".join(definition.overflow_links)),
            )

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            for fmt in self.DATE_FORMATS:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return None

    def _to_qdatetime(self, dt_value: Optional[datetime]) -> QDateTime:
        dt_value = dt_value or datetime.now()
        return QDateTime(
            dt_value.year,
            dt_value.month,
            dt_value.day,
            dt_value.hour,
            dt_value.minute,
            dt_value.second,
        )

    def _create_spin_box(self, column_name: str, current_value: Any) -> QDoubleSpinBox:
        config = self.NUMERIC_COLUMN_CONFIG.get(column_name, {})
        spin = QDoubleSpinBox()
        spin.setDecimals(int(config.get('decimals', 3)))
        spin.setMinimum(float(config.get('min', 0.0)))
        spin.setMaximum(float(config.get('max', 1_000_000.0)))
        step = float(config.get('step', 0.1 if spin.decimals() else 1.0))
        spin.setSingleStep(step)
        try:
            spin.setValue(float(current_value))
        except (TypeError, ValueError):
            spin.setValue(spin.minimum())
        return spin

    def _create_int_spin_box(self, current_value: Any) -> QSpinBox:
        spin = QSpinBox()
        spin.setMinimum(1)
        spin.setMaximum(9_999)
        try:
            spin.setValue(int(current_value))
        except (TypeError, ValueError):
            spin.setValue(1)
        return spin

    def _populate_row(self, row: int, row_data: Dict[str, Any]) -> None:
        for column_index, column_name in enumerate(self.COLUMNS):
            value = row_data.get(
                column_name, self.DEFAULTS.get(column_name, ''))

            if column_name in self.DATE_COLUMNS:
                dt_widget = QDateTimeEdit()
                dt_widget.setDisplayFormat(self.DATE_COLUMNS[column_name])
                dt_widget.setCalendarPopup(True)

                fallback = self.data_start if 'Start' in column_name else self.data_end
                if fallback is None and self.data_start is not None:
                    fallback = self.data_start

                parsed_dt = self._parse_datetime(
                    value) or fallback or datetime.now()
                dt_widget.setDateTime(self._to_qdatetime(parsed_dt))
                self.config_table.setCellWidget(row, column_index, dt_widget)
                continue

            if column_name == 'Run Suffix':
                spin = self._create_int_spin_box(value)
                self.config_table.setCellWidget(row, column_index, spin)
                continue

            if column_name in self.NUMERIC_COLUMN_CONFIG:
                spin = self._create_spin_box(column_name, value)
                self.config_table.setCellWidget(row, column_index, spin)
                continue

            if column_name == 'Pumping Mode':
                combo = QComboBox()
                combo.addItems(['Fixed', 'Variable'])
                current = str(value) if value else self.DEFAULTS.get(
                    column_name, 'Fixed')
                index = combo.findText(current)
                combo.setCurrentText(combo.itemText(
                    index) if index >= 0 else current)
                self.config_table.setCellWidget(row, column_index, combo)
                continue

            if column_name in {'CSO Name', 'Continuation Link'} and self.available_links:
                combo = QComboBox()
                combo.setEditable(False)
                combo.addItems(self.available_links)
                current = str(value) if value else ''
                if current and combo.findText(current) >= 0:
                    combo.setCurrentText(current)
                elif self.available_links:
                    combo.setCurrentIndex(0)
                self.config_table.setCellWidget(row, column_index, combo)
                continue

            if column_name in {'Bathing Season Start (dd/mm)', 'Bathing Season End (dd/mm)'}:
                line_edit = QLineEdit()
                line_edit.setMaxLength(5)
                validator = QRegularExpressionValidator(
                    QRegularExpression(
                        r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])$")
                )
                line_edit.setValidator(validator)
                text_value = str(value) if value else self.DEFAULTS.get(
                    column_name, '')
                if not validator.regularExpression().match(text_value).hasMatch():
                    text_value = self.DEFAULTS.get(column_name, '')
                line_edit.setText(text_value)
                self.config_table.setCellWidget(row, column_index, line_edit)
                continue

            item = QTableWidgetItem(str(value) if value is not None else '')
            self.config_table.setItem(row, column_index, item)

    def _get_row_data(self, row: int) -> Dict[str, str]:
        row_data: Dict[str, str] = {}
        for column_index, column_name in enumerate(self.COLUMNS):
            widget = self.config_table.cellWidget(row, column_index)

            if isinstance(widget, QDateTimeEdit):
                row_data[column_name] = widget.dateTime().toString(
                    self.DATE_COLUMNS[column_name])
            elif isinstance(widget, QSpinBox):
                row_data[column_name] = str(widget.value())
            elif isinstance(widget, QDoubleSpinBox):
                decimals = widget.decimals()
                value = widget.value()
                if decimals == 0:
                    row_data[column_name] = str(int(round(value)))
                else:
                    row_data[column_name] = f"{value:.{decimals}f}"
            elif isinstance(widget, QComboBox):
                row_data[column_name] = widget.currentText()
            elif isinstance(widget, QLineEdit):
                row_data[column_name] = widget.text()
            else:
                item = self.config_table.item(row, column_index)
                row_data[column_name] = item.text() if item else ''

        return row_data

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def on_data_imported(self, data_info: Dict[str, Any]) -> None:
        self.imported_data = data_info or {}
        self.available_links = list(
            self.imported_data.get('available_links', []))

        self.data_start = self._parse_datetime(
            self.imported_data.get('data_start'))
        self.data_end = self._parse_datetime(
            self.imported_data.get('data_end'))
        if self.data_start and not self.data_end:
            self.data_end = self.data_start

        self.status_label.setText(
            f"Data imported from: {self.imported_data.get('data_folder', 'Unknown')}"
        )
        self.status_label.setStyleSheet("QLabel { color: green; }")

        self._set_controls_enabled(True)

        # Rebind existing rows to enforce new widgets/validation
        existing_rows = self.config_table.rowCount()
        for row in range(existing_rows):
            row_values = self._get_row_data(row)
            self._populate_row(row, row_values)

        if self.config_table.rowCount() == 0:
            self.add_row()

        self.effective_csos.clear()
        self._refresh_effective_table()

    def add_row(self) -> None:
        if not self.config_table.isEnabled():
            QMessageBox.warning(self, "Data Required",
                                "Please import data before adding rows.")
            return

        if not self.available_links:
            QMessageBox.warning(
                self,
                "No Links Available",
                "Imported data does not contain any links to configure.",
            )
            return

        new_row = self.config_table.rowCount()
        self.config_table.insertRow(new_row)

        row_defaults: Dict[str, Any] = {column: self.DEFAULTS.get(
            column, '') for column in self.COLUMNS}
        self._populate_row(new_row, row_defaults)

        self.status_label.setText(f"Added row {new_row + 1}")

    def duplicate_selected_row(self) -> None:
        if not self.config_table.isEnabled():
            return

        selection = self.config_table.selectionModel()
        if not selection or not selection.selectedRows():
            QMessageBox.information(
                self, "No Selection", "Please select a row to duplicate.")
            return

        source_row = selection.selectedRows()[0].row()
        row_data = self._get_row_data(source_row)

        new_row = self.config_table.rowCount()
        self.config_table.insertRow(new_row)
        self._populate_row(new_row, row_data)

        try:
            suffix_col = self.COLUMNS.index('Run Suffix')
            widget = self.config_table.cellWidget(new_row, suffix_col)
            if isinstance(widget, QSpinBox):
                widget.setValue(widget.value() + 1)
        except (ValueError, TypeError):
            pass

        self.status_label.setText(
            f"Duplicated row {source_row + 1} to row {new_row + 1}"
        )

    def delete_selected_rows(self) -> None:
        if not self.config_table.isEnabled():
            return

        selection = self.config_table.selectionModel()
        rows = selection.selectedRows() if selection else []
        if not rows:
            QMessageBox.information(
                self, "No Selection", "Please select row(s) to delete.")
            return

        row_indices = sorted((index.row() for index in rows), reverse=True)
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete {len(row_indices)} row(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            for row in row_indices:
                self.config_table.removeRow(row)
            self.status_label.setText(f"Deleted {len(row_indices)} row(s)")

    def show_context_menu(self, position) -> None:
        menu = QMenu(self)

        add_action = QAction("Add Row", self)
        add_action.triggered.connect(self.add_row)
        menu.addAction(add_action)

        duplicate_action = QAction("Duplicate Row", self)
        duplicate_action.triggered.connect(self.duplicate_selected_row)
        menu.addAction(duplicate_action)

        delete_action = QAction("Delete Row", self)
        delete_action.triggered.connect(self.delete_selected_rows)
        menu.addAction(delete_action)

        menu.exec(self.config_table.viewport().mapToGlobal(position))

    def import_from_csv(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Configuration CSV",
            "",
            "CSV Files (*.csv);;All Files (*.*)",
        )

        if not file_path:
            return

        try:
            import pandas as pd  # Lazy import to keep startup fast

            dataframe = pd.read_csv(file_path)
            self.config_table.setRowCount(0)

            for _, row in dataframe.iterrows():
                new_row = self.config_table.rowCount()
                self.config_table.insertRow(new_row)
                row_dict = {
                    column: row.get(column, self.DEFAULTS.get(column, ''))
                    for column in self.COLUMNS
                }
                self._populate_row(new_row, row_dict)

            self.status_label.setText(
                f"Imported {len(dataframe)} row(s) from CSV")
            self.status_label.setStyleSheet("QLabel { color: green; }")

        except Exception as exc:
            QMessageBox.critical(self, "Import Error",
                                 f"Failed to import CSV:\n{exc}")

    def export_to_csv(self) -> None:
        if self.config_table.rowCount() == 0:
            QMessageBox.information(
                self, "No Data", "No configuration data to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Configuration CSV",
            "",
            "CSV Files (*.csv);;All Files (*.*)",
        )

        if not file_path:
            return

        try:
            import pandas as pd

            data = [self._get_row_data(row) for row in range(
                self.config_table.rowCount())]
            pd.DataFrame(data).to_csv(file_path, index=False)

            self.status_label.setText(f"Exported to: {file_path}")
            self.status_label.setStyleSheet("QLabel { color: green; }")

        except Exception as exc:
            QMessageBox.critical(self, "Export Error",
                                 f"Failed to export CSV:\n{exc}")

    def validate_configuration(self) -> None:
        if self.config_table.rowCount() == 0:
            QMessageBox.warning(
                self, "No Data", "No configuration rows to validate.")
            return

        errors: List[str] = []
        for row in range(self.config_table.rowCount()):
            errors.extend(
                f"Row {row + 1}: {message}" for message in self.validate_row(row))

        if errors:
            details = "\n".join(errors[:10])
            if len(errors) > 10:
                details += f"\n\n... and {len(errors) - 10} more"
            QMessageBox.warning(self, "Validation Errors",
                                f"Configuration has errors:\n\n{details}")
            self.config_validated.emit(False)
            return

        QMessageBox.information(
            self,
            "Validation Success",
            f"All {self.config_table.rowCount()} row(s) validated successfully!",
        )
        self.status_label.setText("✓ Configuration validated")
        self.status_label.setStyleSheet(
            "QLabel { color: green; font-weight: bold; }")
        self.config_validated.emit(True)

    def validate_row(self, row: int) -> List[str]:
        issues: List[str] = []

        name_widget = self.config_table.cellWidget(row, 0)
        if isinstance(name_widget, QComboBox):
            cso_name = name_widget.currentText().strip()
        else:
            name_item = self.config_table.item(row, 0)
            cso_name = name_item.text().strip() if name_item else ''
        if not cso_name:
            issues.append("CSO Name is required")
        elif self.available_links and cso_name not in self.available_links:
            issues.append("CSO Name must exist in imported data")

        continuation_widget = self.config_table.cellWidget(row, 1)
        if isinstance(continuation_widget, QComboBox):
            continuation_value = continuation_widget.currentText().strip()
        else:
            cont_item = self.config_table.item(row, 1)
            continuation_value = cont_item.text().strip() if cont_item else ''
        if not continuation_value:
            issues.append("Continuation Link is required")
        elif self.available_links and continuation_value not in self.available_links:
            issues.append("Continuation Link must exist in imported data")

        for column_index, column_name in enumerate(self.COLUMNS):
            if column_name not in self.NUMERIC_COLUMN_CONFIG:
                continue

            widget = self.config_table.cellWidget(row, column_index)
            if isinstance(widget, QDoubleSpinBox):
                if widget.value() < widget.minimum():
                    issues.append(
                        f"{column_name} must be >= {widget.minimum()}")

        for column_name in {'Bathing Season Start (dd/mm)', 'Bathing Season End (dd/mm)'}:
            column_index = self.COLUMNS.index(column_name)
            widget = self.config_table.cellWidget(row, column_index)
            if isinstance(widget, QLineEdit) and not widget.hasAcceptableInput():
                issues.append(f"{column_name} must be in dd/mm format")

        if self.data_start and self.data_end:
            for column_name in self.DATE_COLUMNS:
                column_index = self.COLUMNS.index(column_name)
                widget = self.config_table.cellWidget(row, column_index)
                if isinstance(widget, QDateTimeEdit):
                    dt_value = widget.dateTime().toPyDateTime()
                    if dt_value < self.data_start or dt_value > self.data_end:
                        issues.append(
                            f"{column_name} must fall within the imported data range"
                        )

        return issues

    def get_configuration_data(self) -> List[Dict[str, str]]:
        return [self._get_row_data(row) for row in range(self.config_table.rowCount())]

    def get_effective_csos(self) -> List[EffectiveCSODefinition]:
        return list(self.effective_csos)

    def get_state(self) -> Dict[str, Any]:
        return {
            'configuration_data': self.get_configuration_data(),
            'imported_data': self.imported_data,
            'effective_csos': [asdict(cso) for cso in self.effective_csos],
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        self.imported_data = state.get('imported_data', {})
        self.available_links = list(
            self.imported_data.get('available_links', []))
        self.data_start = self._parse_datetime(
            self.imported_data.get('data_start'))
        self.data_end = self._parse_datetime(
            self.imported_data.get('data_end'))

        self.config_table.setRowCount(0)
        for row_data in state.get('configuration_data', []):
            new_row = self.config_table.rowCount()
            self.config_table.insertRow(new_row)
            self._populate_row(new_row, row_data)

        self.effective_csos = [
            EffectiveCSODefinition(**definition)
            for definition in state.get('effective_csos', [])
        ]
        self._refresh_effective_table()

        has_imported_data = bool(self.imported_data)
        self._set_controls_enabled(has_imported_data)
        if not has_imported_data:
            self.status_label.setText(
                "Configuration loaded (data import required)")
            self.status_label.setStyleSheet("QLabel { color: orange; }")

    def reset(self) -> None:
        self.config_table.setRowCount(0)
        self.imported_data = {}
        self.available_links = []
        self.data_start = None
        self.data_end = None
        self.effective_csos = []
        self._refresh_effective_table()
        self.status_label.setText("No configuration loaded")
        self.status_label.setStyleSheet(
            "QLabel { color: gray; font-style: italic; }")
        self._set_controls_enabled(False)
