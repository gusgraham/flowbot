"""
Analysis Tab - Execute storage modelling analysis with progress tracking
"""

import os
import pandas as pd
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QTextEdit, QProgressBar, QRadioButton, QButtonGroup,
    QMessageBox, QApplication
)
from PyQt6.QtCore import pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QTextCursor

from plato.refactored import (
    DataSourceInfo,
    EffectiveCSODefinition,
    EffectiveSeriesBuilderError,
    ScenarioSettings,
    build_effective_series_bulk,
)
from plato.refactored.models import CSOConfiguration
from plato.refactored.engine import StorageAnalyzer
from plato.gui.widgets.scenario_queue_widget import ScenarioQueueWidget

# Import legacy modules via isolated import module (prevents formatter reordering issues)
# from plato.gui.tabs._legacy_imports import Plato_SM, PLATO_SM_Catchment, PLATO_SM_WWTW


# class AnalysisWorker(QThread):
#     """Background worker thread for running analysis."""

#     progress_update = pyqtSignal(str)  # Log message
#     progress_value = pyqtSignal(int)   # Progress percentage
#     analysis_complete = pyqtSignal(dict)  # Results data
#     analysis_error = pyqtSignal(str)   # Error message

#     def __init__(
#         self,
#         config_data: list,
#         mode: str,
#         output_directory: str,
#         effective_csos: Optional[List[EffectiveCSODefinition]] = None,
#         data_source: Optional[DataSourceInfo] = None,
#         scenario_settings: Optional[ScenarioSettings] = None,
#         parent=None,
#     ):
#         super().__init__(parent)
#         self.config_data = config_data
#         self.mode = mode
#         self.output_directory = output_directory
#         self._is_cancelled = False
#         self.effective_csos = effective_csos or []
#         self.data_source = data_source
#         self.effective_outputs: Dict[str, str] = {}
#         self.scenario_settings = scenario_settings

#     def run(self):
#         """Execute the analysis."""
#         try:
#             self.progress_update.emit(f"Starting {self.mode} analysis...")
#             self.progress_value.emit(10)

#             if self.effective_csos and self.data_source:
#                 self._build_effective_series()

#             if self.mode == "Default Mode":
#                 results = self.run_default_mode()
#             elif self.mode == "Catchment Based Mode":
#                 results = self.run_catchment_mode()
#             elif self.mode == "WWTW Mode":
#                 results = self.run_wwtw_mode()
#             else:
#                 raise ValueError(f"Unknown analysis mode: {self.mode}")

#             if not self._is_cancelled:
#                 self.progress_value.emit(100)
#                 self.progress_update.emit("✓ Analysis completed successfully!")
#                 if self.effective_outputs:
#                     results.setdefault(
#                         "effective_csos", self.effective_outputs)
#                 if self.scenario_settings:
#                     results.setdefault("_scenario", self._scenario_as_dict())
#                 self.analysis_complete.emit(results)

#         except Exception as e:
#             self.progress_update.emit(f"✗ Error: {str(e)}")
#             self.analysis_error.emit(str(e))

#     def run_default_mode(self) -> dict:
#         """Run default mode analysis."""
#         import pandas as pd

#         results = {}

#         try:
#             # Convert config data to DataFrame (Storage_Modeller expects this format)
#             config_df = pd.DataFrame(self.config_data)

#             self.progress_update.emit("Starting storage modeller...")
#             self.progress_value.emit(20)

#             # Call the Storage_Modeller function (it handles the iteration internally)
#             # This function creates Overflow objects, runs analysis, and generates outputs
#             Plato_SM.Storage_Modeller(self.output_directory, config_df)

#             self.progress_value.emit(80)

#             # The Storage_Modeller function writes results to disk
#             # Collect summary information
#             for idx, cso_config in enumerate(self.config_data):
#                 if self._is_cancelled:
#                     break

#                 cso_name = cso_config.get('CSO Name', f'CSO_{idx + 1}')
#                 results[cso_name] = {
#                     'status': 'completed',
#                     'output_directory': os.path.join(
#                         self.output_directory,
#                         f"{cso_name}_Outputs_{cso_config.get('Run Suffix', '001')}"
#                     )
#                 }

#         except Exception as e:
#             self.progress_update.emit(f"  ✗ Error: {str(e)}")
#             results['error'] = {
#                 'status': 'error',
#                 'error': str(e)
#             }

#         return results

#     def _build_effective_series(self) -> None:
#         if not self.data_source:
#             return

#         effective_dir = Path(self.output_directory) / "EffectiveCSOs"
#         effective_dir.mkdir(exist_ok=True)

#         try:
#             self.progress_update.emit("Building effective CSO series...")
#             series_map = build_effective_series_bulk(
#                 self.effective_csos, self.data_source)
#             for name, series in series_map.items():
#                 csv_path = effective_dir / f"{name}_effective_series.csv"
#                 series.data.to_csv(csv_path, index=False,
#                                    date_format="%d/%m/%Y %H:%M:%S")
#                 self.effective_outputs[name] = str(csv_path)
#             self.progress_update.emit(
#                 f"Generated {len(series_map)} effective CSO series."
#             )
#         except EffectiveSeriesBuilderError as exc:
#             self.progress_update.emit(f"⚠ Effective CSO build failed: {exc}")

#     def _scenario_as_dict(self) -> Dict[str, Any]:
#         if not self.scenario_settings:
#             return {}

#         raw = asdict(self.scenario_settings)
#         for key in ("bathing_season_start", "bathing_season_end"):
#             value = raw.get(key)
#             if isinstance(value, date):
#                 raw[key] = value.strftime("%d/%m")
#         return raw

#     def run_catchment_mode(self) -> dict:
#         """Run catchment-based mode analysis."""
#         self.progress_update.emit("Catchment mode analysis starting...")
#         self.progress_value.emit(30)

#         # Get universal parameters from first config
#         if not self.config_data:
#             raise ValueError("No configuration data provided")

#         config = self.config_data[0]

#         self.progress_update.emit("Parsing data files...")
#         self.progress_value.emit(50)

#         # Parse data
#         flow_dfs, depth_dfs = PLATO_SM_Catchment.parseData(
#             config.get('File Type', 'csv'),
#             config.get('Data Folder', '')
#         )

#         self.progress_update.emit("Running catchment analysis...")
#         self.progress_value.emit(70)

#         # Run catchment analysis
#         # This would need proper implementation based on your catchment mode logic
#         results = {
#             'mode': 'catchment',
#             'status': 'completed',
#             'message': 'Catchment analysis completed'
#         }

#         return results

#     def run_wwtw_mode(self) -> dict:
#         """Run WWTW mode analysis."""
#         self.progress_update.emit("WWTW mode analysis starting...")
#         self.progress_value.emit(30)

#         if not self.config_data:
#             raise ValueError("No configuration data provided")

#         config = self.config_data[0]

#         self.progress_update.emit("Parsing WWTW data...")
#         self.progress_value.emit(50)

#         # Parse WWTW-specific data
#         spill_links = config.get('Spill Links', '').split(',')
#         fft_link = config.get('FFT Link', '')
#         pump_links = config.get('Pump Links', '').split(',')

#         parsed_data = PLATO_SM_WWTW.parseData(
#             config.get('Data Folder', ''),
#             config.get('File Type', 'csv'),
#             spill_links,
#             fft_link,
#             pump_links,
#             config.get('Start Date (dd/mm/yy hh:mm:ss)', ''),
#             config.get('End Date (dd/mm/yy hh:mm:ss)', '')
#         )

#         self.progress_update.emit("Running WWTW analysis...")
#         self.progress_value.emit(70)

#         results = {
#             'mode': 'wwtw',
#             'status': 'completed',
#             'data': parsed_data
#         }

#         return results

#     def cancel(self):
#         """Cancel the analysis."""
#         self._is_cancelled = True
#         self.progress_update.emit("Cancelling analysis...")


# Note: RefactoredAnalysisWorker removed - refactored engine runs directly in main thread
# for easier debugging. Will add back threading later when stable.


class AnalysisTab(QWidget):
    """Tab for running and monitoring analysis."""

    CONFIG_DATETIME_FORMATS = (
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%y %H:%M:%S",
        "%d/%m/%y %H:%M",
    )
    OUTPUT_DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"

    analysis_completed = pyqtSignal(dict)  # Emits results

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_data: list = []
        self.scenarios: list = []  # Store AnalysisScenario objects
        self.cso_assets: list = []  # Store CSOAsset objects
        self.configurations: list = []  # Store AnalysisConfiguration objects
        self.catchments: list = []  # Store Catchment objects
        self.imported_data: dict = {}
        self.effective_csos: List[EffectiveCSODefinition] = []
        self.worker_thread: Optional[AnalysisWorker] = None
        self.analysis_results: Dict[str, Any] = {}
        self.output_directory: str = ""
        self.init_ui()

    def _get_date_parser_kwargs(self) -> dict:
        """
        Get pandas date parsing kwargs based on configured date format from imported_data.

        Returns:
            Dictionary of kwargs to pass to pd.read_csv for date parsing.
            Uses explicit format if configured, otherwise uses dayfirst=True.
        """
        date_format = self.imported_data.get('date_format')
        if date_format:
            # Use explicit format for speed
            return {
                'parse_dates': ['Time'],
                'date_format': date_format
            }
        else:
            # Use dayfirst auto-detection (slower but flexible)
            return {
                'parse_dates': ['Time'],
                'dayfirst': True
            }

    def _build_effective_links_for_catchment(self, overflow_df, flow_data, data_folder, date_kwargs):
        """
        Build effective link series for catchment analysis.

        Scans all CSO continuation links for "Effective(...)" patterns and builds
        combined series by summing component flows.

        Args:
            overflow_df: DataFrame with CSO configuration including 'Continuation_Link' column
            flow_data: Existing flow data (to check which columns are already available)
            data_folder: Path to data folder containing CSVs
            date_kwargs: Date parsing kwargs for pd.read_csv

        Returns:
            DataFrame with Time column and effective link columns, or None if no effective links found
        """
        import glob
        import os

        # Find all effective links in the overflow configuration
        effective_links_to_build = {}

        for _, row in overflow_df.iterrows():
            cont_link = row.get('Continuation_Link', '')

            # Check if this is an effective link definition
            if cont_link.startswith('Effective(') and cont_link.endswith(')'):
                # Check if we already have this column in flow_data
                if cont_link not in flow_data.columns:
                    # Parse component links
                    # Remove "Effective(" and ")"
                    components_str = cont_link[10:-1]
                    components = [c.strip() for c in components_str.split(',')]
                    effective_links_to_build[cont_link] = components

        if not effective_links_to_build:
            return None

        # Collect all component links we need
        all_components = set()
        for components in effective_links_to_build.values():
            all_components.update(components)

        self.log(
            f"Found {len(effective_links_to_build)} effective link(s) to build from {len(all_components)} component(s)")

        # Load flow data for all component links
        flow_files = list(sorted(data_folder.glob('*_Q.csv')))
        flow_files.extend(sorted(data_folder.glob('*_us_flow.csv')))

        component_dfs = []
        for f in flow_files:
            # Check which components are in this file
            import pandas as pd
            available_cols = pd.read_csv(f, nrows=0).columns.tolist()
            needed_cols = ['Time'] + \
                [c for c in all_components if c in available_cols]

            if len(needed_cols) > 1:  # Has Time + at least one component
                df = pd.read_csv(f, usecols=needed_cols, **date_kwargs)
                component_dfs.append(df)

        if not component_dfs:
            raise ValueError(
                f"Component links not found in data: {all_components}")

        # Merge all component data
        component_data = component_dfs[0]
        for df in component_dfs[1:]:
            component_data = component_data.merge(df, on='Time', how='outer')

        component_data.sort_values('Time', inplace=True)
        component_data.drop_duplicates(
            subset=['Time'], keep='first', inplace=True)

        # Build effective series
        effective_df = pd.DataFrame({'Time': component_data['Time']})

        for effective_name, components in effective_links_to_build.items():
            # Verify all components exist
            missing = [c for c in components if c not in component_data.columns]
            if missing:
                raise ValueError(
                    f"Components for {effective_name} not found in data: {missing}")

            # Sum component flows
            effective_df[effective_name] = component_data[components].sum(
                axis=1)
            self.log(
                f"  Built {effective_name} from {len(components)} component(s)")

        return effective_df

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Info label
        info_label = QLabel(
            "Run storage modelling analysis on your defined scenarios. "
            "Analysis mode and model are defined in the Analysis Configuration."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "QLabel { color: #666; font-style: italic; margin: 5px; }")
        layout.addWidget(info_label)

        # Engine selection group
        engine_group = QGroupBox("Analysis Engine")
        engine_layout = QHBoxLayout()

        self.engine_button_group = QButtonGroup()

        self.legacy_engine_radio = QRadioButton("Legacy Engine")
        self.legacy_engine_radio.setToolTip(
            "Original proven implementation - stable and tested")
        self.engine_button_group.addButton(self.legacy_engine_radio)
        engine_layout.addWidget(self.legacy_engine_radio)

        self.refactored_engine_radio = QRadioButton("Refactored Engine (Beta)")
        self.refactored_engine_radio.setToolTip(
            "Modern reimplementation - Default Mode, Catchment Based Mode, and WWTW Mode.\n"
            "⚠ Runs in main thread (blocks UI) for easier debugging.")
        self.refactored_engine_radio.setChecked(True)
        self.refactored_engine_radio.setEnabled(True)
        self.engine_button_group.addButton(self.refactored_engine_radio)
        engine_layout.addWidget(self.refactored_engine_radio)

        engine_layout.addStretch()
        engine_group.setLayout(engine_layout)
        # Hide the engine selection - always use refactored engine
        engine_group.setVisible(False)
        layout.addWidget(engine_group)

        # Scenario selection queue
        queue_group = QGroupBox("Scenario Queue")
        queue_layout = QVBoxLayout()

        queue_info = QLabel(
            "Select which scenarios to run or re-run. "
            "Scenarios are automatically selected if they haven't been analyzed yet."
        )
        queue_info.setWordWrap(True)
        queue_info.setStyleSheet(
            "QLabel { color: #666; font-style: italic; margin: 5px; }")
        queue_layout.addWidget(queue_info)

        self.scenario_queue = ScenarioQueueWidget()
        self.scenario_queue.selection_changed.connect(
            self._on_queue_selection_changed)
        queue_layout.addWidget(self.scenario_queue)

        queue_group.setLayout(queue_layout)
        layout.addWidget(queue_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self.start_btn = QPushButton("▶ Start Analysis")
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet(
            "QPushButton { font-weight: bold; min-height: 30px; }")
        self.start_btn.clicked.connect(self.start_analysis)
        button_layout.addWidget(self.start_btn)

        self.cancel_btn = QPushButton("⏹ Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_analysis)
        button_layout.addWidget(self.cancel_btn)

        button_layout.addStretch()

        self.head_discharge_btn = QPushButton("📊 Head-Discharge Analysis")
        self.head_discharge_btn.setEnabled(False)
        self.head_discharge_btn.setToolTip(
            "Reverse-engineer head vs discharge relationship from final spill results")
        self.head_discharge_btn.clicked.connect(self._analyze_head_discharge)
        button_layout.addWidget(self.head_discharge_btn)

        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.clear_log)
        button_layout.addWidget(self.clear_log_btn)

        layout.addLayout(button_layout)

        # Progress group
        progress_group = QGroupBox("Analysis Progress")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready to run analysis")
        self.status_label.setStyleSheet(
            "QLabel { color: gray; font-style: italic; }")
        progress_layout.addWidget(self.status_label)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Log viewer
        log_group = QGroupBox("Analysis Log")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group, 1)

    def on_config_ready(self, is_valid: bool):
        """Enable/disable start button based on configuration validation."""
        self.start_btn.setEnabled(is_valid)
        if is_valid:
            self.status_label.setText("Configuration validated - ready to run")
            self.status_label.setStyleSheet("QLabel { color: green; }")
        else:
            self.status_label.setText("Configuration has errors - cannot run")
            self.status_label.setStyleSheet("QLabel { color: red; }")

    def set_scenarios(self, scenarios: list, assets: list, configurations: list, catchments: list = None):
        """Receive scenarios from the scenarios tab and update button state."""
        self.scenarios = scenarios
        self.cso_assets = assets
        self.configurations = configurations
        self.catchments = catchments or []

        # Clean up orphaned result files when scenarios change
        if self.output_directory:
            self._cleanup_orphaned_results()

        # Update the scenario queue widget
        self.scenario_queue.set_scenarios(scenarios, self.output_directory)

        # Enable start button if we have valid scenarios
        has_scenarios = len(scenarios) > 0
        self.start_btn.setEnabled(has_scenarios)

        if has_scenarios:
            self.status_label.setText(
                f"Ready to analyze {len(scenarios)} scenario(s)")
            self.status_label.setStyleSheet("QLabel { color: green; }")
        else:
            self.status_label.setText(
                "No scenarios defined - please create scenarios first")
            self.status_label.setStyleSheet("QLabel { color: orange; }")

    def _on_queue_selection_changed(self, selected_count: int, analyzed_count: int, new_count: int):
        """Handle changes in scenario queue selection."""
        # Update start button text to show how many will be run
        if selected_count > 0:
            self.start_btn.setText(
                f"▶ Start Analysis ({selected_count} scenarios)")
            self.start_btn.setEnabled(True)
        else:
            self.start_btn.setText("▶ Start Analysis")
            self.start_btn.setEnabled(len(self.scenarios) > 0)

    def start_analysis(self):
        """Start the analysis process."""
        # Get selected scenarios from queue
        selected_scenarios = self.scenario_queue.get_selected_scenarios()

        if not selected_scenarios:
            QMessageBox.warning(
                self,
                "No Scenarios Selected",
                "Please select at least one scenario to analyze.\n\n"
                "Use the checkboxes in the Scenario Queue to select scenarios."
            )
            return

        # Check if project is saved (required for output directory)
        main_window_widget = self.window()
        if not main_window_widget.current_project_file:
            reply = QMessageBox.question(
                self,
                "Save Project First",
                "The project must be saved before running analysis so outputs "
                "can be stored in a permanent location.\n\n"
                "Outputs will be saved to: {project_name}_Outputs folder\n\n"
                "Would you like to save the project now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                # Trigger save dialog
                if main_window_widget.save_project():
                    # Project saved successfully - continue
                    pass
                else:
                    # User cancelled save - abort analysis
                    return
            else:
                # User declined to save - abort analysis
                return

        # Get imported data from data import tab
        data_import_tab = getattr(main_window_widget, 'data_import_tab', None)
        if data_import_tab is not None:
            self.imported_data = data_import_tab.imported_data

        # Build config_data from SELECTED scenarios only
        if not selected_scenarios:
            QMessageBox.warning(
                self,
                "No Scenarios Selected",
                "Please select at least one scenario to analyze."
            )
            return

        # Convert selected scenarios to legacy config format
        self.config_data = []
        for scenario in selected_scenarios:
            # Find the configuration
            config = next(
                (c for c in self.configurations if c.name == scenario.config_name), None)

            if not config:
                QMessageBox.warning(
                    self,
                    "Configuration Not Found",
                    f"Configuration '{scenario.config_name}' not found for scenario '{scenario.scenario_name}'."
                )
                return

            # Handle catchment scenarios vs WwTW scenarios vs regular CSO scenarios
            if scenario.is_catchment_scenario():
                # Catchment scenario - expand into multiple CSO runs
                # Find the catchment
                catchment = next(
                    (c for c in self.catchments if c.name == scenario.catchment_name), None)
                if not catchment:
                    QMessageBox.warning(
                        self,
                        "Catchment Not Found",
                        f"Catchment '{scenario.catchment_name}' not found for scenario '{scenario.scenario_name}'."
                    )
                    return

                # Get CSO names from catchment
                cso_names = catchment.get_cso_names()

                # Create mapping from asset names to overflow link names (for engine compatibility)
                # The engine uses overflow link names as keys, but catchment relationships use asset names
                asset_name_to_link_name = {}
                for name in cso_names:
                    asset = next(
                        (a for a in self.cso_assets if a.name == name), None)
                    if asset and asset.overflow_links:
                        asset_name_to_link_name[asset.name] = asset.overflow_links[0]

                # Create a legacy config for each CSO in the catchment
                for cso_name in cso_names:
                    # Find the asset
                    asset = next(
                        (a for a in self.cso_assets if a.name == cso_name), None)
                    if not asset:
                        QMessageBox.warning(
                            self,
                            "Asset Not Found",
                            f"CSO Asset '{cso_name}' not found in catchment '{scenario.catchment_name}' for scenario '{scenario.scenario_name}'."
                        )
                        return

                    # Get per-CSO intervention parameters from cso_interventions dict
                    if scenario.cso_interventions and cso_name in scenario.cso_interventions:
                        interventions = scenario.cso_interventions[cso_name]

                        # Create a temporary scenario with this CSO's specific parameters
                        from plato.refactored import AnalysisScenario
                        cso_scenario = AnalysisScenario(
                            cso_name=cso_name,
                            config_name=scenario.config_name,
                            scenario_name=f"{scenario.scenario_name}_{cso_name}",
                            pff_increase=interventions.get(
                                'pff_increase', 0.0),
                            pumping_mode=interventions.get(
                                'pumping_mode', 'Fixed'),
                            pump_rate=interventions.get('pump_rate', 0.0),
                            time_delay=interventions.get('time_delay', 0),
                            flow_return_threshold=interventions.get(
                                'flow_return_threshold', 0.0),
                            depth_return_threshold=interventions.get(
                                'depth_return_threshold', 0.0),
                            tank_volume=interventions.get('tank_volume'),
                        )
                        legacy_config = cso_scenario.to_legacy_format(
                            asset, config)
                    else:
                        # No specific interventions for this CSO, use defaults from parent
                        from plato.refactored import AnalysisScenario
                        cso_scenario = AnalysisScenario(
                            cso_name=cso_name,
                            config_name=scenario.config_name,
                            scenario_name=f"{scenario.scenario_name}_{cso_name}",
                            pff_increase=scenario.pff_increase,
                            pumping_mode=scenario.pumping_mode,
                            pump_rate=scenario.pump_rate,
                            time_delay=scenario.time_delay,
                            flow_return_threshold=scenario.flow_return_threshold,
                            depth_return_threshold=scenario.depth_return_threshold,
                            tank_volume=scenario.tank_volume,
                        )
                        legacy_config = cso_scenario.to_legacy_format(
                            asset, config)

                    # Format dates
                    if isinstance(legacy_config.get('Start Date (dd/mm/yy hh:mm:ss)'), datetime):
                        legacy_config['Start Date (dd/mm/yy hh:mm:ss)'] = legacy_config['Start Date (dd/mm/yy hh:mm:ss)'].strftime(
                            self.OUTPUT_DATETIME_FORMAT)
                    if isinstance(legacy_config.get('End Date (dd/mm/yy hh:mm:ss)'), datetime):
                        legacy_config['End Date (dd/mm/yy hh:mm:ss)'] = legacy_config['End Date (dd/mm/yy hh:mm:ss)'].strftime(
                            self.OUTPUT_DATETIME_FORMAT)
                    if isinstance(legacy_config.get('Bathing Season Start (dd/mm)'), date):
                        legacy_config['Bathing Season Start (dd/mm)'] = legacy_config['Bathing Season Start (dd/mm)'].strftime(
                            '%d/%m')
                    if isinstance(legacy_config.get('Bathing Season End (dd/mm)'), date):
                        legacy_config['Bathing Season End (dd/mm)'] = legacy_config['Bathing Season End (dd/mm)'].strftime(
                            '%d/%m')

                    # Add catchment relationship data for this CSO
                    # Find relationship where this CSO is the source
                    relationships_from_this_cso = [
                        rel for rel in catchment.cso_relationships
                        if rel.cso_name == cso_name
                    ]

                    if relationships_from_this_cso:
                        # This CSO has downstream connection(s)
                        # For now, take the first one (assuming single downstream)
                        rel = relationships_from_this_cso[0]
                        # Convert asset names to overflow link names for engine compatibility
                        downstream_link = asset_name_to_link_name.get(
                            rel.downstream_cso, rel.downstream_cso)
                        legacy_config['Downstream CSO'] = downstream_link
                        legacy_config['Distance (m)'] = rel.distance_to_downstream
                        legacy_config['Average Velocity (m/s)'] = rel.average_velocity
                        legacy_config['Maximum Pass Forward Flow (m3/s)'] = rel.max_pff
                    else:
                        # No downstream - this is an outlet CSO
                        legacy_config['Downstream CSO'] = None
                        legacy_config['Distance (m)'] = 0.0
                        legacy_config['Average Velocity (m/s)'] = 0.0
                        legacy_config['Maximum Pass Forward Flow (m3/s)'] = 0.0

                    # Find all upstream CSOs (relationships where this CSO is downstream)
                    # Convert asset names to overflow link names for engine compatibility
                    upstream_csos = [
                        asset_name_to_link_name.get(rel.cso_name, rel.cso_name)
                        for rel in catchment.cso_relationships
                        if rel.downstream_cso == cso_name
                    ]
                    legacy_config['Upstream CSOs'] = upstream_csos if upstream_csos else [
                    ]

                    # Track the original scenario name for grouping purposes
                    # This avoids issues when scenario names contain underscores
                    legacy_config['_original_scenario_name'] = scenario.scenario_name

                    self.config_data.append(legacy_config)

            elif scenario.is_wwtw_scenario():
                # WwTW scenario - needs different handling
                # Find the WwTW asset from the main window's WwTW assets tab
                main_window = self.window()
                wwtw_assets_tab = getattr(main_window, 'wwtw_assets_tab', None)

                if not wwtw_assets_tab:
                    QMessageBox.warning(
                        self,
                        "WwTW Assets Not Available",
                        f"Cannot find WwTW assets tab for scenario '{scenario.scenario_name}'."
                    )
                    return

                wwtw_assets = wwtw_assets_tab.get_assets()
                wwtw_asset = next(
                    (a for a in wwtw_assets if a.name == scenario.wwtw_name), None)

                if not wwtw_asset:
                    QMessageBox.warning(
                        self,
                        "WwTW Asset Not Found",
                        f"WwTW Asset '{scenario.wwtw_name}' not found for scenario '{scenario.scenario_name}'."
                    )
                    return

                # # DEBUG: Log the scenario object state
                # self.log(f"  DEBUG WwTW Scenario '{scenario.scenario_name}':")
                # self.log(
                #     f"    scenario.tank_volume = {scenario.tank_volume} (type: {type(scenario.tank_volume).__name__})")
                # self.log(f"    scenario.wwtw_name = {scenario.wwtw_name}")
                # self.log(
                #     f"    scenario.fft_augmentation = {scenario.fft_augmentation}")
                # self.log(
                #     f"    scenario.wwtw_pump_rate = {scenario.wwtw_pump_rate}")

                # Build legacy config manually for WwTW (can't use to_legacy_format with WWTWAsset)
                legacy_config = {
                    'WwTW Name': wwtw_asset.name,
                    'Scenario Name': scenario.scenario_name,
                    'Run Suffix': scenario.scenario_name,  # Use scenario name as run suffix
                    'Analysis Mode': config.mode,
                    'Model Identifier': config.model,
                    'Start Date (dd/mm/yy hh:mm:ss)': config.start_date.strftime(self.OUTPUT_DATETIME_FORMAT),
                    'End Date (dd/mm/yy hh:mm:ss)': config.end_date.strftime(self.OUTPUT_DATETIME_FORMAT),
                    'Spill Target (Entire Period)': config.spill_target,
                    'Spill Target (Bathing Seasons)': config.spill_target_bathing or -1,
                    'Bathing Season Start (dd/mm)': config.bathing_season_start,
                    'Bathing Season End (dd/mm)': config.bathing_season_end,
                    'Spill Flow Threshold (m3/s)': config.spill_flow_threshold,
                    'Spill Volume Threshold (m3)': config.spill_volume_threshold,

                    # WwTW-specific fields
                    'Spill Links': ','.join(wwtw_asset.spill_links),
                    'FFT Link': wwtw_asset.fft_link,
                    'Pump Links': ','.join(wwtw_asset.pump_links) if wwtw_asset.pump_links else '',

                    # WwTW intervention parameters from scenario
                    'Tank Volume (m3)': scenario.tank_volume if scenario.tank_volume is not None else 0.0,
                    'Time Delay (hours)': scenario.wwtw_time_delay_hours or 0,
                    'FFT Augmentation (m3/s)': scenario.fft_augmentation or 0.0,
                    'WwTW Pump Rate (m3/s)': scenario.wwtw_pump_rate or 0.0,
                    'WwTW Pump On Threshold (m3/s)': scenario.wwtw_pump_on_threshold or 0.0,
                    'WwTW Pump Off Threshold (m3/s)': scenario.wwtw_pump_off_threshold or 0.0,
                }

                # DEBUG: Log what we put in the config
                self.log(
                    f"    legacy_config['Tank Volume (m3)'] = {legacy_config['Tank Volume (m3)']}")

                # Track the original scenario name
                legacy_config['_original_scenario_name'] = scenario.scenario_name

                self.config_data.append(legacy_config)

            else:
                # Regular CSO scenario
                # Find the asset
                asset = next(
                    (a for a in self.cso_assets if a.name == scenario.cso_name), None)

                if not asset:
                    QMessageBox.warning(
                        self,
                        "Asset Not Found",
                        f"CSO Asset '{scenario.cso_name}' not found for scenario '{scenario.scenario_name}'."
                    )
                    return

                # Convert to legacy format
                legacy_config = scenario.to_legacy_format(asset, config)

                # Ensure dates are formatted as strings (to_legacy_format returns datetime objects)
                if isinstance(legacy_config.get('Start Date (dd/mm/yy hh:mm:ss)'), datetime):
                    legacy_config['Start Date (dd/mm/yy hh:mm:ss)'] = legacy_config['Start Date (dd/mm/yy hh:mm:ss)'].strftime(
                        self.OUTPUT_DATETIME_FORMAT)
                if isinstance(legacy_config.get('End Date (dd/mm/yy hh:mm:ss)'), datetime):
                    legacy_config['End Date (dd/mm/yy hh:mm:ss)'] = legacy_config['End Date (dd/mm/yy hh:mm:ss)'].strftime(
                        self.OUTPUT_DATETIME_FORMAT)

                # Format bathing season dates if they're date objects
                if isinstance(legacy_config.get('Bathing Season Start (dd/mm)'), date):
                    legacy_config['Bathing Season Start (dd/mm)'] = legacy_config['Bathing Season Start (dd/mm)'].strftime(
                        '%d/%m')
                if isinstance(legacy_config.get('Bathing Season End (dd/mm)'), date):
                    legacy_config['Bathing Season End (dd/mm)'] = legacy_config['Bathing Season End (dd/mm)'].strftime(
                        '%d/%m')

                # Track the original scenario name
                legacy_config['_original_scenario_name'] = scenario.scenario_name

                self.config_data.append(legacy_config)

        # For now, effective_csos remain empty (this is a legacy feature)
        self.effective_csos = []

        if not self.imported_data or not self.imported_data.get('data_folder'):
            QMessageBox.warning(
                self,
                "No Data Imported",
                "Please import data on the Data Import tab before running analysis."
            )
            return

        normalized_configs, date_errors = self._normalize_date_ranges(
            self.config_data)
        if date_errors:
            message = "\n".join(date_errors[:10])
            if len(date_errors) > 10:
                message += f"\n\n... and {len(date_errors) - 10} more"
            QMessageBox.warning(
                self,
                "Date Validation Errors",
                f"Configuration contains invalid start/end dates:\n\n{message}"
            )
            return

        self.config_data = normalized_configs

        # Create output directory based on project file location
        main_window = self.window()
        project_dir = os.path.dirname(main_window.current_project_file)
        project_name = os.path.splitext(
            os.path.basename(main_window.current_project_file))[0]
        self.output_directory = os.path.join(
            project_dir, f'{project_name}_Outputs')
        os.makedirs(self.output_directory, exist_ok=True)

        self.log(f"Output directory: {self.output_directory}")

        # Get mode from first config in the data (already set by to_legacy_format)
        if not self.config_data:
            QMessageBox.warning(
                self,
                "No Configuration",
                "No configuration data available."
            )
            return

        mode = self.config_data[0].get('Analysis Mode', 'Default Mode')

        # Enrich configuration data with runtime values
        enriched_config_data = []
        timestep = self._get_timestep_from_data()
        scenario_settings = ScenarioSettings()
        scenario_settings = scenario_settings.copy_with_overrides(
            analysis_mode=self._mode_identifier(mode),
            timestep_seconds=timestep,
        )

        for cso_config in self.config_data:
            enriched_config = cso_config.copy()

            # Get model identifier for THIS scenario (each can have a different model)
            model_identifier = int(enriched_config.get('Model Identifier', 1))

            # Add runtime fields (don't overwrite Model Identifier - it's already set correctly)
            enriched_config['Data Folder'] = self.imported_data.get(
                'data_folder', '')
            enriched_config['File Type'] = self.imported_data.get(
                'file_type', 'csv')
            enriched_config['Timestep Length (seconds)'] = int(timestep)

            # Ensure numeric fields are proper types
            enriched_config['Spill Target (Entire Period)'] = int(
                enriched_config.get('Spill Target (Entire Period)', 0))

            # Override bathing season target based on THIS scenario's MODEL
            # Model 4 (Bathing Season Assessment) uses bathing targets
            # All other models ignore bathing season
            if model_identifier == 4:
                # Model 4: Use the configured bathing season value
                bathing_target = enriched_config.get(
                    'Spill Target (Bathing Seasons)', 0)
                enriched_config['Spill Target (Bathing Seasons)'] = int(
                    bathing_target) if bathing_target else -1
            else:
                # Models 1, 2, 3: Always ignore bathing season
                enriched_config['Spill Target (Bathing Seasons)'] = -1

            enriched_config['PFF Increase (m3/s)'] = float(
                enriched_config.get('PFF Increase (m3/s)', 0))
            # Tank Volume: Check if key exists and value is not None (not just truthy, since 0.0 is valid)
            tank_vol = enriched_config.get('Tank Volume (m3)')
            enriched_config['Tank Volume (m3)'] = float(
                tank_vol) if tank_vol is not None else None
            enriched_config['Pump Rate (m3/s)'] = float(
                enriched_config.get('Pump Rate (m3/s)', 0))
            enriched_config['Flow Return Threshold (m3/s)'] = float(
                enriched_config.get('Flow Return Threshold (m3/s)', 0))
            enriched_config['Depth Return Threshold (m)'] = float(
                enriched_config.get('Depth Return Threshold (m)', 0))
            enriched_config['Time Delay (hours)'] = int(
                enriched_config.get('Time Delay (hours)', 0))
            enriched_config['Spill Flow Threshold (m3/s)'] = float(
                enriched_config.get('Spill Flow Threshold (m3/s)', 0))
            enriched_config['Spill Volume Threshold (m3)'] = float(
                enriched_config.get('Spill Volume Threshold (m3)', 0))

            enriched_config_data.append(enriched_config)

        self.log(f"Starting {mode} analysis...")
        self.log(
            f"Processing {len(enriched_config_data)} CSO configuration(s)")
        self.log(f"Output directory: {self.output_directory}")

        # Log mode information
        self.log(f"Mode: {mode}")
        # Model-specific behavior will be logged per CSO based on their model selection

        self.log(
            "Scenario thresholds: flow="
            f"{scenario_settings.spill_flow_threshold:.5f} m3/s, volume="
            f"{scenario_settings.spill_volume_threshold:.2f} m3"
        )

        data_source_info: Optional[DataSourceInfo] = None
        data_folder_path = self.imported_data.get('data_folder')
        if data_folder_path:
            data_source_info = DataSourceInfo(
                data_folder=Path(data_folder_path),
                file_type=self.imported_data.get('file_type', 'csv'),
                timestep_seconds=timestep,
                available_links=list(
                    self.imported_data.get('available_links', [])),
                has_depth_data=bool(
                    self.imported_data.get('has_depth_data', True)),
                raw_metadata={
                    'flow_metadata': self.imported_data.get('flow_metadata', {}),
                    'depth_metadata': self.imported_data.get('depth_metadata', {}),
                },
                date_format=self.imported_data.get(
                    'date_format')  # Pass configured date format
            )

        # Disable start button, enable cancel
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)

        # # Create worker thread based on selected engine
        # use_refactored = self.refactored_engine_radio.isChecked()

        # if use_refactored and mode in ("Default Mode", "Catchment Based Mode", "WWTW Mode"):
        # Use new refactored engine - DIRECT EXECUTION (no threading for easier debugging)
        self.log(
            f"Using refactored engine for {mode} (direct execution - blocks UI during analysis)")
        self._run_refactored_analysis_direct(
            enriched_config_data, data_source_info, scenario_settings)
        # Reset buttons after direct execution
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        # return  # Don't start worker thread

        # else:
        #     # Use legacy engine in worker thread
        #     if use_refactored and mode == "WWTW Mode":
        #         self.log(
        #             "⚠ Refactored engine does not support WWTW Mode - using legacy engine")
        #     elif use_refactored:
        #         self.log(
        #             "⚠ Refactored engine only supports Default Mode and Catchment Based Mode - using legacy engine")
        #     else:
        #         self.log(f"Using legacy engine for {mode}")

        #     self.worker_thread = AnalysisWorker(
        #         enriched_config_data,
        #         mode,
        #         self.output_directory,
        #         effective_csos=self.effective_csos,
        #         data_source=data_source_info,
        #         scenario_settings=scenario_settings,
        #     )
        #     self.worker_thread.progress_update.connect(self.on_progress_update)
        #     self.worker_thread.progress_value.connect(self.on_progress_value)
        #     self.worker_thread.analysis_complete.connect(
        #         self.on_analysis_complete)
        #     self.worker_thread.analysis_error.connect(self.on_analysis_error)
        #     self.worker_thread.finished.connect(self.on_thread_finished)
        #     self.worker_thread.start()

    def _run_refactored_analysis_direct(self, config_data: list, data_source: DataSourceInfo, scenario: ScenarioSettings):
        """
        Run refactored engine directly (blocking) for easier debugging.
        No worker thread - blocks UI but allows step-through debugging.
        """
        try:
            self.log("Starting refactored engine analysis...")
            self.progress_bar.setValue(10)

            results = {'_engine': 'refactored'}

            # Group configs by (mode, original_scenario_name) to handle multiple scenarios correctly
            # This prevents mixing of catchment/WWTW/CSO scenarios
            # Use _original_scenario_name field to avoid issues with underscores in scenario names
            from collections import defaultdict
            grouped_scenarios = defaultdict(list)

            for cfg in config_data:
                mode = cfg.get('Analysis Mode', 'Default Mode')
                # Use the tracked original scenario name (set during config creation)
                # This avoids issues with underscores in user-defined scenario names
                original_scenario_name = cfg.get(
                    '_original_scenario_name', cfg.get('Scenario Name', 'Unknown'))

                key = (mode, original_scenario_name)
                grouped_scenarios[key].append(cfg)

            # Log grouped scenarios
            self.log(
                f"Grouped into {len(grouped_scenarios)} scenario group(s):")
            for (mode, scenario_name), configs in grouped_scenarios.items():
                self.log(
                    f"  - {scenario_name} ({mode}): {len(configs)} config(s)")

            # Process each group with appropriate engine
            for idx, ((mode, base_scenario_name), configs) in enumerate(grouped_scenarios.items()):
                self.log(f"\n{'='*60}")
                self.log(
                    f"Processing scenario group {idx+1}/{len(grouped_scenarios)}: {base_scenario_name}")
                self.log(f"Mode: {mode}, Configs: {len(configs)}")
                self.log(f"{'='*60}")

                if mode == "Catchment Based Mode":
                    # Catchment mode - run all CSOs together through CatchmentAnalysisEngine
                    self.log(
                        f"Running catchment analysis for '{base_scenario_name}' with {len(configs)} CSOs...")
                    self._run_catchment_analysis(
                        configs, data_source, scenario, results)
                elif mode == "WWTW Mode":
                    # WwTW mode - run treatment works analysis
                    self.log(
                        f"Running WwTW analysis for '{base_scenario_name}'...")
                    self._run_wwtw_analysis(
                        configs, data_source, scenario, results)
                else:
                    # Default mode - run each CSO individually
                    self.log(
                        f"Running Default Mode analysis for '{base_scenario_name}' ({len(configs)} CSO(s))...")
                    for config_idx, config_dict in enumerate(configs):
                        cso_name = config_dict.get(
                            'CSO Name', f'CSO_{config_idx+1}')
                        # Use scenario name as the unique key for results
                        scenario_name = config_dict.get(
                            'Scenario Name', f'Scenario_{config_idx+1}')

                        self.log(
                            f"\n  Analyzing {scenario_name}: {cso_name}...")

                        # Convert to typed configuration
                        config = CSOConfiguration.from_dict(config_dict)

                        # Create progress callback that updates within this CSO's progress slice
                        def progress_callback(msg):
                            self.log(f"    {msg}")
                            # Force UI refresh so log updates are visible during analysis
                            QApplication.processEvents()

                        # Run analysis - EASY TO DEBUG WITH BREAKPOINTS HERE
                        analyzer = StorageAnalyzer(
                            config, data_source, scenario, progress_callback)
                        result = analyzer.run()

                        # Store result using scenario name as key (enforced to be unique)
                        results[scenario_name] = result.to_summary_dict()
                        results[scenario_name]['_full_result'] = result
                        # Store display name for UI (CSO name like "CSO_1", not the overflow link ID)
                        results[scenario_name]['_cso_display_name'] = config_dict.get(
                            'CSO Display Name', cso_name)

                        self.log(
                            f"  ✓ {scenario_name}: {result.spill_count} spills, "
                            f"{result.final_storage_m3:.1f} m³ storage"
                        )

            self.progress_bar.setValue(100)
            self.log("✓ Refactored engine analysis completed!")

            # Call completion handler directly
            self.on_analysis_complete(results)

        except Exception as e:
            import traceback
            error_msg = f"✗ Error: {str(e)}\n{traceback.format_exc()}"
            self.log(error_msg)
            QMessageBox.critical(
                self,
                "Analysis Error",
                f"Refactored engine failed:\n\n{str(e)}"
            )
            # Reset UI state
            self.status_label.setText("✗ Analysis failed")
            self.status_label.setStyleSheet(
                "QLabel { color: red; font-weight: bold; }")

    def _run_catchment_analysis(self, config_data: list, data_source: DataSourceInfo, scenario: ScenarioSettings, results: dict):
        """
        Run catchment analysis using CatchmentAnalysisEngine.
        All CSOs are analyzed together in a coordinated fashion.
        """
        import pandas as pd
        from datetime import timedelta
        from plato.refactored.catchment_engine import CatchmentAnalysisEngine

        self.progress_bar.setValue(20)

        # Convert config_data list to DataFrame (CatchmentAnalysisEngine expects this)
        overflow_df = pd.DataFrame(config_data)

        # Load flow and depth data
        data_folder = data_source.data_folder
        file_type = data_source.file_type

        self.log(f"Loading flow data from {data_folder}...")

        # Parse data files (similar to legacy PLATO_SM_Catchment.parseData)
        if file_type == 'csv':
            # Get all flow files (standard + ICM default naming)
            flow_files = list(sorted(data_folder.glob('*_Q.csv')))
            flow_files.extend(sorted(data_folder.glob('*_us_flow.csv')))
            if not flow_files:
                raise ValueError(f"No flow CSV files found in {data_folder}")

            # Read and combine all flow files
            flow_dfs = []
            date_kwargs = self._get_date_parser_kwargs()
            for f in flow_files:
                df = pd.read_csv(f, **date_kwargs)
                flow_dfs.append(df)

            # Merge on Time column
            flow_data = flow_dfs[0]
            for df in flow_dfs[1:]:
                flow_data = flow_data.merge(df, on='Time', how='outer')
            flow_data = flow_data.sort_values('Time').reset_index(drop=True)

            # Get depth data (standard + ICM default naming)
            depth_files = list(sorted(data_folder.glob('*_D.csv')))
            depth_files.extend(sorted(data_folder.glob('*_us_depth.csv')))
            if depth_files:
                depth_dfs = []
                date_kwargs = self._get_date_parser_kwargs()
                for f in depth_files:
                    df = pd.read_csv(f, **date_kwargs)
                    depth_dfs.append(df)
                depth_data = depth_dfs[0]
                for df in depth_dfs[1:]:
                    depth_data = depth_data.merge(df, on='Time', how='outer')
                depth_data = depth_data.sort_values(
                    'Time').reset_index(drop=True)
            else:
                # No depth data - create empty DataFrame with same time index
                depth_data = pd.DataFrame({'Time': flow_data['Time']})
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        self.log(f"Loaded {len(flow_data)} timesteps of flow data")
        self.progress_bar.setValue(40)

        # Calculate timestep
        timestep_seconds = data_source.timestep_seconds or 300  # Default 5 minutes
        timestep = timedelta(seconds=timestep_seconds)

        # Get output directory
        output_dir = self.output_directory

        self.log("Initializing catchment analysis engine...")

        # Create progress callback
        def progress_callback(msg):
            self.log(msg)
            QApplication.processEvents()

        # Initialize and run catchment engine
        engine = CatchmentAnalysisEngine(
            overflow_data=overflow_df,
            flow_data=flow_data,
            depth_data=depth_data,
            master_directory=output_dir,
            timestep_length=timestep,
            progress_callback=progress_callback,
            data_folder=str(data_folder),
            file_type=file_type,
            date_kwargs=date_kwargs
        )

        self.progress_bar.setValue(50)
        self.log("Running catchment analysis...")

        # Get analysis parameters from first config (they're all the same for catchment)
        first_config = config_data[0]
        start_date = first_config.get('Start Date (dd/mm/yy hh:mm:ss)', '')
        end_date = first_config.get('End Date (dd/mm/yy hh:mm:ss)', '')
        model_id = int(first_config.get('Model Identifier', 1))
        bathing_start = first_config.get('Bathing Season Start (dd/mm)')
        bathing_end = first_config.get('Bathing Season End (dd/mm)')

        # Run the analysis with parameters
        catchment_results = engine.run_analysis(
            start_date=start_date,
            end_date=end_date,
            model_id=model_id,
            bathing_season_start=bathing_start,
            bathing_season_end=bathing_end
        )

        self.progress_bar.setValue(90)

        # Convert results to expected format for results tab
        # catchment_results is a dict with CSO names as keys
        from plato.refactored.models import CSOAnalysisResult, SpillEvent
        from datetime import datetime

        for cso_name, cso_result in catchment_results.items():
            # Find the scenario name for this CSO
            cso_config = next(
                (c for c in config_data if c.get('CSO Name') == cso_name), None)
            if cso_config:
                scenario_name = cso_config.get('Scenario Name', cso_name)

                # Extract spill events DataFrame and timeseries from catchment results
                spill_events_df = cso_result.get(
                    'spill_events', pd.DataFrame())
                timeseries_df = cso_result.get('timeseries', pd.DataFrame())

                # Convert DataFrame to list of SpillEvent objects with ACTUAL durations
                spill_event_list = []
                total_spill_volume = 0.0
                bathing_spill_volume = 0.0
                total_spill_duration = 0.0
                bathing_spill_duration = 0.0

                if not spill_events_df.empty and not timeseries_df.empty:
                    # Get flow column name for this CSO
                    cso_flow_col = cso_name + '_Flow'
                    spill_threshold = cso_config.get(
                        'Spill Flow Threshold (m3/s)', 0.0)

                    for _, row in spill_events_df.iterrows():
                        # Extract values from catchment engine format
                        start_time = row['DateTime']
                        volume_m3 = row.get('Spill Volume (m3)', 0.0)
                        in_bathing = row.get('In Bathing Season', False)
                        window_duration_hrs = row.get('Duration (hours)', 12.0)

                        # End time defines the spill WINDOW (not actual spill duration)
                        end_time = start_time + \
                            pd.Timedelta(hours=window_duration_hrs)

                        # Calculate ACTUAL spill duration = sum of timesteps where spill exceeded threshold
                        spill_window_mask = (timeseries_df['Time'] >= start_time) & \
                            (timeseries_df['Time'] <= end_time) & \
                            (timeseries_df[cso_flow_col]
                             > spill_threshold)

                        if spill_window_mask.any():
                            # Count timesteps where spill occurred within the window
                            num_spill_timesteps = spill_window_mask.sum()
                            # Convert to hours (timestep_seconds already defined above)
                            actual_duration_hours = (
                                num_spill_timesteps * timestep_seconds) / 3600.0

                            # Calculate peak flow during this spill window
                            peak_flow_m3s = timeseries_df.loc[spill_window_mask, cso_flow_col].max(
                            )
                        else:
                            # No spill data found in window (shouldn't happen, but handle gracefully)
                            actual_duration_hours = 0.0
                            peak_flow_m3s = 0.0

                        # Create SpillEvent object with actual duration
                        spill_event = SpillEvent(
                            start_time=start_time,
                            end_time=end_time,
                            window_duration_hours=window_duration_hrs,
                            spill_duration_hours=actual_duration_hours,
                            volume_m3=volume_m3,
                            peak_flow_m3s=peak_flow_m3s
                        )
                        spill_event_list.append(spill_event)

                        # Accumulate statistics with actual duration
                        total_spill_volume += volume_m3
                        total_spill_duration += actual_duration_hours

                        if in_bathing:
                            bathing_spill_volume += volume_m3
                            bathing_spill_duration += actual_duration_hours

                # Prepare timeseries DataFrame for plotting
                # Rename columns to match what results tab expects
                plot_timeseries = timeseries_df.copy() if not timeseries_df.empty else pd.DataFrame()
                if not plot_timeseries.empty:
                    cso_flow_col = cso_name + '_Flow'

                    # Create expected column names
                    if cso_flow_col in plot_timeseries.columns:
                        # CSO_Flow_Original should already be in the timeseries from catchment engine
                        # (extracted from Timeseries_Data_Original which has the true original overflow)
                        # Only create it if it doesn't exist (fallback for older code)
                        if 'CSO_Flow_Original' not in plot_timeseries.columns:
                            plot_timeseries['CSO_Flow_Original'] = plot_timeseries[cso_flow_col]

                        # Spill flow is the modified flow (after storage applied)
                        plot_timeseries['Spill_Flow'] = plot_timeseries[cso_flow_col]

                    # Rename Tank Volume column (catchment has space, results tab expects underscore)
                    if 'Tank Volume' in plot_timeseries.columns:
                        plot_timeseries['Tank_Volume'] = plot_timeseries['Tank Volume']

                # Create a CSOAnalysisResult object for consistent results format
                full_result = CSOAnalysisResult(
                    cso_name=cso_name,
                    run_suffix=cso_config.get('Run Suffix', ''),
                    final_storage_m3=cso_result.get('storage_volume', 0.0),
                    converged=cso_result.get('converged', False),
                    iterations_count=cso_result.get('iterations', 0),
                    spill_count=cso_result.get('spill_count', 0),
                    bathing_spills_count=cso_result.get(
                        'bathing_spill_count', 0),
                    total_spill_volume_m3=total_spill_volume,
                    bathing_spill_volume_m3=bathing_spill_volume,
                    total_spill_duration_hours=total_spill_duration,
                    bathing_spill_duration_hours=bathing_spill_duration,
                    spill_events=spill_event_list,
                    time_series=plot_timeseries,
                    analysis_date=datetime.now(),
                    output_directory=None
                )

                results[scenario_name] = {
                    'spill_count': cso_result.get('spill_count', 0),
                    'final_storage_m3': cso_result.get('storage_volume', 0),
                    'status': 'completed',
                    '_cso_display_name': cso_config.get('CSO Display Name', cso_name),
                    '_full_result': full_result,  # Store full result for results tab
                }
                self.log(f"  ✓ {scenario_name}: {cso_result.get('spill_count', 0)} spills, "
                         f"{cso_result.get('storage_volume', 0):.1f} m³ storage")

    def _run_wwtw_analysis(
            self, config_data: list, data_source: DataSourceInfo,
            scenario: ScenarioSettings, results: dict):
        """
        Run WwTW (Wastewater Treatment Works) analysis using WWTWAnalysisEngine.
        """
        import pandas as pd
        from plato.refactored.wwtw_engine import WWTWAnalysisEngine

        self.progress_bar.setValue(20)

        # Convert config_data to DataFrame (WWTWAnalysisEngine expects this)
        # WwTW run data needs: Run Suffix, FFT (m3/s), Pump Rate (m3/s),
        # Pump On Threshold (m3/s), Pump Off Threshold (m3/s)
        run_data_records = []
        for cfg in config_data:
            run_data_records.append({
                'Run Suffix': cfg.get('Scenario Name', 'Run'),
                'FFT (m3/s)': cfg.get('FFT Augmentation (m3/s)', 0.0),
                'Pump Rate (m3/s)': cfg.get('WwTW Pump Rate (m3/s)', 0.0),
                'Pump On Threshold (m3/s)': cfg.get('WwTW Pump On Threshold (m3/s)', 0.0),
                'Pump Off Threshold (m3/s)': cfg.get('WwTW Pump Off Threshold (m3/s)', 0.0),
            })
        run_data = pd.DataFrame(run_data_records)

        # Load flow data
        data_folder = data_source.data_folder
        file_type = data_source.file_type

        self.log(f"Loading flow data from {data_folder}...")

        if file_type == 'csv':
            # Get all flow files
            flow_files = sorted(data_folder.glob('*_Q.csv'))
            if not flow_files:
                raise ValueError(f"No flow CSV files found in {data_folder}")

            # Read and combine all flow files
            flow_dfs = []
            date_kwargs = self._get_date_parser_kwargs()
            for f in flow_files:
                df = pd.read_csv(f, **date_kwargs)
                flow_dfs.append(df)

            # Merge on Time column
            flow_data = flow_dfs[0]
            for df in flow_dfs[1:]:
                flow_data = flow_data.merge(df, on='Time', how='outer')
            flow_data = flow_data.sort_values('Time').reset_index(drop=True)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        self.log(f"Loaded {len(flow_data)} timesteps of flow data")
        self.progress_bar.setValue(40)

        # Prepare flow data for WwTW analysis
        # Need to extract link names from config and set up required columns
        first_config = config_data[0]
        spill_links = first_config.get('Spill Links', '').split(',')
        spill_links = [link.strip() for link in spill_links if link.strip()]
        fft_link = first_config.get('FFT Link', '').strip()
        pump_links = first_config.get('Pump Links', '').split(',')
        pump_links = [link.strip() for link in pump_links if link.strip()]

        self.log(
            f"WwTW Configuration: FFT={fft_link}, Spills={spill_links}, Pumps={pump_links}")

        # Create 'Spill' column by summing all spill links
        if spill_links:
            # Check if columns exist
            missing_spill = [
                col for col in spill_links if col not in flow_data.columns]
            if missing_spill:
                raise ValueError(
                    f"Spill links not found in flow data: {missing_spill}")
            flow_data['Spill'] = flow_data[spill_links].sum(axis=1)
        else:
            flow_data['Spill'] = 0.0

        # Create 'Continuation' column from FFT link
        if fft_link and fft_link in flow_data.columns:
            flow_data.rename(columns={fft_link: 'Continuation'}, inplace=True)
        else:
            raise ValueError(f"FFT Link '{fft_link}' not found in flow data")

        # Create 'Original Continuation' as a copy before pump adjustments
        flow_data['Original Continuation'] = flow_data['Continuation'].copy()

        # Subtract pump flows from continuation (if pumps exist)
        if pump_links:
            missing_pumps = [
                col for col in pump_links if col not in flow_data.columns]
            if missing_pumps:
                raise ValueError(
                    f"Pump links not found in flow data: {missing_pumps}")
            flow_data['Continuation'] -= flow_data[pump_links].sum(axis=1)
            self.log(
                f"Adjusted continuation flow by subtracting {len(pump_links)} pump link(s)")

        # Calculate timestep in seconds
        timestep_seconds = data_source.timestep_seconds or 300  # Default 5 minutes

        # Get output directory
        output_dir = self.output_directory

        self.log("Initializing WwTW analysis engine...")

        # Create progress callback with indentation for nested messages
        def progress_callback(msg):
            self.log(f"  {msg}")
            QApplication.processEvents()

        # Create engine (takes first run only for single WwTW)
        engine = WWTWAnalysisEngine(
            run_data=run_data.iloc[[0]],  # Take first run config
            flow_data=flow_data,
            outputs_directory=str(output_dir),
            timestep_length=timestep_seconds,
            progress_callback=progress_callback
        )

        self.progress_bar.setValue(50)
        self.log("Running WwTW analysis...")

        # Get analysis parameters (first_config already extracted above)
        start_date = first_config.get('Start Date (dd/mm/yy hh:mm:ss)', None)
        end_date = first_config.get('End Date (dd/mm/yy hh:mm:ss)', None)
        bathing_start = first_config.get('Bathing Season Start (dd/mm)', None)
        bathing_end = first_config.get('Bathing Season End (dd/mm)', None)

        # Get storage and threshold parameters
        storage_volume = first_config.get('Tank Volume (m3)', 0.0)
        time_delay_hours = int(first_config.get('Time Delay (hours)', 0))

        # Convert time delay from hours to timesteps
        timestep_seconds = data_source.timestep_seconds or 300  # Default 5 minutes
        time_delay_timesteps = int(
            (time_delay_hours * 3600) / timestep_seconds)

        spill_flow_thresh = first_config.get(
            'Spill Flow Threshold (m3/s)', 0.0)
        spill_vol_thresh = first_config.get('Spill Volume Threshold (m3)', 0.0)
        spill_target = first_config.get('Spill Target (Entire Period)', -1)
        bathing_spill_target = first_config.get(
            'Spill Target (Bathing Seasons)', -1)

        # # DEBUG: Log what we're about to pass to the engine
        # self.log(f"  DEBUG before engine.run_analysis():")
        # self.log(
        #     f"    storage_volume = {storage_volume} (type: {type(storage_volume).__name__})")
        # self.log(
        #     f"    first_config['Tank Volume (m3)'] = {first_config.get('Tank Volume (m3)', 'KEY_NOT_FOUND')}")
        # self.log(f"    first_config keys: {list(first_config.keys())}")

        # Run the analysis
        wwtw_results = engine.run_analysis(
            storage_volume=storage_volume,
            time_delay_timesteps=time_delay_timesteps,
            spill_flow_threshold=spill_flow_thresh,
            spill_volume_threshold=spill_vol_thresh,
            bathing_season_start=bathing_start,
            bathing_season_end=bathing_end,
            spill_target=spill_target,
            bathing_spill_target=bathing_spill_target,
            start_date=start_date,
            end_date=end_date
        )

        self.progress_bar.setValue(90)

        # Convert results to expected format - create full result object for Results tab
        scenario_name = first_config.get('Scenario Name', 'WwTW Run')
        wwtw_name = first_config.get('WwTW Name', 'Unknown')

        # Extract spill events and timeseries from WwTW engine results
        spill_events_df = wwtw_results.get('spill_events', pd.DataFrame())
        timeseries_df = wwtw_results.get('flow_data', pd.DataFrame())

        # Convert spill events DataFrame to SpillEvent objects
        from plato.refactored.models import CSOAnalysisResult, SpillEvent
        from datetime import datetime

        spill_event_list = []
        total_spill_volume = 0.0
        bathing_spill_volume = 0.0
        total_spill_duration = 0.0
        bathing_spill_duration = 0.0

        if not spill_events_df.empty and not timeseries_df.empty:
            # Get spill flow column name (should be 'Spill' in WwTW data)
            spill_col = 'Spill'

            for _, row in spill_events_df.iterrows():
                start_time = row['DateTime']
                volume_m3 = row.get('Spill Volume (m3)', 0.0)
                in_bathing = row.get('In Bathing Season', False)
                window_duration_hrs = row.get('Duration (hours)', 12.0)

                # End time defines the spill WINDOW (not actual spill duration)
                end_time = start_time + pd.Timedelta(hours=window_duration_hrs)

                # Calculate ACTUAL spill duration = sum of timesteps where spill exceeded threshold
                spill_window_mask = (timeseries_df['Time'] >= start_time) & \
                    (timeseries_df['Time'] <= end_time) & \
                    (timeseries_df[spill_col]
                     > spill_flow_thresh)

                if spill_window_mask.any():
                    # Count timesteps where spill occurred within the window
                    num_spill_timesteps = spill_window_mask.sum()
                    # Convert to hours (timestep_seconds already defined above)
                    actual_duration_hours = (
                        num_spill_timesteps * timestep_seconds) / 3600.0

                    # Calculate peak flow during this spill window
                    peak_flow_m3s = timeseries_df.loc[spill_window_mask, spill_col].max(
                    )
                else:
                    # No spill data found in window (shouldn't happen, but handle gracefully)
                    actual_duration_hours = 0.0
                    peak_flow_m3s = 0.0

                spill_event = SpillEvent(
                    start_time=start_time,
                    end_time=end_time,
                    window_duration_hours=window_duration_hrs,
                    spill_duration_hours=actual_duration_hours,
                    volume_m3=volume_m3,
                    peak_flow_m3s=peak_flow_m3s
                )
                spill_event_list.append(spill_event)

                # Accumulate statistics with actual duration
                total_spill_volume += volume_m3
                total_spill_duration += actual_duration_hours

                if in_bathing:
                    bathing_spill_volume += volume_m3
                    bathing_spill_duration += actual_duration_hours

        # Prepare timeseries for plotting (rename columns to match Results tab expectations)
        plot_timeseries = timeseries_df.copy() if not timeseries_df.empty else pd.DataFrame()
        if not plot_timeseries.empty:
            # Rename columns to match what Results tab expects
            if 'Spill' in plot_timeseries.columns:
                plot_timeseries['Spill_Flow'] = plot_timeseries['Spill']
            if 'Continuation' in plot_timeseries.columns:
                plot_timeseries['CSO_Flow_Original'] = plot_timeseries['Original Continuation']
            if 'Tank Volume' in plot_timeseries.columns:
                plot_timeseries['Tank_Volume'] = plot_timeseries['Tank Volume']

        # Create a CSOAnalysisResult object for consistent results format
        # (reusing this class for WwTW since it has the same structure)
        full_result = CSOAnalysisResult(
            cso_name=wwtw_name,
            run_suffix=first_config.get('Run Suffix', ''),
            final_storage_m3=wwtw_results.get(
                'storage_volume', storage_volume),
            converged=True,  # WwTW always converges or hits max iterations
            iterations_count=wwtw_results.get('iterations', 0),
            spill_count=wwtw_results.get('spill_count', 0),
            bathing_spills_count=wwtw_results.get('bathing_spill_count', 0),
            total_spill_volume_m3=total_spill_volume,
            bathing_spill_volume_m3=bathing_spill_volume,
            total_spill_duration_hours=total_spill_duration,
            bathing_spill_duration_hours=bathing_spill_duration,
            spill_events=spill_event_list,
            time_series=plot_timeseries,
            analysis_date=datetime.now(),
            output_directory=None
        )

        results[scenario_name] = {
            'spill_count': wwtw_results.get('spill_count', 0),
            'final_storage_m3': wwtw_results.get('storage_volume', storage_volume),
            'status': 'completed',
            '_wwtw_name': wwtw_name,
            '_full_result': full_result,  # Store full result for Results tab
        }
        self.log(f"  ✓ {scenario_name}: {wwtw_results.get('spill_count', 0)} spills, "
                 f"{wwtw_results.get('storage_volume', storage_volume):.1f} m³ storage")

    def cancel_analysis(self):
        """Cancel the running analysis."""
        if self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Cancel Analysis",
                "Are you sure you want to cancel the running analysis?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.worker_thread.cancel()
                self.log("Cancellation requested...")

    @pyqtSlot(str)
    def on_progress_update(self, message: str):
        """Handle progress message update."""
        self.log(message)

    @pyqtSlot(int)
    def on_progress_value(self, value: int):
        """Handle progress bar update."""
        self.progress_bar.setValue(value)
        self.status_label.setText(f"Analysis running... {value}%")

    @pyqtSlot(dict)
    def on_analysis_complete(self, results: dict):
        """Handle analysis completion."""
        # Merge new results with existing results (don't replace everything)
        # This allows running subsets of scenarios without losing previous results
        if not self.analysis_results:
            # First analysis - just use the new results
            self.analysis_results = results
        else:
            # Merge new results into existing results
            # Keep metadata keys from new results (like _engine)
            for key in ["_engine", "_scenario", "effective_csos"]:
                if key in results:
                    self.analysis_results[key] = results[key]

            # Add/update scenario results
            for key, value in results.items():
                if key not in {"effective_csos", "_scenario", "_engine", "error"}:
                    self.analysis_results[key] = value

        self.status_label.setText("✓ Analysis completed successfully!")
        self.status_label.setStyleSheet(
            "QLabel { color: green; font-weight: bold; }")

        # Enable head-discharge analysis button now that we have results
        self.head_discharge_btn.setEnabled(True)

        # Save results to disk for persistence
        self._save_results_to_disk()

        # Count the number of scenarios that were analyzed
        # Use the selected_scenarios list that was passed to start_analysis()
        # This avoids issues with underscores in scenario names
        selected_scenarios = self.scenario_queue.get_selected_scenarios()
        scenario_count = len(selected_scenarios)

        # Mark completed scenarios in the queue
        for key in results.keys():
            if key not in {"effective_csos", "_scenario", "_engine", "error"}:
                self.scenario_queue.mark_scenario_complete(key)

        QMessageBox.information(
            self,
            "Analysis Complete",
            f"Analysis completed successfully!\n\nProcessed {scenario_count} scenario(s)."
        )

        # Emit ALL results to other tabs (merged results, not just new ones)
        self.analysis_completed.emit(self.analysis_results)

        # Auto-save project to keep state in sync with output files
        self._auto_save_project_after_analysis()

    @pyqtSlot(str)
    def on_analysis_error(self, error_msg: str):
        """Handle analysis error."""
        self.status_label.setText("✗ Analysis failed")
        self.status_label.setStyleSheet(
            "QLabel { color: red; font-weight: bold; }")

        QMessageBox.critical(
            self,
            "Analysis Error",
            f"Analysis failed with error:\n\n{error_msg}"
        )

    def _save_results_to_disk(self):
        """Save analysis results to Parquet files for persistence across sessions."""
        if not self.analysis_results or not self.output_directory:
            self.log("⚠ Cannot save results: no results or output directory")
            return

        import pandas as pd

        try:
            results_dir = Path(self.output_directory)
            results_dir.mkdir(parents=True, exist_ok=True)

            saved_count = 0
            skipped_count = 0

            for scenario_name, result_data in self.analysis_results.items():
                # Skip metadata keys (these are strings or non-dict values)
                if scenario_name in {"effective_csos", "_scenario", "_engine", "error"}:
                    skipped_count += 1
                    continue

                # Skip if result_data is not a dictionary
                if not isinstance(result_data, dict):
                    self.log(
                        f"  ⚠ Skipping {scenario_name}: not a dict (type: {type(result_data).__name__})")
                    skipped_count += 1
                    continue

                # Get the full result object
                full_result = result_data.get('_full_result')
                if not full_result:
                    self.log(
                        f"  ⚠ Skipping {scenario_name}: no _full_result found")
                    self.log(
                        f"     Available keys: {list(result_data.keys())}")
                    skipped_count += 1
                    continue

                # Save timeseries DataFrame
                if hasattr(full_result, 'time_series') and full_result.time_series is not None:
                    parquet_path = results_dir / \
                        f"{scenario_name}_timeseries.parquet"
                    full_result.time_series.to_parquet(parquet_path)

                # Save spill events DataFrame
                if hasattr(full_result, 'spill_events') and full_result.spill_events:
                    spill_df = pd.DataFrame([asdict(evt)
                                            for evt in full_result.spill_events])
                    spill_parquet = results_dir / \
                        f"{scenario_name}_spills.parquet"
                    spill_df.to_parquet(spill_parquet)

                # Save summary metadata as JSON
                import json
                summary = {
                    'cso_name': full_result.cso_name,
                    'run_suffix': full_result.run_suffix,
                    'converged': full_result.converged,
                    'final_storage_m3': full_result.final_storage_m3,
                    'iterations_count': full_result.iterations_count,
                    'spill_count': full_result.spill_count,
                    'bathing_spills_count': full_result.bathing_spills_count,
                    'total_spill_volume_m3': full_result.total_spill_volume_m3,
                    'bathing_spill_volume_m3': full_result.bathing_spill_volume_m3,
                    'total_spill_duration_hours': full_result.total_spill_duration_hours,
                    'bathing_spill_duration_hours': full_result.bathing_spill_duration_hours,
                }
                summary_path = results_dir / f"{scenario_name}_summary.json"
                with open(summary_path, 'w') as f:
                    json.dump(summary, f, indent=2)

                self.log(f"  ✓ Saved {scenario_name}")
                saved_count += 1

            self.log(
                f"✓ Results saved: {saved_count} scenarios, {skipped_count} skipped")
            self.log(f"  Output directory: {results_dir}")

        except Exception as e:
            self.log(f"⚠ Warning: Could not save results to disk: {e}")

    def _load_results_from_disk(self):
        """Load analysis results from Parquet files (for persistence across sessions)."""
        if not self.output_directory or not Path(self.output_directory).exists():
            return

        import pandas as pd
        import json
        from plato.refactored.models import CSOAnalysisResult, SpillEvent

        try:
            results_dir = Path(self.output_directory)

            # Find all summary JSON files
            summary_files = list(results_dir.glob("*_summary.json"))
            if not summary_files:
                return

            # Get current scenario names to filter against orphaned results
            scenario_names = {
                scenario.scenario_name for scenario in self.scenarios
            } if self.scenarios else set()

            self.analysis_results = {}

            for summary_path in summary_files:
                scenario_name = summary_path.stem.replace('_summary', '')

                # Skip loading results that don't have corresponding scenarios
                # (unless we don't have scenario info yet, e.g., during initial load)
                if scenario_names and scenario_name not in scenario_names:
                    self.log(
                        f"⚠ Skipping orphaned result: {scenario_name} (scenario no longer exists)")
                    continue

                try:
                    # Load summary metadata
                    with open(summary_path, 'r') as f:
                        summary = json.load(f)

                    # Load timeseries
                    timeseries_path = results_dir / \
                        f"{scenario_name}_timeseries.parquet"
                    time_series = None
                    if timeseries_path.exists():
                        time_series = pd.read_parquet(timeseries_path)

                    # Load spill events
                    spills_path = results_dir / \
                        f"{scenario_name}_spills.parquet"
                    spill_events = []
                    if spills_path.exists():
                        spill_df = pd.read_parquet(spills_path)
                        for _, row in spill_df.iterrows():
                            spill_events.append(SpillEvent(
                                start_time=pd.to_datetime(row['start_time']),
                                end_time=pd.to_datetime(row['end_time']),
                                window_duration_hours=row.get(
                                    'window_duration_hours', 12.0),
                                spill_duration_hours=row.get(
                                    'spill_duration_hours', 0.0),
                                volume_m3=row.get('volume_m3', 0.0),
                                peak_flow_m3s=row.get('peak_flow_m3s', 0.0)
                            ))

                    # Reconstruct full result object
                    full_result = CSOAnalysisResult(
                        cso_name=summary['cso_name'],
                        run_suffix=summary.get('run_suffix', ''),
                        converged=summary.get('converged', True),
                        final_storage_m3=summary['final_storage_m3'],
                        iterations_count=summary['iterations_count'],
                        spill_events=spill_events,
                        time_series=time_series,
                        spill_count=summary['spill_count'],
                        bathing_spills_count=summary['bathing_spills_count'],
                        total_spill_volume_m3=summary['total_spill_volume_m3'],
                        bathing_spill_volume_m3=summary['bathing_spill_volume_m3'],
                        total_spill_duration_hours=summary['total_spill_duration_hours'],
                        bathing_spill_duration_hours=summary['bathing_spill_duration_hours'],
                        analysis_date=datetime.now(),  # Use current time since not saved
                    )

                    # Store in results dictionary
                    self.analysis_results[scenario_name] = {
                        '_full_result': full_result,
                        # Add other fields that Results tab expects
                        'final_storage': full_result.final_storage_m3,
                        'spill_count': full_result.spill_count,
                        'bathing_spill_count': full_result.bathing_spills_count,
                    }

                except Exception as e:
                    self.log(
                        f"⚠ Could not load results for {scenario_name}: {e}")
                    continue

            if self.analysis_results:
                result_count = len(self.analysis_results)
                self.log(
                    f"✓ Loaded {result_count} result(s) from previous session")
                self.status_label.setText(
                    f"Loaded {result_count} result(s) from disk")
                self.status_label.setStyleSheet("QLabel { color: blue; }")

                # Enable head-discharge analysis button when results exist
                self.head_discharge_btn.setEnabled(True)

                # Emit to results tab
                self.analysis_completed.emit(self.analysis_results)

        except Exception as e:
            self.log(f"⚠ Warning:  results from disk: {e}")

    def _auto_save_project_after_analysis(self):
        """
        Automatically save the project after analysis completes to keep
        project state in sync with analysis output files.
        """
        try:
            # Get the main window
            main_window = self.window()
            if not main_window or not hasattr(main_window, 'save_project'):
                self.log("⚠ Cannot auto-save: main window not accessible")
                return

            # Check if project has been saved before
            if not hasattr(main_window, 'current_project_file') or not main_window.current_project_file:
                self.log("⚠ Cannot auto-save: project has never been saved")
                return

            # Save the project
            self.log("💾 Auto-saving project to keep state in sync with outputs...")
            success = main_window.save_project()

            if success:
                self.log("✓ Project saved successfully")
            else:
                self.log("⚠ Project save was cancelled or failed")

        except Exception as e:
            self.log(f"⚠ Warning: Could not auto-save project: {e}")

    def _cleanup_orphaned_results(self):
        """Remove result files for scenarios that no longer exist."""
        if not self.output_directory or not Path(self.output_directory).exists():
            return

        try:
            results_dir = Path(self.output_directory)

            # Get current scenario names
            scenario_names = {
                scenario.scenario_name for scenario in self.scenarios
            } if self.scenarios else set()

            if not scenario_names:
                # No scenarios defined, don't clean up (might be during initialization)
                return

            # Find all summary JSON files (these indicate what results exist)
            summary_files = list(results_dir.glob("*_summary.json"))
            orphaned_count = 0

            for summary_path in summary_files:
                scenario_name = summary_path.stem.replace('_summary', '')

                if scenario_name not in scenario_names:
                    orphaned_count += 1
                    self.log(
                        f"🧹 Cleaning up orphaned result files for: {scenario_name}")

                    # Remove all related files for this scenario
                    patterns = [
                        f"{scenario_name}_summary.json",
                        f"{scenario_name}_timeseries.parquet",
                        f"{scenario_name}_spills.parquet"
                    ]

                    for pattern in patterns:
                        file_path = results_dir / pattern
                        if file_path.exists():
                            try:
                                file_path.unlink()
                                self.log(f"  ✓ Removed {pattern}")
                            except Exception as e:
                                self.log(
                                    f"  ⚠ Could not remove {pattern}: {e}")

            if orphaned_count > 0:
                self.log(f"✓ Cleaned up {orphaned_count} orphaned result(s)")

        except Exception as e:
            self.log(f"⚠ Warning: Could not clean up orphaned results: {e}")

    def on_thread_finished(self):
        """Clean up when thread finishes."""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.worker_thread = None

    def log(self, message: str):
        """Add message to log."""
        self.log_text.append(message)
        # Auto-scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def clear_log(self):
        """Clear the log text."""
        self.log_text.clear()

    def _mode_identifier(self, mode_label: str) -> str:
        """Convert mode label to short identifier for file naming."""
        mapping = {
            "Default Mode": "default",
            "Catchment Based Mode": "catchment",
            "WWTW Mode": "wwtw",
        }
        return mapping.get(mode_label, "default")

    def _scenario_to_state(self, settings: ScenarioSettings) -> Dict[str, Any]:
        data = asdict(settings)
        for key in ("bathing_season_start", "bathing_season_end"):
            value = data.get(key)
            if isinstance(value, date):
                data[key] = value.strftime("%d/%m")
        return data

    def _scenario_from_state(self, data: Dict[str, Any]) -> ScenarioSettings:
        parsed = data.copy()
        for key in ("bathing_season_start", "bathing_season_end"):
            parsed[key] = self._parse_day_month_value(parsed.get(key))
        return ScenarioSettings(**parsed)

    def _parse_day_month_value(self, value: Any) -> Optional[date]:
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                day, month = map(int, value.split("/"))
                return date(2000, month, day)
            except Exception:
                return None
        return None

    def get_state(self) -> Dict[str, Any]:
        """Get current tab state for saving."""
        # Don't save analysis results - they're too large and should be loaded from output files
        return {
            'output_directory': self.output_directory,  # Store for results persistence
        }

    def load_state(self, state: Dict[str, Any]):
        """Restore tab state from saved data."""
        # Results are not saved - will be loaded from output files
        if 'output_directory' in state:
            self.output_directory = state['output_directory']
            # Update scenario queue with output directory
            self.scenario_queue.set_scenarios(
                self.scenarios, self.output_directory)
            # Try to load results from disk
            self._load_results_from_disk()

    def reset(self):
        """Reset tab to initial state."""
        self.scenarios = []
        self.cso_assets = []
        self.configurations = []
        self.config_data = []
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.status_label.setText("Ready to run analysis")
        self.status_label.setStyleSheet(
            "QLabel { color: gray; font-style: italic; }")
        self.analysis_results = {}
        self.start_btn.setEnabled(False)
        self.scenario_queue.set_scenarios([], None)

    def _normalize_date_ranges(self, configs: list[Dict[str, Any]]) -> tuple[list[Dict[str, Any]], list[str]]:
        """Validate and normalize start/end dates, returning errors if found."""
        normalized: list[Dict[str, Any]] = []
        errors: list[str] = []

        data_start = self._coerce_datetime_value(
            self.imported_data.get('data_start'))
        data_end = self._coerce_datetime_value(
            self.imported_data.get('data_end'))

        for index, config in enumerate(configs, start=1):
            cso_name = config.get('CSO Name') or f"Row {index}"
            start_value = config.get('Start Date (dd/mm/yy hh:mm:ss)', '')
            end_value = config.get('End Date (dd/mm/yy hh:mm:ss)', '')

            start_dt = self._parse_config_datetime(start_value)
            end_dt = self._parse_config_datetime(end_value)

            issues: list[str] = []
            if not start_dt:
                issues.append(
                    "Start Date is missing or invalid (expected dd/mm/yyyy HH:MM[:SS])")
            if not end_dt:
                issues.append(
                    "End Date is missing or invalid (expected dd/mm/yyyy HH:MM[:SS])")

            if start_dt and end_dt and start_dt > end_dt:
                issues.append("Start Date must be before End Date")

            if data_start and start_dt and start_dt < data_start:
                issues.append(
                    f"Start Date {start_dt:%d/%m/%Y %H:%M:%S} is before available data ({data_start:%d/%m/%Y %H:%M:%S})"
                )
            if data_end and end_dt and end_dt > data_end:
                issues.append(
                    f"End Date {end_dt:%d/%m/%Y %H:%M:%S} exceeds available data ({data_end:%d/%m/%Y %H:%M:%S})"
                )

            if issues:
                errors.append(f"{cso_name}: {'; '.join(issues)}")
                normalized.append(config.copy())
                continue

            if start_dt is None or end_dt is None:
                # Should not happen due to checks above, but guard for type-safety
                normalized.append(config.copy())
                continue

            normalized_config = config.copy()
            normalized_config['Start Date (dd/mm/yy hh:mm:ss)'] = start_dt.strftime(
                self.OUTPUT_DATETIME_FORMAT)
            normalized_config['End Date (dd/mm/yy hh:mm:ss)'] = end_dt.strftime(
                self.OUTPUT_DATETIME_FORMAT)
            normalized.append(normalized_config)

        return normalized, errors

    def _parse_config_datetime(self, value: Any) -> Optional[datetime]:
        """Parse configuration date strings using supported formats."""
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            value = value.strip()
            for fmt in self.CONFIG_DATETIME_FORMATS:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return None

    def _coerce_datetime_value(self, value: Any) -> Optional[datetime]:
        """Convert imported metadata values into datetime objects if possible."""
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        to_py = getattr(value, 'to_pydatetime', None)
        if callable(to_py):
            try:
                potential = to_py()
                if isinstance(potential, datetime):
                    return potential
                return None
            except Exception:
                return None
        if isinstance(value, str):
            return self._parse_config_datetime(value)
        return None

    def _get_timestep_from_data(self) -> int:
        """Get timestep length from imported data files."""
        import pandas as pd

        try:
            flow_files = self.imported_data.get('flow_files', [])
            if not flow_files:
                return 300  # Default 5 minutes

            # Read first file to determine timestep
            date_kwargs = self._get_date_parser_kwargs()
            df = pd.read_csv(flow_files[0], nrows=2, **date_kwargs)
            if len(df) >= 2:
                timestep = (df['Time'].iloc[1] -
                            df['Time'].iloc[0]).total_seconds()
                return int(timestep)
            return 300
        except Exception:
            return 300  # Default to 5 minutes if unable to determine

    def _analyze_head_discharge(self):
        """
        Analyze completed scenarios to determine head-discharge relationships.
        Opens a dialog showing the reverse-engineered H-Q curves.
        Only analyzes scenarios selected in the scenario queue.
        """
        from plato.gui.tabs.analysis_tab_head_discharge import HeadDischargeAnalyzer

        self.log("\n" + "="*60)
        self.log("STARTING HEAD-DISCHARGE RELATIONSHIP ANALYSIS")
        self.log("="*60)

        if not self.analysis_results:
            QMessageBox.warning(
                self,
                "No Results Available",
                "Please run an analysis first before performing head-discharge analysis."
            )
            return

        # Get selected scenarios from queue
        selected_scenarios = self.scenario_queue.get_selected_scenarios()
        if not selected_scenarios:
            QMessageBox.warning(
                self,
                "No Scenarios Selected",
                "Please select one or more scenarios in the queue to analyze.\n\n"
                "Use the checkboxes in the scenario queue to select scenarios."
            )
            return

        self.log(f"Selected {len(selected_scenarios)} scenario(s) from queue")

        # Get scenarios with full results (filtered by selection)
        self.log("Checking for scenarios with full result data...")
        scenarios_with_results = {}
        selected_scenario_names = {s.scenario_name for s in selected_scenarios}

        for scenario_name, result in self.analysis_results.items():
            if scenario_name.startswith('_'):
                continue
            # Check if this scenario is selected
            if scenario_name not in selected_scenario_names:
                continue
            if '_full_result' in result:
                scenarios_with_results[scenario_name] = result
            else:
                self.log(
                    f"  ⚠ {scenario_name} is selected but has no full result data")

        if not scenarios_with_results:
            QMessageBox.warning(
                self,
                "No Detailed Results",
                "None of the selected scenarios have detailed time series data.\n\n"
                "Head-discharge analysis requires full result data including time series.\n"
                "Make sure the selected scenarios have been analyzed."
            )
            return

        self.log(
            f"✓ Found {len(scenarios_with_results)} selected scenario(s) with full results")

        # Create analyzer
        analyzer = HeadDischargeAnalyzer()

        # Get data folder from imported_data (saved in project file)
        if not self.imported_data or not self.imported_data.get('data_folder'):
            QMessageBox.warning(
                self,
                "No Data Folder",
                "Data folder information not found.\n\n"
                "The original data folder path should be saved in the project file.\n"
                "Please re-import your data or check the Data Import tab."
            )
            return

        data_folder = Path(self.imported_data['data_folder'])
        file_type = self.imported_data.get('file_type', 'csv')

        if not data_folder.exists():
            QMessageBox.warning(
                self,
                "Data Folder Not Found",
                f"Data folder not found:\n{data_folder}\n\n"
                "The data may have been moved or deleted.\n"
                "Please update the data folder path in the Data Import tab."
            )
            return

        # Load depth and flow data
        self.log("\nLoading original depth and flow data...")
        self.log(f"Data folder: {data_folder}")

        try:
            if file_type == 'csv':
                # Load flow files
                self.log(f"  Loading flow files from {data_folder}...")
                QApplication.processEvents()  # Update UI

                flow_files = sorted(data_folder.glob('*_Q.csv'))
                if not flow_files:
                    raise ValueError(
                        f"No flow CSV files found in {data_folder}")

                self.log(f"  Found {len(flow_files)} flow file(s)")
                flow_dfs = []
                date_kwargs = self._get_date_parser_kwargs()
                for i, f in enumerate(flow_files, 1):
                    self.log(
                        f"    Reading {f.name} ({i}/{len(flow_files)})...")
                    QApplication.processEvents()  # Update UI
                    df = pd.read_csv(f, **date_kwargs)
                    flow_dfs.append(df)

                self.log("  Merging flow data...")
                QApplication.processEvents()
                flow_data = flow_dfs[0]
                for df in flow_dfs[1:]:
                    flow_data = flow_data.merge(df, on='Time', how='outer')
                flow_data = flow_data.sort_values(
                    'Time').reset_index(drop=True)

                # Load depth files
                self.log(f"  Loading depth files from {data_folder}...")
                QApplication.processEvents()

                depth_files = sorted(data_folder.glob('*_D.csv'))
                if not depth_files:
                    raise ValueError(
                        f"No depth CSV files found in {data_folder}")

                self.log(f"  Found {len(depth_files)} depth file(s)")
                depth_dfs = []
                date_kwargs = self._get_date_parser_kwargs()
                for i, f in enumerate(depth_files, 1):
                    self.log(
                        f"    Reading {f.name} ({i}/{len(depth_files)})...")
                    QApplication.processEvents()  # Update UI
                    df = pd.read_csv(f, **date_kwargs)
                    depth_dfs.append(df)

                self.log("  Merging depth data...")
                QApplication.processEvents()
                depth_data = depth_dfs[0]
                for df in depth_dfs[1:]:
                    depth_data = depth_data.merge(df, on='Time', how='outer')
                depth_data = depth_data.sort_values(
                    'Time').reset_index(drop=True)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

        except Exception as e:
            QMessageBox.warning(
                self,
                "Data Load Error",
                f"Failed to load depth/flow data:\n\n{str(e)}"
            )
            return

        self.log(f"✓ Loaded {len(flow_data)} timesteps of flow data")
        self.log(f"✓ Loaded {len(depth_data)} timesteps of depth data")
        # Skip 'Time'
        self.log(f"✓ Flow columns: {', '.join(flow_data.columns[1:])}")
        # Skip 'Time'
        self.log(f"✓ Depth columns: {', '.join(depth_data.columns[1:])}")

        # Analyze each scenario
        self.log("\n" + "="*60)
        self.log("ANALYZING SCENARIOS")
        self.log("="*60)

        hd_results = {}
        total_scenarios = len(scenarios_with_results)

        for idx, (scenario_name, result) in enumerate(scenarios_with_results.items(), 1):
            self.log(
                f"\n[{idx}/{total_scenarios}] Analyzing scenario: {scenario_name}")
            QApplication.processEvents()  # Update UI

            # Get the overflow link name for this scenario
            # Try to find the original scenario or asset
            self.log(f"  Looking up overflow link...")
            original_scenario = next(
                (s for s in self.scenarios if s.scenario_name == scenario_name or
                 f"{s.scenario_name}_{s.cso_name}" == scenario_name), None)

            if original_scenario:
                # Find the asset to get overflow link
                asset = next((a for a in self.cso_assets if a.name ==
                             original_scenario.cso_name), None)
                if asset and asset.overflow_links:
                    overflow_link = asset.overflow_links[0]
                    self.log(f"  ✓ Found overflow link: {overflow_link}")
                else:
                    self.log(
                        f"  ⚠ Could not find overflow link for {original_scenario.cso_name}")
                    continue
            else:
                self.log(f"  ⚠ Could not find original scenario")
                continue

            # Perform analysis
            self.log(f"  Extracting head-discharge data from remaining spills...")
            QApplication.processEvents()  # Update UI

            hd_result = analyzer.analyze_scenario(
                result,
                overflow_link=overflow_link,
                depth_data=depth_data,
                flow_data=flow_data
            )

            if 'error' in hd_result:
                self.log(f"  ⚠ {hd_result['error']}")
            else:
                hd_results[scenario_name] = hd_result
                self.log(f"  ✓ Fitted equation: {hd_result['equation']}")
                self.log(f"  ✓ Control type: {hd_result['control_type']}")
                self.log(f"  ✓ R² = {hd_result['r_squared']:.4f}")
                self.log(
                    f"  ✓ {hd_result['num_points']} data points from {hd_result['spill_events_analyzed']} spill events")
                self.log(
                    f"  ✓ Head range: {hd_result['head_min']:.2f} - {hd_result['head_max']:.2f} m")
                discharge_range = (f"{hd_result['discharge_min']:.4f} - "
                                   f"{hd_result['discharge_max']:.4f} m³/s")
                self.log(f"  ✓ Discharge range: {discharge_range}")

        if not hd_results:
            QMessageBox.warning(
                self,
                "Analysis Failed",
                "Could not analyze any scenarios.\n\n"
                "Check the log for details."
            )
            return

        # Create comparison table
        self.log("\n" + "="*60)
        self.log("GENERATING COMPARISON TABLE")
        self.log("="*60)
        QApplication.processEvents()  # Update UI

        comparison_df = analyzer.compare_scenarios(hd_results)

        self.log(comparison_df.to_string(index=False))
        self.log(
            f"\n✓ Head-discharge analysis complete for {len(hd_results)} scenario(s)")

        # Show results in a dialog
        self.log("Opening results dialog...")
        QApplication.processEvents()  # Update UI
        self._show_head_discharge_dialog(hd_results, comparison_df)

    def _show_head_discharge_dialog(self, hd_results: Dict, comparison_df):
        """Show head-discharge analysis results in a dialog with plots."""
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                                     QTableWidget, QTableWidgetItem, QHeaderView,
                                     QPushButton, QWidget, QLabel, QFileDialog)
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        import csv

        dialog = QDialog(self)
        dialog.setWindowTitle("Head-Discharge Relationship Analysis")
        dialog.resize(1000, 700)

        layout = QVBoxLayout(dialog)

        # Create tab widget
        tabs = QTabWidget()

        # Tab 1: Comparison table
        table_widget = QTableWidget()
        table_widget.setColumnCount(len(comparison_df.columns))
        table_widget.setRowCount(len(comparison_df))
        table_widget.setHorizontalHeaderLabels(comparison_df.columns.tolist())

        for i, row in comparison_df.iterrows():
            for j, value in enumerate(row):
                table_widget.setItem(i, j, QTableWidgetItem(str(value)))

        table_widget.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        tabs.addTab(table_widget, "📊 Comparison Table")

        # Tab 2+: Individual plots for each scenario with manual drawing capability
        for scenario_name, hd_result in hd_results.items():
            # Create a container widget for the plot and controls
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)

            # Create figure and canvas
            fig = Figure(figsize=(8, 6))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)

            # Store manual points and plot elements
            manual_points = [(0.0, 0.0)]  # Start at origin
            manual_line = None
            manual_scatter = None

            # Plot actual data points
            points = hd_result['head_discharge_points']
            heads = [p[0] for p in points]
            discharges = [p[1] for p in points]
            ax.scatter(heads, discharges, alpha=0.5, s=20, label='Actual Data')

            # Plot fitted curve
            if 'head_range' in hd_result and 'fitted_discharge' in hd_result:
                ax.plot(hd_result['head_range'], hd_result['fitted_discharge'],
                        'r-', linewidth=2, label=f"Fitted: {hd_result['equation']}")

            ax.set_xlabel('Head (m)')
            ax.set_ylabel('Discharge (m³/s)')
            ax.set_title(f'{scenario_name}\nR² = {hd_result["r_squared"]:.4f}')
            ax.legend()
            ax.grid(True, alpha=0.3)

            # Add annotation with key parameters
            textstr = f"Overflow Link: {hd_result.get('overflow_link', 'Unknown')}\n"
            textstr += f"Control Type: {hd_result.get('control_type', 'Unknown')}\n"
            textstr += f"Data Points: {hd_result['num_points']}"
            ax.text(0.02, 0.98, textstr, transform=ax.transAxes,
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

            fig.tight_layout()

            # Add canvas to layout
            tab_layout.addWidget(canvas)

            # Control panel for manual drawing
            control_panel = QWidget()
            control_layout = QHBoxLayout(control_panel)

            # Status label
            status_label = QLabel("Manual curve: 1 point (0, 0)")
            control_layout.addWidget(status_label)

            control_layout.addStretch()

            # Clear manual curve button
            clear_btn = QPushButton("Clear Manual Curve")
            clear_btn.setEnabled(False)

            # Copy to clipboard buttons
            export_raw_btn = QPushButton("📋 Copy Raw Data")
            export_raw_btn.setToolTip(
                "Copy raw head-discharge data to clipboard")
            export_manual_btn = QPushButton("📋 Copy Manual Curve")
            export_manual_btn.setToolTip(
                "Copy manually drawn curve points to clipboard")
            export_manual_btn.setEnabled(False)

            control_layout.addWidget(clear_btn)
            control_layout.addWidget(export_raw_btn)
            control_layout.addWidget(export_manual_btn)

            tab_layout.addWidget(control_panel)

            # Define click handler for manual drawing
            def on_click(event):
                nonlocal manual_line, manual_scatter
                if event.inaxes != ax:
                    return

                # Add point
                x, y = event.xdata, event.ydata
                manual_points.append((x, y))

                # Update plot
                # Remove old manual drawings
                if manual_line:
                    manual_line.remove()
                if manual_scatter:
                    manual_scatter.remove()

                # Draw new manual curve
                manual_heads = [p[0] for p in manual_points]
                manual_discharges = [p[1] for p in manual_points]
                manual_line, = ax.plot(manual_heads, manual_discharges,
                                       'g-', linewidth=2, label='Manual Curve',
                                       marker='o', markersize=6)
                manual_scatter = ax.scatter([x], [y], c='green', s=100,
                                            marker='x', linewidths=2, zorder=10)

                # Update legend
                ax.legend()
                canvas.draw()

                # Update status
                status_label.setText(
                    f"Manual curve: {len(manual_points)} points")
                clear_btn.setEnabled(True)
                export_manual_btn.setEnabled(True)

            # Define clear handler
            def on_clear():
                nonlocal manual_line, manual_scatter

                # Reset points to origin only
                manual_points.clear()
                manual_points.append((0.0, 0.0))

                # Remove drawings
                if manual_line:
                    manual_line.remove()
                    manual_line = None
                if manual_scatter:
                    manual_scatter.remove()
                    manual_scatter = None

                # Update legend
                ax.legend()
                canvas.draw()

                # Update UI
                status_label.setText("Manual curve: 1 point (0, 0)")
                clear_btn.setEnabled(False)
                export_manual_btn.setEnabled(False)

            # Define copy raw data to clipboard handler
            def on_export_raw():
                try:
                    # Build CSV text
                    lines = ['Head (m)\tDischarge (m³/s)']
                    for h, q in hd_result['head_discharge_points']:
                        lines.append(f'{h}\t{q}')

                    csv_text = '\n'.join(lines)

                    # Copy to clipboard
                    from PyQt6.QtWidgets import QApplication
                    clipboard = QApplication.clipboard()
                    clipboard.setText(csv_text)

                    self.log(
                        f"✓ Copied {len(hd_result['head_discharge_points'])} raw data points to clipboard")
                    QMessageBox.information(dialog, "Copied to Clipboard",
                                            f"Raw head-discharge data copied to clipboard!\n\n"
                                            f"{len(hd_result['head_discharge_points'])} data points\n\n"
                                            f"Paste into Excel or any spreadsheet application.")
                except Exception as e:
                    QMessageBox.warning(dialog, "Copy Failed",
                                        f"Failed to copy data to clipboard:\n{str(e)}")

            # Define copy manual curve to clipboard handler
            def on_export_manual():
                try:
                    # Build CSV text
                    lines = ['Head (m)\tDischarge (m³/s)']
                    for h, q in manual_points:
                        lines.append(f'{h}\t{q}')

                    csv_text = '\n'.join(lines)

                    # Copy to clipboard
                    from PyQt6.QtWidgets import QApplication
                    clipboard = QApplication.clipboard()
                    clipboard.setText(csv_text)

                    self.log(
                        f"✓ Copied {len(manual_points)} manual curve points to clipboard")
                    QMessageBox.information(dialog, "Copied to Clipboard",
                                            f"Manual curve data copied to clipboard!\n\n"
                                            f"{len(manual_points)} points\n\n"
                                            f"Paste into Excel or any spreadsheet application.")
                except Exception as e:
                    QMessageBox.warning(dialog, "Copy Failed",
                                        f"Failed to copy data to clipboard:\n{str(e)}")

            # Connect handlers
            canvas.mpl_connect('button_press_event', on_click)
            clear_btn.clicked.connect(on_clear)
            export_raw_btn.clicked.connect(on_export_raw)
            export_manual_btn.clicked.connect(on_export_manual)

            tabs.addTab(tab_widget, scenario_name[:20])  # Truncate long names

        layout.addWidget(tabs)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()
