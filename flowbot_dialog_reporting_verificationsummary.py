from PyQt5 import QtWidgets
from flowbot_verification import icmTraces
from ui_elements.ui_flowbot_dialog_reporting_verificationsummary_base import Ui_Dialog


class flowbot_dialog_reporting_verificationsummary(QtWidgets.QDialog, Ui_Dialog):

    def __init__(self, oIT, parent=None):
        """Constructor."""
        super(flowbot_dialog_reporting_verificationsummary, self).__init__(parent)
        self.setupUi(self)

        self.openIcmTraces: icmTraces = oIT
        self.outputFileSpec: str = ""
        self.checkCount: int = 0        

        self.refreshIcmTracesCombo()

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)
        self.btnOutput.clicked.connect(self.saveOutputAs)

        self.enableButtons()

    def refreshIcmTracesCombo(self):
        if self.openIcmTraces is not None:
            for trace in self.openIcmTraces.dictIcmTraces.values():
                self.cboICMTraces.addItem(trace.traceID)

    def onAccept(self):
        self.accept()

    def onReject(self):
        self.reject()

    def enableButtons(self):
        if len(self.outputFileSpec) > 0:
            self.btnOK.setEnabled(True)
        else:
            self.btnOK.setEnabled(False)

    def saveOutputAs(self):
        fileSpec, a_filter = QtWidgets.QFileDialog.getSaveFileName(
            self, "Report Output File...", "", 'PDF files (*.pdf)')
        if len(fileSpec) == 0:
            return
        else:
            self.edtOutputFileSpec.setText(fileSpec)
            self.outputFileSpec = fileSpec
            self.enableButtons()
