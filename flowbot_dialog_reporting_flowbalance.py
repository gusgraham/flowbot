from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from flowbot_monitors import flowMonitors
from flowbot_survey_events import surveyEvents

from ui_elements.ui_flowbot_dialog_reporting_flowbalance_base import Ui_Dialog


class flowbot_dialog_reporting_flowbalance(QtWidgets.QDialog, Ui_Dialog):

    def __init__(self, oFM, oSE, parent=None):
        """Constructor."""
        super(flowbot_dialog_reporting_flowbalance, self).__init__(parent)
        self.setupUi(self)

        self.openFlowMonitors: flowMonitors = oFM
        self.openSurveyEvents: surveyEvents = oSE
        self.outputFileSpec: str = ""
        self.fmCheckCount: int = 0

        self.refreshFlowMonitorListWidget()
        self.refreshSurveyEventCombo()
        self.checkAll()
        # self.refreshEventsListWidget()

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)
        self.btnOutput.clicked.connect(self.saveOutputAs)
        self.btnCheckAll.clicked.connect(self.checkAll)
        self.btnCheckNone.clicked.connect(self.checkNone)

        self.lst_FlowMonitors.itemChanged.connect(self.enableButtons)
        # self.lst_Events.itemChanged.connect(self.enableButtons)

        self.enableButtons()

    def checkAll(self):

        for i in range(self.lst_FlowMonitors.count()):
            it = self.lst_FlowMonitors.item(i)
            it.setCheckState(Qt.Checked)

    def checkNone(self):
        for i in range(self.lst_FlowMonitors.count()):
            it = self.lst_FlowMonitors.item(i)
            it.setCheckState(Qt.Unchecked)

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
        self.fmCheckCount = 0
        # self.seCheckCount = 0
        for index in range(self.lst_FlowMonitors.count()):
            if self.lst_FlowMonitors.item(index).checkState() == Qt.Checked:
                self.fmCheckCount += 1
        # if self.chkFullPeriodData.isChecked():
        #     self.seCheckCount += 1
        # for index in range(self.lst_Events.count()):
        #     if self.lst_Events.item(index).checkState() == Qt.Checked:
        #         self.seCheckCount += 1

    def enableButtons(self):
        self.updateCheckCount()

        if len(self.outputFileSpec) > 0 and self.fmCheckCount > 0:
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
