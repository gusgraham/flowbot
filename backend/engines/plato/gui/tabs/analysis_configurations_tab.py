"""Analysis Configurations Tab - Define reusable analysis settings."""

from typing import List, Optional, Dict, Any
from datetime import datetime
import calendar

from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
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
    QLineEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QDateTimeEdit,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
)

from plato.refactored.asset_models import (
    AnalysisConfiguration,
    get_available_models_for_mode,
    get_model_name,
    get_model_description,
)
import pandas as pd


class DayMonthPicker(QWidget):
    """Widget for selecting day and month with proper validation."""

    def __init__(self, initial_value: str = "15/05", parent=None):
        super().__init__(parent)
        self.init_ui(initial_value)

    def init_ui(self, initial_value: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Parse initial value
        try:
            day_str, month_str = initial_value.split('/')
            initial_day = int(day_str)
            initial_month = int(month_str)
        except (ValueError, AttributeError):
            initial_day = 15
            initial_month = 5

        # Day dropdown
        self.day_combo = QComboBox()
        self.update_days(initial_month)
        # Try to set initial day
        day_index = initial_day - 1
        if day_index < self.day_combo.count():
            self.day_combo.setCurrentIndex(day_index)

        # Month dropdown
        self.month_combo = QComboBox()
        months = [
            "01 - January", "02 - February", "03 - March", "04 - April",
            "05 - May", "06 - June", "07 - July", "08 - August",
            "09 - September", "10 - October", "11 - November", "12 - December"
        ]
        self.month_combo.addItems(months)
        self.month_combo.setCurrentIndex(initial_month - 1)
        self.month_combo.currentIndexChanged.connect(self.on_month_changed)

        # Add widgets to layout (day / month)
        layout.addWidget(self.day_combo)
        layout.addWidget(QLabel("/"))
        layout.addWidget(self.month_combo)
        layout.addStretch()  # Push widgets to the left

    def on_month_changed(self, index):
        """Update available days when month changes."""
        current_day = self.day_combo.currentIndex() + 1
        month = index + 1
        self.update_days(month)

        # Try to restore same day if valid
        max_days = self.day_combo.count()
        if current_day <= max_days:
            self.day_combo.setCurrentIndex(current_day - 1)
        else:
            # Set to last day of month if previous day was invalid
            self.day_combo.setCurrentIndex(max_days - 1)

    def update_days(self, month: int):
        """Update day dropdown based on selected month."""
        # Get number of days in month (using non-leap year to be safe)
        _, num_days = calendar.monthrange(2023, month)

        self.day_combo.clear()
        for day in range(1, num_days + 1):
            self.day_combo.addItem(f"{day:02d}")

    def get_value(self) -> str:
        """Get the current value in dd/mm format."""
        day = self.day_combo.currentIndex() + 1
        month = self.month_combo.currentIndex() + 1
        return f"{day:02d}/{month:02d}"

    def set_value(self, value: str):
        """Set the value from dd/mm format string."""
        try:
            day_str, month_str = value.split('/')
            day = int(day_str)
            month = int(month_str)

            if 1 <= month <= 12:
                self.month_combo.setCurrentIndex(month - 1)
                self.update_days(month)

                if 1 <= day <= self.day_combo.count():
                    self.day_combo.setCurrentIndex(day - 1)
        except (ValueError, AttributeError):
            pass  # Keep current value if parsing fails


class ConfigurationDialog(QDialog):
    """Dialog for creating/editing an analysis configuration."""

    def __init__(self, parent=None, config: Optional[AnalysisConfiguration] = None,
                 date_range: Optional[tuple] = None):
        super().__init__(parent)
        self.config = config
        self.date_range = date_range  # (min_date, max_date) from data import
        self.setWindowTitle("Analysis Configuration")
        self.setModal(True)
        self.init_ui()
        # Size dialog to content after UI is built
        self.adjustSize()
        self.setMinimumWidth(550)

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Add explanation for required fields
        required_info = QLabel("* indicates required field")
        required_info.setStyleSheet(
            "QLabel { color: #666; font-style: italic; font-size: 9pt; }")
        layout.addWidget(required_info)

        # Form layout
        form = QFormLayout()

        # Configuration Name
        self.name_edit = QLineEdit()
        if self.config:
            self.name_edit.setText(self.config.name)
        else:
            self.name_edit.setPlaceholderText(
                "e.g., CSO 10SPA, Bathing Compliance")
        form.addRow("Configuration Name*:", self.name_edit)

        # Mode
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(
            ["Default Mode", "Catchment Based Mode", "WWTW Mode"])
        if self.config:
            self.mode_combo.setCurrentText(self.config.mode)
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        form.addRow("Analysis Mode*:", self.mode_combo)

        # Model (dynamically updates based on mode)
        self.model_combo = QComboBox()
        if self.config:
            self.model_combo.setCurrentText(
                f"{self.config.model} - {get_model_name(self.config.model)}")
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        form.addRow("Model*:", self.model_combo)

        # Model description
        self.model_desc_label = QLabel()
        self.model_desc_label.setWordWrap(True)
        self.model_desc_label.setStyleSheet(
            "QLabel { color: #666; font-size: 10pt; margin-left: 10px; }")
        form.addRow("", self.model_desc_label)

        # Date range
        self.start_date_edit = QDateTimeEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        self.start_date_edit.setWrapping(False)  # Prevent wrapping past bounds

        # Set date constraints if available
        if self.date_range:
            self.start_date_edit.setMinimumDateTime(
                QDateTime(self.date_range[0]))
            self.start_date_edit.setMaximumDateTime(
                QDateTime(self.date_range[1]))

        # Set initial value
        if self.config:
            self.start_date_edit.setDateTime(QDateTime(self.config.start_date))
        elif self.date_range:
            self.start_date_edit.setDateTime(QDateTime(self.date_range[0]))

        self.start_date_edit.dateTimeChanged.connect(self.update_spa_label)
        form.addRow("Start Date*:", self.start_date_edit)

        self.end_date_edit = QDateTimeEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        self.end_date_edit.setWrapping(False)  # Prevent wrapping past bounds

        # Set date constraints if available
        if self.date_range:
            self.end_date_edit.setMinimumDateTime(
                QDateTime(self.date_range[0]))
            self.end_date_edit.setMaximumDateTime(
                QDateTime(self.date_range[1]))

        # Set initial value
        if self.config:
            self.end_date_edit.setDateTime(QDateTime(self.config.end_date))
        elif self.date_range:
            self.end_date_edit.setDateTime(QDateTime(self.date_range[1]))

        self.end_date_edit.dateTimeChanged.connect(self.update_spa_label)
        form.addRow("End Date*:", self.end_date_edit)

        # Spill targets
        self.spill_target_spin = QSpinBox()
        self.spill_target_spin.setRange(1, 9999)
        self.spill_target_spin.setValue(
            self.config.spill_target if self.config else 10)
        self.spill_target_spin.valueChanged.connect(self.update_spa_label)
        form.addRow("Spill Target (Entire Period)*:", self.spill_target_spin)

        # Spills Per Annum label (calculated)
        self.spa_label = QLabel()
        self.spa_label.setStyleSheet(
            "QLabel { color: #0066cc; font-weight: bold; font-size: 10pt; }")
        form.addRow("→ Spills Per Annum:", self.spa_label)

        # Bathing season group (only for Model 4)
        self.bathing_group = QGroupBox(
            "Bathing Season Parameters (Model 4 only)")
        bathing_layout = QFormLayout()

        self.bathing_target_spin = QSpinBox()
        self.bathing_target_spin.setRange(0, 9999)
        self.bathing_target_spin.setSpecialValueText("(not set)")
        if self.config and self.config.spill_target_bathing is not None:
            self.bathing_target_spin.setValue(self.config.spill_target_bathing)
        bathing_layout.addRow("Bathing Season Target:",
                              self.bathing_target_spin)

        # Bathing season start date picker
        start_value = "15/05"
        if self.config and self.config.bathing_season_start:
            start_value = self.config.bathing_season_start
        self.bathing_start_picker = DayMonthPicker(start_value)
        bathing_layout.addRow("Bathing Season Start:",
                              self.bathing_start_picker)

        # Bathing season end date picker
        end_value = "30/09"
        if self.config and self.config.bathing_season_end:
            end_value = self.config.bathing_season_end
        self.bathing_end_picker = DayMonthPicker(end_value)
        bathing_layout.addRow("Bathing Season End:", self.bathing_end_picker)

        self.bathing_group.setLayout(bathing_layout)
        form.addRow(self.bathing_group)

        # Spill definition thresholds
        threshold_group = QGroupBox("Spill Definition Thresholds")
        threshold_layout = QFormLayout()

        self.flow_threshold_spin = QDoubleSpinBox()
        self.flow_threshold_spin.setRange(0.0, 1.0)
        self.flow_threshold_spin.setDecimals(4)
        self.flow_threshold_spin.setSingleStep(0.0001)
        self.flow_threshold_spin.setValue(
            self.config.spill_flow_threshold if self.config else 0.001)
        threshold_layout.addRow("Flow Threshold (m³/s):",
                                self.flow_threshold_spin)

        self.volume_threshold_spin = QDoubleSpinBox()
        self.volume_threshold_spin.setRange(0.0, 1000.0)
        self.volume_threshold_spin.setDecimals(2)
        self.volume_threshold_spin.setValue(
            self.config.spill_volume_threshold if self.config else 0.0)
        threshold_layout.addRow("Volume Threshold (m³):",
                                self.volume_threshold_spin)

        threshold_group.setLayout(threshold_layout)
        form.addRow(threshold_group)

        layout.addLayout(form)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Store reference to OK button for validation
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)

        # Connect validation signals
        self.name_edit.textChanged.connect(self.validate_form)
        self.spill_target_spin.valueChanged.connect(self.validate_form)
        self.model_combo.currentTextChanged.connect(self.validate_form)
        self.bathing_target_spin.valueChanged.connect(self.validate_form)

        # Initialize UI state
        self.on_mode_changed(self.mode_combo.currentText())
        self.update_spa_label()
        self.validate_form()  # Initial validation

    def update_spa_label(self) -> None:
        """Update Spills Per Annum label based on current target and date range."""
        start_date = self.start_date_edit.dateTime().toPyDateTime()
        end_date = self.end_date_edit.dateTime().toPyDateTime()
        spill_target = self.spill_target_spin.value()

        # Calculate years (use 365.25 to account for leap years)
        days = (end_date - start_date).days
        if days <= 0:
            self.spa_label.setText("N/A")
            return

        years = days / 365.25
        spa = spill_target / years

        # Display as integer
        self.spa_label.setText(f"{int(round(spa))} SPA")

    def validate_form(self) -> None:
        """Validate form and enable/disable OK button."""
        is_valid = True

        # Check configuration name
        if not self.name_edit.text().strip():
            is_valid = False

        # Check spill target
        if self.spill_target_spin.value() <= 0:
            is_valid = False

        # Check Model 4 (Bathing Season) requirements
        if self.model_combo.currentData() == 4:
            if self.bathing_target_spin.value() <= 0:
                is_valid = False
            # Bathing dates are always set (have defaults), so no need to check

        # Enable/disable OK button
        self.ok_button.setEnabled(is_valid)

    def on_mode_changed(self, mode: str):
        """Update available models when mode changes."""
        self.model_combo.clear()
        available_models = get_available_models_for_mode(mode)
        for model_num in available_models:
            model_name = get_model_name(model_num, mode)
            self.model_combo.addItem(f"{model_num} - {model_name}", model_num)

        # Update model description
        if self.model_combo.count() > 0:
            self.on_model_changed(self.model_combo.currentText())

    def on_model_changed(self, model_text: str):
        """Update description and bathing season visibility when model changes."""
        if not model_text:
            return

        # Extract model number
        model_num = int(model_text.split(" - ")[0])

        # Get current mode
        mode = self.mode_combo.currentText()

        # Update description
        desc = get_model_description(model_num, mode)
        self.model_desc_label.setText(desc)

        # Enable/disable bathing season fields based on model
        is_model_4 = (model_num == 4)
        self.bathing_group.setEnabled(is_model_4)

    def get_configuration(self) -> Optional[AnalysisConfiguration]:
        """Get the configuration from dialog inputs."""
        try:
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Invalid Input",
                                    "Configuration name is required.")
                return None

            mode = self.mode_combo.currentText()
            model = int(self.model_combo.currentData())

            start_date = self.start_date_edit.dateTime().toPyDateTime()
            end_date = self.end_date_edit.dateTime().toPyDateTime()

            if start_date >= end_date:
                QMessageBox.warning(self, "Invalid Input",
                                    "Start date must be before end date.")
                return None

            spill_target = self.spill_target_spin.value()

            # Bathing season parameters
            spill_target_bathing = None
            bathing_start = None
            bathing_end = None

            if model == 4:
                if self.bathing_target_spin.value() > 0:
                    spill_target_bathing = self.bathing_target_spin.value()

                # Get values from the DayMonthPicker widgets
                bathing_start = self.bathing_start_picker.get_value()
                bathing_end = self.bathing_end_picker.get_value()

                if not spill_target_bathing or not bathing_start or not bathing_end:
                    QMessageBox.warning(
                        self, "Invalid Input",
                        "Model 4 requires bathing season target and dates."
                    )
                    return None

            flow_threshold = self.flow_threshold_spin.value()
            volume_threshold = self.volume_threshold_spin.value()

            return AnalysisConfiguration(
                name=name,
                mode=mode,
                model=model,
                start_date=start_date,
                end_date=end_date,
                spill_target=spill_target,
                spill_target_bathing=spill_target_bathing,
                bathing_season_start=bathing_start,
                bathing_season_end=bathing_end,
                spill_flow_threshold=flow_threshold,
                spill_volume_threshold=volume_threshold,
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to create configuration: {str(e)}")
            return None


class AnalysisConfigurationsTab(QWidget):
    """Tab for defining reusable analysis configurations."""

    # Emitted when configurations are added/removed/modified
    configs_changed = pyqtSignal(list)  # List[AnalysisConfiguration]

    COLUMNS = [
        'Configuration Name',
        'Mode',
        'Model',
        'Start Date',
        'End Date',
        'Spill Target',
        'Bathing Target',
        'Bathing Start',
        'Bathing End',
        'Flow Threshold',
        'Volume Threshold',
    ]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.configurations: List[AnalysisConfiguration] = []
        self.date_range: Optional[tuple] = None  # From data import
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Info label
        info_label = QLabel(
            "📋 Define reusable analysis configurations that can be applied to multiple CSOs.\n"
            "For example: 'CSO 10SPA' (10 spills per annum), 'Bathing Compliance', etc."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "QLabel { background-color: #e3f2fd; color: #0d47a1; padding: 10px; "
            "border-radius: 5px; font-weight: bold; }"
        )
        layout.addWidget(info_label)

        # Button toolbar
        button_layout = QHBoxLayout()

        self.add_config_btn = QPushButton("➕ Add Configuration")
        self.add_config_btn.clicked.connect(self.add_configuration)
        self.add_config_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        button_layout.addWidget(self.add_config_btn)

        self.edit_btn = QPushButton("✏️ Edit Selected")
        self.edit_btn.clicked.connect(self.edit_selected)
        self.edit_btn.setEnabled(False)
        button_layout.addWidget(self.edit_btn)

        self.duplicate_btn = QPushButton("📋 Duplicate Selected")
        self.duplicate_btn.clicked.connect(self.duplicate_selected)
        self.duplicate_btn.setEnabled(False)
        button_layout.addWidget(self.duplicate_btn)

        self.delete_btn = QPushButton("🗑️ Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)

        button_layout.addStretch()

        # self.import_csv_btn = QPushButton("Import from CSV...")
        # self.import_csv_btn.clicked.connect(self.import_from_csv)
        # button_layout.addWidget(self.import_csv_btn)

        # self.export_csv_btn = QPushButton("Export to CSV...")
        # self.export_csv_btn.clicked.connect(self.export_to_csv)
        # self.export_csv_btn.setEnabled(False)
        # button_layout.addWidget(self.export_csv_btn)

        layout.addLayout(button_layout)

        # Configurations table
        table_group = QGroupBox("Analysis Configurations")
        table_layout = QVBoxLayout()

        self.configs_table = QTableWidget()
        self.configs_table.setColumnCount(len(self.COLUMNS))
        self.configs_table.setHorizontalHeaderLabels(self.COLUMNS)
        self.configs_table.setAlternatingRowColors(True)
        self.configs_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.configs_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.configs_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.configs_table.itemSelectionChanged.connect(
            self.on_selection_changed)
        self.configs_table.doubleClicked.connect(self.edit_selected)

        # Set column widths
        header = self.configs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name
        for i in range(1, len(self.COLUMNS)):
            header.setSectionResizeMode(
                i, QHeaderView.ResizeMode.ResizeToContents)

        table_layout.addWidget(self.configs_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # Status label
        self.status_label = QLabel(
            "No configurations defined. Add your first configuration to get started.")
        self.status_label.setStyleSheet(
            "QLabel { color: #666; font-style: italic; }")
        layout.addWidget(self.status_label)

    def set_date_range(self, min_date: datetime, max_date: datetime):
        """Set available date range from data import."""
        self.date_range = (min_date, max_date)
        self.status_label.setText(
            f"Date range from data: {min_date.strftime('%d/%m/%Y %H:%M')} to "
            f"{max_date.strftime('%d/%m/%Y %H:%M')}"
        )

    def add_configuration(self):
        """Show dialog to add a new configuration."""
        dialog = ConfigurationDialog(self, date_range=self.date_range)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_configuration()
            if config:
                # Check for duplicate names
                if any(c.name == config.name for c in self.configurations):
                    QMessageBox.warning(
                        self, "Duplicate Name",
                        f"A configuration named '{config.name}' already exists."
                    )
                    return

                self.configurations.append(config)
                self.refresh_table()
                self.configs_changed.emit(self.configurations)

    def edit_selected(self):
        """Edit the selected configuration."""
        selected_rows = self.configs_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        config = self.configurations[row]

        dialog = ConfigurationDialog(
            self, config=config, date_range=self.date_range)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_config = dialog.get_configuration()
            if new_config:
                # Check for duplicate names (excluding current)
                if any(c.name == new_config.name for i, c in enumerate(self.configurations) if i != row):
                    QMessageBox.warning(
                        self, "Duplicate Name",
                        f"A configuration named '{new_config.name}' already exists."
                    )
                    return

                self.configurations[row] = new_config
                self.refresh_table()
                self.configs_changed.emit(self.configurations)

    def duplicate_selected(self):
        """Duplicate the selected configuration."""
        selected_rows = self.configs_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        config = self.configurations[row]

        # Create a copy with modified name
        base_name = config.name
        copy_num = 1
        new_name = f"{base_name} (Copy)"
        while any(c.name == new_name for c in self.configurations):
            copy_num += 1
            new_name = f"{base_name} (Copy {copy_num})"

        new_config = AnalysisConfiguration(
            name=new_name,
            mode=config.mode,
            model=config.model,
            start_date=config.start_date,
            end_date=config.end_date,
            spill_target=config.spill_target,
            spill_target_bathing=config.spill_target_bathing,
            bathing_season_start=config.bathing_season_start,
            bathing_season_end=config.bathing_season_end,
            spill_flow_threshold=config.spill_flow_threshold,
            spill_volume_threshold=config.spill_volume_threshold
        )

        self.configurations.append(new_config)
        self.refresh_table()
        self.configs_changed.emit(self.configurations)

    def delete_selected(self):
        """Delete the selected configuration."""
        selected_rows = self.configs_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        config = self.configurations[row]

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete configuration '{config.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            del self.configurations[row]
            self.refresh_table()
            self.configs_changed.emit(self.configurations)

    def on_selection_changed(self):
        """Enable/disable buttons based on selection."""
        has_selection = len(
            self.configs_table.selectionModel().selectedRows()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.duplicate_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def refresh_table(self):
        """Refresh the configurations table."""
        self.configs_table.setRowCount(0)

        for config in self.configurations:
            row = self.configs_table.rowCount()
            self.configs_table.insertRow(row)

            self.configs_table.setItem(row, 0, QTableWidgetItem(config.name))
            self.configs_table.setItem(row, 1, QTableWidgetItem(config.mode))
            self.configs_table.setItem(row, 2, QTableWidgetItem(
                f"{config.model} - {get_model_name(config.model)}"))
            self.configs_table.setItem(row, 3, QTableWidgetItem(
                config.start_date.strftime('%d/%m/%Y %H:%M')))
            self.configs_table.setItem(row, 4, QTableWidgetItem(
                config.end_date.strftime('%d/%m/%Y %H:%M')))
            self.configs_table.setItem(
                row, 5, QTableWidgetItem(str(config.spill_target)))
            self.configs_table.setItem(
                row, 6,
                QTableWidgetItem(str(config.spill_target_bathing)
                                 if config.spill_target_bathing else '')
            )
            self.configs_table.setItem(row, 7, QTableWidgetItem(
                config.bathing_season_start or ''))
            self.configs_table.setItem(
                row, 8, QTableWidgetItem(config.bathing_season_end or ''))
            self.configs_table.setItem(row, 9, QTableWidgetItem(
                str(config.spill_flow_threshold)))
            self.configs_table.setItem(row, 10, QTableWidgetItem(
                str(config.spill_volume_threshold)))

        # Update button states
        has_configs = len(self.configurations) > 0
        # self.export_csv_btn.setEnabled(has_configs)

        # Update status
        if has_configs:
            self.status_label.setText(
                f"{len(self.configurations)} configuration(s) defined")
        else:
            self.status_label.setText(
                "No configurations defined. Add your first configuration to get started.")

    def get_configurations(self) -> List[AnalysisConfiguration]:
        """Get all configurations."""
        return self.configurations.copy()

    def get_configuration_names(self) -> List[str]:
        """Get list of configuration names for dropdown population."""
        return [c.name for c in self.configurations]

    def import_from_csv(self):
        """Import configurations from CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Configurations", "", "CSV Files (*.csv)"
        )
        if not file_path:
            return

        try:
            df = pd.read_csv(file_path)
            imported_configs = []

            for _, row in df.iterrows():
                config = AnalysisConfiguration.from_dict(row.to_dict())
                imported_configs.append(config)

            # Ask about duplicate names
            existing_names = {c.name for c in self.configurations}
            duplicate_names = [
                c.name for c in imported_configs if c.name in existing_names]

            if duplicate_names:
                reply = QMessageBox.question(
                    self, "Duplicate Names Found",
                    f"The following configurations already exist:\n{', '.join(duplicate_names)}\n\n"
                    "Overwrite existing configurations?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    # Remove existing configs with same names
                    self.configurations = [
                        c for c in self.configurations if c.name not in duplicate_names]

            self.configurations.extend(imported_configs)
            self.refresh_table()
            self.configs_changed.emit(self.configurations)

            QMessageBox.information(
                self, "Import Successful",
                f"Imported {len(imported_configs)} configuration(s) from {file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Import Failed",
                f"Failed to import configurations:\n{str(e)}"
            )

    def export_to_csv(self):
        """Export configurations to CSV file."""
        if not self.configurations:
            QMessageBox.warning(
                self, "No Data", "No configurations to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Configurations", "analysis_configurations.csv", "CSV Files (*.csv)"
        )
        if not file_path:
            return

        try:
            data = [c.to_dict() for c in self.configurations]
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)

            QMessageBox.information(
                self, "Export Successful",
                f"Exported {len(self.configurations)} configuration(s) to {file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Export Failed",
                f"Failed to export configurations:\n{str(e)}"
            )

    def validate_configs(self, min_date: datetime, max_date: datetime) -> None:
        """Validate existing configurations against new date range and mark invalid ones."""
        for row, config in enumerate(self.configurations):
            is_valid = True

            # Check if config dates are within new data range
            if config.start_date < min_date or config.end_date > max_date:
                is_valid = False

            # Mark row as invalid if dates are outside range
            name_item = self.configs_table.item(row, 0)
            if name_item:
                if not is_valid:
                    name_item.setBackground(Qt.GlobalColor.red)
                    name_item.setToolTip(
                        f"⚠️ Warning: Configuration dates ({config.start_date.strftime('%d/%m/%Y')} to "
                        f"{config.end_date.strftime('%d/%m/%Y')}) are outside imported data range "
                        f"({min_date.strftime('%d/%m/%Y')} to {max_date.strftime('%d/%m/%Y')})")
                else:
                    name_item.setBackground(Qt.GlobalColor.white)
                    name_item.setToolTip("")

    def is_config_valid(self, config: AnalysisConfiguration) -> bool:
        """Check if a configuration's dates are within the current data range."""
        if not self.date_range:
            return False

        min_date, max_date = self.date_range

        # Check if config dates are within data range
        if config.start_date < min_date or config.end_date > max_date:
            return False

        return True

    def get_state(self) -> dict:
        """Get current state for saving to project file."""
        return {
            'configurations': [config.to_dict() for config in self.configurations],
            'date_range': {
                'min_date': self.date_range[0].isoformat() if self.date_range else None,
                'max_date': self.date_range[1].isoformat() if self.date_range else None,
            } if self.date_range else None,
        }

    def load_state(self, state: dict) -> None:
        """Load state from project file."""
        # Restore date range
        if state.get('date_range'):
            date_range_data = state['date_range']
            if date_range_data['min_date'] and date_range_data['max_date']:
                min_date = datetime.fromisoformat(date_range_data['min_date'])
                max_date = datetime.fromisoformat(date_range_data['max_date'])
                self.set_date_range(min_date, max_date)

        # Restore configurations
        if 'configurations' in state:
            self.configurations.clear()
            for config_data in state['configurations']:
                try:
                    config = AnalysisConfiguration.from_dict(config_data)
                    self.configurations.append(config)
                except Exception as e:
                    print(f"Error loading configuration: {e}")
                    continue

        self.refresh_table()
        self.configs_changed.emit(self.configurations)
