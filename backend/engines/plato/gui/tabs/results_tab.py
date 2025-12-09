"""
Results Tab - Display analysis results with plots and tables.
"""

from typing import Any, Dict, Iterable, Tuple
import glob
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QTabWidget,
    QFileDialog, QMessageBox, QHeaderView, QComboBox,
    QMenu, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence

try:
    import pandas as pd
except ImportError:  # pragma: no cover - optional dependency
    pd = None

try:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    MATPLOTLIB_AVAILABLE = False


if MATPLOTLIB_AVAILABLE:
    class XAxisOnlyNavigationToolbar(NavigationToolbar):
        """Custom navigation toolbar that locks zoom/pan to x-axis only."""

        def __init__(self, canvas, parent):
            super().__init__(canvas, parent)

        def press_zoom(self, event):
            """Override zoom to lock to x-axis by setting event.key = 'x'."""
            event.key = 'x'
            super().press_zoom(event)

        def drag_zoom(self, event):
            """Override drag zoom to lock to x-axis by setting event.key = 'x'."""
            event.key = 'x'
            super().drag_zoom(event)

        def release_zoom(self, event):
            """Override release zoom to lock to x-axis by setting event.key = 'x'."""
            event.key = 'x'
            super().release_zoom(event)

        def press_pan(self, event):
            """Override pan to lock to x-axis by setting event.key = 'x'."""
            event.key = 'x'
            super().press_pan(event)

        def drag_pan(self, event):
            """Override drag pan to lock to x-axis by setting event.key = 'x'."""
            event.key = 'x'
            super().drag_pan(event)

        def release_pan(self, event):
            """Override release pan to lock to x-axis by setting event.key = 'x'."""
            event.key = 'x'
            super().release_pan(event)


class CopyableTableWidget(QTableWidget):
    """QTableWidget with context menu for copying selected cells."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Enable selection of multiple items
        self.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.matches(QKeySequence.StandardKey.Copy):
            self.copy_selected_cells()
            event.accept()
        else:
            super().keyPressEvent(event)

    def show_context_menu(self, position):
        """Show context menu at the given position."""
        if self.itemAt(position) is None:
            return

        context_menu = QMenu(self)

        copy_action = QAction("Copy Selected Cells (Ctrl+C)", self)
        copy_action.triggered.connect(self.copy_selected_cells)
        context_menu.addAction(copy_action)

        copy_row_action = QAction("Copy Selected Rows", self)
        copy_row_action.triggered.connect(self.copy_selected_rows)
        context_menu.addAction(copy_row_action)

        context_menu.addSeparator()

        select_all_action = QAction("Select All", self)
        select_all_action.triggered.connect(self.selectAll)
        context_menu.addAction(select_all_action)

        context_menu.exec(self.mapToGlobal(position))

    def copy_selected_cells(self):
        """Copy selected cells to clipboard as tab-separated values."""
        selection = self.selectionModel().selectedIndexes()
        if not selection:
            return

        # Group by row
        rows = {}
        for index in selection:
            row = index.row()
            col = index.column()
            if row not in rows:
                rows[row] = {}
            rows[row][col] = index

        # Build text with proper spacing
        text_lines = []
        for row in sorted(rows.keys()):
            cols = rows[row]
            line_parts = []
            for col in sorted(cols.keys()):
                item = self.item(row, col)
                text = item.text() if item else ""
                line_parts.append(text)
            text_lines.append("\t".join(line_parts))

        clipboard_text = "\n".join(text_lines)
        QApplication.clipboard().setText(clipboard_text)

    def copy_selected_rows(self):
        """Copy entire selected rows to clipboard as tab-separated values."""
        selection = self.selectionModel().selectedRows()
        if not selection:
            return

        text_lines = []
        for index in sorted(selection, key=lambda x: x.row()):
            row = index.row()
            line_parts = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                text = item.text() if item else ""
                line_parts.append(text)
            text_lines.append("\t".join(line_parts))

        clipboard_text = "\n".join(text_lines)
        QApplication.clipboard().setText(clipboard_text)


class ResultsTab(QWidget):
    """Tab for displaying analysis results."""

    META_KEYS = {"effective_csos", "_scenario", "error"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.results_data: Dict[str, Any] = {}
        self.available_scenarios: list = []  # Track current scenarios from Scenarios tab
        self.init_ui()

    def _iter_cso_results(self) -> Iterable[Tuple[str, Dict[str, Any]]]:
        """Yield (name, result) tuples for CSO entries only."""
        for name, result in self.results_data.items():
            if name in self.META_KEYS:
                continue
            if not isinstance(result, dict):
                continue
            yield name, result

    def init_ui(self):
        """Initialise the user interface."""
        layout = QVBoxLayout(self)

        button_layout = QHBoxLayout()

        # self.refresh_btn = QPushButton("🔄 Refresh")
        # self.refresh_btn.clicked.connect(self.refresh_display)
        # button_layout.addWidget(self.refresh_btn)

        # self.load_outputs_btn = QPushButton("📂 Load Outputs...")
        # self.load_outputs_btn.clicked.connect(self.load_outputs_folder)
        # button_layout.addWidget(self.load_outputs_btn)

        self.cleanup_btn = QPushButton("🧹 Clean Up Orphaned Results")
        self.cleanup_btn.setToolTip(
            "Remove results for scenarios that no longer exist in the Scenarios tab"
        )
        self.cleanup_btn.clicked.connect(self.cleanup_orphaned_results)
        button_layout.addWidget(self.cleanup_btn)

        button_layout.addStretch()

        self.export_table_btn = QPushButton("Export Table to CSV...")
        self.export_table_btn.clicked.connect(self.export_table)
        button_layout.addWidget(self.export_table_btn)

        self.export_plots_btn = QPushButton("Export Plots...")
        self.export_plots_btn.clicked.connect(self.export_plots)
        button_layout.addWidget(self.export_plots_btn)

        layout.addLayout(button_layout)

        self.results_tabs = QTabWidget()

        self.summary_widget = self.create_summary_tab()
        self.results_tabs.addTab(self.summary_widget, "📋 Summary")

        self.plots_widget = self.create_plots_tab()
        self.results_tabs.addTab(self.plots_widget, "📈 Plots")

        self.details_widget = self.create_details_tab()
        self.results_tabs.addTab(self.details_widget, "📊 Detailed Results")

        layout.addWidget(self.results_tabs, 1)

        self.status_label = QLabel("No results to display")
        self.status_label.setStyleSheet(
            "QLabel { color: gray; font-style: italic; }"
        )
        layout.addWidget(self.status_label)

    def create_summary_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.summary_table = CopyableTableWidget()
        self.summary_table.setAlternatingRowColors(True)
        layout.addWidget(self.summary_table)

        return widget

    def create_plots_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        if MATPLOTLIB_AVAILABLE:
            selector_layout = QHBoxLayout()
            selector_layout.addWidget(QLabel("Select CSO:"))

            self.cso_selector = QComboBox()
            self.cso_selector.currentTextChanged.connect(self.update_plots)
            selector_layout.addWidget(self.cso_selector, 1)

            self.view_legacy_plot_btn = QPushButton("View Legacy Plot (Bokeh)")
            self.view_legacy_plot_btn.clicked.connect(self.view_legacy_plot)
            selector_layout.addWidget(self.view_legacy_plot_btn)

            selector_layout.addStretch()
            layout.addLayout(selector_layout)

            self.figure = Figure(figsize=(10, 6))
            self.canvas = FigureCanvas(self.figure)

            # Add custom matplotlib navigation toolbar (x-axis zoom/pan only)
            self.toolbar = XAxisOnlyNavigationToolbar(self.canvas, widget)
            layout.addWidget(self.toolbar)

            layout.addWidget(self.canvas, 1)
        else:
            layout.addWidget(
                QLabel("Matplotlib not available. Install matplotlib to view plots.")
            )

        return widget

    def create_details_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Add CSO selector for details
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Select CSO:"))

        self.details_cso_selector = QComboBox()
        self.details_cso_selector.currentTextChanged.connect(
            self.update_details_table)
        selector_layout.addWidget(self.details_cso_selector, 1)

        selector_layout.addStretch()
        layout.addLayout(selector_layout)

        self.details_table = CopyableTableWidget()
        self.details_table.setAlternatingRowColors(True)
        layout.addWidget(self.details_table)

        return widget

    def on_analysis_completed(self, results: Dict[str, Any]):
        self.results_data = results or {}
        self.refresh_display()

    def refresh_display(self):
        cso_items = list(self._iter_cso_results())

        if not cso_items:
            self.summary_table.clear()
            self.summary_table.setRowCount(0)
            self.summary_table.setColumnCount(0)

            self.details_table.clear()
            self.details_table.setRowCount(0)
            self.details_table.setColumnCount(0)

            self.details_cso_selector.blockSignals(True)
            self.details_cso_selector.clear()
            self.details_cso_selector.blockSignals(False)

            if MATPLOTLIB_AVAILABLE:
                self.cso_selector.blockSignals(True)
                self.cso_selector.clear()
                self.cso_selector.blockSignals(False)
                self.figure.clear()
                self.canvas.draw()

            self.status_label.setText("No results to display")
            self.status_label.setStyleSheet(
                "QLabel { color: gray; font-style: italic; }"
            )
            return

        self.populate_summary_table()

        # Get scenario names (which are the keys in results_data)
        # Preserve the original order from results_data (which matches scenario order)
        # Don't sort - maintain the order they were analyzed in
        scenario_names = [name for name, _ in cso_items]

        if MATPLOTLIB_AVAILABLE:
            current = self.cso_selector.currentText()

            self.cso_selector.blockSignals(True)
            self.cso_selector.clear()
            self.cso_selector.addItems(scenario_names)

            target = current if current in scenario_names else scenario_names[0]
            index = self.cso_selector.findText(target)
            if index >= 0:
                self.cso_selector.setCurrentIndex(index)
            self.cso_selector.blockSignals(False)

            self.update_plots(self.cso_selector.currentText())

        # Update details tab selector
        current_details = self.details_cso_selector.currentText()

        self.details_cso_selector.blockSignals(True)
        self.details_cso_selector.clear()
        self.details_cso_selector.addItems(scenario_names)

        target_details = current_details if current_details in scenario_names else scenario_names[
            0]
        index_details = self.details_cso_selector.findText(target_details)
        if index_details >= 0:
            self.details_cso_selector.setCurrentIndex(index_details)
        self.details_cso_selector.blockSignals(False)

        self.update_details_table(self.details_cso_selector.currentText())

        self.status_label.setText(
            f"Displaying results for {len(cso_items)} scenario(s)"
        )
        self.status_label.setStyleSheet("QLabel { color: green; }")

    def populate_summary_table(self):
        columns = [
            "Scenario Name",
            "CSO",
            "Converged",
            "Iterations",
            "Storage (m³)",
            "Total Spills",
            "Bathing Spills",
            "Total Volume (m³)",
            "Bathing Volume (m³)",
            "Total Duration (hrs)",
            "Bathing Duration (hrs)",
        ]

        self.summary_table.clear()
        self.summary_table.setColumnCount(len(columns))
        self.summary_table.setHorizontalHeaderLabels(columns)

        # Preserve original order from results (matches scenario order)
        cso_items = list(self._iter_cso_results())
        self.summary_table.setRowCount(len(cso_items))

        for row, (scenario_name, result) in enumerate(cso_items):
            # Scenario name is the key (column 0)
            self.summary_table.setItem(row, 0, QTableWidgetItem(scenario_name))

            # Check if this is refactored engine result (has _full_result key)
            if "_full_result" in result:
                try:
                    from plato.refactored.models import CSOAnalysisResult
                    full_result: CSOAnalysisResult = result["_full_result"]

                    # CSO name (column 1) - use display name if available, fallback to cso_name
                    cso_display_name = result.get(
                        '_cso_display_name', full_result.cso_name)
                    self.summary_table.setItem(
                        row, 1, QTableWidgetItem(cso_display_name))

                    # Converged status (column 2)
                    converged_text = "Yes" if full_result.converged else "No"
                    converged_item = QTableWidgetItem(converged_text)
                    if full_result.converged:
                        converged_item.setForeground(Qt.GlobalColor.darkGreen)
                    else:
                        converged_item.setForeground(Qt.GlobalColor.red)
                    self.summary_table.setItem(row, 2, converged_item)

                    # Iterations (column 3)
                    self.summary_table.setItem(
                        row, 3, QTableWidgetItem(
                            str(full_result.iterations_count))
                    )

                    # Storage (column 4)
                    self.summary_table.setItem(
                        row, 4, QTableWidgetItem(
                            f"{full_result.final_storage_m3:.1f}")
                    )

                    # Total spills (column 5)
                    self.summary_table.setItem(
                        row, 5, QTableWidgetItem(str(full_result.spill_count))
                    )

                    # Bathing spills (column 6)
                    self.summary_table.setItem(
                        row, 6, QTableWidgetItem(
                            str(full_result.bathing_spills_count))
                    )

                    # Total volume (column 7)
                    self.summary_table.setItem(
                        row, 7, QTableWidgetItem(
                            f"{full_result.total_spill_volume_m3:.1f}")
                    )

                    # Bathing volume (column 8)
                    self.summary_table.setItem(
                        row, 8, QTableWidgetItem(
                            f"{full_result.bathing_spill_volume_m3:.1f}")
                    )

                    # Total duration (column 9)
                    self.summary_table.setItem(
                        row, 9, QTableWidgetItem(
                            f"{full_result.total_spill_duration_hours:.1f}")
                    )

                    # Bathing duration (column 10)
                    self.summary_table.setItem(
                        row, 10, QTableWidgetItem(
                            f"{full_result.bathing_spill_duration_hours:.1f}")
                    )

                except Exception:
                    # Fall back to showing error
                    for col in range(1, 10):
                        self.summary_table.setItem(
                            row, col, QTableWidgetItem("-"))

            # Legacy result format (kept for backwards compatibility)
            elif "summary_df" in result:
                try:
                    summary_df = result["summary_df"]
                    final_row = summary_df.iloc[-1]

                    status = result.get("status", "unknown")
                    status_item = QTableWidgetItem(status.capitalize())
                    if status == "completed":
                        status_item.setForeground(Qt.GlobalColor.darkGreen)
                    elif status == "error":
                        status_item.setForeground(Qt.GlobalColor.red)
                    self.summary_table.setItem(row, 1, status_item)

                    iterations = len(summary_df)
                    self.summary_table.setItem(
                        row, 2, QTableWidgetItem(str(iterations))
                    )

                    tank_volume = final_row.get("Tank Volume", "-")
                    self.summary_table.setItem(
                        row, 3, QTableWidgetItem(str(tank_volume))
                    )

                    spills_entire = final_row.get(
                        "Number of Spills (Entire Period)", "-"
                    )
                    self.summary_table.setItem(
                        row, 4, QTableWidgetItem(str(spills_entire))
                    )

                    bathing_col = "Number of Spills (Bathing Season)"
                    bathing_val = (
                        final_row.get(bathing_col, "-")
                        if bathing_col in summary_df.columns
                        else "-"
                    )
                    self.summary_table.setItem(
                        row, 5, QTableWidgetItem(str(bathing_val))
                    )

                    # Leave volume columns empty for legacy
                    self.summary_table.setItem(row, 6, QTableWidgetItem("-"))
                    self.summary_table.setItem(row, 7, QTableWidgetItem("-"))
                except Exception:
                    for col in range(1, 8):
                        self.summary_table.setItem(
                            row, col, QTableWidgetItem("-"))
            else:
                for col in range(1, 8):
                    self.summary_table.setItem(row, col, QTableWidgetItem("-"))

        header = self.summary_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for idx in range(1, len(columns)):
            header.setSectionResizeMode(
                idx, QHeaderView.ResizeMode.ResizeToContents
            )

    def update_details_table(self, scenario_name: str):
        """Update details table to show spill events for selected CSO."""
        if not scenario_name:
            self.details_table.clear()
            self.details_table.setRowCount(0)
            self.details_table.setColumnCount(0)
            return

        if scenario_name not in self.results_data:
            self.details_table.clear()
            self.details_table.setRowCount(0)
            self.details_table.setColumnCount(0)
            return

        result = self.results_data[scenario_name]

        # Check if this is refactored engine result (has _full_result key)
        if "_full_result" in result:
            self._populate_spill_events_table(scenario_name, result)
        else:
            self._populate_legacy_details_table(scenario_name, result)

    def _populate_spill_events_table(self, cso_name: str, result: dict):
        """Show individual spill events from refactored engine."""
        from plato.refactored.models import CSOAnalysisResult

        try:
            full_result: CSOAnalysisResult = result["_full_result"]
            spill_events = full_result.spill_events

            headers = [
                "Spill #",
                "Start Time",
                "End Time",
                "Duration (hrs)",
                "Volume (m³)",
                "Peak Flow (m³/s)",
                "Bathing Season"
            ]

            self.details_table.clear()
            self.details_table.setColumnCount(len(headers))
            self.details_table.setHorizontalHeaderLabels(headers)
            self.details_table.setRowCount(len(spill_events))

            for row, spill_event in enumerate(spill_events):
                # Spill number
                self.details_table.setItem(
                    row, 0, QTableWidgetItem(str(row + 1)))

                # Start time
                start_time_str = spill_event.start_time.strftime(
                    "%Y-%m-%d %H:%M")
                self.details_table.setItem(
                    row, 1, QTableWidgetItem(start_time_str))

                # End time
                end_time_str = spill_event.end_time.strftime("%Y-%m-%d %H:%M")
                self.details_table.setItem(
                    row, 2, QTableWidgetItem(end_time_str))

                # Duration
                self.details_table.setItem(
                    row, 3, QTableWidgetItem(
                        f"{spill_event.spill_duration_hours:.1f}")
                )

                # Volume
                self.details_table.setItem(
                    row, 4, QTableWidgetItem(f"{spill_event.volume_m3:.1f}")
                )

                # Peak flow
                self.details_table.setItem(
                    row, 5, QTableWidgetItem(
                        f"{spill_event.peak_flow_m3s:.3f}")
                )

                # Bathing season indicator (use standard May 15 - Sep 30)
                is_bathing = spill_event.is_in_bathing_season(5, 15, 9, 30)
                bathing_item = QTableWidgetItem("Yes" if is_bathing else "No")
                if is_bathing:
                    bathing_item.setForeground(Qt.GlobalColor.red)
                self.details_table.setItem(row, 6, bathing_item)

            # Resize columns
            header = self.details_table.horizontalHeader()
            for idx in range(len(headers)):
                header.setSectionResizeMode(
                    idx, QHeaderView.ResizeMode.ResizeToContents)

        except Exception as e:
            # Show error
            self.details_table.clear()
            self.details_table.setRowCount(1)
            self.details_table.setColumnCount(1)
            self.details_table.setItem(
                0, 0, QTableWidgetItem(f"Error: {str(e)}"))

    def _populate_legacy_details_table(self, cso_name: str, result: dict):
        """Show legacy file paths (backwards compatibility)."""
        headers = ["Property", "Value"]

        self.details_table.clear()
        self.details_table.setColumnCount(len(headers))
        self.details_table.setHorizontalHeaderLabels(headers)

        rows_data = [
            ("CSO Name", cso_name),
            ("Output Folder", result.get("output_directory", "-")),
            ("Summary CSV", result.get("summary_path", "-")),
            ("Latest Results CSV", result.get("latest_results_csv", "-"))
        ]

        self.details_table.setRowCount(len(rows_data))

        for row, (prop, value) in enumerate(rows_data):
            self.details_table.setItem(row, 0, QTableWidgetItem(prop))
            self.details_table.setItem(row, 1, QTableWidgetItem(str(value)))

        header = self.details_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def update_plots(self, scenario_name: str):
        if not MATPLOTLIB_AVAILABLE or not scenario_name:
            return

        if scenario_name not in self.results_data:
            return

        result = self.results_data[scenario_name]

        # Check if this is refactored engine result (has _full_result key)
        if "_full_result" in result:
            self._plot_refactored_result(scenario_name, result)
        else:
            self._plot_legacy_result(scenario_name, result)

    def _plot_refactored_result(self, cso_name: str, result: dict):
        """Plot results from refactored engine."""
        from plato.refactored.models import CSOAnalysisResult

        try:
            full_result: CSOAnalysisResult = result["_full_result"]
            time_series = full_result.time_series

            # Detect if this is a catchment engine result (different column naming)
            # Differentiator: Catchment uses 'Tank Volume' (with space), Single CSO uses 'Tank_Volume' (with underscore)
            is_catchment = 'Tank Volume' in time_series.columns

            # Detect if this is a WwTW result (different column structure)
            # WwTW has 'Spill', 'Continuation', 'Original Continuation', 'Tank Volume'
            is_wwtw = ('Spill' in time_series.columns and
                       'Continuation' in time_series.columns and
                       'Original Continuation' in time_series.columns and
                       'Tank Volume' in time_series.columns)

            if is_wwtw:
                # WwTW engine format - uses simple column names
                initial_spill_col = 'Original Spill'  # Spill flow before storage
                final_spill_col = 'Spill'  # Spill flow after storage
                initial_cont_col = 'Original Continuation'  # Continuation before storage
                final_cont_col = 'Continuation'  # Continuation after storage/pump adjustments
            elif is_catchment:
                # Catchment engine format
                # Find columns ending with _Flow (excluding Spill_Flow)
                # In catchment mode, columns are named after actual link IDs (e.g., "BS4334543.1_Flow")
                flow_cols = [col for col in time_series.columns
                             if col.endswith('_Flow') and col != 'Spill_Flow']

                # Usually there are 2 flow columns: overflow_link_Flow and continuation_link_Flow
                # We can't reliably match by scenario name, so use the actual CSO name from result
                actual_cso_name = full_result.cso_name  # This is the overflow link ID

                cso_flow_col = None
                cont_flow_col = None

                # Try to match using the actual CSO/overflow link name from the result
                for col in flow_cols:
                    if actual_cso_name in col or col.startswith(actual_cso_name):
                        cso_flow_col = col
                    else:
                        cont_flow_col = col

                # Fallback: if we couldn't identify by name, use the first two flow columns
                # (order matters - typically overflow comes before continuation in the data)
                if cso_flow_col is None and len(flow_cols) >= 1:
                    cso_flow_col = flow_cols[0]
                if cont_flow_col is None and len(flow_cols) >= 2:
                    cont_flow_col = flow_cols[1]

                # For catchment mode, CSO_Flow_Original is the true initial overflow (before storage)
                initial_spill_col = 'CSO_Flow_Original' if 'CSO_Flow_Original' in time_series.columns else cso_flow_col
                final_spill_col = 'Spill_Flow' if 'Spill_Flow' in time_series.columns else cso_flow_col
                # Catchment engine now creates Cont_Flow_Original just like single CSO mode
                initial_cont_col = 'Cont_Flow_Original'  # Original before storage
                # This contains the modified (after storage) flow
                final_cont_col = cont_flow_col
            else:
                # Single CSO engine format
                initial_spill_col = 'CSO_Flow_Original'
                final_spill_col = 'Spill_Flow'
                initial_cont_col = 'Cont_Flow_Original'

                # Find the continuation link column (final flow)
                final_cont_col = None
                standard_cols = {'Time', 'CSO_Flow_Original', 'Cont_Flow_Original',
                                 'Spill_Flow', 'Tank_Volume', 'Spill_in_Time_Delay'}
                for col in time_series.columns:
                    if col not in standard_cols and not col.endswith('_Depth'):
                        final_cont_col = col
                        break

            self.figure.clear()
            # Create subplots with shared x-axis
            ax1 = self.figure.add_subplot(3, 1, 1)
            ax2 = self.figure.add_subplot(3, 1, 2, sharex=ax1)
            ax3 = self.figure.add_subplot(3, 1, 3, sharex=ax1)

            # Plot 1: Continuation Flow (initial and final)
            # Both modes now have Cont_Flow_Original thanks to catchment engine
            if initial_cont_col and initial_cont_col in time_series.columns:
                # Plot initial continuation flow (before storage)
                ax1.plot(
                    time_series["Time"],
                    time_series[initial_cont_col],
                    color="red",
                    linewidth=0.8,
                    label="Initial (Before Storage)",
                    alpha=0.7
                )

                # Plot final continuation flow (after storage) if different column exists
                if final_cont_col and final_cont_col in time_series.columns:
                    ax1.plot(
                        time_series["Time"],
                        time_series[final_cont_col],
                        color="blue",
                        linewidth=0.8,
                        label="Final (After Storage)",
                        alpha=0.7
                    )

                ax1.set_title(f"{cso_name} - Continuation Flow")
                ax1.set_ylabel("Flow [m³/s]")
                ax1.legend(loc="upper left")
                ax1.grid(True, alpha=0.3)

            # Plot 2: Spill Flow (initial and final)
            if final_spill_col and final_spill_col in time_series.columns:
                # Plot initial spill flow (before storage)
                if initial_spill_col and initial_spill_col in time_series.columns:
                    ax2.plot(
                        time_series["Time"],
                        time_series[initial_spill_col],
                        color="red",
                        linewidth=0.8,
                        label="Initial (Before Storage)",
                        alpha=0.7
                    )

                # Plot final spill flow (after storage)
                if final_spill_col != initial_spill_col or is_catchment:
                    ax2.plot(
                        time_series["Time"],
                        time_series[final_spill_col],
                        color="blue",
                        linewidth=0.8,
                        label="Final (After Storage)" if not is_catchment else "Spill Flow",
                        alpha=0.7
                    )
                ax2.set_title(f"{cso_name} - Spill Flow (Initial and Final)")
                ax2.set_ylabel("Flow [m³/s]")
                ax2.legend(loc="upper left")
                ax2.grid(True, alpha=0.3)

                # # Highlight spill events if available
                # for spill_event in full_result.spill_events:
                #     ax2.axvspan(
                #         spill_event.start_time,
                #         spill_event.end_time,
                #         alpha=0.2,
                #         color='red',
                #         label='Spill Event' if spill_event == full_result.spill_events[0] else ""
                #     )

                # Highlight spill events if available
                for i, spill_event in enumerate(full_result.spill_events):
                    # Color-code by window duration: 12hr = blue, 24hr = cyan
                    if spill_event.window_duration_hours == 12:
                        color = 'blue'
                        label_text = '12hr Window' if i == 0 else ""
                    elif spill_event.window_duration_hours == 24:
                        color = 'cyan'
                        # Find first 24hr event for label
                        is_first_24hr = all(
                            e.window_duration_hours != 24
                            for e in full_result.spill_events[:i]
                        )
                        label_text = '24hr Window' if is_first_24hr else ""
                    else:
                        # Fallback for unexpected durations
                        color = 'red'
                        label_text = f'{spill_event.window_duration_hours}hr Window' if i == 0 else ""

                    ax2.axvspan(
                        spill_event.start_time,
                        spill_event.end_time,
                        alpha=0.2,
                        color=color,
                        label=label_text
                    )

            # Plot 3: Tank Volume
            # Handle both formats: 'Tank_Volume' (CSO) and 'Tank Volume' (Catchment/WwTW)
            tank_vol_col = None
            if 'Tank_Volume' in time_series.columns:
                tank_vol_col = 'Tank_Volume'
            elif 'Tank Volume' in time_series.columns:
                tank_vol_col = 'Tank Volume'

            if tank_vol_col:
                ax3.plot(
                    time_series["Time"],
                    time_series[tank_vol_col],
                    color="green",
                    linewidth=0.8,
                    label=f"Tank Volume (Max: {full_result.final_storage_m3:.1f} m³)"
                )
                # Add horizontal line for max storage
                ax3.axhline(
                    y=full_result.final_storage_m3,
                    color='orange',
                    linestyle='--',
                    linewidth=1.5,
                    label='Tank Capacity'
                )
                ax3.set_title(f"{cso_name} - Storage Tank Volume")
                ax3.set_xlabel("Time")
                ax3.set_ylabel("Volume [m³]")
                ax3.legend(loc="upper left")
                ax3.grid(True, alpha=0.3)

            # Configure axes to auto-scale y when x changes
            def on_xlims_change(event_ax):
                """Auto-scale y-axis to visible data when x-axis changes."""
                for ax in [ax1, ax2, ax3]:
                    if ax.lines:  # Only if there are lines plotted
                        ax.relim()  # Recalculate limits based on visible data
                        # Only autoscale y
                        ax.autoscale_view(scalex=False, scaley=True)
                self.canvas.draw_idle()

            # Connect the callback to x-axis changes
            ax1.callbacks.connect('xlim_changed', on_xlims_change)

            self.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            # Show error message
            self.figure.clear()
            ax = self.figure.add_subplot(1, 1, 1)
            ax.text(
                0.5, 0.5,
                f"Error plotting results:\n{str(e)}",
                ha="center", va="center",
                transform=ax.transAxes,
                fontsize=12,
                color="red",
            )
            self.canvas.draw()

    def _plot_legacy_result(self, cso_name: str, result: dict):
        """Plot results from legacy engine (backwards compatibility)."""
        out_dir = result.get("output_directory")
        if not out_dir or not os.path.exists(out_dir):
            return
        if pd is None:
            QMessageBox.warning(
                self,
                "Plots Unavailable",
                "Install pandas to view detailed plots.",
            )
            return

        initial_csv = os.path.join(
            out_dir, "iteration_Initial", f"{cso_name}_results_Initial.csv"
        )
        if not os.path.exists(initial_csv):
            initial_csv = None

        summary_df = result.get("summary_df")
        final_csv = None
        if summary_df is not None and not summary_df.empty:
            try:
                last_row = summary_df.iloc[-1]
                final_iter = last_row["Iteration"] if "Iteration" in last_row else None
                if pd.notnull(final_iter):
                    candidate = os.path.join(
                        out_dir,
                        f"iteration_{int(final_iter)}",
                        f"{cso_name}_results_{int(final_iter)}.csv",
                    )
                    if os.path.exists(candidate):
                        final_csv = candidate
            except Exception:
                final_csv = None

        if not final_csv:
            iter_dirs = glob.glob(os.path.join(out_dir, "iteration_*"))
            max_iter = -1
            for directory in iter_dirs:
                base = os.path.basename(directory)
                if base == "iteration_Initial":
                    continue
                try:
                    iteration_number = int(base.replace("iteration_", ""))
                except Exception:
                    continue
                candidate = os.path.join(
                    directory, f"{cso_name}_results_{iteration_number}.csv"
                )
                if os.path.exists(candidate) and iteration_number > max_iter:
                    max_iter = iteration_number
                    final_csv = candidate

        if not final_csv:
            candidate = result.get("latest_results_csv")
            if candidate and os.path.exists(candidate):
                final_csv = candidate

        df_initial = (
            pd.read_csv(initial_csv, parse_dates=["Time"], dayfirst=True)
            if initial_csv
            else None
        )
        df_final = (
            pd.read_csv(final_csv, parse_dates=["Time"], dayfirst=True)
            if final_csv
            else None
        )

        self.figure.clear()
        ax1 = self.figure.add_subplot(3, 1, 1)
        ax2 = self.figure.add_subplot(3, 1, 2)
        ax3 = self.figure.add_subplot(3, 1, 3)

        cont_link = result.get("run_inputs", {}).get("Continuation Link")
        if cont_link:
            flow_column = f"{cont_link}_Flow"
            if df_initial is not None and flow_column in df_initial.columns:
                ax1.plot(
                    df_initial["Time"],
                    df_initial[flow_column],
                    color="red",
                    label="Initial",
                )
            if df_final is not None and flow_column in df_final.columns:
                ax1.plot(
                    df_final["Time"],
                    df_final[flow_column],
                    color="blue",
                    label="Final",
                )
            ax1.set_title(f"{cso_name} - Continuation Link Flow")
            ax1.set_xlabel("Time")
            ax1.set_ylabel("Flow [m³/s]")
            ax1.legend(loc="upper left")
            ax1.grid(True, alpha=0.3)
        else:
            ax1.text(
                0.5,
                0.5,
                "No Continuation Link data",
                ha="center",
                va="center",
                transform=ax1.transAxes,
                fontsize=12,
                color="gray",
            )

        spill_col = f"{cso_name}_Flow"
        if df_initial is not None and spill_col in df_initial.columns:
            ax2.plot(
                df_initial["Time"],
                df_initial[spill_col],
                color="red",
                label="Initial",
            )
        if df_final is not None and spill_col in df_final.columns:
            ax2.plot(
                df_final["Time"],
                df_final[spill_col],
                color="blue",
                label="Final",
            )
        ax2.set_title(f"{cso_name} - Spill Link Flow")
        ax2.set_xlabel("Time")
        ax2.set_ylabel("Flow [m³/s]")
        ax2.legend(loc="upper left")
        ax2.grid(True, alpha=0.3)

        if df_final is not None and "Tank Volume" in df_final.columns:
            ax3.plot(
                df_final["Time"],
                df_final["Tank Volume"],
                color="blue",
                label="Final",
            )
        if df_initial is not None and "Tank Volume" in df_initial.columns:
            ax3.plot(
                df_initial["Time"],
                df_initial["Tank Volume"],
                color="red",
                label="Initial",
            )
        ax3.set_title(f"{cso_name} - Tank Volume")
        ax3.set_xlabel("Time")
        ax3.set_ylabel("Volume [m³]")
        ax3.legend(loc="upper left")
        ax3.grid(True, alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw()

    def view_legacy_plot(self):
        if not MATPLOTLIB_AVAILABLE:
            return
        if not hasattr(self, "cso_selector"):
            return

        cso_name = self.cso_selector.currentText()
        if not cso_name or cso_name not in self.results_data:
            QMessageBox.information(
                self, "No Selection", "Please select a CSO with outputs."
            )
            return

        plots_html = self.results_data[cso_name].get("plots_html")
        if not plots_html or not os.path.exists(plots_html):
            QMessageBox.information(
                self, "No Plot", "No legacy Bokeh plot found for this CSO."
            )
            return

        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView  # type: ignore
            from PyQt6.QtCore import QUrl

            webview = QWebEngineView()
            webview.load(QUrl.fromLocalFile(os.path.abspath(plots_html)))

            dialog = QWidget()
            dialog.setWindowTitle(f"Legacy Plot - {cso_name}")
            dialog.setGeometry(200, 200, 1200, 800)
            dialog_layout = QVBoxLayout(dialog)
            dialog_layout.addWidget(webview)
            dialog.show()
        except Exception:
            import webbrowser

            webbrowser.open(f"file://{os.path.abspath(plots_html)}")

    def load_outputs_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select PLATO outputs folder", os.path.expanduser("~")
        )
        if not folder:
            return

        entries = []
        try:
            for name in os.listdir(folder):
                path = os.path.join(folder, name)
                if os.path.isdir(path) and "_Outputs_" in name:
                    entries.append(path)

            looks_like_outputs = "_Outputs_" in os.path.basename(folder)
            has_run_inputs = os.path.exists(
                os.path.join(folder, "RunInputs.csv"))
            if not entries and (looks_like_outputs or has_run_inputs):
                entries = [folder]
        except Exception:
            QMessageBox.critical(
                self, "Error", "Failed to scan selected folder")
            return

        # Check if any entries would be orphaned
        scenario_names = {
            scenario.scenario_name for scenario in self.available_scenarios
        } if self.available_scenarios else set()

        if scenario_names:  # Only check if we have scenario info
            valid_entries = []
            orphaned_entries = []

            for entry in entries:
                cso_name = os.path.basename(entry).split("_Outputs_")[0]
                if cso_name in scenario_names:
                    valid_entries.append(entry)
                else:
                    orphaned_entries.append(cso_name)

            if orphaned_entries and valid_entries:
                # Some entries would be orphaned - ask user
                orphaned_list = "\n".join(
                    f"  • {name}" for name in orphaned_entries)
                reply = QMessageBox.question(
                    self,
                    "Orphaned Results Found",
                    f"Found {len(orphaned_entries)} result(s) that don't match current scenarios:\n\n"
                    f"{orphaned_list}\n\n"
                    "These results won't be loaded since they don't correspond to "
                    "scenarios in the current project.\n\n"
                    f"Continue loading the {len(valid_entries)} matching result(s)?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )

                if reply == QMessageBox.StandardButton.No:
                    return

                entries = valid_entries
            elif orphaned_entries and not valid_entries:
                # All entries would be orphaned
                QMessageBox.information(
                    self,
                    "No Matching Results",
                    "None of the found results match scenarios in the current project.\n\n"
                    "No results will be loaded."
                )
                return

        self._load_entries_from_dirs(entries)

    def _load_entries_from_dirs(self, entries: Iterable[str]):
        if not entries:
            return

        loaded: Dict[str, Dict[str, Any]] = {}

        # Get current scenario names to filter against
        scenario_names = {
            scenario.scenario_name for scenario in self.available_scenarios
        } if self.available_scenarios else set()

        for out_dir in entries:
            cso_name = os.path.basename(out_dir).split("_Outputs_")[0]

            # Skip loading results that don't have corresponding scenarios
            # (unless we don't have scenario info yet, e.g., during initial load)
            if scenario_names and cso_name not in scenario_names:
                continue

            run_inputs_path = os.path.join(out_dir, "RunInputs.csv")
            summary_path = os.path.join(out_dir, f"Summary_{cso_name}.csv")
            plots_html = os.path.join(out_dir, "Plots", "Plots.html")

            run_inputs = None
            if pd is not None and os.path.exists(run_inputs_path):
                try:
                    run_inputs_df = pd.read_csv(run_inputs_path)
                    if not run_inputs_df.empty:
                        run_inputs = run_inputs_df.iloc[0].to_dict()
                except Exception:
                    run_inputs = None

            summary_df = None
            if pd is not None and os.path.exists(summary_path):
                try:
                    summary_df = pd.read_csv(summary_path)
                except Exception:
                    summary_df = None

            latest_results_csv = None
            try:
                pattern = os.path.join(
                    out_dir, "**", f"{cso_name}_results_*.csv")
                found = glob.glob(pattern, recursive=True)
                if found:
                    def iter_key(path: str) -> int:
                        base = os.path.basename(path)
                        for part in reversed(base.split("_")):
                            try:
                                return int(part.split(".")[0])
                            except Exception:
                                continue
                        return 0

                    latest_results_csv = max(found, key=iter_key)
            except Exception:
                latest_results_csv = None

            loaded[cso_name] = {
                "status": "completed",
                "output_directory": out_dir,
                "summary_path": summary_path if os.path.exists(summary_path) else "",
                "summary_df": summary_df,
                "run_inputs": run_inputs,
                "latest_results_csv": latest_results_csv,
                "plots_html": plots_html if os.path.exists(plots_html) else "",
            }

        existing = (
            self.results_data.copy()
            if isinstance(self.results_data, dict)
            else {}
        )
        for name, info in existing.items():
            # Also filter existing results against current scenarios
            if scenario_names and name not in scenario_names:
                continue
            if name not in loaded:
                loaded[name] = info

        self.results_data = loaded
        self.refresh_display()

    def export_table(self):
        if self.summary_table.rowCount() == 0:
            QMessageBox.information(self, "No Data", "No results to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results to CSV",
            "",
            "CSV Files (*.csv);;All Files (*.*)",
        )
        if not file_path:
            return

        if pd is None:
            QMessageBox.warning(
                self,
                "Export Unavailable",
                "Install pandas to export tables.",
            )
            return

        try:
            headers = []
            for col in range(self.summary_table.columnCount()):
                header_item = self.summary_table.horizontalHeaderItem(col)
                headers.append(
                    header_item.text() if header_item else f"Column {col + 1}"
                )

            data = []
            for row in range(self.summary_table.rowCount()):
                row_data = []
                for col in range(self.summary_table.columnCount()):
                    item = self.summary_table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)

            df = pd.DataFrame(data, columns=headers)
            df.to_csv(file_path, index=False)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Summary results exported to {file_path}",
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export table:\n{exc}",
            )

    def export_plots(self):
        if not MATPLOTLIB_AVAILABLE:
            QMessageBox.information(
                self,
                "Not Available",
                "Matplotlib is not installed. Cannot export plots.",
            )
            return
        if not hasattr(self, "cso_selector"):
            QMessageBox.information(
                self, "No Selection", "Please select a CSO to export."
            )
            return

        cso_name = self.cso_selector.currentText()
        if not cso_name:
            QMessageBox.information(
                self, "No Selection", "Please select a CSO to export."
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Plot",
            f"{cso_name}_plot.png",
            "PNG Files (*.png);;PDF Files (*.pdf);;All Files (*.*)",
        )
        if not file_path:
            return

        try:
            self.figure.savefig(file_path, dpi=300, bbox_inches="tight")
            QMessageBox.information(
                self,
                "Export Successful",
                f"Plot exported to:\n{file_path}",
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export plot:\n{exc}",
            )

    def get_state(self) -> Dict[str, Any]:
        return {
            "results_data": {},
            "has_results": bool(self.results_data),
        }

    def load_state(self, state: Dict[str, Any]):
        if isinstance(state, dict) and state.get("results_data"):
            return

        try:
            parent = self.parent() or self.window()
            analysis_results: Dict[str, Any] = {}
            if parent and hasattr(parent, "analysis_tab"):
                analysis_results = getattr(
                    parent.analysis_tab, "analysis_results", {}
                ) or {}  # type: ignore[attr-defined]

            directories = []
            for info in analysis_results.values():
                out_dir = info.get("output_directory") if isinstance(
                    info, dict) else None
                if out_dir and os.path.exists(out_dir):
                    directories.append(out_dir)

            if directories:
                self._load_entries_from_dirs(directories)
        except Exception:
            return

    def reset(self):
        self.results_data = {}
        self.available_scenarios = []
        self.summary_table.clear()
        self.summary_table.setRowCount(0)
        self.details_table.clear()
        self.details_table.setRowCount(0)

        if MATPLOTLIB_AVAILABLE:
            self.cso_selector.clear()
            self.figure.clear()
            self.canvas.draw()

        self.status_label.setText("No results to display")
        self.status_label.setStyleSheet(
            "QLabel { color: gray; font-style: italic; }"
        )

    def set_available_scenarios(self, scenarios: list):
        """
        Update the list of available scenarios from the Scenarios tab.
        This allows detection of orphaned results.

        Args:
            scenarios: List of AnalysisScenario objects currently defined
        """
        self.available_scenarios = scenarios

    def cleanup_orphaned_results(self):
        """
        Find and remove results for scenarios that no longer exist.
        Shows user a dialog to confirm which results to delete.
        """
        if not self.results_data:
            QMessageBox.information(
                self,
                "No Results",
                "There are no results to clean up."
            )
            return

        # Get scenario names from available scenarios
        scenario_names = {
            scenario.scenario_name for scenario in self.available_scenarios}

        # Find orphaned results (results without matching scenarios)
        orphaned = []
        for result_name in self._iter_cso_results():
            name = result_name[0]  # Unpack tuple
            if name not in scenario_names:
                orphaned.append(name)

        if not orphaned:
            QMessageBox.information(
                self,
                "No Orphaned Results",
                "All results have corresponding scenarios.\n\n"
                "No cleanup needed!"
            )
            return

        # Show confirmation dialog with list
        orphaned_list = "\n".join(f"  • {name}" for name in orphaned)
        reply = QMessageBox.question(
            self,
            "Clean Up Orphaned Results",
            f"Found {len(orphaned)} result(s) without corresponding scenarios:\n\n"
            f"{orphaned_list}\n\n"
            f"These scenarios no longer exist in the Scenarios tab.\n\n"
            f"Delete these results?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Default to No for safety
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Delete orphaned results
            deleted_count = 0
            for name in orphaned:
                if name in self.results_data:
                    del self.results_data[name]
                    deleted_count += 1

                    # Also delete files from disk if output directory exists
                    self._delete_result_files(name)

            # Refresh display
            self.refresh_display()

            QMessageBox.information(
                self,
                "Cleanup Complete",
                f"Successfully deleted {deleted_count} orphaned result(s).\n\n"
                "All associated files (Parquet, JSON, and legacy CSV files) "
                "have been removed from disk to prevent them from being "
                "imported again when the project is reopened."
            )

    def _delete_result_files(self, scenario_name: str):
        """
        Delete Parquet, JSON, and legacy CSV files for a scenario from disk.

        Args:
            scenario_name: Name of the scenario whose files should be deleted
        """
        deleted_files = []
        try:
            # Try to find output directory from analysis tab
            parent = self.parent() or self.window()
            output_directory = None

            if parent and hasattr(parent, "analysis_tab"):
                analysis_tab = getattr(parent, "analysis_tab", None)
                if analysis_tab and hasattr(analysis_tab, "output_directory"):
                    output_directory = analysis_tab.output_directory

            if not output_directory or not os.path.exists(output_directory):
                return

            from pathlib import Path
            output_dir = Path(output_directory)

            # Modern Parquet and JSON files (from refactored engine)
            modern_files = [
                output_dir / f"{scenario_name}_timeseries.parquet",
                output_dir / f"{scenario_name}_spills.parquet",
                output_dir / f"{scenario_name}_summary.json",
            ]

            # Legacy CSV files and folders (from old engine)
            legacy_files = [
                output_dir / f"Summary_{scenario_name}.csv",
                output_dir / f"{scenario_name}_Outputs",  # Entire folder
            ]

            # Delete modern files
            for file_path in modern_files:
                if file_path.exists():
                    file_path.unlink()
                    deleted_files.append(str(file_path.name))

            # Delete legacy files/folders
            for file_path in legacy_files:
                if file_path.exists():
                    if file_path.is_dir():
                        # Delete entire legacy output directory
                        import shutil
                        shutil.rmtree(file_path)
                        deleted_files.append(f"{file_path.name}/ (folder)")
                    else:
                        file_path.unlink()
                        deleted_files.append(str(file_path.name))

            # Also check for any other files that start with scenario name
            for file_path in output_dir.glob(f"{scenario_name}_*"):
                if file_path.exists() and file_path.name not in [f.split(' ')[0] for f in deleted_files]:
                    if file_path.is_file():
                        file_path.unlink()
                        deleted_files.append(str(file_path.name))

            if deleted_files:
                # Log what was deleted (could be shown to user in a debug mode)
                # You could uncomment this line to log deletions:
                # print(f"Deleted files for {scenario_name}: {', '.join(deleted_files)}")
                pass

        except Exception:
            # Silently fail - files might not exist or be inaccessible
            pass
