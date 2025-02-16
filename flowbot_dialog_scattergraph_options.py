from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
from flowbot_graphing import graphScatter

from ui_elements.ui_flowbot_dialog_scattergraph_options_base import Ui_Dialog


class flowbot_dialog_scattergraphoptions(QtWidgets.QDialog, Ui_Dialog):

    def __init__(self, scatter, parent=None):
        """Constructor."""
        super(flowbot_dialog_scattergraphoptions, self).__init__(parent)
        self.setupUi(self)

        self.chkFullPeriodData.clicked.connect(self.enableButtons)
        # self.chkEventData.clicked.connect(self.enableButtons)
        self.chkIgnoreDataAboveSoffit.clicked.connect(self.enableButtons)
        self.chkIgnoreZeros.clicked.connect(self.enableButtons)
        self.chkLabelOnHover.clicked.connect(self.enableButtons)
        self.chkModelData.clicked.connect(self.enableButtons)
        self.chkPipeProfile.clicked.connect(self.enableButtons)
        self.chkCBWData.clicked.connect(self.enableButtons)
        self.chkIsoQ.clicked.connect(self.enableButtons)
        self.edtMinIsoQ.setValidator(QtGui.QDoubleValidator())
        self.edtMaxIsoQ.setValidator(QtGui.QDoubleValidator())

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)

        self.aScattergraph: graphScatter = scatter

        self.set_check_state(self.chkFullPeriodData, self.aScattergraph.plotFPData)
        self.set_check_state(self.chkIgnoreDataAboveSoffit, self.aScattergraph.ignoreDataAboveSoffit)
        self.set_check_state(self.chkIgnoreZeros, self.aScattergraph.ignoreZeros)
        self.set_check_state(self.chkLabelOnHover, self.aScattergraph.labelOnHover)
        self.set_check_state(self.chkModelData, self.aScattergraph.plotModelData)
        self.set_check_state(self.chkPipeProfile, self.aScattergraph.showPipeProfile)
        self.set_check_state(self.chkCBWData, self.aScattergraph.plotCBWLine)
        self.set_check_state(self.chkIsoQ, self.aScattergraph.plotIsoQLines)

        self.rbnVelocity.setChecked(self.aScattergraph.plotVelocityScattergraph)
        self.rbnFlow.setChecked(not self.aScattergraph.plotVelocityScattergraph)
        self.spnNoOfLines.setValue(self.aScattergraph.noOfIsoQLines)
        self.edtMinIsoQ.setText(str(self.aScattergraph.isoQLBound))
        self.edtMaxIsoQ.setText(str(self.aScattergraph.isoQUBound))

        self.enableButtons()

    def set_check_state(self, check_box, state):
        check_box.setCheckState(Qt.Checked if state else Qt.Unchecked)

    def onAccept(self):
        self.accept()

    def onReject(self):
        self.reject()

    def enableButtons(self):

        self.chkIgnoreDataAboveSoffit.setEnabled(False)
        self.grpIsoQ.setEnabled(False)
        self.grpModelData.setEnabled(False)
        self.chkPipeProfile.setEnabled(False)
        self.chkCBWData.setEnabled(False)
        self.chkIsoQ.setEnabled(False)
        self.grpIsoQ.setEnabled(False)

        # if self.aScattergraph.plotFMHasModelData():
        if self.aScattergraph.plot_flow_monitor:
            if self.aScattergraph.plot_flow_monitor.hasModelData:
                self.grpModelData.setEnabled(True)
                self.chkIgnoreDataAboveSoffit.setEnabled(True)

        if self.chkModelData.isChecked():
            self.chkPipeProfile.setEnabled(True)
            self.chkCBWData.setEnabled(True)
            self.chkIsoQ.setEnabled(True)
            if self.chkIsoQ.isChecked():
                self.grpIsoQ.setEnabled(True)
