from PyQt5 import QtWidgets

# uiFileSpec = resource_path('ui_elements\\fsp_flowbot_event_dialog_base.ui')
# FORM_CLASS, _ = uic.loadUiType(uiFileSpec)

# class flowbot_dialog_event(QtWidgets.QDialog, FORM_CLASS):

from ui_elements.ui_flowbot_dialog_event_base import Ui_Dialog


class flowbot_dialog_event(QtWidgets.QDialog, Ui_Dialog):

    def __init__(self, parent=None):
        """Constructor."""
        super(flowbot_dialog_event, self).__init__(parent)
        self.setupUi(self)

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)

    def onAccept(self):
        self.accept()

    def onReject(self):
        self.reject()
