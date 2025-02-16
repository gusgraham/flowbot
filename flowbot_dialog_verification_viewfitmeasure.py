import math
import pandas as pd
from flowbot_helper import getKlingGupta, getCoeffVariation, getNashSutcliffe
from flowbot_verification import icmTraceLocation

from PyQt5 import QtWidgets

from ui_elements.ui_flowbot_dialog_verification_viewfitmeasure_base import Ui_Dialog


class flowbot_dialog_verification_viewfitmeasure(QtWidgets.QDialog, Ui_Dialog):

    traceLocation: icmTraceLocation

    plotAxisFit = None

    def __init__(self, aLoc: icmTraceLocation, isFlow=True, parent=None):
        """Constructor."""
        super(flowbot_dialog_verification_viewfitmeasure, self).__init__(parent)
        self.setupUi(self)

        self.traceLocation = aLoc

        self.plotAxisFit = self.plotCanvasFit.figure.add_subplot(111)
        self.plotCanvasFit.figure.set_dpi(100)
        self.plotCanvasFit.figure.set_figwidth(7.7)
        self.plotCanvasFit.figure.set_figheight(5.0)

        self.btnDone.clicked.connect(self.onAccept)

        self.refreshPlot()

    def onAccept(self):
        self.accept()

    def dodgyForceUpdate(self):
        oldSize = self.size()
        self.resize(oldSize.width() + 1, oldSize.height() + 1)
        self.resize(oldSize)

    def refreshPlot(self, isObs: bool = True):

        roundTo = 1/1000  # round up to 1 l/s
        ax_max = math.ceil(max(max(self.traceLocation.rawData[self.traceLocation.iObsFlow]), max(
            self.traceLocation.rawData[self.traceLocation.iPredFlow])) / roundTo) * roundTo
        if ax_max == 0:
            ax_max = 1

        # myFig = plt.figure(dpi=100, figsize=(7, 7))
        self.plotAxisFit.plot(self.traceLocation.rawData[self.traceLocation.iObsFlow],
                              self.traceLocation.rawData[self.traceLocation.iPredFlow],
                              figure=self.plotCanvasFit.figure, ls='None', label='Observed', color="red", marker="x")
        self.plotAxisFit.set_title(
            self.traceLocation.shortTitle, color='black', fontsize=12)
        perfectLine, = self.plotAxisFit.plot(
            [0, ax_max], [0, ax_max], ls='-', label='Perfect Fit', color="green")
        self.plotAxisFit.set_xlim(0, ax_max)
        self.plotAxisFit.set_ylim(0, ax_max)
        self.plotAxisFit.set_box_aspect(1)
        self.plotAxisFit.grid(visible=True, which='both', axis='both')

        self.plotAxisFit.text(ax_max * 0.93, ax_max * 0.95, perfectLine.get_label(),
                              horizontalalignment='right', verticalalignment='center')
        self.plotAxisFit.set_xlabel("Observed")
        self.plotAxisFit.set_ylabel("Predicted")

        myProps = dict(boxstyle='round', facecolor='teal', alpha=0.5)

        myDict = {'Obs': self.traceLocation.rawData[self.traceLocation.iObsFlow].copy(
        ), 'Pred': self.traceLocation.rawData[self.traceLocation.iPredFlow].copy()}
        df = pd.DataFrame(myDict)
        myKG = getKlingGupta(df, 'Obs', 'Pred')
        myNash = getNashSutcliffe(df, 'Obs', 'Pred')
        myCV = getCoeffVariation(df, 'Obs')
        plotModelEff = self.plotAxisFit.text(
            0.05, 0.95, "", transform=self.plotAxisFit.transAxes, fontsize=8, verticalalignment='top', bbox=myProps, family='serif')
        me_textstr = f'Nash Sutcliffe: {(myNash):.2f}\nKling Gupta: {(myKG):.2f}\nCVobs: {(myCV):.2f}'
        plotModelEff.set_text(me_textstr)

        self.dodgyForceUpdate()

    def enableButtons(self):
        pass
