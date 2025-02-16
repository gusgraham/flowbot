from flowbot_graphing import graphRainfallAnalysis

from PyQt5 import (QtWidgets, QtGui)
from PyQt5.QtCore import (Qt)

from ui_elements.ui_flowbot_dialog_event_analysis_params_base import Ui_Dialog


class flowbot_dialog_event_analysis_params(QtWidgets.QDialog, Ui_Dialog):

    aRainfallAnalysis = None

    def __init__(self, aRA, parent=None):
        """Constructor."""
        super(flowbot_dialog_event_analysis_params, self).__init__(parent)
        self.setupUi(self)

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)

        self.aRainfallAnalysis = aRA

        self.edtRainfallDepthTolerance.setValidator(
            QtGui.QIntValidator(0, 1000))
        self.edtPrecedingDryDays.setValidator(QtGui.QIntValidator(0, 1000))
        self.edtConsecZeros.setValidator(QtGui.QIntValidator(0, 1000))
        self.edtReqDepth.setValidator(QtGui.QIntValidator(0, 1000))
        self.edtReqIntensity.setValidator(QtGui.QDoubleValidator(0, 1000, 1))
        self.edtReqIntensityDuration.setValidator(QtGui.QIntValidator(0, 1000))
        self.edtPartialEventThreshold.setValidator(QtGui.QIntValidator(0, 100))

        self.edtRainfallDepthTolerance.setText(
            str(self.aRainfallAnalysis.rainfallDepthTolerance))
        self.edtPrecedingDryDays.setText(
            str(self.aRainfallAnalysis.precedingDryDays))
        self.edtConsecZeros.setText(str(self.aRainfallAnalysis.consecZero))
        self.edtReqDepth.setText(str(self.aRainfallAnalysis.requiredDepth))
        self.edtReqIntensity.setText(
            str(self.aRainfallAnalysis.requiredIntensity))
        self.edtReqIntensityDuration.setText(
            str(self.aRainfallAnalysis.requiredIntensityDuration))
        self.edtPartialEventThreshold.setText(
            str(self.aRainfallAnalysis.partialPercent))
        if self.aRainfallAnalysis.useConsecutiveIntensities:
            self.chkConsecIntensities.setCheckState(Qt.Checked)
        else:
            self.chkConsecIntensities.setCheckState(Qt.Unchecked)

    def onAccept(self):

        self.aRainfallAnalysis.rainfallDepthTolerance = int(
            self.edtRainfallDepthTolerance.text())
        self.aRainfallAnalysis.precedingDryDays = int(
            self.edtPrecedingDryDays.text())

        self.aRainfallAnalysis.consecZero = int(self.edtConsecZeros.text())
        self.aRainfallAnalysis.requiredDepth = int(self.edtReqDepth.text())
        self.aRainfallAnalysis.requiredIntensity = float(
            self.edtReqIntensity.text())
        self.aRainfallAnalysis.requiredIntensityDuration = int(
            self.edtReqIntensityDuration.text())
        self.aRainfallAnalysis.partialPercent = int(
            self.edtPartialEventThreshold.text())
        if self.chkConsecIntensities.checkState() == Qt.Checked:
            self.aRainfallAnalysis.useConsecutiveIntensities = True
        else:
            self.aRainfallAnalysis.useConsecutiveIntensities = False

        if self.matchDefaultParams():
            self.aRainfallAnalysis.useDefaultParams = True
        else:
            self.aRainfallAnalysis.useDefaultParams = False

        self.accept()

    def onReject(self):
        self.reject()

    def matchDefaultParams(self):

        if (graphRainfallAnalysis.rainfallDepthTolerance == int(self.edtRainfallDepthTolerance.text()) and
            graphRainfallAnalysis.precedingDryDays == int(self.edtPrecedingDryDays.text()) and
            graphRainfallAnalysis.consecZero == int(self.edtConsecZeros.text()) and
            graphRainfallAnalysis.requiredDepth == int(self.edtReqDepth.text()) and
            graphRainfallAnalysis.requiredIntensity == float(self.edtReqIntensity.text()) and
            graphRainfallAnalysis.requiredIntensityDuration == int(self.edtReqIntensityDuration.text()) and
            graphRainfallAnalysis.partialPercent == int(self.edtPartialEventThreshold.text()) and
            True if graphRainfallAnalysis.useConsecutiveIntensities and
            self.chkConsecIntensities.checkState() == Qt.Checked else False):
            return True
        else:
            return False


