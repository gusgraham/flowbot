import os
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDialog
from PyQt5.QtCore import QDateTime
from typing import Optional
from tempfile import NamedTemporaryFile

from flowbot_dialog_fsm_add_monitor import flowbot_dialog_fsm_add_monitor
from flowbot_dialog_fsm_add_site import flowbot_dialog_fsm_add_site
from flowbot_management import fsmInstall, fsmMonitor, fsmProject, fsmSite
from ui_elements.ui_flowbot_dialog_fsm_install_base import Ui_Dialog


class flowbot_dialog_fsm_install(QtWidgets.QDialog, Ui_Dialog):

    # def __init__(self, parent, a_project: fsmProject, edit_only: bool = False, a_mon: Optional[fsmMonitor] = None, a_site: Optional[fsmSite] = None):
    def __init__(
        self,
        parent,
        a_project: fsmProject,
        a_inst: Optional[fsmInstall] = None,
        a_mon: Optional[fsmMonitor] = None,
        a_site: Optional[fsmSite] = None,
    ):
        """Constructor."""
        super(flowbot_dialog_fsm_install, self).__init__(parent)
        self.setupUi(self)

        self.a_project: Optional[fsmProject] = a_project

        if a_inst:
            self.a_inst: Optional[fsmInstall] = a_inst
            self.a_mon: Optional[fsmMonitor] = self.a_project.dict_fsm_monitors[self.a_inst.install_monitor_asset_id]
            self.a_site: Optional[fsmSite] = self.a_project.dict_fsm_sites[self.a_inst.install_site_id]
        else:
            self.a_inst: Optional[fsmInstall] = None
            self.a_mon: Optional[fsmMonitor] = a_mon
            self.a_site: Optional[fsmSite] = a_site

        # self.install_type = 'Flow Monitor'
        self.install_sheet: Optional[bytes] = None
        # self.edit_only: bool = edit_only

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)
        self.btn_get_install_sheet.clicked.connect(self.get_install_sheet)
        self.txt_install_id.textChanged.connect(self.enable_buttons)
        # self.btn_add_site.clicked.connect(self.create_new_site)
        # self.btn_add_monitor.clicked.connect(self.create_new_monitor)
        self.cbo_site_id.currentIndexChanged.connect(
            self.onSiteComboItemChanged)
        self.cbo_monitor_id.currentIndexChanged.connect(
            self.onMonitorComboItemChanged)

        self.update_combos()
        self.enable_widgets()
        self.enable_buttons()

        # if self.edit_only:

        #     self.a_inst = self.a_project.get_install_by_site(
        #         self.a_site.siteID)
        if self.a_inst:

            self.txt_install_sheet.setText(self.a_inst.install_sheet_filename)
            #     if a_inst.install_sheet is not None:
            #         with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            #             tmp_file.write(a_inst.install_sheet)
            #             tmp_file_path = tmp_file.name
            #             self.pdf_view_widget.loadPdf(tmp_file_path)
            self.txt_install_id.setText(self.a_inst.install_id)
            self.txt_client_ref.setText(self.a_inst.client_ref)
            self.dte_install_date.setDateTime(
                QDateTime(self.a_inst.install_date))
            self.cbo_fm_pipe_letter.setCurrentText(self.a_inst.fm_pipe_letter)
            self.cbo_fm_pipe_shape.setCurrentText(self.a_inst.fm_pipe_shape)
            self.txt_fm_pipe_height_mm.setText(
                str(self.a_inst.fm_pipe_height_mm))
            self.txt_fm_pipe_width_mm.setText(
                str(self.a_inst.fm_pipe_width_mm))
            self.txt_fm_pipe_depth_to_invert_mm.setText(
                str(self.a_inst.fm_pipe_depth_to_invert_mm))
            self.txt_fm_sensor_offset_mm.setText(
                str(self.a_inst.fm_sensor_offset_mm))
            self.cbo_rg_position.setCurrentText(self.a_inst.rg_position)

    def showEvent(self, event):
        super().showEvent(event)

        if self.a_inst:
            if self.a_inst.install_sheet is not None:
                with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(self.a_inst.install_sheet)
                    tmp_file_path = tmp_file.name
                    self.pdf_view_widget.loadPdf(tmp_file_path)

    def update_combos(self):

        self.block_signals(True)

        if self.a_site is not None and self.a_mon is not None:
            self.cbo_site_id.clear()
            self.cbo_site_id.addItems([self.a_site.siteID])
            self.cbo_site_id.setCurrentIndex(0)

            self.cbo_monitor_id.clear()
            self.cbo_monitor_id.addItems([self.a_mon.monitor_asset_id])
            self.cbo_monitor_id.setCurrentIndex(0)

        elif self.a_site is not None:
            self.cbo_site_id.clear()
            self.cbo_site_id.addItems([self.a_site.siteID])
            self.cbo_site_id.setCurrentIndex(0)

            self.cbo_monitor_id.clear()
            if self.a_site.siteType == 'Network Asset':
                mon_types = ['Flow Monitor', 'Depth Monitor', 'Pump Logger']
            else:
                mon_types = ['Rain Gauge']
            mon_list = self.a_project.get_available_monitor_id_list(mon_types)
            mon_list.append('New Monitor')
            mon_list.insert(0, "")
            self.cbo_monitor_id.addItems(mon_list)
            self.cbo_monitor_id.setCurrentIndex(0)

        elif self.a_mon is not None:
            self.cbo_monitor_id.clear()
            self.cbo_monitor_id.addItems([self.a_mon.monitor_asset_id])
            self.cbo_monitor_id.setCurrentIndex(0)

            self.cbo_site_id.clear()
            if self.a_mon.monitor_type in ['Flow Monitor', 'Depth Monitor', 'Pump Logger']:
                mon_type = 'Network Asset'
            else:
                mon_type = 'Location'
            site_list = self.a_project.get_available_site_id_list(mon_type)
            site_list.append('New Site')
            site_list.insert(0, "")
            self.cbo_site_id.addItems(site_list)
            self.cbo_site_id.setCurrentIndex(0)

        else:
            self.cbo_site_id.clear()
            site_list = ['']
            for a_site in self.a_project.dict_fsm_sites.values():
                if not self.a_project.site_has_install(a_site.siteID):
                    site_list.append(a_site.siteID)
            site_list.append('New Site')
            self.cbo_site_id.addItems(site_list)
            self.cbo_site_id.setCurrentIndex(0)

            self.cbo_monitor_id.clear()
            mon_list = ['']
            for a_mon in self.a_project.dict_fsm_monitors.values():
                if not self.a_project.monitor_is_installed(a_mon.monitor_asset_id):
                    mon_list.append(a_mon.monitor_asset_id)
            mon_list.append('New Monitor')
            self.cbo_monitor_id.addItems(mon_list)
            self.cbo_monitor_id.setCurrentIndex(0)

        self.block_signals(False)

    def onSiteComboItemChanged(self):

        self.block_signals(True)

        if self.cbo_site_id.currentText() == 'New Site':
            self.add_fsm_site()
        elif self.cbo_site_id.currentText() != '':
            self.a_site = self.a_project.dict_fsm_sites[self.cbo_site_id.currentText(
            )]

        self.update_combos()
        self.enable_widgets()
        self.enable_buttons()

        self.block_signals(False)

    def onMonitorComboItemChanged(self):

        self.block_signals(True)

        if self.cbo_monitor_id.currentText() == 'New Monitor':
            self.add_fsm_monitor()
        elif self.cbo_monitor_id.currentText() != '':
            self.a_mon = self.a_project.dict_fsm_monitors[self.cbo_monitor_id.currentText(
            )]

        self.update_combos()
        self.enable_widgets()
        self.enable_buttons()

        self.block_signals(False)

    def add_fsm_site(self) -> bool:

        dlg_add_site = flowbot_dialog_fsm_add_site(parent=self)
        dlg_add_site.setWindowTitle('Add Site')
        if self.a_mon is not None:
            dlg_add_site.cboSiteType.setCurrentText(self.a_mon.monitor_type)
            dlg_add_site.cboSiteType.setEnabled(False)
        # dlg_add_site.show()
        ret = dlg_add_site.exec_()
        if ret == QDialog.Accepted:

            aSite = fsmSite()
            aSite.siteID = dlg_add_site.txtSiteRefNo.text()
            aSite.siteType = dlg_add_site.cboSiteType.currentText()
            aSite.address = dlg_add_site.pteAddress.toPlainText()
            aSite.mh_ref = dlg_add_site.txt_mh_ref.text()
            aSite.w3w = dlg_add_site.txtW3W.text()
            try:
                aSite.easting = float(dlg_add_site.txt_easting.text())
            except ValueError as e:
                aSite.easting = 0.0
            try:
                aSite.northing = float(dlg_add_site.txt_northing.text())
            except ValueError as e:
                aSite.northing = 0.0

            if self.a_project.add_site(aSite):
                self.a_site = self.a_project.dict_fsm_sites[aSite.siteID]
                return True
            else:
                msg = QMessageBox(self)
                msg.setWindowIcon(self.myIcon)
                msg.critical(
                    self, 'Add Site', 'A site with that ID already exists', QMessageBox.Ok)
                return False
        else:
            return False

    def add_fsm_monitor(self) -> bool:

        dlg_add_monitor = flowbot_dialog_fsm_add_monitor(editing=False, parent=self)
        dlg_add_monitor.setWindowTitle('Add Monitor')
        if self.a_site is not None:
            # dlg_add_monitor.cbo_monitor_type.setCurrentText(
            #     self.a_mon.monitor_type)
            dlg_add_monitor.cbo_monitor_type.setCurrentText(
                self.a_site.siteType)
            dlg_add_monitor.cbo_monitor_type.setEnabled(False)
        ret = dlg_add_monitor.exec_()
        if ret == QDialog.Accepted:

            aMon = fsmMonitor()
            aMon.monitor_asset_id = dlg_add_monitor.txt_asset_id.text()
            aMon.monitor_type = dlg_add_monitor.cbo_monitor_type.currentText()
            aMon.monitor_sub_type = dlg_add_monitor.cbo_subtype.currentText()
            aMon.pmac_id = dlg_add_monitor.txt_pmac_id.text()

            if self.a_project.add_monitor(aMon):
                self.a_mon = self.a_project.dict_fsm_monitors[aMon.monitor_asset_id]
                return True
            else:
                msg = QMessageBox(self)
                msg.setWindowIcon(self.myIcon)
                msg.critical(
                    self, 'Add Monitor', 'A monitor with that ID already exists', QMessageBox.Ok)
                return False
        else:
            return False

    def block_signals(self, block):
        self.cbo_site_id.blockSignals(block)
        self.cbo_monitor_id.blockSignals(block)

    def enable_buttons(self):

        install_id = self.txt_install_id.text().strip()
        # Check if install_id is in the dictionary
        if install_id in self.a_project.dict_fsm_installs:
            exists_in_dict = True
            if self.a_inst:
                if install_id == self.a_inst.install_id:
                    exists_in_dict = False
        else:
            exists_in_dict = False
        # Enable the button only if conditions are met and install_id is not in the dictionary
        self.btnOK.setEnabled(
            self.a_mon is not None
            and self.a_site is not None
            and bool(install_id)
            and not exists_in_dict
        )

        if exists_in_dict:
            self.txt_install_id.setStyleSheet("background-color: red;")
        else:
            self.txt_install_id.setStyleSheet("")  # Reset to default

    def enable_widgets(self):

        rain_gauge = False

        if self.a_mon is not None:
            self.install_type = self.a_mon.monitor_type
            rain_gauge = self.install_type == "Rain Gauge"
        elif self.a_site is not None:
            self.install_type = self.a_site.siteType
            rain_gauge = self.install_type == "Rain Gauge"

        self.cbo_monitor_id.setEnabled(not self.a_inst)
        self.cbo_site_id.setEnabled(not self.a_inst)

        self.cbo_fm_pipe_letter.setEnabled(not rain_gauge)
        self.cbo_fm_pipe_shape.setEnabled(not rain_gauge)
        self.txt_fm_pipe_height_mm.setEnabled(not rain_gauge)
        self.txt_fm_pipe_width_mm.setEnabled(not rain_gauge)
        self.txt_fm_pipe_depth_to_invert_mm.setEnabled(not rain_gauge)
        self.txt_fm_sensor_offset_mm.setEnabled(not rain_gauge)
        self.cbo_rg_position.setEnabled(rain_gauge)

    def onAccept(self):
        self.accept()

    def onReject(self):
        self.reject()

    def create_new_site(self):

        dlg_add_site = flowbot_dialog_fsm_add_site(parent=self)
        dlg_add_site.setWindowTitle('Add Site')
        if self.a_mon is not None:
            dlg_add_site.cboSiteType.setCurrentText(self.a_mon.monitor_type)
            dlg_add_site.cboSiteType.setEnabled(False)
        # dlg_add_site.show()
        ret = dlg_add_site.exec_()
        if ret == QDialog.Accepted:

            self.a_site = fsmSite()
            self.a_site.siteID = dlg_add_site.txtSiteRefNo.text()
            self.a_site.siteType = dlg_add_site.cboSiteType.currentText()
            self.a_site.address = dlg_add_site.pteAddress.toPlainText()
            self.a_site.mh_ref = dlg_add_site.txt_mh_ref.text()
            self.a_site.w3w = dlg_add_site.txtW3W.text()
            try:
                self.a_site.easting = float(dlg_add_site.txt_easting.text())
            except ValueError as e:
                self.a_site.easting = 0.0
            try:
                self.a_site.northing = float(dlg_add_site.txt_northing.text())
            except ValueError as e:
                self.a_site.northing = 0.0

            self.enable_widgets()
            self.enable_buttons()

    def create_new_monitor(self):

        dlg_add_monitor = flowbot_dialog_fsm_add_monitor(parent=self)
        dlg_add_monitor.setWindowTitle('Add Monitor')
        if self.a_site is not None:
            dlg_add_monitor.cbo_monitor_type.setCurrentText(
                self.a_site.siteType)
            dlg_add_monitor.cbo_monitor_type.setEnabled(False)
        ret = dlg_add_monitor.exec_()
        if ret == QDialog.Accepted:

            self.a_mon = fsmMonitor()
            self.a_mon.monitor_asset_id = dlg_add_monitor.txt_asset_id.text()
            self.a_mon.monitor_type = dlg_add_monitor.cbo_monitor_type.currentText()
            self.a_mon.monitor_sub_type = dlg_add_monitor.cbo_subtype.currentText()
            self.a_mon.pmac_id = dlg_add_monitor.txt_pmac_id.text()

            self.enable_widgets()
            self.enable_buttons()

    def get_install_sheet(self) -> Optional[bytes]:

        # if self.a_inst:

        #     # a_inst = self.a_project.get_install_by_site(self.a_site.siteID)
        #     self.txt_install_sheet.setText(a_inst.install_sheet_filename)
        #     if a_inst.install_sheet is not None:
        #         with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        #             tmp_file.write(a_inst.install_sheet)
        #             tmp_file_path = tmp_file.name
        #             self.pdf_view_widget.loadPdf(tmp_file_path)

        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Open PDF File")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("PDF Files (*.pdf)")

        # Get the current file path from the QLineEdit
        current_file_path = self.txt_install_sheet.text().strip()

        # Check if the path is valid and exists
        if os.path.isfile(current_file_path):
            file_dialog.setDirectory(os.path.dirname(current_file_path))  # Set default folder

        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                pdf_file_path = selected_files[0]
                with open(pdf_file_path, "rb") as file:
                    self.install_sheet = file.read()
                    self.txt_install_sheet.setText(pdf_file_path)
                    self.pdf_view_widget.loadPdf(pdf_file_path)
