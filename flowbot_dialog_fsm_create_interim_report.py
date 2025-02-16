from PyQt5 import QtWidgets
# from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QFileDialog

from flowbot_management import fsmProject
from ui_elements.ui_flowbot_dialog_fsm_create_interim_report import Ui_Dialog


class flowbot_dialog_fsm_create_interim_report(QtWidgets.QDialog, Ui_Dialog):

    def __init__(self, interim_id: int, fsm_project: fsmProject, parent=None):
        """Constructor."""
        super(flowbot_dialog_fsm_create_interim_report, self).__init__(parent)
        self.setupUi(self)

        self.interim_id = interim_id
        self.fsm_project = fsm_project
        self.btnOK.clicked.connect(self.onAccept)
        self.btnOK.setEnabled(False)
        self.btnCancel.clicked.connect(self.onReject)

        self.selected_folder = None

        self.btn_get_output_folder.clicked.connect(self.showFolderDialog)

        self.txt_interim_summary.setText(self.fsm_project.dict_fsm_interims[self.interim_id].interim_summary_text)

    def onAccept(self):
        self.accept()

    def onReject(self):
        self.reject()

    # def on_start_date_changed(self):
    #     self.chk_survey_complete.setEnabled(self.dte_fsm_survey_start.date() > QDate.currentDate())
    #     self.dte_fsm_survey_end.setEnabled(self.chk_survey_complete.isChecked())
    
    # def on_survey_complete_clicked(self):
    #     if self.chk_survey_complete.isChecked():
    #         self.btnOK.setEnabled(self.dte_fsm_survey_end.date() > QDate.currentDate())
    #     self.dte_fsm_survey_end.setEnabled(self.chk_survey_complete.isChecked())

    # def on_end_date_changed(self):
    #     # self.chk_survey_complete.setEnabled(self.dte_fsm_survey_start.date() > QDate.currentDate())
    #     self.btnOK.setEnabled(self.dte_fsm_survey_end.date() > QDate.currentDate())

    # def set_enabled(self):

    #     self.btnOK.setEnabled(True)
    #     if self.chk_survey_complete.isChecked():
    #         if not (self.dte_fsm_survey_end.date() > self.dte_fsm_survey_start.date()):
    #             self.btnOK.setEnabled(False)
        
    #     self.dte_fsm_survey_end.setEnabled(self.chk_survey_complete.isChecked())

    def showFolderDialog(self):
        # Show the folder selection dialog
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')

        # If a folder is selected, update the label text and enable the OK button
        if folder:
            self.txt_output_folder.setText(folder)
            self.btnOK.setEnabled(True)
        else:
            self.txt_output_folder.setText('No folder selected')
            self.btnOK.setEnabled(False)

    def showFolderDialog(self):
        # Show the folder selection dialog
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')

        # If a folder is selected, update the label text and enable the OK button
        if folder:
            self.selected_folder = folder
            self.txt_output_folder.setText(folder)
            self.btnOK.setEnabled(True)
        else:
            # If no folder is selected but a valid folder was previously selected, keep OK enabled
            if self.selected_folder:
                self.btnOK.setEnabled(True)
            else:
                self.btnOK.setEnabled(False)
