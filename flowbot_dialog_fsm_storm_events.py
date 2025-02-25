from hmac import new
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QDialog, QMessageBox
from flowbot_graphing import graphRainfallAnalysis
from typing import Optional

from flowbot_management import fsmInterimReview, fsmProject, fsmStormEvent
from flowbot_monitors import plottedRainGauges, rainGauge
from flowbot_survey_events import surveyEvents, surveyEvent
from ui_elements.ui_flowbot_dialog_fsm_storm_events_base import Ui_Dialog
from flowbot_dialog_event import flowbot_dialog_event
import matplotlib.dates as mpl_dates


class flowbot_dialog_fsm_storm_events(QtWidgets.QDialog, Ui_Dialog):
    # def __init__(self, aPRGs: plottedRainGauges, a_project: fsmProject, interim_id: int, parent=None):
    def __init__(self, a_project: fsmProject, interim_id: int, parent=None):
        """Constructor."""
        super(flowbot_dialog_fsm_storm_events, self).__init__(parent)
        self.setupUi(self)

        self.a_project: fsmProject = a_project
        self.interim_id = interim_id
        self.eventsModel = QtGui.QStandardItemModel()
        # self.surveyEvents: Optional[surveyEvents] = surveyEvents()
        # for se in a_project.dict_fsm_stormevents.values():
        #     new_se = surveyEvent()
        #     new_se.eventName = se.storm_event_id
        #     new_se.eventType = 'Storm'
        #     new_se.eventStart = se.se_start
        #     new_se.eventEnd = se.se_end
        #     self.surveyEvents.addSurvEvent(new_se)

        self.spinConsecZeros.setToolTip(
            "<p>Specifies the number of consecutive zero rainfall readings required to mark the end of an event. Increasing this value allows the algorithm to group multiple short bursts of rainfall into a single event.</p>")
        self.spinReqDepth.setToolTip(
            "<p>The minimum total rainfall depth (in millimeters) required for a period to qualify as an event. This ensures only significant rainfall periods are considered.</p>")
        self.spinReqIntensity.setToolTip(
            "<p>The minimum rainfall intensity (in millimeters per hour) that must be exceeded for a period to qualify as an event.</p>")
        self.spinReqIntensityDuration.setToolTip(
            "<p>The minimum duration for which rainfall intensity must exceed the required threshold.</p>")
        self.spinPartialEventThreshold.setToolTip(
            "<p>Defines the percentage by which the measured value can fall short of the original threshold (e.g. depth) and qualify as a partial event. For example, if the required depth is 5mm and the partial event threshold is set to 20% the event qualifies as a partial event at 4mm.</p>")
        self.chkConsecIntensities.setToolTip(
            "<p>When enabled, requires the intensity threshold to be continuously met over the specified duration.</p>")

        self.lstStormEvents.setModel(self.eventsModel)
        self.lstStormEvents.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.lstStormEvents.customContextMenuRequested.connect(
            self.openListViewContextMenu)
        self.updateEventListView()

        self.btnDone.clicked.connect(self.onAccept)

        self.plotAxisRainfallAnalysis = self.plotCanvasEventIdentification.figure.add_subplot(
            111)
        self.plotCanvasEventIdentification.figure.set_dpi(100)
        self.plotCanvasEventIdentification.figure.set_figwidth(7.7)
        self.plotCanvasEventIdentification.figure.set_figheight(5.0)

        aPlotRGs: Optional[plottedRainGauges] = None

        a_int_revs = self.a_project.filter_interim_reviews_by_interim_id(
            interim_id)
        for a_int_rev in a_int_revs.values():
            for a_inst in self.a_project.dict_fsm_installs.values():
                if a_inst.install_type == "Rain Gauge":
                    if a_inst.data is not None and not a_inst.data.empty:
                        aRG = rainGauge()
                        aRG.gaugeName = a_inst.client_ref
                        filtered_data = a_inst.data[(a_inst.data['Date'] >= self.a_project.dict_fsm_interims[interim_id].interim_start_date) &
                                                    (a_inst.data['Date'] <= self.a_project.dict_fsm_interims[interim_id].interim_end_date)]
                        timestamp_list = filtered_data['Date'].to_list()
                        aRG.dateRange = [ts.to_pydatetime()
                                         for ts in timestamp_list]
                        aRG.rainfallDataRange = filtered_data['IntensityData'].to_list(
                        )
                        aRG.rgTimestep = a_inst.data_interval
                        if not aPlotRGs:
                            aPlotRGs = plottedRainGauges()
                        aPlotRGs.addRG(aRG)

        self.aRainfallAnalysis = graphRainfallAnalysis(
            self.plotCanvasEventIdentification)

        self.aRainfallAnalysis.consecZero = int(self.spinConsecZeros.value())
        self.aRainfallAnalysis.requiredDepth = int(self.spinReqDepth.value())
        self.aRainfallAnalysis.requiredIntensity = float(
            self.spinReqIntensity.value())
        self.aRainfallAnalysis.requiredIntensityDuration = int(
            self.spinReqIntensityDuration.value())
        self.aRainfallAnalysis.partialPercent = int(
            self.spinPartialEventThreshold.value())
        self.aRainfallAnalysis.useConsecutiveIntensities = self.chkConsecIntensities.isChecked()
        self.aRainfallAnalysis.plotted_rgs = aPlotRGs
        self.widget_values = WidgetValues()
        self.widget_values.update_values(self.spinConsecZeros.value(),
                                         self.spinReqDepth.value(),
                                         self.spinReqIntensity.value(),
                                         self.spinReqIntensityDuration.value(),
                                         self.spinPartialEventThreshold.value(),
                                         self.chkConsecIntensities.isChecked(),
                                         self.chkUseNewMethod.isChecked())
        self.aRainfallAnalysis.update_plot()

        # Connect the signals of the QSpinBox and QCheckBox widgets to the slot
        self.spinConsecZeros.valueChanged.connect(self.enable_update_button)
        self.spinReqDepth.valueChanged.connect(self.enable_update_button)
        self.spinReqIntensity.valueChanged.connect(self.enable_update_button)
        self.spinReqIntensityDuration.valueChanged.connect(
            self.enable_update_button)
        self.spinPartialEventThreshold.valueChanged.connect(
            self.enable_update_button)
        self.chkConsecIntensities.stateChanged.connect(
            self.enable_update_button)
        self.chkUseNewMethod.stateChanged.connect(
            self.enable_update_button)

        # Connect the clicked signal of the btnUpdate to the update_plot_and_disable slot
        self.btnUpdate.clicked.connect(self.update_plot_and_disable)
        self.btnEventAdd.clicked.connect(
            lambda: self.createNewSurveyEvent(False))
        self.btnEventCapture.clicked.connect(
            lambda: self.createNewSurveyEvent(True))

        a_interim = self.a_project.dict_fsm_interims[interim_id]
        if a_interim is not None:
            self.chk_event_review_complete.setChecked(a_interim.identify_events_complete)

        # result = True
        # for a_int_ser in self.fsmProject.dict_fsm_interim_reviews.values():
        #     if a_int_ser.interim_id == interim_id:
        #         if not a_int_ser.ser_complete:
        #             result = False
        #             break
        # self.chk_event_review_complete

    def openListViewContextMenu(self, position):
        # Get the index of the selected item
        index = self.lstStormEvents.indexAt(position)

        if not index.isValid():
            return

        item = self.model.itemFromIndex(index)
        menu = QtWidgets.QMenu()

        editAction = QtWidgets.QAction("Edit Event", menu)
        editAction.triggered.connect(lambda: self.editSurveyEvent(item))
        menu.addAction(editAction)

        removeAction = QtWidgets.QAction("Remove", menu)
        removeAction.triggered.connect(lambda: self.removeSurveyEvent(item))
        menu.addAction(removeAction)

        menu.exec_(self.lstStormEvents.viewport().mapToGlobal(position))

    def dodgyForceUpdate(self):
        oldSize = self.size()
        self.resize(oldSize.width() - 1, oldSize.height() - 1)
        self.resize(oldSize)

    def editSurveyEvent(self, item):

        # se = self.surveyEvents.getSurveyEvent(item.text(0))
        se = self.a_project.dict_fsm_stormevents[item.text(0)]

        dlgNewEvent = flowbot_dialog_event()
        dlgNewEvent.setWindowTitle('Edit Event')
        dlgNewEvent.edtEventID.setText(se.storm_event_id)
        dlgNewEvent.cboEventType.setCurrentText('Storm')
        dlgNewEvent.cboEventType.setEnabled(False)
        dlgNewEvent.dteEventStart.setDateTime(se.se_start)
        dlgNewEvent.dteEventEnd.setDateTime(se.se_end)
        # dlgNewEvent.show()
        ret = dlgNewEvent.exec_()
        if ret == QDialog.Accepted:
            # self.surveyEvents.removeSurveyEvent(se.eventName)
            # aNewEvent = surveyEvent()
            del self.a_project.dict_fsm_stormevents[item.text(0)]
            new_se = fsmStormEvent()
            new_se.storm_event_id = dlgNewEvent.edtEventID.text()
            new_se.se_start = dlgNewEvent.dteEventStart.dateTime().toPyDateTime()
            new_se.se_end = dlgNewEvent.dteEventEnd.dateTime().toPyDateTime()
            self.a_project.dict_fsm_stormevents[dlgNewEvent.edtEventID.text(
            )] = new_se

            self.updateEventListView()

        # se = self.surveyEvents.getSurveyEvent(item.text(0))
        # dlgNewEvent = flowbot_dialog_event()
        # dlgNewEvent.setWindowTitle('Edit Event')
        # dlgNewEvent.edtEventID.setText(se.eventName)
        # dlgNewEvent.cboEventType.setCurrentText(se.eventType)
        # dlgNewEvent.dteEventStart.setDateTime(se.eventStart)
        # dlgNewEvent.dteEventEnd.setDateTime(se.eventEnd)
        # # dlgNewEvent.show()
        # ret = dlgNewEvent.exec_()
        # if ret == QDialog.Accepted:
        #     self.surveyEvents.removeSurveyEvent(se.eventName)
        #     aNewEvent = surveyEvent()
        #     aNewEvent.eventName = dlgNewEvent.edtEventID.text()
        #     aNewEvent.eventType = dlgNewEvent.cboEventType.currentText()
        #     aNewEvent.eventStart = dlgNewEvent.dteEventStart.dateTime().toPyDateTime()
        #     aNewEvent.eventEnd = dlgNewEvent.dteEventEnd.dateTime().toPyDateTime()
        #     self.surveyEvents.addSurvEvent(aNewEvent)
        #     self.updateEventListView()

    def removeSurveyEvent(self, item):

        # self.surveyEvents.removeSurveyEvent(item.text(0))
        del self.a_project.dict_fsm_stormevents[item.text(0)]
        self.updateEventListView()

    def updateEventListView(self):
        self.eventsModel.clear()

        for se in self.a_project.dict_fsm_stormevents.values():
            it = QtGui.QStandardItem(se.storm_event_id)
            self.eventsModel.appendRow(it)

        # if self.surveyEvents is not None:
        #     for se in self.surveyEvents.survEvents.values():
        #         if se.eventType in ["Storm", "DWF"]:
        #             it = QtGui.QStandardItem(se.eventName)
        #             self.eventsModel.appendRow(it)

    def enable_update_button(self):
        """Enable the update button."""
        self.btnUpdate.setEnabled(True)

    def update_plot_and_disable(self):
        """Update the plot and disable the update button."""
        if self.widget_values.values_changed(self.spinConsecZeros.value(),
                                             self.spinReqDepth.value(),
                                             self.spinReqIntensity.value(),
                                             self.spinReqIntensityDuration.value(),
                                             self.spinPartialEventThreshold.value(),
                                             self.chkConsecIntensities.isChecked(),
                                             self.chkUseNewMethod.isChecked()):
            self.aRainfallAnalysis.consecZero = int(
                self.spinConsecZeros.value())
            self.aRainfallAnalysis.requiredDepth = int(
                self.spinReqDepth.value())
            self.aRainfallAnalysis.requiredIntensity = float(
                self.spinReqIntensity.value())
            self.aRainfallAnalysis.requiredIntensityDuration = int(
                self.spinReqIntensityDuration.value())
            self.aRainfallAnalysis.partialPercent = int(
                self.spinPartialEventThreshold.value())
            self.aRainfallAnalysis.useConsecutiveIntensities = self.chkConsecIntensities.isChecked()
            self.aRainfallAnalysis.useNewMethod = self.chkUseNewMethod.isChecked()
            self.aRainfallAnalysis.analysisNeedsRefreshed = True

        self.aRainfallAnalysis.update_plot()
        self.dodgyForceUpdate()
        self.widget_values.update_values(self.spinConsecZeros.value(),
                                         self.spinReqDepth.value(),
                                         self.spinReqIntensity.value(),
                                         self.spinReqIntensityDuration.value(),
                                         self.spinPartialEventThreshold.value(),
                                         self.chkConsecIntensities.isChecked(),
                                         self.chkUseNewMethod.isChecked())
        self.btnUpdate.setEnabled(False)

    def onAccept(self):

        for a_inst in self.a_project.dict_fsm_installs.values():
            a_int_ser = self.a_project.get_interim_review(
                interim_id=self.interim_id, install_id=a_inst.install_id)
            if not a_int_ser:
                a_int_ser = fsmInterimReview()
                a_int_ser.interim_review_id = self.a_project.get_next_interim_review_id()
                a_int_ser.interim_id = self.interim_id
                a_int_ser.install_id = a_inst.install_id
                self.a_project.add_interim_review(a_int_ser)

            a_int_ser.ser_complete = self.chk_event_review_complete.isChecked()
            a_int_ser.ser_comment = self.txt_review_comments.text()

        self.accept()

    def createNewSurveyEvent(self, capture=False):

        dlgNewEvent = flowbot_dialog_event()

        if capture:
            startDate, endDate = self.getStartEndDateFromCurrentPlot()
            dlgNewEvent.setWindowTitle('Edit Captured Event')
        else:
            startDate, endDate = self.getStartEndDateFromPlottedRGs()
            dlgNewEvent.setWindowTitle('Edit New Event')

        if (startDate is not None) and (endDate is not None):
            dlgNewEvent.dteEventStart.setDateTime(startDate)
            dlgNewEvent.dteEventEnd.setDateTime(endDate)

        dlgNewEvent.cboEventType.setCurrentText('Storm')
        dlgNewEvent.cboEventType.setEnabled(False)

        ret = dlgNewEvent.exec_()
        if ret == QtWidgets.QDialog.Accepted:

            new_se = fsmStormEvent()
            new_se.storm_event_id = dlgNewEvent.edtEventID.text()
            new_se.se_start = dlgNewEvent.dteEventStart.dateTime().toPyDateTime()
            new_se.se_end = dlgNewEvent.dteEventEnd.dateTime().toPyDateTime()
            if not self.a_project.add_storm_event(new_se):
                msg = QMessageBox(self)
                msg.setWindowIcon(self.myIcon)
                msg.critical(self, 'Add Storm Event',
                             'An event with that ID already exists', QMessageBox.Ok)
            self.updateEventListView()

    def getStartEndDateFromCurrentPlot(self):

        aStart, aEnd = mpl_dates.num2date(
            self.aRainfallAnalysis.plotAxisIntensity.get_xlim())

        return aStart, aEnd

    def getStartEndDateFromPlottedRGs(self):

        if self.aRainfallAnalysis.plotted_rgs is not None:
            return self.aRainfallAnalysis.plotted_rgs.plotEarliestStart, self.aRainfallAnalysis.plotted_rgs.plotLatestEnd
        else:
            return None, None


class WidgetValues:
    def __init__(self):
        self.values = {}

    def update_values(self, spin_consec_zeros, spin_req_depth, spin_req_intensity, spin_req_intensity_duration, spin_partial_event_threshold, chk_consec_intensities, chk_use_new_method):
        self.values = {
            "spinConsecZeros": spin_consec_zeros,
            "spinReqDepth": spin_req_depth,
            "spinReqIntensity": spin_req_intensity,
            "spinReqIntensityDuration": spin_req_intensity_duration,
            "spinPartialEventThreshold": spin_partial_event_threshold,
            "chkConsecIntensities": chk_consec_intensities,
            "chkUseNewMethod": chk_use_new_method
        }

    def values_changed(self, spin_consec_zeros, spin_req_depth, spin_req_intensity, spin_req_intensity_duration, spin_partial_event_threshold, chk_consec_intensities, chk_use_new_method):
        current_values = {
            "spinConsecZeros": spin_consec_zeros,
            "spinReqDepth": spin_req_depth,
            "spinReqIntensity": spin_req_intensity,
            "spinReqIntensityDuration": spin_req_intensity_duration,
            "spinPartialEventThreshold": spin_partial_event_threshold,
            "chkConsecIntensities": chk_consec_intensities,
            "chkUseNewMethod": chk_use_new_method
        }
        return current_values != self.values
