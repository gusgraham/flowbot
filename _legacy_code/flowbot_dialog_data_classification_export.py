from PyQt5 import QtWidgets

from ui_elements.ui_flowbot_dialog_data_classification_export_base import Ui_Dialog


class flowbot_dialog_data_classification_export(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        """Constructor."""
        super(flowbot_dialog_data_classification_export, self).__init__(parent)
        self.setupUi(self)

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)
        self.btnOutput.clicked.connect(self.saveOutputAs)

    def saveOutputAs(self):
        fileSpec, a_filter = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Classification Output...", "", 'Excel File (*.xlsx)')
        if len(fileSpec) == 0:
            return
        else:
            self.edtOutputFileSpec.setText(fileSpec)
            self.outputFileSpec = fileSpec

    def onAccept(self):
        self.accept()

    def onReject(self):
        self.reject()
