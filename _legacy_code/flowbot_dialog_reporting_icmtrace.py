from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from flowbot_verification import icmTraces

from ui_elements.ui_flowbot_dialog_reporting_icmtrace_base import Ui_Dialog


class flowbot_dialog_reporting_icmtrace(QtWidgets.QDialog, Ui_Dialog):

    def __init__(self, oIT, parent=None):
        """Constructor."""
        super(flowbot_dialog_reporting_icmtrace, self).__init__(parent)
        self.setupUi(self)

        self.openIcmTraces: icmTraces = oIT
        self.outputFileSpec = ""
        self.checkCount = 0

        self.refreshIcmTracesCombo()
        self.checkAll()
        # self.refreshLocationsListWidget()

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)
        self.btnOutput.clicked.connect(self.saveOutputAs)
        self.btnCheckAll.clicked.connect(self.checkAll)
        self.btnCheckNone.clicked.connect(self.checkNone)

        self.cboICMTraces.currentTextChanged.connect(
            self.refreshLocationsListWidget)
        self.lst_Locations.itemChanged.connect(self.enableButtons)

        self.enableButtons()

    def checkAll(self):

        for i in range(self.lst_Locations.count()):
            it = self.lst_Locations.item(i)
            it.setCheckState(Qt.Checked)

    def checkNone(self):
        for i in range(self.lst_Locations.count()):
            it = self.lst_Locations.item(i)
            it.setCheckState(Qt.Unchecked)

    def refreshIcmTracesCombo(self):
        if self.openIcmTraces is not None:
            for trace in self.openIcmTraces.dictIcmTraces.values():
                self.cboICMTraces.addItem(trace.traceID)
        self.refreshLocationsListWidget()

    def refreshLocationsListWidget(self):
        self.lst_Locations.clear()
        if self.openIcmTraces is not None:
            trace = self.openIcmTraces.dictIcmTraces[self.cboICMTraces.currentText()]
            for loc in trace.dictLocations.values():
                myText = loc.obsLocation + ' (' + loc.predLocation + ' - U/S)' if loc.upstreamEnd else loc.obsLocation + ' (' + loc.predLocation + ' - D/S)'
                newItem = QtWidgets.QListWidgetItem(myText, self.lst_Locations)
                newItem.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                newItem.setCheckState(Qt.Unchecked)
                newItem.setSelected(False)

    def onAccept(self):
        self.updateCheckCount()
        self.accept()

    def onReject(self):
        self.reject()

    def updateCheckCount(self):
        self.checkCount = 0
        for index in range(self.lst_Locations.count()):
            if self.lst_Locations.item(index).checkState() == Qt.Checked:
                self.checkCount += 1
                # checked_items.append(self.listWidgetLabels.item(index).text())

    def enableButtons(self):
        self.updateCheckCount()

        if len(self.outputFileSpec) > 0 and self.checkCount > 0:
            self.btnOK.setEnabled(True)
        else:
            self.btnOK.setEnabled(False)

    def saveOutputAs(self):
        fileSpec, filter = QtWidgets.QFileDialog.getSaveFileName(
            self, "Report Output File...", "", 'PDF files (*.pdf)')
        if len(fileSpec) == 0:
            return
        else:
            self.edtOutputFileSpec.setText(fileSpec)
            self.outputFileSpec = fileSpec
            self.enableButtons()
