"""
Main application window for PLATO GUI
"""

from plato.gui.tabs.data_import_tab import DataImportTab
from plato.gui.tabs.results_tab import ResultsTab
from plato.gui.tabs.analysis_tab import AnalysisTab
from plato.gui.tabs.analysis_scenarios_tab import AnalysisScenariosTab
from plato.gui.tabs.analysis_configurations_tab import AnalysisConfigurationsTab
from plato.gui.tabs.cso_assets_tab import CSOAssetsTab
from plato.gui.tabs.wwtw_assets_tab import WWTWAssetsTab
from plato.gui.tabs.catchments_tab import CatchmentsTab
# from plato.gui.tabs.cso_configuration_tab import CSOConfigurationTab
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import asdict, is_dataclass
import pandas as pd

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QAction


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime, pandas objects, and dataclasses."""

    def default(self, o):  # Match base class parameter name
        # Handle datetime objects
        if isinstance(o, datetime):
            return o.isoformat()

        # Handle pandas Timestamp
        if hasattr(o, 'isoformat') and not isinstance(o, datetime):
            return o.isoformat()

        # Handle pandas DataFrame
        if isinstance(o, pd.DataFrame):
            # Convert to dict with orient='records' for easy reloading
            return {
                '__type__': 'DataFrame',
                'data': o.to_dict(orient='records'),
                'columns': list(o.columns)
            }

        # Handle pandas Series
        if isinstance(o, pd.Series):
            return {
                '__type__': 'Series',
                'data': o.to_dict()
            }

        # Handle dataclass objects (CSOAnalysisResult, SpillEvent, etc.)
        if is_dataclass(o) and not isinstance(o, type):
            return {
                '__type__': 'dataclass',
                '__class__': o.__class__.__name__,
                'data': asdict(o)
            }

        return super().default(o)


class PlatoMainWindow(QMainWindow):
    """Main application window with tabbed interface."""

    def __init__(self):
        super().__init__()
        self.current_project_file: Optional[str] = None
        self.project_data: Dict[str, Any] = {}
        self.settings = QSettings('Tetra Tech', 'PLATO')

        self.init_ui()
        self.create_menu_bar()
        self.load_recent_settings()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('PLATO - Storage Modeller')
        self.setGeometry(100, 100, 1400, 900)

        # Create central widget with tab layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Initialize tabs
        self.data_import_tab = DataImportTab(self)
        # self.cso_config_tab = CSOConfigurationTab(self)
        self.cso_assets_tab = CSOAssetsTab(self)
        self.wwtw_assets_tab = WWTWAssetsTab(self)
        self.catchments_tab = CatchmentsTab(self)
        self.analysis_configs_tab = AnalysisConfigurationsTab(self)
        self.analysis_scenarios_tab = AnalysisScenariosTab(self)
        self.analysis_tab = AnalysisTab(self)
        self.results_tab = ResultsTab(self)

        # Add tabs
        self.tabs.addTab(self.data_import_tab, "📁 Data Import")
        # self.tabs.addTab(self.cso_config_tab, "⚙️ CSO Configuration")
        self.tabs.addTab(self.cso_assets_tab, "🏢 CSO Assets")
        self.tabs.addTab(self.catchments_tab, "🔗 Catchments")
        self.tabs.addTab(self.wwtw_assets_tab, "🏭 WwTW Assets")
        self.tabs.addTab(self.analysis_configs_tab,
                         "📋 Analysis Configurations")
        self.tabs.addTab(self.analysis_scenarios_tab, "🔬 Analysis Scenarios")
        self.tabs.addTab(self.analysis_tab, "▶️ Analysis")
        self.tabs.addTab(self.results_tab, "📊 Results")

        layout.addWidget(self.tabs)

        # Connect signals between tabs
        self.connect_tab_signals()

        # Initialize tab states - disable tabs until data is available
        self.update_tab_availability()

        # Status bar
        self.statusBar().showMessage('Ready')

    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('&File')

        new_action = QAction('&New Project', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)

        open_action = QAction('&Open Project...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)

        save_action = QAction('&Save Project', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)

        save_as_action = QAction('Save Project &As...', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)

        # file_menu.addSeparator()

        # import_data_action = QAction('&Import ICM Data...', self)
        # import_data_action.setShortcut('Ctrl+I')
        # import_data_action.triggered.connect(self.show_import_tab)
        # file_menu.addAction(import_data_action)

        file_menu.addSeparator()

        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # # Run menu
        # run_menu = menubar.addMenu('&Run')

        # start_analysis_action = QAction('&Start Analysis', self)
        # start_analysis_action.setShortcut('F5')
        # start_analysis_action.triggered.connect(self.start_analysis)
        # run_menu.addAction(start_analysis_action)

        # cancel_analysis_action = QAction('&Cancel Analysis', self)
        # cancel_analysis_action.setShortcut('Esc')
        # cancel_analysis_action.triggered.connect(self.cancel_analysis)
        # run_menu.addAction(cancel_analysis_action)

        # # View menu
        # view_menu = menubar.addMenu('&View')

        # data_tab_action = QAction('Data Import', self)
        # data_tab_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        # view_menu.addAction(data_tab_action)

        # config_tab_action = QAction('CSO Configuration', self)
        # config_tab_action.triggered.connect(
        #     lambda: self.tabs.setCurrentIndex(1))
        # view_menu.addAction(config_tab_action)

        # analysis_tab_action = QAction('Analysis', self)
        # analysis_tab_action.triggered.connect(
        #     lambda: self.tabs.setCurrentIndex(2))
        # view_menu.addAction(analysis_tab_action)

        # results_tab_action = QAction('Results', self)
        # results_tab_action.triggered.connect(
        #     lambda: self.tabs.setCurrentIndex(3))
        # view_menu.addAction(results_tab_action)

        # Help menu
        help_menu = menubar.addMenu('&Help')

        about_action = QAction('&About PLATO', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # docs_action = QAction('&Documentation', self)
        # docs_action.triggered.connect(self.show_documentation)
        # help_menu.addAction(docs_action)

    def connect_tab_signals(self):
        """Connect signals between different tabs."""
        # self.data_import_tab.data_imported.connect(
        #     self.cso_config_tab.on_data_imported)
        self.analysis_tab.analysis_completed.connect(
            self.results_tab.on_analysis_completed)
        # Enable Results tab after analysis completes
        self.analysis_tab.analysis_completed.connect(
            lambda: self.update_tab_availability())
        # self.cso_config_tab.config_validated.connect(
        #     self.analysis_tab.on_config_ready)

        # Connect data import to CSO assets (populate link dropdowns)
        self.data_import_tab.data_imported.connect(
            self.on_data_imported_for_assets)

        # Connect data import to WwTW assets (populate link dropdowns)
        self.data_import_tab.data_imported.connect(
            self.on_data_imported_for_wwtw_assets)

        # Connect CSO assets to analysis scenarios (populate CSO dropdown)
        self.cso_assets_tab.assets_changed.connect(
            lambda: self.analysis_scenarios_tab.set_available_csos(
                self.cso_assets_tab.get_asset_names(),
                self.cso_assets_tab.get_assets()
            )
        )

        # Connect CSO assets to catchments tab (update available CSOs)
        self.cso_assets_tab.assets_changed.connect(
            lambda: self.catchments_tab.set_cso_assets(
                self.cso_assets_tab.get_assets()
            )
        )

        # Connect WwTW assets to analysis scenarios (populate WwTW dropdown)
        self.wwtw_assets_tab.assets_changed.connect(
            lambda: self.analysis_scenarios_tab.set_available_wwtws(
                [wwtw.name for wwtw in self.wwtw_assets_tab.get_assets()],
                self.wwtw_assets_tab.get_assets()
            )
        )

        # Connect catchments to analysis scenarios (populate catchment dropdown)
        self.catchments_tab.catchments_changed.connect(
            lambda: self.analysis_scenarios_tab.set_available_catchments(
                self.catchments_tab.get_catchment_names(),
                self.catchments_tab.get_catchments()
            )
        )

        # Connect analysis configurations to analysis scenarios (populate config dropdown)
        self.analysis_configs_tab.configs_changed.connect(
            lambda configs: self.analysis_scenarios_tab.set_available_configurations(
                self.analysis_configs_tab.get_configuration_names(),
                configs
            )
        )

        # Connect data import to analysis configurations (set date range bounds)
        self.data_import_tab.data_imported.connect(
            self.on_data_imported_for_configs)

        # Connect data import to analysis tab (for imported_data dictionary)
        self.data_import_tab.data_imported.connect(
            self.on_data_imported_for_analysis)

        # Connect signals to update tab availability
        self.data_import_tab.data_imported.connect(
            lambda: self.update_tab_availability())
        self.cso_assets_tab.assets_changed.connect(
            lambda: self.update_tab_availability())
        self.wwtw_assets_tab.assets_changed.connect(
            lambda: self.update_tab_availability())
        self.analysis_configs_tab.configs_changed.connect(
            lambda: self.update_tab_availability())
        self.analysis_scenarios_tab.scenarios_changed.connect(
            lambda: self.update_tab_availability())

        # Connect scenarios to analysis tab (enable start button when scenarios exist)
        self.analysis_scenarios_tab.scenarios_changed.connect(
            lambda: self.analysis_tab.set_scenarios(
                self.analysis_scenarios_tab.get_scenarios(),
                self.cso_assets_tab.get_assets(),
                self.analysis_configs_tab.get_configurations(),
                self.catchments_tab.get_catchments()
            )
        )

        # Connect scenarios to results tab (for orphaned results cleanup)
        self.analysis_scenarios_tab.scenarios_changed.connect(
            lambda: self.results_tab.set_available_scenarios(
                self.analysis_scenarios_tab.get_scenarios()
            )
        )

        # Initialize with any existing data
        self._sync_initial_data()

    def _sync_initial_data(self):
        """Push any existing data from tabs to scenarios tab on startup."""
        # Sync CSO assets
        if self.cso_assets_tab.get_assets():
            self.analysis_scenarios_tab.set_available_csos(
                self.cso_assets_tab.get_asset_names(),
                self.cso_assets_tab.get_assets()
            )

        # Sync WwTW assets
        if self.wwtw_assets_tab.get_assets():
            self.analysis_scenarios_tab.set_available_wwtws(
                [asset.name for asset in self.wwtw_assets_tab.get_assets()],
                self.wwtw_assets_tab.get_assets()
            )

        # Sync scenarios to results tab
        if self.analysis_scenarios_tab.get_scenarios():
            self.results_tab.set_available_scenarios(
                self.analysis_scenarios_tab.get_scenarios()
            )

        # Sync catchments
        if self.catchments_tab.get_catchments():
            self.analysis_scenarios_tab.set_available_catchments(
                self.catchments_tab.get_catchment_names(),
                self.catchments_tab.get_catchments()
            )

        # Sync configs
        if self.analysis_configs_tab.get_configurations():
            self.analysis_scenarios_tab.set_available_configurations(
                self.analysis_configs_tab.get_configuration_names(),
                self.analysis_configs_tab.get_configurations()
            )

    def on_data_imported_for_assets(self, data_info: dict):
        """Handle data import to update available links in CSO Assets tab."""
        # Extract link names from imported data
        # Data import emits 'all_links' with list of link names
        links = data_info.get('all_links', [])
        if links:
            self.cso_assets_tab.set_available_links(links)
            # Validate existing assets against new data
            self.cso_assets_tab.validate_assets_against_data(links)

    def on_data_imported_for_wwtw_assets(self, data_info: dict):
        """Handle data import to update available links in WwTW Assets tab."""
        # Extract link names from imported data
        links = data_info.get('all_links', [])
        if links:
            self.wwtw_assets_tab.set_available_links(links)
            # Note: validate_assets() is called manually by user, not automatically

    def on_data_imported_for_configs(self, data_info: dict):
        """Handle data import to update date range bounds in Analysis Configurations tab."""
        # Extract date range from imported data
        # Data import sends 'data_start' and 'data_end' as pandas Timestamps
        data_start = data_info.get('data_start')
        data_end = data_info.get('data_end')

        if data_start and data_end:
            # Convert pandas Timestamps to Python datetime objects
            min_date = data_start.to_pydatetime() if hasattr(
                data_start, 'to_pydatetime') else data_start
            max_date = data_end.to_pydatetime() if hasattr(
                data_end, 'to_pydatetime') else data_end
            self.analysis_configs_tab.set_date_range(min_date, max_date)
            # Validate existing configs against new date range
            self.analysis_configs_tab.validate_configs(min_date, max_date)

    def on_data_imported_for_analysis(self, data_info: dict):
        """Forward data import info to analysis tab for head-discharge analysis."""
        if self.analysis_tab:
            self.analysis_tab.imported_data = data_info

    def update_tab_availability(self):
        """Update which tabs are enabled based on data and configuration state."""

        # Get tab indices (CSO Configuration is commented out, so indices shifted)
        data_import_idx = 0
        cso_assets_idx = 1
        catchments_idx = 2
        wwtw_assets_idx = 3
        analysis_configs_idx = 4
        analysis_scenarios_idx = 5
        analysis_idx = 6
        results_idx = 7

        # Data Import is always available

        # Check if data has been imported
        has_data = hasattr(self.data_import_tab, 'imported_data') and bool(
            self.data_import_tab.imported_data)

        # Enable/disable tabs based on data availability
        # CSO Assets, WwTW Assets, and Analysis Configs all require data first
        self.tabs.setTabEnabled(cso_assets_idx, has_data)
        self.tabs.setTabEnabled(wwtw_assets_idx, has_data)
        self.tabs.setTabEnabled(analysis_configs_idx, has_data)

        if not has_data:
            # If no data, disable everything downstream
            self.tabs.setTabEnabled(catchments_idx, False)
            self.tabs.setTabEnabled(analysis_scenarios_idx, False)
            self.tabs.setTabEnabled(analysis_idx, False)
            self.tabs.setTabEnabled(results_idx, False)
            self.statusBar().showMessage('⚠️ Import data to get started')
            return

        # Check if we have at least one valid CSO asset
        all_cso_assets = self.cso_assets_tab.get_assets()
        valid_cso_assets = [asset for asset in all_cso_assets
                            if self.cso_assets_tab.is_asset_valid(asset)]
        has_valid_cso_assets = len(valid_cso_assets) > 0
        has_multiple_cso_assets = len(valid_cso_assets) >= 2

        # Check if we have at least one valid WwTW asset
        all_wwtw_assets = self.wwtw_assets_tab.get_assets()
        has_valid_wwtw_assets = len(all_wwtw_assets) > 0

        # We can create scenarios if we have either CSO or WwTW assets
        has_valid_assets = has_valid_cso_assets or has_valid_wwtw_assets

        # Catchments tab requires at least 2 valid CSO assets (not just data)
        self.tabs.setTabEnabled(catchments_idx, has_multiple_cso_assets)

        # Check if we have at least one valid analysis configuration
        all_configs = self.analysis_configs_tab.get_configurations()
        valid_configs = [config for config in all_configs
                         if self.analysis_configs_tab.is_config_valid(config)]
        has_valid_configs = len(valid_configs) > 0

        # Analysis Scenarios requires BOTH valid assets AND valid configs
        can_create_scenarios = has_valid_assets and has_valid_configs

        self.tabs.setTabEnabled(analysis_scenarios_idx, can_create_scenarios)

        # Check if we have any valid scenarios
        # (A scenario is valid if its referenced CSO/Catchment/WwTW and Config both exist and are valid)
        has_valid_scenarios = False
        if can_create_scenarios:
            scenarios = self.analysis_scenarios_tab.get_scenarios()
            valid_cso_asset_names = {asset.name for asset in valid_cso_assets}
            valid_wwtw_asset_names = {asset.name for asset in all_wwtw_assets}
            valid_config_names = {config.name for config in valid_configs}
            valid_catchment_names = {
                catchment.name for catchment in self.catchments_tab.get_catchments()}

            for scenario in scenarios:
                # Check if config is valid
                if scenario.config_name not in valid_config_names:
                    continue

                # Check if scenario references valid CSO, catchment, or WwTW
                is_valid = False
                if scenario.cso_name:  # Regular CSO scenario
                    is_valid = scenario.cso_name in valid_cso_asset_names
                elif scenario.catchment_name:  # Catchment scenario
                    is_valid = scenario.catchment_name in valid_catchment_names
                elif scenario.wwtw_name:  # WwTW scenario
                    is_valid = scenario.wwtw_name in valid_wwtw_asset_names

                if is_valid:
                    has_valid_scenarios = True
                    break

        # Analysis requires at least one valid scenario
        self.tabs.setTabEnabled(analysis_idx, has_valid_scenarios)

        # Results tab requires completed analysis with results
        has_analysis_results = hasattr(self.analysis_tab, 'analysis_results') and bool(
            self.analysis_tab.analysis_results)
        self.tabs.setTabEnabled(results_idx, has_analysis_results)

        # Update status message
        if not has_valid_assets and not has_valid_configs:
            self.statusBar().showMessage(
                '⚠️ Define at least one CSO Asset and one Analysis Configuration')
        elif not has_valid_assets:
            self.statusBar().showMessage(
                '⚠️ Define at least one valid CSO Asset')
        elif not has_valid_configs:
            self.statusBar().showMessage(
                '⚠️ Define at least one valid Analysis Configuration')
        elif not has_valid_scenarios:
            self.statusBar().showMessage(
                '⚠️ Create at least one Analysis Scenario to run analysis')
        else:
            # Count valid scenarios (CSO, catchment, and WwTW)
            valid_scenario_count = 0
            if can_create_scenarios:
                scenarios = self.analysis_scenarios_tab.get_scenarios()
                valid_cso_asset_names = {
                    asset.name for asset in valid_cso_assets}
                valid_wwtw_asset_names = {
                    asset.name for asset in all_wwtw_assets}
                valid_config_names = {config.name for config in valid_configs}
                valid_catchment_names = {
                    catchment.name for catchment in self.catchments_tab.get_catchments()}

                for scenario in scenarios:
                    if scenario.config_name not in valid_config_names:
                        continue
                    if scenario.cso_name and scenario.cso_name in valid_cso_asset_names:
                        valid_scenario_count += 1
                    elif scenario.catchment_name and scenario.catchment_name in valid_catchment_names:
                        valid_scenario_count += 1
                    elif scenario.wwtw_name and scenario.wwtw_name in valid_wwtw_asset_names:
                        valid_scenario_count += 1

            total_assets = len(valid_cso_assets) + len(all_wwtw_assets)
            self.statusBar().showMessage(
                f'✓ Ready to analyze: {total_assets} assets '
                f'({len(valid_cso_assets)} CSO, {len(all_wwtw_assets)} WwTW), '
                f'{len(valid_configs)} configs, {valid_scenario_count} scenarios')

    # Project management methods
    def new_project(self):
        """Create a new project."""
        if self.project_data and not self.confirm_discard_changes():
            return

        self.current_project_file = None
        self.project_data = {}

        # Reset tabs with reset() methods
        self.data_import_tab.reset()
        # self.cso_config_tab.reset()
        self.analysis_tab.reset()
        self.results_tab.reset()

        # Reset tabs by loading empty state (clears all data)
        self.cso_assets_tab.load_state({})
        self.wwtw_assets_tab.load_state({})
        self.catchments_tab.load_state({})
        self.analysis_configs_tab.load_state({})
        self.analysis_scenarios_tab.load_state({})

        self.setWindowTitle('PLATO - Storage Modeller [New Project]')
        self.statusBar().showMessage('New project created')

    def open_project(self):
        """Open an existing project file."""
        if self.project_data and not self.confirm_discard_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Open PLATO Project',
            self.settings.value('last_project_dir', ''),
            'PLATO Project Files (*.plato);;All Files (*.*)'
        )

        if file_path:
            self.load_project(file_path)

    def load_project(self, file_path: str):
        """Load project data from file."""
        try:
            with open(file_path, 'r') as f:
                self.project_data = json.load(f)

            self.current_project_file = file_path
            self.settings.setValue(
                'last_project_dir', str(Path(file_path).parent))

            # Load data import (all versions)
            if 'data_import' in self.project_data:
                self.data_import_tab.load_state(
                    self.project_data['data_import'])

            # Load new architecture tabs (version 2.0+)
            if 'cso_assets' in self.project_data:
                self.cso_assets_tab.load_state(self.project_data['cso_assets'])
            if 'wwtw_assets' in self.project_data:
                self.wwtw_assets_tab.load_state(
                    self.project_data['wwtw_assets'])
            if 'catchments' in self.project_data:
                self.catchments_tab.load_state(self.project_data['catchments'])
            if 'analysis_configs' in self.project_data:
                self.analysis_configs_tab.load_state(
                    self.project_data['analysis_configs'])

            # Sync loaded data to scenarios tab BEFORE loading scenarios
            # This ensures available_catchments is populated for hierarchical scenarios
            self._sync_initial_data()

            if 'analysis_scenarios' in self.project_data:
                self.analysis_scenarios_tab.load_state(
                    self.project_data['analysis_scenarios'])

            # # Load legacy tab (version 1.0 compatibility)
            # if 'cso_config' in self.project_data:
            #     self.cso_config_tab.load_state(self.project_data['cso_config'])

            # Load analysis and results (all versions)
            if 'analysis' in self.project_data:
                self.analysis_tab.load_state(self.project_data['analysis'])
            if 'results' in self.project_data:
                self.results_tab.load_state(self.project_data['results'])

            self.setWindowTitle(
                f'PLATO - Storage Modeller [{Path(file_path).name}]')
            self.statusBar().showMessage(f'Project loaded: {file_path}')

        except Exception as e:
            QMessageBox.critical(
                self,
                'Error Loading Project',
                f'Failed to load project file:\n{str(e)}'
            )

    def save_project(self) -> bool:
        """Save the current project. Returns True if saved successfully, False if cancelled."""
        if self.current_project_file:
            return self.save_project_to_file(self.current_project_file)
        else:
            return self.save_project_as()

    def save_project_as(self) -> bool:
        """Save the project to a new file. Returns True if saved, False if cancelled."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Save PLATO Project As',
            self.settings.value('last_project_dir', ''),
            'PLATO Project Files (*.plato);;All Files (*.*)'
        )

        if file_path:
            if not file_path.endswith('.plato'):
                file_path += '.plato'
            return self.save_project_to_file(file_path)

        return False  # User cancelled

    def save_project_to_file(self, file_path: str) -> bool:
        """Save project data to specified file. Returns True on success, False on error."""
        """Save project data to specified file."""
        try:
            self.project_data = {
                'version': '2.0',  # Updated for new three-level architecture
                'saved_at': datetime.now().isoformat(),
                'data_import': self.data_import_tab.get_state(),
                # 'cso_config': self.cso_config_tab.get_state(),  # Legacy tab
                'cso_assets': self.cso_assets_tab.get_state(),  # New architecture
                'wwtw_assets': self.wwtw_assets_tab.get_state(),  # WwTW assets
                'catchments': self.catchments_tab.get_state(),  # Catchment groups
                'analysis_configs': self.analysis_configs_tab.get_state(),  # New architecture
                'analysis_scenarios': self.analysis_scenarios_tab.get_state(),  # New architecture
                'analysis': self.analysis_tab.get_state(),
                'results': self.results_tab.get_state()
            }

            with open(file_path, 'w') as f:
                json.dump(self.project_data, f, indent=2, cls=DateTimeEncoder)

            self.current_project_file = file_path
            self.settings.setValue(
                'last_project_dir', str(Path(file_path).parent))

            self.setWindowTitle(
                f'PLATO - Storage Modeller [{Path(file_path).name}]')
            self.statusBar().showMessage(f'Project saved: {file_path}')

            return True  # Success

        except Exception as e:
            QMessageBox.critical(
                self,
                'Error Saving Project',
                f'Failed to save project file:\n{str(e)}'
            )
            return False  # Error occurred

    def confirm_discard_changes(self) -> bool:
        """Ask user to confirm discarding unsaved changes."""
        reply = QMessageBox.question(
            self,
            'Unsaved Changes',
            'You have unsaved changes. Do you want to continue?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    # Menu action methods
    def show_import_tab(self):
        """Switch to the data import tab."""
        self.tabs.setCurrentIndex(0)

    def start_analysis(self):
        """Start the analysis from current configuration."""
        self.tabs.setCurrentIndex(2)
        self.analysis_tab.start_analysis()

    def cancel_analysis(self):
        """Cancel the running analysis."""
        self.analysis_tab.cancel_analysis()

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            'About PLATO',
            '<h2>PLATO - Storage Modeller</h2>'
            '<p>An iterative storage optimiser and pass-forward flow time-series '
            'assessment tool for Combined Sewer Overflow (CSO) analysis.</p>'
            '<p>Version 4.0 - PyQt6 Edition</p>'
            '<p>© Tetra Tech, Inc.</p>'
        )

    def show_documentation(self):
        """Open documentation file."""
        doc_path = Path(__file__).parent.parent.parent / 'docs' / 'README.md'
        if doc_path.exists():
            os.startfile(str(doc_path))
        else:
            QMessageBox.information(
                self,
                'Documentation',
                'Documentation file not found. Please check the docs folder.'
            )

    def load_recent_settings(self):
        """Load recent application settings."""
        geometry = self.settings.value('window_geometry')
        if geometry:
            self.restoreGeometry(geometry)

    def closeEvent(self, event):
        """Handle window close event."""
        if self.project_data and not self.confirm_discard_changes():
            event.ignore()
            return

        self.settings.setValue('window_geometry', self.saveGeometry())

        if hasattr(self.analysis_tab, 'worker_thread') and self.analysis_tab.worker_thread:
            self.analysis_tab.cancel_analysis()

        event.accept()
