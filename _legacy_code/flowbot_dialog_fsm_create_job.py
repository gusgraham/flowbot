from PyQt5 import QtWidgets
from PyQt5.QtCore import QDate

from ui_elements.ui_flowbot_dialog_fsm_create_job_base import Ui_Dialog


class flowbot_dialog_fsm_create_job(QtWidgets.QDialog, Ui_Dialog):

    def __init__(self, parent=None):
        """Constructor."""
        super(flowbot_dialog_fsm_create_job, self).__init__(parent)
        self.setupUi(self)

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)

        # self.dte_fsm_survey_start.dateChanged.connect(self.on_start_date_changed)
        self.chk_survey_complete.toggled.connect(self.set_enabled)
        self.dte_fsm_survey_end.dateChanged.connect(self.set_enabled)

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

    def set_enabled(self):

        self.btnOK.setEnabled(True)
        if self.chk_survey_complete.isChecked():
            if not (self.dte_fsm_survey_end.date() > self.dte_fsm_survey_start.date()):
                self.btnOK.setEnabled(False)
        
        self.dte_fsm_survey_end.setEnabled(self.chk_survey_complete.isChecked())

