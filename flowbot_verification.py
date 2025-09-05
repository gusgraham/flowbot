# from configparser import Interpolation
import os
from datetime import datetime
from matplotlib import cm
from scipy.signal import find_peaks, peak_prominences
from statsmodels.nonparametric.smoothers_lowess import lowess
import numpy as np
import pandas as pd
from PyQt5.QtGui import (QColor)
from PyQt5.QtWidgets import (QMessageBox, QInputDialog)
from typing import Dict, Union, Optional
from datetime import datetime
import time
import sqlite3
from flowbot_helper import (getNashSutcliffe, serialize_list, deserialize_list, serialize_timestamp_list,
                            deserialize_timestamp_list)
from flowbot_database import Tables
# from contextlib import closing
from flowbot_logging import get_logger
logger = get_logger('flowbot_logger')

class icmTraceLocation(object):

    # index: int = -1
    # pageTitle: str = ''
    # shortTitle: str = ''
    # obsLocation: str = ''
    # predLocation: str = ''
    # upstreamEnd: bool = False
    # trTimestep: int = 0

    # isCritical: bool = False
    # isSurcharged: bool = False

    iObsFlow = 0
    iPredFlow = 1
    iObsDepth = 2
    iPredDepth = 3
    iObsVelocity = 4
    iPredVelocity = 5

    # dates: list[datetime] = []
    # rawData: list[list[float]] = [[], [], [], [], [], []]
    # smoothedData: list[list[float]] = [[], [], [], []]
    # peaksDates: list[list[datetime]] = [[], [], [], []]
    # peaksData: list[list[float]] = [[], [], [], []]
    # peaksInitialized: list[bool] = [False, False, False, False]

    # verifyForFlow: bool = False
    # verifyForDepth: bool = False

    # frac: list[float] = [0.0, 0.0, 0.0, 0.0]
    # # frac: list[float] = [0.12, 0, 0.12, 0]
    # peaks_prominance: list[float] = [0.0009, 0.0009, 0.0009, 0.0009]
    # peaks_width: list[float] = [1, 1, 1, 1]
    # peaks_distance: list[float] = [1, 1, 1, 1]

    # flowNSE: float = -99999
    # flowTp_Diff_Hrs: float = -99999
    # flowQp_Diff_Pcnt: float = -99999
    # flowVol_Diff_Pcnt: float = -99999
    # depthTp_Diff_Hrs: float = -99999
    # depthDp_Diff_Pcnt: float = -99999
    # depthDp_Diff: float = -99999

    # verificationDepthScore: float = -1
    # verificationFlowScore: float = -1

    # verificationDepthComment: str = ''
    # verificationFlowComment: str = ''
    # verificationOverallComment: str = ''

    def __init__(self):

        self.index = -1
        self.pageTitle = ''
        self.shortTitle = ''
        self.obsLocation = ''
        self.predLocation = ''
        self.upstreamEnd = False
        self.trTimestep = 0
        self.isCritical = False
        self.isSurcharged = False
        self.dates = []
        self.rawData = [[], [], [], [], [], []]
        self.smoothedData = [[], [], [], []]
        self.peaksDates = [[], [], [], []]
        self.peaksData = [[], [], [], []]
        self.peaksInitialized = [False, False, False, False]
        self.verifyForFlow: bool = False
        self.verifyForDepth: bool = False
        self.frac = [0.0, 0.0, 0.0, 0.0]
        self.peaks_prominance = [0.0009, 0.0009, 0.0009, 0.0009]
        self.peaks_width = [1, 1, 1, 1]
        self.peaks_distance = [1, 1, 1, 1]
        self.flowNSE = -99999
        self.flowTp_Diff_Hrs = -99999
        self.flowQp_Diff_Pcnt = -99999
        self.flowVol_Diff_Pcnt = -99999
        self.depthTp_Diff_Hrs = -99999
        self.depthDp_Diff_Pcnt = -99999
        self.depthDp_Diff = -99999
        self.verificationDepthScore = -1
        self.verificationFlowScore = -1
        self.verificationDepthComment = ''
        self.verificationFlowComment = ''
        self.verificationOverallComment = ''

    def from_database_row(self, row):
        self.index = row[0]
        self.pageTitle = row[2]
        self.shortTitle = row[3]
        self.obsLocation = row[4]
        self.predLocation = row[5]
        self.upstreamEnd = bool(row[6])
        self.trTimestep = int(row[7])
        self.isCritical = bool(row[8])
        self.isSurcharged = bool(row[9])
        self.dates = deserialize_list(row[10])
        self.rawData = deserialize_list(row[11])
        self.smoothedData = deserialize_list(row[12])
        self.peaksDates = deserialize_timestamp_list(row[13])
        self.peaksData = deserialize_list(row[14])
        self.peaksInitialized = deserialize_list(row[15])
        self.verifyForFlow = bool(row[16])
        self.verifyForDepth = bool(row[17])
        self.frac = deserialize_list(row[18])
        self.peaks_prominance = deserialize_list(row[19])
        self.peaks_width = deserialize_list(row[20])
        self.peaks_distance = deserialize_list(row[21])
        self.flowNSE = row[22]
        self.flowTp_Diff_Hrs = row[23]
        self.flowQp_Diff_Pcnt = row[24]
        self.flowVol_Diff_Pcnt = row[25]
        self.depthTp_Diff_Hrs = row[26]
        self.depthDp_Diff_Pcnt = row[27]
        self.depthDp_Diff = row[28]
        self.verificationDepthScore = row[29]
        self.verificationFlowScore = row[30]
        self.verificationDepthComment = row[31]
        self.verificationFlowComment = row[32]
        self.verificationOverallComment = row[33]

    def getColorFromScore(self):

        if self.verifyForFlow and not self.verifyForDepth:
            verificationScore = self.verificationFlowScore
        elif self.verifyForDepth and not self.verifyForFlow:
            verificationScore = self.verificationDepthScore
        elif self.verifyForDepth and self.verifyForFlow:
            verificationScore = (
                self.verificationDepthScore + self.verificationFlowScore) / 2
            # verificationScore = (0 if self.verificationDepthScore < 0 else self.verificationDepthScore) + (
            #     0 if self.verificationFlowScore < 0 else self.verificationFlowScore) / 2
        else:
            verificationScore = -1

        if (self.verifyForFlow or self.verifyForDepth):
            if verificationScore < 0:
                col = [200, 200, 200]
            else:
                myCM = cm.get_cmap('RdYlGn')
                col = [int(i * 255) for i in list(myCM(verificationScore))]
        else:
            col = [255, 255, 255]

        return QColor(col[0], col[1], col[2], 128)

    def updateVerificationScore(self, typeIndex: int):

        if typeIndex == self.iObsDepth or typeIndex == self.iPredDepth:

            cumulativeDepthScore = 0
            totalPossibleDepthScore = 2

            if self.isCritical:

                if (0.5 > self.depthTp_Diff_Hrs > -0.5):
                    cumulativeDepthScore += 1

                if (0.1 > self.depthDp_Diff > -0.1):
                    cumulativeDepthScore += 1

            else:

                if (0.5 > self.depthTp_Diff_Hrs > -0.5):
                    cumulativeDepthScore += 1

                if self.isSurcharged:
                    if (0.5 > self.depthDp_Diff > -0.1):
                        cumulativeDepthScore += 1
                else:
                    if ((10 > self.depthDp_Diff_Pcnt > -10) and (0.1 > self.depthDp_Diff > -0.1)):
                        cumulativeDepthScore += 1

            self.verificationDepthScore = (
                cumulativeDepthScore / totalPossibleDepthScore)

        else:
            cumulativeFlowScore = 0
            totalPossibleFlowScore = 4

            if self.isCritical:

                if (self.flowNSE > 0.5):
                    cumulativeFlowScore += 1

                if (0.5 > self.flowTp_Diff_Hrs > -0.5):
                    cumulativeFlowScore += 1

                if (10 > self.flowQp_Diff_Pcnt > -10):
                    cumulativeFlowScore += 1

                if (10 > self.flowVol_Diff_Pcnt > -10):
                    cumulativeFlowScore += 1

            else:

                if (self.flowNSE > 0.5):
                    cumulativeFlowScore += 1

                if (0.5 > self.flowTp_Diff_Hrs > -0.5):
                    cumulativeFlowScore += 1

                if (25 > self.flowQp_Diff_Pcnt > -15):
                    cumulativeFlowScore += 1

                if (20 > self.flowVol_Diff_Pcnt > -10):
                    cumulativeFlowScore += 1

            self.verificationFlowScore = (
                cumulativeFlowScore / totalPossibleFlowScore)

    # def updateVerificationScore(self):

    #     cumulativeScore = 0
    #     totalPossibleScore = 0
    #     if self.isCritical:
    #         if self.verifyForDepth:
    #             totalPossibleScore = totalPossibleScore + 2

    #             if (0.5 > self.depthTp_Diff_Hrs > -0.5):
    #                 cumulativeScore += 1

    #             if (0.1 > self.depthDp_Diff > -0.1):
    #                 cumulativeScore += 1

    #         if self.verifyForFlow:
    #             totalPossibleScore = totalPossibleScore + 4

    #             if (self.flowNSE > 0.5):
    #                 cumulativeScore += 1

    #             if (0.5 > self.flowTp_Diff_Hrs > -0.5):
    #                 cumulativeScore += 1

    #             if (10 > self.flowQp_Diff_Pcnt > -10):
    #                 cumulativeScore += 1

    #             if (10 > self.flowVol_Diff_Pcnt > -10):
    #                 cumulativeScore += 1

    #     else:
    #         if self.verifyForDepth:
    #             totalPossibleScore = totalPossibleScore + 2

    #             if (0.5 > self.depthTp_Diff_Hrs > -0.5):
    #                 cumulativeScore += 1

    #             if self.isSurcharged:
    #                 if (0.5 > self.depthDp_Diff > -0.1):
    #                     cumulativeScore += 1
    #             else:
    #                 if ((10 > self.depthDp_Diff_Pcnt > -10) and (0.1 > self.depthDp_Diff > -0.1)):
    #                     cumulativeScore += 1

    #         if self.verifyForFlow:
    #             totalPossibleScore = totalPossibleScore + 4

    #             if (self.flowNSE > 0.5):
    #                 cumulativeScore += 1

    #             if (0.5 > self.flowTp_Diff_Hrs > -0.5):
    #                 cumulativeScore += 1

    #             if (25 > self.flowQp_Diff_Pcnt > -15):
    #                 cumulativeScore += 1

    #             if (20 > self.flowVol_Diff_Pcnt > -10):
    #                 cumulativeScore += 1

    #     self.verificationScore = (
    #         cumulativeScore / totalPossibleScore)  # * 100

    def updatePeaks(self, typeIndex: int = 0, noOfPeaksWanted: int = -1):

        self.smoothedData[typeIndex] = self.smooth_lowess(
            self.rawData[typeIndex], self.frac[typeIndex])

        if noOfPeaksWanted == -1:
            peaks, _ = find_peaks(np.asarray(self.smoothedData[typeIndex]), prominence=self.peaks_prominance[typeIndex],
                                  width=self.peaks_width[typeIndex], distance=self.peaks_distance[typeIndex], threshold=0)

            if not self.peaksInitialized[typeIndex]:
                peak_proms, _a, _b = peak_prominences(
                    np.asarray(self.smoothedData[typeIndex]), peaks)
                if len(peak_proms.tolist()) > 0:
                    self.peaks_prominance[typeIndex] = float(
                        '%.*g' % (4, max(peak_proms.tolist()))) - 0.0001
                    peaks, _ = find_peaks(np.asarray(self.smoothedData[typeIndex]), prominence=self.peaks_prominance[typeIndex],
                                          width=self.peaks_width[typeIndex], distance=self.peaks_distance[typeIndex], threshold=0)
        else:
            self.peaks_prominance[typeIndex] = self.getPeakPromFromNoOfPeaksWanted(
                typeIndex, noOfPeaksWanted)
            peaks, _ = find_peaks(np.asarray(self.smoothedData[typeIndex]), prominence=self.peaks_prominance[typeIndex],
                                  width=self.peaks_width[typeIndex], distance=self.peaks_distance[typeIndex], threshold=0)

        self.peaksData[typeIndex] = np.asarray(
            self.smoothedData[typeIndex])[peaks].tolist()
        self.peaksDates[typeIndex] = np.asarray(
            self.dates)[peaks].tolist()

        myDict = {'Obs': self.rawData[self.iObsFlow].copy(
        ), 'Pred': self.rawData[self.iPredFlow].copy()}
        df = pd.DataFrame(myDict)
        self.flowNSE = getNashSutcliffe(df, 'Obs', 'Pred')

        if typeIndex in (self.iObsFlow, self.iPredFlow):
            self.updateMaxTimeToPeakDifference(True)
            self.updateMaximumPeakPcntDifference(True)
            self.updateVolumePcntDifference()
        elif typeIndex in (self.iObsDepth, self.iPredDepth):
            self.updateMaxTimeToPeakDifference(False)
            self.updateMaximumPeakPcntDifference(False)

        self.updateVerificationScore(typeIndex)

        self.peaksInitialized[typeIndex] = True

    def getNoOfPeaks(self, typeIndex: int = 0):
        peaks, _ = find_peaks(np.asarray(self.smoothedData[typeIndex]), prominence=self.peaks_prominance[typeIndex],
                              width=self.peaks_width[typeIndex], distance=self.peaks_distance[typeIndex], threshold=0)
        return len(peaks)

    def getPeakPromFromNoOfPeaksWanted(self, typeIndex: int = 0, noOfPeaksWanted: int = -1):

        peaks, _ = find_peaks(np.asarray(self.smoothedData[typeIndex]), prominence=0,
                              width=self.peaks_width[typeIndex], distance=self.peaks_distance[typeIndex], threshold=0)
        peak_proms, _a, _b = peak_prominences(
            np.asarray(self.smoothedData[typeIndex]), peaks)
        if len(peak_proms.tolist()) >= noOfPeaksWanted:
            return float('%.*g' % (4, np.sort(peak_proms)[-noOfPeaksWanted])) - 0.0001

        return 0

    def updateAllPeaks(self):

        for i in range(4):
            self.updatePeaks(i)

    # def smooth_lowess(self, noisy_data: list[float], frac: float = 0.12):
    def smooth_lowess(self, noisy_data: list[float], frac: float = 0.0):
        npNoisyData = np.asarray(noisy_data)
        in_array = np.arange(len(noisy_data))
        lowess_tight = lowess(npNoisyData, in_array,
                              frac=frac, return_sorted=False)

        return lowess_tight.tolist()

    # def updateAverageTimeToPeakDifference(self, forFlow: bool = True):

    #     if forFlow:
    #         dateObs = self.peaksDates[self.iObsFlow].copy()
    #         datePred = self.peaksDates[self.iPredFlow].copy()
    #     else:
    #         dateObs = self.peaksDates[self.iObsDepth].copy()
    #         datePred = self.peaksDates[self.iPredDepth].copy()

    #     iCountDates = 0
    #     dateDiffTotal = 0

    #     for oDate in dateObs:
    #         iCountDates += 1
    #         pDate = self.getClosestDate(oDate, datePred)
    #         if not pDate is None:
    #             dateDiff = abs(((pDate - oDate).total_seconds())/(60*60))
    #         else:
    #             dateDiff = abs(((dateObs[0] - oDate).total_seconds())/(60*60))

    #         dateDiffTotal = dateDiffTotal + dateDiff

    #     if iCountDates == 0:
    #         dateDiffObsAvg = -99999
    #     else:
    #         dateDiffObsAvg = dateDiffTotal / iCountDates

    #     iCountDates = 0
    #     dateDiffTotal = 0

    #     for pDate in datePred:
    #         iCountDates += 1
    #         oDate = self.getClosestDate(pDate, dateObs)
    #         if not oDate is None:
    #             dateDiff = abs(((pDate - oDate).total_seconds())/(60*60))
    #         else:
    #             dateDiff = abs(((datePred[0] - pDate).total_seconds())/(60*60))

    #         dateDiffTotal = dateDiffTotal + dateDiff

    #     if iCountDates == 0:
    #         dateDiffPredAvg = -99999
    #     else:
    #         dateDiffPredAvg = dateDiffTotal / iCountDates

    #     if forFlow:
    #         if dateDiffObsAvg >= 0 and dateDiffPredAvg >= 0:
    #             dateDiffAvg = (dateDiffObsAvg + dateDiffPredAvg) / 2
    #         if dateDiffObsAvg >= 0 and dateDiffPredAvg >= 0:
    #             dateDiffAvg = (dateDiffObsAvg + dateDiffPredAvg) / 2
    #         self.flowTp_Diff_Hrs = dateDiffAvg
    #     else:
    #         self.depthTp_Diff_Hrs = dateDiffAvg

    #     # i = datePred.index(pDate)

    def updateMaxTimeToPeakDifference(self, forFlow: bool = True):

        if forFlow:
            dateObs = self.peaksDates[self.iObsFlow].copy()
            datePred = self.peaksDates[self.iPredFlow].copy()
        else:
            dateObs = self.peaksDates[self.iObsDepth].copy()
            datePred = self.peaksDates[self.iPredDepth].copy()

        absDiffRecord = 0
        diffRecord = 0

        for oDate in dateObs:
            pDate = self.getClosestDate(oDate, datePred)
            if pDate is not None:
                dateDiff = ((pDate - oDate).total_seconds())/(60*60)
            else:
                dateDiff = ((dateObs[0] - oDate).total_seconds())/(60*60)

            if abs(dateDiff) > absDiffRecord:
                absDiffRecord = abs(dateDiff)
                diffRecord = dateDiff

        for pDate in datePred:
            oDate = self.getClosestDate(pDate, dateObs)
            if oDate is not None:
                dateDiff = abs(((pDate - oDate).total_seconds())/(60*60))
            else:
                dateDiff = abs(((datePred[0] - pDate).total_seconds())/(60*60))

            if abs(dateDiff) > absDiffRecord:
                absDiffRecord = abs(dateDiff)
                diffRecord = dateDiff

        if forFlow:
            self.flowTp_Diff_Hrs = diffRecord
        else:
            self.depthTp_Diff_Hrs = diffRecord

        # i = datePred.index(pDate)

    def updateMaximumPeakPcntDifference(self, forFlow: bool = True):

        if forFlow:
            dateObs = self.peaksDates[self.iObsFlow].copy()
            obsData = self.peaksData[self.iObsFlow].copy()
            datePred = self.peaksDates[self.iPredFlow].copy()
            predData = self.peaksData[self.iPredFlow].copy()
        else:
            dateObs = self.peaksDates[self.iObsDepth].copy()
            obsData = self.peaksData[self.iObsDepth].copy()
            datePred = self.peaksDates[self.iPredDepth].copy()
            predData = self.peaksData[self.iPredDepth].copy()

        absDiffValRecord = 0
        diffValRecord = 0
        absDiffPcntRecord = 0
        diffPcntRecord = 0

        for i in range(len(datePred)):
            # iCountPeaks += 1
            pDate = datePred[i]
            oDate = self.getClosestDate(pDate, dateObs)
            if oDate is not None:
                j = dateObs.index(oDate)
                diffVal = predData[i] - obsData[j]
                if obsData[j] != 0:
                    diffPcnt = (diffVal / obsData[j]) * 100
                else:
                    diffPcnt = 99999
            else:
                diffVal = predData[i]
                diffPcnt = 99999

            if abs(diffVal) > absDiffValRecord:
                absDiffValRecord = abs(diffVal)
                diffValRecord = diffVal

            if abs(diffPcnt) > absDiffPcntRecord:
                absDiffPcntRecord = abs(diffPcnt)
                diffPcntRecord = diffPcnt

        for i in range(len(dateObs)):
            # iCountPeaks += 1
            oDate = dateObs[i]
            pDate = self.getClosestDate(oDate, datePred)
            if pDate is not None:
                j = datePred.index(pDate)
                diffVal = predData[j] - obsData[i]
                if obsData[i] != 0:
                    diffPcnt = (diffVal / obsData[i]) * 100
                else:
                    diffPcnt = 99999
            else:
                diffVal = obsData[i]
                diffPcnt = 99999

            if abs(diffVal) > absDiffValRecord:
                absDiffValRecord = abs(diffVal)
                diffValRecord = diffVal

            if abs(diffPcnt) > absDiffPcntRecord:
                absDiffPcntRecord = abs(diffPcnt)
                diffPcntRecord = diffPcnt

        if forFlow:
            self.flowQp_Diff_Pcnt = diffPcntRecord
        else:
            self.depthDp_Diff_Pcnt = diffPcntRecord
            self.depthDp_Diff = diffValRecord

    # def updateMaximumPeakPcntDifference(self, forFlow: bool = True):

    #     if forFlow:
    #         dateObs = self.peaksDates[self.iObsFlow].copy()
    #         obsData = self.peaksData[self.iObsFlow].copy()
    #         datePred = self.peaksDates[self.iPredFlow].copy()
    #         predData = self.peaksData[self.iPredFlow].copy()
    #     else:
    #         dateObs = self.peaksDates[self.iObsDepth].copy()
    #         obsData = self.peaksData[self.iObsDepth].copy()
    #         datePred = self.peaksDates[self.iPredDepth].copy()
    #         predData = self.peaksData[self.iPredDepth].copy()

    #     iCountPeaks = 0
    #     # peakPcntDiffTotal = 0
    #     # peakDiffTotal = 0

    #     for i in range(len(datePred)):
    #         iCountPeaks += 1
    #         pDate = datePred[i]
    #         oDate = self.getClosestDate(pDate, dateObs)
    #         if not oDate is None:
    #             j = dateObs.index(oDate)
    #             diffVal = predData[i] - obsData[j]
    #             if obsData[j] != 0:
    #                 diffPcnt = (diffVal / obsData[j]) * 100
    #             else:
    #                 diffPcnt = 99999
    #         else:
    #             diffVal = predData[i]
    #             diffPcnt = 99999

    #         peakPcntDiffTotal = peakPcntDiffTotal + diffPcnt
    #         peakDiffTotal = peakDiffTotal + diffVal

    #     if iCountPeaks == 0:
    #         peakPcntDiffAvg = -99999
    #         peakDiffAvg = -99999
    #     else:
    #         peakPcntDiffAvg = peakPcntDiffTotal / iCountPeaks
    #         peakDiffAvg = peakDiffTotal / iCountPeaks

    #     if forFlow:
    #         self.flowQp_Diff_Pcnt = peakPcntDiffAvg
    #     else:
    #         self.depthDp_Diff_Pcnt = peakPcntDiffAvg
    #         self.depthDp_Diff = peakDiffAvg

    # def updateAveragePeakPcntDifference(self, forFlow: bool = True):

    #     if forFlow:
    #         dateObs = self.peaksDates[self.iObsFlow].copy()
    #         obsData = self.peaksData[self.iObsFlow].copy()
    #         datePred = self.peaksDates[self.iPredFlow].copy()
    #         predData = self.peaksData[self.iPredFlow].copy()
    #     else:
    #         dateObs = self.peaksDates[self.iObsDepth].copy()
    #         obsData = self.peaksData[self.iObsDepth].copy()
    #         datePred = self.peaksDates[self.iPredDepth].copy()
    #         predData = self.peaksData[self.iPredDepth].copy()

    #     iCountPeaks = 0
    #     peakPcntDiffTotal = 0
    #     peakDiffTotal = 0

    #     for i in range(len(datePred)):
    #         iCountPeaks += 1
    #         pDate = datePred[i]
    #         oDate = self.getClosestDate(pDate, dateObs)
    #         if not oDate is None:
    #             j = dateObs.index(oDate)
    #             diffVal = predData[i] - obsData[j]
    #             if obsData[j] != 0:
    #                 diffPcnt = (diffVal / obsData[j]) * 100
    #             else:
    #                 diffPcnt = 99999
    #         else:
    #             diffVal = predData[i]
    #             diffPcnt = 99999

    #         peakPcntDiffTotal = peakPcntDiffTotal + diffPcnt
    #         peakDiffTotal = peakDiffTotal + diffVal

    #     if iCountPeaks == 0:
    #         peakPcntDiffAvg = -99999
    #         peakDiffAvg = -99999
    #     else:
    #         peakPcntDiffAvg = peakPcntDiffTotal / iCountPeaks
    #         peakDiffAvg = peakDiffTotal / iCountPeaks

    #     if forFlow:
    #         self.flowQp_Diff_Pcnt = peakPcntDiffAvg
    #     else:
    #         self.depthDp_Diff_Pcnt = peakPcntDiffAvg
    #         self.depthDp_Diff = peakDiffAvg

    def getClosestDate(self, test_date, test_date_list):

        if len(test_date_list) == 0:
            return None
        else:
            cloz_dict = {abs(test_date.timestamp() - date.timestamp()): date for date in test_date_list}

            return cloz_dict[min(cloz_dict.keys())]

    def updateVolumePcntDifference(self):

        totalPredVolume = sum(
            self.rawData[self.iPredFlow][0:-1]) * int(self.trTimestep) * 60
        totalObsVolume = sum(
            self.rawData[self.iObsFlow][0:-1]) * int(self.trTimestep) * 60

        volDiffVal = totalPredVolume - totalObsVolume
        if totalObsVolume != 0:
            volDiffPcnt = (volDiffVal / totalObsVolume) * 100
        else:
            volDiffPcnt = 0

        self.flowVol_Diff_Pcnt = volDiffPcnt


class icmTrace(object):

    def __init__(self):

        self.traceID: str = ''
        self.csvFileSpec: str = ''
        self.dictLocations: Dict[int, icmTraceLocation] = {}
        self.currentLocation: int = 0
        # self.showAllFlowPeaks = False
        # self.showAllDepthPeaks = False

    def from_database_row(self, row, conn: sqlite3.Connection):

        self.traceID = row[0]
        self.csvFileSpec = row[1]
        self.currentLocation = row[2]

        c = conn.cursor()
        try:
            c.execute(f"SELECT * FROM {Tables.ICM_TRACE_LOCATION} WHERE it_traceID = '{row[0]}'")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.ICM_TRACE_LOCATION}' does not exist.")
            return  # Return without attempting to fetch rows
        
        tl_rows = c.fetchall()
        for tl_row in tl_rows:
            tl = icmTraceLocation()
            tl.from_database_row(tl_row)
            self.dictLocations[tl.index] = tl

    def write_to_database(self, conn: sqlite3.Connection):

        try:
            # with closing(conn.cursor()) as c:

            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.ICM_TRACE_LOCATION} (
                            itl_index INTEGER,
                            it_traceID TEXT,
                            pageTitle TEXT,
                            shortTitle TEXT,
                            obsLocation TEXT,
                            predLocation TEXT,
                            upstreamEnd INTEGER,
                            trTimestep INTEGER,
                            isCritical INTEGER,
                            isSurcharged INTEGER,
                            dates TEXT,
                            rawData TEXT,
                            smoothedData TEXT,
                            peaksDates TEXT,
                            peaksData TEXT,
                            peaksInitialized TEXT,
                            verifyForFlow INTEGER,
                            verifyForDepth INTEGER,
                            frac TEXT,
                            peaks_prominance TEXT,
                            peaks_width TEXT,
                            peaks_distance TEXT,
                            flowNSE REAL,
                            flowTp_Diff_Hrs REAL,
                            flowQp_Diff_Pcnt REAL,
                            flowVol_Diff_Pcnt REAL,
                            depthTp_Diff_Hrs REAL,
                            depthDp_Diff_Pcnt REAL,
                            depthDp_Diff REAL,
                            verificationDepthScore REAL,
                            verificationFlowScore REAL,
                            verificationDepthComment TEXT,
                            verificationFlowComment TEXT,
                            verificationOverallComment TEXT,
                            CONSTRAINT pk_{Tables.ICM_TRACE_LOCATION} PRIMARY KEY (itl_index, it_traceID),
                            FOREIGN KEY (it_traceID) REFERENCES {Tables.ICM_TRACE}(traceID)                  
                        )''')
            for loc in self.dictLocations.values():
                conn.execute(f'''INSERT OR REPLACE INTO {Tables.ICM_TRACE_LOCATION} VALUES (
                        ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                        (loc.index, self.traceID, loc.pageTitle, loc.shortTitle, loc.obsLocation, loc.predLocation,
                        int(loc.upstreamEnd), loc.trTimestep, int(loc.isCritical), int(loc.isSurcharged),
                        serialize_list(loc.dates), serialize_list(loc.rawData), serialize_list(loc.smoothedData),
                        serialize_timestamp_list(loc.peaksDates), serialize_list(loc.peaksData), 
                        serialize_list(loc.peaksInitialized), int(loc.verifyForFlow), int(loc.verifyForDepth), 
                        serialize_list(loc.frac), serialize_list(loc.peaks_prominance), serialize_list(loc.peaks_width),
                        serialize_list(loc.peaks_distance), loc.flowNSE, loc.flowTp_Diff_Hrs, loc.flowQp_Diff_Pcnt,
                        loc.flowVol_Diff_Pcnt, loc.depthTp_Diff_Hrs, loc.depthDp_Diff_Pcnt, loc.depthDp_Diff,
                        loc.verificationDepthScore, loc.verificationFlowScore, loc.verificationDepthComment,
                        loc.verificationFlowComment, loc.verificationOverallComment))
            conn.commit()

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            conn.rollback()
        except Exception as e:
            print(f"Exception in _query: {e}")
            conn.rollback()
        # finally:
        #     conn.close()

    def allVerifiedForDepth(self) -> bool:
        iCount = 0
        for aLoc in self.dictLocations.values():
            if aLoc.verifyForDepth:
                iCount += 1
        if iCount == len(self.dictLocations):
            return True
        else:
            return False

    def allVerifiedForFlow(self) -> bool:
        iCount = 0
        for aLoc in self.dictLocations.values():
            if aLoc.verifyForFlow:
                iCount += 1
        if iCount == len(self.dictLocations):
            return True
        else:
            return False
    # def getTraceLocationByIndex(self, index: int) -> icmTraceLocation:


class icmTraces():

    dictIcmTraces: Dict[str, icmTrace]

    def __init__(self):
        self.dictIcmTraces = {}

    def read_from_database(self, conn: sqlite3.Connection):
        c = conn.cursor()
        try:
            c.execute(f"SELECT * FROM {Tables.ICM_TRACE}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.ICM_TRACE}' does not exist.")
            return  # Return without attempting to fetch rows

        rows = c.fetchall()
        for row in rows:
            tr = icmTrace()
            tr.from_database_row(row, conn)
            self.dictIcmTraces[tr.traceID] = tr

    def write_to_database(self, conn: sqlite3.Connection) -> bool:
        result = False

        try:
            conn.execute(f'''DROP TABLE IF EXISTS {Tables.ICM_TRACE}''')
            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.ICM_TRACE} (
                         traceID TEXT PRIMARY KEY,
                         csvFileSpec TEXT,
                         currentLocation INTEGER
                         )''')
            for tr in self.dictIcmTraces.values():
                conn.execute(f'''INSERT OR REPLACE INTO {Tables.ICM_TRACE} VALUES (?, ?, ?)''',
                             (tr.traceID, tr.csvFileSpec, tr.currentLocation))
                tr.write_to_database(conn)
                # for tl in tr.dictLocations.values():
                #     tl.write_to_database(conn)
            conn.commit()
            result = True
            logger.debug("icmTraces.write_to_database Completed")

        except sqlite3.Error as e:
            logger.error(f"icmTraces.write_to_database: Database error: {e}")
            # print(f"Database error: {e}")
            conn.rollback()
        except Exception as e:
            logger.error(f"icmTraces.write_to_database: Exception in _query: {e}")
            # print(f"Exception in _query: {e}")
            conn.rollback()
        finally:
            return result
        #     conn.close()

    def addTrace(self, objTrace: icmTrace):
        if not self.alreadyOpen(objTrace):
            self.dictIcmTraces[objTrace.traceID] = objTrace

    def traceCount(self) -> int:

        return len(self.dictIcmTraces)

    def getTrace(self, traceID: str) -> Optional[icmTrace]:

        if traceID in self.dictIcmTraces:
            return self.dictIcmTraces[traceID]

    def removeTrace(self, traceID: str):

        if traceID in self.dictIcmTraces:
            self.dictIcmTraces.pop(traceID)

    def alreadyOpen(self, objTrace: Union[icmTrace, str]) -> bool:
        if isinstance(objTrace, icmTrace):
            for trace in self.dictIcmTraces.items():
                if trace[1].traceID == objTrace.traceID:
                    reply = QMessageBox.question(None, 'Opened already!',
                                                 'An ICM Trace from file: ' + trace[1].traceID +
                                                 ' was already added.\n\nDo you want to replace it?',
                                                 QMessageBox.Yes | QMessageBox.No,
                                                 QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        self.dictIcmTraces.pop(trace[1].traceID)
                        return False
                    else:
                        return True

            return False
        elif isinstance(objTrace, str):
            for trace in self.dictIcmTraces.items():
                if trace[1].traceID == objTrace:
                    return True

            return False
        else:
            return False

    def getTracesFromCSVFile(self, fileSpec: str, defaultSmoothing: Dict[str, float]) -> Optional[icmTrace]:

        dfTrace = pd.read_csv(fileSpec, skiprows=1, nrows=10)

        i = 0
        # idxObsRainfall = -1
        idxObsVel = -1
        idxPredVelBase = -1
        iPredColCount = 0
        for col in dfTrace.columns:
            if col == "Observed Rainfall (Rainfall intensity (mm/hr))":
                pass
                # idxObsRainfall = i
            if col == "Observed Velocity (Velocity (m/s))":
                idxObsVel = i
            if col[0:9] == "Predicted":
                if idxPredVelBase == -1:
                    idxPredVelBase = i
                iPredColCount += 1
            i += 1

        if dfTrace.columns[idxObsVel - 2][0:4] == "Date":
            idxObsDate = idxObsVel - 2
        else:
            idxObsDate = 0

        strObsDate = dfTrace.columns[idxObsDate]
        strObsTime = dfTrace.columns[idxObsDate + 1]
        obsColsToUse = [idxObsDate, idxObsDate + 1,
                        idxObsVel, idxObsVel + 1, idxObsVel + 2]

        NoOfPred = int(iPredColCount / 3)

        iPredToUse = 1

        if NoOfPred > 1:
            itemList = []

            for i in range(NoOfPred):
                idx = idxPredVelBase + (1 * ((i+1) - 1))
                itemString = str(dfTrace.columns[idx]).split(
                    "Predicted Velocity, ")[1].split(" (Velocity (m/s))")[0]
                itemList.append(itemString)

            items = tuple(itemList)

            item, ok = QInputDialog.getItem(None,
                                            "Select Predicted Profile",
                                            f"{NoOfPred} Predicted Profiles Found\n\n"
                                            "FlowBot currently only supports analysis\n"
                                            "of one predicted profile at a time.\n\n"
                                            "Select which profile number to import:",
                                            items,
                                            0,
                                            False)
            if ok and item:
                iPredToUse = itemList.index(item)+1
            else:
                return

        idxPredDate = idxPredVelBase - 2

        strPredDate = dfTrace.columns[idxPredDate]
        strPredTime = dfTrace.columns[idxPredDate + 1]

        idxPredVelBase = idxPredVelBase + (0 * NoOfPred)
        idxPredVel = idxPredVelBase + (1 * (iPredToUse - 1))
        idxPredFlowBase = idxPredVelBase + (1 * NoOfPred)
        idxPredFlow = idxPredFlowBase + (1 * (iPredToUse - 1))
        idxPredDepthBase = idxPredVelBase + (2 * NoOfPred)
        idxPredDepth = idxPredDepthBase + (1 * (iPredToUse - 1))

        predColsToUse = [idxPredDate, idxPredDate +
                         1, idxPredVel, idxPredFlow, idxPredDepth]

        dfObsTrace = pd.read_csv(fileSpec, skiprows=1, usecols=obsColsToUse,
                                 parse_dates=[[strObsDate, strObsTime]], low_memory=False, dayfirst=True)

        dfObsTrace = dfObsTrace.set_axis(['DateTime', 'ObsVel', 'ObsFlow', 'ObsDep'], axis=1)
        dfObsTrace['DateTime'] = pd.to_datetime(dfObsTrace['DateTime'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        dfObsTrace['ObsVel'] = pd.to_numeric(
            dfObsTrace['ObsVel'], downcast='float', errors='coerce')
        dfObsTrace['ObsFlow'] = pd.to_numeric(
            dfObsTrace['ObsFlow'], downcast='float', errors='coerce')
        dfObsTrace['ObsDep'] = pd.to_numeric(
            dfObsTrace['ObsDep'], downcast='float', errors='coerce')
        dfObsTrace.dropna(subset=['DateTime'], inplace=True)

        dfPredTrace = pd.read_csv(
            fileSpec, skiprows=1, usecols=predColsToUse, parse_dates=[[strPredDate, strPredTime]], low_memory=False)
        dfPredTrace = dfPredTrace.set_axis(['DateTime', 'PredVel', 'PredFlow', 'PredDep'], axis=1)
        dfPredTrace['DateTime'] = pd.to_datetime(
            dfPredTrace['DateTime'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        dfPredTrace['PredVel'] = pd.to_numeric(
            dfPredTrace['PredVel'], downcast='float', errors='coerce')
        dfPredTrace['PredFlow'] = pd.to_numeric(
            dfPredTrace['PredFlow'], downcast='float', errors='coerce')
        dfPredTrace['PredDep'] = pd.to_numeric(
            dfPredTrace['PredDep'], downcast='float', errors='coerce')
        dfPredTrace.dropna(subset=['DateTime'], inplace=True)

        start_date = min(dfPredTrace["DateTime"])
        end_date = max(dfPredTrace["DateTime"])

        dfSplits = dfObsTrace[dfObsTrace.DateTime ==
                              dfObsTrace['DateTime'][0]].copy()
        dfSplits.reset_index(inplace=True)
        # myObsDFs = []

        dfPageTitles = pd.read_fwf(fileSpec, header=None, usecols=[0])
        dfPageTitles = dfPageTitles.set_axis(['PageTitle'], axis=1)
        dfPageTitles = dfPageTitles[dfPageTitles['PageTitle'].str[:10] == 'Page title'].copy(
        )
        dfPageTitles.reset_index(inplace=True, drop=True)

        newTrace = icmTrace()
        newTrace.traceID = os.path.splitext(os.path.basename(fileSpec))[0]
        newTrace.csvFileSpec = fileSpec

        for i in range(len(dfSplits.index)):
            if i < len(dfSplits.index)-1:
                aDF = dfObsTrace[np.logical_and(
                    dfObsTrace.index >= dfSplits['index'][i], dfObsTrace.index < dfSplits['index'][i+1])].copy()
            else:
                aDF = dfObsTrace[dfObsTrace.index >=
                                 dfSplits['index'][i]].copy()

            mask = (aDF["DateTime"] > start_date) & (
                aDF["DateTime"] <= end_date)
            aDF = aDF.loc[mask]

            dfObsTimeResampled = aDF.set_index("DateTime")
            dfObsTimeResampled = dfObsTimeResampled.resample(rule="1min").fillna("pad")
            dfObsTimeResampled = dfObsTimeResampled.reset_index()

            dfObsPrefixed = aDF.add_prefix("Orig_")
            dfObsResampled = pd.merge_asof(dfObsTimeResampled, dfObsPrefixed, left_on="DateTime",
                                           right_on="Orig_DateTime", tolerance=pd.Timedelta("0.5min"))
            dfObsResampled["Orig_ObsVel"] = dfObsResampled["Orig_ObsVel"].interpolate(
                method='linear')
            dfObsResampled["Orig_ObsFlow"] = dfObsResampled["Orig_ObsFlow"].interpolate(
                method='linear')
            dfObsResampled["Orig_ObsDep"] = dfObsResampled["Orig_ObsDep"].interpolate(
                method='linear')

            dfObsResampled = dfObsResampled.drop(
                columns=["Orig_DateTime", "ObsVel", "ObsFlow", "ObsDep"])
            dfObsResampled = dfObsResampled.set_axis(['DateTime', 'ObsVel', 'ObsFlow', 'ObsDep'], axis=1)

            if i < len(dfSplits.index)-1:
                aDF = dfPredTrace[np.logical_and(
                    dfPredTrace.index >= dfSplits['index'][i], dfPredTrace.index < dfSplits['index'][i+1])].copy()
            else:
                aDF = dfPredTrace[dfPredTrace.index >=
                                  dfSplits['index'][i]].copy()
            dfPredTimeResampled = aDF.set_index("DateTime")
            dfPredTimeResampled = dfPredTimeResampled.resample(rule="1min").fillna("pad")
            dfPredTimeResampled = dfPredTimeResampled.reset_index()

            dfPredPrefixed = aDF.add_prefix("Orig_")
            dfPredResampled = pd.merge_asof(dfPredTimeResampled, dfPredPrefixed, left_on="DateTime",
                                            right_on="Orig_DateTime", tolerance=pd.Timedelta("0.5min"))
            dfPredResampled["Orig_PredVel"] = dfPredResampled["Orig_PredVel"].interpolate(
                method='linear')
            dfPredResampled["Orig_PredFlow"] = dfPredResampled["Orig_PredFlow"].interpolate(
                method='linear')
            dfPredResampled["Orig_PredDep"] = dfPredResampled["Orig_PredDep"].interpolate(
                method='linear')

            dfPredResampled = dfPredResampled.drop(
                columns=["Orig_DateTime", "PredVel", "PredFlow", "PredDep"])
            dfPredResampled = dfPredResampled.set_axis(['DateTime', 'PredVel', 'PredFlow', 'PredDep'], axis=1)

            dfCompPrefixed = dfPredResampled.add_prefix("Orig_")
            dfCompare = pd.merge_asof(dfObsResampled, dfCompPrefixed, left_on="DateTime",
                                      right_on="Orig_DateTime", tolerance=pd.Timedelta("0.5min"))
            dfCompare = dfCompare.drop(columns=["Orig_DateTime"])
            dfCompare = dfCompare.set_axis(['DateTime', 'ObsVel', 'ObsFlow', 'ObsDep', 'PredVel', 'PredFlow', 'PredDep'], axis=1)

            newTraceLoc = icmTraceLocation()
            newTraceLoc.index = i
            newTraceLoc.pageTitle = dfPageTitles['PageTitle'][i]
            newTraceLoc.obsLocation = str(dfPageTitles['PageTitle'][i])[len('Page title is, "Flow Survey Location (Obs.) '):str(
                dfPageTitles['PageTitle'][i]).find(', Model Location (Pred.) ')]
            newTraceLoc.upstreamEnd = str(dfPageTitles['PageTitle'][i])[str(dfPageTitles['PageTitle'][i]).find(
                ', Model Location (Pred.) ') + len(', Model Location (Pred.) '):
                (str(dfPageTitles['PageTitle'][i]).find(', Model Location (Pred.) ') +
                 len(', Model Location (Pred.) ')+3)] == "U/S"
            if newTraceLoc.upstreamEnd:
                title = str(dfPageTitles['PageTitle'][i])
                us_index = title.find("U/S") + 4
                comma_index = title.find(",")
                if comma_index >= 0:
                    newTraceLoc.predLocation = title[us_index:len(title)-1][:comma_index]
                else:
                    newTraceLoc.predLocation = title[us_index:len(title)-1]
                # newTraceLoc.predLocation = str(dfPageTitles['PageTitle'][i])[(str(dfPageTitles['PageTitle'][i]).find("U/S") + 4):len(str(dfPageTitles['PageTitle'][i]))-1][0:(str(dfPageTitles['PageTitle'][i])[(str(dfPageTitles['PageTitle'][i]).find("U/S") + 4):len(str(dfPageTitles['PageTitle'][i]))-1].find(","))] if str(dfPageTitles['PageTitle'][i])[(str(dfPageTitles['PageTitle'][i]).find("U/S") + 4):len(str(dfPageTitles['PageTitle'][i]))-1].find(",") >= 0 else str(dfPageTitles['PageTitle'][i])[(str(dfPageTitles['PageTitle'][i]).find("U/S") + 4):len(str(dfPageTitles['PageTitle'][i]))-1]
            else:
                title = str(dfPageTitles['PageTitle'][i])
                ds_index = title.find("D/S") + 4
                substring = title[ds_index:len(title)-1]
                comma_index = substring.find(",")

                newTraceLoc.predLocation = substring[:comma_index] if comma_index >= 0 else substring
                # newTraceLoc.predLocation = str(dfPageTitles['PageTitle'][i])[(str(dfPageTitles['PageTitle'][i]).find("D/S") + 4):len(str(dfPageTitles['PageTitle'][i]))-1][0:(str(dfPageTitles['PageTitle'][i])[(str(dfPageTitles['PageTitle'][i]).find("D/S") + 4):len(str(dfPageTitles['PageTitle'][i]))-1].find(","))] if str(dfPageTitles['PageTitle'][i])[(str(dfPageTitles['PageTitle'][i]).find("D/S") + 4):len(str(dfPageTitles['PageTitle'][i]))-1].find(",") >= 0 else str(dfPageTitles['PageTitle'][i])[(str(dfPageTitles['PageTitle'][i]).find("D/S") + 4):len(str(dfPageTitles['PageTitle'][i]))-1]

            newTraceLoc.shortTitle = newTraceLoc.obsLocation + \
                ' (' + newTraceLoc.predLocation + ' - U/S)' if newTraceLoc.upstreamEnd else newTraceLoc.obsLocation + \
                ' (' + newTraceLoc.predLocation + ' - D/S)'

            newTraceLoc.trTimestep = int(
                (dfCompare['DateTime'][1] - dfCompare['DateTime'][0]).seconds/60)

            newTraceLoc.dates = dfCompare['DateTime'].tolist()
            newTraceLoc.rawData = [dfCompare['ObsFlow'].tolist(), dfCompare['PredFlow'].tolist(), dfCompare['ObsDep'].tolist(
            ), dfCompare['PredDep'].tolist(), dfCompare['ObsVel'].tolist(), dfCompare['PredVel'].tolist()]

            newTraceLoc.frac = [defaultSmoothing['Observed'], defaultSmoothing['Predicted'],
                                defaultSmoothing['Observed'], defaultSmoothing['Predicted']]

            newTrace.dictLocations[newTraceLoc.index] = newTraceLoc

        self.addTrace(newTrace)
        return newTrace


class plottedICMTrace():

    plotTrace: Optional[icmTrace]
    plotEarliestStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
    plotLatestEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')
    __plotCurrentStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
    __plotCurrentEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')
    plotMinObsFlow = 9999
    plotMaxObsFlow = 0
    plotMinObsDepth = 9999
    plotMaxObsDepth = 0
    plotMinObsVelocity = 9999
    plotMaxObsVelocity = 0
    plotTotalObsVolume = 0
    plotMinPredFlow = 9999
    plotMaxPredFlow = 0
    plotMinPredDepth = 9999
    plotMaxPredDepth = 0
    plotMinPredVelocity = 9999
    plotMaxPredVelocity = 0
    plotTotalPredVolume = 0

    def __init__(self):
        self.plotTrace = None
        self.plotEarliestStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
        self.plotLatestEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')
        self.__plotCurrentStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
        self.__plotCurrentEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')
        self.plotMinObsFlow = 9999
        self.plotMaxObsFlow = 0
        self.plotMinObsDepth = 9999
        self.plotMaxObsDepth = 0
        self.plotMinObsVelocity = 9999
        self.plotMaxObsVelocity = 0
        self.plotTotalObsVolume = 0
        self.plotMinPredFlow = 9999
        self.plotMaxPredFlow = 0
        self.plotMinPredDepth = 9999
        self.plotMinPredVelocity = 9999
        self.plotMaxPredDepth = 0
        self.plotMaxPredVelocity = 0
        self.plotTotalPredVolume = 0

    def setPlotDateLimits(self, startDate, endDate):
        if startDate is None:
            self.__plotCurrentStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
        else:
            self.__plotCurrentStart = startDate
        if startDate is None:
            self.__plotCurrentEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')
        else:
            self.__plotCurrentEnd = endDate
        self.updatePlottedICMTracesMinMaxValues()

    def getPlotCurrentStart(self):
        return self.__plotCurrentStart

    def getPlotCurrentEnd(self):
        return self.__plotCurrentEnd

    def addICMTrace(self, objTrace: icmTrace):

        self.plotTrace = objTrace
        self.updatePlottedICMTracesMinMaxValues()
        return True

    def removeICMTrace(self, traceID):

        if traceID == self.plotTrace.traceID:
            self.plotTrace = None
            self.updatePlottedICMTracesMinMaxValues()
            return True
        return False

    def updatePlottedICMTracesMinMaxValues(self):

        self.plotEarliestStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
        self.plotLatestEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')
        self.plotMinObsFlow = 9999
        self.plotMaxObsFlow = 0
        self.plotMinObsDepth = 9999
        self.plotMaxObsDepth = 0
        self.plotMinObsVelocity = 9999
        self.plotMaxObsVelocity = 0
        self.plotTotalObsVolume = 0
        self.plotMinPredFlow = 9999
        self.plotMaxPredFlow = 0
        self.plotMinPredDepth = 9999
        self.plotMaxPredDepth = 0
        self.plotMinPredVelocity = 9999
        self.plotMaxPredVelocity = 0
        self.plotTotalPredVolume = 0

        if self.plotTrace is not None:
            aLoc = list(self.plotTrace.dictLocations.values())[
                self.plotTrace.currentLocation]

            if self.plotEarliestStart > aLoc.dates[0]:
                self.plotEarliestStart = aLoc.dates[0]
            if self.plotLatestEnd < aLoc.dates[len(aLoc.dates)-1]:
                self.plotLatestEnd = aLoc.dates[len(aLoc.dates)-1]

            start_time = time.mktime(self.getPlotCurrentStart().timetuple())
            end_time = time.mktime(self.getPlotCurrentEnd().timetuple())
            first_date_time = time.mktime(aLoc.dates[0].timetuple())
            last_date_time = time.mktime(aLoc.dates[len(aLoc.dates)-1].timetuple())

            if (first_date_time < start_time) and (start_time < last_date_time):
                unix_rounded_xmin_python_datetime = time.mktime(
                    aLoc.dates[0].timetuple())
                unix_rounded_xmax_python_datetime = time.mktime(
                    self.getPlotCurrentStart().timetuple())
                unix_diff_mins = (
                    (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)
                min_row = int(unix_diff_mins / aLoc.trTimestep)
            else:
                min_row = 0

            if (first_date_time < end_time) and (end_time < last_date_time):
                unix_rounded_xmin_python_datetime = time.mktime(
                    aLoc.dates[0].timetuple())
                unix_rounded_xmax_python_datetime = time.mktime(
                    self.getPlotCurrentEnd().timetuple())
                unix_diff_mins = (
                    (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)
                max_row = int(unix_diff_mins / aLoc.trTimestep)
            else:
                max_row = len(aLoc.rawData[aLoc.iObsFlow])

            self.plotMaxObsFlow = max(self.plotMaxObsFlow, max(
                aLoc.rawData[aLoc.iObsFlow][min_row:max_row]))
            self.plotMinObsFlow = min(self.plotMinObsFlow, min(
                aLoc.rawData[aLoc.iObsFlow][min_row:max_row]))
            self.plotTotalObsVolume = (
                sum(aLoc.rawData[aLoc.iObsFlow][min_row:max_row])) * int(aLoc.trTimestep) * 60
            # self.plotTotalObsVolume = self.plotTotalObsVolume + volume

            self.plotMaxObsDepth = max(self.plotMaxObsDepth, max(
                aLoc.rawData[aLoc.iObsDepth][min_row:max_row]))
            self.plotMinObsDepth = min(self.plotMinObsDepth, min(
                aLoc.rawData[aLoc.iObsDepth][min_row:max_row]))

            self.plotMaxObsVelocity = max(self.plotMaxObsVelocity, max(
                aLoc.rawData[aLoc.iObsVelocity][min_row:max_row]))
            self.plotMinObsVelocity = min(self.plotMinObsVelocity, min(
                aLoc.rawData[aLoc.iObsVelocity][min_row:max_row]))

            self.plotMaxPredFlow = max(self.plotMaxPredFlow, max(
                aLoc.rawData[aLoc.iPredFlow][min_row:max_row]))
            self.plotMinPredFlow = min(self.plotMinPredFlow, min(
                aLoc.rawData[aLoc.iPredFlow][min_row:max_row]))
            self.plotTotalPredVolume = (
                sum(aLoc.rawData[aLoc.iPredFlow][min_row:max_row])) * int(aLoc.trTimestep) * 60
            # self.plotTotalPredVolume = self.plotTotalPredVolume + volume

            self.plotMaxPredDepth = max(self.plotMaxPredDepth, max(
                aLoc.rawData[aLoc.iPredDepth][min_row:max_row]))
            self.plotMinPredDepth = min(self.plotMinPredDepth, min(
                aLoc.rawData[aLoc.iPredDepth][min_row:max_row]))

            self.plotMaxPredVelocity = max(self.plotMaxPredVelocity, max(
                aLoc.rawData[aLoc.iPredVelocity][min_row:max_row]))
            self.plotMinPredVelocity = min(self.plotMinPredVelocity, min(
                aLoc.rawData[aLoc.iPredVelocity][min_row:max_row]))
