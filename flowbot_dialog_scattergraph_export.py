from PyQt5 import QtWidgets
from ui_elements.ui_flowbot_dialog_scattergraph_export_base import Ui_Dialog


class flowbot_dialog_scattergraph_export(QtWidgets.QDialog, Ui_Dialog):

    openFlowMonitors = None
    outputFolder = ""

    def __init__(self, oFM, parent=None):
        """Constructor."""
        super(flowbot_dialog_scattergraph_export, self).__init__(parent)
        self.setupUi(self)

        self.openFlowMonitors = oFM
        self.refreshFlowMonitorListWidget()
        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)
        self.btnOutput.clicked.connect(self.saveOutputAs)
        self.lst_FlowMonitors.itemSelectionChanged.connect(self.enableButtons)

        self.enableButtons()

    def saveOutputAs(self):
        fileSpec = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Scattergraph Export Location...", "", QtWidgets.QFileDialog.ShowDirsOnly)
        if len(fileSpec) == 0:
            return
        else:
            self.edtOutputFileSpec.setText(fileSpec)
            self.outputFolder = fileSpec
            self.enableButtons()

    def refreshFlowMonitorListWidget(self):
        self.lst_FlowMonitors.clear()
        if self.openFlowMonitors is not None:
            for fm in self.openFlowMonitors.dictFlowMonitors.items():
                self.lst_FlowMonitors.addItem(fm[1].monitorName)

    def onAccept(self):
        self.accept()

    def onReject(self):
        self.reject()

    def enableButtons(self):
        if len(self.outputFolder) > 0 and len(self.lst_FlowMonitors.selectedItems()) > 0:
            self.btnOK.setEnabled(True)
        else:
            self.btnOK.setEnabled(False)
