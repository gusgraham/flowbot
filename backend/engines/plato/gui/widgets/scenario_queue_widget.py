"""
Scenario Queue Widget - Allows user to select which scenarios to run/re-run.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from pathlib import Path
from typing import Optional
import json


class ScenarioQueueWidget(QWidget):
    """Widget for selecting scenarios to analyze with status indicators."""

    # Signal emitted when selection changes
    # (selected_count, analyzed_count, new_count)
    selection_changed = pyqtSignal(int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scenarios = []
        self.output_directory = None
        self.init_ui()

    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Table for scenario list
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            '', 'Scenario Name', 'Mode', 'Asset/CSO', 'Status', 'Last Run'
        ])

        # Configure table
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        # Column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed)  # Checkbox
        self.table.setColumnWidth(0, 40)
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)  # Scenario name
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents)  # Mode
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents)  # Asset
        header.setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents)  # Last run

        layout.addWidget(self.table)

        # Control buttons
        button_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(self.select_all_btn)

        self.clear_all_btn = QPushButton("Clear All")
        self.clear_all_btn.clicked.connect(self.clear_all)
        button_layout.addWidget(self.clear_all_btn)

        self.select_not_run_btn = QPushButton("Select Not Run")
        self.select_not_run_btn.clicked.connect(self.select_not_run)
        button_layout.addWidget(self.select_not_run_btn)

        self.select_modified_btn = QPushButton("Select Modified")
        self.select_modified_btn.clicked.connect(self.select_modified)
        button_layout.addWidget(self.select_modified_btn)

        self.refresh_btn = QPushButton("Refresh Status")
        self.refresh_btn.clicked.connect(self.refresh_status)
        button_layout.addWidget(self.refresh_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel("No scenarios available")
        self.status_label.setStyleSheet(
            "QLabel { color: gray; font-style: italic; }")
        layout.addWidget(self.status_label)

    def set_scenarios(self, scenarios: list, output_directory: Optional[str] = None):
        """
        Update the scenario list.

        Args:
            scenarios: List of AnalysisScenario objects
            output_directory: Path to output directory for status detection
        """
        self.scenarios = scenarios
        self.output_directory = output_directory
        self._populate_table()

    def _populate_table(self):
        """Populate the table with scenarios."""
        self.table.setRowCount(0)

        if not self.scenarios:
            self.status_label.setText("No scenarios available")
            self.selection_changed.emit(0, 0, 0)
            return

        self.table.setRowCount(len(self.scenarios))

        for row, scenario in enumerate(self.scenarios):
            # Checkbox column
            checkbox = QCheckBox()
            checkbox.setChecked(False)  # Default: not selected
            checkbox.stateChanged.connect(self._on_selection_changed)

            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)

            self.table.setCellWidget(row, 0, checkbox_widget)

            # Scenario name
            self.table.setItem(
                row, 1, QTableWidgetItem(scenario.scenario_name))

            # Mode
            if scenario.is_catchment_scenario():
                mode = "Catchment"
            elif scenario.is_wwtw_scenario():
                mode = "WwTW"
            else:
                mode = "CSO"
            self.table.setItem(row, 2, QTableWidgetItem(mode))

            # Asset/CSO name
            if scenario.is_catchment_scenario():
                asset_name = scenario.catchment_name
            elif scenario.is_wwtw_scenario():
                asset_name = scenario.wwtw_name
            else:
                asset_name = scenario.cso_name
            self.table.setItem(row, 3, QTableWidgetItem(asset_name))

            # Status and last run (detect from output directory)
            status, last_run = self._get_scenario_status(scenario)

            status_item = QTableWidgetItem(status)
            if status == "✓ Analyzed":
                status_item.setForeground(QColor(0, 128, 0))  # Green
            elif status == "⚠ Modified":
                status_item.setForeground(QColor(255, 140, 0))  # Orange
            else:  # Not Run
                status_item.setForeground(QColor(128, 128, 128))  # Gray

            self.table.setItem(row, 4, status_item)
            self.table.setItem(row, 5, QTableWidgetItem(last_run))

            # Auto-select not run scenarios
            if status == "○ Not Run":
                checkbox.setChecked(True)

        self._update_status_label()

    def _get_scenario_status(self, scenario) -> tuple[str, str]:
        """
        Get the status of a scenario by checking for output files.

        Returns:
            (status_text, last_run_text)
        """
        if not self.output_directory:
            return ("○ Not Run", "—")

        output_dir = Path(self.output_directory)
        if not output_dir.exists():
            return ("○ Not Run", "—")

        # Check for summary file
        summary_path = output_dir / f"{scenario.scenario_name}_summary.json"
        if not summary_path.exists():
            return ("○ Not Run", "—")

        try:
            # Read summary to get metadata
            with open(summary_path, 'r', encoding='utf-8') as f:
                summary = json.load(f)

            # Check if timeseries exists
            timeseries_path = output_dir / \
                f"{scenario.scenario_name}_timeseries.parquet"
            if not timeseries_path.exists():
                return ("○ Not Run", "—")

            # Get last modified time
            import datetime
            mtime = timeseries_path.stat().st_mtime
            last_run = datetime.datetime.fromtimestamp(
                mtime).strftime("%Y-%m-%d %H:%M")

            # TODO: Detect if scenario has been modified since last run
            # For now, just show as analyzed if files exist
            return ("✓ Analyzed", last_run)

        except Exception:
            return ("○ Not Run", "—")

    def get_selected_scenarios(self) -> list:
        """Get list of scenarios that are checked for analysis."""
        selected = []
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected.append(self.scenarios[row])
        return selected

    def select_all(self):
        """Select all scenarios."""
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(True)

    def clear_all(self):
        """Clear all selections."""
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)

    def select_not_run(self):
        """Select only scenarios that haven't been run."""
        for row in range(self.table.rowCount()):
            status_item = self.table.item(row, 4)
            if status_item and status_item.text() == "○ Not Run":
                checkbox_widget = self.table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(True)
            else:
                checkbox_widget = self.table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(False)

    def select_modified(self):
        """Select only scenarios that have been modified."""
        for row in range(self.table.rowCount()):
            status_item = self.table.item(row, 4)
            if status_item and status_item.text() == "⚠ Modified":
                checkbox_widget = self.table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(True)
            else:
                checkbox_widget = self.table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(False)

    def refresh_status(self):
        """Refresh the status of all scenarios."""
        # Re-populate table to update status
        self._populate_table()

    def mark_scenario_complete(self, scenario_name: str):
        """Mark a scenario as complete after analysis."""
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 1)
            if name_item and name_item.text() == scenario_name:
                status_item = self.table.item(row, 4)
                if status_item:
                    status_item.setText("✓ Analyzed")
                    status_item.setForeground(QColor(0, 128, 0))

                # Update last run time
                import datetime
                last_run = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                last_run_item = self.table.item(row, 5)
                if last_run_item:
                    last_run_item.setText(last_run)

                # Uncheck the scenario
                checkbox_widget = self.table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(False)

                break

        self._update_status_label()

    def _on_selection_changed(self):
        """Handle selection change."""
        self._update_status_label()

    def _update_status_label(self):
        """Update the status label with current counts."""
        total = self.table.rowCount()

        if total == 0:
            self.status_label.setText("No scenarios available")
            self.selection_changed.emit(0, 0, 0)
            return

        selected = 0
        analyzed = 0
        not_run = 0

        for row in range(total):
            # Count selected
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected += 1

            # Count analyzed vs not run
            status_item = self.table.item(row, 4)
            if status_item:
                status = status_item.text()
                if status == "✓ Analyzed":
                    analyzed += 1
                elif status == "○ Not Run":
                    not_run += 1

        self.status_label.setText(
            f"⚙ Selected: {selected} scenarios | "
            f"✓ Analyzed: {analyzed} | "
            f"○ Not Run: {not_run}"
        )

        self.selection_changed.emit(selected, analyzed, not_run)
