from PyQt5 import QtWidgets

from ui_elements.ui_flowbot_dialog_fsm_set_interim_dates_base import Ui_Dialog

class flowbot_dialog_fsm_set_interim_dates(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        """Constructor."""
        super(flowbot_dialog_fsm_set_interim_dates, self).__init__(parent)
        self.setupUi(self)

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)

    def onAccept(self):
        self.accept()

    def onReject(self):
        self.reject()

    # def getDates(self):
    #     start_date = self.start_date_edit.dateTime().toPyDateTime().date()
    #     end_date = self.end_date_edit.dateTime().toPyDateTime().date()
    #     return start_date, end_date