from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from ui_elements.ui_flowbot_dialog_reporting_fdv_base import Ui_Dialog


class flowbot_dialog_reporting_fdv(QtWidgets.QDialog, Ui_Dialog):

    openFlowMonitors = None
    openRainGauges = None
    openSurveyEvents = None
    outputFileSpec = ""
    checkCount = 0

    def __init__(self, oFM, oRG, oSE, parent=None):
        """Constructor."""
        super(flowbot_dialog_reporting_fdv, self).__init__(parent)
        self.setupUi(self)

        self.openFlowMonitors = oFM
        self.openRainGauges = oRG
        self.openSurveyEvents = oSE

        self.refreshFlowMonitorListWidget()
        self.refreshRaingGaugeCombo()
        self.refreshSurveyEventCombo()

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)
        self.btnOutput.clicked.connect(self.saveOutputAs)

        self.checkAll(self.lst_FlowMonitors)

        self.btnFMCheckAll.clicked.connect(
            lambda: self.checkAll(self.lst_FlowMonitors))
        self.btnFMCheckNone.clicked.connect(
            lambda: self.checkNone(self.lst_FlowMonitors))
        self.lst_FlowMonitors.itemChanged.connect(self.enableButtons)

        self.enableButtons()

    def refreshFlowMonitorListWidget(self):
        self.lst_FlowMonitors.clear()
        if self.openFlowMonitors is not None:
            for fm in self.openFlowMonitors.dictFlowMonitors.items():

                newItem = QtWidgets.QListWidgetItem(
                    fm[1].monitorName, self.lst_FlowMonitors)
                newItem.setFlags(Qt.ItemIsUserCheckable |
                                 Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                newItem.setCheckState(Qt.Unchecked)
                newItem.setSelected(False)

            # for i in range(self.lst_FlowMonitors.count()):
            #     item=self.lst_FlowMonitors.item(i)
            #     item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            #     item.setCheckState(QtCore.Qt.Unchecked)

                # self.lst_FlowMonitors.addItem(fm[1].monitorName)
    def checkAll(self, myList: QtWidgets.QListWidget):

        for i in range(myList.count()):
            it = myList.item(i)
            it.setCheckState(Qt.Checked)

    def checkNone(self, myList: QtWidgets.QListWidget):
        for i in range(myList.count()):
            it = myList.item(i)
            it.setCheckState(Qt.Unchecked)

    def refreshRaingGaugeCombo(self):
        if self.openRainGauges is not None:
            for rg in self.openRainGauges.dictRainGauges.values():
                self.cboRainGauge.addItem(rg.gaugeName)

    def refreshSurveyEventCombo(self):
        if self.openSurveyEvents is not None:
            for se in self.openSurveyEvents.survEvents.values():
                self.cboEvent.addItem(se.eventName)

    def onAccept(self):
        self.updateCheckCount()
        self.accept()

    def onReject(self):
        self.reject()

    def updateCheckCount(self):
        self.checkCount = 0
        for index in range(self.lst_FlowMonitors.count()):
            if self.lst_FlowMonitors.item(index).checkState() == Qt.Checked:
                self.checkCount += 1
                # checked_items.append(self.listWidgetLabels.item(index).text())

    def enableButtons(self):
        self.updateCheckCount()

        if len(self.outputFileSpec) > 0 and self.checkCount > 0:
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
