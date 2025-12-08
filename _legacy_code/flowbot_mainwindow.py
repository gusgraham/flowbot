from flowbot_helper import *
from flowbot_monitors import *
from flowbot_graphing import *
from flowbot_data_classification import *
from flowbot_schematic import *
from flowbot_verification import *
from flowbot_reporting import *
from flowbot_mapping import *
from flowbot_dialog_reporting_verificationsummary import flowbot_dialog_reporting_verificationsummary
from flowbot_dialog_scattergraph_options import *
from flowbot_dialog_modeldata import *
from flowbot_dialog_fmdataentry import *
from flowbot_dialog_event_analysis_params import *
from flowbot_dialog_event import *
from flowbot_dialog_sumFM_multiplier import *
from flowbot_dialog_data_classification import *
from flowbot_dialog_data_classification_export import *
from flowbot_dialog_scattergraph_export import *
from flowbot_dialog_reporting_fdv import *
from flowbot_dialog_reporting_scatter import *
from flowbot_dialog_reporting_flowbalance import *
from flowbot_dialog_verification_setpeaks import *
from flowbot_dialog_reporting_icmtrace import *
from flowbot_dialog_verification_viewfitmeasure import *
from flowbot_dialog_reporting_eventsuitability import *

from ui_elements.ui_flowbot_mainwindow_base import Ui_MainWindow

class FlowbotMainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    """Main Application Window"""

    def __init__(self, parent=None):
        """Constructor."""
        super(FlowbotMainWindow, self).__init__(parent)

        self.setupUi(self)

        self.myIcon: QtGui.QIcon = QtGui.QIcon()
        self.myIcon.addPixmap(QtGui.QPixmap(resource_path(
            "resources\\Flowbot.ico")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(self.myIcon)

        self.aFDVGraph: Optional[GraphFDV] = None
        self.aScattergraph: Optional[graphScatter] = None
        self.aCumDepthGraph: Optional[graphCumulativeDepth] = None
        self.aRainfallAnalysis: Optional[graphRainfallAnalysis] = None
        self.aDataClassification: Optional[dataClassification] = None
        self.aTraceGraph: Optional[graphICMTrace] = None

        self.openFlowMonitors: Optional[flowMonitors] = None
        self.openRainGauges: Optional[rainGauges] = None
        self.mappedFlowMonitors: Optional[mappedFlowMonitors] = None
        self.identifiedSurveyEvents: Optional[surveyEvents] = None
        self.summedFMs: Optional[Dict[str, summedFlowMonitor]] = None
        self.dummyFMs: Optional[Dict[str, dummyFlowMonitor]] = None
        self.openIcmTraces: Optional[icmTraces] = None

        self.importedICMData = None
        self.lastOpenDialogPath = ''

        self.plotCanvasMain.figure.set_dpi(100)
        self.plotCanvasMain.figure.set_figwidth(15.4)
        self.plotCanvasMain.figure.set_figheight(10.0)

        self.schematicGraphicsView._thisApp = app
        self.defaultSmoothing = {'Observed': 0.0, 'Predicted': 0.0}

        # Main Window Setup:
        self.actionNew_Project.triggered.connect(self.newProject)
        self.actionLoad_Project.triggered.connect(self.loadProject)
        self.actionSave_Project.triggered.connect(self.saveProject)
        self.actionHelp.triggered.connect(self.showHelpFile)
        self.actionInfo.triggered.connect(self.aboutBox)
        self.actionClose.triggered.connect(self.closeApplication)

        self.action_Add_Flow_Monitors.triggered.connect(self.open_FM_files)
        self.action_Add_Rain_Gauges.triggered.connect(self.open_RG_files)
        self.action_Rem_Flow_Monitors.triggered.connect(
            self.remove_all_FM_files)
        self.action_Rem_Rain_Gauges.triggered.connect(self.remove_all_RG_files)
        self.actionICM_Data_Import.triggered.connect(self.importICMModelData)
        self.actionEdit_Monitor_Model_Data.triggered.connect(
            self.updateFlowMonitorModelData)

        self.actionFDV_Graphs.triggered.connect(
            self.createReport_FDV)
        self.actionScattergraphs.triggered.connect(
            self.createReport_Scattergraph)
        self.actionFlow_Volume_Balance.triggered.connect(
            self.createReport_VolumeBalance)
        self.actionEvent_Suitability.triggered.connect(
            self.createReport_EventSuitability)
        self.actionFDV_Graphs_2CSV.triggered.connect(self.toCSV_FDVGraphs)
        self.actionScatter_Graphs_2CSV.triggered.connect(
            self.toCSV_Scattergraph)
        self.actionCumulative_Depth_Graphs_2CSV.triggered.connect(
            self.toCSV_CumulativeRainfall)

        self.actionImport_Trace.triggered.connect(
            self.importICMVerificationTraces)
        self.actionTrace_Outputs.triggered.connect(
            self.createReport_TraceOutputs)
        self.actionVerificationSummary.triggered.connect(
            self.createReport_VerificationSummary)
        self.actionVerificationDetail.triggered.connect(
            self.createReport_VerificationDetail)
        self.actionTraces_2CSV.triggered.connect(self.toCSV_ICMTraces)

        self.actionImportFMLocations.triggered.connect(self.importFMLocations)


        self.progressBar = QProgressBar()
        self.statusBar().addPermanentWidget(self.progressBar)
        self.progressBar.setGeometry(30, 40, 200, 25)
        self.progressBar.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.progressBar.hide()

        self.tbxGraphs.currentChanged.connect(self.update_plot)

        self.trw_PlottedMonitors.customContextMenuRequested.connect(
            self.openPlotTreeViewContextMenu)
        self.trw_PlottedMonitors.viewport().installEventFilter(self)

        self.trw_Scattergraph.customContextMenuRequested.connect(
            self.openPlotTreeViewContextMenu)
        self.trw_Scattergraph.viewport().installEventFilter(self)
        self.btnScattergraphOptions.clicked.connect(
            self.updateScattergraphOption)
        self.btnExportMultiple.clicked.connect(self.exportScattergraphs)

        self.trw_CumDepth.customContextMenuRequested.connect(
            self.openPlotTreeViewContextMenu)
        self.trw_CumDepth.viewport().installEventFilter(self)
        self.btnCumDepthRefresh.clicked.connect(self.update_plot)

        self.trw_RainfallAnalysis.customContextMenuRequested.connect(
            self.openPlotTreeViewContextMenu)
        self.trw_RainfallAnalysis.viewport().installEventFilter(self)
        self.btnRainfallAnalysisRefresh.clicked.connect(self.update_plot)

        self.trw_DataClassification.customContextMenuRequested.connect(
            self.openPlotTreeViewContextMenu)
        self.trw_DataClassification.viewport().installEventFilter(self)
        self.btnExportDCToExcel.clicked.connect(self.exportDataClassification)
        self.btnRefreshDC.clicked.connect(self.refreshDataClassification)

        self.tbxVerification.currentChanged.connect(self.update_plot)

        self.trw_PlottedICMTraces.viewport().installEventFilter(self)
        self.btnTracePrev.clicked.connect(
            lambda: self.updateCurrentTrace(False))
        self.btnTraceNext.clicked.connect(
            lambda: self.updateCurrentTrace(True))

        self.toolBox.currentChanged.connect(self.toolboxChanged)

        # Lists for Open Monitors/Gauges:

        self.lst_FlowMonitors.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lst_FlowMonitors.customContextMenuRequested.connect(self.openFlowMonitorsListContextMenu)

        self.lst_RainGauges.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lst_RainGauges.customContextMenuRequested.connect(self.openRainGaugeListContextMenu)

        # Tree Widget for Summed FMs:
        self.btnSumPlots.clicked.connect(self.toggleSummedFMs)
        self.trwSummedFMs.customContextMenuRequested.connect(
            self.openSummedFMsTreeViewContextMenu)
        self.trwSummedFMs.viewport().installEventFilter(self)

        # Tree Widget for Dummy FMs:
        self.btnDummyFMs.clicked.connect(self.toggleDummyFMs)
        self.trwDummyFMs.customContextMenuRequested.connect(
            self.openDummyFMsTreeViewContextMenu)
        self.trwDummyFMs.viewport().installEventFilter(self)

        # Tree Widget for Events:
        self.trwEvents.customContextMenuRequested.connect(
            self.openEventTreeViewContextMenu)

        # Tree Widget for ICM Traces:
        self.trw_PlottedICMTraces.customContextMenuRequested.connect(
            self.openPlottedTraceTreeViewContextMenu)
        self.lst_ICMTraces.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lst_ICMTraces.customContextMenuRequested.connect(self.openICMTraceListContextMenu)

        # Schematic Graphics View
        self.schematicGraphicsView.viewport().installEventFilter(self)
        schematicToolbar = QToolBar()
        schematicToolbarActionGroup = QActionGroup(self)
        schematicToolbarActionGroup.setExclusive(True)

        myIcon = QtGui.QIcon()
        myIcon.addPixmap(QtGui.QPixmap(
            ":/icons/resources/addWwPS.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.schematicAddWwPSAction = QAction(myIcon, 'Add WwPS', self, triggered=self.schematicAddWwPS)
        self.schematicAddWwPSAction.setCheckable(True)
        schematicToolbar.addAction(self.schematicAddWwPSAction)
        schematicToolbarActionGroup.addAction(self.schematicAddWwPSAction)

        myIcon = QtGui.QIcon()
        myIcon.addPixmap(QtGui.QPixmap(
            ":/icons/resources/addCSO.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.schematicAddCSOAction = QAction(
            myIcon, 'Add CSO', self, triggered=self.schematicAddCSO)
        self.schematicAddCSOAction.setCheckable(True)
        schematicToolbar.addAction(self.schematicAddCSOAction)
        schematicToolbarActionGroup.addAction(self.schematicAddCSOAction)

        myIcon = QtGui.QIcon()
        myIcon.addPixmap(QtGui.QPixmap(
            ":/icons/resources/addWwTW.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.schematicAddWwTWAction = QAction(
            myIcon, 'Add WwTW', self, triggered=self.schematicAddWwTW)
        self.schematicAddWwTWAction.setCheckable(True)
        schematicToolbar.addAction(self.schematicAddWwTWAction)
        schematicToolbarActionGroup.addAction(self.schematicAddWwTWAction)

        myIcon = QtGui.QIcon()
        myIcon.addPixmap(QtGui.QPixmap(
            ":/icons/resources/addJunction.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.schematicAddJuncAction = QAction(
            myIcon, 'Add Junction', self, triggered=self.schematicAddJunction)
        self.schematicAddJuncAction.setCheckable(True)
        schematicToolbar.addAction(self.schematicAddJuncAction)
        schematicToolbarActionGroup.addAction(self.schematicAddJuncAction)

        myIcon = QtGui.QIcon()
        myIcon.addPixmap(QtGui.QPixmap(
            ":/icons/resources/addOutfall.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.schematicAddOutfallAction = QAction(
            myIcon, 'Add Outfall', self, triggered=self.schematicAddOutfall)
        self.schematicAddOutfallAction.setCheckable(True)
        schematicToolbar.addAction(self.schematicAddOutfallAction)
        schematicToolbarActionGroup.addAction(self.schematicAddOutfallAction)

        myIcon = QtGui.QIcon()
        myIcon.addPixmap(QtGui.QPixmap(
            ":/icons/resources/addConnection.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.schematicAddConnectionAction = QAction(
            myIcon, 'Add Connection', self, triggered=self.schematicAddConnection)
        self.schematicAddConnectionAction.setCheckable(True)
        schematicToolbar.addAction(self.schematicAddConnectionAction)
        schematicToolbarActionGroup.addAction(
            self.schematicAddConnectionAction)

        schematicToolbar.addSeparator()

        schematicToolbar.addAction(
            QAction('Print', self, triggered=self.schematicGraphicsView.printSchematic))
        self.tlbSchematicToolbar.layout().setMenuBar(schematicToolbar)

        self.btnEventAdd.clicked.connect(self.addSurveyEvent)
        self.btnEventCapture.clicked.connect(self.captureSurveyEvent)

        # WebEngineView
        self.flowbotWebMap = flowbotWebMap()
        self.webEngineView.handler.signal_popup_clicked.connect(self.handle_webViewPopup_clicked)
        self.webEngineView.load(QUrl.fromLocalFile(self.flowbotWebMap.mapHTMLFile))

        # Finally instantiate a blank FDV graph and update the canvas
        self.initialiseAllVariables()

    def importFMLocations(self):
        
        feature_classes = []
        # Open file dialog to select GeoPackage file
        gpkg_file_path, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Open GeoPackage File", "", "GeoPackage files (*.gpkg)")
        if not gpkg_file_path:
            print("No file selected.")
            return
        try:
            for layername in fiona.listlayers(gpkg_file_path):
                feature_classes.append(layername)

            if len(feature_classes) == 0:
                print("No feature classes found in the GeoPackage.")
                return

            # If there's only one feature class, select it automatically
            if len(feature_classes) == 1:
                selected_feature_class = feature_classes[0]
            else:
                # If there are multiple feature classes, display a dialog to choose one
                selected_feature_class, ok_pressed = QInputDialog.getItem(self, "Select Feature Class", "Choose a feature class:", feature_classes, 0, False)
                if not ok_pressed:
                    print("No feature class selected.")
                    return

            # Open the GeoPackage file
            gdf = gpd.read_file(gpkg_file_path, layer=selected_feature_class)

            crs = CRS.from_user_input(gdf.crs)
            transformer = Transformer.from_crs(crs, "epsg:4326", always_xy=True)

            # Read the selected feature class from the GeoPackage
            # mapped_flow_monitors = gdf[selected_feature_class]

            if self.mappedFlowMonitors is None:
                self.mappedFlowMonitors = mappedFlowMonitors()

            # Now you can iterate through mapped_flow_monitors or perform any other operation as needed
            for index, row in gdf.iterrows():
                if not row['monitorName'] in self.mappedFlowMonitors.dictMappedFlowMonitors:
                    lon, lat = transformer.transform(
                        row.geometry.x, row.geometry.y)
                    mFM = mappedFlowMonitor(row['monitorName'], lat, lon)
                    self.mappedFlowMonitors.addMappedFlowMonitor(mFM)

            self.refreshFlowMonitorListWidget()
            self.updateMapView()
            # print("Mapped flow monitors read successfully.")

        except Exception as e:
            print(f"An error occurred while reading the GeoPackage file: {str(e)}")


    def updateMapView(self, refreshMonitors:bool = False):
        
        if refreshMonitors:
            self.flowbotWebMap.mappedFMs = self.mappedFlowMonitors
        self.flowbotWebMap.updateMap()
        self.webEngineView.load(QUrl.fromLocalFile(self.flowbotWebMap.mapHTMLFile))



    def handle_webViewPopup_clicked(self, popupText):
        # index = self.station_dropdown.findText(popupText)
        # if index != -1:
        #     self.station_dropdown.setCurrentIndex(index)
        pass

    def showHelpFile(self):

        os.startfile(os.getcwd()+"/resources/chm/FlowBot User Manual.chm")

    def toCSV_CumulativeRainfall(self):

        if not self.openRainGauges is None:
            myDict = {}
            fileSpec, filter = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save Cumulative Rainfall to CSV...", self.lastOpenDialogPath, 'csv Files (*.csv)')
            if len(fileSpec) == 0:
                return
            for rg in self.openRainGauges.dictRainGauges.values():

                dates = rg.dateRange
                intencities = rg.rainfallDataRange
                cum_depths = intencities.copy()

                for i in range(len(dates)):
                    if i == 0:
                        cum_depths[0] = 0.0
                    else:
                        timeDelta = int((dates[i] - dates[i-1]).seconds/60)
                        avgIntensity = (intencities[i] + intencities[i-1]) / 2
                        inc_depth = avgIntensity * (timeDelta / 60)
                        cum_depths[i] = cum_depths[i-1] + inc_depth

                myDict.update({f'Date{rg.gaugeName}': rg.dateRange.copy(
                ), f'CumDepth{rg.gaugeName}': cum_depths.copy()})

            max_length = 0
            for item in myDict.values():
                max_length = max(max_length, len(item))

            for item in myDict.values():
                item.extend([None] * (max_length - len(item)))

            if len(myDict) > 0:
                df = pd.DataFrame(myDict)
                df.to_csv(fileSpec)

            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.information(self, 'Export Cumulative Rainfall to CSV',
                            'Export Complete', QMessageBox.Ok)

        else:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.warning(self, 'Export Cumulative Rainfall to CSV',
                        'No open Rain Gauges found', QMessageBox.Ok)

    def toCSV_Scattergraph(self):
        if not self.openFlowMonitors is None:

            myDict = {}
            fileSpec, filter = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save Scatter Graphs to CSV...", self.lastOpenDialogPath, 'csv Files (*.csv)')
            if len(fileSpec) == 0:
                return

            for fm in self.openFlowMonitors.dictFlowMonitors.values():
                myDict.update({f'Depth{fm.monitorName}': fm.depthDataRange.copy(
                ), f'Flow{fm.monitorName}': fm.flowDataRange.copy(), f'Vel{fm.monitorName}': fm.velocityDataRange.copy()})

                if fm.hasModelData:
                    tempPW = PlotWidget(self, False, (15.4, 10.0), 100)
                    scatter = graphScatter(tempPW)
                    scatter.setPlotFM(fm)
                    scatter.calculateCBW()

                    myDict.update({f'CBWDepth{fm.monitorName}': scatter.CBW_depth.copy(
                    ), f'CBWFlow{fm.monitorName}': scatter.CBW_flow.copy(), f'CBWVel{fm.monitorName}': scatter.CBW_velocity.copy()})

                    scatter = None

            max_length = 0
            for item in myDict.values():
                max_length = max(max_length, len(item))

            for item in myDict.values():
                item.extend([None] * (max_length - len(item)))

            if len(myDict) > 0:
                df = pd.DataFrame(myDict)
                df.to_csv(fileSpec)

            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.information(self, 'Export Scattergraph to CSV',
                            'Export Complete', QMessageBox.Ok)
        else:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.warning(self, 'Export Scattergraph to CSV',
                        'No open Flow Monitors found', QMessageBox.Ok)

    def toCSV_FDVGraphs(self):
        if not self.openFlowMonitors is None:

            myDict = {}
            fileSpec, filter = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save FDV Graphs to CSV...", self.lastOpenDialogPath, 'csv Files (*.csv)')
            if len(fileSpec) == 0:
                return

            for fm in self.openFlowMonitors.dictFlowMonitors.values():
                myDict.update({f'Date{fm.monitorName}': fm.dateRange.copy(), f'Flow{fm.monitorName}': fm.flowDataRange.copy(
                ), f'Depth{fm.monitorName}': fm.depthDataRange.copy(), f'Vel{fm.monitorName}': fm.velocityDataRange.copy()})

            if not self.openRainGauges is None:

                for rg in self.openRainGauges.dictRainGauges.values():
                    myDict.update({f'Date{rg.gaugeName}': rg.dateRange.copy(
                    ), f'Intensity{rg.gaugeName}': rg.rainfallDataRange.copy()})

            max_length = 0
            for item in myDict.values():
                max_length = max(max_length, len(item))

            for item in myDict.values():
                item.extend([None] * (max_length - len(item)))

            if len(myDict) > 0:
                df = pd.DataFrame(myDict)
                df.to_csv(fileSpec)

            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.information(self, 'Export FDV to CSV',
                            'Export Complete', QMessageBox.Ok)
        else:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.warning(self, 'Export FDV to CSV',
                        'No open Flow Monitors found', QMessageBox.Ok)

    def copyAndMatchLength(self, origList: list, listToMatchLength: list):

        copyOfList = copy.copy(origList)
        extensionLength = len(listToMatchLength)-len(origList)
        copyOfList.extend([None] * extensionLength)

        return copyOfList

    def toCSV_ICMTraces(self):

        if not self.aTraceGraph is None:
            if not self.aTraceGraph.plottedICMTrace is None:
                if not self.aTraceGraph.plottedICMTrace.plotTrace is None:
                    myDict = {}
                    fileSpec, filter = QtWidgets.QFileDialog.getSaveFileName(
                        self, "Save Traces to CSV...", self.lastOpenDialogPath, 'csv Files (*.csv)')
                    if len(fileSpec) == 0:
                        return
                    traceNo = 1
                    for aLoc in self.aTraceGraph.plottedICMTrace.plotTrace.dictLocations.values():

                        myDict.update(
                            {f'PageTitle{traceNo}': copy.copy([aLoc.pageTitle]),
                             f'Date{traceNo}': copy.copy(aLoc.dates),
                             f'ObsDepth{traceNo}': copy.copy(aLoc.rawData[aLoc.iObsDepth]),
                             f'ObsDepthSmoothed{traceNo}': copy.copy(aLoc.smoothedData[aLoc.iObsDepth]),
                             f'ObsDepthPeakDates{traceNo}': copy.copy(aLoc.peaksDates[aLoc.iObsDepth]),
                             f'ObsDepthPeaks{traceNo}': copy.copy(aLoc.peaksData[aLoc.iObsDepth]),
                             f'PredDepth{traceNo}': copy.copy(aLoc.rawData[aLoc.iPredDepth]),
                             f'PredDepthSmoothed{traceNo}': copy.copy(aLoc.smoothedData[aLoc.iPredDepth]),
                             f'PredDepthPeakDates{traceNo}': copy.copy(aLoc.peaksDates[aLoc.iPredDepth]),
                             f'PredDepthPeaks{traceNo}': copy.copy(aLoc.peaksData[aLoc.iPredDepth]),
                             f'ObsFlow{traceNo}': copy.copy(aLoc.rawData[aLoc.iObsFlow]),
                             f'ObsFlowSmoothed{traceNo}': copy.copy(aLoc.smoothedData[aLoc.iObsFlow]),
                             f'ObsFlowPeakDates{traceNo}': copy.copy(aLoc.peaksDates[aLoc.iObsFlow]),
                             f'ObsFlowPeaks{traceNo}': copy.copy(aLoc.peaksData[aLoc.iObsFlow]),
                             f'PredFlow{traceNo}': copy.copy(aLoc.rawData[aLoc.iPredFlow]),
                             f'PredFlowSmoothed{traceNo}': copy.copy(aLoc.smoothedData[aLoc.iPredFlow]),
                             f'PredFlowPeakDates{traceNo}': copy.copy(aLoc.peaksDates[aLoc.iPredFlow]),
                             f'PredFlowPeaks{traceNo}': copy.copy(aLoc.peaksData[aLoc.iPredFlow]),
                             f'ObsVel{traceNo}': copy.copy(aLoc.rawData[aLoc.iObsVelocity]),
                             f'PredVel{traceNo}': copy.copy(aLoc.rawData[aLoc.iPredVelocity]),
                             f'NSE{traceNo}': copy.copy([aLoc.flowNSE])}
                        )
                        traceNo += 1

                    max_length = 0
                    for item in myDict.values():
                        max_length = max(max_length, len(item))

                    for item in myDict.values():
                        item.extend([None] * (max_length - len(item)))

                    if len(myDict) > 0:
                        df = pd.DataFrame(myDict)
                        df.to_csv(fileSpec)

                        msg = QMessageBox(self)
                        msg.setWindowIcon(self.myIcon)
                        msg.information(self, 'Export Trace CSV',
                                        'Export Complete', QMessageBox.Ok)
                    return

        msg = QMessageBox(self)
        msg.setWindowIcon(self.myIcon)
        msg.information(self, 'Export Trace CSV',
                        'No Plotted Traces Found', QMessageBox.Ok)

    def createReport_VerificationSummary(self):
        if not self.openIcmTraces is None:
            verifSummaryReportDialog = flowbot_dialog_reporting_verificationsummary(self.openIcmTraces, self)
            verifSummaryReportDialog.setWindowTitle(
                'Configure Verification Summary Report')
            verifSummaryReportDialog.show()
            ret = verifSummaryReportDialog.exec_()
            if ret == QDialog.Accepted:
                headers = ['Obs.\nLocation',
                           'Pred.\nLocation',
                           'Critical\nLocation',
                           'Surcharged\nLocation',
                           'Verified\nOverall',
                           'Verified\nFor Flow',
                           'Shape\n(NSE)',
                           'Time of\nFlow Peaks',
                           'Peak\nFlow',
                           'Flow\nVolume',
                           'Verified\nFor Depth',
                           'Time of\nDepth Peaks',
                           'Peak\nDepth']
                rows = []
                summaryTrace = self.openIcmTraces.getTrace(
                    verifSummaryReportDialog.cboICMTraces.currentText())
                for aLoc in summaryTrace.dictLocations.values():

                    obsLoc = aLoc.obsLocation
                    predLoc = aLoc.predLocation + \
                        ' (U/S)' if aLoc.upstreamEnd else aLoc.predLocation + ' (D/S)'
                    critLoc = 'Yes' if aLoc.isCritical else 'No'
                    surchLoc = 'Yes' if aLoc.isSurcharged else 'No'
                    if aLoc.verificationFlowScore + aLoc.verificationDepthScore == 2:
                        verifOverall = 'Yes'
                    elif aLoc.verificationFlowScore + aLoc.verificationDepthScore > 0:
                        verifOverall = 'Partial'
                    else:
                        verifOverall = 'No'
                    if aLoc.verificationFlowScore == 1:
                        verifFlow = 'Yes'
                    elif aLoc.verificationFlowScore > 0:
                        verifFlow = 'Partial'
                    else:
                        verifFlow = 'No'
                    shape = f'{aLoc.flowNSE:.{2}f}'
                    ToPFlow = f'{aLoc.flowTp_Diff_Hrs:.{2}f}'
                    Qp = f'{aLoc.flowQp_Diff_Pcnt:.{1}f}%'
                    QVol = f'{aLoc.flowVol_Diff_Pcnt:.{1}f}%'
                    if aLoc.verificationDepthScore == 1:
                        verifDepth = 'Yes'
                    elif aLoc.verificationDepthScore > 0:
                        verifDepth = 'Partial'
                    else:
                        verifDepth = 'No'
                    ToPFlow = f'{aLoc.depthTp_Diff_Hrs:.{2}f}'
                    Dp = f'{aLoc.depthDp_Diff:.{1}f}m/' + \
                        f'{aLoc.depthDp_Diff_Pcnt:.{1}f}%'
                    myColor = aLoc.getColorFromScore().getRgb()

                    row = []
                    row.append(obsLoc)
                    row.append(predLoc)
                    row.append(critLoc)
                    row.append(surchLoc)
                    row.append(verifOverall)
                    row.append(verifFlow)
                    row.append(shape)
                    row.append(ToPFlow)
                    row.append(Qp)
                    row.append(QVol)
                    row.append(verifDepth)
                    row.append(ToPFlow)
                    row.append(Dp)
                    row.append(myColor)
                    rows.append(row)

                pdf = tablePDF(
                    'L', strTitle=verifSummaryReportDialog.edtReportTitle.text())
                pdf.set_font("helvetica", size=14)
                pdf.add_page('L')
                pdf.colored_table_vs(headers, rows)
                pdf.output(verifSummaryReportDialog.outputFileSpec, 'F')
                os.startfile(verifSummaryReportDialog.outputFileSpec)
        else:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.warning(self, 'Warning',
                        'No open ICM Traces', QMessageBox.Ok)

    def createReport_VerificationDetail(self):

        if not self.openIcmTraces is None:
            tempPlotDir = 'plots'
            try:
                shutil.rmtree(tempPlotDir)
                os.mkdir(tempPlotDir)
                os.mkdir(tempPlotDir + "/graphs/")
                os.mkdir(tempPlotDir + "/tables/")
            except FileNotFoundError:
                os.mkdir(tempPlotDir)
                os.mkdir(tempPlotDir + "/graphs/")
                os.mkdir(tempPlotDir + "/tables/")

            icmTraceReportDialog = flowbot_dialog_reporting_icmtrace(
                self.openIcmTraces)
            icmTraceReportDialog.setWindowTitle(
                'Configure Verification Detail Report')
            icmTraceReportDialog.show()
            ret = icmTraceReportDialog.exec_()
            if ret == QDialog.Accepted:
                self.statusBar().showMessage('Exporting Verification Detail Reports: ')
                self.progressBar.setMinimum(0)
                self.progressBar.setValue(0)
                self.progressBar.show()
                self.progressBar.setMaximum(icmTraceReportDialog.checkCount)

                iFigureNo = 0
                pages_data = []
                for index in range(icmTraceReportDialog.lst_Locations.count()):
                    if icmTraceReportDialog.lst_Locations.item(index).checkState() == Qt.Checked:
                        tr = self.openIcmTraces.getTrace(
                            icmTraceReportDialog.cboICMTraces.currentText())

                        aLoc = tr.dictLocations[index]
                        temp = []
                        myPlotFig = createVerificationDetailPlot(tr, aLoc)
                        myPlotFig.savefig(
                            f'{tempPlotDir}/graphs/{iFigureNo}.png', dpi=100)
                        plt.close(myPlotFig)
                        temp.append(f'{tempPlotDir}/graphs/{iFigureNo}.png')

                        myPlotFig = createVerificationDetailUDGTablePlot(
                            tr, aLoc)
                        myPlotFig.savefig(
                            f'{tempPlotDir}/tables/{iFigureNo}.png', dpi=100)
                        plt.close(myPlotFig)
                        temp.append(f'{tempPlotDir}/tables/{iFigureNo}.png')
                        temp.append("None" if len(
                            aLoc.verificationFlowComment) == 0 else aLoc.verificationFlowComment)
                        temp.append("None" if len(
                            aLoc.verificationDepthComment) == 0 else aLoc.verificationDepthComment)
                        temp.append("None" if len(
                            aLoc.verificationOverallComment) == 0 else aLoc.verificationOverallComment)
                        pages_data.append(temp)

                        iFigureNo += 1

                pdf = verificationDetailPDF(
                    strTitle=icmTraceReportDialog.edtReportTitle.text())
                self.progressBar.setValue(0)
                self.progressBar.setMaximum(len(pages_data))
                iCount = 1

                for pagedata in pages_data:
                    self.progressBar.setValue(iCount)
                    self.statusBar().showMessage('Generating Report Page: ' + str(iCount))
                    pdf.print_page(pagedata)
                    iCount += 1
                    app.processEvents()
                pdf.output(icmTraceReportDialog.outputFileSpec, 'F')
                os.startfile(icmTraceReportDialog.outputFileSpec)

                self.progressBar.hide()
                self.statusBar().clearMessage()

        else:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.warning(self, 'Warning', 'No open ICM Traces', QMessageBox.Ok)

    def createReport_TraceOutputs(self):
        if not self.openIcmTraces is None:
            tempPlotDir = 'plots'
            try:
                shutil.rmtree(tempPlotDir)
                os.mkdir(tempPlotDir)
            except FileNotFoundError:
                os.mkdir(tempPlotDir)

            icmTraceReportDialog = flowbot_dialog_reporting_icmtrace(
                self.openIcmTraces)
            icmTraceReportDialog.setWindowTitle('Configure ICM Traces Report')
            icmTraceReportDialog.show()
            ret = icmTraceReportDialog.exec_()
            if ret == QDialog.Accepted:
                self.statusBar().showMessage('Exporting ICM Traces: ')
                self.progressBar.setMinimum(0)
                self.progressBar.setValue(0)
                self.progressBar.show()
                self.progressBar.setMaximum(icmTraceReportDialog.checkCount)

                tempPW = PlotWidget(self, False, (15.4, 10.0), 100)
                tempTraceGraph = graphICMTrace(tempPW)

                iFigureNo = 0
                for index in range(icmTraceReportDialog.lst_Locations.count()):
                    if icmTraceReportDialog.lst_Locations.item(index).checkState() == Qt.Checked:
                        tr = self.openIcmTraces.getTrace(
                            icmTraceReportDialog.cboICMTraces.currentText())
                        tempTraceGraph.plottedICMTrace.addICMTrace(tr)
                        if not tempTraceGraph.plottedICMTrace.plotTrace is None:
                            tempTraceGraph.plottedICMTrace.plotTrace.currentLocation = index
                            tempTraceGraph.plottedICMTrace.updatePlottedICMTracesMinMaxValues()
                            tempTraceGraph.update_plot()

                            tempTraceGraph.main_window_plot_widget.figure.savefig(
                                f'{tempPlotDir}/{iFigureNo}.png', dpi=100)
                            iFigureNo += 1
                            self.progressBar.setValue(iFigureNo)
                            self.statusBar().showMessage('Generating ICM Trace: ' + str(iFigureNo))
                            app.processEvents()
                pdf = onePagePDF(icmTraceReportDialog.edtReportTitle.text())
                plots_per_page = constructGenericOnePageReport(tempPlotDir)
                self.progressBar.setValue(0)
                self.progressBar.setMaximum(len(plots_per_page))
                iCount = 1

                for elem in plots_per_page:
                    self.progressBar.setValue(iFigureNo)
                    self.statusBar().showMessage('Generating Report Page: ' + str(iCount))
                    app.processEvents()
                    pdf.print_page(elem)
                    iCount += 1

                pdf.output(icmTraceReportDialog.outputFileSpec, 'F')
                os.startfile(icmTraceReportDialog.outputFileSpec)

                self.progressBar.hide()
                self.statusBar().clearMessage()

                plt.close(tempTraceGraph.main_window_plot_widget.figure)
                tempTraceGraph = None

        else:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.warning(self, 'Warning',
                        'No Open Flow Monitors', QMessageBox.Ok)

    def createReport_FDV(self):

        if not self.openFlowMonitors is None:
            tempPlotDir = 'plots'
            try:
                shutil.rmtree(tempPlotDir)
                os.mkdir(tempPlotDir)
            except FileNotFoundError:
                os.mkdir(tempPlotDir)

            fdvReportDialog = flowbot_dialog_reporting_fdv(self.openFlowMonitors, self.openRainGauges, self.identifiedSurveyEvents)
            fdvReportDialog.setWindowTitle('Configure FDV Report')
            fdvReportDialog.show()
            ret = fdvReportDialog.exec_()
            if ret == QDialog.Accepted:

                self.statusBar().showMessage('Exporting FDV Graphs: ')
                self.progressBar.setMinimum(0)
                self.progressBar.setValue(0)
                self.progressBar.show()
                self.progressBar.setMaximum(fdvReportDialog.checkCount)

                tempPW = PlotWidget(self, False, (15.4, 10.0), 100)
                tempGraph = GraphFDV(tempPW)

                iFigureNo = 0
                for index in range(fdvReportDialog.lst_FlowMonitors.count()):
                    if fdvReportDialog.lst_FlowMonitors.item(index).checkState() == Qt.Checked:
                        tempGraph.plotted_fms.clear()
                        tempGraph.plotted_rgs.clear()
                        tempGraph.set_plot_event(None)
                        fm = self.openFlowMonitors.getFlowMonitor(
                            fdvReportDialog.lst_FlowMonitors.item(index).text())
                        if tempGraph.plotted_fms.addFM(fm):
                            if fdvReportDialog.cboRainGauge.currentText() == 'From Model Data':
                                if fm.hasModelData == True:
                                    if len(fm.modelDataRG) > 0:
                                        if not self.openRainGauges is None:
                                            rg = self.openRainGauges.getRainGauge(
                                                fm.modelDataRG)
                                            if not rg is None:
                                                tempGraph.plotted_rgs.clear()
                                                tempGraph.plotted_rgs.addRG(
                                                    rg)
                            else:
                                tempGraph.plotted_rgs.addRG(self.openRainGauges.getRainGauge(
                                    fdvReportDialog.cboRainGauge.currentText()))

                            if not fdvReportDialog.cboEvent.currentText() == 'Full Period':
                                tempGraph.set_plot_event(self.identifiedSurveyEvents.getSurveyEvent(
                                    fdvReportDialog.cboEvent.currentText()))
                            tempGraph.update_plot()
                            tempGraph.main_window_plot_widget.figure.savefig(
                                f'{tempPlotDir}/{iFigureNo}.png', dpi=100)
                            iFigureNo += 1
                            self.progressBar.setValue(iFigureNo)
                            self.statusBar().showMessage('Generating FDV Graph: ' + str(iFigureNo))
                            app.processEvents()

                pdf = onePagePDF(fdvReportDialog.edtReportTitle.text())
                plots_per_page = constructGenericOnePageReport(tempPlotDir)
                self.progressBar.setValue(0)
                self.progressBar.setMaximum(len(plots_per_page))
                iCount = 1

                for elem in plots_per_page:
                    self.progressBar.setValue(iFigureNo)
                    self.statusBar().showMessage('Generating Report Page: ' + str(iCount))
                    app.processEvents()
                    pdf.print_page(elem)
                    iCount += 1

                pdf.output(fdvReportDialog.outputFileSpec, 'F')
                os.startfile(fdvReportDialog.outputFileSpec)

                self.progressBar.hide()
                self.statusBar().clearMessage()

                plt.close(tempGraph.main_window_plot_widget.figure)
                tempGraph = None
                # self.update_plot()

        else:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.warning(self, 'Warning',
                        'No Open Flow Monitors', QMessageBox.Ok)

    def createReport_VolumeBalance(self):

        if not self.openFlowMonitors is None:

            flowbalReportDialog = flowbot_dialog_reporting_flowbalance(
                self.openFlowMonitors, self.identifiedSurveyEvents)
            flowbalReportDialog.setWindowTitle('Configure Flow Balance Report')
            flowbalReportDialog.show()
            ret = flowbalReportDialog.exec_()
            if ret == QDialog.Accepted:
                headers = ['FM ID', 'Flow Vol', 'US FMs',
                           'US Flow Vol', 'Vol Difference']
                rows = []
                nisList = []
                for index in range(flowbalReportDialog.lst_FlowMonitors.count()):
                    if flowbalReportDialog.lst_FlowMonitors.item(index).checkState() == Qt.Checked:
                        fm = self.openFlowMonitors.getFlowMonitor(
                            flowbalReportDialog.lst_FlowMonitors.item(index).text())
                        FMName = fm.monitorName
                        fmSchem = self.schematicGraphicsView.getSchematicFlowMonitorsByName(
                            FMName)

                        if not fmSchem is None:
                            startDate = None
                            endDate = None
                            if not flowbalReportDialog.cboEvent.currentText() == 'Full Period':
                                se = self.identifiedSurveyEvents.getSurveyEvent(
                                    flowbalReportDialog.cboEvent.currentText())
                                startDate = se.eventStart
                                endDate = se.eventEnd
                            else:
                                startDate = fm.dateRange[0]
                                endDate = fm.dateRange[len(fm.dateRange)-1]
                            flowVol = fm.getFlowVolumeBetweenDates(
                                startDate, endDate)
                            self.schematicGraphicsView.schematicFMUSTrace(
                                FMName, True)
                            usVolume = 0
                            usFMs = ''
                            for item in self.schematicGraphicsView._currentTrace:
                                if isinstance(item, fmGraphicsItem):
                                    if not item is fmSchem:
                                        usfm = self.openFlowMonitors.getFlowMonitor(
                                            item._text)
                                        if len(usFMs) == 0:
                                            usFMs = item._text
                                        else:
                                            usFMs = usFMs + ', ' + item._text
                                        usVolume += usfm.getFlowVolumeBetweenDates(
                                            startDate, endDate)
                            volDiff = flowVol - usVolume
                            flowVol = "%.2f" % round(flowVol, 2)
                            usVolume = "%.2f" % round(usVolume, 2)
                            volDiff = "%.2f" % round(volDiff, 2)
                            if len(usFMs) == 0:
                                usFMs = "-"
                                usVolume = "-"
                                volDiff = "-"
                            row = []
                            row.append(FMName)
                            row.append(flowVol)
                            row.append(usFMs)
                            row.append(usVolume)
                            row.append(volDiff)
                            rows.append(row)
                        else:
                            nisList.append(FMName)

                for item in nisList:
                    row = []
                    row.append(item)
                    row.append("Not in schematic")
                    row.append("-")
                    row.append("-")
                    row.append("-")
                    rows.append(row)

                pdf = tablePDF(
                    strTitle=flowbalReportDialog.edtReportTitle.text())
                pdf.set_font("helvetica", size=14)
                pdf.add_page()
                pdf.colored_table_vb(headers, rows)
                pdf.output(flowbalReportDialog.outputFileSpec, 'F')
                os.startfile(flowbalReportDialog.outputFileSpec)

        else:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.warning(self, 'Warning',
                        'No Open Flow Monitors', QMessageBox.Ok)
            
    def createReport_EventSuitability(self):

        if not self.openFlowMonitors is None and not self.openRainGauges is None and not self.identifiedSurveyEvents is None:
            tempPlotDir = 'plots'
            try:
                shutil.rmtree(tempPlotDir)
                os.mkdir(tempPlotDir)
                os.mkdir(tempPlotDir + "/graph1/")
                os.mkdir(tempPlotDir + "/graph2/")
                os.mkdir(tempPlotDir + "/table1/")
                os.mkdir(tempPlotDir + "/table2/")
            except FileNotFoundError:
                os.mkdir(tempPlotDir)
                os.mkdir(tempPlotDir + "/graph1/")
                os.mkdir(tempPlotDir + "/graph2/")
                os.mkdir(tempPlotDir + "/table1/")
                os.mkdir(tempPlotDir + "/table2/")

            esReportDialog = flowbot_dialog_reporting_eventsuitability(
                self.openFlowMonitors, self.openRainGauges, self.identifiedSurveyEvents)
            esReportDialog.setWindowTitle('Configure EVent Suitability Report')
            esReportDialog.show()
            ret = esReportDialog.exec_()
            if ret == QDialog.Accepted:

                self.statusBar().showMessage('Exporting Event Suitability Graphs: ')
                self.progressBar.setMinimum(0)
                self.progressBar.setValue(0)
                self.progressBar.show()
                self.progressBar.setMaximum(esReportDialog.fmCheckCount)

                tempPW = PlotWidget(self, False, (8.3, 5), 100)
                tempGraph = dataClassification(tempPW, app, self, False)

                iFigureNo = 0
                for index in range(esReportDialog.lst_FlowMonitors.count()):
                    if esReportDialog.lst_FlowMonitors.item(index).checkState() == Qt.Checked:
                        tempGraph.classifiedFMs.addFM(self.openFlowMonitors.getFlowMonitor(
                            esReportDialog.lst_FlowMonitors.item(index).text()))
                tempGraph.classificationNeedsRefreshed = True
                tempGraph.updateFlowSurveyDataClassification()
                while tempGraph.classificationNeedsRefreshed:
                    time.sleep(0.1)

                tempGraph2 = graphCumulativeDepth(tempPW)

                pages_data = []
                for se_index in range(esReportDialog.lst_Events.count()):
                    temp = []

                    if esReportDialog.lst_Events.item(se_index).checkState() == Qt.Checked:

                        se = self.identifiedSurveyEvents.getSurveyEvent(
                            esReportDialog.lst_Events.item(se_index).text())
                        tempGraph2.set_plot_event(se)

                        myPlotFig = createEventSuitabilityEventSummaryTablePlot(se)
                        myPlotFig.savefig(
                            f'{tempPlotDir}/table1/{iFigureNo}.png', dpi=100)
                        plt.close(myPlotFig)
                        temp.append(f'{tempPlotDir}/table1/{iFigureNo}.png')

                        rgStats = {}
                        for rg_index in range(esReportDialog.lst_RainGauges.count()):
                            if esReportDialog.lst_RainGauges.item(rg_index).checkState() == Qt.Checked:
                                rg = self.openRainGauges.getRainGauge(
                                    esReportDialog.lst_RainGauges.item(rg_index).text())
                                rgStats[rg_index] = rg.eventStatsBetweenDates(
                                    se.eventStart, se.eventEnd)
                                tempGraph2.plotted_rgs.addRG(rg)

                        table_data = [["RG Name", "Start Time", "Duration", "Total\nDepth",
                                       "Peak\nIntensity", "Period Greater\nthan 6mm/hr", "Variability\n(per RG)"]]
                        avgTotDepth = 0
                        for rg_key in rgStats.keys():
                            temp1 = []
                            for i in range(len(rgStats[rg_key])):
                                temp1.append(rgStats[rg_key][i])
                                if i == 3:
                                    avgTotDepth += rgStats[rg_key][i]
                            table_data.append(temp1)

                        avgTotDepth = avgTotDepth / len(rgStats.keys())

                        for i in range(len(table_data)):
                            if i > 0:
                                if avgTotDepth > 0:
                                    table_data[i].append(
                                        f'{((table_data[i][3] - avgTotDepth) / avgTotDepth)*100:.{2}f}%')
                                else:
                                    table_data[i].append('')

                        myPlotFig = createEventSuitabilityRaingaugeDetailsTablePlot(
                            table_data)
                        myPlotFig.savefig(
                            f'{tempPlotDir}/table2/{iFigureNo}.png', dpi=100)
                        plt.close(myPlotFig)
                        temp.append(f'{tempPlotDir}/table2/{iFigureNo}.png')

                        fmClass = tempGraph.getEventBasedFMClassifications(se)

                        myPlotFig = createEventSuitabilityFMClassPiePlot(
                            fmClass)
                        myPlotFig.savefig(
                            f'{tempPlotDir}/graph1/{iFigureNo}.png', dpi=100)
                        plt.close(myPlotFig)
                        temp.append(f'{tempPlotDir}/graph1/{iFigureNo}.png')

                        tempGraph2.update_plot()
                        tempGraph2.main_window_plot_widget.figure.savefig(
                            f'{tempPlotDir}/graph2/{iFigureNo}.png', dpi=100)
                        temp.append(f'{tempPlotDir}/graph2/{iFigureNo}.png')

                        pages_data.append(temp)
                        iFigureNo += 1

                pdf = eventSuitabilityPDF(
                    strTitle=esReportDialog.edtReportTitle.text())
                self.progressBar.setValue(0)
                self.progressBar.setMaximum(len(pages_data))
                iCount = 1

                for pagedata in pages_data:
                    self.progressBar.setValue(iCount)
                    self.statusBar().showMessage('Generating Report Page: ' + str(iCount))
                    app.processEvents()
                    pdf.print_page(pagedata)
                    iCount += 1

                pdf.output(esReportDialog.outputFileSpec, 'F')
                os.startfile(esReportDialog.outputFileSpec)

                self.progressBar.hide()
                self.statusBar().clearMessage()

                plt.close(tempGraph2.main_window_plot_widget.figure)
                tempGraph = None
                tempGraph2 = None
        else:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.warning(self, 'Warning',
                        'No open Flow Monitors/Rain Gauges/Events', QMessageBox.Ok)

    def load_data_from_csv(self, csv_filepath):
        headings, rows = [], []
        with open(csv_filepath, encoding="utf8") as csv_file:
            for row in csv.reader(csv_file, delimiter=","):
                if not headings:  # extracting column names from first row:
                    headings = row
                else:
                    rows.append(row)
        return headings, rows

    def createReport_Scattergraph(self):

        if not self.openFlowMonitors is None:
            tempPlotDir = 'plots'
            try:
                shutil.rmtree(tempPlotDir)
                os.mkdir(tempPlotDir)
            except FileNotFoundError:
                os.mkdir(tempPlotDir)

            scatterReportDialog = flowbot_dialog_reporting_scatter(
                self.openFlowMonitors, self.identifiedSurveyEvents)
            scatterReportDialog.setWindowTitle('Configure Scattergraph Report')
            scatterReportDialog.show()
            ret = scatterReportDialog.exec_()
            if ret == QDialog.Accepted:
                self.statusBar().showMessage('Exporting Scattergraphs: ')
                self.progressBar.setMinimum(0)
                self.progressBar.setValue(0)
                self.progressBar.show()
                self.progressBar.setMaximum(scatterReportDialog.fmCheckCount)

                tempPW = PlotWidget(self, False, (15.4, 10.0), 100)
                tempGraph = graphScatter(tempPW)

                for index in range(scatterReportDialog.lst_Events.count()):
                    if scatterReportDialog.lst_Events.item(index).checkState() == Qt.Checked:
                        tempGraph.plottedEvents.addSurveyEvent(self.identifiedSurveyEvents.getSurveyEvent(
                            scatterReportDialog.lst_Events.item(index).text()))

                iFigureNo = 0
                for index in range(scatterReportDialog.lst_FlowMonitors.count()):
                    if scatterReportDialog.lst_FlowMonitors.item(index).checkState() == Qt.Checked:
                        tempGraph.setPlotFM(None)

                        fm = self.openFlowMonitors.getFlowMonitor(
                            scatterReportDialog.lst_FlowMonitors.item(index).text())
                        tempGraph.setPlotFM(fm)

                        tempGraph.plotFPData = scatterReportDialog.chkFullPeriodData.isChecked()
                        tempGraph.ignoreDataAboveSoffit = scatterReportDialog.chkIgnoreDataAboveSoffit.isChecked()
                        tempGraph.ignoreZeros = scatterReportDialog.chkIgnoreZeros.isChecked()
                        tempGraph.plotModelData = scatterReportDialog.chkModelData.isChecked()
                        if scatterReportDialog.chkModelData.isChecked():
                            tempGraph.showPipeProfile = scatterReportDialog.chkPipeProfile.isChecked()
                            tempGraph.plotCBWLine = scatterReportDialog.chkCBWData.isChecked()
                        else:
                            tempGraph.showPipeProfile = tempGraph.plotCBWLine = False
                        tempGraph.plotIsoQLines = False
                        tempGraph.plotVelocityScattergraph = scatterReportDialog.rbnVelocity.isChecked()

                        tempGraph.update_plot()
                        tempGraph.main_window_plot_widget.figure.savefig(
                            f'{tempPlotDir}/{iFigureNo}.png', dpi=100)
                        iFigureNo += 1
                        self.progressBar.setValue(iFigureNo)
                        self.statusBar().showMessage('Generating Scattergraph: ' + str(iFigureNo))
                        app.processEvents()

                pdf = onePagePDF(scatterReportDialog.edtReportTitle.text())
                plots_per_page = constructGenericOnePageReport(tempPlotDir)
                self.progressBar.setValue(0)
                self.progressBar.setMaximum(len(plots_per_page))
                iCount = 1

                for elem in plots_per_page:
                    self.progressBar.setValue(iFigureNo)
                    self.statusBar().showMessage('Generating Report Page: ' + str(iCount))
                    app.processEvents()
                    pdf.print_page(elem)
                    iCount += 1

                pdf.output(scatterReportDialog.outputFileSpec, 'F')
                os.startfile(scatterReportDialog.outputFileSpec)

                self.progressBar.hide()
                self.statusBar().clearMessage()

                plt.close(tempGraph.main_window_plot_widget.figure)
                tempGraph = None

        else:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.warning(self, 'Warning',
                        'No Open Flow Monitors', QMessageBox.Ok)

    def toolboxChanged(self):

        if self.toolBox.currentWidget().objectName() == 'pageFlowSurveyAnalysis':
            self.tabWidgetMainWindow.setTabVisible(1, True)
        else:
            self.tabWidgetMainWindow.setTabVisible(1, False)
        self.update_plot()

    def setCurrentTrace(self, newLocation: int):
        if not self.aTraceGraph is None:
            if not self.aTraceGraph.plottedICMTrace.plotTrace is None:
                self.aTraceGraph.plottedICMTrace.plotTrace.currentLocation = newLocation
                self.aTraceGraph.plottedICMTrace.updatePlottedICMTracesMinMaxValues()
                self.update_plot()
                self.updateICMTraceButtons()

    def updateCurrentTrace(self, next: bool):

        if not self.aTraceGraph is None:
            if not self.aTraceGraph.plottedICMTrace.plotTrace is None:
                if next:
                    if self.aTraceGraph.plottedICMTrace.plotTrace.currentLocation < len(self.aTraceGraph.plottedICMTrace.plotTrace.dictLocations) - 1:
                        self.aTraceGraph.plottedICMTrace.plotTrace.currentLocation += 1
                        self.aTraceGraph.plottedICMTrace.updatePlottedICMTracesMinMaxValues()
                else:
                    if self.aTraceGraph.plottedICMTrace.plotTrace.currentLocation > 0:
                        self.aTraceGraph.plottedICMTrace.plotTrace.currentLocation -= 1
                        self.aTraceGraph.plottedICMTrace.updatePlottedICMTracesMinMaxValues()
                self.update_plot()
                self.updateICMTraceButtons()

    def importICMVerificationTraces(self):

        dialog = QtWidgets.QFileDialog(self)
        path, _ = dialog.getOpenFileNames(
            self, 'Please select the ICM trace file', self.lastOpenDialogPath, 'ICM Trace Files (*.csv)')
        if not path:
            return

        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(len(path))
        self.progressBar.setValue(0)
        self.progressBar.show()

        if self.openIcmTraces is None:
            self.openIcmTraces = icmTraces()

        for i in range(len(path)):
            self.progressBar.setValue(i)
            app.processEvents()
            traceFileSpec = path[i]
            self.statusBar().showMessage('Reading: ' + traceFileSpec)

            self.openIcmTraces.getTracesFromCSVFile(
                traceFileSpec, self.defaultSmoothing)

        self.statusBar().clearMessage()
        self.progressBar.hide()
        self.refreshICMTraceListWidget()
        self.lastOpenDialogPath = os.path.dirname(path[0])

    def schematicAddWwPS(self):
        if self.schematicGraphicsView._curretSchematicTool == cstWWPS:
            app.instance().restoreOverrideCursor()
            self.schematicGraphicsView._curretSchematicTool = cstNONE
            self.schematicAddWwPSAction.setChecked(False)
        else:
            app.instance().restoreOverrideCursor()
            app.instance().setOverrideCursor(Qt.CrossCursor)
            self.schematicGraphicsView._curretSchematicTool = cstWWPS

    def schematicAddCSO(self):
        if self.schematicGraphicsView._curretSchematicTool == cstCSO:
            app.instance().restoreOverrideCursor()
            self.schematicGraphicsView._curretSchematicTool = cstNONE
            self.schematicAddCSOAction.setChecked(False)
        else:
            app.instance().restoreOverrideCursor()
            app.instance().setOverrideCursor(Qt.CrossCursor)
            self.schematicGraphicsView._curretSchematicTool = cstCSO

    def schematicAddJunction(self):
        if self.schematicGraphicsView._curretSchematicTool == cstJUNCTION:
            app.instance().restoreOverrideCursor()
            self.schematicGraphicsView._curretSchematicTool = cstNONE
            self.schematicAddJuncAction.setChecked(False)
        else:
            app.instance().restoreOverrideCursor()
            app.instance().setOverrideCursor(Qt.CrossCursor)
            self.schematicGraphicsView._curretSchematicTool = cstJUNCTION

    def schematicAddOutfall(self):
        if self.schematicGraphicsView._curretSchematicTool == cstOUTFALL:
            app.instance().restoreOverrideCursor()
            self.schematicGraphicsView._curretSchematicTool = cstNONE
            self.schematicAddOutfallAction.setChecked(False)
        else:
            app.instance().restoreOverrideCursor()
            app.instance().setOverrideCursor(Qt.CrossCursor)
            self.schematicGraphicsView._curretSchematicTool = cstOUTFALL

    def schematicAddWwTW(self):
        if self.schematicGraphicsView._curretSchematicTool == cstWWTW:
            app.instance().restoreOverrideCursor()
            self.schematicGraphicsView._curretSchematicTool = cstNONE
            self.schematicAddWwTWAction.setChecked(False)
        else:
            app.instance().restoreOverrideCursor()
            app.instance().setOverrideCursor(Qt.CrossCursor)
            self.schematicGraphicsView._curretSchematicTool = cstWWTW

    def schematicAddConnection(self):
        if self.schematicGraphicsView._curretSchematicTool == cstCONNECTION:
            app.instance().restoreOverrideCursor()
            self.schematicGraphicsView._curretSchematicTool = cstNONE
            self.schematicAddConnectionAction.setChecked(False)
            self.schematicGraphicsView.clearAllVisibleControlPoints()
            self.schematicGraphicsView.setDragMode(
                QGraphicsView.RubberBandDrag)
        else:
            app.instance().restoreOverrideCursor()
            app.instance().setOverrideCursor(Qt.CrossCursor)
            self.schematicGraphicsView._curretSchematicTool = cstCONNECTION

    def aboutBox(self):

        myTxt = "Flowbot " + strVersion + "\n" + "\n" + \
            "Refactored from Flowbot v1.3.4" + "\n" + "by Fergus.Graham@rpsgroup.com"
        msg = QMessageBox(self)
        msg.setWindowIcon(self.myIcon)
        msg.information(self, 'About', myTxt, QMessageBox.Ok)

    def eventFilter(self, o, e):
        if e.type() == QtCore.QEvent.Type.Drop:
            if ((o == self.trw_PlottedMonitors.viewport()) or
                (o == self.trw_Scattergraph.viewport()) or
                (o == self.trw_CumDepth.viewport()) or
                (o == self.trw_RainfallAnalysis.viewport()) or
                    (o == self.trw_DataClassification.viewport())):
                self.tbxGraphs_drop_action(e)
                return True
            elif (o == self.trwSummedFMs.viewport()):
                self.summedFM_drop_action(e)
                return True
            elif (o == self.schematicGraphicsView.viewport()):
                self.schematic_drop_action(e)
                return True
            elif (o == self.trw_PlottedICMTraces.viewport()):
                self.tbxVerification_drop_action(e)
                return True

            else:
                return False
        if e.type() == QtCore.QEvent.Type.MouseButtonDblClick:
            if o == self.trw_PlottedICMTraces.viewport():
                item = self.trw_PlottedICMTraces.itemAt(e.pos())
                self.setCurrentTrace(
                    self.trw_PlottedICMTraces.indexFromItem(item).row())
                self.trw_PlottedICMTraces.setCurrentItem(item)
                return True
            else:
                return False
        else:
            return False

    def schematic_drop_action(self, e):
        if e.source() == self.lst_FlowMonitors:

            source_item = QStandardItemModel()
            source_item.dropMimeData(
                e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

            offset = 0
            for i in range(source_item.rowCount()):
                fm = self.openFlowMonitors.getFlowMonitor(
                    source_item.item(i, 0).text())
                if fm._schematicGraphicItem is None:
                    fm._schematicGraphicItem = self.schematicGraphicsView.addFlowMonitor(
                        fm.monitorName, self.schematicGraphicsView.mapToScene(e.pos()), offset)
                    offset += 50

        elif e.source() == self.lst_RainGauges:

            source_item = QStandardItemModel()
            source_item.dropMimeData(
                e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

            offset = 0
            for i in range(source_item.rowCount()):
                rg = self.openRainGauges.getRainGauge(
                    source_item.item(i, 0).text())
                if rg._schematicGraphicItem is None:
                    rg._schematicGraphicItem = self.schematicGraphicsView.addRaingauge(
                        rg.gaugeName, self.schematicGraphicsView.mapToScene(e.pos()), offset)
                    offset += 50

    def summedFM_drop_action(self, e):

        if e.source() == self.lst_FlowMonitors:
            target_item = self.trwSummedFMs.itemAt(e.pos())
            if not target_item is None:
                level = 0
                if not target_item.parent() is None:
                    while target_item.parent().isValid():
                        index = target_item.parent()
                        level += 1

                if level == 0:
                    sFM = self.summedFMs[target_item.text(0)]
                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())
                    for i in range(source_item.rowCount()):
                        sFM.addFM(self.openFlowMonitors.getFlowMonitor(
                            source_item.item(i, 0).text()), 1)
                    self.summedFMs[target_item.text(0)] = sFM
                    self.updateSummedFMTreeView()

                    if self.tbxGraphs.currentWidget().objectName() == "pageFDV":
                        if sFM.equivalentFM.monitorName in self.aFDVGraph.plotted_fms.plotFMs:
                            self.update_plot()

                    if self.tbxGraphs.currentWidget().objectName() == "pageScattergraphs":
                        if sFM.equivalentFM.monitorName == self.aScattergraph.getPlotFM().monitorName:
                            self.update_plot()

            else:
                if self.summedFMs is None:
                    self.summedFMs = {}

                text, ok = QInputDialog.getText(
                    self, 'New Summed FM', 'Name for Summed FM:')
                if ok:
                    if not text in self.summedFMs:
                        sFM = summedFlowMonitor()
                        sFM.sumFMName = text

                        source_item = QStandardItemModel()
                        source_item.dropMimeData(
                            e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())
                        for i in range(source_item.rowCount()):
                            sFM.addFM(self.openFlowMonitors.getFlowMonitor(
                                source_item.item(i, 0).text()), 1)

                        self.summedFMs[text] = sFM
                        self.updateSummedFMTreeView()

    def tbxGraphs_drop_action(self, e):

        addedToPlot = False
        if self.tbxGraphs.currentWidget().objectName() == "pageFDV":
            if not self.aFDVGraph is None:
                if e.source() == self.lst_FlowMonitors:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    if source_item.rowCount() == 1:
                        self.aFDVGraph.plotted_fms = plottedFlowMonitors()
                        addedToPlot = True

                    for i in range(source_item.rowCount()):
                        fm = self.openFlowMonitors.getFlowMonitor(
                            source_item.item(i, 0).text())
                        if self.aFDVGraph.plotted_fms.addFM(fm, False):
                            if fm.hasModelData == True:
                                if len(fm.modelDataRG) > 0:
                                    if not self.openRainGauges is None:
                                        rg = self.openRainGauges.getRainGauge(
                                            fm.modelDataRG)
                                        if not rg is None:
                                            self.aFDVGraph.plotted_rgs.clear()
                                            self.aFDVGraph.plotted_rgs.addRG(
                                                rg)
                            addedToPlot = True
                    self.aFDVGraph.plotted_fms.updatePlottedFMsMinMaxValues()
                elif e.source() == self.lst_RainGauges:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    if source_item.rowCount() > 0:
                        # Just ploting one RG at a time on the FDV graph
                        self.aFDVGraph.plotted_rgs.clear()
                        self.aFDVGraph.plotted_rgs.addRG(
                            self.openRainGauges.getRainGauge(source_item.item(0, 0).text()))
                        addedToPlot = True

                elif e.source() == self.trwEvents:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    if source_item.rowCount() > 0:
                        self.aFDVGraph.set_plot_event(
                            self.identifiedSurveyEvents.getSurveyEvent(source_item.item(0, 0).text()))
                        addedToPlot = True

                elif e.source() == self.trwSummedFMs:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    if source_item.rowCount() > 0:
                        if source_item.item(0, 0).text() in self.summedFMs:
                            sFM = self.summedFMs[source_item.item(0, 0).text()]
                            if self.aFDVGraph.plotted_fms.addFM(sFM.equivalentFM):
                                addedToPlot = True

                elif e.source() == self.trwDummyFMs:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    if source_item.rowCount() > 0:
                        if source_item.item(0, 0).text() in self.dummyFMs:
                            dFM = self.dummyFMs[source_item.item(0, 0).text()]
                            if self.aFDVGraph.plotted_fms.addFM(dFM.equivalentFM):
                                addedToPlot = True

                else:
                    print("dropped from IDK?")

        if self.tbxGraphs.currentWidget().objectName() == "pageScattergraphs":
            if not self.aScattergraph is None:
                if e.source() == self.lst_FlowMonitors:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    if source_item.rowCount() > 0:
                        self.aScattergraph.setPlotFM(
                            self.openFlowMonitors.getFlowMonitor(source_item.item(0, 0).text()))
                        addedToPlot = True

                elif e.source() == self.trwDummyFMs:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    if source_item.rowCount() > 0:
                        if source_item.item(0, 0).text() in self.dummyFMs:
                            dFM = self.dummyFMs[source_item.item(0, 0).text()]
                            self.aScattergraph.setPlotFM(dFM.equivalentFM)
                            addedToPlot = True

                elif e.source() == self.trwEvents:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    for i in range(source_item.rowCount()):
                        if self.aScattergraph.plottedEvents.addSurveyEvent(self.identifiedSurveyEvents.getSurveyEvent(source_item.item(i, 0).text())):
                            addedToPlot = True

        if self.tbxGraphs.currentWidget().objectName() == "pageRainfallCumDepth":
            if not self.aCumDepthGraph is None:
                if e.source() == self.lst_RainGauges:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    for i in range(source_item.rowCount()):
                        if self.aCumDepthGraph.plotted_rgs.addRG(self.openRainGauges.getRainGauge(source_item.item(i, 0).text()), False):
                            addedToPlot = True
                    self.aCumDepthGraph.plotted_rgs.updatePlottedRGsMinMaxValues()

                elif e.source() == self.trwEvents:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    if source_item.rowCount() > 0:
                        self.aCumDepthGraph.set_plot_event(
                            self.identifiedSurveyEvents.getSurveyEvent(source_item.item(0, 0).text()))
                        addedToPlot = True

                else:
                    print("dropped from IDK?")

        if self.tbxGraphs.currentWidget().objectName() == "pageRainfallAnalysis":
            if not self.aRainfallAnalysis is None:
                if e.source() == self.lst_RainGauges:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    for i in range(source_item.rowCount()):
                        if self.aRainfallAnalysis.plotted_rgs.addRG(self.openRainGauges.getRainGauge(source_item.item(i, 0).text()), False):
                            addedToPlot = True
                            self.aRainfallAnalysis.analysisNeedsRefreshed = True
                    self.aRainfallAnalysis.plotted_rgs.updatePlottedRGsMinMaxValues()
                else:
                    print("dropped from IDK?")

        if self.tbxGraphs.currentWidget().objectName() == "pageDataClassification":
            if not self.aDataClassification is None:
                if e.source() == self.lst_FlowMonitors:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    for i in range(source_item.rowCount()):
                        if self.aDataClassification.classifiedFMs.addFM(self.openFlowMonitors.getFlowMonitor(source_item.item(i, 0).text())):
                            addedToPlot = True
                            self.aDataClassification.classificationNeedsRefreshed = True
                    self.aDataClassification.classifiedFMs.updateClassifiedFMsMinMaxValues()
                elif e.source() == self.trwEvents:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    for i in range(source_item.rowCount()):
                        if self.aDataClassification.plottedEvents.addSurveyEvent(self.identifiedSurveyEvents.getSurveyEvent(source_item.item(i, 0).text())):
                            addedToPlot = True
                    self.aDataClassification.plottedEvents.updateMinMaxValues()
                else:
                    print("dropped from IDK?")

        if addedToPlot:
            self.update_plot()

    def tbxVerification_drop_action(self, e):

        addedToPlot = False

        if self.tbxVerification.currentWidget().objectName() == "pageVerificationPlots":
            if not self.aTraceGraph is None:
                if e.source() == self.lst_ICMTraces:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    for i in range(source_item.rowCount()):
                        tr = self.openIcmTraces.getTrace(
                            source_item.item(i, 0).text())
                        if self.aTraceGraph.plottedICMTrace.addICMTrace(tr):
                            addedToPlot = True

                else:
                    print("dropped from IDK?")

        if addedToPlot:
            self.update_plot()

    def initialiseAllVariables(self):

        self.aFDVGraph = GraphFDV(self.plotCanvasMain)
        self.aScattergraph = graphScatter(self.plotCanvasMain)
        self.aCumDepthGraph = graphCumulativeDepth(self.plotCanvasMain)
        self.aRainfallAnalysis = graphRainfallAnalysis(self.plotCanvasMain)
        self.aDataClassification = dataClassification(
            self.plotCanvasMain, app, self)
        self.aTraceGraph = graphICMTrace(self.plotCanvasMain)

        self.openFlowMonitors = None
        self.openRainGauges = None
        self.mappedFlowMonitors = None
        self.identifiedSurveyEvents = None
        self.summedFMs = None
        self.dummyFMs = None
        self.openIcmTraces = None
        self.importedICMData = None

        self.lastOpenDialogPath = ''

        self.refreshFlowMonitorListWidget()
        self.refreshRainGaugeListWidget()
        self.refreshICMTraceListWidget()
        self.updateEventTreeView()
        self.updateSummedFMTreeView()
        self.updateDummyFMTreeView()
        self.update_plot()
        self.schematicGraphicsView.createNewScene()

    def newProject(self):
        msg = QMessageBox(self)
        msg.setWindowIcon(self.myIcon)

        ret = msg.warning(
            self, 'Warning', 'Are you sure you want to start a new project?', QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            self.initialiseAllVariables()

    def loadProject(self):
        msg = QMessageBox(self)
        msg.setWindowIcon(self.myIcon)

        ret = msg.warning(
            self, 'Warning', 'Are you sure you want to load a new project?', QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            self.initialiseAllVariables()
        else:
            return

        fileSpec, filter = QtWidgets.QFileDialog.getOpenFileName(
            self, "Load Flowbot Project...", self.lastOpenDialogPath, 'Flowbot Project Files (*.fbp)')

        if len(fileSpec) == 0:
            return
        if self.openFlowMonitors is None:
            self.openFlowMonitors = flowMonitors()
        if self.openRainGauges is None:
            self.openRainGauges = rainGauges()
        if self.identifiedSurveyEvents is None:
            self.identifiedSurveyEvents = surveyEvents()
        if self.openIcmTraces is None:
            self.openIcmTraces = icmTraces()

        self.progressBar.setMinimum(0)
        self.progressBar.setValue(0)
        self.progressBar.show()

        lineCount = 0
        with open(fileSpec) as f:
            for lineCount, l in enumerate(f):
                pass
        self.progressBar.setMaximum(lineCount)

        iCount = -1

        with open(fileSpec, newline='') as f:
            fieldnames = ["dataID", "monitorName", "fdvFileSpec", "flowUnits", "depthUnits", "velocityUnits", "rainGaugeName", "fmTimestep",
                          "minFlow", "maxFlow", "totalVolume", "minDepth", "maxDepth", "minVelocity", "maxVelocity", "hasModelData",
                          "modelDataPipeRef", "modelDataRG", "modelDataPipeLength", "modelDataPipeShape", "modelDataPipeDia", "modelDataPipeHeight",
                          "modelDataPipeRoughness", "modelDataPipeUSInvert", "modelDataPipeDSInvert", "modelDataPipeSystemType"]
            reader = csv.DictReader(f, fieldnames=fieldnames)
            for row in reader:
                if row["dataID"] == "FM":
                    if os.path.exists(row["fdvFileSpec"]):
                        self.statusBar().showMessage(
                            'Reading: ' + row["fdvFileSpec"])
                        if not self.openFlowMonitors.alreadyOpen(row["fdvFileSpec"]):
                            self.openFlowMonitors.addFlowMonitor(
                                row["fdvFileSpec"])
                            if row["hasModelData"] == "True":
                                self.openFlowMonitors.dictFlowMonitors[row["monitorName"]
                                                                       ].modelDataPipeRef = row["modelDataPipeRef"]
                                self.openFlowMonitors.dictFlowMonitors[row["monitorName"]
                                                                       ].modelDataRG = row["modelDataRG"]
                                self.openFlowMonitors.dictFlowMonitors[row["monitorName"]
                                                                       ].modelDataPipeSystemType = row["modelDataPipeSystemType"]
                                self.openFlowMonitors.dictFlowMonitors[row["monitorName"]
                                                                       ].modelDataPipeShape = row["modelDataPipeShape"]
                                self.openFlowMonitors.dictFlowMonitors[row["monitorName"]].modelDataPipeDia = int(
                                    row["modelDataPipeDia"])
                                self.openFlowMonitors.dictFlowMonitors[row["monitorName"]].modelDataPipeHeight = int(
                                    row["modelDataPipeHeight"])
                                self.openFlowMonitors.dictFlowMonitors[row["monitorName"]].modelDataPipeUSInvert = float(
                                    row["modelDataPipeUSInvert"])
                                self.openFlowMonitors.dictFlowMonitors[row["monitorName"]].modelDataPipeDSInvert = float(
                                    row["modelDataPipeDSInvert"])
                                self.openFlowMonitors.dictFlowMonitors[row["monitorName"]].modelDataPipeLength = float(
                                    row["modelDataPipeLength"])
                                self.openFlowMonitors.dictFlowMonitors[row["monitorName"]].modelDataPipeRoughness = float(
                                    row["modelDataPipeRoughness"])
                                self.openFlowMonitors.dictFlowMonitors[row["monitorName"]
                                                                       ].hasModelData = True
                    iCount += 2
                    app.processEvents()
                    self.progressBar.setValue(iCount)
                else:
                    iCount += 1
                    self.progressBar.setValue(iCount)
                    break
                app.processEvents()
            fieldnames = ["dataID", "sumFMName", "fmNo", "fmName", "fmMult"]
            reader = csv.DictReader(f, fieldnames=fieldnames)
            aSFM = None
            for row in reader:
                if row["dataID"] == "SFM":
                    if int(row["fmNo"]) == 0:
                        if not aSFM is None:
                            if self.summedFMs is None:
                                self.summedFMs = {}
                            self.summedFMs[aSFM.sumFMName] = aSFM

                        aSFM = summedFlowMonitor()
                        aSFM.sumFMName = row["sumFMName"]

                    fm = self.openFlowMonitors.getFlowMonitor(row["fmName"])
                    aSFM.addFM(fm, float(row["fmMult"]))
                    iCount += 1
                    self.progressBar.setValue(iCount)
                else:
                    iCount += 1
                    self.progressBar.setValue(iCount)
                    break
                app.processEvents()
            if not aSFM is None:
                if self.summedFMs is None:
                    self.summedFMs = {}
                self.summedFMs[aSFM.sumFMName] = aSFM
            fieldnames = ["dataID", "gaugeName", "rFileSpec", "rgTimestep",
                          "minIntensity", "maxIntensity", "totalDepth", "returnPeriod"]
            reader = csv.DictReader(f, fieldnames=fieldnames)
            for row in reader:
                if row["dataID"] == "RG":
                    if os.path.exists(row["rFileSpec"]):
                        self.statusBar().showMessage(
                            'Reading: ' + row["rFileSpec"])
                        if not self.openRainGauges.alreadyOpen(row["rFileSpec"]):
                            self.openRainGauges.addRainGauge(row["rFileSpec"])
                    iCount += 1
                    self.progressBar.setValue(iCount)
                else:
                    iCount += 1
                    self.progressBar.setValue(iCount)
                    break
                app.processEvents()
            fieldnames = ["dataID", "eventName",
                          "eventType", "eventStart", "eventEnd"]
            reader = csv.DictReader(f, fieldnames=fieldnames)
            for row in reader:
                if row["dataID"] == "SE":
                    aSE = surveyEvent()
                    aSE.eventName = row["eventName"]
                    aSE.eventType = row["eventType"]
                    aSE.eventStart = dt.strptime(
                        row["eventStart"], "%d/%m/%Y %H:%M")
                    aSE.eventEnd = dt.strptime(
                        row["eventEnd"], "%d/%m/%Y %H:%M")
                    self.identifiedSurveyEvents.addSurvEvent(aSE)
                    iCount += 1
                    self.progressBar.setValue(iCount)
                else:
                    iCount += 1
                    self.progressBar.setValue(iCount)
                    break
                app.processEvents()
            fieldnames = ["dataID", "itemType",
                          "labelName", "systemType", "posX", "posY", "toPosX", "toPosY", "vertices"]
            reader = csv.DictReader(f, fieldnames=fieldnames)
            for row in reader:
                if row["dataID"] == "SGV":

                    if row["itemType"] == "FM":
                        fm = self.openFlowMonitors.getFlowMonitor(
                            row["labelName"])
                        if fm._schematicGraphicItem is None:
                            fm._schematicGraphicItem = self.schematicGraphicsView.addFlowMonitor(fm.monitorName, QPointF(
                                float(row["posX"]), float(row["posY"])), 0)

                    if row["itemType"] == "RG":
                        rg = self.openRainGauges.getRainGauge(row["labelName"])
                        if rg._schematicGraphicItem is None:
                            rg._schematicGraphicItem = self.schematicGraphicsView.addRaingauge(rg.gaugeName, QPointF(
                                float(row["posX"]), float(row["posY"])), 0)

                    if row["itemType"] == cstCSO:
                        self.schematicGraphicsView.addCSO(row["labelName"], QPointF(
                            float(row["posX"]), float(row["posY"])))
                    if row["itemType"] == cstWWPS:
                        self.schematicGraphicsView.addWwPS(row["labelName"], QPointF(
                            float(row["posX"]), float(row["posY"])), row["systemType"])
                    if row["itemType"] == cstWWTW:
                        self.schematicGraphicsView.addWwTW(row["labelName"], QPointF(
                            float(row["posX"]), float(row["posY"])))
                    if row["itemType"] == cstJUNCTION:
                        self.schematicGraphicsView.addJunction(row["labelName"], QPointF(
                            float(row["posX"]), float(row["posY"])), row["systemType"])
                    if row["itemType"] == cstOUTFALL:
                        self.schematicGraphicsView.addOutfall(row["labelName"], QPointF(
                            float(row["posX"]), float(row["posY"])), row["systemType"])
                    if row["itemType"] == cstCONNECTION:

                        self.schematicGraphicsView.showAllVisibleControlPoints()

                        fromPoint = self.schematicGraphicsView.controlPointAt(
                            QPointF(float(row["posX"]), float(row["posY"])))
                        toPoint = self.schematicGraphicsView.controlPointAt(
                            QPointF(float(row["toPosX"]), float(row["toPosY"])))

                        if not fromPoint is None and not toPoint is None:
                            aConnection = Connection(fromPoint, toPoint.pos())
                            aConnection.setDestination(toPoint.pos(), toPoint)
                            if len(row["vertices"]) > 2:
                                aConnection.intermediateVertices = self.getPointListFromString(
                                    row["vertices"])

                            self.schematicGraphicsView.scene().addItem(aConnection)

                            fromPoint.addLine(aConnection)
                            toPoint.addLine(aConnection)

                        self.schematicGraphicsView.clearAllVisibleControlPoints()

                    iCount += 1
                    self.progressBar.setValue(iCount)
                else:
                    iCount += 1
                    self.progressBar.setValue(iCount)
                    break
                app.processEvents()
            fieldnames = ["dataID", "traceID", "csvFileSpec"]
            reader = csv.DictReader(f, fieldnames=fieldnames)
            for row in reader:
                if row["dataID"] == "TR":

                    if not self.openIcmTraces.alreadyOpen(row["traceID"]):
                        tr = self.openIcmTraces.getTracesFromCSVFile(
                            row["csvFileSpec"], self.defaultSmoothing)

                    iCount += 1
                    self.progressBar.setValue(iCount)
                else:
                    iCount += 1
                    self.progressBar.setValue(iCount)
                    break
                app.processEvents()
            fieldnames = ["dataID", "traceID", "index", "isCritical", "isSurcharged", "peaksInitialized", "verifyForFlow", "verifyForDepth", "frac",
                          "peaks_prominance", "peaks_width", "peaks_distance", "verificationDepthComment", "verificationFlowComment", "verificationOverallComment"]
            reader = csv.DictReader(f, fieldnames=fieldnames)
            for row in reader:
                if row["dataID"] == "TL":

                    if self.openIcmTraces.alreadyOpen(row["traceID"]):
                        tr = self.openIcmTraces.getTrace(row["traceID"])
                        aLoc = tr.dictLocations[int(row["index"])]
                        aLoc.isCritical = row["isCritical"] == "True"
                        aLoc.isSurcharged = row["isSurcharged"] == "True"
                        aLoc.peaksInitialized = [
                            (x == "True") for x in row["peaksInitialized"].split(":")]
                        aLoc.verifyForFlow = row["verifyForFlow"] == "True"
                        aLoc.verifyForDepth = row["verifyForDepth"] == "True"
                        aLoc.frac = [float(x) for x in row["frac"].split(":")]
                        aLoc.peaks_prominance = [
                            float(x) for x in row["peaks_prominance"].split(":")]
                        aLoc.peaks_width = [
                            float(x) for x in row["peaks_width"].split(":")]
                        aLoc.peaks_distance = [
                            float(x) for x in row["peaks_distance"].split(":")]
                        aLoc.verificationDepthComment = row["verificationDepthComment"]
                        aLoc.verificationFlowComment = row["verificationFlowComment"]
                        aLoc.verificationOverallComment = row["verificationOverallComment"]
                        aLoc.updateAllPeaks()

                        tr.dictLocations[int(row["index"])] = aLoc

                    iCount += 1
                    self.progressBar.setValue(iCount)
                else:
                    iCount += 1
                    self.progressBar.setValue(iCount)
                    break
                app.processEvents()
        self.statusBar().clearMessage()
        self.progressBar.hide()
        self.refreshFlowMonitorListWidget()
        self.refreshRainGaugeListWidget()
        self.updateSummedFMTreeView()
        self.updateEventTreeView()
        self.refreshICMTraceListWidget()

        msg = QMessageBox(self)
        msg.setWindowIcon(self.myIcon)
        msg.information(self, 'Load Project',
                        'Project Loaded Sucessfully', QMessageBox.Ok)

    def getPointListFromString(self, myString):
        newList = []
        myList = myString[1:-2].split("), ")
        for item in myList:
            lhs, rhs = item.split("PyQt5.QtCore.QPointF(")
            lhs, rhs = rhs.split(", ")
            newList.append(QPointF(float(lhs), float(rhs)))
        return newList

    def saveProject(self):

        fmData = self.createFMDataTable()
        sfmData = self.createSFMDataTable()
        rgData = self.createRGDataTable()
        seData = self.createSEDataTable()
        sgvData = self.createSGVDataTable()
        itrData = self.createITRDataTable()
        itlData = self.createITLDataTable()

        if (len(fmData["dataID"]) + len(sfmData["dataID"]) + len(rgData["dataID"]) + len(seData["dataID"]) + len(sgvData["dataID"]) + len(itrData["dataID"]) + len(itlData["dataID"])) > 0:

            fileSpec, filter = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save Flowbot Project...", self.lastOpenDialogPath, 'fbp Files (*.fbp)')
            if len(fileSpec) == 0:
                return

            with open(fileSpec, 'w', newline='') as csvfile:

                fieldnames = ["dataID", "monitorName", "fdvFileSpec", "flowUnits", "depthUnits", "velocityUnits", "rainGaugeName", "fmTimestep",
                              "minFlow", "maxFlow", "totalVolume", "minDepth", "maxDepth", "minVelocity", "maxVelocity", "hasModelData",
                              "modelDataPipeRef", "modelDataRG", "modelDataPipeLength", "modelDataPipeShape", "modelDataPipeDia", "modelDataPipeHeight",
                              "modelDataPipeRoughness", "modelDataPipeUSInvert", "modelDataPipeDSInvert", "modelDataPipeSystemType"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                for i in range(len(fmData["monitorName"])):
                    writer.writerow({
                                    "dataID": fmData["dataID"][i],
                                    "monitorName": fmData["monitorName"][i],
                                    "fdvFileSpec": fmData["fdvFileSpec"][i],
                                    "flowUnits": fmData["flowUnits"][i],
                                    "depthUnits": fmData["depthUnits"][i],
                                    "velocityUnits": fmData["velocityUnits"][i],
                                    "rainGaugeName": fmData["rainGaugeName"][i],
                                    "fmTimestep": fmData["fmTimestep"][i],
                                    "minFlow": fmData["minFlow"][i],
                                    "maxFlow": fmData["maxFlow"][i],
                                    "totalVolume": fmData["totalVolume"][i],
                                    "minDepth": fmData["minDepth"][i],
                                    "maxDepth": fmData["maxDepth"][i],
                                    "minVelocity": fmData["minVelocity"][i],
                                    "maxVelocity": fmData["maxVelocity"][i],
                                    "hasModelData": fmData["hasModelData"][i],
                                    "modelDataPipeRef": fmData["modelDataPipeRef"][i],
                                    "modelDataRG": fmData["modelDataRG"][i],
                                    "modelDataPipeLength": fmData["modelDataPipeLength"][i],
                                    "modelDataPipeShape": fmData["modelDataPipeShape"][i],
                                    "modelDataPipeDia": fmData["modelDataPipeDia"][i],
                                    "modelDataPipeHeight": fmData["modelDataPipeHeight"][i],
                                    "modelDataPipeRoughness": fmData["modelDataPipeRoughness"][i],
                                    "modelDataPipeUSInvert": fmData["modelDataPipeUSInvert"][i],
                                    "modelDataPipeDSInvert": fmData["modelDataPipeDSInvert"][i],
                                    "modelDataPipeSystemType": fmData["modelDataPipeSystemType"][i]
                                    })

                writer.writerow({"dataID": "FM_END"})

                fieldnames = ["dataID", "sumFMName",
                              "fmNo", "fmName", "fmMult"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                for i in range(len(sfmData["sumFMName"])):
                    writer.writerow({
                                    "dataID": sfmData["dataID"][i],
                                    "sumFMName": sfmData["sumFMName"][i],
                                    "fmNo": sfmData["fmNo"][i],
                                    "fmName": sfmData["fmName"][i],
                                    "fmMult": sfmData["fmMult"][i]
                                    })

                writer.writerow({"dataID": "SFM_END"})

                fieldnames = ["dataID", "gaugeName", "rFileSpec", "rgTimestep",
                              "minIntensity", "maxIntensity", "totalDepth", "returnPeriod"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                for i in range(len(rgData["gaugeName"])):
                    writer.writerow({
                                    "dataID": rgData["dataID"][i],
                                    "gaugeName": rgData["gaugeName"][i],
                                    "rFileSpec": rgData["rFileSpec"][i],
                                    "rgTimestep": rgData["rgTimestep"][i],
                                    "minIntensity": rgData["minIntensity"][i],
                                    "maxIntensity": rgData["maxIntensity"][i],
                                    "totalDepth": rgData["totalDepth"][i],
                                    "returnPeriod": rgData["returnPeriod"][i]
                                    })

                writer.writerow({"dataID": "RG_END"})

                fieldnames = ["dataID", "eventName",
                              "eventType", "eventStart", "eventEnd"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                for i in range(len(seData["eventName"])):
                    writer.writerow({
                                    "dataID": seData["dataID"][i],
                                    "eventName": seData["eventName"][i],
                                    "eventType": seData["eventType"][i],
                                    "eventStart": seData["eventStart"][i].strftime("%d/%m/%Y %H:%M"),
                                    "eventEnd": seData["eventEnd"][i].strftime("%d/%m/%Y %H:%M")
                                    })

                writer.writerow({"dataID": "SE_END"})

                fieldnames = ["dataID", "itemType", "labelName",
                              "systemType", "posX", "posY", "toPosX", "toPosY", "vertices"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                for i in range(len(sgvData["itemType"])):
                    writer.writerow({
                                    "dataID": sgvData["dataID"][i],
                                    "itemType": sgvData["itemType"][i],
                                    "labelName": sgvData["labelName"][i],
                                    "systemType": sgvData["systemType"][i],
                                    "posX": sgvData["posX"][i],
                                    "posY": sgvData["posY"][i],
                                    "toPosX": sgvData["toPosX"][i],
                                    "toPosY": sgvData["toPosY"][i],
                                    "vertices": sgvData["vertices"][i]
                                    })

                writer.writerow({"dataID": "SGV_END"})

                fieldnames = ["dataID", "traceID", "csvFileSpec"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                for i in range(len(itrData["traceID"])):
                    writer.writerow({
                                    "dataID": itrData["dataID"][i],
                                    "traceID": itrData["traceID"][i],
                                    "csvFileSpec": itrData["csvFileSpec"][i]
                                    })

                writer.writerow({"dataID": "TR_END"})

                fieldnames = ["dataID", "traceID", "index", "isCritical", "isSurcharged", "peaksInitialized", "verifyForFlow", "verifyForDepth", "frac",
                              "peaks_prominance", "peaks_width", "peaks_distance", "verificationDepthComment", "verificationFlowComment", "verificationOverallComment"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                for i in range(len(itlData["traceID"])):
                    writer.writerow({
                                    "dataID": itlData["dataID"][i],
                                    "traceID": itlData["traceID"][i],
                                    "index": itlData["index"][i],
                                    "isCritical": itlData["isCritical"][i],
                                    "isSurcharged": itlData["isSurcharged"][i],
                                    "peaksInitialized": itlData["peaksInitialized"][i],
                                    "verifyForFlow": itlData["verifyForFlow"][i],
                                    "verifyForDepth": itlData["verifyForDepth"][i],
                                    "frac": itlData["frac"][i],
                                    "peaks_prominance": itlData["peaks_prominance"][i],
                                    "peaks_width": itlData["peaks_width"][i],
                                    "peaks_distance": itlData["peaks_distance"][i],
                                    "verificationDepthComment": itlData["verificationDepthComment"][i],
                                    "verificationFlowComment": itlData["verificationFlowComment"][i],
                                    "verificationOverallComment": itlData["verificationOverallComment"][i]
                                    })

                writer.writerow({"dataID": "TL_END"})

            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.information(self, 'Save Project',
                            'Project Saved Sucessfully', QMessageBox.Ok)
        else:

            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.information(self, 'Save Project',
                            'No Data to Save', QMessageBox.Ok)

    def createSGVDataTable(self):

        sgvData = {
            "dataID": [],
            "itemType": [],
            "labelName": [],
            "systemType": [],
            "posX": [],
            "posY": [],
            "toPosX": [],
            "toPosY": [],
            "vertices": []
        }
        if len(self.schematicGraphicsView.scene().items()) > 0:
            sgvConnections = []
            for item in self.schematicGraphicsView.scene().items():
                if isinstance(item, fmGraphicsItem):
                    sgvData["dataID"].append("SGV")
                    sgvData["itemType"].append("FM")
                    sgvData["labelName"].append(item._text)
                    sgvData["systemType"].append("")
                    sgvData["posX"].append(item.pos().x())
                    sgvData["posY"].append(item.pos().y())
                    sgvData["toPosX"].append(0)
                    sgvData["toPosY"].append(0)
                    sgvData["vertices"].append("")
                if isinstance(item, rgGraphicsItem):
                    sgvData["dataID"].append("SGV")
                    sgvData["itemType"].append("RG")
                    sgvData["labelName"].append(item._text)
                    sgvData["systemType"].append("")
                    sgvData["posX"].append(item.pos().x())
                    sgvData["posY"].append(item.pos().y())
                    sgvData["toPosX"].append(0)
                    sgvData["toPosY"].append(0)
                    sgvData["vertices"].append("")
                if isinstance(item, csoGraphicsItem):
                    sgvData["dataID"].append("SGV")
                    sgvData["itemType"].append(cstCSO)
                    sgvData["labelName"].append(item._text)
                    sgvData["systemType"].append("")
                    sgvData["posX"].append(item.pos().x())
                    sgvData["posY"].append(item.pos().y())
                    sgvData["toPosX"].append(0)
                    sgvData["toPosY"].append(0)
                    sgvData["vertices"].append("")
                if isinstance(item, wwpsGraphicsItem):
                    sgvData["dataID"].append("SGV")
                    sgvData["itemType"].append(cstWWPS)
                    sgvData["labelName"].append(item._text)
                    sgvData["systemType"].append(item._systemType)
                    sgvData["posX"].append(item.pos().x())
                    sgvData["posY"].append(item.pos().y())
                    sgvData["toPosX"].append(0)
                    sgvData["toPosY"].append(0)
                    sgvData["vertices"].append("")
                if isinstance(item, wwtwGraphicsItem):
                    sgvData["dataID"].append("SGV")
                    sgvData["itemType"].append(cstWWTW)
                    sgvData["labelName"].append(item._text)
                    sgvData["systemType"].append("")
                    sgvData["posX"].append(item.pos().x())
                    sgvData["posY"].append(item.pos().y())
                    sgvData["toPosX"].append(0)
                    sgvData["toPosY"].append(0)
                    sgvData["vertices"].append("")
                if isinstance(item, juncGraphicsItem):
                    sgvData["dataID"].append("SGV")
                    sgvData["itemType"].append(cstJUNCTION)
                    sgvData["labelName"].append("")
                    sgvData["systemType"].append(item._systemType)
                    sgvData["posX"].append(item.pos().x())
                    sgvData["posY"].append(item.pos().y())
                    sgvData["toPosX"].append(0)
                    sgvData["toPosY"].append(0)
                    sgvData["vertices"].append("")
                if isinstance(item, outfallGraphicsItem):
                    sgvData["dataID"].append("SGV")
                    sgvData["itemType"].append(cstOUTFALL)
                    sgvData["labelName"].append("")
                    sgvData["systemType"].append(item._systemType)
                    sgvData["posX"].append(item.pos().x())
                    sgvData["posY"].append(item.pos().y())
                    sgvData["toPosX"].append(0)
                    sgvData["toPosY"].append(0)
                    sgvData["vertices"].append("")
                if isinstance(item, Connection):
                    sgvConnections.append(item)
                else:
                    pass
            for item in sgvConnections:
                sgvData["dataID"].append("SGV")
                sgvData["itemType"].append(cstCONNECTION)
                sgvData["labelName"].append("")
                sgvData["systemType"].append(item._systemType)
                sgvData["posX"].append(item._sourcePoint.x())
                sgvData["posY"].append(item._sourcePoint.y())
                sgvData["toPosX"].append(item._destinationPoint.x())
                sgvData["toPosY"].append(item._destinationPoint.y())
                sgvData["vertices"].append(item.intermediateVertices)

        return sgvData

    def createFMDataTable(self):

        fmData = {
            "dataID": [],
            "monitorName": [],
            "fdvFileSpec": [],
            "flowUnits": [],
            "depthUnits": [],
            "velocityUnits": [],
            "rainGaugeName": [],
            "fmTimestep": [],
            "minFlow": [],
            "maxFlow": [],
            "totalVolume": [],
            "minDepth": [],
            "maxDepth": [],
            "minVelocity": [],
            "maxVelocity": [],
            "hasModelData": [],
            "modelDataPipeRef": [],
            "modelDataRG": [],
            "modelDataPipeLength": [],
            "modelDataPipeShape": [],
            "modelDataPipeDia": [],
            "modelDataPipeHeight": [],
            "modelDataPipeRoughness": [],
            "modelDataPipeUSInvert": [],
            "modelDataPipeDSInvert": [],
            "modelDataPipeSystemType": []
        }

        if not self.openFlowMonitors is None:
            if len(self.openFlowMonitors.dictFlowMonitors) > 0:
                for fm in self.openFlowMonitors.dictFlowMonitors.values():
                    fmData["dataID"].append("FM")
                    fmData["monitorName"].append(fm.monitorName)
                    fmData["fdvFileSpec"].append(fm.fdvFileSpec)
                    fmData["flowUnits"].append(fm.flowUnits)
                    fmData["depthUnits"].append(fm.depthUnits)
                    fmData["velocityUnits"].append(fm.velocityUnits)
                    fmData["rainGaugeName"].append(fm.rainGaugeName)
                    fmData["fmTimestep"].append(fm.fmTimestep)
                    fmData["minFlow"].append(fm.minFlow)
                    fmData["maxFlow"].append(fm.maxFlow)
                    fmData["totalVolume"].append(fm.totalVolume)
                    fmData["minDepth"].append(fm.minDepth)
                    fmData["maxDepth"].append(fm.maxDepth)
                    fmData["minVelocity"].append(fm.minVelocity)
                    fmData["maxVelocity"].append(fm.maxVelocity)
                    fmData["hasModelData"].append(fm.hasModelData)
                    fmData["modelDataPipeRef"].append(fm.modelDataPipeRef)
                    fmData["modelDataRG"].append(fm.modelDataRG)
                    fmData["modelDataPipeLength"].append(
                        fm.modelDataPipeLength)
                    fmData["modelDataPipeShape"].append(fm.modelDataPipeShape)
                    fmData["modelDataPipeDia"].append(fm.modelDataPipeDia)
                    fmData["modelDataPipeHeight"].append(
                        fm.modelDataPipeHeight)
                    fmData["modelDataPipeRoughness"].append(
                        fm.modelDataPipeRoughness)
                    fmData["modelDataPipeUSInvert"].append(
                        fm.modelDataPipeUSInvert)
                    fmData["modelDataPipeDSInvert"].append(
                        fm.modelDataPipeDSInvert)
                    fmData["modelDataPipeSystemType"].append(
                        fm.modelDataPipeSystemType)

        return fmData

    def createSFMDataTable(self):

        sfmData = {
            "dataID": [],
            "sumFMName": [],
            "fmNo": [],
            "fmName": [],
            "fmMult": []
        }

        if not self.summedFMs is None:
            if len(self.summedFMs) > 0:
                for sfm in self.summedFMs.values():
                    i = 0
                    for fm, mult in sfm.fmCollection.values():
                        sfmData["dataID"].append("SFM")
                        sfmData["sumFMName"].append(sfm.sumFMName)
                        sfmData["fmNo"].append(i)
                        sfmData["fmName"].append(fm.monitorName)
                        sfmData["fmMult"].append(mult)
                        i += 1

        return sfmData

    def createRGDataTable(self):

        rgData = {
            "dataID": [],
            "gaugeName": [],
            "rFileSpec": [],
            "rgTimestep": [],
            "minIntensity": [],
            "maxIntensity": [],
            "totalDepth": [],
            "returnPeriod": []
        }

        if not self.openRainGauges is None:
            if len(self.openRainGauges.dictRainGauges) > 0:
                for rg in self.openRainGauges.dictRainGauges.values():
                    rgData["dataID"].append("RG")
                    rgData["gaugeName"].append(rg.gaugeName)
                    rgData["rFileSpec"].append(rg.rFileSpec)
                    rgData["rgTimestep"].append(rg.rgTimestep)
                    rgData["minIntensity"].append(rg.minIntensity)
                    rgData["maxIntensity"].append(rg.maxIntensity)
                    rgData["totalDepth"].append(rg.totalDepth)
                    rgData["returnPeriod"].append(rg.returnPeriod)

        return rgData

    def createSEDataTable(self):

        eventData = {
            "dataID": [],
            "eventName": [],
            "eventType": [],
            "eventStart": [],
            "eventEnd": []
        }

        if not self.identifiedSurveyEvents is None:
            if len(self.identifiedSurveyEvents.survEvents) > 0:
                for se in self.identifiedSurveyEvents.survEvents.values():
                    eventData["dataID"].append("SE")
                    eventData["eventName"].append(se.eventName)
                    eventData["eventType"].append(se.eventType)
                    eventData["eventStart"].append(se.eventStart)
                    eventData["eventEnd"].append(se.eventEnd)

        return eventData

    def createITRDataTable(self):

        itrData = {
            "dataID": [],
            "traceID": [],
            "csvFileSpec": [],
        }

        if not self.openIcmTraces is None:
            if len(self.openIcmTraces.dictIcmTraces) > 0:
                for tr in self.openIcmTraces.dictIcmTraces.values():
                    itrData["dataID"].append("TR")
                    itrData["traceID"].append(tr.traceID)
                    itrData["csvFileSpec"].append(tr.csvFileSpec)

        return itrData

    def createITLDataTable(self):

        itlData = {
            "dataID": [],
            "traceID": [],
            "index": [],
            "isCritical": [],
            "isSurcharged": [],
            "peaksInitialized": [],
            "verifyForFlow": [],
            "verifyForDepth": [],
            "frac": [],
            "peaks_prominance": [],
            "peaks_width": [],
            "peaks_distance": [],
            "verificationDepthComment": [],
            "verificationFlowComment": [],
            "verificationOverallComment": []

        }

        if not self.openIcmTraces is None:
            if len(self.openIcmTraces.dictIcmTraces) > 0:
                for tr in self.openIcmTraces.dictIcmTraces.values():
                    for aLoc in tr.dictLocations.values():
                        itlData["dataID"].append("TL")
                        itlData["traceID"].append(tr.traceID)
                        itlData["index"].append(aLoc.index)
                        itlData["isCritical"].append(str(aLoc.isCritical))
                        itlData["isSurcharged"].append(str(aLoc.isSurcharged))
                        itlData["verifyForFlow"].append(
                            str(aLoc.verifyForFlow))
                        itlData["verifyForDepth"].append(
                            str(aLoc.verifyForDepth))
                        itlData["peaksInitialized"].append(
                            ":".join([str(i) for i in aLoc.peaksInitialized]))
                        itlData["frac"].append(
                            ":".join([str(i) for i in aLoc.frac]))
                        itlData["peaks_prominance"].append(
                            ":".join([str(i) for i in aLoc.peaks_prominance]))
                        itlData["peaks_width"].append(
                            ":".join([str(i) for i in aLoc.peaks_width]))
                        itlData["peaks_distance"].append(
                            ":".join([str(i) for i in aLoc.peaks_distance]))
                        itlData["verificationDepthComment"].append(
                            aLoc.verificationDepthComment)
                        itlData["verificationFlowComment"].append(
                            aLoc.verificationFlowComment)
                        itlData["verificationOverallComment"].append(
                            aLoc.verificationOverallComment)

        return itlData

    def closeApplication(self):
        msg = QMessageBox(self)
        msg.setWindowIcon(self.myIcon)
        ret = msg.warning(
            self, 'Warning', 'Are you sure you want to exit?', QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            sys.exit()

    def open_FM_files(self):

        path, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, 'Please locate the flow survey files', self.lastOpenDialogPath, 'Flow Survey Files (*.FDV *.std *.txt)')
        if not path:
            return

        if self.openFlowMonitors is None:
            self.openFlowMonitors = flowMonitors()

        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(len(path))
        self.progressBar.setValue(0)
        self.progressBar.show()

        for i in range(len(path)):
            self.progressBar.setValue(i)
            fmFileSpec = path[i]
            self.statusBar().showMessage('Reading: ' + fmFileSpec)
            if not self.openFlowMonitors.alreadyOpen(fmFileSpec):
                self.openFlowMonitors.addFlowMonitor(fmFileSpec)
            app.processEvents()
        self.statusBar().clearMessage()
        self.progressBar.hide()
        self.refreshFlowMonitorListWidget()
        self.lastOpenDialogPath = os.path.dirname(path[0])

    def open_RG_files(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, 'Please locate the rainfall files', self.lastOpenDialogPath, 'Rainfall Survey Files (*.R *.std *.txt)')
        if not path:
            return

        if self.openRainGauges is None:
            self.openRainGauges = rainGauges()

        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(len(path))
        self.progressBar.setValue(0)
        self.progressBar.show()

        for i in range(len(path)):
            self.progressBar.setValue(i)
            rgFileSpec = path[i]
            self.statusBar().showMessage('Reading: ' + rgFileSpec)
            if not self.openRainGauges.alreadyOpen(rgFileSpec):
                self.openRainGauges.addRainGauge(rgFileSpec)
            app.processEvents()
        self.statusBar().clearMessage()
        self.progressBar.hide()
        self.refreshRainGaugeListWidget()
        self.lastOpenDialogPath = os.path.dirname(path[0])

    def remove_all_FM_files(self):

        if not self.aFDVGraph is None:
            self.aFDVGraph.plotted_fms = plottedFlowMonitors()
        self.aScattergraph = graphScatter(self.plotCanvasMain)
        if not self.aDataClassification is None:
            self.aDataClassification.classifiedFMs = classifiedFlowMonitors()
        self.openFlowMonitors = None
        self.refreshFlowMonitorListWidget()
        self.summedFMs = None
        self.updateSummedFMTreeView()
        self.update_plot()

    def remove_all_RG_files(self):

        if not self.aFDVGraph is None:
            self.aFDVGraph.plotted_rgs = plottedRainGauges()
        if not self.aCumDepthGraph is None:
            self.aCumDepthGraph.plotted_rgs = plottedRainGauges()
        if not self.aRainfallAnalysis is None:
            self.aRainfallAnalysis.plotted_rgs = plottedRainGauges()
        self.update_plot()
        self.openRainGauges = None
        self.refreshRainGaugeListWidget()

    def editRainfallAnalysisParams(self):

        editRainfallAnalysisParamsDialog = flowbot_dialog_event_analysis_params(
            self.aRainfallAnalysis, self)
        editRainfallAnalysisParamsDialog.setWindowTitle(
            'Edit Rainfall Analysis Parameters')
        editRainfallAnalysisParamsDialog.show()
        ret = editRainfallAnalysisParamsDialog.exec_()
        if ret == QDialog.Accepted:
            self.aRainfallAnalysis.analysisNeedsRefreshed = True
            self.update_plot()

    def editDataClassificationParams(self):

        if not self.aDataClassification is None:
            editDataClassificationParamsDialog = flowbot_dialog_data_classification(
                self.aDataClassification, self)
            editDataClassificationParamsDialog.setWindowTitle(
                'Edit Data Classification Parameters')
            editDataClassificationParamsDialog.show()
            ret = editDataClassificationParamsDialog.exec_()
            if ret == QDialog.Accepted:
                self.aDataClassification.classificationNeedsRefreshed = True
                self.update_plot()

    def removeTreeItem(self):

        if self.tbxGraphs.currentWidget().objectName() == "pageFDV":
            if not self.aFDVGraph is None:
                item = self.trw_PlottedMonitors.selectedItems()[0]
                if item.parent().text(0) == "Flow Monitors":
                    self.aFDVGraph.plotted_fms.removeFM(item.text(0))
                elif item.parent().text(0) == "Rain Gauges":
                    self.aFDVGraph.plotted_rgs.removeRG(item.text(0))
                elif item.parent().text(0) == "Event":
                    self.aFDVGraph.set_plot_event(None)

        elif self.tbxGraphs.currentWidget().objectName() == "pageScattergraphs":
            if not self.aScattergraph is None:
                item = self.trw_Scattergraph.selectedItems()[0]
                if item.parent().text(0) == "Flow Monitor":
                    self.aScattergraph.setPlotFM(None)
                elif item.parent().text(0) == "Events":
                    self.aScattergraph.plottedEvents.removeSurveyEvent(
                        item.text(0))

        if self.tbxGraphs.currentWidget().objectName() == "pageRainfallCumDepth":
            if not self.aCumDepthGraph is None:
                item = self.trw_CumDepth.selectedItems()[0]
                if item.parent().text(0) == "Rain Gauges":
                    self.aCumDepthGraph.plotted_rgs.removeRG(item.text(0))
                elif item.parent().text(0) == "Event":
                    self.aCumDepthGraph.set_plot_event(None)

        if self.tbxGraphs.currentWidget().objectName() == "pageRainfallAnalysis":
            if not self.aRainfallAnalysis is None:
                item = self.trw_RainfallAnalysis.selectedItems()[0]
                if item.parent().text(0) == "Rain Gauges":
                    self.aRainfallAnalysis.analysisNeedsRefreshed = True
                    self.aRainfallAnalysis.plotted_rgs.removeRG(item.text(0))

        if self.tbxGraphs.currentWidget().objectName() == "pageDataClassification":
            if not self.aDataClassification is None:
                item = self.trw_DataClassification.selectedItems()[0]
                if item.parent().text(0) == "Flow Monitors":
                    self.aDataClassification.classifiedFMs.removeFM(
                        item.text(0))
                    self.aDataClassification.classificationNeedsRefreshed = True
                elif item.parent().text(0) == "Events":
                    self.aDataClassification.plottedEvents.removeSurveyEvent(
                        item.text(0))

        self.update_plot()

    def removeTreeItems(self):

        if self.tbxGraphs.currentWidget().objectName() == "pageFDV":
            if not self.aFDVGraph is None:
                item = self.trw_PlottedMonitors.currentItem()
                if item.text(0) == "Flow Monitors":
                    self.aFDVGraph.plotted_fms = plottedFlowMonitors()
                elif item.text(0) == "Rain Gauges":
                    self.aFDVGraph.plotted_rgs = plottedRainGauges()
                elif item.text(0) == "Event":
                    self.aFDVGraph.set_plot_event(None)

        if self.tbxGraphs.currentWidget().objectName() == "pageScattergraphs":
            if not self.aScattergraph is None:
                item = self.trw_Scattergraph.currentItem()
                if item.text(0) == "Flow Monitor":
                    self.aScattergraph.setPlotFM(None)
                elif item.text(0) == "Events":
                    self.aScattergraph.plottedEvents = plottedSurveyEvents()

        if self.tbxGraphs.currentWidget().objectName() == "pageRainfallCumDepth":
            if not self.aCumDepthGraph is None:
                item = self.trw_CumDepth.currentItem()
                if item.text(0) == "Rain Gauges":
                    self.aCumDepthGraph.plotted_rgs = plottedRainGauges()
                elif item.text(0) == "Event":
                    self.aCumDepthGraph.set_plot_event(None)

        if self.tbxGraphs.currentWidget().objectName() == "pageRainfallAnalysis":
            if not self.aRainfallAnalysis is None:
                item = self.trw_RainfallAnalysis.currentItem()
                if item.text(0) == "Rain Gauges":
                    self.aRainfallAnalysis.plotted_rgs = plottedRainGauges()
                    self.aRainfallAnalysis.analysisNeedsRefreshed = True

        if self.tbxGraphs.currentWidget().objectName() == "pageDataClassification":
            if not self.aDataClassification is None:
                item = self.trw_DataClassification.currentItem()
                if item.text(0) == "Flow Monitors":
                    self.aDataClassification.classifiedFMs = classifiedFlowMonitors()
                    self.aDataClassification.classificationNeedsRefreshed = True
                elif item.text(0) == "Events":
                    self.aDataClassification.plottedEvents = plottedSurveyEvents()

        self.update_plot()

    def openFlowMonitorsListContextMenu(self, position):

        if not self.lst_FlowMonitors.currentItem() is None:
            rightMenu = QMenu(self.lst_FlowMonitors)
            rightMenu.addAction(
                QAction('Remove Monitor', self, triggered=self.remove_FM_file))
            rightMenu.addAction(
                QAction('Model Data', self, triggered=self.editModelData))
            if not self.mappedFlowMonitors is None:
                if self.mappedFlowMonitors.isMapped(self.lst_FlowMonitors.currentItem().text()):
                    rightMenu.addSeparator()
                    rightMenu.addAction(QAction('Zoom to', self, triggered=self.zoomTo))
                    rightMenu.addAction(QAction('Clear Location', self, triggered=self.clearLocation))
            rightMenu.exec_(QCursor.pos())

    def zoomTo(self):
        
        self.flowbotWebMap.zoomTo(self.mappedFlowMonitors.locationByFMName(self.lst_FlowMonitors.currentItem().text()), 18)
        self.updateMapView()

    def clearLocation(self):
        pass


    def openRainGaugeListContextMenu(self, position):

        if not self.lst_RainGauges.currentItem() is None:
            rightMenu = QMenu(self.lst_RainGauges)
            rightMenu.addAction(
                QAction('Remove Gauge', self, triggered=self.remove_RG_file))
            rightMenu.exec_(QCursor.pos())

    def openPlotTreeViewContextMenu(self, position):

        treeWidget = None

        if self.tbxGraphs.currentWidget().objectName() == "pageFDV":
            treeWidget = self.trw_PlottedMonitors
        if self.tbxGraphs.currentWidget().objectName() == "pageScattergraphs":
            treeWidget = self.trw_Scattergraph
        if self.tbxGraphs.currentWidget().objectName() == "pageRainfallCumDepth":
            treeWidget = self.trw_CumDepth
        if self.tbxGraphs.currentWidget().objectName() == "pageRainfallAnalysis":
            treeWidget = self.trw_RainfallAnalysis
        if self.tbxGraphs.currentWidget().objectName() == "pageDataClassification":
            treeWidget = self.trw_DataClassification

        if not treeWidget is None:
            level = self.getTreeViewLevel(treeWidget)
            menu = QMenu()
            if level == 0:
                if not treeWidget.itemAt(position) is None:
                    if treeWidget.objectName() == "trw_RainfallAnalysis":
                        if not treeWidget.itemAt(position).text(0) == "Event Parameters":
                            if treeWidget.itemAt(position).childCount() > 0:
                                remCallback = QtWidgets.QAction(
                                    "Remove All", menu)
                                remCallback.triggered.connect(
                                    self.removeTreeItems)
                                menu.addAction(remCallback)
                    elif treeWidget.objectName() == "trw_DataClassification":
                        if not treeWidget.itemAt(position).text(0) == "Parameters":
                            if treeWidget.itemAt(position).childCount() > 0:
                                remCallback = QtWidgets.QAction(
                                    "Remove All", menu)
                                remCallback.triggered.connect(
                                    self.removeTreeItems)
                                menu.addAction(remCallback)
                    else:
                        if treeWidget.itemAt(position).childCount() > 0:
                            remCallback = QtWidgets.QAction("Remove All", menu)
                            remCallback.triggered.connect(self.removeTreeItems)
                            menu.addAction(remCallback)
                # return
            elif level == 1:
                if treeWidget.objectName() == "trw_RainfallAnalysis":
                    if treeWidget.itemFromIndex(treeWidget.selectedIndexes()[0].parent()).text(0) == "Event Parameters":
                        remCallback = QtWidgets.QAction(
                            "Edit Parameters", menu)
                        remCallback.triggered.connect(
                            self.editRainfallAnalysisParams)
                        menu.addAction(remCallback)
                    else:
                        remCallback = QtWidgets.QAction("Remove", menu)
                        remCallback.triggered.connect(self.removeTreeItem)
                        menu.addAction(remCallback)
                elif treeWidget.objectName() == "trw_DataClassification":
                    if treeWidget.itemFromIndex(treeWidget.selectedIndexes()[0].parent()).text(0) == "Parameters":
                        remCallback = QtWidgets.QAction(
                            "Edit Parameters", menu)
                        remCallback.triggered.connect(
                            self.editDataClassificationParams)
                        menu.addAction(remCallback)
                    else:
                        remCallback = QtWidgets.QAction("Remove", menu)
                        remCallback.triggered.connect(self.removeTreeItem)
                        menu.addAction(remCallback)
                else:
                    remCallback = QtWidgets.QAction("Remove", menu)
                    remCallback.triggered.connect(self.removeTreeItem)
                    menu.addAction(remCallback)

            if not len(menu.actions()) == 0:
                menu.exec_(treeWidget.viewport().mapToGlobal(position))

    def openSummedFMsTreeViewContextMenu(self, position):

        level = self.getTreeViewLevel(self.trwSummedFMs)
        menu = QMenu()
        if level == 0:
            remCallback = QtWidgets.QAction("Add Summed FM", menu)
            remCallback.triggered.connect(self.summedFM_Add)
            menu.addAction(remCallback)

            if (not self.summedFMs is None) and (len(self.summedFMs) > 0):

                remCallback = QtWidgets.QAction("Edit Multipliers", menu)
                remCallback.triggered.connect(self.summedFM_UpdateMultiplier)
                menu.addAction(remCallback)

                remCallback = QtWidgets.QAction("Rename Summed FM", menu)
                remCallback.triggered.connect(self.summedFM_Rename)
                menu.addAction(remCallback)

                remCallback = QtWidgets.QAction("Remove Summed FM", menu)
                remCallback.triggered.connect(self.summedFM_Delete)
                menu.addAction(remCallback)

        elif level == 1:
            remCallback = QtWidgets.QAction("Remove FM", menu)
            remCallback.triggered.connect(self.summedFM_RemoveFM)
            menu.addAction(remCallback)

        menu.exec_(self.trwSummedFMs.viewport().mapToGlobal(position))

    def openDummyFMsTreeViewContextMenu(self, position):

        level = self.getTreeViewLevel(self.trwDummyFMs)
        menu = QMenu()
        if level == 0:
            if self.trwDummyFMs.itemAt(position).childCount() > 0:
                remCallback = QtWidgets.QAction("Remove All", menu)
                remCallback.triggered.connect(self.dummyFM_DeleteAll)
                menu.addAction(remCallback)

                remCallback = QtWidgets.QAction("Add Model Data", menu)
                remCallback.triggered.connect(self.dummyFM_AddModelData)
                menu.addAction(remCallback)

        elif level == 1:
            if (not self.dummyFMs is None) and (len(self.dummyFMs) > 0):

                remCallback = QtWidgets.QAction("Remove Dummy FM", menu)
                remCallback.triggered.connect(self.dummyFM_Delete)
                menu.addAction(remCallback)

        menu.exec_(self.trwDummyFMs.viewport().mapToGlobal(position))

    def openEventTreeViewContextMenu(self, position):

        level = self.getTreeViewLevel(self.trwEvents)
        menu = QMenu()
        if level == 0:
            return
        elif level == 1:
            remCallback = QtWidgets.QAction("Edit Event", menu)
            remCallback.triggered.connect(self.editSurveyEvent)
            menu.addAction(remCallback)

            remCallback = QtWidgets.QAction("Remove", menu)
            remCallback.triggered.connect(self.removeSurveyEvent)
            menu.addAction(remCallback)

        menu.exec_(self.trwEvents.viewport().mapToGlobal(position))

    def openICMTraceListContextMenu(self, position):

        if not self.lst_ICMTraces.currentItem() is None:
            rightMenu = QMenu(self.lst_ICMTraces)
            rightMenu.addAction(
                QAction('Remove ICM Trace File', self, triggered=self.remove_ICMTrace_file))
            rightMenu.exec_(QCursor.pos())

    def remove_ICMTrace_file(self):
        self.removeICMTrace()
        self.openIcmTraces.removeTrace(self.lst_ICMTraces.currentItem().text())
        self.refreshICMTraceListWidget()

    def setDefaultSmoothing(self, forObserved: bool = True):
        if forObserved:
            newValue, ok = QInputDialog.getDouble(
                self, 'Set Default Smoothing:', 'Observed:', self.defaultSmoothing['Observed'], 0, 1, 3)
            if ok:
                self.defaultSmoothing['Observed'] = newValue

                for tr in self.aTraceGraph.plottedICMTrace.plotTrace.dictLocations.values():
                    if not tr.peaksInitialized[tr.iObsFlow]:
                        tr.frac[tr.iObsFlow] = self.defaultSmoothing['Observed']
                    if not tr.peaksInitialized[tr.iObsDepth]:
                        tr.frac[tr.iObsDepth] = self.defaultSmoothing['Observed']
        else:
            newValue, ok = QInputDialog.getDouble(
                self, 'Set Default Smoothing:', 'Predicted:', self.defaultSmoothing['Predicted'], 0, 1, 3)
            if ok:
                self.defaultSmoothing['Predicted'] = newValue

                for tr in self.aTraceGraph.plottedICMTrace.plotTrace.dictLocations.values():
                    if not tr.peaksInitialized[tr.iPredFlow]:
                        tr.frac[tr.iPredFlow] = self.defaultSmoothing['Predicted']
                    if not tr.peaksInitialized[tr.iPredDepth]:
                        tr.frac[tr.iPredDepth] = self.defaultSmoothing['Predicted']

    def openPlottedTraceTreeViewContextMenu(self, position):

        level = self.getTreeViewLevel(self.trw_PlottedICMTraces)
        menu = QMenu()
        if level == 0:
            remCallback = QtWidgets.QAction("Remove", menu)
            remCallback.triggered.connect(self.removeICMTrace)
            menu.addAction(remCallback)

            menu.addSeparator()

            subMenu = QMenu(menu)
            subMenu.setTitle('Verify All')

            remCallback = QtWidgets.QAction("For Depth and Flow", subMenu)
            remCallback.setCheckable(True)
            remCallback.setChecked(
                self.aTraceGraph.plottedICMTrace.plotTrace.allVerifiedForDepth() and self.aTraceGraph.plottedICMTrace.plotTrace.allVerifiedForFlow())
            remCallback.triggered.connect(lambda: self.toggleAllVerification())
            subMenu.addAction(remCallback)

            remCallback = QtWidgets.QAction("For Depth", subMenu)
            remCallback.setCheckable(True)
            remCallback.setChecked(
                self.aTraceGraph.plottedICMTrace.plotTrace.allVerifiedForDepth())
            remCallback.triggered.connect(self.toggleAllDepthVerification)
            subMenu.addAction(remCallback)

            remCallback = QtWidgets.QAction("For Flow", subMenu)
            remCallback.setCheckable(True)
            remCallback.setChecked(
                self.aTraceGraph.plottedICMTrace.plotTrace.allVerifiedForFlow())
            remCallback.triggered.connect(self.toggleAllFlowVerification)
            subMenu.addAction(remCallback)

            menu.addMenu(subMenu)

            subMenu = QMenu(menu)
            subMenu.setTitle('Set Default Smoothing')

            remCallback = QtWidgets.QAction("Observed", subMenu)
            remCallback.triggered.connect(
                lambda: self.setDefaultSmoothing(True))
            subMenu.addAction(remCallback)

            remCallback = QtWidgets.QAction("Predicted", subMenu)
            remCallback.triggered.connect(
                lambda: self.setDefaultSmoothing(False))
            subMenu.addAction(remCallback)
            menu.addMenu(subMenu)
            menu.addSeparator()

            remCallback = QtWidgets.QAction("Convert to Dummy Monitors", menu)
            remCallback.triggered.connect(self.convertToDummyMonitors)
            menu.addAction(remCallback)

        elif level == 1:

            myIndex = self.trw_PlottedICMTraces.indexFromItem(
                self.trw_PlottedICMTraces.itemAt(position)).row()
            aLoc = self.aTraceGraph.plottedICMTrace.plotTrace.dictLocations[myIndex]

            item = self.trw_PlottedICMTraces.itemAt(position)

            if item.isSelected() and len(self.trw_PlottedICMTraces.selectedItems()) > 1:
                remCallback = QtWidgets.QAction(
                    "Verify Selected for Depth and Flow", menu)
                remCallback.triggered.connect(self.verifSelectedBoth)
                menu.addAction(remCallback)

                remCallback = QtWidgets.QAction(
                    "Verify Selected for Depth Only", menu)
                remCallback.triggered.connect(self.verifSelectedDepth)
                menu.addAction(remCallback)

                remCallback = QtWidgets.QAction(
                    "Verify Selected for Flow Only", menu)
                remCallback.triggered.connect(self.verifSelectedFlow)
                menu.addAction(remCallback)

                remCallback = QtWidgets.QAction(
                    "No Verification for Selected", menu)
                remCallback.triggered.connect(self.verifSelectedNeither)
                menu.addAction(remCallback)

            else:
                subMenu = QMenu(menu)
                subMenu.setTitle('Set Location As')

                remCallback = QtWidgets.QAction("Critical", subMenu)
                remCallback.setCheckable(True)
                remCallback.setChecked(aLoc.isCritical)
                remCallback.triggered.connect(
                    lambda: self.toggleCriticality(aLoc))
                subMenu.addAction(remCallback)

                remCallback = QtWidgets.QAction("Surcharged", subMenu)
                remCallback.setCheckable(True)
                remCallback.setChecked(aLoc.isSurcharged)
                remCallback.triggered.connect(
                    lambda: self.toggleSurcharged(aLoc))
                subMenu.addAction(remCallback)

                menu.addMenu(subMenu)
                menu.addSeparator()

                remCallback = QtWidgets.QAction(
                    "Verify for Depth and Flow", menu)
                remCallback.setCheckable(True)
                remCallback.setChecked(
                    (aLoc.verifyForFlow and aLoc.verifyForDepth))
                remCallback.triggered.connect(
                    lambda: self.toggleVerifBoth(aLoc))
                menu.addAction(remCallback)

                remCallback = QtWidgets.QAction("Verify for Depth", menu)
                remCallback.setCheckable(True)
                remCallback.setChecked(aLoc.verifyForDepth)
                remCallback.triggered.connect(
                    lambda: self.toggleVerifDepth(aLoc))
                menu.addAction(remCallback)

                remCallback = QtWidgets.QAction("Verify for Flow", menu)
                remCallback.setCheckable(True)
                remCallback.setChecked(aLoc.verifyForFlow)
                remCallback.triggered.connect(
                    lambda: self.toggleVerifFlow(aLoc))
                menu.addAction(remCallback)
                menu.addSeparator()

                remCallback = QtWidgets.QAction("Edit Peaks: Depth", menu)
                remCallback.triggered.connect(
                    lambda: self.addICMTracePeak(aLoc, False))
                menu.addAction(remCallback)

                remCallback = QtWidgets.QAction("Edit Peaks: Flow", menu)
                remCallback.triggered.connect(
                    lambda: self.addICMTracePeak(aLoc, True))
                menu.addAction(remCallback)
                menu.addSeparator()

                remCallback = QtWidgets.QAction(
                    "Add Depth Verification Comment", menu)
                remCallback.triggered.connect(
                    lambda: self.addVerificationComment(aLoc, "Depth"))
                menu.addAction(remCallback)

                remCallback = QtWidgets.QAction(
                    "Add Flow Verification Comment", menu)
                remCallback.triggered.connect(
                    lambda: self.addVerificationComment(aLoc, "Flow"))
                menu.addAction(remCallback)

                remCallback = QtWidgets.QAction(
                    "Add Overall Verification Comment", menu)
                remCallback.triggered.connect(
                    lambda: self.addVerificationComment(aLoc, "Overall"))
                menu.addAction(remCallback)

                menu.addSeparator()

                remCallback = QtWidgets.QAction("View Fit Measures", menu)
                remCallback.triggered.connect(
                    lambda: self.viewFitMeasures(aLoc))
                menu.addAction(remCallback)

        menu.exec_(self.trw_PlottedICMTraces.viewport().mapToGlobal(position))

    def addVerificationComment(self, aLoc: icmTraceLocation, commentType: str):

        if commentType == "Depth":
            userText = aLoc.verificationDepthComment
        elif commentType == "Flow":
            userText = aLoc.verificationFlowComment
        else:
            userText = aLoc.verificationOverallComment

        userText, ok = QInputDialog.getMultiLineText(
            self, 'Verification Comment', commentType + ' Verification Comment:', text=userText)
        if ok:
            if commentType == "Depth":
                aLoc.verificationDepthComment = userText
            elif commentType == "Flow":
                aLoc.verificationFlowComment = userText
            else:
                aLoc.verificationOverallComment = userText

    def convertToDummyMonitors(self):

        if self.dummyFMs is None:
            self.dummyFMs = {}
        for aLoc in self.aTraceGraph.plottedICMTrace.plotTrace.dictLocations.values():

            if not aLoc.shortTitle in self.dummyFMs:
                dFM = dummyFlowMonitor()
                dFM.updateEquivalentFMFromTraceLocation(aLoc)

                self.dummyFMs[dFM.dumFMName] = dFM
                self.updateDummyFMTreeView()

    def toggleSmoothing(self, aLoc: icmTraceLocation):

        if ((aLoc.frac[aLoc.iObsFlow] > 0) or (aLoc.frac[aLoc.iObsDepth] > 0)):
            aLoc.frac[aLoc.iObsFlow] = 0
            aLoc.frac[aLoc.iObsDepth] = 0
        else:
            aLoc.frac[aLoc.iObsFlow] = self.defaultSmoothing['Observed']
            aLoc.frac[aLoc.iObsDepth] = self.defaultSmoothing['Observed']

        aLoc.updatePeaks(aLoc.iObsFlow)
        aLoc.updatePeaks(aLoc.iObsDepth)
        self.update_plot()

    def viewFitMeasures(self, aLoc: icmTraceLocation):
        viewFitMeasuresDialog = flowbot_dialog_verification_viewfitmeasure(
            aLoc)
        viewFitMeasuresDialog.setWindowTitle('Fit Measures')
        viewFitMeasuresDialog.show()
        ret = viewFitMeasuresDialog.exec_()

    def toggleCriticality(self, aLoc: icmTraceLocation):
        aLoc.isCritical = not aLoc.isCritical
        self.update_plot()

    def toggleSurcharged(self, aLoc: icmTraceLocation):
        aLoc.isSurcharged = not aLoc.isSurcharged
        self.update_plot()

    def toggleVerifBoth(self, aLoc: icmTraceLocation):

        if aLoc.verifyForFlow == True and aLoc.verifyForDepth == True:
            aLoc.verifyForFlow = False
            aLoc.verifyForDepth = False
        elif aLoc.verifyForFlow == False and aLoc.verifyForDepth == False:
            aLoc.verifyForFlow = True
            aLoc.verifyForDepth = True
        else:
            aLoc.verifyForFlow = True
            aLoc.verifyForDepth = True

        self.update_plot()

    def toggleVerifFlow(self, aLoc: icmTraceLocation):

        aLoc.verifyForFlow = not aLoc.verifyForFlow
        self.update_plot()

    def toggleVerifDepth(self, aLoc: icmTraceLocation):

        aLoc.verifyForDepth = not aLoc.verifyForDepth
        self.update_plot()

    def verifSelectedBoth(self):

        myItems = self.trw_PlottedICMTraces.selectedItems()
        for item in myItems:
            myIndex = self.trw_PlottedICMTraces.indexFromItem(item).row()
            aLoc = self.aTraceGraph.plottedICMTrace.plotTrace.dictLocations[myIndex]
            aLoc.verifyForDepth = True
            aLoc.verifyForFlow = True
        self.update_plot()

    def verifSelectedFlow(self):

        myItems = self.trw_PlottedICMTraces.selectedItems()
        for item in myItems:
            myIndex = self.trw_PlottedICMTraces.indexFromItem(item).row()
            aLoc = self.aTraceGraph.plottedICMTrace.plotTrace.dictLocations[myIndex]
            aLoc.verifyForDepth = False
            aLoc.verifyForFlow = True
        self.update_plot()

    def verifSelectedDepth(self):
        myItems = self.trw_PlottedICMTraces.selectedItems()
        for item in myItems:
            myIndex = self.trw_PlottedICMTraces.indexFromItem(item).row()
            aLoc = self.aTraceGraph.plottedICMTrace.plotTrace.dictLocations[myIndex]
            aLoc.verifyForDepth = True
            aLoc.verifyForFlow = False
        self.update_plot()

    def verifSelectedNeither(self):
        myItems = self.trw_PlottedICMTraces.selectedItems()
        for item in myItems:
            myIndex = self.trw_PlottedICMTraces.indexFromItem(item).row()
            aLoc = self.aTraceGraph.plottedICMTrace.plotTrace.dictLocations[myIndex]
            aLoc.verifyForDepth = False
            aLoc.verifyForFlow = False
        self.update_plot()

    def toggleAllVerification(self):
        self.toggleAllDepthVerification()
        self.toggleAllFlowVerification()

    def toggleAllDepthVerification(self):

        verifyForDepth = not self.aTraceGraph.plottedICMTrace.plotTrace.allVerifiedForDepth()
        for aLoc in self.aTraceGraph.plottedICMTrace.plotTrace.dictLocations.values():
            aLoc.verifyForDepth = verifyForDepth
            if aLoc.verifyForDepth and not aLoc.peaksInitialized[aLoc.iObsDepth]:
                aLoc.frac[aLoc.iObsDepth] = self.defaultSmoothing['Observed']
                aLoc.updatePeaks(aLoc.iObsDepth, 1)
            if aLoc.verifyForDepth and not aLoc.peaksInitialized[aLoc.iPredDepth]:
                aLoc.frac[aLoc.iPredDepth] = self.defaultSmoothing['Predicted']
                aLoc.updatePeaks(aLoc.iPredDepth, 1)

        self.update_plot()

    def toggleAllFlowVerification(self):

        verifyForFlow = not self.aTraceGraph.plottedICMTrace.plotTrace.allVerifiedForFlow()
        for aLoc in self.aTraceGraph.plottedICMTrace.plotTrace.dictLocations.values():
            aLoc.verifyForFlow = verifyForFlow
            if aLoc.verifyForFlow and not aLoc.peaksInitialized[aLoc.iObsFlow]:
                aLoc.frac[aLoc.iObsFlow] = self.defaultSmoothing['Observed']
                aLoc.updatePeaks(aLoc.iObsFlow, 1)
            if aLoc.verifyForFlow and not aLoc.peaksInitialized[aLoc.iPredFlow]:
                aLoc.frac[aLoc.iPredFlow] = self.defaultSmoothing['Predicted']
                aLoc.updatePeaks(aLoc.iPredFlow, 1)

        self.update_plot()

    def removeICMTrace(self):
        if not self.aTraceGraph is None:
            self.aTraceGraph.plottedICMTrace.plotTrace = None
            self.update_plot()

    def addICMTracePeak(self, aLoc: icmTraceLocation, isFlow: bool = True):

        setPeaksDialog = flowbot_dialog_verification_setpeaks(aLoc, isFlow)
        setPeaksDialog.setWindowTitle('Set Peaks')
        setPeaksDialog.show()
        ret = setPeaksDialog.exec_()
        if ret == QDialog.Accepted:
            self.update_plot()

    def toggleSummedFMs(self):

        if self.trwSummedFMs.maximumHeight() == 0:
            self.trwSummedFMs.setMaximumHeight(16777215)
        else:
            self.trwSummedFMs.setMaximumHeight(0)

    def toggleDummyFMs(self):
        if self.trwDummyFMs.maximumHeight() == 0:
            self.trwDummyFMs.setMaximumHeight(16777215)
        else:
            self.trwDummyFMs.setMaximumHeight(0)

    def summedFM_Add(self):

        if self.summedFMs is None:
            self.summedFMs = {}

        text, ok = QInputDialog.getText(
            self, 'New Summed FM', 'Name for Summed FM:')
        if ok:
            if not text in self.summedFMs:
                sFM = summedFlowMonitor()
                sFM.sumFMName = text
                self.summedFMs[text] = sFM

                self.updateSummedFMTreeView()

    def summedFM_Rename(self):

        item = self.trwSummedFMs.selectedItems()[0]
        text, ok = QInputDialog.getText(
            self, 'Rename Summed FM', 'Name for Summed FM:')
        if ok:
            if not text in self.summedFMs:
                sFM = self.summedFMs[item.text(0)]
                sFM.sumFMName = text
                self.summedFMs.pop(item.text(0))
                self.summedFMs[text] = sFM
                self.updateSummedFMTreeView()
                self.update_plot()

    def summedFM_Delete(self):

        item = self.trwSummedFMs.selectedItems()[0]
        if item.text(0) in self.summedFMs:
            sFM = self.summedFMs[item.text(0)]
            if self.removeFMFromAllPlots(sFM.equivalentFM):
                self.update_plot()
            self.summedFMs.pop(item.text(0))
            self.updateSummedFMTreeView()

    def summedFM_RemoveFM(self):
        item = self.trwSummedFMs.selectedItems()[0]
        if not item.parent() is None:
            if item.parent().text(0) in self.summedFMs:
                sFM = self.summedFMs[item.parent().text(0)]
                sFM.removeFM(item.text(0))
                self.summedFMs[item.parent().text(0)] = sFM
                self.updateSummedFMTreeView()
                self.update_plot()

    def summedFM_RemoveFM(self, fmName):
        for sFM in self.summedFMs.values():
            if sFM.containsFM(fmName):
                sFM.removeFM(fmName)
                self.summedFMs[sFM.sumFMName] = sFM
                self.updateSummedFMTreeView()
                self.update_plot()

    def summedFM_UpdateMultiplier(self):
        item = self.trwSummedFMs.selectedItems()[0]
        if item.text(0) in self.summedFMs:
            sFM = self.summedFMs[item.text(0)]

            editMultipliers = flowbot_dialog_sumFMmultiplier(sFM, self)
            editMultipliers.setWindowTitle('Update Multipliers')
            editMultipliers.show()
            ret = editMultipliers.exec_()
            if ret == QDialog.Accepted:

                for i in range(editMultipliers.tableWidget.rowCount()):
                    fm, mult = sFM.fmCollection[editMultipliers.tableWidget.item(
                        i, 0).text()]
                    sFM.removeFM(editMultipliers.tableWidget.item(i, 0).text())
                    sFM.addFM(
                        fm, float(editMultipliers.tableWidget.item(i, 1).text()))

                self.summedFMs[item.text(0)] = sFM
                self.updateSummedFMTreeView()

                if self.tbxGraphs.currentWidget().objectName() == "pageFDV":
                    if sFM.equivalentFM.monitorName in self.aFDVGraph.plotted_fms.plotFMs:
                        self.update_plot()

                if self.tbxGraphs.currentWidget().objectName() == "pageScattergraphs":
                    if sFM.equivalentFM.monitorName == self.aScattergraph.getPlotFM().monitorName:
                        self.update_plot()

    def dummyFM_Delete(self):

        item = self.trwDummyFMs.selectedItems()[0]
        if item.text(0) in self.dummyFMs:
            dFM = self.dummyFMs[item.text(0)]
            if self.removeFMFromAllPlots(dFM.equivalentFM):
                self.update_plot()
            self.dummyFMs.pop(item.text(0))
            self.updateDummyFMTreeView()

    def dummyFM_DeleteAll(self):

        if not self.aFDVGraph is None:
            self.aFDVGraph.plotted_fms = plottedFlowMonitors()
        self.aScattergraph = graphScatter(self.plotCanvasMain)

        self.dummyFMs.clear()
        self.dummyFMs = None
        self.updateDummyFMTreeView()
        self.update_plot()

    def remove_FM_file(self):

        if self.removeFMFromAllPlots(self.lst_FlowMonitors.currentItem().text()):
            self.update_plot()
        self.openFlowMonitors.removeFlowMonitor(
            self.lst_FlowMonitors.currentItem().text())
        self.summedFM_RemoveFM(self.lst_FlowMonitors.currentItem().text())
        self.refreshFlowMonitorListWidget()

    def remove_RG_file(self):

        if self.removeRGFromAllPlots(self.lst_RainGauges.currentItem().text()):
            self.update_plot()
        self.openRainGauges.removeRainGauge(
            self.lst_RainGauges.currentItem().text())
        self.refreshRainGaugeListWidget()

    def editModelData(self):

        fm = self.openFlowMonitors.getFlowMonitor(
            self.lst_FlowMonitors.currentItem().text())

        editFMDataDialog = flobot_dialog_fmdataentry(
            fm, self.importedICMData, self)
        editFMDataDialog.setWindowTitle('Edit FM Data Dialog')
        editFMDataDialog.show()
        ret = editFMDataDialog.exec_()
        if ret == QDialog.Accepted:
            fm.modelDataRG = editFMDataDialog.edtRG.text()
            fm.modelDataPipeRef = editFMDataDialog.cboPipeID.currentText()
            fm.modelDataPipeSystemType = editFMDataDialog.edtSystemType.text()
            fm.modelDataPipeShape = editFMDataDialog.edtPipeShape.text()
            fm.modelDataPipeDia = 0 if editFMDataDialog.edtWidth.text(
            ) == '' else int(editFMDataDialog.edtWidth.text())
            fm.modelDataPipeHeight = 0 if editFMDataDialog.edtHeight.text(
            ) == '' else int(editFMDataDialog.edtHeight.text())
            fm.modelDataPipeUSInvert = 0 if editFMDataDialog.edtUSInvert.text(
            ) == '' else float(editFMDataDialog.edtUSInvert.text())
            fm.modelDataPipeDSInvert = 0 if editFMDataDialog.edtDSInvert.text(
            ) == '' else float(editFMDataDialog.edtDSInvert.text())
            fm.modelDataPipeLength = 0 if editFMDataDialog.edtPipeLength.text(
            ) == '' else float(editFMDataDialog.edtPipeLength.text())
            fm.modelDataPipeRoughness = 0 if editFMDataDialog.edtRoughness.text(
            ) == '' else float(editFMDataDialog.edtRoughness.text())
            fm.hasModelData = True

            if self.tbxGraphs.currentWidget().objectName() == "pageScattergraphs":
                self.update_plot()

    def importICMModelData(self):

        try:
            fileSpec, _ = QtWidgets.QFileDialog.getOpenFileNames(
                self, 'Please locate the model data CSV file', self.lastOpenDialogPath, 'CSV Files (*.CSV)')
            if not fileSpec:
                return
            else:
                self.lastOpenDialogPath = os.path.dirname(fileSpec[0])

                self.importedICMData = {
                    "Pipe ID": [],
                    "Length": [],
                    "Width": [],
                    "Roughness": [],
                    "US Invert": [],
                    "DS Invert": [],
                    "Shape": [],
                    "Height": [],
                    "System": []
                }

                with open(fileSpec[0]) as csvfile:
                    reader = csv.DictReader(csvfile)

                    r = 1
                    for row in reader:

                        if r % 2 == 0:
                            tag = 'even'
                        else:
                            tag = 'odd'

                        self.importedICMData["Pipe ID"].append(
                            row['US node ID']+'.'+row['Link suffix'])
                        self.importedICMData["Length"].append(
                            row['Length (m)'])
                        self.importedICMData["Width"].append(row['Width (mm)'])
                        self.importedICMData["Roughness"].append(
                            row['Bottom roughness Colebrook-White (mm)'])
                        self.importedICMData["US Invert"].append(
                            row['US invert level (m AD)'])
                        self.importedICMData["DS Invert"].append(
                            row['DS invert level (m AD)'])
                        self.importedICMData["Shape"].append(row['Shape ID'])
                        self.importedICMData["Height"].append(
                            row['Height (mm)'])
                        self.importedICMData["System"].append(
                            row['System type'])

                msg = QMessageBox(self)
                msg.setWindowIcon(self.myIcon)
                msg.information(self, 'Information', 'Import Complete')
        except:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.critical(self, 'Error', 'Import Abandoned')

    def dummyFM_AddModelData(self):

        if (not self.dummyFMs is None) and len(self.dummyFMs) > 0:
            self.dlgModelData = flobot_dialog_modeldata(
                self.dummyFMs, self.importedICMData, self)
            self.dlgModelData.setWindowTitle('Model Data Dialog')
            self.dlgModelData.show()
            ret = self.dlgModelData.exec_()
            if ret == QDialog.Accepted:
                if self.tbxGraphs.currentWidget().objectName() == "pageScattergraphs":
                    self.update_plot()
        else:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.critical(self, 'Critical', 'No flow monitors to edit')
            return

        if self.tbxGraphs.currentWidget().objectName() == "pageScattergraphs":
            self.update_plot()

    def updateFlowMonitorModelData(self):

        if not self.openFlowMonitors is None and self.openFlowMonitors.flowMonitorCount() > 0:
            self.dlgModelData = flobot_dialog_modeldata(
                self.openFlowMonitors, self.importedICMData, self)
            self.dlgModelData.setWindowTitle('Model Data Dialog')
            self.dlgModelData.show()
            ret = self.dlgModelData.exec_()
            if ret == QDialog.Accepted:
                if self.tbxGraphs.currentWidget().objectName() == "pageScattergraphs":
                    self.update_plot()
        else:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.critical(self, 'Critical', 'No flow monitors to edit')
            return

        if self.tbxGraphs.currentWidget().objectName() == "pageScattergraphs":
            self.update_plot()

    def editSurveyEvent(self):

        item = self.trwEvents.selectedItems()[0]
        se = self.identifiedSurveyEvents.getSurveyEvent(item.text(0))

        dlgNewEvent = flowbot_dialog_event()
        dlgNewEvent.setWindowTitle('Edit Event')
        dlgNewEvent.edtEventID.setText(se.eventName)
        dlgNewEvent.cboEventType.setCurrentText(se.eventType)
        dlgNewEvent.dteEventStart.setDateTime(se.eventStart)
        dlgNewEvent.dteEventEnd.setDateTime(se.eventEnd)
        dlgNewEvent.show()
        ret = dlgNewEvent.exec_()
        if ret == QDialog.Accepted:
            self.identifiedSurveyEvents.removeSurveyEvent(se.eventName)
            aNewEvent = surveyEvent()
            aNewEvent.eventName = dlgNewEvent.edtEventID.text()
            aNewEvent.eventType = dlgNewEvent.cboEventType.currentText()
            aNewEvent.eventStart = dlgNewEvent.dteEventStart.dateTime().toPyDateTime()
            aNewEvent.eventEnd = dlgNewEvent.dteEventEnd.dateTime().toPyDateTime()
            self.identifiedSurveyEvents.addSurvEvent(aNewEvent)
            self.updateEventTreeView()

    def removeSurveyEvent(self):

        item = self.trwEvents.selectedItems()[0]
        if self.aFDVGraph.has_plot_event():
            pe = self.aFDVGraph.getPlotEvent()
            if pe.eventName == item.text(0):
                self.aFDVGraph.set_plot_event(None)
                self.update_plot()
        self.identifiedSurveyEvents.removeSurveyEvent(item.text(0))
        self.updateEventTreeView()

    def getTreeViewLevel(self, aTreeWidget):

        level = 0

        indexes = aTreeWidget.selectedIndexes()
        if len(indexes) > 0:
            level = 0
            index = indexes[0]

            while index.parent().isValid():
                index = index.parent()
                level += 1

        return level

    def refreshFlowMonitorListWidget(self):
        self.lst_FlowMonitors.clear()
        if not self.openFlowMonitors is None:
            for fm in self.openFlowMonitors.dictFlowMonitors.items():
                self.lst_FlowMonitors.addItem(fm[1].monitorName)
            if not self.mappedFlowMonitors is None:
                for mFM in self.mappedFlowMonitors.dictMappedFlowMonitors.items():
                    if mFM[1].monitorName in self.openFlowMonitors.dictFlowMonitors:
                        myIcon = QtGui.QIcon()
                        # myIcon.addPixmap(QtGui.QPixmap(":/icons/resources/mapPin.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                        pixmap = QtGui.QPixmap(":/icons/resources/mapPin.png")
                        pixmap_resized = pixmap.scaled(16, 16)
                        myIcon.addPixmap(
                            pixmap_resized, QtGui.QIcon.Normal, QtGui.QIcon.Off)
                        self.addIconToItem(self.lst_FlowMonitors, mFM[1].monitorName, myIcon)
                        # self.lst_FlowMonitors.addItem(fm[1].monitorName)

    def addIconToItem(self, listWidget:QListWidget, item_text: str, icon:QtGui.QIcon):
        for index in range(listWidget.count()):
            item = listWidget.item(index)
            if item.text() == item_text:
                item.setIcon(icon)
                break

    def refreshRainGaugeListWidget(self):

        self.lst_RainGauges.clear()
        if not self.openRainGauges is None:
            for rg in self.openRainGauges.dictRainGauges.items():
                self.lst_RainGauges.addItem(rg[1].gaugeName)

    def refreshICMTraceListWidget(self):
        self.lst_ICMTraces.clear()
        if not self.openIcmTraces is None:
            for tr in self.openIcmTraces.dictIcmTraces.items():
                self.lst_ICMTraces.addItem(tr[1].traceID)

    def update_plottedTreeView(self):

        if self.toolBox.currentWidget().objectName() == 'pageFlowSurveyAnalysis':
            if self.tbxGraphs.currentWidget().objectName() == "pageFDV":
                if not self.aFDVGraph is None:
                    root = self.trw_PlottedMonitors.invisibleRootItem()
                    child_count = root.childCount()

                    for i in range(child_count):
                        item = root.child(i)

                        if item.text(0) == 'Flow Monitors':
                            for i in range(item.childCount()):
                                item.removeChild(item.child(0))

                            for fm in self.aFDVGraph.plotted_fms.plotFMs:
                                it = QtWidgets.QTreeWidgetItem()
                                it.setText(0, fm)
                                item.addChild(it)

                            if item.childCount() > 0:
                                item.setExpanded(True)

                        elif item.text(0) == 'Rain Gauges':
                            for i in range(item.childCount()):
                                item.removeChild(item.child(0))

                            for rg in self.aFDVGraph.plotted_rgs.plotRGs:
                                it = QtWidgets.QTreeWidgetItem()
                                it.setText(0, rg)
                                item.addChild(it)

                            if item.childCount() > 0:
                                item.setExpanded(True)

                        elif item.text(0) == 'Event':
                            for i in range(item.childCount()):
                                item.removeChild(item.child(0))

                            if self.aFDVGraph.has_plot_event():
                                it = QtWidgets.QTreeWidgetItem()
                                it.setText(
                                    0, self.aFDVGraph.get_plot_eventName())
                                item.addChild(it)

                            if item.childCount() > 0:
                                item.setExpanded(True)

                        else:
                            root.removeChild(item)

            elif self.tbxGraphs.currentWidget().objectName() == "pageScattergraphs":
                if not self.aScattergraph is None:
                    root = self.trw_Scattergraph.invisibleRootItem()
                    child_count = root.childCount()

                    for i in range(child_count):
                        item = root.child(i)

                        if item.text(0) == 'Flow Monitor':
                            for i in range(item.childCount()):
                                item.removeChild(item.child(0))

                            if self.aScattergraph.hasPlotFM():
                                it = QtWidgets.QTreeWidgetItem()
                                it.setText(
                                    0, self.aScattergraph.getPlotFM().monitorName)
                                item.addChild(it)

                            if item.childCount() > 0:
                                item.setExpanded(True)

                        elif item.text(0) == 'Events':
                            for i in range(item.childCount()):
                                item.removeChild(item.child(0))

                            for se in self.aScattergraph.plottedEvents.plotEvents:
                                it = QtWidgets.QTreeWidgetItem()
                                it.setText(0, se)
                                item.addChild(it)

                            if item.childCount() > 0:
                                item.setExpanded(True)

                        else:
                            root.removeChild(item)

            elif self.tbxGraphs.currentWidget().objectName() == "pageRainfallCumDepth":
                if not self.aCumDepthGraph is None:
                    root = self.trw_CumDepth.invisibleRootItem()
                    child_count = root.childCount()

                    for i in range(child_count):
                        item = root.child(i)

                        if item.text(0) == 'Rain Gauges':
                            for i in range(item.childCount()):
                                item.removeChild(item.child(0))

                            for rg in self.aCumDepthGraph.plotted_rgs.plotRGs:
                                it = QtWidgets.QTreeWidgetItem()
                                it.setText(0, rg)
                                item.addChild(it)

                            if item.childCount() > 0:
                                item.setExpanded(True)

                        elif item.text(0) == 'Event':
                            for i in range(item.childCount()):
                                item.removeChild(item.child(0))

                            if self.aCumDepthGraph.has_plot_event():
                                it = QtWidgets.QTreeWidgetItem()
                                it.setText(
                                    0, self.aCumDepthGraph.get_plot_eventName())
                                item.addChild(it)

                            if item.childCount() > 0:
                                item.setExpanded(True)

                        else:
                            root.removeChild(item)

            elif self.tbxGraphs.currentWidget().objectName() == "pageRainfallAnalysis":
                if not self.aRainfallAnalysis is None:
                    root = self.trw_RainfallAnalysis.invisibleRootItem()
                    child_count = root.childCount()

                    for i in range(child_count):
                        item = root.child(i)

                        if item.text(0) == 'Rain Gauges':
                            for i in range(item.childCount()):
                                item.removeChild(item.child(0))

                            for rg in self.aRainfallAnalysis.plotted_rgs.plotRGs:
                                it = QtWidgets.QTreeWidgetItem()
                                it.setText(0, rg)
                                item.addChild(it)

                            if item.childCount() > 0:
                                item.setExpanded(True)

                        elif item.text(0) == 'Event Parameters':
                            for i in range(item.childCount()):
                                item.removeChild(item.child(0))

                            it = QtWidgets.QTreeWidgetItem()
                            if self.aRainfallAnalysis.useDefaultParams:
                                it.setText(0, "Default")
                            else:
                                it.setText(0, "User Specified")
                            item.addChild(it)

                            if item.childCount() > 0:
                                item.setExpanded(True)

                        else:
                            root.removeChild(item)

            elif self.tbxGraphs.currentWidget().objectName() == "pageDataClassification":
                if not self.aDataClassification is None:
                    root = self.trw_DataClassification.invisibleRootItem()
                    child_count = root.childCount()

                    for i in range(child_count):
                        item = root.child(i)

                        if item.text(0) == 'Flow Monitors':
                            for i in range(item.childCount()):
                                item.removeChild(item.child(0))

                            for fm in self.aDataClassification.classifiedFMs.classFMs:
                                it = QtWidgets.QTreeWidgetItem()
                                it.setText(0, fm)
                                item.addChild(it)

                            if item.childCount() > 0:
                                item.setExpanded(True)

                        elif item.text(0) == 'Events':
                            for i in range(item.childCount()):
                                item.removeChild(item.child(0))

                            for se in self.aDataClassification.plottedEvents.plotEvents:
                                it = QtWidgets.QTreeWidgetItem()
                                it.setText(0, se)
                                item.addChild(it)

                            if item.childCount() > 0:
                                item.setExpanded(True)

                        elif item.text(0) == 'Parameters':
                            for i in range(item.childCount()):
                                item.removeChild(item.child(0))

                            it = QtWidgets.QTreeWidgetItem()
                            if self.aDataClassification.useDefaultParams:
                                it.setText(0, "Default")
                            else:
                                it.setText(0, "User Specified")
                            item.addChild(it)

                            if item.childCount() > 0:
                                item.setExpanded(True)

                        else:
                            root.removeChild(item)

                if len(self.aDataClassification.classifiedFMs.classFMs) == 0:
                    self.btnRefreshDC.setEnabled(False)
                else:
                    if self.aDataClassification.classificationNeedsRefreshed:
                        self.btnRefreshDC.setEnabled(True)
                    else:
                        self.btnRefreshDC.setEnabled(False)

                if self.aDataClassification.join_df is None:
                    self.btnExportDCToExcel.setEnabled(False)
                else:
                    if not self.aDataClassification.classificationNeedsRefreshed:
                        self.btnExportDCToExcel.setEnabled(True)
                    else:
                        self.btnExportDCToExcel.setEnabled(False)
        else:
            if self.tbxVerification.currentWidget().objectName() == "pageVerificationPlots":

                if not self.aTraceGraph is None:
                    root = self.trw_PlottedICMTraces.invisibleRootItem()
                    child_count = root.childCount()

                    if child_count > 0:
                        traceItem = root.child(0)
                        if not self.aTraceGraph.plottedICMTrace.plotTrace is None:
                            if traceItem.text(0) == self.aTraceGraph.plottedICMTrace.plotTrace.traceID:
                                for i in range(traceItem.childCount()):
                                    aLoc = self.aTraceGraph.plottedICMTrace.plotTrace.dictLocations[i]
                                    traceItem.child(i).setBackground(
                                        0, QBrush(aLoc.getColorFromScore()))
                                    f = traceItem.child(i).font(0)
                                    f.setStrikeOut((not aLoc.verifyForDepth) and (
                                        not aLoc.verifyForFlow))
                                    traceItem.child(i).setFont(0, f)
                                return
                            else:
                                root.removeChild(traceItem)
                        else:
                            root.removeChild(traceItem)

                    if not self.aTraceGraph.plottedICMTrace.plotTrace is None:
                        traceItem = QtWidgets.QTreeWidgetItem()
                        traceItem.setText(
                            0, self.aTraceGraph.plottedICMTrace.plotTrace.traceID)
                        root.addChild(traceItem)

                        i = 0
                        for aLoc in self.aTraceGraph.plottedICMTrace.plotTrace.dictLocations.values():
                            locationItem = QtWidgets.QTreeWidgetItem()
                            myText = aLoc.shortTitle

                            locationItem.setText(0, myText)
                            if i == 0:
                                self.aTraceGraph.plottedICMTrace.plotTrace.currentLocation = 0
                            i += 1
                            locationItem.setBackground(
                                0, QBrush(aLoc.getColorFromScore()))
                            f = locationItem.font(0)
                            f.setStrikeOut((not aLoc.verifyForDepth) and (
                                not aLoc.verifyForFlow))
                            locationItem.setFont(0, f)
                            traceItem.addChild(locationItem)

                        if traceItem.childCount() > 0:
                            traceItem.setExpanded(True)

                self.updateICMTraceButtons()

    def updateICMTraceButtons(self):
        self.btnTracePrev.setEnabled(False)
        self.btnTraceNext.setEnabled(False)
        if not self.aTraceGraph is None:
            if not self.aTraceGraph.plottedICMTrace.plotTrace is None:
                if self.aTraceGraph.plottedICMTrace.plotTrace.currentLocation == 0:
                    self.btnTracePrev.setEnabled(False)
                    self.btnTraceNext.setEnabled(True)
                elif self.aTraceGraph.plottedICMTrace.plotTrace.currentLocation == len(self.aTraceGraph.plottedICMTrace.plotTrace.dictLocations) - 1:
                    self.btnTracePrev.setEnabled(True)
                    self.btnTraceNext.setEnabled(False)
                else:
                    self.btnTracePrev.setEnabled(True)
                    self.btnTraceNext.setEnabled(True)

                root = self.trw_PlottedICMTraces.invisibleRootItem()
                if not root.child(0) is None:
                    item = root.child(0)
                    self.trw_PlottedICMTraces.selectionModel().clearSelection()
                    item.child(
                        self.aTraceGraph.plottedICMTrace.plotTrace.currentLocation).setSelected(True)

    def updateSummedFMTreeView(self):

        self.trwSummedFMs.clear()

        root = self.trwSummedFMs.invisibleRootItem()
        child_count = root.childCount()

        if not self.summedFMs is None:
            for sFM in self.summedFMs.values():
                it = QtWidgets.QTreeWidgetItem()
                it.setText(0, sFM.sumFMName)
                root.addChild(it)
                for fm, mult in sFM.fmCollection.values():
                    ch = QtWidgets.QTreeWidgetItem()
                    ch.setText(0, fm.monitorName + "(x" + str(mult) + ")")
                    it.addChild(ch)

    def updateDummyFMTreeView(self):

        root = self.trwDummyFMs.invisibleRootItem()
        child_count = root.childCount()

        for i in range(child_count):
            item = root.child(i)

            if item.text(0) == 'Dummy FMs':
                for i in range(item.childCount()):
                    item.removeChild(item.child(0))

                if not self.dummyFMs is None:
                    for dFM in self.dummyFMs.values():
                        it = QtWidgets.QTreeWidgetItem()
                        it.setText(0, dFM.dumFMName)
                        item.addChild(it)

            if item.childCount() > 0:
                item.setExpanded(True)

    def dodgyForceUpdate(self):
        oldSize = self.size()
        self.resize(oldSize.width() - 1, oldSize.height() - 1)
        self.resize(oldSize)

    def update_plot(self):

        if self.toolBox.currentWidget().objectName() == 'pageFlowSurveyAnalysis':
            if self.tbxGraphs.currentWidget().objectName() == "pageFDV":
                if not self.aFDVGraph is None:
                    self.aFDVGraph.update_plot()

            if self.tbxGraphs.currentWidget().objectName() == "pageScattergraphs":
                if not self.aScattergraph is None:
                    self.aScattergraph.update_plot()

            if self.tbxGraphs.currentWidget().objectName() == "pageRainfallCumDepth":
                if not self.aCumDepthGraph is None:
                    self.dteScattergraphStart.setMinimumDateTime(
                        self.aCumDepthGraph.plotted_rgs.plotEarliestStart)
                    self.dteScattergraphStart.setMaximumDateTime(
                        self.aCumDepthGraph.plotted_rgs.plotLatestEnd)
                    self.aCumDepthGraph.startDate = self.dteScattergraphStart.dateTime()
                    self.aCumDepthGraph.update_plot()
            if self.tbxGraphs.currentWidget().objectName() == "pageRainfallAnalysis":
                if not self.aRainfallAnalysis is None:
                    self.dteRainfallAnalysisStart.setMinimumDateTime(
                        self.aRainfallAnalysis.plotted_rgs.plotEarliestStart)
                    self.dteRainfallAnalysisStart.setMaximumDateTime(
                        self.aRainfallAnalysis.plotted_rgs.plotLatestEnd)
                    self.aRainfallAnalysis.startDate = self.dteRainfallAnalysisStart.dateTime()
                    self.aRainfallAnalysis.update_plot()

            if self.tbxGraphs.currentWidget().objectName() == "pageDataClassification":
                if not self.aDataClassification is None:
                    self.aDataClassification.updatePlot()

        else:
            if self.tbxVerification.currentWidget().objectName() == "pageVerificationPlots":
                if not self.aTraceGraph is None:
                    self.aTraceGraph.update_plot()

                self.updateICMTraceButtons()

        self.update_plottedTreeView()
        self.dodgyForceUpdate()

    def addSurveyEvent(self):
        self.createNewSurveyEvent()

    def captureSurveyEvent(self):
        self.createNewSurveyEvent(True)

    def createNewSurveyEvent(self, capture=False):

        dlgNewEvent = flowbot_dialog_event()

        if capture:
            startDate, endDate = self.getStartEndDateFromCurrentPlot()
            dlgNewEvent.setWindowTitle('Edit Captured Event')
        else:
            startDate, endDate = self.getStartEndDateFromCurrentRGs()
            dlgNewEvent.setWindowTitle('Edit New Event')

        if (not startDate is None) and (not endDate is None):
            dlgNewEvent.dteEventStart.setDateTime(startDate)
            dlgNewEvent.dteEventEnd.setDateTime(endDate)

        dlgNewEvent.show()
        ret = dlgNewEvent.exec_()
        if ret == QDialog.Accepted:
            aNewEvent = surveyEvent()
            aNewEvent.eventName = dlgNewEvent.edtEventID.text()
            aNewEvent.eventType = dlgNewEvent.cboEventType.currentText()
            aNewEvent.eventStart = dlgNewEvent.dteEventStart.dateTime().toPyDateTime()
            aNewEvent.eventEnd = dlgNewEvent.dteEventEnd.dateTime().toPyDateTime()

            if self.identifiedSurveyEvents is None:
                self.identifiedSurveyEvents = surveyEvents()

            self.identifiedSurveyEvents.addSurvEvent(aNewEvent)

            self.updateEventTreeView()

    def updateScattergraphOption(self):

        if (not self.openFlowMonitors is None) or ((not self.dummyFMs is None) and (len(self.dummyFMs) > 0)):
            if not self.aScattergraph is None:
                dlgScattergraphOptions = flowbot_dialog_scattergraphoptions(
                    self.aScattergraph)
                dlgScattergraphOptions.setWindowTitle('Scattergraph Dialog')
                dlgScattergraphOptions.show()
                ret = dlgScattergraphOptions.exec_()
                if ret == QDialog.Accepted:

                    self.aScattergraph.plotFPData = dlgScattergraphOptions.chkFullPeriodData.isChecked()
                    self.aScattergraph.ignoreDataAboveSoffit = dlgScattergraphOptions.chkIgnoreDataAboveSoffit.isChecked()
                    self.aScattergraph.ignoreZeros = dlgScattergraphOptions.chkIgnoreZeros.isChecked()
                    self.aScattergraph.labelOnHover = dlgScattergraphOptions.chkLabelOnHover.isChecked()
                    self.aScattergraph.plotModelData = dlgScattergraphOptions.chkModelData.isChecked()
                    self.aScattergraph.showPipeProfile = dlgScattergraphOptions.chkPipeProfile.isChecked()
                    self.aScattergraph.plotCBWLine = dlgScattergraphOptions.chkCBWData.isChecked()
                    self.aScattergraph.plotIsoQLines = dlgScattergraphOptions.chkIsoQ.isChecked()
                    self.aScattergraph.noOfIsoQLines = int(
                        dlgScattergraphOptions.spnNoOfLines.value())
                    self.aScattergraph.isoQLBound = float(
                        dlgScattergraphOptions.edtMinIsoQ.text())
                    self.aScattergraph.isoQUBound = float(
                        dlgScattergraphOptions.edtMaxIsoQ.text())
                    self.aScattergraph.plotVelocityScattergraph = dlgScattergraphOptions.rbnVelocity.isChecked()

                    self.update_plot()

    def refreshDataClassification(self):
        if not self.openFlowMonitors is None:
            if not self.aDataClassification is None:
                self.aDataClassification.updateFlowSurveyDataClassification()
                self.update_plot()

    def exportDataClassification(self):

        if not self.openFlowMonitors is None:
            if not self.aDataClassification is None:
                exportDataClassificationDialog = flowbot_dialog_data_classification_export(self)
                exportDataClassificationDialog.setWindowTitle(
                    'Export Data Classification to Excel')
                exportDataClassificationDialog.show()
                ret = exportDataClassificationDialog.exec_()
                if ret == QDialog.Accepted:
                    self.aDataClassification.strOutputFileSpec = exportDataClassificationDialog.edtOutputFileSpec.text()
                    self.aDataClassification.exportDataClassificationToExcel()
                    self.update_plot()

    def exportScattergraphs(self):

        if not self.openFlowMonitors is None:
            if not self.aScattergraph is None:
                exportScattergraphDialog = flowbot_dialog_scattergraph_export(
                    self.openFlowMonitors)
                exportScattergraphDialog.setWindowTitle('Export Scattergraphs')
                exportScattergraphDialog.show()
                ret = exportScattergraphDialog.exec_()
                if ret == QDialog.Accepted:
                    self.statusBar().showMessage('Exporting Scattergraphs: ')
                    self.progressBar.setMinimum(0)
                    self.progressBar.setValue(0)
                    self.progressBar.show()
                    self.progressBar.setMaximum(
                        len(exportScattergraphDialog.lst_FlowMonitors.selectedItems()))

                    currentFM = self.aScattergraph.getPlotFM()
                    iCount = 0
                    for fm_name in exportScattergraphDialog.lst_FlowMonitors.selectedItems():
                        self.statusBar().showMessage('Exporting Scattergraphs: ' + fm_name.text())
                        self.aScattergraph.setPlotFM(
                            self.openFlowMonitors.getFlowMonitor(fm_name.text()))
                        self.aScattergraph.update_plot()
                        scatFileSpec = exportScattergraphDialog.outputFolder + '/' + fm_name.text() + \
                            '.jpg'
                        self.aScattergraph.main_window_plot_widget.figure.savefig(
                            scatFileSpec)
                        self.progressBar.setValue(iCount)
                        iCount += 1
                        app.processEvents()
                    self.aScattergraph.setPlotFM(currentFM)
                    self.aScattergraph.update_plot()
                    self.update_plot()

                    self.progressBar.hide()
                    self.statusBar().clearMessage()

    def removeFMFromAllPlots(self, fmName):

        fmRemoved = False

        if not self.aFDVGraph is None:
            fmRemoved = self.aFDVGraph.plotted_fms.removeFM(fmName)

        if not self.aScattergraph is None:
            if not self.aScattergraph.getPlotFM() is None:
                if self.aScattergraph.getPlotFM().monitorName == fmName:
                    self.aScattergraph = graphScatter(self.plotCanvasMain)
                    fmRemoved = True
            else:
                fmRemoved = True

        return fmRemoved

    def removeRGFromAllPlots(self, rgName):

        fmRemoved = False

        if not self.aFDVGraph is None:
            rgRemoved = self.aFDVGraph.plotted_rgs.removeRG(rgName)

        if not self.aCumDepthGraph is None:
            if self.aCumDepthGraph.plotted_rgs.removeRG(rgName):
                rgRemoved = True

        if not self.aRainfallAnalysis is None:
            if self.aRainfallAnalysis.plotted_rgs.removeRG(rgName):
                rgRemoved = True

        return rgRemoved

    def updateEventTreeView(self):

        root = self.trwEvents.invisibleRootItem()
        child_count = root.childCount()

        for i in range(child_count):
            item = root.child(i)

            if item.text(0) == 'Storm':
                for i in range(item.childCount()):
                    item.removeChild(item.child(0))

                if not self.identifiedSurveyEvents is None:
                    for se in self.identifiedSurveyEvents.survEvents.values():
                        if se.eventType == "Storm":
                            it = QtWidgets.QTreeWidgetItem()
                            it.setText(0, se.eventName)
                            item.addChild(it)

                if item.childCount() > 0:
                    item.setExpanded(True)

            elif item.text(0) == 'Dry Day':
                for i in range(item.childCount()):
                    item.removeChild(item.child(0))

                if not self.identifiedSurveyEvents is None:
                    for se in self.identifiedSurveyEvents.survEvents.values():
                        if se.eventType == "Dry Day":
                            it = QtWidgets.QTreeWidgetItem()
                            it.setText(0, se.eventName)
                            item.addChild(it)

                if item.childCount() > 0:
                    item.setExpanded(True)

            elif item.text(0) == 'Dry Period':
                for i in range(item.childCount()):
                    item.removeChild(item.child(0))

                if not self.identifiedSurveyEvents is None:
                    for se in self.identifiedSurveyEvents.survEvents.values():
                        if se.eventType == "Dry Period":
                            it = QtWidgets.QTreeWidgetItem()
                            it.setText(0, se.eventName)
                            item.addChild(it)

                if item.childCount() > 0:
                    item.setExpanded(True)

            else:
                root.removeChild(item)

    def getStartEndDateFromCurrentPlot(self):

        if self.tbxGraphs.currentWidget().objectName() == "pageScattergraphs":
            return None, None  # Scattergraph does not have a temporal axis

        elif self.tbxGraphs.currentWidget().objectName() == "pageFDV":
            aStart, aEnd = mpl_dates.num2date(self.aFDVGraph.plot_axis_rg.get_xlim())

        elif self.tbxGraphs.currentWidget().objectName() == "pageRainfallCumDepth":
            aStart, aEnd = mpl_dates.num2date(
                self.aCumDepthGraph.plotAxisCumDepth.get_xlim())

        elif self.tbxGraphs.currentWidget().objectName() == "pageRainfallAnalysis":
            aStart, aEnd = mpl_dates.num2date(
                self.aRainfallAnalysis.plotAxisIntensity.get_xlim())

        return aStart, aEnd

    def getStartEndDateFromCurrentRGs(self):

        if not self.openRainGauges is None:
            return self.openRainGauges.rgsEarliestStart, self.openRainGauges.rgsLatestEnd
        else:
            return None, None


app = QApplication(sys.argv)
app.setStyle('Fusion')

mainWindow = FlowbotMainWindow()

stylesheet_path = os.path.join(os.path.dirname(__file__), f'resources/qss/{rps_or_tt}_default.qss')
# stylesheet_path = os.path.join(os.path.dirname(__file__), "resources/qss/toolery.qss")
# stylesheet_path = os.path.join(os.path.dirname(__file__), "resources/qss/combinear.qss")

# Open the file
file = QFile(stylesheet_path)
if file.open(QFile.ReadOnly):
    # Read the content
    content = QByteArray(file.readAll())
    # Close the file
    file.close()
else:
    print("Failed to open " + stylesheet_path)

# Set the stylesheet
app.setStyleSheet(str(content, encoding='utf-8'))
mainWindow.setWindowTitle("Flowbot v" + strVersion)
mainWindow.show()

def excepthook(exctype, value, traceback):
    traceback_formated = traceback.format_exception(exctype, value, traceback)
    traceback_string = "".join(traceback_formated)
    print(traceback_string, file=sys.stderr)
    sys.exit(1)
sys.excepthook = excepthook

app.exec_()
