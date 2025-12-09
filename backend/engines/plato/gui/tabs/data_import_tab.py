"""
Data Import Tab - Handle InfoWorks ICM data file import and validation
"""

import os
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem, QFileDialog,
    QGroupBox, QTextEdit, QComboBox, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

import pandas as pd
from datetime import datetime


class DataImportTab(QWidget):
    """Tab for importing and previewing InfoWorks ICM data files."""

    data_imported = pyqtSignal(dict)  # Emits imported data info

    def __init__(self, parent=None):
        super().__init__(parent)
        self.imported_data: Dict[str, Any] = {}
        self.flow_files: List[str] = []
        self.depth_files: List[str] = []
        self.date_format: Optional[str] = None  # User-configured date format
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # File selection group
        file_group = QGroupBox("Data Folder Selection")
        file_layout = QVBoxLayout()

        # Data folder selector
        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("Data Folder:"))
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText(
            "Select folder containing ICM export files...")
        folder_row.addWidget(self.folder_edit, 1)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_folder)
        folder_row.addWidget(self.browse_btn)

        file_layout.addLayout(folder_row)

        # File type selector
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("File Type:"))
        self.file_type_combo = QComboBox()
        self.file_type_combo.addItems(['csv'])  # , 'hyx'])
        self.file_type_combo.currentTextChanged.connect(
            self.on_file_type_changed)
        type_row.addWidget(self.file_type_combo)
        type_row.addStretch()
        file_layout.addLayout(type_row)

        # Load button
        load_btn_row = QHBoxLayout()
        self.load_btn = QPushButton("Load Data Files")
        self.load_btn.clicked.connect(self.load_data_files)
        self.load_btn.setEnabled(False)
        load_btn_row.addStretch()
        load_btn_row.addWidget(self.load_btn)
        file_layout.addLayout(load_btn_row)

        # Date format info row
        date_format_row = QHBoxLayout()
        date_format_row.addWidget(QLabel("Date Format:"))
        self.date_format_label = QLabel("Auto-detect")
        self.date_format_label.setStyleSheet(
            "QLabel { color: gray; font-style: italic; }")
        date_format_row.addWidget(self.date_format_label, 1)

        self.configure_date_btn = QPushButton("Configure...")
        self.configure_date_btn.clicked.connect(self.configure_date_format)
        self.configure_date_btn.setEnabled(False)
        date_format_row.addWidget(self.configure_date_btn)
        file_layout.addLayout(date_format_row)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Data preview group
        preview_group = QGroupBox("Data Preview")
        preview_layout = QVBoxLayout()

        # Summary info
        self.info_label = QLabel("No data loaded")
        self.info_label.setStyleSheet(
            "QLabel { color: gray; font-style: italic; }")
        preview_layout.addWidget(self.info_label)

        # Available links/nodes table
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(4)
        self.preview_table.setHorizontalHeaderLabels(
            ['Link/Node Name', 'Type', 'Data Points', 'Date Range'])
        # Set all columns to equal width
        header = self.preview_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.preview_table.setAlternatingRowColors(True)
        preview_layout.addWidget(self.preview_table)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group, 1)

        # Validation log
        log_group = QGroupBox("Import Log")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

    def browse_folder(self):
        """Open folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Data Folder",
            self.folder_edit.text() or os.path.expanduser("~")
        )

        if folder:
            self.folder_edit.setText(folder)
            self.load_btn.setEnabled(True)
            self.log(f"Folder selected: {folder}")

    def on_file_type_changed(self):
        """Handle file type selection change."""
        if self.folder_edit.text():
            self.load_btn.setEnabled(True)

    def _get_date_parser_kwargs(self) -> dict:
        """
        Get pandas date parsing kwargs based on configured date format.

        Returns:
            Dictionary of kwargs to pass to pd.read_csv for date parsing.
            Uses explicit format if configured, otherwise uses dayfirst=True.
        """
        if self.date_format:
            # Use explicit format for speed
            return {
                'parse_dates': ['Time'],
                'date_format': self.date_format
            }
        else:
            # Use dayfirst auto-detection (slower but flexible)
            return {
                'parse_dates': ['Time'],
                'dayfirst': True
            }

    def detect_date_format(self, csv_file: str, sample_size: int = 10) -> tuple[bool, Optional[str], List[str]]:
        """
        Sample the Time column and detect if pandas can parse dates automatically.

        Args:
            csv_file: Path to CSV file to sample
            sample_size: Number of rows to sample

        Returns:
            Tuple of (can_auto_parse, detected_format, sample_dates)
            - can_auto_parse: True if pandas can parse dates automatically
            - detected_format: Best-guess format string (or None if auto-detect works)
            - sample_dates: List of sample date strings from the file
        """
        try:
            # Read sample rows without parsing dates
            df_sample = pd.read_csv(csv_file, nrows=sample_size)

            if 'Time' not in df_sample.columns:
                return False, None, []

            # Get sample date strings
            sample_dates = df_sample['Time'].astype(str).tolist()

            # Try to parse with pandas auto-detection (dayfirst=True)
            # BUT: We want to detect if it's using the slow dateutil fallback
            # Check if pandas can infer a consistent format (fast path)
            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                try:
                    parsed = pd.to_datetime(
                        df_sample['Time'], dayfirst=True, errors='raise')

                    # Check if we got the "could not infer format" warning
                    # This means pandas is using slow dateutil fallback
                    has_infer_warning = any(
                        "Could not infer format" in str(warning.message)
                        for warning in w
                    )

                    if not has_infer_warning:
                        # Success - pandas can efficiently auto-parse
                        return True, None, sample_dates
                    # Otherwise fall through to try explicit formats

                except:
                    pass

            # Try common ICM export formats
            common_formats = [
                '%d/%m/%Y %H:%M:%S',  # 01/12/2023 14:30:00
                '%d-%m-%y %H:%M',      # 01-12-23 14:30
                '%d/%m/%Y %H:%M',      # 01/12/2023 14:30
                '%Y-%m-%d %H:%M:%S',   # 2023-12-01 14:30:00
                '%d/%m/%y %H:%M:%S',   # 01/12/23 14:30:00
                '%d-%m-%Y %H:%M:%S',   # 01-12-2023 14:30:00
            ]

            for fmt in common_formats:
                try:
                    parsed = pd.to_datetime(
                        df_sample['Time'], format=fmt, errors='raise')
                    # Success - found matching format
                    return False, fmt, sample_dates
                except:
                    continue

            # Could not auto-parse and no common format matched
            return False, None, sample_dates

        except Exception as e:
            self.log(f"Error detecting date format: {str(e)}")
            return False, None, []

    def configure_date_format(self):
        """Show dialog to configure date format for CSV parsing."""
        if not self.flow_files:
            QMessageBox.warning(
                self, "No Files", "Please load data files first.")
            return

        # Sample first flow file to get example dates
        first_file = self.flow_files[0]
        can_auto_parse, detected_format, sample_dates = self.detect_date_format(
            first_file)

        if not sample_dates:
            QMessageBox.warning(
                self, "No Dates", "Could not sample dates from file.")
            return

        # Show configuration dialog
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Configure Date Format")
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout(dialog)

        # Info label
        if can_auto_parse:
            info_text = "✓ Pandas can auto-detect these dates. You can specify a format for faster parsing:"
        elif detected_format:
            info_text = f"✓ Detected format: {detected_format}\nYou can change it if needed:"
        else:
            info_text = "⚠ Could not auto-detect date format. Please specify the format:"

        layout.addWidget(QLabel(info_text))

        # Sample dates display
        layout.addWidget(QLabel("\nSample dates from file:"))
        sample_list = QListWidget()
        for date_str in sample_dates[:5]:  # Show first 5
            sample_list.addItem(date_str)
        sample_list.setMaximumHeight(100)
        layout.addWidget(sample_list)

        # Format input
        layout.addWidget(
            QLabel("\nDate format string (leave empty for auto-detect):"))
        from PyQt6.QtWidgets import QLineEdit
        format_input = QLineEdit()
        if detected_format and not can_auto_parse:
            format_input.setText(detected_format)
        elif self.date_format:
            format_input.setText(self.date_format)
        format_input.setPlaceholderText("e.g., %d/%m/%Y %H:%M:%S")
        layout.addWidget(format_input)

        # Common format presets
        layout.addWidget(QLabel("\nCommon formats (click to use):"))
        from PyQt6.QtWidgets import QComboBox
        presets = QComboBox()
        presets.addItems([
            "Auto-detect (dayfirst=True)",
            "%d/%m/%Y %H:%M:%S",
            "%d-%m-%y %H:%M",
            "%d/%m/%Y %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%y %H:%M:%S",
            "%d-%m-%Y %H:%M:%S",
        ])
        presets.currentTextChanged.connect(
            lambda text: format_input.setText(
                "" if text.startswith("Auto") else text)
        )
        layout.addWidget(presets)

        # Help text
        help_text = QLabel(
            "\n<b>Format codes:</b><br>"
            "%d = day (01-31), %m = month (01-12), %Y = 4-digit year, %y = 2-digit year<br>"
            "%H = hour (00-23), %M = minute (00-59), %S = second (00-59)<br>"
            "<br>"
            "<b>Note:</b> Specifying format improves CSV reading speed significantly."
        )
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_format = format_input.text().strip() or None
            self.date_format = new_format

            # Update UI label
            if self.date_format:
                self.date_format_label.setText(self.date_format)
                self.date_format_label.setStyleSheet(
                    "QLabel { color: green; font-weight: bold; }")
                self.log(f"Date format configured: {self.date_format}")
            else:
                self.date_format_label.setText("Auto-detect (dayfirst=True)")
                self.date_format_label.setStyleSheet(
                    "QLabel { color: blue; font-weight: bold; }")
                self.log("Date format: Auto-detect mode enabled")

            # Ask if user wants to reload data with new format
            reply = QMessageBox.question(
                self,
                "Reload Data?",
                "Reload data files with the new date format?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.load_data_files()

    def load_data_files(self):
        """Load and parse data files from selected folder."""
        folder = self.folder_edit.text()
        file_type = self.file_type_combo.currentText()

        if not folder or not os.path.exists(folder):
            QMessageBox.warning(self, "Invalid Folder",
                                "Please select a valid data folder.")
            return

        self.log("=" * 60)
        self.log(f"Loading {file_type.upper()} files from: {folder}")

        try:
            # Find flow and depth files
            if file_type == 'csv':
                # Look for both standard (_Q, _D) and ICM default (_us_flow, _us_depth) naming
                self.flow_files = glob.glob(os.path.join(folder, "*_Q.csv"))
                self.flow_files.extend(
                    glob.glob(os.path.join(folder, "*_us_flow.csv")))

                self.depth_files = glob.glob(os.path.join(folder, "*_D.csv"))
                self.depth_files.extend(
                    glob.glob(os.path.join(folder, "*_us_depth.csv")))
            else:  # hyx
                self.flow_files = glob.glob(os.path.join(folder, "*.hyq"))
                self.depth_files = glob.glob(os.path.join(folder, "*.hyd"))

            self.log(f"Found {len(self.flow_files)} flow file(s)")
            self.log(f"Found {len(self.depth_files)} depth file(s)")

            if not self.flow_files:
                QMessageBox.warning(
                    self,
                    "No Files Found",
                    f"No {file_type.upper()} flow files found in the selected folder."
                )
                return

            # Auto-detect date format if not configured and we have CSV files
            if file_type == 'csv' and not self.date_format and self.flow_files:
                self.log("Detecting date format...")
                can_auto_parse, detected_format, sample_dates = self.detect_date_format(
                    self.flow_files[0])

                if can_auto_parse:
                    self.log(
                        "✓ Pandas can auto-detect date format (dayfirst=True)")
                    self.date_format_label.setText(
                        "Auto-detect (dayfirst=True)")
                    self.date_format_label.setStyleSheet(
                        "QLabel { color: blue; font-weight: bold; }")
                elif detected_format:
                    self.log(f"✓ Auto-detected date format: {detected_format}")
                    self.date_format = detected_format
                    self.date_format_label.setText(detected_format)
                    self.date_format_label.setStyleSheet(
                        "QLabel { color: green; font-weight: bold; }")
                else:
                    self.log(
                        "⚠ Could not auto-detect date format - manual configuration recommended")
                    self.date_format_label.setText(
                        "⚠ Unknown - Click Configure")
                    self.date_format_label.setStyleSheet(
                        "QLabel { color: orange; font-weight: bold; }")

                # Enable configure button
                self.configure_date_btn.setEnabled(True)

            # Parse and preview first file
            preview_metadata = self.parse_and_preview(file_type)

            # Store imported data info
            self.imported_data = {
                'data_folder': folder,
                'file_type': file_type,
                'flow_files': self.flow_files,
                'depth_files': self.depth_files,
                'has_depth_data': len(self.depth_files) > 0,
                'date_format': self.date_format  # Include date format for analysis_tab
            }

            if preview_metadata:
                self.imported_data.update(preview_metadata)

            # Emit signal that data is imported
            self.data_imported.emit(self.imported_data)

            self.log("✓ Data import completed successfully")

        except Exception as e:
            self.log(f"✗ Error loading files: {str(e)}")
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to load data files:\n{str(e)}"
            )

    def parse_and_preview(self, file_type: str) -> Dict[str, Any]:
        """Parse files, display preview, and return metadata."""
        self.preview_table.setRowCount(0)

        if file_type == 'csv':
            return self.preview_csv_files()
        return self.preview_hyx_files()

    def preview_csv_files(self) -> Dict[str, Any]:
        """Preview CSV format files and return metadata used elsewhere."""
        flow_metadata: Dict[str, Dict[str, Any]] = {}
        depth_metadata: Dict[str, Dict[str, Any]] = {}
        all_links = set()
        flow_min: Optional[pd.Timestamp] = None
        flow_max: Optional[pd.Timestamp] = None

        for flow_file in self.flow_files:
            try:
                # Read only column headers (zero data rows) - instant
                df_headers = pd.read_csv(flow_file, nrows=0)
                available_columns = [col for col in df_headers.columns
                                     if col not in {'Time', 'Seconds'}]

                # Read ONLY first and last rows for date range (fast)
                # Use configured date format for speed
                date_kwargs = self._get_date_parser_kwargs()
                df_first = pd.read_csv(
                    flow_file,
                    nrows=1,
                    usecols=['Time'],
                    **date_kwargs
                )

                # Read last line reliably using tail-like approach
                # Read backwards from end until we find a complete line
                with open(flow_file, 'rb') as f:
                    # Go to end of file
                    f.seek(0, 2)
                    file_size = f.tell()

                    # Read backwards in chunks to find last complete line
                    buffer = b''
                    chunk_size = 512
                    position = file_size

                    while position > 0:
                        # Move backwards by chunk_size (or remaining bytes)
                        chunk_to_read = min(chunk_size, position)
                        position -= chunk_to_read
                        f.seek(position)

                        # Read chunk and prepend to buffer
                        chunk = f.read(chunk_to_read)
                        buffer = chunk + buffer

                        # Try to decode and find newlines
                        try:
                            decoded = buffer.decode('utf-8')
                            # Use splitlines() to handle both \n and \r\n properly
                            lines = decoded.splitlines()

                            # We need at least 2 non-empty lines (header + at least 1 data line)
                            # Find all non-empty lines working backwards
                            non_empty_lines = [line.strip()
                                               for line in lines if line.strip()]

                            # If we have at least 2 lines, the last one is likely header, second-to-last is data
                            # But we need to be sure it's an actual data line with a timestamp
                            if len(non_empty_lines) >= 2:
                                # Try the last line first (might be data if no trailing header)
                                candidate = non_empty_lines[-1]
                                if ',' in candidate and not candidate.startswith('Time'):
                                    last_line = candidate
                                    break
                                # Otherwise use second-to-last (skip header)
                                elif len(non_empty_lines) >= 2:
                                    candidate = non_empty_lines[-2]
                                    if ',' in candidate:
                                        last_line = candidate
                                        break
                        except UnicodeDecodeError:
                            # Keep reading if we hit a decode error
                            continue
                    else:
                        # Fallback if we read entire file
                        lines = buffer.decode(
                            'utf-8', errors='ignore').splitlines()
                        non_empty_lines = [line.strip()
                                           for line in lines if line.strip()]
                        last_line = ''
                        if len(non_empty_lines) >= 1:
                            # Try last line first
                            candidate = non_empty_lines[-1]
                            if ',' in candidate and not candidate.startswith('Time'):
                                last_line = candidate
                            elif len(non_empty_lines) >= 2:
                                last_line = non_empty_lines[-2]

                # Parse the last timestamp from the last line
                if last_line and ',' in last_line:
                    # Split CSV line and get first column (Time)
                    last_time_str = last_line.split(',')[0].strip('"').strip()
                    try:
                        date_max = pd.to_datetime(last_time_str, dayfirst=True)
                    except Exception:
                        date_max = df_first['Time'].iloc[0]
                else:
                    date_max = df_first['Time'].iloc[0]

                date_min = df_first['Time'].iloc[0]

                # Estimate row count from file size
                row_count = file_size // 150  # ~150 bytes per CSV row

                flow_min = date_min if flow_min is None else min(
                    flow_min, date_min)
                flow_max = date_max if flow_max is None else max(
                    flow_max, date_max)

                for column in available_columns:
                    all_links.add(column)
                    if column not in flow_metadata:
                        flow_metadata[column] = {
                            'count': row_count,
                            'range': (date_min, date_max),
                            'file': Path(flow_file).name,
                            'files': [flow_file]
                        }
                    else:
                        # Update existing metadata
                        meta = flow_metadata[column]
                        meta['count'] += row_count
                        old_min, old_max = meta['range']
                        meta['range'] = (
                            min(old_min, date_min),
                            max(old_max, date_max)
                        )
                        meta['files'].append(flow_file)

            except Exception as e:
                self.log(
                    f"Warning: Could not preview {Path(flow_file).name}: {str(e)}")

        for depth_file in self.depth_files:
            try:
                # Read only column headers (instant)
                df_headers = pd.read_csv(depth_file, nrows=0)
                available_columns = [col for col in df_headers.columns
                                     if col not in {'Time', 'Seconds'}]

                # Read first row only
                # Use configured date format for speed
                date_kwargs = self._get_date_parser_kwargs()
                df_first = pd.read_csv(
                    depth_file,
                    nrows=1,
                    usecols=['Time'],
                    **date_kwargs
                )

                # Read last line reliably using tail-like approach
                with open(depth_file, 'rb') as f:
                    # Go to end of file
                    f.seek(0, 2)
                    file_size = f.tell()

                    # Read backwards in chunks to find last complete line
                    buffer = b''
                    chunk_size = 512
                    position = file_size

                    while position > 0:
                        # Move backwards by chunk_size (or remaining bytes)
                        chunk_to_read = min(chunk_size, position)
                        position -= chunk_to_read
                        f.seek(position)

                        # Read chunk and prepend to buffer
                        chunk = f.read(chunk_to_read)
                        buffer = chunk + buffer

                        # Try to decode and find newlines
                        try:
                            decoded = buffer.decode('utf-8')
                            # Use splitlines() to handle both \n and \r\n properly
                            lines = decoded.splitlines()

                            # We need at least 2 non-empty lines (header + at least 1 data line)
                            # Find all non-empty lines working backwards
                            non_empty_lines = [line.strip()
                                               for line in lines if line.strip()]

                            # If we have at least 2 lines, the last one is likely header, second-to-last is data
                            # But we need to be sure it's an actual data line with a timestamp
                            if len(non_empty_lines) >= 2:
                                # Try the last line first (might be data if no trailing header)
                                candidate = non_empty_lines[-1]
                                if ',' in candidate and not candidate.startswith('Time'):
                                    last_line = candidate
                                    break
                                # Otherwise use second-to-last (skip header)
                                elif len(non_empty_lines) >= 2:
                                    candidate = non_empty_lines[-2]
                                    if ',' in candidate:
                                        last_line = candidate
                                        break
                        except UnicodeDecodeError:
                            # Keep reading if we hit a decode error
                            continue
                    else:
                        # Fallback if we read entire file
                        lines = buffer.decode(
                            'utf-8', errors='ignore').splitlines()
                        non_empty_lines = [line.strip()
                                           for line in lines if line.strip()]
                        last_line = ''
                        if len(non_empty_lines) >= 1:
                            # Try last line first
                            candidate = non_empty_lines[-1]
                            if ',' in candidate and not candidate.startswith('Time'):
                                last_line = candidate
                            elif len(non_empty_lines) >= 2:
                                last_line = non_empty_lines[-2]

                # Parse last timestamp
                if last_line and ',' in last_line:
                    last_time_str = last_line.split(',')[0].strip('"').strip()
                    try:
                        date_max = pd.to_datetime(last_time_str, dayfirst=True)
                    except Exception:
                        date_max = df_first['Time'].iloc[0]
                else:
                    date_max = df_first['Time'].iloc[0]

                date_min = df_first['Time'].iloc[0]

                # Estimate row count
                row_count = file_size // 150

                for column in available_columns:
                    all_links.add(column)
                    if column not in depth_metadata:
                        depth_metadata[column] = {
                            'count': row_count,
                            'range': (date_min, date_max),
                            'file': Path(depth_file).name,
                            'files': [depth_file]
                        }
                    else:
                        # Update existing
                        meta = depth_metadata[column]
                        meta['count'] += row_count
                        old_min, old_max = meta['range']
                        meta['range'] = (
                            min(old_min, date_min),
                            max(old_max, date_max)
                        )
                        meta['files'].append(depth_file)

            except Exception as e:
                self.log(
                    f"Warning: Could not preview {Path(depth_file).name}: {str(e)}")

        combined_links = sorted(all_links)
        self.preview_table.setRowCount(len(combined_links))

        for index, link_name in enumerate(combined_links):
            flow_info = flow_metadata.get(link_name)
            depth_info = depth_metadata.get(link_name)
            has_flow = flow_info is not None
            has_depth = depth_info is not None

            if has_flow and has_depth:
                type_label = "Flow & Depth"
            elif has_flow:
                type_label = "Flow"
            else:
                type_label = "Depth"

            self.preview_table.setItem(index, 0, QTableWidgetItem(link_name))
            self.preview_table.setItem(index, 1, QTableWidgetItem(type_label))

            counts = []
            if flow_info:
                counts.append(f"Flow: {flow_info['count']:,}")
            if depth_info:
                counts.append(f"Depth: {depth_info['count']:,}")
            self.preview_table.setItem(
                index, 2, QTableWidgetItem('\n'.join(counts) or '-'))

            mismatch = False
            range_lines = []
            if flow_info:
                flow_min_date, flow_max_date = flow_info['range']
                range_lines.append(
                    f"Flow: {flow_min_date:%d/%m/%Y} to {flow_max_date:%d/%m/%Y}"
                )
            if depth_info:
                depth_min_date, depth_max_date = depth_info['range']
                range_lines.append(
                    f"Depth: {depth_min_date:%d/%m/%Y} to {depth_max_date:%d/%m/%Y}"
                )

            if has_flow and has_depth:
                flow_range = flow_info['range']
                depth_range = depth_info['range']
                mismatch = flow_range != depth_range
                if mismatch:
                    self.log(
                        f"Warning: Depth range for {link_name} does not match flow data "
                        f"({flow_range[0]:%d/%m/%Y} to {flow_range[1]:%d/%m/%Y} vs "
                        f"{depth_range[0]:%d/%m/%Y} to {depth_range[1]:%d/%m/%Y})"
                    )

            if mismatch:
                range_lines.append("⚠ Range mismatch")

            self.preview_table.setItem(
                index, 3, QTableWidgetItem('\n'.join(range_lines) or '-'))

        self.info_label.setText(
            f"Loaded {len(flow_metadata)} flow link(s), "
            f"{len(depth_metadata)} depth link(s) from {len(self.flow_files) + len(self.depth_files)} file(s)"
        )
        self.info_label.setStyleSheet(
            "QLabel { color: green; font-weight: bold; }")

        return {
            'available_links': sorted(flow_metadata.keys()),
            'all_links': combined_links,
            'data_start': flow_min,
            'data_end': flow_max,
            'flow_metadata': flow_metadata,
            'depth_metadata': depth_metadata,
        }

    def preview_hyx_files(self) -> Dict[str, Any]:
        """Preview HYX format files."""
        all_links = set()

        for flow_file in self.flow_files:
            try:
                with open(flow_file, 'r') as f:
                    lines = f.readlines()

                # Parse header info
                info_line = lines[2].split()
                try:
                    start_date = datetime.strptime(
                        f"{info_line[1]} {info_line[2]}", "%d-%m-%y %H:%M")
                    num_links = int(info_line[4])
                except:
                    start_date = datetime.strptime(
                        info_line[1], "%d%m%Y%H%M%S")
                    num_links = int(info_line[3])

                # Extract link names
                for i in range(3, 3 + num_links):
                    link_name = lines[i].strip().strip('"')
                    all_links.add(link_name)

            except Exception as e:
                self.log(
                    f"Warning: Could not preview {Path(flow_file).name}: {str(e)}")

        # Populate table
        self.preview_table.setRowCount(len(all_links))
        for idx, link in enumerate(sorted(all_links)):
            self.preview_table.setItem(idx, 0, QTableWidgetItem(link))
            self.preview_table.setItem(idx, 1, QTableWidgetItem("Flow"))
            self.preview_table.setItem(idx, 2, QTableWidgetItem("-"))
            self.preview_table.setItem(idx, 3, QTableWidgetItem("-"))

        self.info_label.setText(
            f"Found {len(all_links)} link(s) in {len(self.flow_files)} HYX file(s)"
        )
        self.info_label.setStyleSheet(
            "QLabel { color: green; font-weight: bold; }")

        return {
            'available_links': sorted(all_links),
            'all_links': sorted(all_links),
            'data_start': None,
            'data_end': None,
            'flow_metadata': {},
            'depth_metadata': {},
        }

    def log(self, message: str):
        """Add message to log window."""
        self.log_text.append(message)

    def get_state(self) -> Dict[str, Any]:
        """Get current tab state for saving."""
        return {
            'data_folder': self.folder_edit.text(),
            'file_type': self.file_type_combo.currentText(),
            'imported_data': self.imported_data,
            'date_format': self.date_format
        }

    def load_state(self, state: Dict[str, Any]):
        """Restore tab state from saved data."""
        if 'data_folder' in state:
            self.folder_edit.setText(state['data_folder'])
        if 'file_type' in state:
            self.file_type_combo.setCurrentText(state['file_type'])
        if 'date_format' in state:
            self.date_format = state['date_format']
            # Update UI label
            if self.date_format:
                self.date_format_label.setText(self.date_format)
                self.date_format_label.setStyleSheet(
                    "QLabel { color: green; font-weight: bold; }")
            else:
                self.date_format_label.setText("Auto-detect (dayfirst=True)")
                self.date_format_label.setStyleSheet(
                    "QLabel { color: blue; font-weight: bold; }")
        if 'imported_data' in state and state['imported_data']:
            self.imported_data = state['imported_data']
            self.load_data_files()

    def reset(self):
        """Reset tab to initial state."""
        self.folder_edit.clear()
        self.file_type_combo.setCurrentIndex(0)
        self.preview_table.setRowCount(0)
        self.log_text.clear()
        self.info_label.setText("No data loaded")
        self.info_label.setStyleSheet(
            "QLabel { color: gray; font-style: italic; }")
        self.imported_data = {}
        self.flow_files = []
        self.depth_files = []

        # Reset date format configuration
        self.date_format = None
        self.date_format_label.setText("Auto-detect")
        self.date_format_label.setStyleSheet(
            "QLabel { color: gray; font-style: italic; }")
        self.configure_date_btn.setEnabled(False)

    def _build_effective_link_series(self, link_name: str, flow_files: list) -> Optional[pd.DataFrame]:
        """
        Build effective link series by loading and summing component links.

        Args:
            link_name: Effective link name like "Effective(link1, link2, ...)"
            flow_files: List of flow data file paths

        Returns:
            DataFrame with 'Time' and link_name columns, or None if components not found
        """
        # Check if this is an effective link
        if not (link_name.startswith('Effective(') and link_name.endswith(')')):
            return None

        # Parse component links
        components_str = link_name[10:-1]  # Remove "Effective(" and ")"
        components = [c.strip() for c in components_str.split(',')]

        # Load component data from files
        component_dfs = []
        date_kwargs = self._get_date_parser_kwargs()

        for flow_file in flow_files:
            try:
                # Check which components are in this file
                available_cols = pd.read_csv(
                    flow_file, nrows=0).columns.tolist()
                needed_cols = ['Time'] + \
                    [c for c in components if c in available_cols]

                if len(needed_cols) > 1:  # Has Time + at least one component
                    df = pd.read_csv(
                        flow_file, usecols=needed_cols, **date_kwargs)
                    component_dfs.append(df)
            except Exception as e:
                continue

        if not component_dfs:
            return None

        # Merge all component data
        component_data = component_dfs[0]
        for df in component_dfs[1:]:
            component_data = component_data.merge(df, on='Time', how='outer')

        component_data.sort_values('Time', inplace=True)
        component_data.drop_duplicates(
            subset=['Time'], keep='first', inplace=True)

        # Verify all components exist
        missing = [c for c in components if c not in component_data.columns]
        if missing:
            self.log(
                f"Warning: Components for {link_name} not found: {missing}")
            return None

        # Build effective series by summing components
        result_df = pd.DataFrame({'Time': component_data['Time']})
        result_df[link_name] = component_data[components].sum(axis=1)

        return result_df

    def get_flow_statistics(self, link_name: str) -> Optional[Dict[str, Any]]:
        """
        Get flow statistics for a specific link by sampling data.
        Returns statistics without loading entire dataset.
        Supports effective links like "Effective(link1, link2, ...)".

        Args:
            link_name: Name of the flow link (or effective link)

        Returns:
            Dict with keys: min, max, mean, median, p95, p99, sample_data (time series)
            or None if link not found
        """
        if not self.imported_data or not self.flow_files:
            return None

        file_type = self.imported_data.get('file_type', 'csv')
        if file_type != 'csv':
            return None  # Only support CSV for now

        # Check if this is an effective link
        if link_name.startswith('Effective(') and link_name.endswith(')'):
            # Build effective link series
            df_full = self._build_effective_link_series(
                link_name, self.flow_files)
            if df_full is None:
                return None

            # Sample for performance
            sample_interval = 100
            df_sample = df_full.iloc[::sample_interval].copy()
        else:
            # Regular link - find ALL files containing it
            target_files = []
            for flow_file in self.flow_files:
                try:
                    df_headers = pd.read_csv(flow_file, nrows=0)
                    if link_name in df_headers.columns:
                        target_files.append(flow_file)
                except:
                    continue

            if not target_files:
                return None

            try:
                # Sample every Nth row for speed (e.g., every 100th row)
                sample_interval = 100

                # Read sampled data using configured date format for speed
                date_kwargs = self._get_date_parser_kwargs()
                
                dfs = []
                for f in target_files:
                    try:
                        df = pd.read_csv(
                            f,
                            usecols=['Time', link_name],
                            **date_kwargs
                        )
                        # Sample
                        dfs.append(df.iloc[::sample_interval])
                    except:
                        continue
                
                if not dfs:
                    return None
                    
                df_sample = pd.concat(dfs, ignore_index=True)
                df_sample.sort_values('Time', inplace=True)
            except Exception as e:
                self.log(f"Error loading data for {link_name}: {str(e)}")
                return None

        try:
            flow_values = df_sample[link_name].dropna()

            if len(flow_values) == 0:
                return None

            # Calculate actual timestep from sampled data
            if len(df_sample) > 1:
                timestep_seconds = (
                    df_sample['Time'].iloc[1] - df_sample['Time'].iloc[0]
                ).total_seconds() * sample_interval
            else:
                timestep_seconds = 300  # Fallback to 5 minutes

            # Compute statistics
            stats = {
                'min': float(flow_values.min()),
                'max': float(flow_values.max()),
                'mean': float(flow_values.mean()),
                'median': float(flow_values.median()),
                'p95': float(flow_values.quantile(0.95)),
                'p99': float(flow_values.quantile(0.99)),
                'sample_interval': sample_interval,
                'sample_count': len(flow_values),
                'timestep_seconds': timestep_seconds,
                # Return Series for plotting
                'sample_data': df_sample[[link_name]].copy(),
                'sample_times': df_sample['Time'].copy(),
            }

            return stats

        except Exception as e:
            self.log(f"Error computing statistics for {link_name}: {str(e)}")
            return None

    def get_flow_statistics_during_spills(self, continuation_link: str, overflow_link: str,
                                          sample_interval: int = 100) -> Optional[Dict[str, Any]]:
        """
        Get flow statistics by extracting individual spill events and creating a composite mean event.
        Supports effective links for both continuation and overflow links.

        This approach:
        1. Identifies individual spill events (continuous periods of overflow > 0)
        2. Extracts continuation flow for each event
        3. Aligns all events to common timebase (T=0 at start)
        4. Calculates mean continuation flow across all events at each timestep
        5. Returns statistics from this composite "average spill event"

        Args:
            continuation_link: Link name for continuation flow (can be effective)
            overflow_link: Link name for overflow/spill flow (can be effective)
            sample_interval: Not used (kept for API compatibility)

        Returns:
            Dictionary with statistics and composite mean event data, or None if failed
        """
        if not self.imported_data or not self.flow_files:
            return None

        file_type = self.imported_data.get('file_type', 'csv')
        if file_type != 'csv':
            return None  # Only support CSV for now

        try:
            # Check if either link is an effective link
            cont_is_effective = continuation_link.startswith(
                'Effective(') and continuation_link.endswith(')')
            overflow_is_effective = overflow_link.startswith(
                'Effective(') and overflow_link.endswith(')')

            # Step 1: Load data based on link types
            if cont_is_effective or overflow_is_effective:
                # Need to build effective links
                df = None

                # Build continuation link if effective
                if cont_is_effective:
                    df_cont = self._build_effective_link_series(
                        continuation_link, self.flow_files)
                    if df_cont is None:
                        self.log(
                            f"Warning: Could not build effective link '{continuation_link}'")
                        return self.get_flow_statistics(continuation_link)
                    df = df_cont

                # Build overflow link if effective
                if overflow_is_effective:
                    df_overflow = self._build_effective_link_series(
                        overflow_link, self.flow_files)
                    if df_overflow is None:
                        self.log(
                            f"Warning: Could not build effective link '{overflow_link}'")
                        return self.get_flow_statistics(continuation_link)

                    # Merge with continuation data
                    if df is None:
                        df = df_overflow
                    else:
                        df = df.merge(df_overflow, on='Time', how='outer')
                        df.sort_values('Time', inplace=True)

                # Load non-effective links from files
                date_kwargs = self._get_date_parser_kwargs()

                if not cont_is_effective:
                    # Load continuation link
                    for flow_file in self.flow_files:
                        try:
                            df_headers = pd.read_csv(flow_file, nrows=0)
                            if continuation_link in df_headers.columns:
                                df_temp = pd.read_csv(flow_file, usecols=[
                                                      'Time', continuation_link], **date_kwargs)
                                if df is None:
                                    df = df_temp
                                else:
                                    df = df.merge(
                                        df_temp, on='Time', how='outer')
                                    df.sort_values('Time', inplace=True)
                                break
                        except:
                            continue

                if not overflow_is_effective:
                    # Load overflow link
                    for flow_file in self.flow_files:
                        try:
                            df_headers = pd.read_csv(flow_file, nrows=0)
                            if overflow_link in df_headers.columns:
                                df_temp = pd.read_csv(flow_file, usecols=[
                                                      'Time', overflow_link], **date_kwargs)
                                if df is None:
                                    df = df_temp
                                else:
                                    df = df.merge(
                                        df_temp, on='Time', how='outer')
                                    df.sort_values('Time', inplace=True)
                                break
                        except:
                            continue

                if df is None:
                    self.log(f"Warning: Could not load data for links")
                    return self.get_flow_statistics(continuation_link)

            else:
                # Regular links - find file containing both
                data_file = None
                for flow_file in self.flow_files:
                    try:
                        df_headers = pd.read_csv(flow_file, nrows=0)
                        if overflow_link in df_headers.columns and continuation_link in df_headers.columns:
                            data_file = flow_file
                            break
                    except:
                        continue

                if not data_file:
                    # Try to find them separately (fallback for split files)
                    self.log(
                        f"Warning: Could not find both '{overflow_link}' and '{continuation_link}' in same file")
                    return self.get_flow_statistics(continuation_link)

                # Load both overflow and continuation data in one read
                # Use configured date format for speed
                date_kwargs = self._get_date_parser_kwargs()
                df = pd.read_csv(
                    data_file,
                    usecols=['Time', overflow_link, continuation_link],
                    **date_kwargs
                )

            # Calculate actual timestep from data
            if len(df) > 1:
                timestep_seconds = (
                    df['Time'].iloc[1] - df['Time'].iloc[0]
                ).total_seconds()
            else:
                timestep_seconds = 300  # Fallback to 5 minutes if data is insufficient

            # Step 2: Identify individual spill events
            spill_threshold = 0  # m³/s
            is_spilling = df[overflow_link] > spill_threshold

            # Find event boundaries (start/end of each continuous spill)
            # Use diff() to detect transitions
            spill_starts = is_spilling & ~is_spilling.shift(
                1, fill_value=False)
            spill_ends = ~is_spilling & is_spilling.shift(1, fill_value=False)

            start_indices = df.index[spill_starts].tolist()
            end_indices = df.index[spill_ends].tolist()

            # Handle edge cases
            if len(start_indices) == 0:
                self.log(
                    f"Warning: No spills detected for '{overflow_link}', using full continuation data")
                return self.get_flow_statistics(continuation_link)

            # If data starts mid-spill
            if is_spilling.iloc[0]:
                start_indices.insert(0, 0)

            # If data ends mid-spill
            if is_spilling.iloc[-1]:
                end_indices.append(len(df) - 1)

            # Ensure we have matching pairs
            num_events = min(len(start_indices), len(end_indices))
            start_indices = start_indices[:num_events]
            end_indices = end_indices[:num_events]

            self.log(f"Found {num_events} spill events for composite analysis")

            # Step 4: Extract each event and align to common timebase
            # Also calculate spill volumes and collect overflow data
            events_aligned = []  # List of DataFrames, each with [timestep, continuation_flow]
            spill_volumes = []  # List of spill volumes (m³) for each event

            for event_idx, (start_idx, end_idx) in enumerate(zip(start_indices, end_indices)):
                # Get time range for this event
                event_times = df.iloc[start_idx:end_idx + 1]['Time']

                # Extract continuation flow and overflow for this event
                event_data = df[
                    (df['Time'] >= event_times.iloc[0]) &
                    (df['Time'] <= event_times.iloc[-1])
                ][[continuation_link, overflow_link]].copy()

                if len(event_data) == 0:
                    continue

                # Calculate spill volume for this event (m³)
                # Volume = sum of overflow flow × timestep (convert seconds to appropriate unit)
                spill_volume = event_data[overflow_link].sum(
                ) * timestep_seconds
                spill_volumes.append(spill_volume)

                # Create relative timestep (T=0 at event start) for continuation flow
                event_continuation = event_data[[continuation_link]].copy()
                event_continuation['timestep'] = range(len(event_continuation))
                event_continuation['event_id'] = event_idx

                events_aligned.append(
                    event_continuation[['timestep', continuation_link, 'event_id']])

            if len(events_aligned) == 0:
                self.log(
                    "Warning: No valid events extracted, using full continuation data")
                return self.get_flow_statistics(continuation_link)

            # Step 5: Combine all events and calculate mean at each timestep
            all_events = pd.concat(events_aligned, ignore_index=True)

            # Calculate mean across events at each timestep
            # This only averages existing values (doesn't include zeros for ended events)
            composite_mean = all_events.groupby(
                'timestep')[continuation_link].mean()
            composite_std = all_events.groupby(
                'timestep')[continuation_link].std()
            composite_count = all_events.groupby(
                'timestep')[continuation_link].count()

            # Filter out timesteps with no data (count == 0)
            # This removes timesteps where no events are active
            valid_mask = composite_count > 0
            composite_mean = composite_mean[valid_mask]
            composite_std = composite_std[valid_mask]
            composite_count = composite_count[valid_mask]

            # Calculate average spill volume
            avg_spill_volume = sum(spill_volumes) / \
                len(spill_volumes) if spill_volumes else 0.0

            # Calculate average non-spill continuation flow
            # (flow when NOT spilling - this is the baseline flow)
            non_spill_mask = ~is_spilling
            non_spill_continuation = df.loc[non_spill_mask, continuation_link]
            avg_non_spill_flow = float(non_spill_continuation.mean()) if len(
                non_spill_continuation) > 0 else 0.0

            # Calculate maximum pump return rate estimate
            # This is the difference between peak spill continuation flow and baseline non-spill flow
            max_spill_continuation = float(composite_mean.max())
            max_pump_return_estimate = max_spill_continuation - avg_non_spill_flow

            # Calculate statistics from the composite mean event (not individual events)
            # This gives us statistics for the "average spill event"
            stats = {
                'min': float(composite_mean.min()),
                'max': float(composite_mean.max()),
                'mean': float(composite_mean.mean()),
                'median': float(composite_mean.median()),
                'p95': float(composite_mean.quantile(0.95)),
                'p99': float(composite_mean.quantile(0.99)),
                'sample_count': len(composite_mean),
                'spill_focused': True,
                'composite_event': True,
                'num_events': num_events,
                'total_timesteps': len(df),
                'spill_timesteps': len(composite_mean),
                'sample_interval': 1,
                'timestep_seconds': timestep_seconds,  # Actual timestep from data
                # New metrics for pump return analysis
                'avg_spill_volume_m3': avg_spill_volume,
                'avg_non_spill_continuation_flow': avg_non_spill_flow,
                'max_pump_return_estimate': max_pump_return_estimate,
                # Return composite mean as the sample data for plotting
                'sample_data': pd.DataFrame({
                    continuation_link: composite_mean.values,
                    'std': composite_std.values,
                    'count': composite_count.values
                }),
                # Relative timesteps
                'sample_times': pd.Series(composite_mean.index, name='timestep'),
            }

            self.log(
                f"Created composite mean event from {num_events} spills "
                f"(max length: {len(composite_mean)} timesteps)"
            )
            self.log(
                f"Average spill volume: {avg_spill_volume:.1f} m³, "
                f"Average non-spill flow: {avg_non_spill_flow:.4f} m³/s, "
                f"Max pump return estimate: {max_pump_return_estimate:.4f} m³/s"
            )

            return stats

        except Exception as e:
            self.log(
                f"Error computing composite spill event statistics: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            # Fallback to regular statistics
            return self.get_flow_statistics(continuation_link)
