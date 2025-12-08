from PyQt5 import QtWidgets
from ui_elements.ui_flowbot_dialog_projection_base import Ui_Dialog


class fsp_flowbot_projectionDialog(QtWidgets.QDialog, Ui_Dialog):

    def __init__(self, parent=None):
        """Constructor."""
        super(fsp_flowbot_projectionDialog, self).__init__(parent)
        self.setupUi(self)

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)

    def onAccept(self):
        self.accept()

    def onReject(self):
        self.reject()
