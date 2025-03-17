import os
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QTableWidget, QMessageBox, QAbstractItemView, QLineEdit, QFileDialog
# from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QStandardItemModel, QPalette, QColor
from ui_elements.ui_flowbot_dialog_fsm_raw_data_settings_base import Ui_Dialog
from flowbot_management import fsmProject, fsmInstall
from flowbot_helper import generate_shape
from flowbot_graphing import graphPipeShapeDefinition
import pandas as pd
from datetime import datetime


class flowbot_dialog_fsm_raw_data_settings(QtWidgets.QDialog, Ui_Dialog):

    def __init__(self, install: fsmInstall, fsm_project: fsmProject, parent=None):
        """Constructor."""
        super(flowbot_dialog_fsm_raw_data_settings, self).__init__(parent)
        self.setupUi(self)

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)
        self.project = fsm_project
        self.inst = install
        self.raw = self.project.get_raw_data_by_install(self.inst.install_id)
        self.pipe_settings_grid_layout.setAlignment(Qt.AlignTop)
        self.pipeShapeGraph = graphPipeShapeDefinition(
            self.plotCanvas_pipe_shape_definition)
        self.btn_set_folder.clicked.connect(self.browse_for_folder)

        self.setupTabs()

        self.tableWidget_rainfall_timing.cellChanged.connect(
            self.onDefaultCellChanged)
        self.tableWidget_pumplogger_timing.cellChanged.connect(self.onDefaultCellChanged)
        self.tableWidget_pumplogger_added_onoffs.cellChanged.connect(self.onDefaultCellChanged)
        self.tableWidget_pipe_shape_definition.cellChanged.connect(
            self.onPipeShapeDefCellChanged)
        self.tableWidget_silt_depths.cellChanged.connect(
            self.onDefaultCellChanged)
        self.tableWidget_depth_corrections.cellChanged.connect(
            self.onDepthCorrectionCellChanged)
        self.tableWidget_velocity_corrections.cellChanged.connect(
            self.onDefaultCellChanged)
        self.tableWidget_timing_corrections.cellChanged.connect(
            self.onDefaultCellChanged)

        self.comboBox_pipe_shape.currentIndexChanged.connect(
            self.pipeShapeChanged)
        self.spinBox_intervals.valueChanged.connect(self.pipeShapeChanged)
        self.spinBox_width.editingFinished.connect(self.pipeWidthChanged)
        self.spinBox_height.editingFinished.connect(self.pipeHeightChanged)

        self.lastValidShape = self.comboBox_pipe_shape.currentText()
        self.lastValidWidth = self.spinBox_width.value()
        self.lastValidHeight = self.spinBox_height.value()

        self.pipeShapeChanged()
        #

    def browse_for_folder(self):
        
        initialPath = ''
        if self.raw is not None:
            if os.path.exists(self.raw.file_path):
                initialPath = self.raw.file_path
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder', initialPath)
        if folder_path:
            self.txtFolderLocation.setText(folder_path)

    def eventFilter(self, o, e):
        if e.type() == QtCore.QEvent.Type.DragEnter:
            if o in (
                self.txtRainfallFileNameFormat,
                self.txtPumpLoggerFileNameFormat,
                self.txtDepthFileNameFormat,
                self.txtVelocityFileNameFormat,
                self.txtBatteryFileNameFormat,
            ):
                source_item = QStandardItemModel()
                source_item.dropMimeData(
                    e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())
                if source_item.item(0, 0):
                    e.accept()
                    return True
        elif e.type() == QtCore.QEvent.Type.DragMove:
            if o in (self.txtRainfallFileNameFormat, self.txtPumpLoggerFileNameFormat, self.txtDepthFileNameFormat, self.txtVelocityFileNameFormat, self.txtBatteryFileNameFormat):
                # Update the cursor position dynamically
                cursor_position = self.get_cursor_position(o, e.pos())
                o.setCursorPosition(cursor_position)
                o.setSelection(cursor_position, 1)
                return True
        elif e.type() == QtCore.QEvent.Type.DragLeave:
            if o in (self.txtRainfallFileNameFormat, self.txtPumpLoggerFileNameFormat, self.txtDepthFileNameFormat, self.txtVelocityFileNameFormat, self.txtBatteryFileNameFormat):
                o.deselect()
        elif e.type() == QtCore.QEvent.Type.Drop:
            if o in (self.txtRainfallFileNameFormat, self.txtPumpLoggerFileNameFormat, self.txtDepthFileNameFormat, self.txtVelocityFileNameFormat, self.txtBatteryFileNameFormat):
                self.custom_drop_action(o, e)
                o.deselect()
                return True
            else:
                return False
        return super().eventFilter(o, e)

    def get_cursor_position(self, line_edit, pos):
        """Get the cursor position from the drop location."""
        cursor_position = line_edit.cursorPositionAt(pos)
        return cursor_position

    def custom_drop_action(self, o, e):
        # Get the position of the drop
        cursor_position = self.get_cursor_position(o, e.pos())

        # Extract the dragged text
        model = QStandardItemModel()
        if model.dropMimeData(e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex()):
            item = model.item(0, 0)
            if item:
                # Insert text at the cursor position
                current_text = o.text()
                dropped_text = self.mapIdentifierToFlag(item.text())
                new_text = (
                    current_text[:cursor_position] +
                    dropped_text +
                    current_text[cursor_position:]
                )
                o.setText(new_text)
                if o.objectName() == 'txtRainfallFileNameFormat':
                    self.updateRainfallFile()
                elif o.objectName() == 'txtDepthFileNameFormat':
                    self.updateDepthFile()
                elif o.objectName() == 'txtVelocityFileNameFormat':
                    self.updateVelocityFile()
                elif o.objectName() == 'txtBatteryFileNameFormat':
                    self.updateBatteryFile()
                elif o.objectName() == "txtPumpLoggerFileNameFormat":
                    self.updatePumpLoggerFile()

    def mapIdentifierToFlag(self, ident_text: str) -> str:

        map_dict = {'PMAC ID': '{pmac_id}', 'Asset ID': '{ast_id}', 'Install ID': '{inst_id}',
                    'Client Ref': '{cl_ref}', 'Site ID': '{site_id}', 'Project ID': '{prj_id}'}
        return map_dict[ident_text]

    def decode_file_format(self, file_format: str) -> str:

        if '{pmac_id}' in file_format:
            file_format = file_format.replace('{pmac_id}', self.project.get_monitor(
                self.inst.install_monitor_asset_id).pmac_id)
        if '{ast_id}' in file_format:
            file_format = file_format.replace(
                '{ast_id}', self.inst.install_monitor_asset_id)
        if '{inst_id}' in file_format:
            file_format = file_format.replace(
                '{inst_id}', self.inst.install_id)
        if '{cl_ref}' in file_format:
            file_format = file_format.replace('{cl_ref}', self.inst.client_ref)
        if '{site_id}' in file_format:
            file_format = file_format.replace(
                '{site_id}', self.inst.install_site_id)
        if '{prj_id}' in file_format:
            file_format = file_format.replace(
                '{prj_id}', self.project.job_number)
        return file_format

    def set_validation(self, qle: QLineEdit):
        palette = qle.palette()
        file_spec = os.path.join(self.txtFolderLocation.text(), qle.text())
        if os.path.isfile(file_spec):
            palette.setColor(QPalette.Base, QColor('lightgreen'))
        else:
            palette.setColor(QPalette.Base, QColor('lightcoral'))
        qle.setPalette(palette)

    def updateFolder(self):

        if self.inst.install_type == 'Rain Gauge':
            self.updateRainfallFile()
            # self.updateBatteryFile()
        elif self.inst.install_type in ['Flow Monitor', 'Depth Monitor']:
            self.updateDepthFile()
            self.updateVelocityFile()
            self.updateBatteryFile()
        else:
            self.updatePumpLoggerFile()

    def updateRainfallFile(self):
        self.txtRainfallFileName.setText(self.decode_file_format(
            self.txtRainfallFileNameFormat.text()))
        self.set_validation(self.txtRainfallFileName)

    def updateDepthFile(self):
        self.txtDepthFileName.setText(self.decode_file_format(
            self.txtDepthFileNameFormat.text()))
        self.set_validation(self.txtDepthFileName)

    def updateVelocityFile(self):
        self.txtVelocityFileName.setText(self.decode_file_format(
            self.txtVelocityFileNameFormat.text()))
        self.set_validation(self.txtVelocityFileName)

    def updateBatteryFile(self):
        self.txtBatteryFileName.setText(self.decode_file_format(
            self.txtBatteryFileNameFormat.text()))
        self.set_validation(self.txtBatteryFileName)

    def updatePumpLoggerFile(self):
        self.txtPumpLoggerFileName.setText(self.decode_file_format(
            self.txtPumpLoggerFileNameFormat.text()))
        self.set_validation(self.txtPumpLoggerFileName)

    def pipeWidthChanged(self):
        if self.comboBox_pipe_shape.currentText() == 'CIRC':
            self.spinBox_height.blockSignals(True)
            self.spinBox_height.setValue(self.spinBox_width.value())
            self.spinBox_height.blockSignals(False)
        self.pipeShapeChanged()

    def pipeHeightChanged(self):
        if self.comboBox_pipe_shape.currentText() == 'CIRC':
            self.spinBox_width.blockSignals(True)
            self.spinBox_width.setValue(self.spinBox_height.value())
            self.spinBox_width.blockSignals(False)
        self.pipeShapeChanged()

    def pipeShapeChanged(self):

        isStandardShape = self.comboBox_pipe_shape.currentText() in [
            'CIRC', 'RECT']
        isUserShape = self.comboBox_pipe_shape.currentText() == 'USER'

        self.spinBox_width.setEnabled(not isUserShape)
        self.spinBox_height.setEnabled(not isUserShape)
        self.label_pipe_shape_definition.setVisible(not isStandardShape)
        self.lbl_no_of_intervals.setVisible(
            not (isStandardShape or isUserShape))
        self.spinBox_intervals.setVisible(not (isStandardShape or isUserShape))
        self.tableWidget_pipe_shape_definition.setVisible(
            not isStandardShape)
        self.plotCanvas_pipe_shape_definition.setVisible(
            not isStandardShape)

        self.tableWidget_pipe_shape_definition.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed | QAbstractItemView.AnyKeyPressed)

        if not (isStandardShape or isUserShape):
            try:
                list_shape = generate_shape(self.spinBox_width.value(), self.spinBox_height.value(
                ), self.spinBox_intervals.value(), self.comboBox_pipe_shape.currentText())

                self.pipeShapeGraph.df_shape = pd.DataFrame(
                    list_shape, columns=['Width', 'Height'])
                self.pipeShapeGraph.update_plot()

                # self.tableWidget_pipe_shape_definition.clear()
                self.tableWidget_pipe_shape_definition.setRowCount(0)
                self.populateTableWidget(
                    self.tableWidget_pipe_shape_definition, self.pipeShapeGraph.df_shape)

                self.tableWidget_pipe_shape_definition.setEditTriggers(
                    QAbstractItemView.NoEditTriggers)

                self.lastValidShape = self.comboBox_pipe_shape.currentText()
                self.lastValidWidth = self.spinBox_width.value()
                self.lastValidHeight = self.spinBox_height.value()

            except ValueError as e:
                # Show an error message dialog
                QMessageBox.warning(self, "Invalid Shape Parameters", str(e))

                self.spinBox_width.blockSignals(True)
                self.spinBox_height.blockSignals(True)
                self.comboBox_pipe_shape.blockSignals(True)

                self.comboBox_pipe_shape.setCurrentText(self.lastValidShape)
                self.spinBox_width.setValue(self.lastValidWidth)
                self.spinBox_height.setValue(self.lastValidHeight)

                self.comboBox_pipe_shape.blockSignals(False)
                self.spinBox_width.blockSignals(False)
                self.spinBox_height.blockSignals(False)

                self.pipeShapeChanged()

        elif isUserShape:
            try:
                self.pipeShapeGraph.df_shape, max_width, max_height = self.getDataFromPipeShapeDefTableWidget()

                # self.tableWidget_pipe_shape_definition.clear()
                self.tableWidget_pipe_shape_definition.setRowCount(0)
                self.populateTableWidget(
                    self.tableWidget_pipe_shape_definition, self.pipeShapeGraph.df_shape)

                self.spinBox_width.blockSignals(True)
                self.spinBox_height.blockSignals(True)

                self.spinBox_width.setValue(int(max_width))
                self.spinBox_height.setValue(int(max_height))

                self.spinBox_width.blockSignals(False)
                self.spinBox_height.blockSignals(False)

                self.pipeShapeGraph.update_plot()

                self.lastValidShape = self.comboBox_pipe_shape.currentText()
                self.lastValidWidth = self.spinBox_width.value()
                self.lastValidHeight = self.spinBox_height.value()

            except ValueError as e:
                # Show an error message dialog
                QMessageBox.warning(self, "Invalid Shape Parameters", str(e))

                self.spinBox_width.blockSignals(True)
                self.spinBox_height.blockSignals(True)
                self.comboBox_pipe_shape.blockSignals(True)

                self.comboBox_pipe_shape.setCurrentText(self.lastValidShape)
                self.spinBox_width.setValue(self.lastValidWidth)
                self.spinBox_height.setValue(self.lastValidHeight)

                self.comboBox_pipe_shape.blockSignals(False)
                self.spinBox_width.blockSignals(False)
                self.spinBox_height.blockSignals(False)

                self.pipeShapeChanged()
        else:
            if self.comboBox_pipe_shape.currentText() == 'CIRC':
                self.spinBox_height.blockSignals(True)
                self.spinBox_height.setValue(self.spinBox_width.value())
                self.spinBox_height.blockSignals(False)

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Delete:
            self.deleteSelectedRows()
        else:
            super().keyPressEvent(event)

    def setupTabs(self):

        # for index in range(self.tabRawDataSettings.count()):
        #     tab = self.tabRawDataSettings.widget(index)  # Get the tab widget
        #     if tab.objectName() == 'tab_depth':  # Check its object name
        #         self.tabRawDataSettings.setTabText(index, 'Depth\nCorrections')
        #     elif tab.objectName() == 'tab_velocity':  # Check its object name
        #         self.tabRawDataSettings.setTabText(
        #             index, 'Velocity\nCorrections')
        #     elif tab.objectName() == 'tab_dv_timing':  # Check its object name
        #         self.tabRawDataSettings.setTabText(
        #             index, 'Depth/Velocity\nTiming')

        # Determine visibility based on install type
        if self.inst.install_type == 'Rain Gauge':
            visible_tabs = {'tab_file_location', 'tab_rainfall'}
            # self.populateRainfallTimingTable()

            self.lblRainfallFileFormat.setVisible(True)
            self.txtRainfallFileNameFormat.setVisible(True)
            self.txtRainfallFileName.setVisible(True)

            self.lblDepthFileFormat.setVisible(False)
            self.txtDepthFileNameFormat.setVisible(False)
            self.txtDepthFileName.setVisible(False)

            self.lblVelocityFileFormat.setVisible(False)
            self.txtVelocityFileNameFormat.setVisible(False)
            self.txtVelocityFileName.setVisible(False)

            self.lblBatteryFileFormat.setVisible(False)
            self.txtBatteryFileNameFormat.setVisible(False)
            self.txtBatteryFileName.setVisible(False)

            self.lblPumpLoggerFileFormat.setVisible(False)
            self.txtPumpLoggerFileNameFormat.setVisible(False)
            self.txtPumpLoggerFileName.setVisible(False)

            self.txtFolderLocation.textChanged.connect(self.updateFolder)

            self.txtRainfallFileNameFormat.editingFinished.connect(self.updateRainfallFile)
            self.txtRainfallFileNameFormat.setAcceptDrops(True)
            self.txtRainfallFileNameFormat.installEventFilter(self)

            self.txtBatteryFileNameFormat.editingFinished.connect(self.updateBatteryFile)
            self.txtBatteryFileNameFormat.setAcceptDrops(True)
            self.txtBatteryFileNameFormat.installEventFilter(self)

            self.txtFolderLocation.setText(self.raw.file_path)
            self.txtRainfallFileNameFormat.setText(self.raw.rainfall_file_format)
            self.updateRainfallFile()
            # self.txtBatteryFileNameFormat.setText(self.raw.battery_file_format)
            # self.updateBatteryFile()

            self.doubleSpinBox_tipping_bucket.setValue(self.raw.rg_tb_depth)
            self.populateTableWidget(self.tableWidget_rainfall_timing, self.raw.rg_timing_corr)

        elif self.inst.install_type in ['Flow Monitor', 'Depth Monitor']:  # Flow Monitor or Depth Monitor
            visible_tabs = {'tab_file_location', 'tab_depth', 'tab_velocity',
                            'tab_dv_timing', 'tab_pipe_shape', 'tab_silt'}

            self.lblRainfallFileFormat.setVisible(False)
            self.txtRainfallFileNameFormat.setVisible(False)
            self.txtRainfallFileName.setVisible(False)

            self.lblDepthFileFormat.setVisible(True)
            self.txtDepthFileNameFormat.setVisible(True)
            self.txtDepthFileName.setVisible(True)

            self.lblVelocityFileFormat.setVisible(True)
            self.txtVelocityFileNameFormat.setVisible(True)
            self.txtVelocityFileName.setVisible(True)

            self.lblBatteryFileFormat.setVisible(True)
            self.txtBatteryFileNameFormat.setVisible(True)
            self.txtBatteryFileName.setVisible(True)

            self.lblPumpLoggerFileFormat.setVisible(False)
            self.txtPumpLoggerFileNameFormat.setVisible(False)
            self.txtPumpLoggerFileName.setVisible(False)

            self.txtFolderLocation.textChanged.connect(self.updateFolder)

            self.txtDepthFileNameFormat.editingFinished.connect(self.updateDepthFile)
            self.txtDepthFileNameFormat.setAcceptDrops(True)
            self.txtDepthFileNameFormat.installEventFilter(self)

            self.txtVelocityFileNameFormat.editingFinished.connect(self.updateVelocityFile)
            self.txtVelocityFileNameFormat.setAcceptDrops(True)
            self.txtVelocityFileNameFormat.installEventFilter(self)

            self.txtBatteryFileNameFormat.editingFinished.connect(self.updateBatteryFile)
            self.txtBatteryFileNameFormat.setAcceptDrops(True)
            self.txtBatteryFileNameFormat.installEventFilter(self)

            self.txtFolderLocation.setText(self.raw.file_path)
            self.txtDepthFileNameFormat.setText(self.raw.depth_file_format)
            self.updateDepthFile()
            self.txtVelocityFileNameFormat.setText(self.raw.velocity_file_format)
            self.updateVelocityFile()
            self.txtBatteryFileNameFormat.setText(self.raw.battery_file_format)
            self.updateBatteryFile()

            self.spinBox_width.setValue(self.raw.pipe_width)
            self.spinBox_height.setValue(self.raw.pipe_height)
            self.comboBox_pipe_shape.setCurrentText(self.raw.pipe_shape)
            self.spinBox_intervals.setValue(self.raw.pipe_shape_intervals)

            self.populateTableWidget(self.tableWidget_pipe_shape_definition, self.raw.pipe_shape_def)
            self.populateTableWidget(self.tableWidget_silt_depths, self.raw.silt_levels)
            self.populateTableWidget(self.tableWidget_depth_corrections, self.raw.dep_corr)
            self.populateTableWidget(self.tableWidget_velocity_corrections, self.raw.vel_corr)
            self.populateTableWidget(self.tableWidget_timing_corrections, self.raw.dv_timing_corr)
        else:
            visible_tabs = {
                "tab_file_location",
                "tab_pump_logger",
                "tab_pump_logger_onoff",
            }

            self.lblRainfallFileFormat.setVisible(False)
            self.txtRainfallFileNameFormat.setVisible(False)
            self.txtRainfallFileName.setVisible(False)

            self.lblDepthFileFormat.setVisible(False)
            self.txtDepthFileNameFormat.setVisible(False)
            self.txtDepthFileName.setVisible(False)

            self.lblVelocityFileFormat.setVisible(False)
            self.txtVelocityFileNameFormat.setVisible(False)
            self.txtVelocityFileName.setVisible(False)

            self.lblBatteryFileFormat.setVisible(False)
            self.txtBatteryFileNameFormat.setVisible(False)
            self.txtBatteryFileName.setVisible(False)

            self.lblPumpLoggerFileFormat.setVisible(True)
            self.txtPumpLoggerFileNameFormat.setVisible(True)
            self.txtPumpLoggerFileName.setVisible(True)

            self.txtFolderLocation.textChanged.connect(self.updateFolder)

            self.txtPumpLoggerFileNameFormat.editingFinished.connect(self.updatePumpLoggerFile)
            self.txtPumpLoggerFileNameFormat.setAcceptDrops(True)
            self.txtPumpLoggerFileNameFormat.installEventFilter(self)

            self.txtFolderLocation.setText(self.raw.file_path)
            self.txtPumpLoggerFileNameFormat.setText(self.raw.pumplogger_file_format)
            self.updatePumpLoggerFile()

            self.populateTableWidget(self.tableWidget_pumplogger_timing, self.raw.pl_timing_corr)
            self.populateTableWidget(self.tableWidget_pumplogger_added_onoffs, self.raw.pl_added_onoffs)

        # Set visibility for all tabs
        for index in range(self.tabRawDataSettings.count()):
            tab = self.tabRawDataSettings.widget(index)
            tab_name = tab.objectName()
            is_visible = tab_name in visible_tabs
            self.tabRawDataSettings.setTabVisible(index, is_visible)

    def populateTableWidget(self, tableWidget: QTableWidget, df_data: pd.DataFrame):
        """Populate the rainfall timing table without triggering signals."""
        # Block signals to prevent unwanted triggers
        tableWidget.blockSignals(True)

        if df_data is not None:
            for row_data in df_data.itertuples(index=False):
                if tableWidget.objectName() in ['tableWidget_rainfall_timing', 'tableWidget_pumplogger_timing', 'tableWidget_pumplogger_added_onoffs','tableWidget_silt_depths', 'tableWidget_velocity_corrections', 'tableWidget_timing_corrections']:
                    self.addDefaultRow(tableWidget, row_data)
                elif tableWidget.objectName() == 'tableWidget_pipe_shape_definition':
                    self.addPipeShapeDefRow(row_data)
                elif tableWidget.objectName() == 'tableWidget_depth_corrections':
                    self.addDepthCorrectionRow(row_data)

        if tableWidget.objectName() in [
            "tableWidget_rainfall_timing",
            "tableWidget_pumplogger_timing",
            "tableWidget_pumplogger_added_onoffs",
            "tableWidget_silt_depths",
            "tableWidget_velocity_corrections",
            "tableWidget_timing_corrections",
        ]:
            self.addDefaultEmptyRow(tableWidget)
        elif tableWidget.objectName() == 'tableWidget_pipe_shape_definition':
            if self.comboBox_pipe_shape.currentText() == 'USER':
                self.addPipeShapeDefEmptyRow()
        elif tableWidget.objectName() == 'tableWidget_depth_corrections':
            self.addDepthCorrectionEmptyRow()
        # Re-enable signals
        tableWidget.blockSignals(False)

    def addDefaultRow(self, tableWidget: QTableWidget, row_data):
        row = tableWidget.rowCount()
        tableWidget.insertRow(row)

        # Ensure datetime is handled correctly
        if isinstance(row_data[0], datetime):
            qdate_time = QtCore.QDateTime(row_data[0].year, row_data[0].month, row_data[0].day,
                                          row_data[0].hour, row_data[0].minute)
        else:
            qdate_time = QtCore.QDateTime.fromString(
                row_data[0], "yyyy-MM-dd HH:mm")

        # Add DateTimeEdit
        date_edit = QtWidgets.QDateTimeEdit(qdate_time)
        date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        date_edit.setCalendarPopup(True)
        # self.tableWidget_depth_corrections.setCellWidget(row, 0, date_edit)
        tableWidget.setCellWidget(row, 0, date_edit)

        # Add Float Item
        float_item = QtWidgets.QTableWidgetItem(str(row_data[1]))
        float_item.setFlags(float_item.flags() | QtCore.Qt.ItemIsEditable)
        tableWidget.setItem(row, 1, float_item)

        # Add Description Item
        string_item = QtWidgets.QTableWidgetItem(str(row_data[2]))
        string_item.setFlags(string_item.flags() | QtCore.Qt.ItemIsEditable)
        tableWidget.setItem(row, 2, string_item)

# from PyQt5 import QtWidgets, QtCore
# from PyQt5.QtWidgets import QTableWidget, QComboBox
# from datetime import datetime


    def addDefaultRow(self, tableWidget: QTableWidget, row_data):
        row = tableWidget.rowCount()
        tableWidget.insertRow(row)

        # Ensure datetime is handled correctly
        if isinstance(row_data[0], datetime):
            qdate_time = QtCore.QDateTime(row_data[0].year, row_data[0].month, row_data[0].day,
                                        row_data[0].hour, row_data[0].minute)
        else:
            qdate_time = QtCore.QDateTime.fromString(row_data[0], "yyyy-MM-dd HH:mm")

        # Add DateTimeEdit
        date_edit = QtWidgets.QDateTimeEdit(qdate_time)
        date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        date_edit.setCalendarPopup(True)
        tableWidget.setCellWidget(row, 0, date_edit)

        if tableWidget.objectName() == 'tableWidget_pumplogger_added_onoffs':
            # Create a QComboBox for float values
            combo_box = QComboBox()
            combo_box.addItem("On", 1.0)
            combo_box.addItem("Off", 0.0)

            # Set the initial value based on row_data[1]
            if row_data[1] == 1.0:
                combo_box.setCurrentText("On")
            else:
                combo_box.setCurrentText("Off")

            # Connect selection change to update internal data
            combo_box.currentIndexChanged.connect(lambda: self.handleSelectionChange(combo_box))

            # Add the combo box to the table
            tableWidget.setCellWidget(row, 1, combo_box)
        else:
            # Add Float Item
            float_item = QtWidgets.QTableWidgetItem(str(row_data[1]))
            float_item.setFlags(float_item.flags() | QtCore.Qt.ItemIsEditable)
            tableWidget.setItem(row, 1, float_item)            

        # Add Description Item
        string_item = QtWidgets.QTableWidgetItem(str(row_data[2]))
        string_item.setFlags(string_item.flags() | QtCore.Qt.ItemIsEditable)
        tableWidget.setItem(row, 2, string_item)


    def handleSelectionChange(self, combo_box):
        selected_value = combo_box.currentData()  # Gets the float value (1.0 or 0.0)
        print(f"Selected float value: {selected_value}")
        
    def addPipeShapeDefRow(self, row_data):
        row = self.tableWidget_pipe_shape_definition.rowCount()
        self.tableWidget_pipe_shape_definition.insertRow(row)

        # Add Float Item
        float_item = QtWidgets.QTableWidgetItem(f"{row_data[0]:.2f}")
        float_item.setFlags(float_item.flags() | QtCore.Qt.ItemIsEditable)
        self.tableWidget_pipe_shape_definition.setItem(row, 0, float_item)

        # Add Float Item
        float_item = QtWidgets.QTableWidgetItem(f"{row_data[1]:.2f}")
        float_item.setFlags(float_item.flags() | QtCore.Qt.ItemIsEditable)
        self.tableWidget_pipe_shape_definition.setItem(row, 1, float_item)

    def addDepthCorrectionRow(self, row_data):
        row = self.tableWidget_depth_corrections.rowCount()
        self.tableWidget_depth_corrections.insertRow(row)

        # Ensure datetime is handled correctly
        if isinstance(row_data[0], datetime):
            qdate_time = QtCore.QDateTime(row_data[0].year, row_data[0].month, row_data[0].day,
                                          row_data[0].hour, row_data[0].minute)
        else:
            qdate_time = QtCore.QDateTime.fromString(
                row_data[0], "yyyy-MM-dd HH:mm")

        # Add DateTimeEdit
        date_edit = QtWidgets.QDateTimeEdit(qdate_time)
        date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        date_edit.setCalendarPopup(True)
        self.tableWidget_depth_corrections.setCellWidget(row, 0, date_edit)

        # Add Float Item
        float_item = QtWidgets.QTableWidgetItem(str(row_data[1]))
        float_item.setFlags(float_item.flags() | QtCore.Qt.ItemIsEditable)
        self.tableWidget_depth_corrections.setItem(row, 1, float_item)

        # Add Float Item
        float_item = QtWidgets.QTableWidgetItem(str(row_data[2]))
        float_item.setFlags(float_item.flags() | QtCore.Qt.ItemIsEditable)
        self.tableWidget_depth_corrections.setItem(row, 2, float_item)

        # Add Description Item
        string_item = QtWidgets.QTableWidgetItem(str(row_data[3]))
        string_item.setFlags(string_item.flags() | QtCore.Qt.ItemIsEditable)
        self.tableWidget_depth_corrections.setItem(row, 3, string_item)

    def addDefaultEmptyRow(self, tableWidget: QTableWidget):
        row = tableWidget.rowCount()
        tableWidget.insertRow(row)

        date_edit = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        date_edit.setCalendarPopup(True)
        tableWidget.setCellWidget(row, 0, date_edit)

        float_item = QtWidgets.QTableWidgetItem("")
        float_item.setFlags(float_item.flags() | QtCore.Qt.ItemIsEditable)
        tableWidget.setItem(row, 1, float_item)

        string_item = QtWidgets.QTableWidgetItem("")
        string_item.setFlags(string_item.flags() | QtCore.Qt.ItemIsEditable)
        tableWidget.setItem(row, 2, string_item)

    def addPipeShapeDefEmptyRow(self):
        row = self.tableWidget_pipe_shape_definition.rowCount()
        self.tableWidget_pipe_shape_definition.insertRow(row)

        float_item = QtWidgets.QTableWidgetItem("")
        float_item.setFlags(float_item.flags() | QtCore.Qt.ItemIsEditable)
        self.tableWidget_pipe_shape_definition.setItem(row, 0, float_item)

        string_item = QtWidgets.QTableWidgetItem("")
        string_item.setFlags(string_item.flags() | QtCore.Qt.ItemIsEditable)
        self.tableWidget_pipe_shape_definition.setItem(row, 1, string_item)

    def addDepthCorrectionEmptyRow(self):
        row = self.tableWidget_depth_corrections.rowCount()
        self.tableWidget_depth_corrections.insertRow(row)

        date_edit = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        date_edit.setCalendarPopup(True)
        self.tableWidget_depth_corrections.setCellWidget(row, 0, date_edit)

        float_item = QtWidgets.QTableWidgetItem("")
        float_item.setFlags(float_item.flags() | QtCore.Qt.ItemIsEditable)
        self.tableWidget_depth_corrections.setItem(row, 1, float_item)

        float_item = QtWidgets.QTableWidgetItem("")
        float_item.setFlags(float_item.flags() | QtCore.Qt.ItemIsEditable)
        self.tableWidget_depth_corrections.setItem(row, 2, float_item)

        string_item = QtWidgets.QTableWidgetItem("")
        string_item.setFlags(string_item.flags() | QtCore.Qt.ItemIsEditable)
        self.tableWidget_depth_corrections.setItem(row, 3, string_item)

    # def onDefaultCellChanged(self, row, column):

    #     focused_widget = self.focusWidget()
    #     # Check if this is the last row
    #     if row != focused_widget.rowCount() - 1:
    #         return

    #     try:
    #         # Extract and validate data
    #         date_edit = focused_widget.cellWidget(row, 0)
    #         float_item = focused_widget.item(row, 1)

    #         if (
    #             date_edit and
    #             float_item and float_item.text().strip()
    #         ):
    #             float(float_item.text().strip())  # Validate numeric value

    #             # Block signals to prevent loops
    #             focused_widget.blockSignals(True)
    #             # self.highlightRowAsComplete(row)
    #             self.addDefaultEmptyRow(focused_widget)
    #             focused_widget.blockSignals(False)
    #     except (ValueError, AttributeError):
    #         pass

    def onDefaultCellChanged(self, row, column):
        """Generic handler for QTableWidget cell changes."""
        # Get the table that triggered the signal
        table_widget = self.sender()
        # Ensure it's a QTableWidget
        if not isinstance(table_widget, QtWidgets.QTableWidget):
            return
        # Check if this is the last row
        if row != table_widget.rowCount() - 1:
            return

        try:
            # Extract and validate data
            date_edit = table_widget.cellWidget(row, 0)
            float_item = table_widget.item(row, 1)

            if date_edit and float_item and float_item.text().strip():
                float(float_item.text().strip())  # Validate numeric value

                # Block signals to prevent unwanted triggers
                table_widget.blockSignals(True)
                # Add a new empty row
                self.addDefaultEmptyRow(table_widget)
                # Re-enable signals
                table_widget.blockSignals(False)
        except (ValueError, AttributeError):
            pass

    def onDepthCorrectionCellChanged(self, row, column):
        # Check if this is the last row
        if row != self.tableWidget_depth_corrections.rowCount() - 1:
            return

        try:
            # Extract and validate data
            date_edit = self.tableWidget_depth_corrections.cellWidget(row, 0)
            float_item1 = self.tableWidget_depth_corrections.item(row, 1)
            float_item2 = self.tableWidget_depth_corrections.item(row, 2)

            if (
                date_edit and
                float_item1 and float_item2 and float_item1.text(
                ).strip() and float_item2.text().strip()
            ):
                float(float_item1.text().strip())  # Validate numeric value
                float(float_item2.text().strip())  # Validate numeric value

                # Block signals to prevent loops
                self.tableWidget_depth_corrections.blockSignals(True)
                # self.highlightRowAsComplete(row)
                self.addDepthCorrectionEmptyRow()
                self.tableWidget_depth_corrections.blockSignals(False)
        except (ValueError, AttributeError):
            pass

    def onPipeShapeDefCellChanged(self, row, column):
        # Check if this is the last row
        if row != self.tableWidget_pipe_shape_definition.rowCount() - 1:
            return

        try:

            float_item1 = self.tableWidget_pipe_shape_definition.item(row, 0)
            float_item2 = self.tableWidget_pipe_shape_definition.item(row, 1)

            if (
                float_item1 and float_item2 and float_item1.text(
                ).strip() and float_item2.text().strip()
            ):
                float(float_item1.text().strip())  # Validate numeric value
                float(float_item2.text().strip())  # Validate numeric value

                # Block signals to prevent loops
                self.tableWidget_pipe_shape_definition.blockSignals(True)
                if self.comboBox_pipe_shape.currentText() == 'USER':

                    if self.tableWidget_pipe_shape_definition.rowCount() >= 2:

                        # Collect all rows and sort by height
                        rows = []
                        for i in range(self.tableWidget_pipe_shape_definition.rowCount()):
                            item1 = self.tableWidget_pipe_shape_definition.item(
                                i, 0)
                            item2 = self.tableWidget_pipe_shape_definition.item(
                                i, 1)
                            if item1 and item2 and item1.text().strip() and item2.text().strip():
                                rows.append(
                                    (float(item1.text().strip()),
                                     float(item2.text().strip()))
                                )

                        # Sort rows by height (second column)
                        rows.sort(key=lambda x: x[1])

                        # Block signals to prevent loops
                        self.tableWidget_pipe_shape_definition.blockSignals(
                            True)

                        # Clear and re-populate the table with sorted rows
                        self.tableWidget_pipe_shape_definition.setRowCount(0)
                        for width, height in rows:
                            row_position = self.tableWidget_pipe_shape_definition.rowCount()
                            self.tableWidget_pipe_shape_definition.insertRow(
                                row_position)
                            self.tableWidget_pipe_shape_definition.setItem(
                                row_position, 0, QtWidgets.QTableWidgetItem(str(width)))
                            self.tableWidget_pipe_shape_definition.setItem(
                                row_position, 1, QtWidgets.QTableWidgetItem(str(height)))

                        self.tableWidget_pipe_shape_definition.blockSignals(
                            False)
                        self.pipeShapeChanged()

                    self.addPipeShapeDefEmptyRow()
                self.tableWidget_pipe_shape_definition.blockSignals(False)
        except (ValueError, AttributeError):
            pass

    def deleteSelectedRows(self):
        """Delete selected rows from the currently focused QTableWidget."""
        focused_widget = self.focusWidget()

        if isinstance(focused_widget, QtWidgets.QTableWidget):
            selected_rows = set(index.row()
                                for index in focused_widget.selectedIndexes())

            if not selected_rows:
                QtWidgets.QMessageBox.warning(
                    self, "No Selection", "Please select one or more rows to delete.")
                return

            # Prevent deleting all rows
            if len(selected_rows) == focused_widget.rowCount():
                QtWidgets.QMessageBox.warning(
                    self, "Delete Error", "Cannot delete all rows. At least one row must remain.")
                return

            # Block signals to prevent unwanted triggers
            focused_widget.blockSignals(True)

            # Delete rows in reverse to avoid index shifting
            for row in sorted(selected_rows, reverse=True):
                focused_widget.removeRow(row)

            # Ensure an empty row exists if the last row was deleted
            if focused_widget == self.tableWidget_pipe_shape_definition:
                if focused_widget.rowCount() == 0:
                    self.addPipeShapeDefEmptyRow()
            elif focused_widget == self.tableWidget_depth_corrections:
                if focused_widget.rowCount() == 0 or not self.isLastRowEmpty(focused_widget):
                    self.addDepthCorrectionEmptyRow()
            else:
                if focused_widget.rowCount() == 0 or not self.isLastRowEmpty(focused_widget):
                    self.addDefaultEmptyRow(focused_widget)
            # Re-enable signals
            focused_widget.blockSignals(False)

            self.pipeShapeChanged()
        else:
            QtWidgets.QMessageBox.warning(
                self, "No Table Selected", "Please click inside a table to delete rows.")

    def isLastRowEmpty(self, table_widget):
        """Check if the last row in the table is empty."""
        last_row = table_widget.rowCount() - 1

        if last_row < 0:
            return True  # Table is already empty

        # Check if all cells in the last row are empty
        for col in range(table_widget.columnCount()):
            # If its one of the correction tables ignore the first column
            if table_widget.objectName() != 'tableWidget_pipe_shape_definition':
                if col == 0:
                    continue

            cell_widget = table_widget.cellWidget(last_row, col)
            item = table_widget.item(last_row, col)

            # If there's a widget, check its text
            if cell_widget and hasattr(cell_widget, 'text') and cell_widget.text().strip():
                return False

            # If there's a standard table item, check its text
            if item and item.text().strip():
                return False

        # If all cells are empty
        return True

    # def isLastRowEmpty(self, table_widget):
    #     """Check if the last row in the table is empty."""
    #     last_row = table_widget.rowCount() - 1

    #     # Check if the first two cells are empty
    #     date_edit = table_widget.cellWidget(last_row, 0)
    #     float_item = table_widget.item(last_row, 1)

    #     if (
    #         date_edit is None or
    #         float_item is None or
    #         not float_item.text().strip()
    #     ):
    #         return True

    #     return False

    # def generatePipeShape(self):
    #     pass

    def onAccept(self):
        if self.inst.install_type == 'Rain Gauge':
            # Update DataFrame
            self.raw.rg_tb_depth = self.doubleSpinBox_tipping_bucket.value()
            self.raw.rg_timing_corr = self.getDataFrameFromDefaultTableWidget(
                self.tableWidget_rainfall_timing)
            self.raw.file_path = self.txtFolderLocation.text()
            self.raw.rainfall_file_format = self.txtRainfallFileNameFormat.text()
        elif self.inst.install_type in ['Flow Monitor', 'Depth Monitor']:
            self.raw.dep_corr = self.getDataFrameFromDepthCorrTableWidget()
            self.raw.vel_corr = self.getDataFrameFromDefaultTableWidget(
                self.tableWidget_velocity_corrections)
            self.raw.dv_timing_corr = self.getDataFrameFromDefaultTableWidget(
                self.tableWidget_timing_corrections)
            self.raw.pipe_shape = self.comboBox_pipe_shape.currentText()
            self.raw.pipe_width = int(self.spinBox_width.value())
            self.raw.pipe_height = int(self.spinBox_height.value())

            self.raw.pipe_shape_def, max_width, max_height = self.getDataFromPipeShapeDefTableWidget()
            self.raw.silt_levels = self.getDataFrameFromDefaultTableWidget(
                self.tableWidget_silt_depths)
            self.raw.pipe_shape_intervals = int(self.spinBox_intervals.value())

            self.raw.file_path = self.txtFolderLocation.text()
            self.raw.depth_file_format = self.txtDepthFileNameFormat.text()
            self.raw.velocity_file_format = self.txtVelocityFileNameFormat.text()
            self.raw.battery_file_format = self.txtBatteryFileNameFormat.text()

        elif self.inst.install_type == 'Pump Logger':
            # Update DataFrame
            self.raw.pl_timing_corr = self.getDataFrameFromDefaultTableWidget(self.tableWidget_pumplogger_timing)
            self.raw.pl_added_onoffs = self.getDataFrameFromDefaultTableWidget(self.tableWidget_pumplogger_added_onoffs)

            self.raw.file_path = self.txtFolderLocation.text()
            self.raw.pumplogger_file_format = self.txtPumpLoggerFileNameFormat.text()
        # Accept the dialog
        self.accept()

    def onReject(self):
        self.reject()

    # def getDataFrameFromDefaultTableWidget(self, tableWidget: pd.DataFrame):

    #     data = []

    #     for row in range(tableWidget.rowCount() - 1):
    #         date_edit = tableWidget.cellWidget(row, 0)
    #         float_item = tableWidget.item(row, 1)
    #         string_item = tableWidget.item(row, 2)

    #         try:
    #             # Extract and format date
    #             date_value = date_edit.dateTime().toString("yyyy-MM-dd HH:mm")
    #             float_value = float(float_item.text().strip())
    #             string_value = string_item.text().strip()

    #             # Validate and append data
    #             if string_value:
    #                 data.append([date_value, float_value, string_value])
    #             else:
    #                 data.append([date_value, float_value, ''])

    #         except (ValueError, AttributeError):
    #             QtWidgets.QMessageBox.warning(
    #                 self, "Invalid Data", f"Invalid data in row {row + 1}. Please correct it.")
    #             return  # Stop saving on error

    #     # Update DataFrame
    #     return pd.DataFrame(data, columns=["DateTime", "FloatValue", "StringValue"])

    def getDataFrameFromDefaultTableWidget(self, tableWidget: QtWidgets.QTableWidget) -> pd.DataFrame:
        data = []

        for row in range(tableWidget.rowCount() - (1 if self.isLastRowEmpty(tableWidget) else 0)):
            # for row in range(tableWidget.rowCount()):
            try:
                # Extract datetime from QDateTimeEdit
                date_edit = tableWidget.cellWidget(row, 0)
                if date_edit is None or not isinstance(date_edit, QtWidgets.QDateTimeEdit):
                    raise AttributeError(
                        "Missing or invalid DateTimeEdit in row {row + 1}")
                date_value = date_edit.dateTime().toPyDateTime()

                # Extract float from QTableWidgetItem
                float_item = tableWidget.item(row, 1)
                if float_item is None:
                    raise AttributeError(
                        f"Missing FloatValue in row {row + 1}")
                float_value = float(float_item.text().strip())

                # Extract string from QTableWidgetItem
                string_item = tableWidget.item(row, 2)
                if string_item is None:
                    string_value = ''
                else:
                    string_value = string_item.text().strip()

                # Append row data
                data.append([date_value, float_value, string_value])

            except (ValueError, AttributeError) as e:
                QtWidgets.QMessageBox.warning(
                    self, "Invalid Data", f"Error in row {row + 1}: {e}. Please correct it.")
                return pd.DataFrame(columns=["DateTime", "FloatValue", "StringValue"])

        # Return DataFrame
        return pd.DataFrame(data, columns=["DateTime", "FloatValue", "StringValue"])

    # def getDataFrameFromDepthCorrTableWidget(self, tableWidget: pd.DataFrame):

    #     data = []

    #     for row in range(tableWidget.rowCount() - 1):
    #         date_edit = tableWidget.cellWidget(row, 0)
    #         float_item1 = tableWidget.item(row, 1)
    #         float_item2 = tableWidget.item(row, 2)
    #         string_item = tableWidget.item(row, 3)

    #         try:
    #             # Extract and format date
    #             date_value = date_edit.dateTime().toString("yyyy-MM-dd HH:mm")
    #             float_value1 = float(float_item1.text().strip())
    #             float_value2 = float(float_item2.text().strip())
    #             string_value = string_item.text().strip()

    #             # Validate and append data
    #             if string_value:
    #                 data.append([date_value, float_value1,
    #                             float_value2, string_value])
    #             else:
    #                 data.append([date_value, float_value1, float_value2, ''])

    #         except (ValueError, AttributeError):
    #             QtWidgets.QMessageBox.warning(
    #                 self, "Invalid Data", f"Invalid data in row {row + 1}. Please correct it.")
    #             return  # Stop saving on error

    #     # Update DataFrame
    #     return pd.DataFrame(data, columns=["DateTime", "DepthCorr", "InvertOffset", "Comment"])

    def getDataFrameFromDepthCorrTableWidget(self) -> pd.DataFrame:
        data = []

        for row in range(self.tableWidget_depth_corrections.rowCount() - (1 if self.isLastRowEmpty(self.tableWidget_depth_corrections) else 0)):
            # for row in range(self.tableWidget_depth_corrections.rowCount()):
            try:
                # Extract datetime from QDateTimeEdit
                date_edit = self.tableWidget_depth_corrections.cellWidget(
                    row, 0)
                if date_edit is None or not isinstance(date_edit, QtWidgets.QDateTimeEdit):
                    raise AttributeError(
                        f"Missing or invalid DateTimeEdit in row {row + 1}")
                date_value = date_edit.dateTime().toPyDateTime()

                # Extract float values from QTableWidgetItems
                float_item1 = self.tableWidget_depth_corrections.item(row, 1)
                float_item2 = self.tableWidget_depth_corrections.item(row, 2)
                if float_item1 is None or float_item2 is None:
                    raise AttributeError(
                        f"Missing depth correction values in row {row + 1}")
                float_value1 = float(float_item1.text().strip())
                float_value2 = float(float_item2.text().strip())

                # Extract string value from QTableWidgetItem
                string_item = self.tableWidget_depth_corrections.item(row, 3)
                if string_item is None:
                    string_value = ''
                else:
                    string_value = string_item.text().strip()

                # Append row data
                data.append([date_value, float_value1,
                            float_value2, string_value])

            except (ValueError, AttributeError) as e:
                QtWidgets.QMessageBox.warning(
                    self, "Invalid Data", f"Error in row {row + 1}: {e}. Please correct it.")
                return pd.DataFrame(columns=["DateTime", "DepthCorr", "InvertOffset", "Comment"])

        # Return DataFrame
        return pd.DataFrame(data, columns=["DateTime", "DepthCorr", "InvertOffset", "Comment"])

    def getDataFromPipeShapeDefTableWidget(self):

        data = []
        max_width = 0
        max_height = 0

        i_range = self.tableWidget_pipe_shape_definition.rowCount() - (1 if self.isLastRowEmpty(self.tableWidget_pipe_shape_definition) else 0)

        for row in range(i_range):
            float_item1 = self.tableWidget_pipe_shape_definition.item(row, 0)
            float_item2 = self.tableWidget_pipe_shape_definition.item(row, 1)

            try:
                # Extract and format date
                float_value1 = float(float_item1.text().strip())
                float_value2 = float(float_item2.text().strip())

                if float_value1 > max_width:
                    max_width = float_value1
                if float_value2 > max_height:
                    max_height = float_value2

                data.append([float_value1, float_value2])

            except (ValueError, AttributeError):
                QtWidgets.QMessageBox.warning(
                    self, "Invalid Data", f"Invalid data in row {row + 1}. Please correct it.")
                return  # Stop saving on error

        # Update DataFrame
        return pd.DataFrame(data, columns=["Width", "Height"]), max_width, max_height


# class flowbot_dialog_fsm_raw_data_settings(QtWidgets.QDialog, Ui_Dialog):

#     def __init__(self, install: fsmInstall, fsm_project: fsmProject, parent=None):
#         """Constructor."""
#         super(flowbot_dialog_fsm_raw_data_settings, self).__init__(parent)
#         self.setupUi(self)

#         self.btnOK.clicked.connect(self.onAccept)
#         self.btnCancel.clicked.connect(self.onReject)
#         # self.monitor_id = monitor_id
#         self.project = fsm_project
#         self.inst = install
#         self.raw = self.project.get_raw_data_by_install(self.inst.install_id)

#         self.tableWidget_rainfall_timing.cellChanged.connect(
#             self.onRainfallTimingCellChanged)

#         # Types are: 'Rain Gauge', 'Flow Monitor' or 'Depth Monitor'
#         if self.inst.install_type == 'Rain Gauge':
#             for index in range(self.tabRawDataSettings.count()):
#                 tab = self.tabRawDataSettings.widget(index)
#                 if tab.objectName() == 'tab_rainfall':
#                     self.tabRawDataSettings.setTabVisible(index, True)
#                 else:
#                     self.tabRawDataSettings.setTabVisible(index, False)

#             self.doubleSpinBox_tipping_bucket.setValue(self.raw.rg_tb_depth)

#             # Populate the table with DataFrame data
#             if self.raw.rg_timing_corr is not None:
#                 for row in range(len(self.raw.rg_timing_corr)):
#                     # First column: DateTime widget
#                     date_item = QtWidgets.QTableWidgetItem(
#                         str(self.raw.rg_timing_corr.iat[row, 0]))
#                     date_item.setFlags(
#                         QtCore.Qt.ItemIsEditable)  # Allow editing
#                     self.tableWidget_rainfall_timing.setItem(row, 0, date_item)
#                     # Set a date/time editor for the first column
#                     date_edit = QtWidgets.QDateTimeEdit()
#                     # Allow calendar popup for easier date selection
#                     date_edit.setCalendarPopup(True)
#                     self.tableWidget_rainfall_timing.setCellWidget(
#                         row, 0, date_edit)

#                     # Second column: Float
#                     float_item = QtWidgets.QTableWidgetItem(
#                         str(self.raw.rg_timing_corr.iat[row, 1]))
#                     float_item.setFlags(
#                         QtCore.Qt.ItemIsEditable)  # Allow editing
#                     self.tableWidget_rainfall_timing.setItem(
#                         row, 1, float_item)

#                     # Last column: String
#                     string_item = QtWidgets.QTableWidgetItem(
#                         str(self.raw.rg_timing_corr.iat[row, 2]))
#                     string_item.setFlags(
#                         QtCore.Qt.ItemIsEditable)  # Allow editing
#                     self.tableWidget_rainfall_timing.setItem(
#                         row, 2, string_item)

#             self.addRainfallTimingEmptyRow()

#         elif self.inst.install_type == 'Flow Monitor':
#             for index in range(self.tabRawDataSettings.count()):
#                 tab = self.tabRawDataSettings.widget(index)
#                 if tab.objectName() == 'tab_rainfall':
#                     self.tabRawDataSettings.setTabVisible(index, False)
#                 else:
#                     self.tabRawDataSettings.setTabVisible(index, True)
#         elif self.inst.install_type == 'Depth Monitor':
#             for index in range(self.tabRawDataSettings.count()):
#                 tab = self.tabRawDataSettings.widget(index)
#                 if tab.objectName() in ['tab_rainfall', 'tab_dv_timing']:
#                     self.tabRawDataSettings.setTabVisible(index, False)
#                 else:
#                     self.tabRawDataSettings.setTabVisible(index, True)

#     def addRainfallTimingEmptyRow(self):
#         # Add a new blank row
#         self.tableWidget_rainfall_timing.insertRow(
#             self.tableWidget_rainfall_timing.rowCount())

#         # First column: DateTime editor
#         self.tableWidget_rainfall_timing.setCellWidget(
#             self.tableWidget_rainfall_timing.rowCount() - 1, 0, QtWidgets.QDateTimeEdit())

#         # Second column: Float (editable)
#         float_item = QtWidgets.QTableWidgetItem("")
#         float_item.setFlags(QtCore.Qt.ItemIsEditable)  # Allow editing
#         self.tableWidget_rainfall_timing.setItem(
#             self.tableWidget_rainfall_timing.rowCount() - 1, 1, float_item)

#         # Last column: String (editable)
#         string_item = QtWidgets.QTableWidgetItem("")
#         string_item.setFlags(QtCore.Qt.ItemIsEditable)  # Allow editing
#         self.tableWidget_rainfall_timing.setItem(
#             self.tableWidget_rainfall_timing.rowCount() - 1, 2, string_item)

#     def onRainfallTimingCellChanged(self, row, column):
#         # Validate the data in the current row
#         if all(self.tableWidget_rainfall_timing.item(row, col) is not None and
#                self.tableWidget_rainfall_timing.item(row, col).text() != ""
#                for col in range(3)):  # Assuming 3 columns
#             self.addRainfallTimingEmptyRow()

#     def onAccept(self):
#         self.accept()

#     def onReject(self):
#         self.reject()
