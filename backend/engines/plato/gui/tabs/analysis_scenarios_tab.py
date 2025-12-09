"""Analysis Scenarios Tab - Define what-if analysis configurations."""

import os
import glob
import traceback
from typing import List, Optional
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
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
    QSpinBox,
    QDoubleSpinBox,
    QTabWidget,
)

from plato.refactored import (
    CSOAsset,
    WWTWAsset,
    AnalysisScenario,
)
from plato.gui.widgets.flow_return_analyzer_dialog import FlowReturnAnalyzerDialog
import pandas as pd


class AnalysisScenariosTab(QWidget):
    """Tab for defining analysis scenarios on CSO assets."""

    # Emitted when scenarios are added/removed/modified
    scenarios_changed = pyqtSignal()

    # Column definitions for each table type
    CSO_COLUMNS = [
        'Scenario\nName',
        'Asset',
        'Configuration',
        'PFF Increase\n(m3/s)',
        'Pumping\nMode',
        'Pump Rate\n(m3/s)',
        'Time Delay\n(h)',
        'Flow Return\nThreshold\n(m3/s)',
        'Depth Return\nThreshold\n(m)',
        'Tank Volume\n(m³)',
    ]

    CATCHMENT_COLUMNS = [
        '▶',  # Expand/collapse button column
        'Scenario\nName',
        'Catchment / CSO',
        'Configuration',
        'PFF Increase\n(m3/s)',
        'Pumping\nMode',
        'Pump Rate\n(m3/s)',
        'Time Delay\n(h)',
        'Flow Return\nThreshold\n(m3/s)',
        'Depth Return\nThreshold\n(m)',
        'Tank Volume\n(m³)',
    ]

    WWTW_COLUMNS = [
        'Scenario\nName',
        'Asset',
        'Configuration',
        'Tank\nVolume\n(m3)',
        'FFT\nAugmentation\n(m3/s)',
        'WwTW Pump\nRate\n(m3/s)',
        'WwTW Pump\nOn Threshold\n(m3/s)',
        'WwTW Pump\nOff Threshold\n(m3/s)',
        'WwTW Time\nDelay\n(h)',
    ]

    # Legacy COLUMNS for backward compatibility
    COLUMNS = [
        'Asset',
        'Configuration',
        'Scenario\nName',
        # CSO/Catchment intervention columns
        'PFF Increase\n(m3/s)',
        'Pumping\nMode',
        'Pump Rate\n(m3/s)',
        'Time Delay\n(h)',
        'Flow Return\nThreshold\n(m3/s)',
        'Depth Return\nThreshold\n(m)',
        'Tank Volume\n(m³)',
        # WwTW intervention columns
        'FFT\nAugmentation\n(m3/s)',
        'WwTW Pump\nRate\n(m3/s)',
        'WwTW Pump\nOn Threshold\n(m3/s)',
        'WwTW Pump\nOff Threshold\n(m3/s)',
        'WwTW Time\nDelay\n(h)',
        # 'Tools',  # Temporarily removed - will re-add after WwTW mode implementation
    ]

    # Column indices for enabling/disabling based on scenario type
    CSO_COLUMN_INDICES = [3, 4, 5, 6, 7, 8, 9]  # PFF through Tank Volume
    # FFT Augmentation through WwTW Time Delay
    WWTW_COLUMN_INDICES = [10, 11, 12, 13, 14]

    DEFAULTS = {
        'Scenario Name': 'Base',
        # CSO defaults
        'PFF Increase (m3/s)': 0.0,
        'Pumping Mode': 'Fixed',
        'Pump Rate (m3/s)': 0.0,
        'Time Delay (h)': 0,
        'Flow Return Threshold (m3/s)': 0.0,
        'Depth Return Threshold (m)': 10.0,
        'Tank Volume (m3)': 0.0,
        # WwTW defaults
        'FFT Augmentation (m3/s)': 0.0,
        'WwTW Pump Rate (m3/s)': 0.0,
        'WwTW Pump On Threshold (m3/s)': 0.0,
        'WwTW Pump Off Threshold (m3/s)': 0.0,
        'WwTW Time Delay (h)': 0,
    }

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.available_csos: List[str] = []
        self.cso_assets: List[CSOAsset] = []
        self.available_wwtws: List[str] = []
        self.wwtw_assets: List[WWTWAsset] = []
        self.available_catchments: List[str] = []
        self.catchments: List = []
        self.available_configs: List[str] = []
        self.configurations: List = []

        # Three separate tables for different scenario modes
        self.cso_scenario_table: Optional[QTableWidget] = None
        self.catchment_scenario_table: Optional[QTableWidget] = None
        self.wwtw_scenario_table: Optional[QTableWidget] = None
        self.tab_widget: Optional[QTabWidget] = None

        # Row metadata tracking for hierarchical catchment scenarios
        # Structure: {row_num: {'type': 'parent'|'child', 'parent_row': int|None,
        #                       'cso_name': str|None, 'expanded': bool}}
        self.catchment_row_metadata: dict = {}

        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Info label
        info_label = QLabel(
            "Define analysis scenarios by combining assets with analysis configurations. "
            "Use tabs to organize CSO, Catchment, and WwTW scenarios separately."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "QLabel { color: #666; font-style: italic; margin: 5px; }")
        layout.addWidget(info_label)

        # Button toolbar
        button_layout = QHBoxLayout()

        self.add_scenario_btn = QPushButton("Add Scenario")
        self.add_scenario_btn.clicked.connect(self.add_scenario)
        button_layout.addWidget(self.add_scenario_btn)

        self.duplicate_btn = QPushButton("Duplicate Selected")
        self.duplicate_btn.clicked.connect(self.duplicate_selected)
        button_layout.addWidget(self.duplicate_btn)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected)
        button_layout.addWidget(self.delete_btn)

        button_layout.addStretch()

        self.analyze_selected_btn = QPushButton("Analyze Selected CSO")
        self.analyze_selected_btn.clicked.connect(
            self._analyze_selected_scenario)
        self.analyze_selected_btn.setToolTip(
            "Analyze the flow return characteristics of selected scenarios")
        button_layout.addWidget(self.analyze_selected_btn)

        # self.import_csv_btn = QPushButton("Import from CSV...")
        # self.import_csv_btn.clicked.connect(self.import_from_csv)
        # button_layout.addWidget(self.import_csv_btn)

        # self.import_legacy_btn = QPushButton("Import from Legacy CSV...")
        # self.import_legacy_btn.clicked.connect(self.import_from_legacy_csv)
        # self.import_legacy_btn.setToolTip(
        #     "Import legacy CSO Configuration format - creates proxy configurations and scenarios")
        # button_layout.addWidget(self.import_legacy_btn)

        # self.export_csv_btn = QPushButton("Export to CSV...")
        # self.export_csv_btn.clicked.connect(self.export_to_csv)
        # button_layout.addWidget(self.export_csv_btn)

        # self.export_legacy_btn = QPushButton("Export to Legacy CSV...")
        # self.export_legacy_btn.clicked.connect(self.export_to_legacy_csv)
        # self.export_legacy_btn.setToolTip(
        #     "Export scenarios in legacy CSO Configuration format for testing in the old tool")
        # button_layout.addWidget(self.export_legacy_btn)

        # self.validate_btn = QPushButton("Validate Scenarios")
        # self.validate_btn.clicked.connect(self.validate_scenarios)
        # self.validate_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        # button_layout.addWidget(self.validate_btn)

        layout.addLayout(button_layout)

        # Tabbed interface for different scenario types
        self.tab_widget = QTabWidget()

        # CSO Tab
        self.cso_scenario_table = self._create_cso_scenario_table()
        self.tab_widget.addTab(self.cso_scenario_table, "🏭 CSO Scenarios")

        # Catchment Tab
        self.catchment_scenario_table = self._create_catchment_scenario_table()
        self.tab_widget.addTab(
            self.catchment_scenario_table, "🌊 Catchment Scenarios")

        # WwTW Tab
        self.wwtw_scenario_table = self._create_wwtw_scenario_table()
        self.tab_widget.addTab(self.wwtw_scenario_table, "🏗️ WwTW Scenarios")

        layout.addWidget(self.tab_widget)

        # Status label
        self.status_label = QLabel(
            "No scenarios defined. Please define assets and configurations first.")
        self.status_label.setStyleSheet(
            "QLabel { color: gray; font-style: italic; }")
        layout.addWidget(self.status_label)

    @staticmethod
    def _sanitize_scenario_name(name: str) -> str:
        """
        Sanitize scenario name to ensure it's safe for file system operations.
        Removes or replaces characters that could cause issues with file paths.

        Invalid characters: / \\ : * ? " < > |
        """
        import re
        # Replace invalid filename characters with underscore
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, '_', name)

        # Remove leading/trailing dots and spaces (Windows restriction)
        sanitized = sanitized.strip('. ')

        # If empty after sanitization, use default
        if not sanitized:
            sanitized = "Unnamed"

        return sanitized

    @staticmethod
    def _validate_scenario_name(name: str) -> tuple[bool, str]:
        """
        Validate scenario name for file system safety.
        Returns (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Scenario name cannot be empty"

        # Check for invalid filename characters
        invalid_chars = r'[<>:"/\\|?*]'
        import re
        if re.search(invalid_chars, name):
            invalid_found = re.findall(invalid_chars, name)
            return False, f"Scenario name contains invalid characters: {', '.join(set(invalid_found))}\n\nThese characters cannot be used in filenames: / \\ : * ? \" < > |"

        # Check for leading/trailing dots or spaces (Windows issue)
        if name != name.strip('. '):
            return False, "Scenario name cannot start or end with dots or spaces"

        # Check for reserved Windows filenames
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                          'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                          'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        if name.upper() in reserved_names:
            return False, f"'{name}' is a reserved Windows filename and cannot be used"

        return True, ""

    def _create_cso_scenario_table(self) -> QTableWidget:
        """Create table for CSO scenarios."""
        table = QTableWidget()
        table.setColumnCount(len(self.CSO_COLUMNS))
        table.setHorizontalHeaderLabels(self.CSO_COLUMNS)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)

        # Configure header
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setDefaultSectionSize(120)
        header.setMinimumSectionSize(80)
        header.setSectionsMovable(False)

        table.setStyleSheet("""
            QHeaderView::section {
                padding: 8px;
                min-height: 60px;
                max-height: 60px;
                border: 1px solid #d0d0d0;
                background-color: #f0f0f0;
                font-weight: bold;
            }
        """)

        # Connect change signal
        table.itemChanged.connect(self.on_item_changed)

        # Set column widths
        table.setColumnWidth(0, 120)   # Scenario Name
        table.setColumnWidth(1, 150)   # Asset
        table.setColumnWidth(2, 150)   # Configuration
        table.setColumnWidth(3, 130)   # PFF Increase
        table.setColumnWidth(4, 120)   # Pumping Mode
        table.setColumnWidth(5, 120)   # Pump Rate
        table.setColumnWidth(6, 110)   # Time Delay
        table.setColumnWidth(7, 140)   # Flow Return Threshold
        table.setColumnWidth(8, 140)   # Depth Return Threshold
        table.setColumnWidth(9, 120)   # Tank Volume

        return table

    def _create_catchment_scenario_table(self) -> QTableWidget:
        """Create table for catchment scenarios with master-detail structure."""
        table = QTableWidget()
        table.setColumnCount(len(self.CATCHMENT_COLUMNS))
        table.setHorizontalHeaderLabels(self.CATCHMENT_COLUMNS)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)

        # Configure header
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setDefaultSectionSize(120)
        header.setMinimumSectionSize(40)
        header.setSectionsMovable(False)

        table.setStyleSheet("""
            QHeaderView::section {
                padding: 8px;
                min-height: 60px;
                max-height: 60px;
                border: 1px solid #d0d0d0;
                background-color: #f0f0f0;
                font-weight: bold;
            }
        """)

        # Connect change signal
        table.itemChanged.connect(self.on_item_changed)

        # Set column widths - now includes intervention columns
        table.setColumnWidth(0, 50)    # Expand/collapse button
        table.setColumnWidth(1, 120)   # Scenario Name
        table.setColumnWidth(2, 180)   # Catchment / CSO
        table.setColumnWidth(3, 150)   # Configuration
        table.setColumnWidth(4, 130)   # PFF Increase
        table.setColumnWidth(5, 120)   # Pumping Mode
        table.setColumnWidth(6, 120)   # Pump Rate
        table.setColumnWidth(7, 110)   # Time Delay
        table.setColumnWidth(8, 140)   # Flow Return Threshold
        table.setColumnWidth(9, 140)   # Depth Return Threshold
        table.setColumnWidth(10, 120)  # Tank Volume

        return table

    def _create_wwtw_scenario_table(self) -> QTableWidget:
        """Create table for WwTW scenarios."""
        table = QTableWidget()
        table.setColumnCount(len(self.WWTW_COLUMNS))
        table.setHorizontalHeaderLabels(self.WWTW_COLUMNS)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)

        # Configure header
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setDefaultSectionSize(120)
        header.setMinimumSectionSize(80)
        header.setSectionsMovable(False)

        table.setStyleSheet("""
            QHeaderView::section {
                padding: 8px;
                min-height: 60px;
                max-height: 60px;
                border: 1px solid #d0d0d0;
                background-color: #f0f0f0;
                font-weight: bold;
            }
        """)

        # Connect change signal
        table.itemChanged.connect(self.on_item_changed)

        # Set column widths
        table.setColumnWidth(0, 120)   # Scenario Name
        table.setColumnWidth(1, 150)   # Asset
        table.setColumnWidth(2, 150)   # Configuration
        table.setColumnWidth(3, 120)   # Tank Volume
        table.setColumnWidth(4, 140)   # FFT Augmentation
        table.setColumnWidth(5, 140)   # WwTW Pump Rate
        table.setColumnWidth(6, 160)   # WwTW Pump On Threshold
        table.setColumnWidth(7, 160)   # WwTW Pump Off Threshold
        table.setColumnWidth(8, 140)   # WwTW Time Delay

        return table

    def _get_current_table(self) -> QTableWidget:
        """Get the currently active table based on selected tab."""
        if not self.tab_widget:
            # Fallback during initialization
            return self.cso_scenario_table if self.cso_scenario_table else QTableWidget()

        current_widget = self.tab_widget.currentWidget()
        if current_widget == self.cso_scenario_table:
            return self.cso_scenario_table
        elif current_widget == self.catchment_scenario_table:
            return self.catchment_scenario_table
        elif current_widget == self.wwtw_scenario_table:
            return self.wwtw_scenario_table
        else:
            return self.cso_scenario_table  # Default fallback

    def _get_current_mode(self) -> str:
        """Get the current scenario mode based on active tab."""
        if not self.tab_widget:
            return 'CSO'

        current_widget = self.tab_widget.currentWidget()
        if current_widget == self.cso_scenario_table:
            return 'CSO'
        elif current_widget == self.catchment_scenario_table:
            return 'Catchment'
        elif current_widget == self.wwtw_scenario_table:
            return 'WwTW'
        else:
            return 'CSO'  # Default fallback

    # Temporary backward compatibility property
    @property
    def scenarios_table(self) -> QTableWidget:
        """Backward compatibility: returns current active table."""
        return self._get_current_table()

    def set_available_csos(self, cso_names: List[str], cso_assets: List[CSOAsset]) -> None:
        """Update available CSO list from assets tab."""
        self.available_csos = cso_names
        self.cso_assets = cso_assets

        # Update add button state (enable if we have assets AND configs)
        has_assets = len(cso_names) > 0 or len(self.available_wwtws) > 0
        has_configs = len(self.available_configs) > 0
        self.add_scenario_btn.setEnabled(has_assets and has_configs)

        self.update_status()

    def set_available_wwtws(self, wwtw_names: List[str], wwtw_assets: List[WWTWAsset]) -> None:
        """Update available WwTW list from WwTW assets tab."""
        self.available_wwtws = wwtw_names
        self.wwtw_assets = wwtw_assets

        # Update add button state (enable if we have assets AND configs)
        has_assets = len(self.available_csos) > 0 or len(wwtw_names) > 0
        has_configs = len(self.available_configs) > 0
        self.add_scenario_btn.setEnabled(has_assets and has_configs)

        self.update_status()

    def set_available_configurations(self, config_names: List[str], configs: List) -> None:
        """Update available analysis configurations from configurations tab."""
        self.available_configs = config_names
        self.configurations = configs

        # Update existing config dropdowns in all rows
        self._refresh_config_dropdowns()

        # Update add button state (enable if we have assets AND configs)
        has_assets = len(self.available_csos) > 0 or len(
            self.available_wwtws) > 0
        has_configs = len(config_names) > 0
        self.add_scenario_btn.setEnabled(has_assets and has_configs)

        self.update_status()

    def set_available_catchments(self, catchment_names: List[str], catchments: List) -> None:
        """Update available catchments from catchments tab."""
        self.available_catchments = catchment_names
        self.catchments = catchments

        # Note: With split-table architecture, each table has its own asset type
        # No need to refresh dropdowns dynamically based on configuration mode

        self.update_status()

    # ===== Row Metadata Helpers for Hierarchical Catchment Scenarios =====

    def _is_parent_row(self, row: int) -> bool:
        """Check if a row is a parent (catchment scenario) row."""
        return row in self.catchment_row_metadata and self.catchment_row_metadata[row].get('type') == 'parent'

    def _is_child_row(self, row: int) -> bool:
        """Check if a row is a child (per-CSO intervention) row."""
        return row in self.catchment_row_metadata and self.catchment_row_metadata[row].get('type') == 'child'

    def _get_parent_row(self, child_row: int) -> Optional[int]:
        """Get the parent row number for a child row."""
        if self._is_child_row(child_row):
            return self.catchment_row_metadata[child_row].get('parent_row')
        return None

    def _get_child_rows(self, parent_row: int) -> List[int]:
        """Get all child row numbers for a parent row."""
        if not self._is_parent_row(parent_row):
            return []
        return [row for row in self.catchment_row_metadata
                if self.catchment_row_metadata[row].get('parent_row') == parent_row]

    def _is_expanded(self, parent_row: int) -> bool:
        """Check if a parent row is expanded (children visible)."""
        if self._is_parent_row(parent_row):
            return self.catchment_row_metadata[parent_row].get('expanded', True)
        return False

    def _set_row_metadata(self, row: int, row_type: str, parent_row: Optional[int] = None,
                          cso_name: Optional[str] = None, expanded: bool = True) -> None:
        """Set metadata for a row."""
        self.catchment_row_metadata[row] = {
            'type': row_type,  # 'parent' or 'child'
            'parent_row': parent_row,
            'cso_name': cso_name,
            'expanded': expanded
        }

    def _clear_row_metadata(self, row: int) -> None:
        """Clear metadata for a row."""
        if row in self.catchment_row_metadata:
            del self.catchment_row_metadata[row]

    def _update_row_indices_after_deletion(self, deleted_row: int) -> None:
        """Update all row metadata indices after a row deletion."""
        # Create new metadata dict with updated indices
        new_metadata = {}
        for row, data in self.catchment_row_metadata.items():
            if row < deleted_row:
                # Rows before deletion stay the same
                new_metadata[row] = data.copy()
            elif row > deleted_row:
                # Rows after deletion shift down by 1
                new_data = data.copy()
                # Update parent_row reference if needed
                if new_data.get('parent_row') is not None:
                    if new_data['parent_row'] == deleted_row:
                        # Parent was deleted, mark orphan
                        new_data['parent_row'] = None
                    elif new_data['parent_row'] > deleted_row:
                        # Parent row shifts down
                        new_data['parent_row'] -= 1
                new_metadata[row - 1] = new_data
        self.catchment_row_metadata = new_metadata

    def _update_row_indices_after_insertion(self, inserted_row: int, num_rows: int = 1) -> None:
        """Update all row metadata indices after row insertion(s)."""
        # Create new metadata dict with updated indices
        new_metadata = {}
        for row, data in self.catchment_row_metadata.items():
            if row < inserted_row:
                # Rows before insertion stay the same
                new_metadata[row] = data.copy()
            else:
                # Rows at or after insertion shift down
                new_data = data.copy()
                # Update parent_row reference if needed
                if new_data.get('parent_row') is not None and new_data['parent_row'] >= inserted_row:
                    new_data['parent_row'] += num_rows
                new_metadata[row + num_rows] = new_data
        self.catchment_row_metadata = new_metadata

    # ===== End Row Metadata Helpers =====

    def _create_expand_collapse_button(self, parent_row: int) -> QPushButton:
        """Create an expand/collapse button for a parent row."""
        button = QPushButton("▼")  # Down arrow when expanded
        button.setMaximumWidth(30)
        button.setToolTip("Click to collapse/expand child rows")
        button.clicked.connect(
            lambda: self._toggle_expand_collapse(parent_row))
        return button

    def _toggle_expand_collapse(self, parent_row: int) -> None:
        """Toggle visibility of child rows for a parent."""
        if not self._is_parent_row(parent_row):
            return

        # Toggle expanded state
        is_expanded = self._is_expanded(parent_row)
        self.catchment_row_metadata[parent_row]['expanded'] = not is_expanded

        # Update button text
        button_widget = self.catchment_scenario_table.cellWidget(parent_row, 0)
        if button_widget and isinstance(button_widget, QPushButton):
            button_widget.setText("▶" if is_expanded else "▼")

        # Show/hide child rows
        child_rows = self._get_child_rows(parent_row)
        for child_row in child_rows:
            self.catchment_scenario_table.setRowHidden(child_row, is_expanded)

    def _create_child_rows_for_catchment(self, parent_row: int, catchment_name: str) -> None:
        """Create child rows for each CSO in a catchment."""
        # Find the catchment
        catchment = next(
            (c for c in self.catchments if c.name == catchment_name), None)
        if not catchment:
            return

        # Get CSO names using the method
        cso_names = catchment.get_cso_names()
        if not cso_names:
            return

        # Block signals during bulk insertion
        self.catchment_scenario_table.blockSignals(True)

        # Insert child rows after parent
        insert_position = parent_row + 1
        num_csos = len(cso_names)

        # Update metadata indices BEFORE inserting (shifts rows after parent)
        self._update_row_indices_after_insertion(insert_position, num_csos)

        for i, cso_name in enumerate(cso_names):
            child_row = insert_position + i
            self.catchment_scenario_table.insertRow(child_row)

            # Set row metadata
            self._set_row_metadata(
                child_row, 'child', parent_row=parent_row, cso_name=cso_name)

            # Add child-specific widgets (per-CSO intervention parameters)
            self._populate_child_row(child_row, cso_name)

        self.catchment_scenario_table.blockSignals(False)

    def _populate_child_row(self, row: int, cso_name: str) -> None:
        """Populate a child row with CSO-specific intervention widgets."""
        # Column 0: Empty (expand button is parent-only)
        empty_item = QTableWidgetItem("")
        empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        empty_item.setBackground(QColor("#f0f0f0"))
        self.catchment_scenario_table.setItem(row, 0, empty_item)

        # Column 1: Empty (scenario name is at parent level) - make non-editable
        scenario_item = QTableWidgetItem("")
        scenario_item.setFlags(scenario_item.flags() & ~
                               Qt.ItemFlag.ItemIsEditable)
        scenario_item.setBackground(QColor("#f0f0f0"))
        self.catchment_scenario_table.setItem(row, 1, scenario_item)

        # Column 2: Indented CSO name label
        cso_label = QLabel(f"    └─ {cso_name}")
        cso_label.setStyleSheet("QLabel { color: #666; padding-left: 20px; }")
        self.catchment_scenario_table.setCellWidget(row, 2, cso_label)

        # Column 3: Empty (config is at parent level) - make non-editable
        config_item = QTableWidgetItem("")
        config_item.setFlags(config_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        config_item.setBackground(QColor("#f0f0f0"))
        self.catchment_scenario_table.setItem(row, 3, config_item)

        # Columns 4-10: Intervention parameters (same as parent but per-CSO)
        # Column 4: PFF Increase
        pff_spin = QDoubleSpinBox()
        pff_spin.setRange(0.0, 100.0)
        pff_spin.setDecimals(5)
        pff_spin.setSingleStep(0.001)
        pff_spin.setValue(self.DEFAULTS['PFF Increase (m3/s)'])
        pff_spin.setSuffix(" m³/s")
        pff_spin.valueChanged.connect(lambda: self.scenarios_changed.emit())
        self.catchment_scenario_table.setCellWidget(row, 4, pff_spin)

        # Column 5: Pumping Mode
        pump_mode_combo = QComboBox()
        pump_mode_combo.addItems(['Fixed', 'Variable'])
        pump_mode_combo.setCurrentText(self.DEFAULTS['Pumping Mode'])
        pump_mode_combo.currentTextChanged.connect(
            lambda: self.scenarios_changed.emit())
        self.catchment_scenario_table.setCellWidget(row, 5, pump_mode_combo)

        # Column 6: Pump Rate
        pump_rate_spin = QDoubleSpinBox()
        pump_rate_spin.setRange(0.0, 10.0)
        pump_rate_spin.setDecimals(5)
        pump_rate_spin.setSingleStep(0.001)
        pump_rate_spin.setValue(self.DEFAULTS['Pump Rate (m3/s)'])
        pump_rate_spin.setSuffix(" m³/s")
        pump_rate_spin.valueChanged.connect(
            lambda: self.scenarios_changed.emit())
        self.catchment_scenario_table.setCellWidget(row, 6, pump_rate_spin)

        # Column 7: Time Delay
        time_delay_spin = QSpinBox()
        time_delay_spin.setRange(0, 168)
        time_delay_spin.setValue(self.DEFAULTS['Time Delay (h)'])
        time_delay_spin.setSuffix(" h")
        time_delay_spin.valueChanged.connect(
            lambda: self.scenarios_changed.emit())
        self.catchment_scenario_table.setCellWidget(row, 7, time_delay_spin)

        # Column 8: Flow Return Threshold
        flow_threshold_spin = QDoubleSpinBox()
        flow_threshold_spin.setRange(0.0, 10.0)
        flow_threshold_spin.setDecimals(5)
        flow_threshold_spin.setSingleStep(0.001)
        flow_threshold_spin.setValue(
            self.DEFAULTS['Flow Return Threshold (m3/s)'])
        flow_threshold_spin.setSuffix(" m³/s")
        flow_threshold_spin.valueChanged.connect(
            lambda: self.scenarios_changed.emit())
        self.catchment_scenario_table.setCellWidget(
            row, 8, flow_threshold_spin)

        # Column 9: Depth Return Threshold
        depth_threshold_spin = QDoubleSpinBox()
        depth_threshold_spin.setRange(0.0, 10.0)
        depth_threshold_spin.setDecimals(3)
        depth_threshold_spin.setSingleStep(0.05)
        depth_threshold_spin.setValue(
            self.DEFAULTS['Depth Return Threshold (m)'])
        depth_threshold_spin.setSuffix(" m")
        depth_threshold_spin.valueChanged.connect(
            lambda: self.scenarios_changed.emit())
        self.catchment_scenario_table.setCellWidget(
            row, 9, depth_threshold_spin)

        # Column 10: Tank Volume
        tank_volume_spin = QDoubleSpinBox()
        tank_volume_spin.setRange(0.0, 100000.0)
        tank_volume_spin.setDecimals(1)
        tank_volume_spin.setSingleStep(10.0)
        tank_volume_spin.setValue(
            self.DEFAULTS['Tank Volume (m3)'])
        tank_volume_spin.setSuffix(" m³")
        tank_volume_spin.valueChanged.connect(
            lambda: self.scenarios_changed.emit())
        self.catchment_scenario_table.setCellWidget(row, 10, tank_volume_spin)

    # ===== End Hierarchical Row Methods =====

    def _on_catchment_selected(self, parent_row: int, catchment_name: str) -> None:
        """Handle catchment selection - create parent/child row structure."""
        if not catchment_name or catchment_name == "(No catchments defined)":
            return

        # Remove any existing child rows for this parent
        existing_children = self._get_child_rows(parent_row)
        if existing_children:
            # Delete children in reverse order to maintain indices
            for child_row in reversed(existing_children):
                self.catchment_scenario_table.removeRow(child_row)
                self._clear_row_metadata(child_row)

        # Mark this as a parent row
        self._set_row_metadata(parent_row, 'parent', expanded=True)

        # Replace the asset combo with a layout containing expand button + combo
        asset_combo = self.catchment_scenario_table.cellWidget(parent_row, 2)
        if not asset_combo:
            return

        # Create container widget with horizontal layout
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(2)

        # Add expand/collapse button
        expand_btn = self._create_expand_collapse_button(parent_row)
        layout.addWidget(expand_btn)

        # Create new combo with current selection
        new_combo = QComboBox()
        new_combo.addItems(self.available_catchments)
        new_combo.setCurrentText(catchment_name)
        new_combo.currentTextChanged.connect(
            lambda text, r=parent_row: self._on_catchment_selected(r, text))
        layout.addWidget(new_combo, 1)  # Stretch factor 1

        # Replace the widget
        self.catchment_scenario_table.setCellWidget(parent_row, 0, container)

        # Clear intervention parameter widgets from parent row (columns 3-9)
        # These are now per-CSO in child rows
        for col in range(3, 10):
            self.catchment_scenario_table.removeCellWidget(parent_row, col)
            # Add empty label to show this is a parent row
            empty_label = QLabel("")
            empty_label.setStyleSheet("QLabel { background-color: #f0f0f0; }")
            self.catchment_scenario_table.setCellWidget(
                parent_row, col, empty_label)

        # Create child rows for each CSO in the catchment
        self._create_child_rows_for_catchment(parent_row, catchment_name)

        # Emit changed signal
        self.scenarios_changed.emit()

    # ===== End Catchment Selection Handler =====

    def _refresh_config_dropdowns(self) -> None:
        """Refresh all configuration dropdowns with updated config list."""
        # Update all three tables
        for table in [self.cso_scenario_table, self.catchment_scenario_table, self.wwtw_scenario_table]:
            if not table:
                continue

            # Determine config column index and filter configs based on table type
            if table == self.cso_scenario_table:
                config_col = 2
                # CSO table: only "Default Mode" configs
                filtered_configs = [
                    c.name for c in self.configurations if c.mode == "Default Mode"]
            elif table == self.catchment_scenario_table:
                config_col = 3  # Catchment has expand button in column 0, name in column 1
                # Catchment table: only "Catchment Based Mode" configs
                filtered_configs = [
                    c.name for c in self.configurations if c.mode == "Catchment Based Mode"]
            elif table == self.wwtw_scenario_table:
                config_col = 2
                # WwTW table: only "WWTW Mode" configs
                filtered_configs = [
                    c.name for c in self.configurations if c.mode == "WWTW Mode"]
            else:
                continue

            for row in range(table.rowCount()):
                config_combo = table.cellWidget(row, config_col)
                if config_combo and isinstance(config_combo, QComboBox):
                    # Save current selection
                    current_config = config_combo.currentText()

                    # Block signals to avoid triggering updates during refresh
                    config_combo.blockSignals(True)
                    config_combo.clear()
                    config_combo.addItems(filtered_configs)

                    # Restore selection if it still exists
                    if current_config in filtered_configs:
                        config_combo.setCurrentText(current_config)

                    config_combo.blockSignals(False)

    def on_item_changed(self, item: QTableWidgetItem) -> None:
        """Handle item changes, particularly for scenario name validation."""
        if not item:
            return

        table = item.tableWidget()
        if not table:
            return

        # Determine which table this item belongs to and check if it's the scenario name column
        is_scenario_name_column = False

        if table == self.cso_scenario_table and item.column() == 0:
            # CSO: Scenario Name is column 0
            is_scenario_name_column = True
        elif table == self.catchment_scenario_table and item.column() == 1:
            # Catchment: Scenario Name is column 1 (after expand button)
            # Validate if it's NOT a child row (parent rows and new rows without metadata)
            row_meta = self.catchment_row_metadata.get(item.row(), {})
            if row_meta.get('type') != 'child':
                is_scenario_name_column = True
        elif table == self.wwtw_scenario_table and item.column() == 0:
            # WwTW: Scenario Name is column 0
            is_scenario_name_column = True

        if is_scenario_name_column:
            self._validate_and_sanitize_scenario_name_realtime(item)

        # Emit the changed signal
        self.scenarios_changed.emit()

    def _validate_and_sanitize_scenario_name_realtime(self, item: QTableWidgetItem) -> None:
        """
        Validate scenario name in real-time as user types.
        Checks for invalid characters and duplicates.
        """
        current_row = item.row()
        current_table = item.tableWidget()
        new_name = item.text()

        if not new_name.strip():
            # Don't validate empty names while user is typing
            return

        # Block signals to prevent recursive calls
        current_table.blockSignals(True)

        try:
            # Check for invalid filename characters
            import re
            invalid_chars = r'[<>:"/\\|?*]'
            if re.search(invalid_chars, new_name):
                # Found invalid characters - sanitize immediately
                sanitized = self._sanitize_scenario_name(new_name)
                item.setText(sanitized)

                # Show tooltip-style warning (non-blocking)
                invalid_found = re.findall(invalid_chars, new_name)
                QMessageBox.warning(
                    self,
                    "Invalid Characters Removed",
                    f"Scenario names cannot contain: {', '.join(set(invalid_found))}\n\n"
                    f"Invalid characters have been replaced with underscores.\n\n"
                    f"Characters not allowed: / \\ : * ? \" < > |"
                )
                new_name = sanitized

            # Check for duplicates across all three tables
            duplicate_found = False
            duplicate_location = ""

            # Check CSO table
            if self.cso_scenario_table:
                for row in range(self.cso_scenario_table.rowCount()):
                    if self.cso_scenario_table == current_table and row == current_row:
                        continue
                    scenario_item = self.cso_scenario_table.item(row, 0)
                    if scenario_item and scenario_item.text().strip() == new_name.strip():
                        duplicate_found = True
                        duplicate_location = "CSO Scenarios"
                        break

            # Check Catchment table (only parent rows)
            if not duplicate_found and self.catchment_scenario_table:
                for row in range(self.catchment_scenario_table.rowCount()):
                    if self.catchment_scenario_table == current_table and row == current_row:
                        continue
                    row_meta = self.catchment_row_metadata.get(row, {})
                    if row_meta.get('type') == 'parent':
                        scenario_item = self.catchment_scenario_table.item(
                            row, 1)
                        if scenario_item and scenario_item.text().strip() == new_name.strip():
                            duplicate_found = True
                            duplicate_location = "Catchment Scenarios"
                            break

            # Check WwTW table
            if not duplicate_found and self.wwtw_scenario_table:
                for row in range(self.wwtw_scenario_table.rowCount()):
                    if self.wwtw_scenario_table == current_table and row == current_row:
                        continue
                    scenario_item = self.wwtw_scenario_table.item(row, 0)
                    if scenario_item and scenario_item.text().strip() == new_name.strip():
                        duplicate_found = True
                        duplicate_location = "WwTW Scenarios"
                        break

            if duplicate_found:
                # Generate unique name
                base_name = new_name.strip()
                counter = 2
                unique_name = f"{base_name}_{counter}"

                # Keep incrementing until we find a unique name
                while self._is_scenario_name_duplicate(unique_name, current_table, current_row):
                    counter += 1
                    unique_name = f"{base_name}_{counter}"

                item.setText(unique_name)

                QMessageBox.warning(
                    self,
                    "Duplicate Scenario Name",
                    f"A scenario named '{base_name}' already exists in {duplicate_location}.\n\n"
                    f"Scenario names must be unique across all tabs.\n\n"
                    f"The name has been changed to '{unique_name}'."
                )

        finally:
            # Re-enable signals
            current_table.blockSignals(False)

    def _is_scenario_name_duplicate(self, name: str, exclude_table: QTableWidget, exclude_row: int) -> bool:
        """Check if a scenario name already exists across all tables."""
        name = name.strip()

        # Check CSO table
        if self.cso_scenario_table:
            for row in range(self.cso_scenario_table.rowCount()):
                if self.cso_scenario_table == exclude_table and row == exclude_row:
                    continue
                scenario_item = self.cso_scenario_table.item(row, 0)
                if scenario_item and scenario_item.text().strip() == name:
                    return True

        # Check Catchment table (only parent rows)
        if self.catchment_scenario_table:
            for row in range(self.catchment_scenario_table.rowCount()):
                if self.catchment_scenario_table == exclude_table and row == exclude_row:
                    continue
                row_meta = self.catchment_row_metadata.get(row, {})
                if row_meta.get('type') == 'parent':
                    scenario_item = self.catchment_scenario_table.item(row, 1)
                    if scenario_item and scenario_item.text().strip() == name:
                        return True

        # Check WwTW table
        if self.wwtw_scenario_table:
            for row in range(self.wwtw_scenario_table.rowCount()):
                if self.wwtw_scenario_table == exclude_table and row == exclude_row:
                    continue
                scenario_item = self.wwtw_scenario_table.item(row, 0)
                if scenario_item and scenario_item.text().strip() == name:
                    return True

        return False

    def add_scenario(self) -> None:
        """Add a new scenario row to the currently active table."""
        # Check if we have configs
        if not self.available_configs:
            QMessageBox.warning(
                self, "No Configurations Available",
                "Please define analysis configurations in the Analysis Configurations tab first."
            )
            return

        # Get current mode and add to appropriate table
        current_mode = self._get_current_mode()

        if current_mode == 'CSO':
            self._add_cso_scenario()
        elif current_mode == 'Catchment':
            self._add_catchment_scenario()
        elif current_mode == 'WwTW':
            self._add_wwtw_scenario()

        self.update_status()
        self.scenarios_changed.emit()

    def _add_cso_scenario(self) -> None:
        """Add a new CSO scenario row."""
        if not self.available_csos:
            QMessageBox.warning(
                self, "No CSO Assets Available",
                "Please define CSO assets first."
            )
            return

        table = self.cso_scenario_table
        row = table.rowCount()
        table.insertRow(row)

        # Scenario Name - NOW FIRST COLUMN (column 0)
        scenario_name_item = QTableWidgetItem(self.DEFAULTS['Scenario Name'])
        table.setItem(row, 0, scenario_name_item)

        # Asset dropdown
        asset_combo = QComboBox()
        asset_combo.addItems(self.available_csos)
        asset_combo.currentTextChanged.connect(
            lambda: self.scenarios_changed.emit())
        table.setCellWidget(row, 1, asset_combo)

        # Configuration dropdown - filter to CSO/Default mode configs only
        config_combo = QComboBox()
        cso_configs = [c.name for c in self.configurations if c.mode in [
            "Default Mode"]]
        if not cso_configs:
            cso_configs = ["(No CSO configs available)"]
        config_combo.addItems(cso_configs)
        config_combo.currentTextChanged.connect(
            lambda: self.scenarios_changed.emit())
        table.setCellWidget(row, 2, config_combo)

        # PFF Increase
        pff_spin = QDoubleSpinBox()
        pff_spin.setRange(0.0, 100.0)
        pff_spin.setDecimals(5)
        pff_spin.setSingleStep(0.001)
        pff_spin.setValue(self.DEFAULTS['PFF Increase (m3/s)'])
        pff_spin.setSuffix(" m³/s")
        pff_spin.valueChanged.connect(lambda: self.scenarios_changed.emit())
        table.setCellWidget(row, 3, pff_spin)

        # Pumping Mode
        pump_mode_combo = QComboBox()
        pump_mode_combo.addItems(['Fixed', 'Variable'])
        pump_mode_combo.setCurrentText(self.DEFAULTS['Pumping Mode'])
        pump_mode_combo.currentTextChanged.connect(
            lambda: self.scenarios_changed.emit())
        table.setCellWidget(row, 4, pump_mode_combo)

        # Pump Rate
        pump_rate_spin = QDoubleSpinBox()
        pump_rate_spin.setRange(0.0, 10.0)
        pump_rate_spin.setDecimals(5)
        pump_rate_spin.setSingleStep(0.001)
        pump_rate_spin.setValue(self.DEFAULTS['Pump Rate (m3/s)'])
        pump_rate_spin.setSuffix(" m³/s")
        pump_rate_spin.valueChanged.connect(
            lambda: self.scenarios_changed.emit())
        table.setCellWidget(row, 5, pump_rate_spin)

        # Time Delay
        time_delay_spin = QSpinBox()
        time_delay_spin.setRange(0, 168)
        time_delay_spin.setValue(self.DEFAULTS['Time Delay (h)'])
        time_delay_spin.setSuffix(" h")
        time_delay_spin.valueChanged.connect(
            lambda: self.scenarios_changed.emit())
        table.setCellWidget(row, 6, time_delay_spin)

        # Flow Return Threshold
        flow_threshold_spin = QDoubleSpinBox()
        flow_threshold_spin.setRange(0.0, 10.0)
        flow_threshold_spin.setDecimals(5)
        flow_threshold_spin.setSingleStep(0.001)
        flow_threshold_spin.setValue(
            self.DEFAULTS['Flow Return Threshold (m3/s)'])
        flow_threshold_spin.setSuffix(" m³/s")
        flow_threshold_spin.valueChanged.connect(
            lambda: self.scenarios_changed.emit())
        table.setCellWidget(row, 7, flow_threshold_spin)

        # Depth Return Threshold
        depth_threshold_spin = QDoubleSpinBox()
        depth_threshold_spin.setRange(0.0, 10.0)
        depth_threshold_spin.setDecimals(3)
        depth_threshold_spin.setSingleStep(0.05)
        depth_threshold_spin.setValue(
            self.DEFAULTS['Depth Return Threshold (m)'])
        depth_threshold_spin.setSuffix(" m")
        depth_threshold_spin.valueChanged.connect(
            lambda: self.scenarios_changed.emit())
        table.setCellWidget(row, 8, depth_threshold_spin)

        # Tank Volume
        tank_volume_spin = QDoubleSpinBox()
        tank_volume_spin.setRange(0.0, 100000.0)
        tank_volume_spin.setDecimals(1)
        tank_volume_spin.setSingleStep(10.0)
        tank_volume_spin.setValue(self.DEFAULTS.get('Tank Volume (m3)', 0.0))
        tank_volume_spin.setSuffix(" m³")
        tank_volume_spin.valueChanged.connect(
            lambda: self.scenarios_changed.emit())
        table.setCellWidget(row, 9, tank_volume_spin)

    def _add_catchment_scenario(self) -> None:
        """Add a new catchment scenario row with master-detail structure."""
        if not self.available_catchments:
            QMessageBox.warning(
                self, "No Catchments Available",
                "Please define catchments first in the Catchments tab."
            )
            return

        table = self.catchment_scenario_table
        row = table.rowCount()
        table.insertRow(row)

        # Expand/collapse button
        expand_btn = self._create_expand_collapse_button(row)
        table.setCellWidget(row, 0, expand_btn)

        # Scenario Name - NOW COLUMN 1 (after expand button)
        scenario_name_item = QTableWidgetItem(self.DEFAULTS['Scenario Name'])
        table.setItem(row, 1, scenario_name_item)

        # Catchment dropdown - connect to trigger child row creation
        catchment_combo = QComboBox()
        catchment_combo.addItems(self.available_catchments)
        catchment_combo.currentTextChanged.connect(
            lambda text, r=row: self._on_catchment_selected_new(r, text))
        table.setCellWidget(row, 2, catchment_combo)

        # Configuration dropdown - filter to Catchment mode configs only
        config_combo = QComboBox()
        catchment_configs = [
            c.name for c in self.configurations if c.mode == "Catchment Based Mode"]
        if not catchment_configs:
            catchment_configs = ["(No Catchment configs available)"]
        config_combo.addItems(catchment_configs)
        config_combo.currentTextChanged.connect(
            lambda: self.scenarios_changed.emit())
        table.setCellWidget(row, 3, config_combo)

        # Parent row gets empty cells for intervention columns (4-10)
        # Child rows will have the actual intervention widgets
        for col in range(4, 11):
            empty_item = QTableWidgetItem("")
            empty_item.setFlags(empty_item.flags() & ~
                                Qt.ItemFlag.ItemIsEditable)
            empty_item.setBackground(QColor("#f5f5f5"))
            table.setItem(row, col, empty_item)

        # Mark as parent row
        self._set_row_metadata(row, 'parent', expanded=True)

        # Trigger child row creation for the first catchment if auto-selected
        if self.available_catchments:
            first_catchment = catchment_combo.currentText()
            if first_catchment:
                self._on_catchment_selected_new(row, first_catchment)

    def _on_catchment_selected_new(self, parent_row: int, catchment_name: str) -> None:
        """Handle catchment selection in catchment scenario table - create child rows."""
        if not catchment_name or catchment_name == "(No catchments defined)":
            return

        table = self.catchment_scenario_table

        # Remove any existing child rows for this parent
        existing_children = self._get_child_rows(parent_row)
        if existing_children:
            # Delete children in reverse order to maintain indices
            for child_row in reversed(existing_children):
                table.removeRow(child_row)
                self._clear_row_metadata(child_row)

        # Mark this as a parent row
        self._set_row_metadata(parent_row, 'parent', expanded=True)

        # Find the catchment
        catchment = next(
            (c for c in self.catchments if c.name == catchment_name), None)
        if not catchment:
            return

        # Get CSO names in the catchment
        cso_names = catchment.get_cso_names()
        if not cso_names:
            return

        # Create child rows
        table.blockSignals(True)

        # Insert child rows after parent
        insert_position = parent_row + 1
        num_csos = len(cso_names)

        # Update metadata indices BEFORE inserting
        self._update_row_indices_after_insertion(insert_position, num_csos)

        for i, cso_name in enumerate(cso_names):
            child_row = insert_position + i
            table.insertRow(child_row)

            # Set row metadata
            self._set_row_metadata(
                child_row, 'child', parent_row=parent_row, cso_name=cso_name)

            # Column 0: Empty (expand button is parent-only)
            empty_item = QTableWidgetItem("")
            empty_item.setFlags(empty_item.flags() & ~
                                Qt.ItemFlag.ItemIsEditable)
            empty_item.setBackground(QColor("#f5f5f5"))
            table.setItem(child_row, 0, empty_item)

            # Column 1: Scenario name (empty - inherited from parent)
            scenario_item = QTableWidgetItem("")
            scenario_item.setFlags(scenario_item.flags() & ~
                                   Qt.ItemFlag.ItemIsEditable)
            scenario_item.setBackground(QColor("#f5f5f5"))
            table.setItem(child_row, 1, scenario_item)

            # Column 2: Indented CSO name
            cso_label = QLabel(f"    └─ {cso_name}")
            cso_label.setStyleSheet(
                "QLabel { color: #666; padding-left: 10px; }")
            table.setCellWidget(child_row, 2, cso_label)

            # Column 3: Config (empty - inherited from parent)
            config_item = QTableWidgetItem("")
            config_item.setFlags(config_item.flags() & ~
                                 Qt.ItemFlag.ItemIsEditable)
            config_item.setBackground(QColor("#f5f5f5"))
            table.setItem(child_row, 3, config_item)

            # Column 4: PFF Increase
            pff_spin = QDoubleSpinBox()
            pff_spin.setRange(0.0, 100.0)
            pff_spin.setDecimals(5)
            pff_spin.setSingleStep(0.001)
            pff_spin.setValue(self.DEFAULTS['PFF Increase (m3/s)'])
            pff_spin.setSuffix(" m³/s")
            pff_spin.valueChanged.connect(
                lambda: self.scenarios_changed.emit())
            table.setCellWidget(child_row, 4, pff_spin)

            # Column 5: Pumping Mode
            pump_mode_combo = QComboBox()
            pump_mode_combo.addItems(['Fixed', 'Variable'])
            pump_mode_combo.setCurrentText(self.DEFAULTS['Pumping Mode'])
            pump_mode_combo.currentTextChanged.connect(
                lambda: self.scenarios_changed.emit())
            table.setCellWidget(child_row, 5, pump_mode_combo)

            # Column 6: Pump Rate
            pump_rate_spin = QDoubleSpinBox()
            pump_rate_spin.setRange(0.0, 10.0)
            pump_rate_spin.setDecimals(5)
            pump_rate_spin.setSingleStep(0.001)
            pump_rate_spin.setValue(self.DEFAULTS['Pump Rate (m3/s)'])
            pump_rate_spin.setSuffix(" m³/s")
            pump_rate_spin.valueChanged.connect(
                lambda: self.scenarios_changed.emit())
            table.setCellWidget(child_row, 6, pump_rate_spin)

            # Column 7: Time Delay
            time_delay_spin = QSpinBox()
            time_delay_spin.setRange(0, 168)
            time_delay_spin.setValue(self.DEFAULTS['Time Delay (h)'])
            time_delay_spin.setSuffix(" h")
            time_delay_spin.valueChanged.connect(
                lambda: self.scenarios_changed.emit())
            table.setCellWidget(child_row, 7, time_delay_spin)

            # Column 8: Flow Return Threshold
            flow_threshold_spin = QDoubleSpinBox()
            flow_threshold_spin.setRange(0.0, 10.0)
            flow_threshold_spin.setDecimals(5)
            flow_threshold_spin.setSingleStep(0.001)
            flow_threshold_spin.setValue(
                self.DEFAULTS['Flow Return Threshold (m3/s)'])
            flow_threshold_spin.setSuffix(" m³/s")
            flow_threshold_spin.valueChanged.connect(
                lambda: self.scenarios_changed.emit())
            table.setCellWidget(child_row, 8, flow_threshold_spin)

            # Column 9: Depth Return Threshold
            depth_threshold_spin = QDoubleSpinBox()
            depth_threshold_spin.setRange(0.0, 10.0)
            depth_threshold_spin.setDecimals(3)
            depth_threshold_spin.setSingleStep(0.05)
            depth_threshold_spin.setValue(
                self.DEFAULTS['Depth Return Threshold (m)'])
            depth_threshold_spin.setSuffix(" m")
            depth_threshold_spin.valueChanged.connect(
                lambda: self.scenarios_changed.emit())
            table.setCellWidget(child_row, 9, depth_threshold_spin)

            # Column 10: Tank Volume
            tank_volume_spin = QDoubleSpinBox()
            tank_volume_spin.setRange(0.0, 100000.0)
            tank_volume_spin.setDecimals(1)
            tank_volume_spin.setSingleStep(10.0)
            tank_volume_spin.setValue(self.DEFAULTS['Tank Volume (m3)'])
            tank_volume_spin.setSuffix(" m³")
            tank_volume_spin.valueChanged.connect(
                lambda: self.scenarios_changed.emit())
            table.setCellWidget(child_row, 10, tank_volume_spin)

        table.blockSignals(False)
        self.scenarios_changed.emit()

    def _add_wwtw_scenario(self) -> None:
        """Add a new WwTW scenario row."""
        if not self.available_wwtws:
            QMessageBox.warning(
                self, "No WwTW Assets Available",
                "Please define WwTW assets first."
            )
            return

        table = self.wwtw_scenario_table
        row = table.rowCount()
        table.insertRow(row)

        # Scenario Name - NOW FIRST COLUMN (column 0)
        scenario_name_item = QTableWidgetItem(self.DEFAULTS['Scenario Name'])
        table.setItem(row, 0, scenario_name_item)

        # Asset dropdown
        asset_combo = QComboBox()
        asset_combo.addItems(self.available_wwtws)
        asset_combo.currentTextChanged.connect(
            lambda: self.scenarios_changed.emit())
        table.setCellWidget(row, 1, asset_combo)

        # Configuration dropdown - filter to WWTW mode configs only
        config_combo = QComboBox()
        wwtw_configs = [
            c.name for c in self.configurations if c.mode == "WWTW Mode"]
        if not wwtw_configs:
            wwtw_configs = ["(No WWTW configs available)"]
        config_combo.addItems(wwtw_configs)
        config_combo.currentTextChanged.connect(
            lambda: self.scenarios_changed.emit())
        table.setCellWidget(row, 2, config_combo)

        # Tank Volume
        tank_volume_spin = QDoubleSpinBox()
        tank_volume_spin.setRange(0.0, 1000000.0)  # Up to 1 million m³
        tank_volume_spin.setDecimals(1)
        tank_volume_spin.setSingleStep(100.0)
        tank_volume_spin.setValue(self.DEFAULTS.get('Tank Volume (m3)', 0.0))
        tank_volume_spin.setSuffix(" m³")
        tank_volume_spin.valueChanged.connect(
            lambda: self.scenarios_changed.emit())
        table.setCellWidget(row, 3, tank_volume_spin)

        # FFT Augmentation
        fft_aug_spin = QDoubleSpinBox()
        fft_aug_spin.setRange(0.0, 100.0)
        fft_aug_spin.setDecimals(5)
        fft_aug_spin.setSingleStep(0.001)
        fft_aug_spin.setValue(self.DEFAULTS.get(
            'FFT Augmentation (m3/s)', 0.0))
        fft_aug_spin.setSuffix(" m³/s")
        fft_aug_spin.valueChanged.connect(
            lambda: self.scenarios_changed.emit())
        table.setCellWidget(row, 4, fft_aug_spin)

        # WwTW Pump Rate
        wwtw_pump_rate_spin = QDoubleSpinBox()
        wwtw_pump_rate_spin.setRange(0.0, 10.0)
        wwtw_pump_rate_spin.setDecimals(5)
        wwtw_pump_rate_spin.setSingleStep(0.001)
        wwtw_pump_rate_spin.setValue(
            self.DEFAULTS.get('WwTW Pump Rate (m3/s)', 0.0))
        wwtw_pump_rate_spin.setSuffix(" m³/s")
        wwtw_pump_rate_spin.valueChanged.connect(
            lambda: self.scenarios_changed.emit())
        table.setCellWidget(row, 5, wwtw_pump_rate_spin)

        # WwTW Pump On Threshold
        wwtw_on_spin = QDoubleSpinBox()
        wwtw_on_spin.setRange(0.0, 10.0)
        wwtw_on_spin.setDecimals(5)
        wwtw_on_spin.setSingleStep(0.001)
        wwtw_on_spin.setValue(self.DEFAULTS.get(
            'WwTW Pump On Threshold (m3/s)', 0.0))
        wwtw_on_spin.setSuffix(" m³/s")
        wwtw_on_spin.valueChanged.connect(
            lambda: self.scenarios_changed.emit())
        table.setCellWidget(row, 6, wwtw_on_spin)

        # WwTW Pump Off Threshold
        wwtw_off_spin = QDoubleSpinBox()
        wwtw_off_spin.setRange(0.0, 10.0)
        wwtw_off_spin.setDecimals(5)
        wwtw_off_spin.setSingleStep(0.001)
        wwtw_off_spin.setValue(self.DEFAULTS.get(
            'WwTW Pump Off Threshold (m3/s)', 0.0))
        wwtw_off_spin.setSuffix(" m³/s")
        wwtw_off_spin.valueChanged.connect(
            lambda: self.scenarios_changed.emit())
        table.setCellWidget(row, 7, wwtw_off_spin)

        # WwTW Time Delay
        wwtw_time_delay_spin = QSpinBox()
        wwtw_time_delay_spin.setRange(0, 168)
        wwtw_time_delay_spin.setValue(
            self.DEFAULTS.get('WwTW Time Delay (h)', 0))
        wwtw_time_delay_spin.setSuffix(" h")
        wwtw_time_delay_spin.valueChanged.connect(
            lambda: self.scenarios_changed.emit())
        table.setCellWidget(row, 8, wwtw_time_delay_spin)

    def duplicate_selected(self) -> None:
        """Duplicate selected scenario rows from the currently active table."""
        # Get current table and mode
        current_table = self._get_current_table()
        current_mode = self._get_current_mode()

        selected_rows = set(item.row()
                            for item in current_table.selectedItems())
        if not selected_rows:
            QMessageBox.warning(self, "No Selection",
                                "Please select a scenario to duplicate.")
            return

        # Only catchment mode has parent/child rows
        if current_mode == 'Catchment':
            # Filter out child rows - only allow duplicating parent rows
            rows_to_duplicate = []
            child_rows_selected = []

            for row in sorted(selected_rows):
                if self._is_child_row(row):
                    cso_name = self.catchment_row_metadata[row].get(
                        'cso_name', 'Unknown')
                    child_rows_selected.append(cso_name)
                else:
                    rows_to_duplicate.append(row)

            # Warn if user tried to duplicate child rows
            if child_rows_selected:
                QMessageBox.warning(
                    self, "Cannot Duplicate Child Rows",
                    f"Cannot duplicate individual CSO rows: {', '.join(child_rows_selected[:5])}\n\n"
                    f"Child rows are part of a catchment scenario. "
                    f"To duplicate them, select and duplicate the parent catchment row instead."
                )
                if not rows_to_duplicate:
                    return

            # Duplicate catchment scenarios (parent + children)
            for row in rows_to_duplicate:
                # Extract scenario from this row
                scenario = self._get_catchment_scenario_from_row(row)
                if not scenario:
                    continue

                # Modify scenario name
                scenario.scenario_name = f"{scenario.scenario_name}_copy"

                # Add to table (will create parent + children)
                self._add_catchment_scenario()
                new_row = current_table.rowCount() - len(scenario.cso_interventions or {}) - 1

                # Set values on new parent row
                catchment_combo = current_table.cellWidget(new_row, 1)
                config_combo = current_table.cellWidget(new_row, 2)
                scenario_item = current_table.item(new_row, 3)

                if catchment_combo:
                    catchment_combo.setCurrentText(
                        scenario.catchment_name or "")
                if config_combo:
                    config_combo.setCurrentText(scenario.config_name)
                if scenario_item:
                    scenario_item.setText(scenario.scenario_name)

                # Child rows will be created by _on_catchment_selected_new
                # and populated with intervention values from the scenario

        else:
            # CSO or WwTW modes - simple duplication
            for row in sorted(selected_rows):
                if current_mode == 'CSO':
                    scenario = self._get_cso_scenario_from_row(row)
                    if scenario:
                        scenario.scenario_name = f"{scenario.scenario_name}_copy"
                        self._add_cso_scenario()
                        new_row = current_table.rowCount() - 1
                        self._populate_cso_row(new_row, scenario)

                elif current_mode == 'WwTW':
                    scenario = self._get_wwtw_scenario_from_row(row)
                    if scenario:
                        scenario.scenario_name = f"{scenario.scenario_name}_copy"
                        self._add_wwtw_scenario()
                        new_row = current_table.rowCount() - 1
                        self._populate_wwtw_row(new_row, scenario)

        self.scenarios_changed.emit()

    def _populate_cso_row(self, row: int, scenario: AnalysisScenario) -> None:
        """Populate a CSO table row with scenario values."""
        table = self.cso_scenario_table

        scenario_item = table.item(row, 0)
        asset_combo = table.cellWidget(row, 1)
        config_combo = table.cellWidget(row, 2)

        if asset_combo:
            asset_combo.setCurrentText(scenario.cso_name or "")
        if config_combo:
            config_combo.setCurrentText(scenario.config_name)
        if scenario_item:
            scenario_item.setText(scenario.scenario_name)

        # Set intervention parameters
        widgets = [
            (3, scenario.pff_increase),
            (4, scenario.pumping_mode),
            (5, scenario.pump_rate),
            (6, scenario.time_delay),
            (7, scenario.flow_return_threshold),
            (8, scenario.depth_return_threshold),
            (9, scenario.tank_volume if scenario.tank_volume is not None else 0.0),
        ]

        for col, value in widgets:
            widget = table.cellWidget(row, col)
            if widget:
                if isinstance(widget, QComboBox):
                    widget.setCurrentText(str(value))
                elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    widget.setValue(value)

    def _populate_wwtw_row(self, row: int, scenario: AnalysisScenario) -> None:
        """Populate a WwTW table row with scenario values."""
        table = self.wwtw_scenario_table

        scenario_item = table.item(row, 0)
        asset_combo = table.cellWidget(row, 1)
        config_combo = table.cellWidget(row, 2)

        if asset_combo:
            asset_combo.setCurrentText(scenario.wwtw_name or "")
        if config_combo:
            config_combo.setCurrentText(scenario.config_name)
        if scenario_item:
            scenario_item.setText(scenario.scenario_name)

        # Set WwTW parameters
        widgets = [
            (3, scenario.tank_volume or 0.0),
            (4, scenario.fft_augmentation or 0.0),
            (5, scenario.wwtw_pump_rate or 0.0),
            (6, scenario.wwtw_pump_on_threshold or 0.0),
            (7, scenario.wwtw_pump_off_threshold or 0.0),
            (8, scenario.wwtw_time_delay_hours or 0),
        ]

        for col, value in widgets:
            widget = table.cellWidget(row, col)
            if widget and isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(value)

    def delete_selected(self) -> None:
        """Delete selected scenario rows from the currently active table."""
        # Get current table and mode
        current_table = self._get_current_table()
        current_mode = self._get_current_mode()

        selected_rows = set(item.row()
                            for item in current_table.selectedItems())
        if not selected_rows:
            QMessageBox.warning(self, "No Selection",
                                "Please select scenarios to delete.")
            return

        # Only catchment mode has parent/child rows
        if current_mode == 'Catchment':
            # Filter out child rows - only allow deleting parent rows
            rows_to_delete = set()
            child_rows_selected = []

            for row in selected_rows:
                if self._is_child_row(row):
                    # Get the CSO name for the error message
                    cso_name = self.catchment_row_metadata[row].get(
                        'cso_name', 'Unknown')
                    child_rows_selected.append(cso_name)
                else:
                    rows_to_delete.add(row)
                    # If this is a parent row, add all its children to the delete list
                    if self._is_parent_row(row):
                        child_rows = self._get_child_rows(row)
                        rows_to_delete.update(child_rows)

            # Warn if user tried to delete child rows
            if child_rows_selected:
                QMessageBox.warning(
                    self, "Cannot Delete Child Rows",
                    f"Cannot delete individual CSO rows: {', '.join(child_rows_selected[:5])}\n\n"
                    f"Child rows are part of a catchment scenario. "
                    f"To delete them, select and delete the parent catchment row instead."
                )
                if not rows_to_delete:
                    return

            if not rows_to_delete:
                return

            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Delete {len([r for r in rows_to_delete if not self._is_child_row(r)])} scenario(s) "
                f"(including child rows)?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Delete in reverse order to maintain indices
                for row in sorted(rows_to_delete, reverse=True):
                    current_table.removeRow(row)
                    self._clear_row_metadata(row)

                # After all deletions, rebuild metadata indices
                self._rebuild_row_metadata_indices()
        else:
            # CSO or WwTW modes - simple deletion (no parent/child)
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Delete {len(selected_rows)} scenario(s)?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Delete in reverse order to maintain indices
                for row in sorted(selected_rows, reverse=True):
                    current_table.removeRow(row)

        self.update_status()
        self.scenarios_changed.emit()

    def _rebuild_row_metadata_indices(self) -> None:
        """Rebuild row metadata after bulk deletions by shifting all indices."""
        # Get current table row count (use catchment table)
        current_rows = set(range(self.catchment_scenario_table.rowCount()))

        # Remove metadata for rows that no longer exist
        # Create a new dict from existing items that are still valid
        valid_metadata = {
            row: data for row, data in list(self.catchment_row_metadata.items())
            if row in current_rows
        }
        self.catchment_row_metadata = valid_metadata

    def get_scenarios(self) -> List[AnalysisScenario]:
        """Get all scenarios from all three tables."""
        scenarios = []

        # Collect CSO scenarios
        for row in range(self.cso_scenario_table.rowCount()):
            try:
                scenario = self._get_cso_scenario_from_row(row)
                if scenario:
                    scenarios.append(scenario)
            except Exception as e:
                continue  # Skip invalid rows

        # Collect Catchment scenarios
        for row in range(self.catchment_scenario_table.rowCount()):
            # Skip child rows - they're included in their parent scenario
            if self._is_child_row(row):
                continue

            try:
                scenario = self._get_catchment_scenario_from_row(row)
                if scenario:
                    scenarios.append(scenario)
            except Exception as e:
                continue  # Skip invalid rows

        # Collect WwTW scenarios
        for row in range(self.wwtw_scenario_table.rowCount()):
            try:
                scenario = self._get_wwtw_scenario_from_row(row)
                if scenario:
                    scenarios.append(scenario)
            except Exception as e:
                continue  # Skip invalid rows

        return scenarios

    def _get_cso_scenario_from_row(self, row: int) -> Optional[AnalysisScenario]:
        """Extract CSO scenario from CSO table row."""
        table = self.cso_scenario_table

        # NEW COLUMN ORDER: Scenario Name, Asset, Config, then 7 intervention params
        scenario_item = table.item(row, 0)
        asset_combo = table.cellWidget(row, 1)
        config_combo = table.cellWidget(row, 2)
        pff_widget = table.cellWidget(row, 3)
        pump_mode_combo = table.cellWidget(row, 4)
        pump_rate_widget = table.cellWidget(row, 5)
        time_delay_widget = table.cellWidget(row, 6)
        flow_threshold_widget = table.cellWidget(row, 7)
        depth_threshold_widget = table.cellWidget(row, 8)
        tank_volume_widget = table.cellWidget(row, 9)

        if not all([asset_combo, config_combo, scenario_item]):
            return None

        cso_name = asset_combo.currentText()
        config_name = config_combo.currentText()
        scenario_name_raw = scenario_item.text().strip() or "Unnamed"

        # Validate and sanitize scenario name
        is_valid, error_msg = self._validate_scenario_name(scenario_name_raw)
        if not is_valid:
            # Show error to user and sanitize
            QMessageBox.warning(
                self,
                "Invalid Scenario Name",
                f"Scenario in row {row + 1}:\n\n{error_msg}\n\nThe name will be automatically corrected."
            )
            scenario_name = self._sanitize_scenario_name(scenario_name_raw)
            # Update the table with sanitized name
            scenario_item.setText(scenario_name)
        else:
            scenario_name = scenario_name_raw

        try:
            scenario = AnalysisScenario(
                cso_name=cso_name,
                config_name=config_name,
                scenario_name=scenario_name,
                pff_increase=pff_widget.value() if pff_widget else 0.0,
                pumping_mode=pump_mode_combo.currentText() if pump_mode_combo else "Fixed",
                pump_rate=pump_rate_widget.value() if pump_rate_widget else 0.0,
                time_delay=time_delay_widget.value() if time_delay_widget else 0,
                flow_return_threshold=flow_threshold_widget.value() if flow_threshold_widget else 0.0,
                depth_return_threshold=depth_threshold_widget.value(
                ) if depth_threshold_widget else 0.0,
                tank_volume=tank_volume_widget.value() if tank_volume_widget else None,
            )
            return scenario
        except Exception:
            return None

    def _get_catchment_scenario_from_row(self, parent_row: int) -> Optional[AnalysisScenario]:
        """Extract catchment scenario from parent row and its child rows."""
        table = self.catchment_scenario_table

        # NEW COLUMN ORDER: Expand, Scenario Name, Catchment/CSO, Config, then 7 empty intervention cols
        scenario_item = table.item(parent_row, 1)
        catchment_combo = table.cellWidget(parent_row, 2)
        config_combo = table.cellWidget(parent_row, 3)

        if not all([catchment_combo, config_combo, scenario_item]):
            return None

        catchment_name = catchment_combo.currentText()
        config_name = config_combo.currentText()
        scenario_name_raw = scenario_item.text().strip() or "Unnamed"

        # Validate and sanitize scenario name
        is_valid, error_msg = self._validate_scenario_name(scenario_name_raw)
        if not is_valid:
            QMessageBox.warning(
                self,
                "Invalid Scenario Name",
                f"Catchment scenario in row {parent_row + 1}:\n\n{error_msg}\n\nThe name will be automatically corrected."
            )
            scenario_name = self._sanitize_scenario_name(scenario_name_raw)
            scenario_item.setText(scenario_name)
        else:
            scenario_name = scenario_name_raw

        # Get child rows and extract per-CSO interventions
        child_rows = self._get_child_rows(parent_row)
        cso_interventions = {}

        for child_row in child_rows:
            # Get CSO name from child row column 2 (label widget - Catchment/CSO column)
            cso_label = table.cellWidget(child_row, 2)
            if not cso_label:
                continue

            # Extract CSO name from label text (format: "    └─ CSO Name")
            cso_text = cso_label.text()
            cso_name = cso_text.replace("└─", "").strip()

            # Get intervention widgets from columns 4-10
            pff_widget = table.cellWidget(child_row, 4)
            pump_mode_combo = table.cellWidget(child_row, 5)
            pump_rate_widget = table.cellWidget(child_row, 6)
            time_delay_widget = table.cellWidget(child_row, 7)
            flow_threshold_widget = table.cellWidget(child_row, 8)
            depth_threshold_widget = table.cellWidget(child_row, 9)
            tank_volume_widget = table.cellWidget(child_row, 10)

            # Store per-CSO interventions
            cso_interventions[cso_name] = {
                'pff_increase': pff_widget.value() if pff_widget else 0.0,
                'pumping_mode': pump_mode_combo.currentText() if pump_mode_combo else "Fixed",
                'pump_rate': pump_rate_widget.value() if pump_rate_widget else 0.0,
                'time_delay': time_delay_widget.value() if time_delay_widget else 0,
                'flow_return_threshold': flow_threshold_widget.value() if flow_threshold_widget else 0.0,
                'depth_return_threshold': depth_threshold_widget.value() if depth_threshold_widget else 0.0,
                'tank_volume': tank_volume_widget.value() if tank_volume_widget else None,
            }

        try:
            scenario = AnalysisScenario(
                catchment_name=catchment_name,
                config_name=config_name,
                scenario_name=scenario_name,
                cso_interventions=cso_interventions,
            )
            return scenario
        except Exception:
            return None

    def _get_wwtw_scenario_from_row(self, row: int) -> Optional[AnalysisScenario]:
        """Extract WwTW scenario from WwTW table row."""
        table = self.wwtw_scenario_table

        # NEW COLUMN ORDER: Scenario Name, Asset, Config, Tank Volume, then 5 WwTW params
        scenario_item = table.item(row, 0)
        asset_combo = table.cellWidget(row, 1)
        config_combo = table.cellWidget(row, 2)
        tank_volume_widget = table.cellWidget(row, 3)
        fft_aug_widget = table.cellWidget(row, 4)
        wwtw_pump_rate_widget = table.cellWidget(row, 5)
        wwtw_on_widget = table.cellWidget(row, 6)
        wwtw_off_widget = table.cellWidget(row, 7)
        wwtw_time_delay_widget = table.cellWidget(row, 8)

        if not all([asset_combo, config_combo, scenario_item]):
            return None

        wwtw_name = asset_combo.currentText()
        config_name = config_combo.currentText()
        scenario_name_raw = scenario_item.text().strip() or "Unnamed"

        # Validate and sanitize scenario name
        is_valid, error_msg = self._validate_scenario_name(scenario_name_raw)
        if not is_valid:
            QMessageBox.warning(
                self,
                "Invalid Scenario Name",
                f"WwTW scenario in row {row + 1}:\n\n{error_msg}\n\nThe name will be automatically corrected."
            )
            scenario_name = self._sanitize_scenario_name(scenario_name_raw)
            scenario_item.setText(scenario_name)
        else:
            scenario_name = scenario_name_raw

        try:
            tank_vol_value = tank_volume_widget.value() if tank_volume_widget else 0.0

            scenario = AnalysisScenario(
                wwtw_name=wwtw_name,
                config_name=config_name,
                scenario_name=scenario_name,
                tank_volume=tank_vol_value,
                fft_augmentation=fft_aug_widget.value() if fft_aug_widget else 0.0,
                wwtw_pump_rate=wwtw_pump_rate_widget.value() if wwtw_pump_rate_widget else 0.0,
                wwtw_pump_on_threshold=wwtw_on_widget.value() if wwtw_on_widget else 0.0,
                wwtw_pump_off_threshold=wwtw_off_widget.value() if wwtw_off_widget else 0.0,
                wwtw_time_delay_hours=wwtw_time_delay_widget.value() if wwtw_time_delay_widget else 0,
            )

            return scenario
        except Exception:
            return None

    def _analyze_selected_scenario(self) -> None:
        """Get the currently selected scenario row and open flow analyzer."""
        current_table = self._get_current_table()
        current_mode = self._get_current_mode()

        selected_rows = set(item.row()
                            for item in current_table.selectedItems())
        if not selected_rows:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a scenario to analyze."
            )
            return

        if len(selected_rows) > 1:
            QMessageBox.warning(
                self,
                "Multiple Selection",
                "Please select only one scenario to analyze."
            )
            return

        # Get the selected row
        row = list(selected_rows)[0]

        # For catchment table, only allow analyzing child rows (individual CSOs)
        if current_mode == 'Catchment':
            if not self._is_child_row(row):
                QMessageBox.warning(
                    self,
                    "Invalid Selection",
                    "Please select a CSO row (child row) to analyze.\n\n"
                    "Flow analysis is performed on individual CSOs, not catchments."
                )
                return

        # Call the flow analyzer with the selected row
        self._show_flow_analyzer(row)

    def _show_flow_analyzer(self, row: int) -> None:
        """
        Show the flow return analyzer dialog for the selected scenario.

        PERFORMANCE TOGGLE:
        - USE_SPILL_FOCUSED_ANALYSIS = True (NEW): Only analyzes continuation flow during spill periods
          * Faster: ~5-10x speedup
          * More relevant: Flow return threshold only matters during spills
        - USE_SPILL_FOCUSED_ANALYSIS = False (OLD): Analyzes entire continuation flow time series
          * Slower but uses full dataset
          * To revert: Just change the flag below to False
        """
        # Get main window and data import tab
        main_window = self.window()
        data_import_tab = getattr(main_window, 'data_import_tab', None)

        if not data_import_tab or not data_import_tab.imported_data:
            QMessageBox.warning(
                self,
                "No Flow Data",
                "Flow data has not been imported yet. Please import data first."
            )
            return

        imported_data = data_import_tab.imported_data
        data_folder = imported_data.get('data_folder')
        file_type = imported_data.get('file_type', 'csv')

        if not data_folder:
            QMessageBox.warning(
                self,
                "No Data",
                "No data folder found. Please import data first."
            )
            return

        current_table = self._get_current_table()
        if self._get_current_mode() == 'Catchment':
            asset_widget = current_table.cellWidget(row, 2)
            cso_text = asset_widget.text()
            cso_name = cso_text.replace("└─", "").strip()
        else:
            asset_widget = current_table.cellWidget(row, 1)
            cso_name = asset_widget.currentText()

            # QMessageBox.warning(self, "Error", "Could not determine CSO name")
            # return

        # Find the CSO asset to get continuation link
        cso_asset = next(
            (a for a in self.cso_assets if a.name == cso_name), None)
        if not cso_asset:
            QMessageBox.warning(
                self,
                "CSO Not Found",
                f"Could not find CSO asset '{cso_name}'"
            )
            return

        continuation_link = cso_asset.continuation_link

        # Get flow statistics efficiently (no full data load)
        # Toggle flag: Set to False to revert to full continuation flow analysis
        USE_SPILL_FOCUSED_ANALYSIS = True

        try:
            if USE_SPILL_FOCUSED_ANALYSIS and cso_asset.overflow_links:
                # NEW: Load statistics only during spill periods (more efficient and relevant)
                overflow_link = cso_asset.overflow_links[0]
                flow_statistics = data_import_tab.get_flow_statistics_during_spills(
                    continuation_link, overflow_link)
            else:
                # OLD: Load statistics for entire continuation flow time series
                flow_statistics = data_import_tab.get_flow_statistics(
                    continuation_link)

            if flow_statistics is None:
                QMessageBox.warning(
                    self,
                    "No Flow Data",
                    f"Could not load flow statistics for continuation link '{continuation_link}'"
                )
                return

            # Get timestep from flow_statistics
            # Both get_flow_statistics() and get_flow_statistics_during_spills()
            # now provide timestep_seconds directly in the returned dictionary
            timestep_seconds = flow_statistics.get('timestep_seconds', 300)

            # Get current parameter values from the row
            if self._get_current_mode() == 'Catchment':
                pff_spin = self.catchment_scenario_table.cellWidget(row, 4)
                pump_rate_spin = self.catchment_scenario_table.cellWidget(
                    row, 6)
                threshold_spin = self.catchment_scenario_table.cellWidget(
                    row, 8)
            else:
                pff_spin = self.scenarios_table.cellWidget(row, 3)
                pump_rate_spin = self.scenarios_table.cellWidget(row, 5)
                threshold_spin = self.scenarios_table.cellWidget(row, 7)

            pff_increase = pff_spin.value() if pff_spin else 0.0
            pump_rate = pump_rate_spin.value() if pump_rate_spin else 0.0
            threshold = threshold_spin.value() if threshold_spin else 0.0

            # Show the analyzer dialog with statistics (fast!)
            dialog = FlowReturnAnalyzerDialog(
                cso_name=cso_name,
                flow_statistics=flow_statistics,
                initial_pump_rate=pump_rate,
                initial_threshold=threshold,
                pff_increase=pff_increase,
                timestep_seconds=timestep_seconds,
                parent=self
            )
            dialog.exec()

        except Exception as e:
            import traceback
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load flow data and open analyzer:\n{str(e)}\n\n{traceback.format_exc()}"
            )

    def update_status(self) -> None:
        """Update the status label."""
        cso_count = self.cso_scenario_table.rowCount() if self.cso_scenario_table else 0
        catchment_count = self.catchment_scenario_table.rowCount(
        ) if self.catchment_scenario_table else 0
        wwtw_count = self.wwtw_scenario_table.rowCount() if self.wwtw_scenario_table else 0
        total_count = cso_count + catchment_count + wwtw_count

        has_assets = len(self.available_csos) > 0 or len(
            self.available_wwtws) > 0 or len(self.available_catchments) > 0

        if not has_assets:
            self.status_label.setText(
                "No assets available. Please define CSO, Catchment, or WwTW assets first.")
        elif not self.available_configs:
            self.status_label.setText(
                "No analysis configurations available. Please define configurations first.")
        elif total_count == 0:
            self.status_label.setText("No scenarios defined")
        elif total_count == 1:
            self.status_label.setText("1 scenario defined")
        else:
            self.status_label.setText(
                f"{total_count} scenarios defined (CSO: {cso_count}, Catchment: {catchment_count}, WwTW: {wwtw_count})"
            )

    def get_scenarios_for_cso(self, cso_name: str) -> List[AnalysisScenario]:
        """Get all scenarios for a specific CSO."""
        return [s for s in self.get_scenarios() if s.cso_name == cso_name]

    def get_state(self) -> dict:
        """Get current state for saving to project file."""
        scenarios = self.get_scenarios()
        return {
            'scenarios': [s.to_dict() for s in scenarios],
            'available_csos': self.available_csos,
            'available_configs': self.available_configs,
            # 'active_tab_index': self.scenario_tabs.currentIndex(),  # Save which tab is active
            'active_tab_index': self.tab_widget.currentIndex(),
        }

    def load_state(self, state: dict) -> None:
        """Load state from project file."""
        # Clear existing scenarios from all tables
        self.cso_scenario_table.setRowCount(0)
        self.catchment_scenario_table.setRowCount(0)
        self.wwtw_scenario_table.setRowCount(0)
        self.catchment_row_metadata.clear()  # Clear hierarchical metadata

        # Restore available CSOs and configs (these should be restored by their respective tabs first)
        if 'available_csos' in state:
            self.available_csos = state['available_csos']
        if 'available_configs' in state:
            self.available_configs = state['available_configs']

        # Restore scenarios to appropriate tables based on type
        if 'scenarios' in state:
            for scenario_data in state['scenarios']:
                try:
                    # Use from_dict to properly reconstruct scenario with all fields
                    scenario = AnalysisScenario.from_dict(scenario_data)

                    # Add to appropriate table based on scenario type
                    if scenario.is_catchment_scenario():
                        self._load_catchment_scenario_to_new_table(scenario)
                    elif scenario.is_wwtw_scenario():
                        self._load_wwtw_scenario_to_new_table(scenario)
                    else:
                        self._load_cso_scenario_to_new_table(scenario)
                except Exception as e:
                    print(f"Error loading scenario: {e}")
                    continue

        # Restore active tab
        if 'active_tab_index' in state:
            self.tab_widget.setCurrentIndex(state['active_tab_index'])
            # self.scenario_tabs.setCurrentIndex(state['active_tab_index'])

        self.update_status()

    def _load_cso_scenario_to_new_table(self, scenario: AnalysisScenario) -> None:
        """Load a CSO scenario into the CSO table."""
        self._add_cso_scenario()
        row = self.cso_scenario_table.rowCount() - 1
        self._populate_cso_row(row, scenario)

    def _load_wwtw_scenario_to_new_table(self, scenario: AnalysisScenario) -> None:
        """Load a WwTW scenario into the WwTW table."""
        self._add_wwtw_scenario()
        row = self.wwtw_scenario_table.rowCount() - 1
        self._populate_wwtw_row(row, scenario)

    def _load_catchment_scenario_to_new_table(self, scenario: AnalysisScenario) -> None:
        """Load a catchment scenario into the catchment table (with parent + child rows)."""
        table = self.catchment_scenario_table

        # Add parent row
        self._add_catchment_scenario()
        parent_row = table.rowCount() - 1

        # Find actual parent row (last non-child row added)
        # After _add_catchment_scenario, children may have been added
        # We need to find the parent row that was just added
        for row in range(table.rowCount() - 1, -1, -1):
            if self._is_parent_row(row):
                parent_row = row
                break

        # Set parent row values
        scenario_item = table.item(parent_row, 1)
        catchment_combo = table.cellWidget(parent_row, 2)
        config_combo = table.cellWidget(parent_row, 3)

        # Block signals on the combos to prevent triggering _on_catchment_selected_new multiple times
        if catchment_combo:
            catchment_combo.blockSignals(True)
        if config_combo:
            config_combo.blockSignals(True)

        table.blockSignals(True)

        if scenario_item:
            scenario_item.setText(scenario.scenario_name)
        if config_combo:
            config_combo.setCurrentText(scenario.config_name)
        if catchment_combo:
            catchment_combo.setCurrentText(scenario.catchment_name or "")

        # Unblock combo signals BEFORE manually triggering child row creation
        if catchment_combo:
            catchment_combo.blockSignals(False)
        if config_combo:
            config_combo.blockSignals(False)

        # Manually trigger child row creation (this won't auto-trigger because we blocked signals above)
        if scenario.catchment_name:
            self._on_catchment_selected_new(
                parent_row, scenario.catchment_name)

        # Populate child rows with intervention values
        if scenario.cso_interventions:
            child_rows = self._get_child_rows(parent_row)
            for child_row in child_rows:
                # Get CSO name from child row
                cso_label = table.cellWidget(child_row, 2)
                if not cso_label:
                    continue

                cso_text = cso_label.text()
                cso_name = cso_text.replace("└─", "").strip()

                if cso_name in scenario.cso_interventions:
                    interventions = scenario.cso_interventions[cso_name]

                    # Set intervention widgets (columns 4-10)
                    widgets = [
                        (4, interventions.get('pff_increase', 0.0)),
                        (5, interventions.get('pumping_mode', 'Fixed')),
                        (6, interventions.get('pump_rate', 0.0)),
                        (7, interventions.get('time_delay', 0)),
                        (8, interventions.get('flow_return_threshold', 0.0)),
                        (9, interventions.get('depth_return_threshold', 0.0)),
                        (10, interventions.get('tank_volume') if interventions.get(
                            'tank_volume') is not None else 0.0),
                    ]

                    for col, value in widgets:
                        widget = table.cellWidget(child_row, col)
                        if widget:
                            if isinstance(widget, QComboBox):
                                widget.setCurrentText(str(value))
                            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                                widget.setValue(value)

        table.blockSignals(False)

        self.update_status()
        self.scenarios_changed.emit()
