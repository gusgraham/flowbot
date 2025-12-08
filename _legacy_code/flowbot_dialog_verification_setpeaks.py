from typing import Optional
import numpy as np
from scipy.signal import find_peaks, peak_prominences, peak_widths
from matplotlib.dates import DateFormatter
from matplotlib.ticker import MaxNLocator, FuncFormatter
from flowbot_verification import icmTraceLocation

from PyQt5 import QtWidgets

from ui_elements.ui_flowbot_dialog_verification_setpeaks_base import Ui_Dialog


class flowbot_dialog_verification_setpeaks(QtWidgets.QDialog, Ui_Dialog):

    traceLocation: Optional[icmTraceLocation] = None

    plotAxisObs = None
    plotAxisPred = None

    obsIndex = 0
    predIndex = 1

    isFlowPeaksReview: bool = True
    currentLabel: str = ''
    currentObsLabel2: str = ''
    currentPredLabel2: str = ''

    def __init__(self, aLoc: icmTraceLocation, isFlow=True, parent=None):
        """Constructor."""
        super(flowbot_dialog_verification_setpeaks, self).__init__(parent)
        self.setupUi(self)

        self.spinSmoothingObs.setDecimals(2)
        self.spinSmoothingObs.setMinimum(0)
        self.spinSmoothingObs.setMaximum(1)
        self.spinSmoothingObs.setSingleStep(0.01)
        self.spinSmoothingPred.setDecimals(2)
        self.spinSmoothingPred.setMinimum(0)
        self.spinSmoothingPred.setMaximum(1)
        self.spinSmoothingPred.setSingleStep(0.01)

        self.spinProminanceObs.setDecimals(4)
        self.spinProminanceObs.setMinimum(0.0009)
        self.spinProminanceObs.setSingleStep(0.0001)
        self.spinProminancePred.setDecimals(4)
        self.spinProminancePred.setMinimum(0.0009)
        self.spinProminancePred.setSingleStep(0.0001)

        self.traceLocation = aLoc
        if isFlow:
            self.obsIndex = self.traceLocation.iObsFlow
            self.predIndex = self.traceLocation.iPredFlow
            self.isFlowPeaksReview = True
            self.currentLabel = "Flow l/s"
            self.currentObsLabel2 = 'Obs. Flow (Smoothed)'
            self.currentPredLabel2 = 'Pred. Flow (Smoothed)'
        else:
            self.obsIndex = self.traceLocation.iObsDepth
            self.predIndex = self.traceLocation.iPredDepth
            self.isFlowPeaksReview = False
            self.currentLabel = "Depth mm"
            self.currentObsLabel2 = 'Obs. Depth (Smoothed)'
            self.currentPredLabel2 = 'Pred. Depth (Smoothed)'

        if self.chkEditManuallyObs.isChecked():
            if len(self.traceLocation.smoothedData[self.obsIndex]) == 0:
                self.traceLocation.updatePeaks(self.obsIndex)
            if len(self.traceLocation.smoothedData[self.predIndex]) == 0:
                self.traceLocation.updatePeaks(self.predIndex)
        else:
            if len(self.traceLocation.smoothedData[self.obsIndex]) == 0:
                self.traceLocation.updatePeaks(
                    self.obsIndex, self.spinNoOfPeaksObs.value())
            if len(self.traceLocation.smoothedData[self.predIndex]) == 0:
                self.traceLocation.updatePeaks(self.predIndex)

        self.plotAxisObs = self.plotCanvasObs.figure.add_subplot(111)
        self.plotCanvasObs.figure.set_dpi(100)
        self.plotCanvasObs.figure.set_figwidth(7.7)
        self.plotCanvasObs.figure.set_figheight(5.0)

        self.plotAxisPred = self.plotCanvasPred.figure.add_subplot(111)
        self.plotCanvasPred.figure.set_dpi(100)
        self.plotCanvasPred.figure.set_figwidth(7.7)
        self.plotCanvasPred.figure.set_figheight(5.0)

        self.btnDone.clicked.connect(self.onAccept)

        self.initializeSpinners()

        self.spinSmoothingObs.valueChanged.connect(
            lambda: self.updateValues(True))
        self.spinProminanceObs.valueChanged.connect(
            lambda: self.updateValues(True))
        self.spinWidthObs.valueChanged.connect(lambda: self.updateValues(True))
        self.spinDistanceObs.valueChanged.connect(
            lambda: self.updateValues(True))

        self.spinSmoothingPred.valueChanged.connect(
            lambda: self.updateValues(False))
        self.spinProminancePred.valueChanged.connect(
            lambda: self.updateValues(False))
        self.spinWidthPred.valueChanged.connect(
            lambda: self.updateValues(False))
        self.spinDistancePred.valueChanged.connect(
            lambda: self.updateValues(False))

        self.chkEditManuallyObs.toggled.connect(self.enableButtons)
        self.spinNoOfPeaksObs.valueChanged.connect(
            lambda: self.updateValues(True))
        self.chkEditManuallyPred.toggled.connect(self.enableButtons)
        self.spinNoOfPeaksPred.valueChanged.connect(
            lambda: self.updateValues(False))
        self.enableButtons()

        self.refreshPlot(True)
        self.refreshPlot(False)

    def updateValues(self, isObs: bool = True, smoothingChanged: bool = True):

        if isObs:
            self.traceLocation.frac[self.obsIndex] = self.spinSmoothingObs.value(
            )
            self.traceLocation.peaks_prominance[self.obsIndex] = self.spinProminanceObs.value(
            )
            self.traceLocation.peaks_width[self.obsIndex] = self.spinWidthObs.value(
            )
            self.traceLocation.peaks_distance[self.obsIndex] = self.spinDistanceObs.value(
            )
            if self.chkEditManuallyObs.isChecked():
                self.traceLocation.updatePeaks(self.obsIndex)
            else:
                self.traceLocation.updatePeaks(
                    self.obsIndex, self.spinNoOfPeaksObs.value())
            self.refreshPlot(True)
        else:
            self.traceLocation.frac[self.predIndex] = self.spinSmoothingPred.value(
            )
            self.traceLocation.peaks_prominance[self.predIndex] = self.spinProminancePred.value(
            )
            self.traceLocation.peaks_width[self.predIndex] = self.spinWidthPred.value(
            )
            self.traceLocation.peaks_distance[self.predIndex] = self.spinDistancePred.value(
            )
            if self.chkEditManuallyPred.isChecked():
                self.traceLocation.updatePeaks(self.predIndex)
            else:
                self.traceLocation.updatePeaks(
                    self.predIndex, self.spinNoOfPeaksPred.value())
            self.refreshPlot(False)

        self.updateProminanceAndWidthSpinners()

    def initializeSpinners(self):

        if self.isFlowPeaksReview:
            self.spinNoOfPeaksObs.setValue(
                self.traceLocation.getNoOfPeaks(self.traceLocation.iObsFlow))
            self.spinNoOfPeaksPred.setValue(
                self.traceLocation.getNoOfPeaks(self.traceLocation.iPredFlow))
        else:
            self.spinNoOfPeaksObs.setValue(
                self.traceLocation.getNoOfPeaks(self.traceLocation.iObsDepth))
            self.spinNoOfPeaksPred.setValue(
                self.traceLocation.getNoOfPeaks(self.traceLocation.iPredDepth))

        self.spinSmoothingObs.setMinimum(0)
        self.spinSmoothingObs.setMaximum(1)
        self.spinSmoothingObs.setValue(
            self.traceLocation.frac[self.obsIndex])

        self.spinSmoothingPred.setMinimum(0)
        self.spinSmoothingPred.setMaximum(1)
        self.spinSmoothingPred.setValue(
            self.traceLocation.frac[self.predIndex])

        maxObsProm, maxObsWidth = self.calculateMaxProminanceAndWidth(
            self.traceLocation.smoothedData[self.obsIndex])
        self.spinProminanceObs.setMinimum(0.0009)
        self.spinProminanceObs.setMaximum(maxObsProm)
        self.spinProminanceObs.setValue(
            min(self.traceLocation.peaks_prominance[self.obsIndex], maxObsProm))
        maxPredProm, maxPredWidth = self.calculateMaxProminanceAndWidth(
            self.traceLocation.smoothedData[self.predIndex])
        self.spinProminancePred.setMinimum(0.0009)
        self.spinProminancePred.setMaximum(maxPredProm)
        self.spinProminancePred.setValue(
            min(self.traceLocation.peaks_prominance[self.predIndex], maxPredProm))

        self.spinWidthObs.setMinimum(1)
        self.spinWidthObs.setMaximum(int(maxObsWidth))
        self.spinWidthObs.setValue(
            min(self.traceLocation.peaks_width[self.obsIndex], int(maxObsWidth)))
        self.spinWidthPred.setMinimum(1)
        self.spinWidthPred.setMaximum(int(maxPredWidth))
        self.spinWidthPred.setValue(
            min(self.traceLocation.peaks_width[self.predIndex], int(maxPredWidth)))

        self.spinDistanceObs.setMinimum(1)
        self.spinDistanceObs.setMaximum(
            max(1, len(self.traceLocation.smoothedData[self.obsIndex])))
        self.spinDistanceObs.setValue(max(1, min(
            self.traceLocation.peaks_distance[self.obsIndex], len(self.traceLocation.smoothedData[self.obsIndex]))))
        self.spinDistancePred.setMinimum(1)
        self.spinDistancePred.setMaximum(
            max(1, len(self.traceLocation.smoothedData[self.predIndex])))
        self.spinDistancePred.setValue(max(1, min(
            self.traceLocation.peaks_distance[self.predIndex], len(self.traceLocation.smoothedData[self.predIndex]))))

    def updateProminanceAndWidthSpinners(self):

        maxObsProm, maxObsWidth = self.calculateMaxProminanceAndWidth(
            self.traceLocation.smoothedData[self.obsIndex])
        self.spinProminanceObs.setMaximum(maxObsProm)
        self.spinProminanceObs.setValue(
            min(self.traceLocation.peaks_prominance[self.obsIndex], maxObsProm))
        maxPredProm, maxPredWidth = self.calculateMaxProminanceAndWidth(
            self.traceLocation.smoothedData[self.predIndex])
        self.spinProminancePred.setMaximum(maxPredProm)
        self.spinProminancePred.setValue(
            min(self.traceLocation.peaks_prominance[self.predIndex], maxPredProm))

        self.spinWidthObs.setMaximum(int(maxObsWidth))
        self.spinWidthObs.setValue(
            min(self.traceLocation.peaks_width[self.obsIndex], int(maxObsWidth)))
        self.spinWidthPred.setMaximum(int(maxPredWidth))
        self.spinWidthPred.setValue(
            min(self.traceLocation.peaks_width[self.predIndex], int(maxPredWidth)))

    def calculateMaxProminanceAndWidth(self, lstData: list[float]):

        peaks, _ = find_peaks(np.asarray(lstData),
                              prominence=0, width=1, distance=1, threshold=0)
        proms = peak_prominences(np.asarray(lstData), peaks)
        widths = peak_widths(np.asarray(lstData), peaks)

        maxProm = 0
        maxWidth = 0

        if len(proms[0]) > 0:
            maxProm = float(np.max(proms[0]))

        if len(widths[0]) > 0:
            maxWidth = float(np.max(widths[0]))

        return (maxProm, maxWidth)

    def onAccept(self):
        self.accept()

    def dodgyForceUpdate(self):
        oldSize = self.size()
        self.resize(oldSize.width() + 1, oldSize.height() + 1)
        self.resize(oldSize)

    def refreshPlot(self, isObs: bool = True):

        major_tick_format = DateFormatter("%d/%m/%Y %H:%M")

        flowColour = "indianred"
        obsSmColour = "steelblue"
        obsSmPeakColour = "navy"

        if isObs:
            self.plotAxisObs.clear()
            self.plotAxisObs.plot(
                self.traceLocation.dates, self.traceLocation.rawData[self.obsIndex], '-', linewidth=1.1, label='', color=flowColour)

            self.plotAxisObs.yaxis.set_major_locator(MaxNLocator(integer=True))
            self.plotAxisObs.xaxis.set_major_locator(
                MaxNLocator(integer=False))
            self.plotAxisObs.xaxis.set_major_formatter(
                FuncFormatter(major_tick_format))
            self.plotAxisObs.set_ylabel(self.currentLabel, fontsize=8)
            self.plotAxisObs.tick_params(axis='y', which='major', labelsize=8)

            self.plotAxisObs.plot(self.traceLocation.dates, self.traceLocation.smoothedData[
                                  self.obsIndex], '-', linewidth=1.1, label=self.currentObsLabel2, color=obsSmColour)

            self.plotAxisObs.plot(
                self.traceLocation.peaksDates[self.obsIndex], self.traceLocation.peaksData[self.obsIndex], 'o', label='Peaks (Smoothed)', color=obsSmPeakColour)

            self.plotAxisObs.grid(True)

            self.plotCanvasObs.figure.autofmt_xdate()
            self.plotCanvasObs.figure.subplots_adjust(
                left=0.09, right=0.98, bottom=0.17, top=0.94)

        else:
            self.plotAxisPred.clear()
            self.plotAxisPred.plot(
                self.traceLocation.dates, self.traceLocation.rawData[self.predIndex], '-', linewidth=1.1, label='', color=flowColour)

            self.plotAxisPred.yaxis.set_major_locator(
                MaxNLocator(integer=True))
            self.plotAxisPred.xaxis.set_major_locator(
                MaxNLocator(integer=False))
            self.plotAxisPred.xaxis.set_major_formatter(
                FuncFormatter(major_tick_format))
            self.plotAxisPred.set_ylabel(self.currentLabel, fontsize=8)
            self.plotAxisPred.tick_params(axis='y', which='major', labelsize=8)

            self.plotAxisPred.plot(self.traceLocation.dates, self.traceLocation.smoothedData[
                                   self.predIndex], '-', linewidth=1.1, label=self.currentPredLabel2, color=obsSmColour)

            self.plotAxisPred.plot(
                self.traceLocation.peaksDates[self.predIndex], self.traceLocation.peaksData[self.predIndex], 'o', label='Peaks (Smoothed)', color=obsSmPeakColour)

            self.plotAxisPred.grid(True)

            self.plotCanvasPred.figure.autofmt_xdate()
            self.plotCanvasPred.figure.subplots_adjust(
                left=0.09, right=0.98, bottom=0.17, top=0.94)

        self.dodgyForceUpdate()

    def enableButtons(self):

        self.lblProminanceObs.setVisible(self.chkEditManuallyObs.isChecked())
        self.spinProminanceObs.setVisible(self.chkEditManuallyObs.isChecked())
        self.lblWidthObs.setVisible(self.chkEditManuallyObs.isChecked())
        self.spinWidthObs.setVisible(self.chkEditManuallyObs.isChecked())
        self.lblDistanceObs.setVisible(self.chkEditManuallyObs.isChecked())
        self.spinDistanceObs.setVisible(self.chkEditManuallyObs.isChecked())

        self.lblProminancePred.setVisible(self.chkEditManuallyPred.isChecked())
        self.spinProminancePred.setVisible(
            self.chkEditManuallyPred.isChecked())
        self.lblWidthPred.setVisible(self.chkEditManuallyPred.isChecked())
        self.spinWidthPred.setVisible(self.chkEditManuallyPred.isChecked())
        self.lblDistancePred.setVisible(self.chkEditManuallyPred.isChecked())
        self.spinDistancePred.setVisible(self.chkEditManuallyPred.isChecked())
