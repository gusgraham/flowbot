# from decimal import ROUND_UP
import os
from io import BytesIO
import re
# from re import A
import sys
import shutil
import time
# from datetime import datetime
from typing import Optional, Dict, List
import fiona
from flowbot_dialog_fsm_add_inspection import flowbot_dialog_fsm_add_inspection
from flowbot_dialog_fsm_add_monitor import flowbot_dialog_fsm_add_monitor
from flowbot_dialog_fsm_create_interim_report import flowbot_dialog_fsm_create_interim_report
from flowbot_dialog_fsm_create_job import flowbot_dialog_fsm_create_job
# from flowbot_dialog_fsm_install import flowbot_dialog_fsm_install
# from flowbot_dialog_fsm_install_fm import flowbot_dialog_fsm_install_fm
# from flowbot_dialog_fsm_install_rg import flowbot_dialog_fsm_install_rg
from flowbot_dialog_fsm_install import flowbot_dialog_fsm_install
from flowbot_dialog_fsm_interim_data_imports import flowbot_dialog_fsm_interim_data_imports
from flowbot_dialog_fsm_review_flowmonitor import flowbot_dialog_fsm_review_flowmonitor
from flowbot_dialog_fsm_review_raingauge import flowbot_dialog_fsm_review_raingauge
from flowbot_dialog_fsm_review_pumplogger import flowbot_dialog_fsm_review_pumplogger
from flowbot_dialog_fsm_uninstall import flowbot_dialog_fsm_uninstall
from flowbot_dialog_fsm_view_photographs import flowbot_dialog_fsm_view_photographs
from flowbot_water_quality import fwqMonitor, fwqMonitors, plottedWQMonitors, MappingDialog
import geopandas as gpd
from pyproj import CRS, Transformer
import pandas as pd
import copy
import csv
from matplotlib import pyplot as plt
import matplotlib.dates as mpl_dates
import sqlite3
import struct
from datetime import datetime, timedelta
import math
from PyPDF2 import PdfWriter, PdfReader
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from PIL import Image
import tempfile
import numpy as np
import gc

from matplotlib.backends.backend_pdf import PdfPages

from matplotlib.dates import DateFormatter
from matplotlib.ticker import MaxNLocator, FuncFormatter

from PyQt5 import (QtCore, QtWidgets, QtGui)
from PyQt5.QtWidgets import (QProgressBar, QMessageBox, QDialog, QInputDialog, QMenu, QGraphicsView,
                             QToolBar, QAction, QActionGroup, QListWidget, QPushButton, QScrollArea)
from PyQt5.QtGui import (
    QStandardItemModel, QStandardItem, QCursor, QBrush, QColor)
from PyQt5.QtCore import (Qt, QModelIndex, QPointF, QUrl, QDateTime)

from qgis.core import (QgsCoordinateReferenceSystem, QgsLayerTreeModel,
                       QgsProject, QgsRasterLayer, QgsVectorLayer, QgsLayerTreeNode, QgsMapLayer)
from qgis.gui import (QgsLayerTreeMapCanvasBridge,
                      QgsLayerTreeView, QgsMapToolPan, QgsMapToolZoom)

from flowbot_helper import (resource_path, PlotWidget,
                            serialize_list, deserialize_list, strVersion, bytes_to_text)
from flowbot_graphing import (GraphFDV, graph_fsm_classification, graph_fsm_cumulative_interim_summary, graph_fsm_dwf_plot, graph_fsm_fdv_plot, graph_fsm_fm_install_summary, graph_fsm_monitor_data_summary, graph_fsm_raingauge_plot, graph_fsm_rg_install_summary, graph_fsm_scatter_plot, graph_fsm_storm_event_summary,
                              graphScatter, graphCumulativeDepth, graphRainfallAnalysis, graphICMTrace, createVerificationDetailPlot, createVerificationDetailUDGTablePlot, createEventSuitabilityEventSummaryTablePlot,  createEventSuitabilityRaingaugeDetailsTablePlot, createEventSuitabilityFMClassPiePlot, graphWQGraph, graphFSMInstall, graphDWF)
from flowbot_verification import icmTraces
from flowbot_data_classification import dataClassification
from flowbot_monitors import (flowMonitors, plottedFlowMonitors, rainGauges, mappedFlowMonitor, mappedFlowMonitors, summedFlowMonitor,
                              dummyFlowMonitor, classifiedFlowMonitors, plottedRainGauges)
from flowbot_survey_events import surveyEvent, surveyEvents, plottedSurveyEvents
# from flowbot_mapping import flowbotWebMap
from flowbot_schematic import (fmGraphicsItem, rgGraphicsItem, csoGraphicsItem, wwpsGraphicsItem, juncGraphicsItem, outfallGraphicsItem,
                               wwtwGraphicsItem, ConnectionPath, cstWWPS, cstCSO, cstWWTW, cstOUTFALL, cstJUNCTION, cstCONNECTION, cstNONE)
from flowbot_dialog_reporting_verificationsummary import flowbot_dialog_reporting_verificationsummary
from flowbot_reporting import tablePDF, verificationDetailPDF, onePagePDF, constructGenericOnePageReport, eventSuitabilityPDF
from flowbot_dialog_reporting_icmtrace import flowbot_dialog_reporting_icmtrace
from flowbot_dialog_reporting_fdv import flowbot_dialog_reporting_fdv
from flowbot_dialog_reporting_flowbalance import flowbot_dialog_reporting_flowbalance
from flowbot_dialog_reporting_eventsuitability import flowbot_dialog_reporting_eventsuitability
from flowbot_dialog_reporting_scatter import flowbot_dialog_reporting_scatter
from flowbot_dialog_scattergraph_options import flowbot_dialog_scattergraphoptions
from flowbot_dialog_modeldata import flowbot_dialog_modeldata
from flowbot_dialog_fmdataentry import flowbot_dialog_fmdataentry
from flowbot_dialog_event_analysis_params import flowbot_dialog_event_analysis_params
from flowbot_dialog_event import flowbot_dialog_event
from flowbot_dialog_sumFM_multiplier import flowbot_dialog_sumFMmultiplier
from flowbot_dialog_data_classification import flowbot_dialog_data_classification
from flowbot_dialog_data_classification_export import flowbot_dialog_data_classification_export
from flowbot_dialog_scattergraph_export import flowbot_dialog_scattergraph_export
from flowbot_dialog_verification_setpeaks import flowbot_dialog_verification_setpeaks, icmTraceLocation
from flowbot_dialog_verification_viewfitmeasure import flowbot_dialog_verification_viewfitmeasure
from flowbot_dialog_projection import fsp_flowbot_projectionDialog
from flowbot_database import DatabaseManager, Tables
from flowbot_dialog_fsm_add_site import flowbot_dialog_fsm_add_site
from flowbot_management import fsmDataClassification, fsmInspection, fsmInstall, fsmInterim, fsmInterimReview, fsmMonitor, fsmProject, fsmSite, fsmRawData, MonitorDataFlowCalculator, PumpLoggerDataCalculator
from flowbot_dialog_fsm_set_interim_dates import flowbot_dialog_fsm_set_interim_dates
from flowbot_dialog_fsm_storm_events import flowbot_dialog_fsm_storm_events
from flowbot_dialog_fsm_review_classification import flowbot_dialog_fsm_review_classification
from flowbot_dialog_fsm_raw_data_settings import flowbot_dialog_fsm_raw_data_settings

from ui_elements.ui_flowbot_mainwindow_gis_base import Ui_MainWindow

from flowbot_logging import get_logger

logger = get_logger('flowbot_logger')


class FlowbotMainWindowGis(QtWidgets.QMainWindow, Ui_MainWindow):

    thisQgsProjectGPKGFileSpec = ''
    thisQgsProject = None
    thisQgsLayerTreeModel = None
    thisQgsLayerTreeView = None
    thisQgsLayerTree = None
    thisQgsLayerTreeMapCanvasBridge = None

    statusbarCrsButton = None
    statusbarCoordinates = None

    worldStreetMapLayer = None
    worldImageryLayer = None

    currentMapTool = None

    def __init__(self, parent=None, app=None):
        """Constructor."""
        super(FlowbotMainWindowGis, self).__init__(parent)

        self.setupUi(self)

        self._thisApp = app
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
        self.aWQGraph: Optional[graphWQGraph] = None
        self.aFSMInstallGraph: Optional[graphFSMInstall] = None
        self.a_dwf_graph: Optional[graphDWF] = None

        self.openFlowMonitors: Optional[flowMonitors] = None
        self.openRainGauges: Optional[rainGauges] = None
        self.mappedFlowMonitors: Optional[mappedFlowMonitors] = None
        self.identifiedSurveyEvents: Optional[surveyEvents] = None
        self.summedFMs: Optional[Dict[str, summedFlowMonitor]] = None
        self.dummyFMs: Optional[Dict[str, dummyFlowMonitor]] = None
        self.openIcmTraces: Optional[icmTraces] = None
        self.fsmProject: Optional[fsmProject] = None
        self.fsm_project_model: QStandardItemModel = QStandardItemModel()
        self.root_item: QStandardItem
        self.openWQMonitors: Optional[fwqMonitors] = None

        self.importedICMData = None
        self.lastOpenDialogPath = ''

        self.mainPageIsSetup = False
        self.tabMapIsSetup = False
        
        self.db_manager: Optional[DatabaseManager] = None

        self.setupMainWindow()
        self.setupMainMenu()
        self.setupMainStatusBar()
        self.setupManagementPage()
        self.setupAnalysisPage()
        self.setupVerificationPage()
        self.setupWaterQualityPage()

        self.initialiseAllVariables()

        # self.load_project_from_filespec('C:/Temp/Flowbot/Flowbot Test Data/FSM/T1172.fbsqlite')
        # self.load_project_from_filespec('C:/Temp/Flowbot/Flowbot Test Data/RealWorldData/Sutton/test.fbsqlite')

    # def update_fsm_project_standard_item_model(self):

    #     self.fsm_project_model.clear()

    #     if self.fsmProject is None:
    #         root_item = QStandardItem("Project: None")
    #         self.fsm_project_model.appendRow(root_item)
    #         return

    #     root_item = QStandardItem(f"Project: {self.fsmProject.job_name}")

    #     planned_group = QStandardItem("Planned")
    #     installed_group = QStandardItem("Installed")
    #     removed_group = QStandardItem("Removed")

    #     for site_id, site in self.fsmProject.dict_fsm_sites.items():
    #         site_item = QStandardItem(f"Site: {site_id}")
    #         # for key, value in site.__dict__.items():
    #         #     site_item.appendRow([
    #         #         QStandardItem(key),
    #         #         QStandardItem(str(value))
    #         #     ])

    #         # Determine the group based on installed status and site type
    #         group = planned_group if not site.installed else installed_group
    #         sub_group_name = "Flow Monitor" if site.siteType == "Flow Monitor" else "Rain Gauge"
    #         sub_group = None

    #         # Find or create sub-group for the site type
    #         for row_index in range(group.rowCount()):
    #             if group.child(row_index).text() == sub_group_name:
    #                 sub_group = group.child(row_index)
    #                 break
    #         else:
    #             sub_group = QStandardItem(sub_group_name)
    #             group.appendRow(sub_group)

    #         sub_group.appendRow(site_item)

    #     root_item.appendRow(planned_group)
    #     root_item.appendRow(installed_group)

    #     self.fsm_project_model.appendRow(root_item)

    #     self.trv_flow_survey_management.expandRecursively(self.trv_flow_survey_management.rootIndex())

    def showEvent(self, event):
        super().showEvent(event)

        if not self.mainPageIsSetup:
            total_width = self.splitterMainWindow.width()
            sizes = [300, int(total_width - 300)]
            self.splitterMainWindow.setSizes(sizes)

            total_height = self.fsm_splitter.height()
            sizes = [int(total_height * 0.85), int(total_height * 0.15)]
            self.fsm_splitter.setSizes(sizes)

            self.mainPageIsSetup = True

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            event.accept()  # Allow the window to close
        else:
            event.ignore()  # Ignore the close event

    def set_active_page_by_name(self, page_name):
        for index in range(self.mainToolBox.count()):
            if self.mainToolBox.itemText(index) == page_name:
                self.mainToolBox.setCurrentIndex(index)
                break

    # def update_fsm_project_standard_item_model(self):

    #     expand_states = self.get_treeview_expand_states()

    #     self.fsm_project_model.clear()

    #     # def updateTreeViewModel(self):
    #     #     for row in range(model.rowCount()):
    #     #         item = model.item(row)
    #     #         if shouldBeDraggable(item):  # Your custom condition
    #     #             item.setFlags(item.flags() | Qt.ItemIsDragEnabled)
    #     #         else:
    #     #             item.setFlags(item.flags() & ~Qt.ItemIsDragEnabled)

    #     if self.fsmProject is None:
    #         proj_item = QStandardItem("Project: None")
    #         font = proj_item.font()
    #         font.setBold(True)
    #         proj_item.setFont(font)
    #         proj_item.setFlags(proj_item.flags() & ~Qt.ItemIsDragEnabled)

    #     else:

    #         proj_item = QStandardItem(f"Project: {self.fsmProject.job_name}")
    #         font = proj_item.font()
    #         font.setBold(True)
    #         proj_item.setFont(font)
    #         proj_item.setFlags(proj_item.flags() & ~Qt.ItemIsDragEnabled)

    #         if self.fsmProject.survey_start_date:
    #             start_date_item = QStandardItem(
    #                 f"Survey Starts: {self.fsmProject.survey_start_date.strftime('%d/%m/%Y')}")
    #         else:
    #             start_date_item = QStandardItem("Survey Starts: Unknown")
    #         if self.fsmProject.survey_complete:
    #             end_date_item = QStandardItem(
    #                 f"Survey Ends: {self.fsmProject.survey_end_date.strftime('%d/%m/%Y')}")
    #         else:
    #             end_date_item = QStandardItem("Survey Ends: Not Set")

    #         start_date_item.setFlags(
    #             start_date_item.flags() & ~Qt.ItemIsDragEnabled)
    #         end_date_item.setFlags(end_date_item.flags()
    #                                & ~Qt.ItemIsDragEnabled)

    #         proj_item.appendRow(start_date_item)
    #         proj_item.appendRow(end_date_item)

    #         sites_group = QStandardItem("Sites")
    #         font = sites_group.font()
    #         font.setBold(True)
    #         sites_group.setFont(font)

    #         monitors_group = QStandardItem("Monitors")
    #         font = monitors_group.font()
    #         font.setBold(True)
    #         monitors_group.setFont(font)

    #         installed_group = QStandardItem("Installed")
    #         font = installed_group.font()
    #         font.setBold(True)
    #         installed_group.setFont(font)

    #         removed_group = QStandardItem("Removed")
    #         font = removed_group.font()
    #         font.setBold(True)
    #         removed_group.setFont(font)

    #         interim_group = QStandardItem("Interims")
    #         font = interim_group.font()
    #         font.setBold(True)
    #         interim_group.setFont(font)

    #         # site_items = {}

    #         for site_id, site in self.fsmProject.dict_fsm_sites.items():
    #             # if not self.fsmProject.site_has_install(site_id):
    #             site_item = QStandardItem(f"Site ID: {site_id}")
    #             # site_items[site_id] = site_item  # Store site item for later reference

    #             # sub_group_name = "FM/DM Sites" if site.siteType in [
    #             #     "Flow Monitor", "Depth Monitor"] else "RG Sites"
    #             if site.siteType in ["Flow Monitor", "Depth Monitor"]:
    #                 sub_group_name = "FM/DM Sites"
    #             elif site.siteType == "Pump Logger":
    #                 sub_group_name = "PL Sites"
    #             else:
    #                 sub_group_name = "RG Sites"
    #             sub_group = None

    #             for row_index in range(sites_group.rowCount()):
    #                 if sites_group.child(row_index).text() == sub_group_name:
    #                     sub_group = sites_group.child(row_index)
    #                     break
    #             else:
    #                 sub_group = QStandardItem(sub_group_name)
    #                 sub_group.setFlags(sub_group.flags() & ~Qt.ItemIsDragEnabled)
    #                 sites_group.appendRow(sub_group)

    #             site_item.setFlags(site_item.flags() & ~Qt.ItemIsDragEnabled)
    #             sub_group.appendRow(site_item)

    #         for monitor_id, monitor in self.fsmProject.dict_fsm_monitors.items():
    #             if not self.fsmProject.monitor_is_installed(monitor_id):
    #                 monitor_item = QStandardItem(f"Monitor ID: {monitor_id}")

    #                 # sub_group_name = "Flow/Depth Monitor" if monitor.monitor_type in [
    #                 #     "Flow Monitor", "Depth Monitor"] else "Rain Gauge"
    #                 if monitor.monitor_type in ["Flow Monitor", "Depth Monitor"]:
    #                     sub_group_name = "Flow/Depth Monitor"
    #                 elif monitor.monitor_type == "Pump Logger":
    #                     sub_group_name = "Pump Logger"
    #                 else:
    #                     sub_group_name = "Rain Gauge"
    #                 sub_group = None

    #                 for row_index in range(monitors_group.rowCount()):
    #                     if monitors_group.child(row_index).text() == sub_group_name:
    #                         sub_group = monitors_group.child(row_index)
    #                         break
    #                 else:
    #                     sub_group = QStandardItem(sub_group_name)
    #                     sub_group.setFlags(sub_group.flags() & ~Qt.ItemIsDragEnabled)
    #                     monitors_group.appendRow(sub_group)

    #                 monitor_item.setFlags(
    #                     monitor_item.flags() & ~Qt.ItemIsDragEnabled)
    #                 sub_group.appendRow(monitor_item)

    #                 # monitors_group.appendRow(monitor_item)

    #         for inst_id, a_install in self.fsmProject.dict_fsm_installs.items():

    #             is_uninstalled = self.fsmProject.uninstalled(inst_id)

    #             if not is_uninstalled:
    #                 group = installed_group
    #             else:
    #                 group = removed_group

    #             if not is_uninstalled:
    #                 site_item = QStandardItem(f"Site ID: {a_install.install_site_id}")
    #                 monitor_item = QStandardItem(f"Monitor ID: {a_install.install_monitor_asset_id}")
    #             else:
    #                 site_item = QStandardItem(f"Site ID: {a_install.install_site_id} (Install ID: {inst_id})")
    #                 monitor_item = QStandardItem(f"Monitor ID: {a_install.install_monitor_asset_id} (Install ID: {inst_id})")

    #             for a_raw in self.fsmProject.dict_fsm_rawdata.values():
    #                 if a_raw.install_id == inst_id:
    #                     rawdata_item = QStandardItem("Raw Data")

    #                     # rawdata_item.appendRow(QStandardItem("Settings"))
    #                     if a_install.install_type in ["Flow Monitor", "Depth Monitor"]:

    #                         dep_data_item = QStandardItem("Depth")
    #                         if a_raw.dep_data is not None:
    #                             dep_data_item.appendRow(QStandardItem(
    #                                 f"Start: {a_raw.dep_data_start.strftime('%d/%m/%Y %H:%M')}"))
    #                             dep_data_item.appendRow(QStandardItem(
    #                                 f"End: {a_raw.dep_data_end.strftime('%d/%m/%Y %H:%M')}"))
    #                         dep_data_item.setFlags(
    #                             dep_data_item.flags() & ~Qt.ItemIsDragEnabled)
    #                         rawdata_item.appendRow(dep_data_item)

    #                     if a_install.install_type == "Flow Monitor":
    #                         vel_data_item = QStandardItem("Velocity")
    #                         if a_raw.dep_data is not None:
    #                             vel_data_item.appendRow(QStandardItem(
    #                                 f"Start: {a_raw.vel_data_start.strftime('%d/%m/%Y %H:%M')}"))
    #                             vel_data_item.appendRow(QStandardItem(
    #                                 f"End: {a_raw.vel_data_end.strftime('%d/%m/%Y %H:%M')}"))
    #                             vel_data_item.setFlags(
    #                                 vel_data_item.flags() & ~Qt.ItemIsDragEnabled)
    #                             rawdata_item.appendRow(vel_data_item)

    #                     if a_install.install_type == "Pump Logger":
    #                         pl_data_item = QStandardItem("Logger")
    #                         if a_raw.pl_data is not None:
    #                             pl_data_item.appendRow(QStandardItem(
    #                                 f"Start: {a_raw.pl_data_start.strftime('%d/%m/%Y %H:%M')}"))
    #                             pl_data_item.appendRow(QStandardItem(
    #                                 f"End: {a_raw.pl_data_end.strftime('%d/%m/%Y %H:%M')}"))
    #                             pl_data_item.setFlags(
    #                                 pl_data_item.flags() & ~Qt.ItemIsDragEnabled)
    #                             rawdata_item.appendRow(pl_data_item)

    #                     if a_install.install_type == "Rain Gauge":
    #                         rg_data_item = QStandardItem("Raingauge")
    #                         if a_raw.rg_data is not None:
    #                             rg_data_item.appendRow(QStandardItem(
    #                                 f"Start: {a_raw.rg_data_start.strftime('%d/%m/%Y %H:%M')}"))
    #                             rg_data_item.appendRow(QStandardItem(
    #                                 f"End: {a_raw.rg_data_end.strftime('%d/%m/%Y %H:%M')}"))
    #                             rg_data_item.setFlags(
    #                                 rg_data_item.flags() & ~Qt.ItemIsDragEnabled)
    #                             rawdata_item.appendRow(rg_data_item)

    #                     bat_data_item = QStandardItem("Voltage")
    #                     if a_raw.bat_data is not None:
    #                         bat_data_item.appendRow(QStandardItem(
    #                             f"Start: {a_raw.bat_data_start.strftime('%d/%m/%Y %H:%M')}"))
    #                         bat_data_item.appendRow(QStandardItem(
    #                             f"End: {a_raw.bat_data_end.strftime('%d/%m/%Y %H:%M')}"))
    #                         bat_data_item.setFlags(
    #                             bat_data_item.flags() & ~Qt.ItemIsDragEnabled)
    #                         rawdata_item.appendRow(bat_data_item)

    #                     rawdata_item.setFlags(
    #                         rawdata_item.flags() & ~Qt.ItemIsDragEnabled)
    #                     monitor_item.appendRow(rawdata_item)

    #             if a_install.data is not None:
    #                 data_item = QStandardItem("Processed Data")
    #                 data_item.appendRow(QStandardItem(
    #                     f"Start: {a_install.data_start.strftime('%d/%m/%Y %H:%M')}"))
    #                 data_item.appendRow(QStandardItem(
    #                     f"End: {a_install.data_end.strftime('%d/%m/%Y %H:%M')}"))
    #                 data_item.setFlags(data_item.flags() & ~
    #                                    Qt.ItemIsDragEnabled)
    #                 monitor_item.appendRow(data_item)

    #             for a_insp in self.fsmProject.dict_fsm_inspections.values():
    #                 if a_insp.install_id == inst_id:
    #                     insp_item = QStandardItem(
    #                         f"Inspection: {a_insp.inspection_date.strftime('%d/%m/%Y')}")
    #                     insp_item.setFlags(
    #                         insp_item.flags() & ~Qt.ItemIsDragEnabled)
    #                     monitor_item.appendRow(insp_item)

    #             site_item.appendRow(monitor_item)

    #             if a_install.install_type in ["Flow Monitor", "Depth Monitor"]:
    #                 sub_group_name = "FM/DM Sites"
    #             elif a_install.install_type == "Rain Gauge":
    #                 sub_group_name = "RG Sites"
    #             elif a_install.install_type == "Pump Logger":
    #                 sub_group_name = "PL Sites"

    #             # sub_group_name = "FM/DM Sites" if a_install.install_type in [
    #             #     "Flow Monitor", "Depth Monitor"] else "RG Sites"
    #             sub_group = None
    #             for row_index in range(group.rowCount()):
    #                 if group.child(row_index).text() == sub_group_name:
    #                     sub_group = group.child(row_index)
    #                     break
    #             else:
    #                 sub_group = QStandardItem(sub_group_name)
    #                 sub_group.setFlags(sub_group.flags() & ~Qt.ItemIsDragEnabled)
    #                 group.appendRow(sub_group)

    #             sub_group.appendRow(site_item)

    #         true_color = QColor(70, 195, 80)  # RGB values for light blue
    #         false_color = QColor(195, 70, 80)  # RGB values for light blue

    #         for int_id, interim in self.fsmProject.dict_fsm_interims.items():
    #             interim_item = QStandardItem(f"Interim: {str(int_id)}")
    #             interim_item.appendRow(QStandardItem(
    #                 f"Start: {interim.interim_start_date.strftime('%d/%m/%Y')}"))
    #             interim_item.appendRow(QStandardItem(
    #                 f"End: {interim.interim_end_date.strftime('%d/%m/%Y')}"))

    #             child_item = QStandardItem(
    #                 f"Data Import: {interim.data_import_complete}")
    #             child_item.setBackground(
    #                 QBrush(true_color if interim.data_import_complete else false_color))
    #             interim_item.appendRow(child_item)

    #             child_item = QStandardItem(
    #                 f"Data Classification: {interim.data_classification_complete}")
    #             child_item.setBackground(
    #                 QBrush(true_color if interim.data_classification_complete else false_color))
    #             interim_item.appendRow(child_item)

    #             child_item = QStandardItem(
    #                 f"Identify Events: {interim.identify_events_complete}")
    #             child_item.setBackground(
    #                 QBrush(true_color if interim.identify_events_complete else false_color))
    #             interim_item.appendRow(child_item)

    #             child_item = QStandardItem(
    #                 f"FM Data Review: {interim.fm_data_review_complete}")
    #             child_item.setBackground(
    #                 QBrush(true_color if interim.fm_data_review_complete else false_color))
    #             interim_item.appendRow(child_item)

    #             child_item = QStandardItem(
    #                 f"RG Data Review: {interim.rg_data_review_complete}")
    #             child_item.setBackground(
    #                 QBrush(true_color if interim.rg_data_review_complete else false_color))
    #             interim_item.appendRow(child_item)

    #             child_item = QStandardItem(
    #                 f"PL Data Review: {interim.pl_data_review_complete}")
    #             child_item.setBackground(
    #                 QBrush(true_color if interim.pl_data_review_complete else false_color))
    #             interim_item.appendRow(child_item)

    #             child_item = QStandardItem(
    #                 f"Interim Report: {interim.report_complete}")
    #             child_item.setBackground(
    #                 QBrush(true_color if interim.report_complete else false_color))
    #             interim_item.appendRow(child_item)

    #             interim_group.appendRow(interim_item)

    #         sites_group.setFlags(sites_group.flags() & ~Qt.ItemIsDragEnabled)
    #         monitors_group.setFlags(
    #             monitors_group.flags() & ~Qt.ItemIsDragEnabled)
    #         installed_group.setFlags(
    #             installed_group.flags() & ~Qt.ItemIsDragEnabled)
    #         removed_group.setFlags(removed_group.flags()
    #                                & ~Qt.ItemIsDragEnabled)
    #         interim_group.setFlags(interim_group.flags()
    #                                & ~Qt.ItemIsDragEnabled)

    #         proj_item.appendRow(sites_group)
    #         proj_item.appendRow(monitors_group)
    #         proj_item.appendRow(installed_group)
    #         proj_item.appendRow(removed_group)
    #         proj_item.appendRow(interim_group)

    #     self.root_item = QStandardItem("Root Item")
    #     self.root_item.appendRow(proj_item)
    #     self.fsm_project_model.appendRow(self.root_item)
    #     root_index = self.fsm_project_model.indexFromItem(self.root_item)
    #     self.trv_flow_survey_management.setRootIndex(root_index)

    #     self.set_treeview_expand_states(expand_states)

    def update_fsm_project_standard_item_model(self):

        expand_states = self.get_treeview_expand_states()

        self.fsm_project_model.clear()

        if self.fsmProject is None:
            proj_item = QStandardItem("Project: None")
            font = proj_item.font()
            font.setBold(True)
            proj_item.setFont(font)
            proj_item.setFlags(proj_item.flags() & ~Qt.ItemIsDragEnabled)

        else:

            proj_item = QStandardItem(f"Project: {self.fsmProject.job_name}")
            font = proj_item.font()
            font.setBold(True)
            proj_item.setFont(font)
            proj_item.setFlags(proj_item.flags() & ~Qt.ItemIsDragEnabled)

            if self.fsmProject.survey_start_date:
                start_date_item = QStandardItem(
                    f"Survey Starts: {self.fsmProject.survey_start_date.strftime('%d/%m/%Y')}")
            else:
                start_date_item = QStandardItem("Survey Starts: Unknown")
            if self.fsmProject.survey_complete:
                end_date_item = QStandardItem(
                    f"Survey Ends: {self.fsmProject.survey_end_date.strftime('%d/%m/%Y')}")
            else:
                end_date_item = QStandardItem("Survey Ends: Not Set")

            start_date_item.setFlags(
                start_date_item.flags() & ~Qt.ItemIsDragEnabled)
            end_date_item.setFlags(end_date_item.flags()
                                   & ~Qt.ItemIsDragEnabled)

            proj_item.appendRow(start_date_item)
            proj_item.appendRow(end_date_item)

            sites_group = QStandardItem("Sites")
            font = sites_group.font()
            font.setBold(True)
            sites_group.setFont(font)

            monitors_group = QStandardItem("Monitors")
            font = monitors_group.font()
            font.setBold(True)
            monitors_group.setFont(font)

            installed_group = QStandardItem("Installed")
            font = installed_group.font()
            font.setBold(True)
            installed_group.setFont(font)

            removed_group = QStandardItem("Removed")
            font = removed_group.font()
            font.setBold(True)
            removed_group.setFont(font)

            interim_group = QStandardItem("Interims")
            font = interim_group.font()
            font.setBold(True)
            interim_group.setFont(font)

            # site_items = {}

            for site_id, site in self.fsmProject.dict_fsm_sites.items():

                site_item = QStandardItem(f"Site ID: {site_id}")

                if site.siteType == "Network Asset":
                    sub_group_name = "Network Asset"
                else:
                    sub_group_name = "Location"
                sub_group = None

                for row_index in range(sites_group.rowCount()):
                    if sites_group.child(row_index).text() == sub_group_name:
                        sub_group = sites_group.child(row_index)
                        break
                else:
                    sub_group = QStandardItem(sub_group_name)
                    sub_group.setFlags(sub_group.flags() & ~Qt.ItemIsDragEnabled)
                    sites_group.appendRow(sub_group)

                site_item.setFlags(site_item.flags() & ~Qt.ItemIsDragEnabled)
                sub_group.appendRow(site_item)

            for monitor_id, monitor in self.fsmProject.dict_fsm_monitors.items():
                if not self.fsmProject.monitor_is_installed(monitor_id):
                    monitor_item = QStandardItem(f"Monitor ID: {monitor_id}")

                    # if monitor.monitor_type in ["Flow Monitor", "Depth Monitor"]:
                    #     sub_group_name = "Flow/Depth Monitor"
                    # elif monitor.monitor_type == "Pump Logger":
                    #     sub_group_name = "Pump Logger"
                    # else:
                    #     sub_group_name = "Rain Gauge"
                    # sub_group = None
                    sub_group_name = monitor.monitor_type

                    for row_index in range(monitors_group.rowCount()):
                        if monitors_group.child(row_index).text() == sub_group_name:
                            sub_group = monitors_group.child(row_index)
                            break
                    else:
                        sub_group = QStandardItem(sub_group_name)
                        sub_group.setFlags(sub_group.flags() & ~Qt.ItemIsDragEnabled)
                        monitors_group.appendRow(sub_group)

                    monitor_item.setFlags(
                        monitor_item.flags() & ~Qt.ItemIsDragEnabled)
                    sub_group.appendRow(monitor_item)

            for inst_id, a_install in self.fsmProject.dict_fsm_installs.items():

                is_uninstalled = self.fsmProject.uninstalled(inst_id)

                if not is_uninstalled:
                    group = installed_group
                else:
                    group = removed_group

                # if not is_uninstalled:
                #     site_item = QStandardItem(f"Site ID: {a_install.install_site_id}")
                #     monitor_item = QStandardItem(f"Monitor ID: {a_install.install_monitor_asset_id}")
                # else:
                #     site_item = QStandardItem(f"Site ID: {a_install.install_site_id} (Install ID: {inst_id})")
                #     monitor_item = QStandardItem(f"Monitor ID: {a_install.install_monitor_asset_id} (Install ID: {inst_id})")

                sub_group_name = a_install.install_type

                install_item = QStandardItem(f"Install ID: {a_install.install_id}")

                for a_raw in self.fsmProject.dict_fsm_rawdata.values():
                    if a_raw.install_id == inst_id:
                        rawdata_item = QStandardItem("Raw Data")

                        # rawdata_item.appendRow(QStandardItem("Settings"))
                        if a_install.install_type in ["Flow Monitor", "Depth Monitor"]:

                            dep_data_item = QStandardItem("Depth")
                            if a_raw.dep_data is not None:
                                dep_data_item.appendRow(QStandardItem(
                                    f"Start: {a_raw.dep_data_start.strftime('%d/%m/%Y %H:%M')}"))
                                dep_data_item.appendRow(QStandardItem(
                                    f"End: {a_raw.dep_data_end.strftime('%d/%m/%Y %H:%M')}"))
                            dep_data_item.setFlags(
                                dep_data_item.flags() & ~Qt.ItemIsDragEnabled)
                            rawdata_item.appendRow(dep_data_item)

                        if a_install.install_type == "Flow Monitor":
                            vel_data_item = QStandardItem("Velocity")
                            if a_raw.dep_data is not None:
                                vel_data_item.appendRow(QStandardItem(
                                    f"Start: {a_raw.vel_data_start.strftime('%d/%m/%Y %H:%M')}"))
                                vel_data_item.appendRow(QStandardItem(
                                    f"End: {a_raw.vel_data_end.strftime('%d/%m/%Y %H:%M')}"))
                                vel_data_item.setFlags(
                                    vel_data_item.flags() & ~Qt.ItemIsDragEnabled)
                                rawdata_item.appendRow(vel_data_item)

                        if a_install.install_type == "Pump Logger":
                            pl_data_item = QStandardItem("Logger")
                            if a_raw.pl_data is not None:
                                pl_data_item.appendRow(QStandardItem(
                                    f"Start: {a_raw.pl_data_start.strftime('%d/%m/%Y %H:%M')}"))
                                pl_data_item.appendRow(QStandardItem(
                                    f"End: {a_raw.pl_data_end.strftime('%d/%m/%Y %H:%M')}"))
                                pl_data_item.setFlags(
                                    pl_data_item.flags() & ~Qt.ItemIsDragEnabled)
                                rawdata_item.appendRow(pl_data_item)

                        if a_install.install_type == "Rain Gauge":
                            rg_data_item = QStandardItem("Raingauge")
                            if a_raw.rg_data is not None:
                                rg_data_item.appendRow(QStandardItem(
                                    f"Start: {a_raw.rg_data_start.strftime('%d/%m/%Y %H:%M')}"))
                                rg_data_item.appendRow(QStandardItem(
                                    f"End: {a_raw.rg_data_end.strftime('%d/%m/%Y %H:%M')}"))
                                rg_data_item.setFlags(
                                    rg_data_item.flags() & ~Qt.ItemIsDragEnabled)
                                rawdata_item.appendRow(rg_data_item)

                        bat_data_item = QStandardItem("Voltage")
                        if a_raw.bat_data is not None:
                            bat_data_item.appendRow(QStandardItem(
                                f"Start: {a_raw.bat_data_start.strftime('%d/%m/%Y %H:%M')}"))
                            bat_data_item.appendRow(QStandardItem(
                                f"End: {a_raw.bat_data_end.strftime('%d/%m/%Y %H:%M')}"))
                            bat_data_item.setFlags(
                                bat_data_item.flags() & ~Qt.ItemIsDragEnabled)
                            rawdata_item.appendRow(bat_data_item)

                        rawdata_item.setFlags(
                            rawdata_item.flags() & ~Qt.ItemIsDragEnabled)
                        install_item.appendRow(rawdata_item)

                if a_install.data is not None:
                    data_item = QStandardItem("Processed Data")
                    data_item.appendRow(QStandardItem(
                        f"Start: {a_install.data_start.strftime('%d/%m/%Y %H:%M')}"))
                    data_item.appendRow(QStandardItem(
                        f"End: {a_install.data_end.strftime('%d/%m/%Y %H:%M')}"))
                    data_item.setFlags(data_item.flags() & ~
                                       Qt.ItemIsDragEnabled)
                    install_item.appendRow(data_item)

                for a_insp in self.fsmProject.dict_fsm_inspections.values():
                    if a_insp.install_id == inst_id:
                        insp_item = QStandardItem(
                            f"Inspection: {a_insp.inspection_date.strftime('%d/%m/%Y')}")
                        insp_item.setFlags(
                            insp_item.flags() & ~Qt.ItemIsDragEnabled)
                        install_item.appendRow(insp_item)

                # site_item.appendRow(monitor_item)

                # if a_install.install_type in ["Flow Monitor", "Depth Monitor"]:
                #     sub_group_name = "FM/DM Sites"
                # elif a_install.install_type == "Rain Gauge":
                #     sub_group_name = "RG Sites"
                # elif a_install.install_type == "Pump Logger":
                #     sub_group_name = "PL Sites"

                # sub_group_name = "FM/DM Sites" if a_install.install_type in [
                #     "Flow Monitor", "Depth Monitor"] else "RG Sites"
                sub_group = None
                for row_index in range(group.rowCount()):
                    if group.child(row_index).text() == sub_group_name:
                        sub_group = group.child(row_index)
                        break
                else:
                    sub_group = QStandardItem(sub_group_name)
                    sub_group.setFlags(sub_group.flags() & ~Qt.ItemIsDragEnabled)
                    group.appendRow(sub_group)

                sub_group.appendRow(install_item)

            true_color = QColor(70, 195, 80)  # RGB values for light blue
            false_color = QColor(195, 70, 80)  # RGB values for light blue

            for int_id, interim in self.fsmProject.dict_fsm_interims.items():
                interim_item = QStandardItem(f"Interim: {str(int_id)}")
                interim_item.appendRow(QStandardItem(
                    f"Start: {interim.interim_start_date.strftime('%d/%m/%Y')}"))
                interim_item.appendRow(QStandardItem(
                    f"End: {interim.interim_end_date.strftime('%d/%m/%Y')}"))

                child_item = QStandardItem(
                    f"Data Import: {interim.data_import_complete}")
                child_item.setBackground(
                    QBrush(true_color if interim.data_import_complete else false_color))
                interim_item.appendRow(child_item)

                child_item = QStandardItem(
                    f"Data Classification: {interim.data_classification_complete}")
                child_item.setBackground(
                    QBrush(true_color if interim.data_classification_complete else false_color))
                interim_item.appendRow(child_item)

                child_item = QStandardItem(
                    f"Identify Events: {interim.identify_events_complete}")
                child_item.setBackground(
                    QBrush(true_color if interim.identify_events_complete else false_color))
                interim_item.appendRow(child_item)

                child_item = QStandardItem(
                    f"FM Data Review: {interim.fm_data_review_complete}")
                child_item.setBackground(
                    QBrush(true_color if interim.fm_data_review_complete else false_color))
                interim_item.appendRow(child_item)

                child_item = QStandardItem(
                    f"RG Data Review: {interim.rg_data_review_complete}")
                child_item.setBackground(
                    QBrush(true_color if interim.rg_data_review_complete else false_color))
                interim_item.appendRow(child_item)

                child_item = QStandardItem(
                    f"PL Data Review: {interim.pl_data_review_complete}")
                child_item.setBackground(
                    QBrush(true_color if interim.pl_data_review_complete else false_color))
                interim_item.appendRow(child_item)

                child_item = QStandardItem(
                    f"Interim Report: {interim.report_complete}")
                child_item.setBackground(
                    QBrush(true_color if interim.report_complete else false_color))
                interim_item.appendRow(child_item)

                interim_group.appendRow(interim_item)

            sites_group.setFlags(sites_group.flags() & ~Qt.ItemIsDragEnabled)
            monitors_group.setFlags(
                monitors_group.flags() & ~Qt.ItemIsDragEnabled)
            installed_group.setFlags(
                installed_group.flags() & ~Qt.ItemIsDragEnabled)
            removed_group.setFlags(removed_group.flags()
                                   & ~Qt.ItemIsDragEnabled)
            interim_group.setFlags(interim_group.flags()
                                   & ~Qt.ItemIsDragEnabled)

            proj_item.appendRow(sites_group)
            proj_item.appendRow(monitors_group)
            proj_item.appendRow(installed_group)
            proj_item.appendRow(removed_group)
            proj_item.appendRow(interim_group)

        self.root_item = QStandardItem("Root Item")
        self.root_item.appendRow(proj_item)
        self.fsm_project_model.appendRow(self.root_item)
        root_index = self.fsm_project_model.indexFromItem(self.root_item)
        self.trv_flow_survey_management.setRootIndex(root_index)

        self.set_treeview_expand_states(expand_states)

    def get_index_for_item(self, item_text, parent_index=QModelIndex()):
        for row in range(self.fsm_project_model.rowCount(parent_index)):
            index = self.fsm_project_model.index(row, 0, parent_index)
            if index.data() == item_text:
                return index
            child_index = self.get_index_for_item(item_text, index)
            if child_index.isValid():
                return child_index
        return QModelIndex()

    def get_treeview_expand_states(self):
        expand_states = {}
        root_index = self.trv_flow_survey_management.rootIndex()

        def traverse(index):
            if index.isValid():
                expand_states[self.fsm_project_model.data(
                    index)] = self.trv_flow_survey_management.isExpanded(index)
                for row in range(self.fsm_project_model.rowCount(index)):
                    child_index = self.fsm_project_model.index(row, 0, index)
                    traverse(child_index)

        traverse(root_index)
        return expand_states

    def set_treeview_expand_states(self, expand_states):
        root_index = self.trv_flow_survey_management.rootIndex()

        def traverse(index):
            if index.isValid():
                item_text = self.fsm_project_model.data(index)
                if item_text in expand_states:
                    self.trv_flow_survey_management.setExpanded(
                        index, expand_states[item_text])
                for row in range(self.fsm_project_model.rowCount(index)):
                    child_index = self.fsm_project_model.index(row, 0, index)
                    traverse(child_index)

        traverse(root_index)

    def create_fsm_project_from_csv(self):

        if self.fsmProject is not None:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)

            ret = msg.warning(self, 'Warning', 'A Flow Survey Job already exists\nAre you sure you want to overwrite it?',
                                QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.No:
                return
                        
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Please locate the batch import file CSV', self.lastOpenDialogPath, 'Flowbot FSM Batch File (*.csv)')
        if not path:
            return
        try:
            key_value_pairs = {}
            table_data = []
            with open(path, mode='r') as file:
                reader = csv.reader(file)
                # Read key-value pairs
                for row in reader:
                    if row and row[0].strip().lower() != 'install reference':
                        key = row[0].strip()
                        value = row[1].strip()
                        key_value_pairs[key] = value
                    else:
                        # Now read the table headers
                        table_headers = row
                        break
                # Read the rest as table data
                for row in reader:
                    if row:
                        table_data.append(row)
                

            self.fsmProject = fsmProject()
            self.fsmProject.job_number = key_value_pairs['Survey Number']
            self.fsmProject.job_name = key_value_pairs['Survey Name']
            self.fsmProject.client = key_value_pairs['Client']
            self.fsmProject.client_job_ref = key_value_pairs['Client Job Ref']
            self.fsmProject.survey_start_date = datetime.strptime(key_value_pairs['Survey Start (DD/MM/YYYY)'], "%d/%m/%Y")

            for row in table_data:
                if row:
                    if 'Site ID' in table_headers:
                        column_index = table_headers.index('Site ID')
                        sSiteID = row[column_index]
                    if 'Location' in table_headers:
                        column_index = table_headers.index('Location')
                        sLocation = row[column_index]
                    if 'Monitor Type (FM/DM/PL/RG)' in table_headers:
                        column_index = table_headers.index('Monitor Type (FM/DM/PL/RG)')
                        sMonitorType = row[column_index]
                    if 'MH Ref' in table_headers:
                        column_index = table_headers.index('MH Ref')
                        sMHRef = row[column_index]                                        
                    if 'Asset ID' in table_headers:
                        column_index = table_headers.index('Asset ID')
                        sMonID = row[column_index]
                    if 'Install Reference' in table_headers:
                        column_index = table_headers.index('Install Reference')
                        sInstallRef = row[column_index]
                    if 'Client Ref' in table_headers:
                        column_index = table_headers.index('Client Ref')
                        sClientRef = row[column_index]
                    if 'Installed Date (DD/MM/YYYY)' in table_headers:
                        column_index = table_headers.index('Installed Date (DD/MM/YYYY)')
                        sInstalledDate = row[column_index]
                    if 'Height (mm)' in table_headers:
                        column_index = table_headers.index('Height (mm)')
                        sHeight = row[column_index]
                    if 'Width (mm)' in table_headers:
                        column_index = table_headers.index('Width (mm)')
                        sWidth = row[column_index]
                    if 'Shape (C/R)' in table_headers:
                        column_index = table_headers.index('Shape (C/R)')
                        sShape = row[column_index]
                    if 'Depth Offset mm' in table_headers:
                        column_index = table_headers.index('Depth Offset mm')
                        sDepthOffset = row[column_index]

                    a_site = self.fsmProject.get_site(sSiteID)
                    if a_site is None:
                        a_site = fsmSite()
                        a_site.siteID = sSiteID
                        if sMonitorType in ['FM', 'DM', 'PL']:
                            a_site.siteType = 'Network Asset'
                        else:
                            a_site.siteType = 'Location'
                        a_site.address = sLocation
                        a_site.mh_ref = sMHRef
                        self.fsmProject.add_site(a_site)
                    
                    if (sMonitorType in ['FM', 'DM', 'PL'] and a_site.siteType == 'Location') or (sMonitorType in ['RG'] and a_site.siteType == 'Network Asset'):
                        raise Exception(f"A Monitor of type '{sMonitorType}' can't be installed in a Site of type '{a_site.siteType}'")
                    
                    

                    a_mon = self.fsmProject.get_monitor(sMonID)
                    if a_mon is None:
                        a_mon = fsmMonitor()
                        a_mon.monitor_asset_id = sMonID
                        if sMonitorType == 'FM':
                            a_mon.monitor_type = 'Flow Monitor'
                        elif sMonitorType == 'DM':
                            a_mon.monitor_type = 'Depth Monitor'
                        elif sMonitorType == 'PL':
                            a_mon.monitor_type = 'Pump Logger'
                        else:
                            a_mon.monitor_type = 'Rain Gauge'
                        self.fsmProject.add_monitor(a_mon)
                    else:
                        raise Exception(f"A Monitor with an Asset ID of '{sMonID}' already exisits")
                        # a_ins_check = self.fsmProject.get_current_install_by_monitor(sMonID)
                        # if a_ins_check is not None:


                    a_ins = self.fsmProject.get_install(sInstallRef)
                    if a_ins is None:
                        a_ins = fsmInstall()
                        a_ins.install_id = sInstallRef
                        a_ins.install_site_id = a_site.siteID
                        a_ins.install_monitor_asset_id = a_mon.monitor_asset_id
                        a_ins.install_type = a_mon.monitor_type
                        a_ins.client_ref = sClientRef
                        a_ins.install_date = datetime.strptime(sInstalledDate, "%d/%m/%Y")
                        if sShape == "C":
                            a_ins.fm_pipe_shape = "Circular"
                        else:
                            a_ins.fm_pipe_shape = "Rectangular"
                        a_ins.fm_pipe_height_mm = int(sHeight)
                        a_ins.fm_pipe_width_mm = int(sWidth)
                        a_ins.fm_sensor_offset_mm = int(sDepthOffset)
                        self.fsmProject.add_install(a_ins)

                    a_raw = fsmRawData()
                    a_raw.rawdata_id = self.fsmProject.get_next_rawdata_id()
                    a_raw.install_id = a_ins.install_id
                    a_raw.file_path = key_value_pairs['Default Data Path']
                    self.fsmProject.add_rawdata(a_raw)

            self.update_fsm_project_standard_item_model()
            self.enable_fsm_menu()
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)
            

# 'Install Reference'
# 'Site ID'
# 'Location'
# 'Monitor Type (FM/DM/PL/RG)'
# 'Asset ID'
# 'Client Ref'
# 'Installed Date (DD/MM/YYYY)'
# 'Height (mm)'
# 'Width (mm)'
# 'Shape (C/R)'
# 'Depth Offset mm'
# 'MH Ref'
# 'Rain Reference'
# 'Silt Level mm'

#     print(f"Column '{header_name}' is at index {column_index}")
# else:
#     print(f"Column '{header_name}' not found in table headers")                


    #     return key_value_pairs, table_headers, table_data

    # file_path = 'ProjectSetup.csv'
    # key_values, headers, data = parse_custom_csv(file_path)
    # print("Key-Value Pairs:", key_values)
    # print("Headers:", headers)
    # print("Data:", data)

        
        

    def create_fsm_job_csv_template(self):

        fileSpec, filter = QtWidgets.QFileDialog.getSaveFileName(self, "Save Batch Import Template File...", self.lastOpenDialogPath, 'Flowbot FSM Batch File (*.csv)')
        if len(fileSpec) == 0:
            return
        
# Define metadata
        metadata = [
            ["Survey Name", "Clevedon"],
            ["Survey Number", "M9999"],
            ["Client", "Some Client Ltd"],
            ["Client Job Ref", "CLI9999"],
            ["Survey Start (DD/MM/YYYY)", "18/09/2024"],
            ["Default Data Path", r"C:\Some\File\Path"]
        ]

        # Define table headers and data
        headers = [
            "Install Reference", "Site ID", "Location", "Monitor Type (FM/DM/PL/RG)",
            "Asset ID", "Client Ref", "Installed Date (DD/MM/YYYY)", "Height (mm)",
            "Width (mm)", "Shape (C/R)", "Depth Offset mm", "MH Ref",
            "Rain Reference", "Silt Level mm"
        ]

        table_data = [
            ["FM001", 4165, "Corner of Wishaw High Rd & Swinstie Rd (5791)", "FM", 4165, "FM001", "20/09/2024", 375, 375, "C", 0, "NS80571601", "RG001", 0]
        ]

        # Write to CSV file
        with open(fileSpec, "w", newline="") as file:
            writer = csv.writer(file, delimiter=",")
            writer.writerows(metadata)
            writer.writerow(headers)  # Write table headers
            writer.writerows(table_data)  # Write data rows

        msg = QMessageBox(self)
        msg.information(self, f"CSV file '{csv_filename}' created successfully.", QMessageBox.Ok)

    def create_fsm_project(self):

        try:
            if self.fsmProject is not None:
                msg = QMessageBox(self)
                msg.setWindowIcon(self.myIcon)

                ret = msg.warning(self, 'Warning', 'A Flow Survey Job already exists\nAre you sure you want to overwrite it?',
                                  QMessageBox.Yes | QMessageBox.No)
                if ret == QMessageBox.No:
                    return

            dlg_create_proj = flowbot_dialog_fsm_create_job(self)
            dlg_create_proj.setWindowTitle('Create Job')
            # dlg_create_proj.show()
            ret = dlg_create_proj.exec_()
            if ret == QDialog.Accepted:

                self.fsmProject = fsmProject()
                self.fsmProject.job_number = dlg_create_proj.txt_job_no.text()
                self.fsmProject.job_name = dlg_create_proj.txt_job_name.text()
                self.fsmProject.client = dlg_create_proj.txt_client.text()
                self.fsmProject.client_job_ref = dlg_create_proj.txt_client_job_ref.text()
                self.fsmProject.survey_start_date = dlg_create_proj.dte_fsm_survey_start.dateTime().toPyDateTime()
                self.fsmProject.survey_end_date = dlg_create_proj.dte_fsm_survey_end.dateTime().toPyDateTime()

            self.update_fsm_project_standard_item_model()
            self.enable_fsm_menu()
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def edit_fsm_project(self):

        try:
            if self.fsmProject is not None:
                dlg_create_proj = flowbot_dialog_fsm_create_job(self)
                dlg_create_proj.setWindowTitle('Edit Job')
                dlg_create_proj.txt_job_no.setText(self.fsmProject.job_number)
                dlg_create_proj.txt_job_name.setText(self.fsmProject.job_name)
                dlg_create_proj.txt_client.setText(self.fsmProject.client)
                dlg_create_proj.txt_client_job_ref.setText(
                    self.fsmProject.client_job_ref)
                dlg_create_proj.dte_fsm_survey_start.setDateTime(
                    QDateTime(self.fsmProject.survey_start_date))
                dlg_create_proj.dte_fsm_survey_end.setDateTime(
                    QDateTime(self.fsmProject.survey_end_date))
                # dlg_create_proj.show()
                ret = dlg_create_proj.exec_()
                if ret == QDialog.Accepted:
                    self.fsmProject.job_number = dlg_create_proj.txt_job_no.text()
                    self.fsmProject.job_name = dlg_create_proj.txt_job_name.text()
                    self.fsmProject.client = dlg_create_proj.txt_client.text()
                    self.fsmProject.client_job_ref = dlg_create_proj.txt_client_job_ref.text()
                    self.fsmProject.survey_start_date = dlg_create_proj.dte_fsm_survey_start.dateTime().toPyDateTime()
                    self.fsmProject.survey_end_date = dlg_create_proj.dte_fsm_survey_end.dateTime().toPyDateTime()

            self.update_fsm_project_standard_item_model()
            self.enable_fsm_menu()
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def enable_fsm_menu(self):

        # self.menu_fsm_submenu_add.setEnabled(self.fsmProject is not None)
        self.action_fsm_add_site.setEnabled(self.fsmProject is not None)
        self.action_fsm_add_monitor.setEnabled(self.fsmProject is not None)
        self.action_fsm_import_data_raw.setEnabled(self.fsmProject is not None)
        self.action_fsm_import_data_fdv.setEnabled(self.fsmProject is not None)
        self.action_fsm_import_data_r.setEnabled(self.fsmProject is not None)
        self.action_fsm_export_data_processed.setEnabled(self.fsmProject is not None)
        self.action_fsm_process_raw_data.setEnabled(self.fsmProject is not None)

    def openFSMTreeViewContextMenu(self, position):

        menu = None
        index = self.trv_flow_survey_management.indexAt(position)
        if index.isValid():
            item = self.fsm_project_model.itemFromIndex(index)
            if item.text().startswith("Project"):
                menu = QMenu(self)
                if self.fsmProject is None:
                    remCallback = QtWidgets.QAction("Create Job", menu)
                    remCallback.triggered.connect(self.create_fsm_project)
                    menu.addAction(remCallback)
                else:
                    remCallback = QtWidgets.QAction("Edit Job", menu)
                    remCallback.triggered.connect(self.edit_fsm_project)
                    menu.addAction(remCallback)

            if item.text().startswith("Sites"):
                menu = QMenu(self)
                remCallback = QtWidgets.QAction("Add Site", menu)
                remCallback.triggered.connect(self.add_fsm_site)
                menu.addAction(remCallback)

            if item.text().startswith("Site ID:"):

                # match = re.search(r"Site ID:\s*([A-Za-z0-9_]+)(?:\s*\(Install ID:\s*(\d+)\))?", item.text())
                # if match:
                #     site_id = match.group(1)  # Capture the Monitor ID
                #     install_id = match.group(2) if match.group(2) else None

                # if install_id:
                #     a_inst = self.fsmProject.dict_fsm_installs[int(install_id)]
                # elif site_id:
                #     a_inst = self.fsmProject.get_current_install_by_site(site_id)

                match = re.search(r'Site ID:\s*(.+)', item.text())  # Capture everything after "Site ID:"

                if match:
                    site_id = match.group(1).strip()  # Extract and remove leading/trailing spaces

                menu = QMenu(self)
                parent_item = item.parent()

                if parent_item:
                    grandparent_item = parent_item.parent()
                    if grandparent_item:
                        if grandparent_item.text() == "Sites":
                            remCallback = QtWidgets.QAction("Edit Site", menu)
                            remCallback.triggered.connect(lambda: self.edit_fsm_site(site_id))
                            menu.addAction(remCallback)
                            remCallback = QtWidgets.QAction("Install Monitor", menu)
                            remCallback.triggered.connect(lambda: self.add_fsm_install(site_id, None))
                            menu.addAction(remCallback)
                        # elif grandparent_item.text() == "Installed":
                        #     remCallback = QtWidgets.QAction("Edit Install Details", menu)
                        #     remCallback.triggered.connect(lambda: self.edit_fsm_install(a_inst))
                        #     menu.addAction(remCallback)
                        #     remCallback = QtWidgets.QAction("Add Inspection", menu)
                        #     remCallback.triggered.connect(lambda: self.add_fsm_inspection(a_inst))
                        #     menu.addAction(remCallback)
                        # elif grandparent_item.text() in ["Installed", "Removed"]:
                        #     remCallback = QtWidgets.QAction("View Photographs", menu)
                        #     remCallback.triggered.connect(lambda: self.add_fsm_install_photographs(a_inst))
                        #     menu.addAction(remCallback)
                        #     remCallback = QtWidgets.QAction(
                        #         "Delete Install Record", menu)
                        #     remCallback.triggered.connect(lambda: self.delete_fsm_install(a_inst))
                        #     menu.addAction(remCallback)

            if item.text().startswith("Monitors"):
                menu = QMenu(self)
                remCallback = QtWidgets.QAction("Add Monitor", menu)
                remCallback.triggered.connect(self.add_fsm_monitor)
                menu.addAction(remCallback)

            if item.text().startswith("Monitor ID:"):

                # match = re.search(r"Monitor ID:\s*([A-Za-z0-9_]+)(?:\s*\(Install ID:\s*(\d+)\))?", item.text())
                # if match:
                #     monitor_id = match.group(1)  # Capture the Monitor ID
                #     install_id = match.group(2) if match.group(2) else None

                # if install_id:
                #     a_inst = self.fsmProject.dict_fsm_installs[int(install_id)]
                # elif monitor_id:
                #     a_inst = self.fsmProject.get_current_install_by_monitor(monitor_id)

                match = re.search(r'Monitor ID:\s*(.+)', item.text())  # Capture everything after "Monitor ID:"

                if match:
                    monitor_id = match.group(1).strip()  # Extract and remove leading/trailing spaces

                menu = QMenu(self)
                parent_item = item.parent()
                if parent_item:
                    grandparent_item = parent_item.parent()
                    if grandparent_item:
                        if grandparent_item.text() == "Monitors":
                            remCallback = QtWidgets.QAction("Edit Monitor", menu)
                            remCallback.triggered.connect(lambda: self.edit_fsm_monitor(monitor_id))
                            menu.addAction(remCallback)
                            remCallback = QtWidgets.QAction("Install Monitor", menu)
                            remCallback.triggered.connect(lambda: self.add_fsm_install(None, monitor_id))
                            menu.addAction(remCallback)
                        # greatgrandparent_item = grandparent_item.parent()
                        # if greatgrandparent_item:
                        #     if greatgrandparent_item.text() == "Installed":

                        #         remCallback = QtWidgets.QAction("Edit Install Details", menu)
                        #         remCallback.triggered.connect(lambda: self.edit_fsm_install(a_inst))
                        #         menu.addAction(remCallback)

                        #         remCallback = QtWidgets.QAction("Add Inspection", menu)
                        #         remCallback.triggered.connect(lambda: self.add_fsm_inspection(a_inst))
                        #         menu.addAction(remCallback)

                        #         remCallback = QtWidgets.QAction("Remove Monitor", menu)
                        #         remCallback.triggered.connect(lambda: self.uninstall_fsm_monitor(a_inst))
                        #         menu.addAction(remCallback)

                        #     if greatgrandparent_item.text() in ["Installed", "Removed"]:

                        #         subMenu = QMenu(menu)
                        #         subMenu.setTitle('Raw Data')

                        #         remCallback = QtWidgets.QAction("Settings", menu)
                        #         # remCallback.triggered.connect(lambda: self.edit_fsm_raw_data_settings(item.text()[len("Monitor ID: "):]))
                        #         remCallback.triggered.connect(lambda: self.edit_fsm_raw_data_settings(a_inst))
                        #         subMenu.addAction(remCallback)

                        #         remCallback = QtWidgets.QAction("Import Raw Data", menu)
                        #         # remCallback.triggered.connect(lambda: self.import_fsm_raw_data(item.text()[len("Monitor ID: "):]))
                        #         remCallback.triggered.connect(lambda: self.import_fsm_raw_data(a_inst))
                        #         subMenu.addAction(remCallback)

                        #         remCallback = QtWidgets.QAction("Process Raw Data", menu)
                        #         # remCallback.triggered.connect(lambda: self.fsm_process_raw_data(item.text()[len("Monitor ID: "):]))
                        #         remCallback.triggered.connect(lambda: self.fsm_process_raw_data(a_inst))
                        #         subMenu.addAction(remCallback)

                        #         menu.addMenu(subMenu)

                        #         remCallback = QtWidgets.QAction("Import Processed Data", menu)
                        #         # remCallback.triggered.connect(lambda: self.add_fsm_data(item.text()[len("Monitor ID: "):]))
                        #         remCallback.triggered.connect(lambda: self.add_fsm_data(a_inst))
                        #         menu.addAction(remCallback)

                        #         remCallback = QtWidgets.QAction("View Photographs", menu)
                        #         # remCallback.triggered.connect(lambda: self.add_fsm_install_photographs(None, item.text()[len("Monitor ID: "):]))
                        #         remCallback.triggered.connect(lambda: self.add_fsm_install_photographs(a_inst))
                        #         menu.addAction(remCallback)

                        #         remCallback = QtWidgets.QAction("Delete Install Record", menu)
                        #         # remCallback.triggered.connect(lambda: self.delete_fsm_install(None, item.text()[len("Monitor ID: "):]))
                        #         remCallback.triggered.connect(lambda: self.delete_fsm_install(a_inst))
                        #         menu.addAction(remCallback)

            if item.text().startswith("Installed"):
                menu = QMenu(self)
                remCallback = QtWidgets.QAction("New Installation", menu)
                remCallback.triggered.connect(
                    lambda:  self.add_fsm_install(None, None))
                menu.addAction(remCallback)

            if item.text().startswith("Install ID:"):

                # match = re.search(r"Monitor ID:\s*([A-Za-z0-9_]+)(?:\s*\(Install ID:\s*(\d+)\))?", item.text())
                # if match:
                #     monitor_id = match.group(1)  # Capture the Monitor ID
                #     install_id = match.group(2) if match.group(2) else None

                # if install_id:
                #     a_inst = self.fsmProject.dict_fsm_installs[int(install_id)]
                # elif monitor_id:
                #     a_inst = self.fsmProject.get_current_install_by_monitor(monitor_id)

                match = re.search(r'Install ID:\s*(.+)', item.text())  # Capture everything after "Install ID:"

                if match:
                    install_id = match.group(1).strip()  # Extract and remove leading/trailing spaces
                    a_inst = self.fsmProject.dict_fsm_installs[install_id]

                menu = QMenu(self)
                parent_item = item.parent()
                if parent_item:
                    grandparent_item = parent_item.parent()
                    if grandparent_item:
                        if grandparent_item.text() == "Installed":

                            remCallback = QtWidgets.QAction("Edit Install Details", menu)
                            remCallback.triggered.connect(lambda: self.edit_fsm_install(a_inst))
                            menu.addAction(remCallback)

                            remCallback = QtWidgets.QAction("Add Inspection", menu)
                            remCallback.triggered.connect(lambda: self.add_fsm_inspection(a_inst))
                            menu.addAction(remCallback)

                            remCallback = QtWidgets.QAction("Remove Monitor", menu)
                            remCallback.triggered.connect(lambda: self.uninstall_fsm_monitor(a_inst))
                            menu.addAction(remCallback)

                        if grandparent_item.text() in ["Installed", "Removed"]:

                            subMenu = QMenu(menu)
                            subMenu.setTitle('Raw Data')

                            remCallback = QtWidgets.QAction("Settings", menu)
                            remCallback.triggered.connect(lambda: self.edit_fsm_raw_data_settings(a_inst))
                            subMenu.addAction(remCallback)

                            remCallback = QtWidgets.QAction("Import Raw Data", menu)
                            remCallback.triggered.connect(lambda: self.import_fsm_raw_data(a_inst))
                            subMenu.addAction(remCallback)

                            remCallback = QtWidgets.QAction("Process Raw Data", menu)
                            remCallback.triggered.connect(lambda: self.fsm_process_raw_data(a_inst))
                            subMenu.addAction(remCallback)

                            menu.addMenu(subMenu)

                            remCallback = QtWidgets.QAction("Import Processed Data", menu)
                            remCallback.triggered.connect(lambda: self.add_fsm_data(a_inst))
                            menu.addAction(remCallback)

                            remCallback = QtWidgets.QAction("View Photographs", menu)
                            remCallback.triggered.connect(lambda: self.add_fsm_install_photographs(a_inst))
                            menu.addAction(remCallback)

                            remCallback = QtWidgets.QAction("Delete Install Record", menu)
                            remCallback.triggered.connect(lambda: self.delete_fsm_install(a_inst))
                            menu.addAction(remCallback)

            if item.text().startswith("Interims"):
                menu = QMenu(self)
                remCallback = QtWidgets.QAction("Create New Interim", menu)
                remCallback.triggered.connect(self.add_fsm_interim)
                menu.addAction(remCallback)

            if item.text().startswith("Interim:"):
                menu = QMenu(self)
                remCallback = QtWidgets.QAction("Edit Interim", menu)
                remCallback.triggered.connect(lambda: self.edit_fsm_interim(
                    int(item.text()[len("Interim: "):])))
                menu.addAction(remCallback)

            if item.text().startswith("Data Import:"):
                parent_item = item.parent()
                if parent_item:
                    menu = QMenu(self)
                    remCallback = QtWidgets.QAction("Review Data Import", menu)
                    remCallback.triggered.connect(lambda: self.review_fsm_interim_data_imports(
                        int(parent_item.text()[len("Interim: "):])))
                    menu.addAction(remCallback)

            if item.text().startswith("Data Classification:"):
                parent_item = item.parent()
                if parent_item:
                    menu = QMenu(self)
                    remCallback = QtWidgets.QAction(
                        "Update Data Classification", menu)
                    remCallback.triggered.connect(lambda: self.update_fsm_data_classification(
                        int(parent_item.text()[len("Interim: "):])))
                    menu.addAction(remCallback)
                    remCallback = QtWidgets.QAction(
                        "Review Data Classification", menu)
                    remCallback.triggered.connect(lambda: self.review_fsm_interim_data_classification(
                        int(parent_item.text()[len("Interim: "):])))
                    menu.addAction(remCallback)

            if item.text().startswith("Identify Events:"):
                parent_item = item.parent()
                if parent_item:
                    menu = QMenu(self)
                    remCallback = QtWidgets.QAction("Identify Events", menu)
                    remCallback.triggered.connect(lambda: self.review_fsm_interim_identify_events(
                        int(parent_item.text()[len("Interim: "):])))
                    menu.addAction(remCallback)

            if item.text().startswith("FM Data Review:"):
                parent_item = item.parent()
                if parent_item:
                    menu = QMenu(self)
                    remCallback = QtWidgets.QAction("Review FM Data", menu)
                    remCallback.triggered.connect(lambda: self.review_fsm_interim_fm_data(
                        int(parent_item.text()[len("Interim: "):])))
                    menu.addAction(remCallback)

            if item.text().startswith("RG Data Review:"):
                parent_item = item.parent()
                if parent_item:
                    menu = QMenu(self)
                    remCallback = QtWidgets.QAction("Review RG Data", menu)
                    remCallback.triggered.connect(lambda: self.review_fsm_interim_rg_data(
                        int(parent_item.text()[len("Interim: "):])))
                    menu.addAction(remCallback)

            if item.text().startswith("PL Data Review:"):
                parent_item = item.parent()
                if parent_item:
                    menu = QMenu(self)
                    remCallback = QtWidgets.QAction("Review PL Data", menu)
                    remCallback.triggered.connect(lambda: self.review_fsm_interim_pl_data(
                        int(parent_item.text()[len("Interim: "):])))
                    menu.addAction(remCallback)

            if item.text().startswith("Interim Report:"):
                parent_item = item.parent()
                if parent_item:
                    menu = QMenu(self)
                    remCallback = QtWidgets.QAction(
                        "Produce Interim Report", menu)
                    remCallback.triggered.connect(lambda: self.review_fsm_interim_produce_interim_report(
                        int(parent_item.text()[len("Interim: "):])))
                    menu.addAction(remCallback)

            if item.text() in ["Depth", "Velocity", "Raingauge", "Voltage"]:
                menu = QMenu(self)
                parent_item = item.parent()
                if parent_item:
                    grandparent_item = parent_item.parent()
                    if grandparent_item:
                        if grandparent_item.text().startswith("Monitor ID: "):
                            remCallback = QtWidgets.QAction("Copy to clipboard", menu)
                            remCallback.triggered.connect(
                                lambda: self.copy_raw_data_to_clipboard(item.text(), grandparent_item.text()[len("Monitor ID: "):]
                                )
                            )
                            menu.addAction(remCallback)

            if item.text() == "Processed Data":
                menu = QMenu(self)
                parent_item = item.parent()
                if parent_item:
                    if parent_item.text().startswith("Monitor ID: "):
                        remCallback = QtWidgets.QAction("Copy to clipboard", menu)
                        remCallback.triggered.connect(lambda: self.copy_processed_data_to_clipboard(parent_item.text()[len("Monitor ID: "):]))
                        menu.addAction(remCallback)
            if menu:
                menu.exec_(
                    self.trv_flow_survey_management.viewport().mapToGlobal(position))

    def copy_processed_data_to_clipboard(self, monitor_id: str):
        copy_complete = False
        a_inst = self.fsmProject.get_install_by_monitor(monitor_id)
        if a_inst:
            if a_inst.data is not None:
                a_inst.data.to_clipboard()
                copy_complete = True

        if copy_complete:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.information(self, 'Processed Data', 'Copied to clipboard', QMessageBox.Ok)            

    def copy_raw_data_to_clipboard(self, data_type: str, monitor_id: str):
        copy_complete = False
        a_inst = self.fsmProject.get_install_by_monitor(monitor_id)
        if a_inst:
            a_raw = self.fsmProject.get_raw_data_by_install(a_inst.install_id)
            if a_raw:
                if data_type == "Depth":
                    if a_raw.dep_data is not None:
                        a_raw.dep_data.to_clipboard()
                        copy_complete = True
                elif data_type == "Velocity":
                    if a_raw.vel_data is not None:
                        a_raw.vel_data.to_clipboard()
                        copy_complete = True
                elif data_type == "Raingauge":
                    if a_raw.rg_data is not None:
                        a_raw.rg_data.to_clipboard()
                        copy_complete = True
                elif data_type == "Voltage":
                    if a_raw.bat_data is not None:
                        a_raw.bat_data.to_clipboard()
                        copy_complete = True
        if copy_complete:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.information(self, 'Raw Data', 'Copied to clipboard', QMessageBox.Ok)            

    def edit_fsm_raw_data_settings(self, a_inst: fsmInstall):

        if a_inst:
            a_raw = self.fsmProject.get_raw_data_by_install(a_inst.install_id)
            if not a_raw:
                a_raw = fsmRawData()
                a_raw.rawdata_id = self.fsmProject.get_next_rawdata_id()
                a_raw.install_id = a_inst.install_id

                if a_inst.install_type in ['Flow Monitor', 'Depth Monitor']:
                    dict_ConvertShape = {'Circular': 'CIRC', 'Rectangular': 'RECT', 'Arched': 'ARCH', 'Cunette': 'CNET',
                                         'Egg': 'EGG', 'Egg 2': 'EGG2', 'Oval': 'OVAL', 'U-Shaped': 'UTOP', 'Other': 'USER'}
                    a_raw.pipe_shape = dict_ConvertShape.get(
                        a_inst.fm_pipe_shape, 'CIRC')
                    a_raw.pipe_width = a_inst.fm_pipe_width_mm
                    a_raw.pipe_height = a_inst.fm_pipe_height_mm
                    data = []
                    data.append([a_inst.install_date, 0,
                                a_inst.fm_sensor_offset_mm, 'Install'])
                    a_raw.dep_corr = pd.DataFrame(
                        data, columns=["DateTime", "DepthCorr", "InvertOffset", "Comment"])

                if not self.fsmProject.add_rawdata(a_raw):
                    msg = QMessageBox(self)
                    msg.setWindowIcon(self.myIcon)
                    msg.critical(
                        self, 'Raw Data Settings', 'Could not add Raw Data settings', QMessageBox.Ok)

            dlg_rawdata_settings = flowbot_dialog_fsm_raw_data_settings(
                a_inst, self.fsmProject)
            dlg_rawdata_settings.setWindowTitle('Raw Data Settings')
            ret = dlg_rawdata_settings.exec_()
            if ret == QDialog.Accepted:
                self.update_plot()

    # def edit_fsm_raw_data_settings(self, monitor_id):

    #     a_inst = self.fsmProject.get_install_by_monitor(monitor_id)
    #     if a_inst:
    #         a_raw = self.fsmProject.get_raw_data_by_install(a_inst.install_id)
    #         if not a_raw:
    #             a_raw = fsmRawData()
    #             a_raw.rawdata_id = self.fsmProject.get_next_rawdata_id()
    #             a_raw.install_id = a_inst.install_id

    #             if a_inst.install_type in ['Flow Monitor', 'Depth Monitor']:
    #                 dict_ConvertShape = {'Circular': 'CIRC', 'Egg': 'EGG',
    #                                      'Oval': 'OVAL', 'Rectangular': 'RECT', 'Other': 'CIRC'}
    #                 a_raw.pipe_shape = dict_ConvertShape.get(
    #                     a_inst.fm_pipe_shape, 'CIRC')
    #                 a_raw.pipe_width = a_inst.fm_pipe_width_mm
    #                 a_raw.pipe_height = a_inst.fm_pipe_height_mm
    #                 data = []
    #                 data.append([a_inst.install_date, 0,
    #                             a_inst.fm_sensor_offset_mm, 'Install'])
    #                 a_raw.dep_corr = pd.DataFrame(
    #                     data, columns=["DateTime", "DepthCorr", "InvertOffset", "Comment"])

    #             if not self.fsmProject.add_rawdata(a_raw):
    #                 msg = QMessageBox(self)
    #                 msg.setWindowIcon(self.myIcon)
    #                 msg.critical(
    #                     self, 'Raw Data Settings', 'Could not add Raw Data settings', QMessageBox.Ok)

    #         dlg_rawdata_settings = flowbot_dialog_fsm_raw_data_settings(
    #             a_inst, self.fsmProject)
    #         dlg_rawdata_settings.setWindowTitle('Raw Data Settings')
    #         ret = dlg_rawdata_settings.exec_()
    #         if ret == QDialog.Accepted:
    #             self.update_plot()

    def fsm_bulk_import_raw_data(self):
        i_count = 0
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(len(self.fsmProject.dict_fsm_installs) - 1)
        self.progressBar.setValue(0)
        self.progressBar.show()

        try:
            for a_inst in self.fsmProject.dict_fsm_installs.values():
                self.statusBar().showMessage('Importing Raw Data for ' + a_inst.install_id + '/' + a_inst.client_ref)
                self.progressBar.setValue(i_count)
                self._thisApp.processEvents()
                self.import_fsm_raw_data(a_inst, False)

                i_count += 1

            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.information(self, 'Import Raw Data',
                            'Import Complete', QMessageBox.Ok)

        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

        finally:
            # This block will execute regardless of whether an exception occurred
            self.statusBar().clearMessage()
            self.progressBar.hide()
            self._thisApp.processEvents()

    def import_fsm_raw_data(self, a_inst:fsmInstall, show_progress: bool = True):

        if a_inst:
            a_raw = self.fsmProject.get_raw_data_by_install(a_inst.install_id)
            if not a_raw:
                return

            if a_inst.install_type == 'Rain Gauge':
                file_spec = os.path.join(a_raw.file_path, self.decode_file_format(
                    a_raw.rainfall_file_format, a_inst))
                if os.path.isfile(file_spec):
                    a_raw.rg_data, s_units = self.read_dat_file(
                        file_spec, show_progress)
                    a_raw.rg_data_start = a_raw.rg_data['Timestamp'].min()
                    a_raw.rg_data_end = a_raw.rg_data['Timestamp'].max()

            if a_inst.install_type in ['Flow Monitor', 'Depth Monitor']:
                file_spec = os.path.join(a_raw.file_path, self.decode_file_format(
                    a_raw.depth_file_format, a_inst))
                if os.path.isfile(file_spec):
                    a_raw.dep_data, s_units = self.read_dat_file(
                        file_spec, show_progress)
                    a_raw.dep_data_start = a_raw.dep_data['Timestamp'].min()
                    a_raw.dep_data_end = a_raw.dep_data['Timestamp'].max()

                file_spec = os.path.join(a_raw.file_path, self.decode_file_format(
                    a_raw.velocity_file_format, a_inst))
                if os.path.isfile(file_spec):
                    a_raw.vel_data, s_units = self.read_dat_file(
                        file_spec, show_progress)
                    a_raw.vel_data_start = a_raw.vel_data['Timestamp'].min()
                    a_raw.vel_data_end = a_raw.vel_data['Timestamp'].max()

            file_spec = os.path.join(a_raw.file_path, self.decode_file_format(
                a_raw.battery_file_format, a_inst))
            if os.path.isfile(file_spec):
                a_raw.bat_data, s_units = self.read_dat_file(
                    file_spec, show_progress)
                a_raw.bat_data_start = a_raw.bat_data['Timestamp'].min()
                a_raw.bat_data_end = a_raw.bat_data['Timestamp'].max()

            if a_inst.install_type == 'Pump Logger':
                file_spec = os.path.join(a_raw.file_path, self.decode_file_format(
                    a_raw.pumplogger_file_format, a_inst))
                if os.path.isfile(file_spec):
                    a_raw.pl_data, s_units = self.read_hobo_csv_file(file_spec, show_progress)
                    a_raw.pl_data_start = a_raw.pl_data['Timestamp'].min()
                    a_raw.pl_data_end = a_raw.pl_data['Timestamp'].max()

        if show_progress:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.information(self, 'Import Raw Data',
                            'Import Complete', QMessageBox.Ok)

        self.update_fsm_project_standard_item_model()

    # def import_fsm_raw_data(self, monitor_id, show_progress: bool = True):
    #     a_inst = self.fsmProject.get_install_by_monitor(monitor_id)
    #     if a_inst:
    #         a_raw = self.fsmProject.get_raw_data_by_install(a_inst.install_id)
    #         if not a_raw:
    #             return

    #         if a_inst.install_type == 'Rain Gauge':
    #             file_spec = os.path.join(a_raw.file_path, self.decode_file_format(
    #                 a_raw.rainfall_file_format, a_inst))
    #             if os.path.isfile(file_spec):
    #                 a_raw.rg_data, s_units = self.read_dat_file(
    #                     file_spec, show_progress)
    #                 a_raw.rg_data_start = a_raw.rg_data['Timestamp'].min()
    #                 a_raw.rg_data_end = a_raw.rg_data['Timestamp'].max()

    #         if a_inst.install_type == 'Flow Monitor':
    #             file_spec = os.path.join(a_raw.file_path, self.decode_file_format(
    #                 a_raw.depth_file_format, a_inst))
    #             if os.path.isfile(file_spec):
    #                 a_raw.dep_data, s_units = self.read_dat_file(
    #                     file_spec, show_progress)
    #                 a_raw.dep_data_start = a_raw.dep_data['Timestamp'].min()
    #                 a_raw.dep_data_end = a_raw.dep_data['Timestamp'].max()

    #             file_spec = os.path.join(a_raw.file_path, self.decode_file_format(
    #                 a_raw.velocity_file_format, a_inst))
    #             if os.path.isfile(file_spec):
    #                 a_raw.vel_data, s_units = self.read_dat_file(
    #                     file_spec, show_progress)
    #                 a_raw.vel_data_start = a_raw.vel_data['Timestamp'].min()
    #                 a_raw.vel_data_end = a_raw.vel_data['Timestamp'].max()

    #         file_spec = os.path.join(a_raw.file_path, self.decode_file_format(
    #             a_raw.battery_file_format, a_inst))
    #         if os.path.isfile(file_spec):
    #             a_raw.bat_data, s_units = self.read_dat_file(
    #                 file_spec, show_progress)
    #             a_raw.bat_data_start = a_raw.bat_data['Timestamp'].min()
    #             a_raw.bat_data_end = a_raw.bat_data['Timestamp'].max()

    #     if show_progress:
    #         msg = QMessageBox(self)
    #         msg.setWindowIcon(self.myIcon)
    #         msg.information(self, 'Import Raw Data',
    #                         'Import Complete', QMessageBox.Ok)

    #     self.update_fsm_project_standard_item_model()

    def decode_file_format(self, file_format: str, a_inst: fsmInstall) -> str:

        if '{pmac_id}' in file_format:
            file_format = file_format.replace('{pmac_id}', self.fsmProject.get_monitor(
                a_inst.install_monitor_asset_id).pmac_id)
        if '{inst_id}' in file_format:
            file_format = file_format.replace('{inst_id}', a_inst.install_id)
        if '{ast_id}' in file_format:
            file_format = file_format.replace(
                '{ast_id}', a_inst.install_monitor_asset_id)
        if '{cl_ref}' in file_format:
            file_format = file_format.replace('{cl_ref}', a_inst.client_ref)
        if '{site_id}' in file_format:
            file_format = file_format.replace(
                '{site_id}', a_inst.install_site_id)
        if '{prj_id}' in file_format:
            file_format = file_format.replace(
                '{prj_id}', self.fsmProject.job_number)
        return file_format

    def read_hobo_csv_file(self, filespec, show_progress: bool = True):
        dt_timestamps = []
        i_values = []

        with open(filespec, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)  # Read all rows into a list
            num_rows = len(rows)
            file.seek(0)

            if show_progress:
                self.progressBar.setMinimum(0)
                self.progressBar.setMaximum(num_rows)
                self.progressBar.setValue(0)
                self.progressBar.show()
                self.statusBar().showMessage(f'Reading HOBO CSV File: {filespec}')

            row_num = 0

            for row in reader:
                row_num += 0
                if show_progress:
                    self.progressBar.setValue(row_num)
                    self._thisApp.processEvents()

                if len(row[0]) == 0:
                    break

                try:
                    value = float(row[2].strip())
                except:
                    continue

                a_datetime = datetime.strptime(row[1].strip(), "%m/%d/%y %I:%M:%S %p")

                i_values.append(int(value))
                dt_timestamps.append(a_datetime)

            if show_progress:
                self.statusBar().clearMessage()
                self.progressBar.hide()
                self._thisApp.processEvents()

        return pd.DataFrame({'Timestamp': dt_timestamps, 'Value': i_values}), 'on/off'

    def read_dat_file(self, filespec, show_progress: bool = True):
        dt_timestamps = []
        i_values = []

        with open(filespec, "rb") as file:
            file.seek(0, 2)  # Move the cursor to the end of the file
            file_size = file.tell()
            if show_progress:
                self.progressBar.setMinimum(0)
                self.progressBar.setMaximum(file_size)
                self.progressBar.setValue(0)
                self.progressBar.show()
                self.statusBar().showMessage(f'Reading DAT File: {filespec}')

            file.seek(0, 0)  # Move the cursor to the start of the file
            s_header = bytes_to_text(file.read(30))
            i_flag = struct.unpack('<B', file.read(1))[0]
            i_year = struct.unpack('<H', file.read(2))[0]
            i_month = struct.unpack('<H', file.read(2))[0]
            i_day = struct.unpack('<H', file.read(2))[0]
            i_hour = struct.unpack('<H', file.read(2))[0]
            i_minute = struct.unpack('<H', file.read(2))[0]
            i_second = struct.unpack('<H', file.read(2))[0]
            i_interval = int((struct.unpack('<H', file.read(2))[0])/(10*60))
            s_measurement_type = bytes_to_text(file.read(15))
            s_units = bytes_to_text(file.read(10))
            f_max_value = struct.unpack('<f', file.read(4))[0]
            f_min_value = struct.unpack('<f', file.read(4))[0]
            start_datetime = datetime(
                i_year, i_month, i_day, i_hour, i_minute, i_second)
            i = 0
            my_pos = 78
            tip_timestamps = []

            # Determine max threshold based on flag
            if i_flag == 2:
                no_of_bytes = 1
                max_threshold = 255
            elif i_flag == 8:
                no_of_bytes = 2
                max_threshold = 32767
            elif i_flag == 17:
                no_of_bytes = 4
                max_threshold = 1

            while True:

                if show_progress:
                    self.progressBar.setValue(my_pos)
                    self._thisApp.processEvents()

                float_bytes = file.read(no_of_bytes)
                my_pos = my_pos + no_of_bytes
                if not float_bytes:
                    break

                try:
                    # Extract initial value based on flag
                    if i_flag == 2:
                        int_value = struct.unpack('<B', float_bytes)[0]
                    elif i_flag == 8:
                        int_value = struct.unpack('<H', float_bytes)[0]
                    elif i_flag == 17:
                        int_value = struct.unpack('<I', float_bytes)[0]

                    if i_flag != 17:
                        # Check if value exceeds maximum threshold
                        if int_value >= max_threshold:
                            int_value = np.nan
                        else:
                            # Normalize and scale the value
                            int_value = int_value / max_threshold
                            int_value = f_min_value + \
                                ((f_max_value - f_min_value) * int_value)

                        i_values.append(int_value)
                        dt_timestamps.append(
                            start_datetime + timedelta(minutes=i * i_interval))
                    else:
                        if int_value < 4294967295:
                            tip_time = start_datetime + \
                                timedelta(seconds=int_value)
                            tip_timestamps.append(tip_time)

                except Exception as e:
                    print(f"Error processing value at index {i}: {e}")

                i += 1

            if show_progress:
                self.statusBar().clearMessage()
                self.progressBar.hide()
                self._thisApp.processEvents()

            # Post-processing based on flag type
            if i_flag == 17:
                # return pd.DataFrame(columns=['Timestamp']), s_units
                return pd.DataFrame({'Timestamp': tip_timestamps}), s_units
            else:
                # Round values for non-tipping bucket data
                i_values = [round(val, 3) if not np.isnan(
                    val) else val for val in i_values]
                # Return the DataFrame with rounded values
                return pd.DataFrame({'Timestamp': dt_timestamps, 'Value': i_values}), s_units

    def fsm_bulk_process_raw_data(self):
        i_count = 0
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(len(self.fsmProject.dict_fsm_installs) - 1)
        self.progressBar.setValue(0)
        self.progressBar.show()

        try:
            for a_inst in self.fsmProject.dict_fsm_installs.values():
                self.statusBar().showMessage('Processing Raw Data for ' + a_inst.install_id + '/' + a_inst.client_ref)
                self.progressBar.setValue(i_count)
                self._thisApp.processEvents()
                self.fsm_process_raw_data(a_inst, False)

                i_count += 1

            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.information(self, 'Process Raw Data',
                            'Processing Complete', QMessageBox.Ok)
            self.update_plot()

        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

        finally:
            # This block will execute regardless of whether an exception occurred
            self.statusBar().clearMessage()
            self.progressBar.hide()
            self._thisApp.processEvents()

    def fsm_process_raw_data(self, a_inst: fsmInstall, show_progress: bool = True):

        if a_inst:
            a_raw = self.fsmProject.get_raw_data_by_install(a_inst.install_id)
            if not a_raw:
                return
            if a_inst.install_type == 'Rain Gauge':
                a_inst.data = self.post_process_raw_rainfall_data(
                    a_raw, show_progress)
            if a_inst.install_type == 'Flow Monitor':
                a_inst.data = self.post_process_raw_flowmonitor_data(a_raw)
            if a_inst.install_type == 'Depth Monitor':
                a_inst.data = self.post_process_raw_depthmonitor_data(a_raw)
            if a_inst.install_type == 'Pump Logger':
                a_inst.data = self.post_process_raw_pumplogger_data(a_raw)
            a_inst.data_start = a_inst.data['Date'].min().to_pydatetime()
            a_inst.data_end = a_inst.data['Date'].max().to_pydatetime()
            a_inst.data_date_updated = datetime.now()

        if show_progress:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.information(self, 'Process Raw Data',
                            'Processing Complete', QMessageBox.Ok)
            self.update_plot()

        self.update_fsm_project_standard_item_model()

    # def fsm_process_raw_data(self, monitor_id, show_progress: bool = True):

    #     a_inst = self.fsmProject.get_install_by_monitor(monitor_id)
    #     if a_inst:
    #         a_raw = self.fsmProject.get_raw_data_by_install(a_inst.install_id)
    #         if not a_raw:
    #             return
    #         if a_inst.install_type == 'Rain Gauge':
    #             a_inst.data = self.post_process_raw_rainfall_data(
    #                 a_raw, show_progress)
    #             # # a_inst.data_start = a_inst.data['Date'].min()
    #             # a_inst.data_start = datetime.strptime(a_inst.data['Date'].min(), '%y%m%d%H%M')
    #             # # a_inst.data_end = a_inst.data['Date'].max()
    #             # a_inst.data_end = datetime.strptime(a_inst.data['Date'].max(), '%y%m%d%H%M')
    #             # a_inst.data_date_updated = datetime.now()
    #         if a_inst.install_type == 'Flow Monitor':
    #             a_inst.data = self.post_process_raw_flowmonitor_data(a_raw)
    #         a_inst.data_start = a_inst.data['Date'].min().to_pydatetime()
    #         a_inst.data_end = a_inst.data['Date'].max().to_pydatetime()
    #         a_inst.data_date_updated = datetime.now()

    #     if show_progress:
    #         msg = QMessageBox(self)
    #         msg.setWindowIcon(self.myIcon)
    #         msg.information(self, 'Process Raw Data',
    #                         'Processing Complete', QMessageBox.Ok)
    #         self.update_plot()

    #     self.update_fsm_project_standard_item_model()

    def post_process_raw_rainfall_data(self, a_raw: fsmRawData, show_progress: bool = True):

        tip_timestamps = a_raw.rg_data['Timestamp'].to_list()

        # Create full 2-minute interval range
        start_datetime = min(tip_timestamps)
        end_datetime = max(tip_timestamps)

        # Round start time to the next 2-minute interval
        first_interval_start = start_datetime.replace(
            minute=((start_datetime.minute // 2) * 2 + 2),
            second=0,
            microsecond=0
        )

        full_timestamps = pd.date_range(
            start=first_interval_start,
            end=end_datetime.replace(minute=(end_datetime.minute // 2) * 2,
                                     second=0,
                                     microsecond=0),
            freq='2T'
        )

        # Group tips into 2-minute intervals
        grouped_tips = {}
        for tip in tip_timestamps:
            rounded_time = pd.Timestamp(tip).floor(
                '2T') + pd.Timedelta(minutes=2)
            grouped_tips.setdefault(rounded_time, []).append(tip)

        # Calculate rainfall intensities for full interval range
        df = pd.DataFrame(0.0, index=full_timestamps, columns=['Value'])
        # dt_timestamps = []
        # i_values = []
        # Track the last tip time
        last_tip_time = None

        i_count = 0
        if show_progress:
            self.progressBar.setMinimum(0)
            self.progressBar.setMaximum(len(full_timestamps) - 1)
            self.progressBar.setValue(0)
            self.progressBar.show()

        for timestamp in full_timestamps:

            if show_progress:
                self.statusBar().showMessage('Processing Raw Data')
                self.progressBar.setValue(i_count)
                self._thisApp.processEvents()
            i_count += 1
            tips_in_interval = grouped_tips.get(timestamp, [])

            if tips_in_interval:
                # Calculate time since previous measurement
                if last_tip_time is None:
                    time_since_prev = 10  # Default to 10 minutes if first interval
                else:
                    time_since_prev = (
                        timestamp - last_tip_time).total_seconds() / 60

                # Determine averaging period (minimum of time since prev and 10 minutes)
                avg_period = min(time_since_prev, 10)

                # Calculate total tips and rainfall intensity
                tips_this_interval = len(tips_in_interval)

                if tips_this_interval > 1:
                    if avg_period > 2:
                        tips_current_timestamps = tips_this_interval - 1
                        mm_per_hour_current_timestamps = tips_current_timestamps * \
                            (60 / 2) * a_raw.rg_tb_depth
                        tips_to_distribute = 1
                        mm_per_hour_to_distribute = tips_to_distribute * \
                            (60 / (avg_period - 2)) * a_raw.rg_tb_depth
                    else:
                        tips_current_timestamps = tips_this_interval
                        mm_per_hour_current_timestamps = tips_current_timestamps * \
                            (60 / 2) * a_raw.rg_tb_depth
                else:
                    tips_current_timestamps = 1
                    mm_per_hour_current_timestamps = tips_current_timestamps * \
                        (60 / avg_period) * a_raw.rg_tb_depth
                    if avg_period > 2:
                        tips_to_distribute = 1
                        mm_per_hour_to_distribute = tips_to_distribute * \
                            (60 / avg_period) * a_raw.rg_tb_depth

                # Determine number of periods to distribute across
                periods_in_avg = math.ceil(avg_period / 2)

                # Fill in values for all periods in the averaging interval
                for period in range(periods_in_avg):
                    period_timestamp = timestamp - \
                        pd.Timedelta(
                            minutes=2 * (periods_in_avg - period))
                    if period == periods_in_avg - 1:
                        value_to_add = mm_per_hour_current_timestamps
                    else:
                        value_to_add = mm_per_hour_to_distribute

                    if period_timestamp in df.index:
                        df.loc[period_timestamp, 'Value'] += value_to_add
                    else:
                        new_row = pd.DataFrame(
                            {'Value': value_to_add}, index=[period_timestamp])
                        df = pd.concat([df, new_row]).sort_index()

                # Update last tip time to the last tip in this interval
                last_tip_time = timestamp

        # # Convert the index to the desired format
        # df.index = df.index.to_series().apply(
        #     lambda x: datetime(x.year, x.month, x.day, x.hour, x.minute))
        # Return the processed DataFrame
        if show_progress:
            self.statusBar().clearMessage()
            self.progressBar.hide()
            self._thisApp.processEvents()

        return df.reset_index().rename(columns={'index': 'Date', 'Value': 'IntensityData'})

    def post_process_raw_flowmonitor_data(self, a_raw: fsmRawData):

        calculator = MonitorDataFlowCalculator(a_raw)
        return calculator.calculate_flow()

    def post_process_raw_depthmonitor_data(self, a_raw: fsmRawData):

        calculator = PumpLoggerDataCalculator(a_raw)
        return calculator.calculate_pumplog()

    def post_process_raw_pumplogger_data(self, a_raw: fsmRawData):
        pass

    def fsm_export_data_processed(self):

        file_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Directory:", self.lastOpenDialogPath, QtWidgets.QFileDialog.ShowDirsOnly)
        if len(file_path) == 0:
            return
        self.lastOpenDialogPath = file_path

        for a_inst in self.fsmProject.dict_fsm_installs.values():

            if a_inst.install_type in ['Flow Monitor', 'Depth Monitor']:
                pass
            elif a_inst.install_type == 'Rain Gauge':
                self.write_rangauge_to_file(file_path, a_inst)

            else:
                pass

        msg = QMessageBox(self)
        msg.setWindowIcon(self.myIcon)
        msg.information(self, 'Export Processed Data', 'Export Complete', QMessageBox.Ok)

    def write_rangauge_to_file(self, file_path: str, rg_inst: fsmInstall):

        file_spec = os.path.join(file_path, f'{self.fsmProject.job_number}_{rg_inst.client_ref}.r')

        identifier = f'{self.fsmProject.job_number}_{rg_inst.client_ref}'
        # 'YYMMDDHHMM'
        start_date = rg_inst.data_start.strftime('%y%m%d%H%M')
        end_date = rg_inst.data_end.strftime('%y%m%d%H%M')

        header = "\n".join(["**DATA_FORMAT:               1,ASCII",
                            f"**IDENTIFIER:                1,{identifier}",
                            "**FIELD:                     1,INTENSITY",
                            "**UNITS:                     1,MM/HR",
                            "**FORMAT:                    2,F15.1,[5]",
                            "**RECORD_LENGTH:             I2,75",
                            "**CONSTANTS:                 35,LOCATION,0_ANT_RAIN,1_ANT_RAIN,2_ANT_RAIN,",
                            "*+                           3_ANT_RAIN,4_ANT_RAIN,5_ANT_RAIN,6_ANT_RAIN,",
                            "*+                           7_ANT_RAIN,8_ANT_RAIN,9_ANT_RAIN,10_ANT_RAIN,",
                            "*+                           11_ANT_RAIN,12_ANT_RAIN,13_ANT_RAIN,14_ANT_RAIN,",
                            "*+                           15_ANT_RAIN,16_ANT_RAIN,17_ANT_RAIN,18_ANT_RAIN,",
                            "*+                           19_ANT_RAIN,20_ANT_RAIN,21_ANT_RAIN,22_ANT_RAIN,",
                            "*+                           23_ANT_RAIN,24_ANT_RAIN,25_ANT_RAIN,26_ANT_RAIN,",
                            "*+                           27_ANT_RAIN,28_ANT_RAIN,29_ANT_RAIN,30_ANT_RAIN,",
                            "*+                           START,END,INTERVAL",
                            "**C_UNITS:                   35,,MM,MM,MM,MM,MM,MM,MM,MM,MM,MM,",
                            "*+                           MM,MM,MM,MM,MM,MM,MM,MM,MM,MM,MM,",
                            "*+                           MM,MM,MM,MM,MM,MM,MM,MM,MM,MM,GMT,GMT,MIN",
                            "**C_FORMAT:                  8,A20,F7.2/15F5.1/15F5.1/D10,2X,D10,I4",
                            "*CSTART",
                            "UNKNOWN                0.00",
                            " -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0",
                            " -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0 -1.0",
                            f"{start_date}  {end_date}    2",
                            "*CEND"])

        try:
            # Write the header and data
            with open(file_spec, 'w') as file:
                # Write header
                file.write(header + "\n")

                # Write DataFrame data (IntensityValues) in rows of 5 values each
                values = rg_inst.data['IntensityData'].tolist()
                for i in range(0, len(values), 5):
                    row = values[i:i+5]
                    file.write("".join(f"{value: >15.1f}" for value in row) + "\n")

                file.write("*END")
        except Exception as e:
            print(f"An error occurred: {e}")

    def review_fsm_interim_data_imports(self, interim_id):

        try:
            for a_inst in self.fsmProject.dict_fsm_installs.values():
                a_int_rev = self.fsmProject.get_interim_review(
                    interim_id=interim_id, install_id=a_inst.install_id)
                if not a_int_rev:
                    a_int_rev = fsmInterimReview()
                    a_int_rev.interim_review_id = self.fsmProject.get_next_interim_review_id()
                    a_int_rev.interim_id = interim_id
                    a_int_rev.install_id = a_inst.install_id
                    a_int_rev.dr_identifier = a_inst.client_ref
                    self.fsmProject.add_interim_review(a_int_rev)
                int_rev_id = a_int_rev.interim_review_id

                if a_inst.data is not None and not a_inst.data.empty:
                    if (a_inst.data_start <= self.fsmProject.dict_fsm_interims[interim_id].interim_start_date) and (a_inst.data_end >= self.fsmProject.dict_fsm_interims[interim_id].interim_end_date):
                        self.fsmProject.dict_fsm_interim_reviews[int_rev_id].dr_data_covered = True
                        self.fsmProject.dict_fsm_interim_reviews[int_rev_id].dr_ignore_missing = False
                        self.fsmProject.dict_fsm_interim_reviews[int_rev_id].dr_reason_missing = ""
                    else:
                        self.fsmProject.dict_fsm_interim_reviews[int_rev_id].dr_data_covered = False

            dlg_review_data = flowbot_dialog_fsm_interim_data_imports(
                self.fsmProject.filter_interim_reviews_by_interim_id(interim_id))
            dlg_review_data.setWindowTitle('Data Coverage Review')
            ret = dlg_review_data.exec_()
            if ret == QDialog.Accepted:
                self.fsmProject.dict_fsm_interims[interim_id].data_import_complete = dlg_review_data.dataReviewComplete
                self.update_fsm_project_standard_item_model()
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def update_fsm_data_classification(self, interim_id):

        try:
            a_int = self.fsmProject.dict_fsm_interims[interim_id]

            if a_int.data_import_complete:
                i_total = 0
                i_count = 0
                for a_inst in self.fsmProject.dict_fsm_installs.values():
                    if a_inst.data is not None and not a_inst.data.empty:
                        i_total += 1

                self.progressBar.setMinimum(0)
                self.progressBar.setMaximum(i_total)
                self.progressBar.setValue(0)
                self.progressBar.show()

                for a_inst in self.fsmProject.dict_fsm_installs.values():
                    if a_inst.data is not None and not a_inst.data.empty:
                        if a_inst.class_data_ml_date_updated <= a_inst.data_date_updated:
                            self.statusBar().showMessage('Classifying Data for ' +
                                                         a_inst.install_monitor_asset_id + '/' + a_inst.client_ref)
                            self.progressBar.setValue(i_count)
                            self._thisApp.processEvents()
                            i_count += 1
                            aDC = fsmDataClassification()
                            my_results = aDC.run_classification(a_inst)
                            if a_inst.class_data_ml is not None:
                                common_dates = my_results['Date'].isin(
                                    a_inst.class_data_ml['Date'])
                                filtered_my_results = my_results[~common_dates]
                                a_inst.class_data_ml = pd.concat(
                                    [a_inst.class_data_ml, filtered_my_results], ignore_index=True)
                                a_inst.class_data_ml.sort_values(
                                    by='Date', inplace=True)
                            else:
                                a_inst.class_data_ml = my_results
                            a_inst.class_data_ml_date_updated = datetime.now()
                        # pd.to_datetime(, format='%d/%m/%Y')

                self.statusBar().clearMessage()
                self.progressBar.hide()
                self._thisApp.processEvents()

                msg = QMessageBox(self)
                msg.setWindowIcon(self.myIcon)
                msg.information(self, 'Automated Classification',
                                'Automated classification is up to date', QMessageBox.Ok)

            else:
                msg = QMessageBox(self)
                msg.setWindowIcon(self.myIcon)
                msg.warning(self, 'Identify Storm Event',
                            'Data Import Review not complete', QMessageBox.Ok)

        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def review_fsm_interim_data_classification(self, interim_id):

        try:
            if self.fsmProject.dict_fsm_interims[interim_id].data_import_complete:
                # a_int_crs = self.fsmProject.filter_interim_classification_reviews_by_interim_id(interim_id)

                dlg_review = flowbot_dialog_fsm_review_classification(
                    interim_id, self.fsmProject)
                dlg_review.setWindowTitle('Review Data Classification')
                ret = dlg_review.exec_()
                if ret == QDialog.Accepted:
                    result = True
                    for a_int_cr in self.fsmProject.dict_fsm_interim_reviews.values():
                        if a_int_cr.interim_id == interim_id:
                            if not a_int_cr.cr_complete:
                                result = False
                                break

                    self.fsmProject.dict_fsm_interims[interim_id].data_classification_complete = result
                    self.update_fsm_project_standard_item_model()

            else:
                msg = QMessageBox(self)
                msg.setWindowIcon(self.myIcon)
                msg.critical(self, 'Data Classification',
                             'Data Import Review not complete', QMessageBox.Ok)
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def review_fsm_interim_identify_events(self, interim_id):

        try:
            if self.fsmProject.dict_fsm_interims[interim_id].data_import_complete:

                dlg_events = flowbot_dialog_fsm_storm_events(
                    self.fsmProject, interim_id)
                dlg_events.setWindowTitle('Identify Storm Events')

                ret = dlg_events.exec_()
                if ret == QDialog.Accepted:
                    result = True
                    for a_int_ser in self.fsmProject.dict_fsm_interim_reviews.values():
                        if a_int_ser.interim_id == interim_id:
                            if not a_int_ser.ser_complete:
                                result = False
                                break

                    self.fsmProject.dict_fsm_interims[interim_id].identify_events_complete = result
                    self.update_fsm_project_standard_item_model()
                    self.enable_fsm_menu()

            else:
                msg = QMessageBox(self)
                msg.setWindowIcon(self.myIcon)
                msg.warning(self, 'Identify Storm Event',
                            'Please review data imports first', QMessageBox.Ok)
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def review_fsm_interim_rg_data(self, interim_id):

        try:
            if self.fsmProject.dict_fsm_interims[interim_id].data_import_complete:

                dlg_review = flowbot_dialog_fsm_review_raingauge(
                    interim_id, self.fsmProject)
                dlg_review.setWindowTitle('Review Rain Gauge Data')
                ret = dlg_review.exec_()
                if ret == QDialog.Accepted:
                    result = True
                    for a_int_rg in self.fsmProject.dict_fsm_interim_reviews.values():
                        if a_int_rg.interim_id == interim_id:
                            if self.fsmProject.dict_fsm_installs[a_int_rg.install_id].install_type == 'Rain Gauge':
                                if not a_int_rg.rg_complete:
                                    result = False
                                    break

                    self.fsmProject.dict_fsm_interims[interim_id].rg_data_review_complete = result
                    self.update_fsm_project_standard_item_model()

            else:
                msg = QMessageBox(self)
                msg.setWindowIcon(self.myIcon)
                msg.critical(self, 'Rain Gauge Review',
                             'Interim Review not complete', QMessageBox.Ok)
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def review_fsm_interim_pl_data(self, interim_id):

        try:
            if self.fsmProject.dict_fsm_interims[interim_id].data_import_complete:

                dlg_review = flowbot_dialog_fsm_review_pumplogger(interim_id, self.fsmProject)
                dlg_review.setWindowTitle('Review Pump Logger Data')
                ret = dlg_review.exec_()
                if ret == QDialog.Accepted:
                    result = True
                    for a_int_pl in self.fsmProject.dict_fsm_interim_reviews.values():
                        if a_int_pl.interim_id == interim_id:
                            if self.fsmProject.dict_fsm_installs[a_int_pl.install_id].install_type == 'Pump Logger':
                                if not a_int_pl.pl_complete:
                                    result = False
                                    break

                    self.fsmProject.dict_fsm_interims[interim_id].pl_data_review_complete = result
                    self.update_fsm_project_standard_item_model()

            else:
                msg = QMessageBox(self)
                msg.setWindowIcon(self.myIcon)
                msg.critical(self, 'Pump Logger Review',
                             'Interim Review not complete', QMessageBox.Ok)
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def review_fsm_interim_fm_data(self, interim_id):

        try:
            if self.fsmProject.dict_fsm_interims[interim_id].data_import_complete:
                # a_int_crs = self.fsmProject.filter_interim_classification_reviews_by_interim_id(interim_id)

                dlg_review = flowbot_dialog_fsm_review_flowmonitor(
                    interim_id, self.fsmProject)
                dlg_review.setWindowTitle('Review Flow Monitor Data')
                ret = dlg_review.exec_()
                if ret == QDialog.Accepted:
                    result = True
                    for a_int_fm in self.fsmProject.dict_fsm_interim_reviews.values():
                        if a_int_fm.interim_id == interim_id:
                            if self.fsmProject.dict_fsm_installs[a_int_fm.install_id].install_type != 'Rain Gauge':
                                if not a_int_fm.fm_complete:
                                    result = False
                                    break

                    self.fsmProject.dict_fsm_interims[interim_id].fm_data_review_complete = result
                    self.update_fsm_project_standard_item_model()

            else:
                msg = QMessageBox(self)
                msg.setWindowIcon(self.myIcon)
                msg.critical(self, 'Flow Monitor Review',
                             'Interim Review not complete', QMessageBox.Ok)
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def review_fsm_interim_produce_interim_report(self, interim_id):

        try:
            a_int = self.fsmProject.dict_fsm_interims[interim_id]
            if all([
                    a_int.data_import_complete,
                    a_int.data_classification_complete,
                    a_int.fm_data_review_complete,
                    a_int.rg_data_review_complete,
                    a_int.identify_events_complete]):

                dlg_interim = flowbot_dialog_fsm_create_interim_report(
                    interim_id, self.fsmProject)
                dlg_interim.setWindowTitle('Interim Report Options')
                ret = dlg_interim.exec_()
                if ret == QDialog.Accepted:

                    self.statusBar().showMessage('Creating Interim Report: ')
                    self.progressBar.setMinimum(0)
                    self.progressBar.setValue(0)
                    self.progressBar.setMaximum(4)
                    self.progressBar.show()

                    output_paths = []

                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                        temp_pdf_path = temp_pdf.name

                    with PdfPages(temp_pdf_path) as pdf:
                        self.i_current_page_no = 0
                        if dlg_interim.chk_overall_summary.isChecked():
                            self.createReport_fsm_summary_for_interims(
                                interim_id, pdf)
                        if dlg_interim.chk_storm_events.isChecked():
                            self.createReport_fsm_storm_event_summary(
                                interim_id, pdf)
                        if dlg_interim.chk_data_classification.isChecked():
                            self.createReport_fsm_data_classification(
                                interim_id, pdf)
                        if dlg_interim.chk_fm_dm_summary.isChecked():
                            self.createReport_fsm_flow_monitor_summary(
                                interim_id, pdf)
                        if dlg_interim.chk_rg_summary.isChecked():
                            self.createReport_fsm_rain_gauge_summary(
                                interim_id, pdf)
                        if dlg_interim.chk_cumuative_install_summary.isChecked():
                            for a_inst in self.fsmProject.dict_fsm_installs.values():
                                self.createReport_fsm_cumulative_install_summaries(
                                    interim_id, a_inst, pdf)

                    output_pdf = os.path.join(dlg_interim.txt_output_folder.text(),
                                              f'{self.fsmProject.job_number} {self.fsmProject.job_name} Interim {self.fsmProject.dict_fsm_interims[interim_id].interim_id} Report.pdf')

                    if self.i_current_page_no > 0:
                        # Move the temporary PDF to the final location
                        shutil.move(temp_pdf_path, output_pdf)
                        output_paths.append(output_pdf)
                    else:
                        # No content was added, delete the temporary file
                        os.remove(temp_pdf_path)

                    appendix_count = 0

                    if dlg_interim.chk_raingauge_plots.isChecked():
                        # self.i_current_page_no = 0
                        appendix_count += 1
                        output_pdf = os.path.join(dlg_interim.txt_output_folder.text(),
                                                  f'Appendix {appendix_count} - Raingauge Plots.pdf')
                        output_paths.append(output_pdf)
                        self.createReport_fsm_raingauge_plots(
                            interim_id, output_pdf)

                    if dlg_interim.chk_fdv_plots.isChecked():
                        # self.i_current_page_no = 0
                        appendix_count += 1
                        output_pdf = os.path.join(dlg_interim.txt_output_folder.text(),
                                                  f'Appendix {appendix_count} - FDV Plots.pdf')
                        output_paths.append(output_pdf)
                        self.createReport_fsm_fdv_plots(interim_id, output_pdf)

                    if dlg_interim.chk_dwf_plots.isChecked():
                        # self.i_current_page_no = 0
                        appendix_count += 1
                        output_pdf = os.path.join(dlg_interim.txt_output_folder.text(),
                                                  f'Appendix {appendix_count} - DWF Plots.pdf')
                        output_paths.append(output_pdf)
                        self.createReport_fsm_dwf_plots(interim_id, output_pdf)

                    if dlg_interim.chk_scatter_plots.isChecked():
                        # self.i_current_page_no = 0
                        appendix_count += 1
                        output_pdf = os.path.join(dlg_interim.txt_output_folder.text(),
                                                  f'Appendix {appendix_count} - Scatter Plots.pdf')
                        output_paths.append(output_pdf)
                        self.createReport_fsm_scatter_plots(
                            interim_id, output_pdf)

                    if dlg_interim.chk_site_sheets.isChecked():
                        # self.i_current_page_no = 0
                        appendix_count += 1
                        output_pdf = os.path.join(dlg_interim.txt_output_folder.text(),
                                                  f'Appendix {appendix_count} - Site Sheets.pdf')
                        if self.createReport_fsm_site_sheets(interim_id, output_pdf):
                            output_paths.append(output_pdf)

                    if dlg_interim.chk_photographs.isChecked():
                        # self.i_current_page_no = 0
                        appendix_count += 1
                        output_pdf = os.path.join(dlg_interim.txt_output_folder.text(),
                                                  f'Appendix {appendix_count} - Photographs.pdf')
                        if self.createReport_fsm_photographs(interim_id, output_pdf):
                            output_paths.append(output_pdf)

                    for a_path in output_paths:
                        os.startfile(a_path)

            else:
                msg = QMessageBox(self)
                msg.setWindowIcon(self.myIcon)
                msg.critical(
                    self, 'Error', 'Interim Reviews are not Complete', QMessageBox.Ok)

        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def merge_fpdfs(self, pdf_objects, output_path):
        writer = PdfWriter()

        for pdf in pdf_objects:
            pdf_output = BytesIO(pdf.output(dest='S').encode('latin1'))
            reader = PdfReader(pdf_output)
            for page_num in range(len(reader.pages)):
                writer.add_page(reader.pages[page_num])

        with open(output_path, 'wb') as f_out:
            writer.write(f_out)

    def createReport_fsm_summary_for_interims(self, interim_id: int, pdf: PdfPages):

        self.statusBar().showMessage('Exporting Survey Summary')

        fig_width = 14.1
        fig_height = (fig_width * 10) / 14.1

        tempPW = PlotWidget(self, False, (fig_width, fig_height), dpi=100)

        self.i_current_page_no += 1
        tempGraph = graph_fsm_cumulative_interim_summary(
            tempPW, self.fsmProject, interim_id, f'Page {self.i_current_page_no}')
        tempGraph.update_plot()
        pdf.savefig(tempGraph.a_plot_widget.figure)

    def createReport_fsm_storm_event_summary(self, interim_id: int, pdf: PdfPages):

        self.statusBar().showMessage('Exporting Identified Storms')

        fig_width = 14.1
        fig_height = (fig_width * 10) / 14.1

        tempPW = PlotWidget(self, False, (fig_width, fig_height), dpi=100)

        self.i_current_page_no += 1
        tempGraph = graph_fsm_storm_event_summary(
            tempPW, self.fsmProject, interim_id, f'Page {self.i_current_page_no}')
        tempGraph.update_plot()
        pdf.savefig(tempGraph.a_plot_widget.figure)

    def createReport_fsm_data_classification(self, interim_id: int, pdf: PdfPages):

        self.statusBar().showMessage('Exporting Data Classification Summary')

        fig_width = 14.1
        fig_height = (fig_width * 10) / 14.1

        tempPW = PlotWidget(self, False, (fig_width, fig_height), dpi=100)

        self.i_current_page_no += 1
        tempGraph = graph_fsm_classification(
            tempPW, self.fsmProject, interim_id, f'Page {self.i_current_page_no}')
        tempGraph.update_plot()
        pdf.savefig(tempGraph.a_plot_widget.figure)

    def createReport_fsm_flow_monitor_summary(self, interim_id, pdf: PdfPages):

        self.statusBar().showMessage('Exporting FM Install Summary')

        fig_width = 14.1
        fig_height = (fig_width * 10) / 14.1

        tempPW = PlotWidget(self, False, (fig_width, fig_height), dpi=100)

        self.i_current_page_no += 1
        tempGraph = graph_fsm_fm_install_summary(
            tempPW, self.fsmProject, interim_id, f'Page {self.i_current_page_no}')
        tempGraph.update_plot()
        pdf.savefig(tempGraph.a_plot_widget.figure)

    def createReport_fsm_rain_gauge_summary(self, interim_id, pdf: PdfPages):

        self.statusBar().showMessage('Exporting RG Install Summary')

        fig_width = 14.1
        fig_height = (fig_width * 10) / 14.1

        tempPW = PlotWidget(self, False, (fig_width, fig_height), dpi=100)

        self.i_current_page_no += 1
        tempGraph = graph_fsm_rg_install_summary(
            tempPW, self.fsmProject, interim_id, f'Page {self.i_current_page_no}')
        tempGraph.update_plot()
        pdf.savefig(tempGraph.a_plot_widget.figure)

    def createReport_fsm_cumulative_install_summaries(self, interim_id, a_inst: fsmInstall, pdf: PdfPages):

        self.statusBar().showMessage('Exporting Cumulative Install Summary')

        fig_width = 14.1
        fig_height = (fig_width * 10) / 14.1

        tempPW = PlotWidget(self, False, (fig_width, fig_height), dpi=100)

        self.i_current_page_no += 1
        tempGraph = graph_fsm_monitor_data_summary(
            tempPW, self.fsmProject, interim_id, a_inst, f'Page {self.i_current_page_no}')
        tempGraph.update_plot()
        pdf.savefig(tempGraph.a_plot_widget.figure)

    def createReport_fsm_raingauge_plots(self, interim_id: int, output_pdf: str):

        self.statusBar().showMessage('Exporting Rain Gauge Plots')

        fig_width = 14.1
        fig_height = (fig_width * 10) / 14.1

        tempPW = PlotWidget(self, False, (fig_width, fig_height), dpi=100)

        with PdfPages(output_pdf) as pdf:
            i_pagecount = 0
            start_date = self.fsmProject.dict_fsm_interims[interim_id].interim_start_date
            end_date = self.fsmProject.dict_fsm_interims[interim_id].interim_end_date
            for a_inst in self.fsmProject.dict_fsm_installs.values():
                if a_inst.install_type == 'Rain Gauge':
                    i_pagecount += 1
                    tempGraph = graph_fsm_raingauge_plot(
                        tempPW, a_inst, start_date, end_date, f'Page {i_pagecount}')
                    tempGraph.update_plot()
                    pdf.savefig(tempGraph.a_plot_widget.figure)

    def createReport_fsm_fdv_plots(self, interim_id: int, output_pdf: str):

        self.statusBar().showMessage('Exporting FDV Plots')

        fig_width = 14.1
        fig_height = (fig_width * 10) / 14.1

        tempPW = PlotWidget(self, False, (fig_width, fig_height), dpi=100)

        with PdfPages(output_pdf) as pdf:
            i_pagecount = 0
            start_date = self.fsmProject.dict_fsm_interims[interim_id].interim_start_date
            end_date = self.fsmProject.dict_fsm_interims[interim_id].interim_end_date
            for a_inst in self.fsmProject.dict_fsm_installs.values():
                if a_inst.install_type != 'Rain Gauge':
                    i_pagecount += 1
                    tempGraph = graph_fsm_fdv_plot(
                        tempPW, a_inst, self.fsmProject, start_date, end_date, f'Page {i_pagecount}')
                    tempGraph.update_plot()
                    pdf.savefig(tempGraph.a_plot_widget.figure)

    def createReport_fsm_dwf_plots(self, interim_id: int, output_pdf: str):

        self.statusBar().showMessage('Exporting DWF Plots')

        fig_width = 14.1
        fig_height = (fig_width * 10) / 14.1

        tempPW = PlotWidget(self, False, (fig_width, fig_height), dpi=100)

        with PdfPages(output_pdf) as pdf:
            i_pagecount = 0
            start_date = self.fsmProject.dict_fsm_interims[interim_id].interim_start_date
            end_date = self.fsmProject.dict_fsm_interims[interim_id].interim_end_date
            for a_inst in self.fsmProject.dict_fsm_installs.values():
                if a_inst.install_type != 'Rain Gauge':
                    i_pagecount += 1
                    tempGraph = graph_fsm_dwf_plot(
                        tempPW, a_inst, self.fsmProject, start_date, end_date, f'Page {i_pagecount}')
                    tempGraph.update_plot()
                    pdf.savefig(tempGraph.a_plot_widget.figure)

    def createReport_fsm_scatter_plots(self, interim_id: int, output_pdf: str):

        self.statusBar().showMessage('Exporting Scatter Plots')

        fig_width = 14.1
        fig_height = (fig_width * 10) / 14.1

        tempPW = PlotWidget(self, False, (fig_width, fig_height), dpi=100)

        with PdfPages(output_pdf) as pdf:
            i_pagecount = 0
            start_date = self.fsmProject.dict_fsm_interims[interim_id].interim_start_date
            end_date = self.fsmProject.dict_fsm_interims[interim_id].interim_end_date
            for a_inst in self.fsmProject.dict_fsm_installs.values():
                if a_inst.install_type != 'Rain Gauge':
                    i_pagecount += 1
                    tempGraph = graph_fsm_scatter_plot(
                        tempPW, a_inst, self.fsmProject, start_date, end_date, f'Page {i_pagecount}')
                    tempGraph.update_plot()
                    pdf.savefig(tempGraph.a_plot_widget.figure)

    def createReport_fsm_site_sheets(self, interim_id: int, output_pdf: str) -> bool:

        self.statusBar().showMessage('Exporting Site Sheets')

        site_sheets = []
        start_date = self.fsmProject.dict_fsm_interims[interim_id].interim_start_date
        end_date = self.fsmProject.dict_fsm_interims[interim_id].interim_end_date
        for a_inst in self.fsmProject.dict_fsm_installs.values():
            if a_inst.install_date <= end_date:
                if isinstance(a_inst.install_sheet, bytes):  # Check if it's a bytes object
                    site_sheets.append(a_inst.install_sheet)
                for a_insp in self.fsmProject.dict_fsm_inspections.values():
                    if a_insp.install_id == a_inst.install_id:
                        if a_insp.inspection_date <= end_date:
                            # Check if it's a bytes object
                            if isinstance(a_insp.inspection_sheet, bytes):
                                site_sheets.append(a_insp.inspection_sheet)

        if len(site_sheets) > 0:
            # Create a PDF writer object
            pdf_writer = PdfWriter()

            # Iterate through the collected PDF BLOBs and add them to the writer
            for pdf_blob in site_sheets:
                pdf_reader = PdfReader(BytesIO(pdf_blob))
                for page_num in range(len(pdf_reader.pages)):
                    pdf_writer.add_page(pdf_reader.pages[page_num])

            # Write the collected pages to the output PDF file
            with open(output_pdf, 'wb') as out_pdf_file:
                pdf_writer.write(out_pdf_file)

            return True

    def createReport_fsm_photographs(self, interim_id: int, output_pdf: str) -> bool:

        self.statusBar().showMessage('Exporting Photographs')

        photos = []
        # start_date = self.fsmProject.dict_fsm_interims[interim_id].interim_start_date
        end_date = self.fsmProject.dict_fsm_interims[interim_id].interim_end_date

        # Collect photographs
        for a_inst in self.fsmProject.dict_fsm_installs.values():
            if a_inst.install_date <= end_date:
                for picture in self.fsmProject.dict_fsm_install_pictures.values():
                    if picture.install_id == a_inst.install_id:
                        if picture.picture_taken_date <= end_date and picture.picture is not None:
                            photos.append(picture.picture)

        if len(photos) > 0:
            # Create PDF canvas in landscape mode with A4 size
            c = canvas.Canvas(output_pdf, pagesize=landscape(A4))

            # Calculate number of pages needed
            no_of_cols = 3
            no_of_rows = 2
            num_photos_per_page = no_of_cols * no_of_rows
            num_photos = len(photos)
            num_pages = (num_photos + num_photos_per_page -
                         1) // num_photos_per_page  # Ceiling division

            # Define header and footer properties
            header_text = "Photographs Report"
            footer_text = "Page {}/{}".format("{}", num_pages)

            header_height = 1 * cm
            footer_height = 1 * cm
            page_margin = 1 * cm
            pic_margin = 1 * cm

            # height less footer and header
            available_width = A4[1] - (2 * page_margin)
            # height less footer and header
            available_height = A4[0] - (header_height + footer_height)

            pic_col_width = available_width / no_of_cols
            pic_row_height = available_height / no_of_rows

            # Iterate through pages
            for page in range(num_pages):
                # Draw header
                c.setFont("Helvetica-Bold", 16)
                c.drawCentredString(A4[1] / 2, A4[0] -
                                    header_height, header_text)

                # Draw footer
                c.setFont("Helvetica", 10)
                c.drawRightString(
                    A4[1] - 2.5 * cm, footer_height, footer_text.format(page + 1))

                # Draw photos on the page
                for i in range(num_photos_per_page):
                    index = page * num_photos_per_page + i
                    if index < num_photos:
                        photo_bytes = photos[index]
                        try:
                            img = Image.open(BytesIO(photo_bytes))
                            img_width, img_height = img.size
                            # Divide A4 landscape width into columns with margins on each side
                            max_width = pic_col_width - (pic_margin * 2)
                            # Divide A4 landscape height into rows with margins at the top and bottom
                            max_height = pic_row_height - (pic_margin * 2)
                            ratio = min(max_width / img_width,
                                        max_height / img_height)
                            col = i % no_of_cols
                            row = i // no_of_cols
                            reversed_row = no_of_rows - 1 - row
                            x = page_margin + \
                                (col * pic_col_width) + pic_margin
                            y = header_height + \
                                (reversed_row * pic_row_height) + pic_margin
                            # y = footer_height + (row * pic_row_height) + pic_margin
                            c.drawInlineImage(
                                img, x, y, img_width * ratio, img_height * ratio)
                        except Exception as e:
                            print(f"Error processing image: {e}")

                c.showPage()

            # Save PDF
            c.save()

            return True

    def add_fsm_interim(self):

        try:
            dlgInterimDates = flowbot_dialog_fsm_set_interim_dates()
            dlgInterimDates.txt_interim_id.setText(
                str(self.fsmProject.get_next_interim_id()))
            dlgInterimDates.dte_interim_start.setDateTime(
                QDateTime(self.fsmProject.get_next_interim_date()))
            dlgInterimDates.dte_interim_end.setDateTime(
                dlgInterimDates.dte_interim_start.dateTime().addDays(7))
            dlgInterimDates.setWindowTitle('Create Interim')
            # dlgInterimDates.show()
            ret = dlgInterimDates.exec_()
            if ret == QDialog.Accepted:
                a_int = fsmInterim()
                a_int.interim_id = int(dlgInterimDates.txt_interim_id.text())
                a_int.interim_start_date = dlgInterimDates.dte_interim_start.dateTime().toPyDateTime()
                a_int.interim_end_date = dlgInterimDates.dte_interim_end.dateTime().toPyDateTime()

                self.fsmProject.add_interim(a_int)

                self.update_fsm_project_standard_item_model()
                self.enable_fsm_menu()

        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def edit_fsm_interim(self, interim_id: int):

        try:
            dlgInterimDates = flowbot_dialog_fsm_set_interim_dates()

            dlgInterimDates.txt_interim_id.setText(
                str(self.fsmProject.dict_fsm_interims[interim_id].interim_id))
            dlgInterimDates.dte_interim_start.setDateTime(
                QDateTime(self.fsmProject.dict_fsm_interims[interim_id].interim_start_date))
            dlgInterimDates.dte_interim_end.setDateTime(
                QDateTime(self.fsmProject.dict_fsm_interims[interim_id].interim_end_date))
            dlgInterimDates.setWindowTitle('Edit Interim')
            # dlgInterimDates.show()
            ret = dlgInterimDates.exec_()
            if ret == QDialog.Accepted:
                self.fsmProject.dict_fsm_interims[interim_id].interim_start_date = dlgInterimDates.dte_interim_start.dateTime(
                ).toPyDateTime()
                self.fsmProject.dict_fsm_interims[interim_id].interim_end_date = dlgInterimDates.dte_interim_end.dateTime(
                ).toPyDateTime()
                self.update_fsm_project_standard_item_model()
                self.enable_fsm_menu()
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def add_fsm_install(self, site_id: Optional[str], monitor_id: Optional[str]):

        try:
            site = None
            monitor = None

            if site_id is not None:
                site = self.fsmProject.dict_fsm_sites[site_id]

            if monitor_id is not None:
                monitor = self.fsmProject.dict_fsm_monitors[monitor_id]

            dlg_inst = flowbot_dialog_fsm_install(self, self.fsmProject, None, monitor, site)
            dlg_inst.setWindowTitle('New Install')
            ret = dlg_inst.exec_()

            if ret == QDialog.Accepted:

                inst = fsmInstall()

                inst.install_id = dlg_inst.txt_install_id.text()
                inst.install_site_id = dlg_inst.a_site.siteID
                inst.install_monitor_asset_id = dlg_inst.a_mon.monitor_asset_id
                inst.install_type = dlg_inst.install_type
                inst.client_ref = dlg_inst.txt_client_ref.text() or ''
                inst.install_date = dlg_inst.dte_install_date.dateTime().toPyDateTime()

                # if (dlg_inst.install_type == 'Flow Monitor') or (dlg_inst.install_type == 'Depth Monitor'):
                if dlg_inst.install_type in ['Flow Monitor', 'Depth Monitor', 'Pump Logger']:
                    inst.fm_pipe_letter = dlg_inst.cbo_fm_pipe_letter.currentText() or ''
                    inst.fm_pipe_shape = dlg_inst.cbo_fm_pipe_shape.currentText() or ''
                    inst.fm_pipe_height_mm = int(
                        dlg_inst.txt_fm_pipe_height_mm.text() or '0')
                    inst.fm_pipe_width_mm = int(
                        dlg_inst.txt_fm_pipe_width_mm.text() or '0')
                    inst.fm_pipe_depth_to_invert_mm = int(
                        dlg_inst.txt_fm_pipe_depth_to_invert_mm.text() or 0)
                    inst.fm_sensor_offset_mm = int(
                        dlg_inst.txt_fm_sensor_offset_mm.text() or 0)
                else:
                    inst.rg_position = dlg_inst.cbo_rg_position.currentText()

                inst.install_sheet = dlg_inst.install_sheet
                inst.install_sheet_filename = dlg_inst.txt_install_sheet.text()

                self.fsmProject.dict_fsm_installs[inst.install_id] = inst

            self.update_fsm_project_standard_item_model()
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def edit_fsm_install(self, a_inst: fsmInstall):

        try:
            # site = self.fsmProject.dict_fsm_sites[a_inst.install_site_id]
            # monitor = self.fsmProject.dict_fsm_monitors[a_inst.install_monitor_asset_id]

            # if site_id is not None:
            #     a_inst = self.fsmProject.get_install_by_site(site_id)
            #     site = self.fsmProject.dict_fsm_sites[site_id]
            #     monitor = self.fsmProject.dict_fsm_monitors[a_inst.install_monitor_asset_id]

            # if monitor_id is not None:
            #     a_inst = self.fsmProject.get_install_by_monitor(monitor_id)
            #     monitor = self.fsmProject.dict_fsm_monitors[monitor_id]
            #     site = self.fsmProject.dict_fsm_sites[a_inst.install_site_id]

            # dlg_inst = flowbot_dialog_fsm_install(self, self.fsmProject, True, monitor, site)
            dlg_inst = flowbot_dialog_fsm_install(self, self.fsmProject, a_inst)
            dlg_inst.setWindowTitle('Edit Install')
            ret = dlg_inst.exec_()

            if ret == QDialog.Accepted:

                if dlg_inst.txt_install_id.text() != a_inst.install_id:
                    if self.fsmProject.update_install_id(a_inst.install_id, dlg_inst.txt_install_id.text()):
                        del self.fsmProject.dict_fsm_installs[a_inst.install_id]
                        a_inst.install_id = dlg_inst.txt_install_id.text()

                a_inst.client_ref = dlg_inst.txt_client_ref.text() or ''
                a_inst.install_date = dlg_inst.dte_install_date.dateTime().toPyDateTime()

                if (dlg_inst.install_type == 'Flow Monitor') or (dlg_inst.install_type == 'Depth Monitor'):
                    a_inst.fm_pipe_letter = dlg_inst.cbo_fm_pipe_letter.currentText() or ''
                    a_inst.fm_pipe_shape = dlg_inst.cbo_fm_pipe_shape.currentText() or ''
                    a_inst.fm_pipe_height_mm = int(
                        dlg_inst.txt_fm_pipe_height_mm.text() or '0')
                    a_inst.fm_pipe_width_mm = int(
                        dlg_inst.txt_fm_pipe_width_mm.text() or '0')
                    a_inst.fm_pipe_depth_to_invert_mm = int(
                        dlg_inst.txt_fm_pipe_depth_to_invert_mm.text() or 0)
                    a_inst.fm_sensor_offset_mm = int(
                        dlg_inst.txt_fm_sensor_offset_mm.text() or 0)
                else:
                    a_inst.rg_position = dlg_inst.cbo_rg_position.currentText()

                a_inst.install_sheet = dlg_inst.install_sheet
                a_inst.install_sheet_filename = dlg_inst.txt_install_sheet.text()

                self.fsmProject.dict_fsm_installs[a_inst.install_id] = a_inst

            self.update_fsm_project_standard_item_model()

        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    # def edit_fsm_install(self, site_id: Optional[str], monitor_id: Optional[str]):

    #     try:
    #         site = None
    #         monitor = None

    #         if site_id is not None:
    #             a_inst = self.fsmProject.get_install_by_site(site_id)
    #             site = self.fsmProject.dict_fsm_sites[site_id]
    #             monitor = self.fsmProject.dict_fsm_monitors[a_inst.install_monitor_asset_id]

    #         if monitor_id is not None:
    #             a_inst = self.fsmProject.get_install_by_monitor(monitor_id)
    #             monitor = self.fsmProject.dict_fsm_monitors[monitor_id]
    #             site = self.fsmProject.dict_fsm_sites[a_inst.install_site_id]

    #         dlg_inst = flowbot_dialog_fsm_install(
    #             self, self.fsmProject, True, monitor, site)
    #         dlg_inst.setWindowTitle('Edit Install')
    #         ret = dlg_inst.exec_()

    #         if ret == QDialog.Accepted:

    #             a_inst.client_ref = dlg_inst.txt_client_ref.text() or ''
    #             a_inst.install_date = dlg_inst.dte_install_date.dateTime().toPyDateTime()

    #             if (dlg_inst.install_type == 'Flow Monitor') or (dlg_inst.install_type == 'Depth Monitor'):
    #                 a_inst.fm_pipe_letter = dlg_inst.cbo_fm_pipe_letter.currentText() or ''
    #                 a_inst.fm_pipe_shape = dlg_inst.cbo_fm_pipe_shape.currentText() or ''
    #                 a_inst.fm_pipe_height_mm = int(
    #                     dlg_inst.txt_fm_pipe_height_mm.text() or '0')
    #                 a_inst.fm_pipe_width_mm = int(
    #                     dlg_inst.txt_fm_pipe_width_mm.text() or '0')
    #                 a_inst.fm_pipe_depth_to_invert_mm = int(
    #                     dlg_inst.txt_fm_pipe_depth_to_invert_mm.text() or 0)
    #                 a_inst.fm_sensor_offset_mm = int(
    #                     dlg_inst.txt_fm_sensor_offset_mm.text() or 0)
    #             else:
    #                 a_inst.rg_position = dlg_inst.cbo_rg_position.currentText()

    #             a_inst.install_sheet = dlg_inst.install_sheet
    #             a_inst.install_sheet_filename = dlg_inst.txt_install_sheet.text()

    #             self.fsmProject.dict_fsm_installs[a_inst.install_id] = a_inst

    #         self.update_fsm_project_standard_item_model()

    #     except Exception as e:
    #         logger.error('Exception occurred', exc_info=True)
    #         msg = QMessageBox(self)
    #         msg.critical(
    #             self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def delete_fsm_install(self, a_inst: fsmInstall):

        try:
            # site = None
            # monitor = None

            # if site_id is not None:
            #     a_inst = self.fsmProject.get_install_by_site(site_id)
            #     site = self.fsmProject.dict_fsm_sites[site_id]
            #     monitor = self.fsmProject.dict_fsm_monitors[a_inst.install_monitor_asset_id]

            # if monitor_id is not None:
            #     a_inst = self.fsmProject.get_install_by_monitor(monitor_id)
            #     monitor = self.fsmProject.dict_fsm_monitors[monitor_id]
            #     site = self.fsmProject.dict_fsm_sites[a_inst.install_site_id]

            # Add confirmation message box
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Confirm Deletion")
            msg_box.setText(
                "Are you sure you want to delete this install record?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            response = msg_box.exec_()

            if response == QMessageBox.Yes:
                # Proceed with deletion
                self.fsmProject.delete_install(a_inst.install_id)
                self.update_fsm_project_standard_item_model()

        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def add_fsm_monitor(self):

        try:
            dlg_add_monitor = flowbot_dialog_fsm_add_monitor(self)
            dlg_add_monitor.setWindowTitle('Add Monitor')
            ret = dlg_add_monitor.exec_()
            if ret == QDialog.Accepted:

                aMon = fsmMonitor()
                aMon.monitor_asset_id = dlg_add_monitor.txt_asset_id.text()
                aMon.monitor_type = dlg_add_monitor.cbo_monitor_type.currentText()
                aMon.monitor_sub_type = dlg_add_monitor.cbo_subtype.currentText()
                aMon.pmac_id = dlg_add_monitor.txt_pmac_id.text()

                if not self.fsmProject.add_monitor(aMon):
                    msg = QMessageBox(self)
                    msg.setWindowIcon(self.myIcon)
                    msg.critical(
                        self, 'Install Monitor', 'A monitor with that ID already exists', QMessageBox.Ok)

                self.update_fsm_project_standard_item_model()
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def edit_fsm_monitor(self, monitor_id: str):

        try:
            dlg_edit = flowbot_dialog_fsm_add_monitor()

            dlg_edit.setWindowTitle('Edit Monitor')

            if not self.fsmProject.monitor_is_installed(monitor_id):

                dlg_edit.txt_asset_id.setText(
                    self.fsmProject.dict_fsm_monitors[monitor_id].monitor_asset_id)
                dlg_edit.txt_asset_id.setEnabled(False)

                dlg_edit.cbo_monitor_type.setCurrentText(
                    self.fsmProject.dict_fsm_monitors[monitor_id].monitor_type)
                dlg_edit.cbo_monitor_type.setCurrentText(
                    self.fsmProject.dict_fsm_monitors[monitor_id].monitor_type)
                dlg_edit.cbo_subtype.setCurrentText(
                    self.fsmProject.dict_fsm_monitors[monitor_id].monitor_sub_type)
                dlg_edit.txt_pmac_id.setText(
                    self.fsmProject.dict_fsm_monitors[monitor_id].pmac_id)

                ret = dlg_edit.exec_()
                if ret == QDialog.Accepted:

                    self.fsmProject.dict_fsm_monitors[monitor_id].monitor_type = dlg_edit.cbo_monitor_type.currentText(
                    )
                    self.fsmProject.dict_fsm_monitors[monitor_id].monitor_sub_type = dlg_edit.cbo_subtype.currentText(
                    )
                    self.fsmProject.dict_fsm_monitors[monitor_id].pmac_id = dlg_edit.txt_pmac_id.text(
                    )

                    self.update_fsm_project_standard_item_model()
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def add_fsm_install_photographs(self, a_inst: fsmInstall):

        try:
            # a_inst = None

            # if site_id is not None:
            #     # site = self.fsmProject.dict_fsm_sites[site_id]
            #     a_inst = self.fsmProject.get_install_by_site(site_id)

            # if monitor_id is not None:
            #     # monitor = self.fsmProject.dict_fsm_monitors[monitor_id]
            #     a_inst = self.fsmProject.get_install_by_monitor(monitor_id)

            dlg_insp = flowbot_dialog_fsm_view_photographs(
                None, self.fsmProject, a_inst.install_id)
            dlg_insp.setWindowTitle(
                f'Install Photographs: {a_inst.install_monitor_asset_id}/{a_inst.client_ref}')

            ret = dlg_insp.exec_()
            if ret == QDialog.Accepted:
                pass

            self.update_fsm_project_standard_item_model()
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def add_fsm_inspection(self, a_inst: fsmInstall):

        try:
            # a_inst = None

            # if site_id is not None:
            #     # site = self.fsmProject.dict_fsm_sites[site_id]
            #     a_inst = self.fsmProject.get_install_by_site(site_id)

            # if monitor_id is not None:
            #     # monitor = self.fsmProject.dict_fsm_monitors[monitor_id]
            #     a_inst = self.fsmProject.get_install_by_monitor(monitor_id)

            dlg_insp = flowbot_dialog_fsm_add_inspection()
            dlg_insp.setWindowTitle(
                f'Add Inspection: {a_inst.install_monitor_asset_id}/{a_inst.client_ref}')
            dlg_insp.dte_inspection_date.setDateTime(
                QDateTime(a_inst.install_date))
            # dlg_insp.dte_install_date.setEnabled(False)
            dlg_insp.dte_inspection_date.setMinimumDateTime(
                QDateTime(a_inst.install_date))
            ret = dlg_insp.exec_()
            if ret == QDialog.Accepted:

                a_insp = fsmInspection()
                a_insp.inspection_id = self.fsmProject.get_next_inspection_id()
                a_insp.install_id = a_inst.install_id
                a_insp.inspection_date = dlg_insp.dte_inspection_date.dateTime().toPyDateTime()
                a_insp.inspection_sheet = dlg_insp.inspection_sheet
                a_insp.inspection_sheet_filename = dlg_insp.txt_inspection_sheet.text()
                a_insp.inspection_type = "Inspection"

                self.fsmProject.dict_fsm_inspections[a_insp.inspection_id] = a_insp

            self.update_fsm_project_standard_item_model()
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    # def add_fsm_inspection(self, site_id: Optional[str], monitor_id: Optional[str]):

    #     try:
    #         a_inst = None

    #         if site_id is not None:
    #             # site = self.fsmProject.dict_fsm_sites[site_id]
    #             a_inst = self.fsmProject.get_install_by_site(site_id)

    #         if monitor_id is not None:
    #             # monitor = self.fsmProject.dict_fsm_monitors[monitor_id]
    #             a_inst = self.fsmProject.get_install_by_monitor(monitor_id)

    #         dlg_insp = flowbot_dialog_fsm_add_inspection()
    #         dlg_insp.setWindowTitle(
    #             f'Add Inspection: {a_inst.install_monitor_asset_id}/{a_inst.client_ref}')
    #         dlg_insp.dte_inspection_date.setDateTime(
    #             QDateTime(a_inst.install_date))
    #         # dlg_insp.dte_install_date.setEnabled(False)
    #         dlg_insp.dte_inspection_date.setMinimumDateTime(
    #             QDateTime(a_inst.install_date))
    #         ret = dlg_insp.exec_()
    #         if ret == QDialog.Accepted:

    #             a_insp = fsmInspection()
    #             a_insp.inspection_id = self.fsmProject.get_next_inspection_id()
    #             a_insp.install_id = a_inst.install_id
    #             a_insp.inspection_date = dlg_insp.dte_inspection_date.dateTime().toPyDateTime()
    #             a_insp.inspection_sheet = dlg_insp.inspection_sheet
    #             a_insp.inspection_sheet_filename = dlg_insp.txt_inspection_sheet.text()
    #             a_insp.inspection_type = "Inspection"

    #             self.fsmProject.dict_fsm_inspections[a_insp.inspection_id] = a_insp

    #         self.update_fsm_project_standard_item_model()
    #     except Exception as e:
    #         logger.error('Exception occurred', exc_info=True)
    #         msg = QMessageBox(self)
    #         msg.critical(
    #             self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def uninstall_fsm_monitor(self, a_inst: fsmInstall):

        try:
            # a_inst = self.fsmProject.get_install_by_monitor(monitor_id)
            dlg_uninst = flowbot_dialog_fsm_uninstall()
            dlg_uninst.setWindowTitle(
                f'Uninstall {a_inst.install_type}: {a_inst.install_monitor_asset_id}/{a_inst.client_ref}')
            dlg_uninst.dte_install_date.setDateTime(
                QDateTime(a_inst.install_date))
            dlg_uninst.dte_install_date.setEnabled(False)
            dlg_uninst.dte_uninstall_date.setMinimumDateTime(
                QDateTime(a_inst.install_date))
            ret = dlg_uninst.exec_()
            if ret == QDialog.Accepted:

                a_inst.remove_date = dlg_uninst.dte_uninstall_date.dateTime().toPyDateTime()

                insp = fsmInspection()
                insp.inspection_id = self.fsmProject.get_next_inspection_id()
                insp.install_id = a_inst.install_id
                insp.inspection_date = dlg_uninst.dte_uninstall_date.dateTime().toPyDateTime()
                insp.inspection_sheet = dlg_uninst.inspection_sheet
                insp.inspection_sheet_filename = dlg_uninst.txt_inspection_sheet.text()
                insp.inspection_type = "Uninstall"

                self.fsmProject.dict_fsm_inspections[insp.inspection_id] = insp

            self.update_fsm_project_standard_item_model()
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    # def uninstall_fsm_monitor(self, monitor_id: str):

    #     try:
    #         # a_inst = self.fsmProject.get_install_by_monitor(monitor_id)
    #         a_inst = self.fsmProject.get_current_install_by_monitor(monitor_id)

    #         dlg_uninst = flowbot_dialog_fsm_uninstall()
    #         dlg_uninst.setWindowTitle(
    #             f'Uninstall {a_inst.install_type}: {a_inst.install_monitor_asset_id}/{a_inst.client_ref}')
    #         dlg_uninst.dte_install_date.setDateTime(
    #             QDateTime(a_inst.install_date))
    #         dlg_uninst.dte_install_date.setEnabled(False)
    #         dlg_uninst.dte_uninstall_date.setMinimumDateTime(
    #             QDateTime(a_inst.install_date))
    #         ret = dlg_uninst.exec_()
    #         if ret == QDialog.Accepted:

    #             a_inst.remove_date = dlg_uninst.dte_uninstall_date.dateTime().toPyDateTime()

    #             insp = fsmInspection()
    #             insp.inspection_id = self.fsmProject.get_next_inspection_id()
    #             insp.install_id = a_inst.install_id
    #             insp.inspection_date = dlg_uninst.dte_uninstall_date.dateTime().toPyDateTime()
    #             insp.inspection_sheet = dlg_uninst.inspection_sheet
    #             insp.inspection_sheet_filename = dlg_uninst.txt_inspection_sheet.text()
    #             insp.inspection_type = "Uninstall"

    #             self.fsmProject.dict_fsm_inspections[insp.inspection_id] = insp

    #         self.update_fsm_project_standard_item_model()
    #     except Exception as e:
    #         logger.error('Exception occurred', exc_info=True)
    #         msg = QMessageBox(self)
    #         msg.critical(
    #             self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def delete_fsm_monitor(self, monitor_id: str):

        try:
            self.fsmProject.remove_monitor(monitor_id)
            self.update_fsm_project_standard_item_model()
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def edit_fsm_site(self, site_id: str):

        try:
            dlg_edit_site = flowbot_dialog_fsm_add_site(self)
            dlg_edit_site.setWindowTitle('Edit Site')
            dlg_edit_site.txtSiteRefNo.setText(site_id)
            dlg_edit_site.cboSiteType.setCurrentText(
                self.fsmProject.dict_fsm_sites[site_id].siteType)
            dlg_edit_site.pteAddress.setPlainText(
                self.fsmProject.dict_fsm_sites[site_id].address)
            dlg_edit_site.txt_mh_ref.setText(
                self.fsmProject.dict_fsm_sites[site_id].mh_ref)
            dlg_edit_site.txtW3W.setText(
                self.fsmProject.dict_fsm_sites[site_id].w3w)
            dlg_edit_site.txt_easting.setText(
                str(self.fsmProject.dict_fsm_sites[site_id].easting))
            dlg_edit_site.txt_northing.setText(
                str(self.fsmProject.dict_fsm_sites[site_id].northing))
            dlg_edit_site.txtSiteRefNo.setEnabled(False)
            if self.fsmProject.get_install_by_site(site_id) is not None:
                dlg_edit_site.cboSiteType.setEnabled(False)
            ret = dlg_edit_site.exec_()
            if ret == QDialog.Accepted:

                # new_site = fsmSite()
                # new_site.siteID = site_id
                self.fsmProject.dict_fsm_sites[site_id].siteType = dlg_edit_site.cboSiteType.currentText(
                )
                self.fsmProject.dict_fsm_sites[site_id].address = dlg_edit_site.pteAddress.toPlainText(
                )
                self.fsmProject.dict_fsm_sites[site_id].mh_ref = dlg_edit_site.txt_mh_ref.text(
                )
                self.fsmProject.dict_fsm_sites[site_id].w3w = dlg_edit_site.txtW3W.text(
                )
                try:
                    self.fsmProject.dict_fsm_sites[site_id].easting = float(
                        dlg_edit_site.txt_easting.text())
                except ValueError as e:
                    self.fsmProject.dict_fsm_sites[site_id].easting = 0.0
                try:
                    self.fsmProject.dict_fsm_sites[site_id].northing = float(
                        dlg_edit_site.txt_northing.text())
                except ValueError as e:
                    self.fsmProject.dict_fsm_sites[site_id].northing = 0.0

                self.update_fsm_project_standard_item_model()
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def add_fsm_site(self):

        try:
            dlg_add_site = flowbot_dialog_fsm_add_site(self)
            dlg_add_site.setWindowTitle('Add Site')
            # dlg_add_site.show()
            ret = dlg_add_site.exec_()
            if ret == QDialog.Accepted:

                aSite = fsmSite()
                aSite.siteID = dlg_add_site.txtSiteRefNo.text()
                aSite.siteType = dlg_add_site.cboSiteType.currentText()
                aSite.address = dlg_add_site.pteAddress.toPlainText()
                aSite.mh_ref = dlg_add_site.txt_mh_ref.text()
                aSite.w3w = dlg_add_site.txtW3W.text()
                try:
                    aSite.easting = float(dlg_add_site.txt_easting.text())
                except ValueError as e:
                    aSite.easting = 0.0
                try:
                    aSite.northing = float(dlg_add_site.txt_northing.text())
                except ValueError as e:
                    aSite.northing = 0.0
                self.fsmProject.add_site(aSite)

                self.update_fsm_project_standard_item_model()
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    # def fsm_import_data_pmac(self):

    #     try:
    #         file_path = QtWidgets.QFileDialog.getExistingDirectory(
    #             self, "Select PMAC Server Download Directory:", self.lastOpenDialogPath,
    #             QtWidgets.QFileDialog.ShowDirsOnly)
    #         if len(file_path) == 0:
    #             return
    #         self.lastOpenDialogPath = file_path

    #         # site_ids = []
    #         for a_site in self.fsmProject.dict_fsm_sites.values():
    #             if a_site.installed:
    #                 for a_mon in self.fsmProject.dict_fsm_monitors.values():
    #                     if a_mon.install_site == a_site.siteID:
    #                         if a_site.siteType in ["Flow Monitor", "Depth Monitor"]:
    #                             file_spec = os.path.join(
    #                                 file_path, f"{a_mon.pmac_id}_06.dat")
    #                             if os.path.exists(file_spec):
    #                                 file_data = self.read_06_depth_file(
    #                                     file_spec)
    #                             file_spec = os.path.join(
    #                                 file_path, f"{a_mon.pmac_id}_07.dat")
    #                             if os.path.exists(file_spec):
    #                                 file_data = self.read_06_depth_file(
    #                                     file_spec)
    #                             file_spec = os.path.join(
    #                                 file_path, f"{a_mon.pmac_id}_08.dat")
    #                             if os.path.exists(file_spec):
    #                                 file_data = self.read_06_depth_file(
    #                                     file_spec)
    #                         # if a_site.siteType in ["Rain Gauge"]:
    #                         #     file_spec = os.path.join(
    #                         #         file_path, f"{a_mon.pmac_id}_06.dat")
    #                         #     if os.path.exists(file_spec):
    #                         #         file_data = self.read_06_depth_file(
    #                         #             file_spec)
    #     except Exception as e:
    #         logger.error('Exception occurred', exc_info=True)
    #         msg = QMessageBox(self)
    #         msg.critical(
    #             self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    # try:
    #     file_path = QtWidgets.QFileDialog.getExistingDirectory(
    #         self, "Select Raw Data Directory:", self.lastOpenDialogPath,
    #         QtWidgets.QFileDialog.ShowDirsOnly)
    #     if len(file_path) == 0:
    #         return
    #     self.lastOpenDialogPath = file_path

    #     for a_inst in self.fsmProject.dict_fsm_installs.values():
    #         if a_inst.install_type in ["Flow Monitor", "Depth Monitor"]:
    #             file_spec = os.path.join(
    #                 file_path, f"{self.fsmProject.get_monitor(a_inst.install_monitor_asset_id).pmac_id}.fdv")
    #             if os.path.exists(file_spec):
    #                 a_inst.get_fdv_data_from_file(file_spec)

    #     self.update_fsm_project_standard_item_model()
    # except Exception as e:
    #     logger.error('Exception occurred', exc_info=True)
    #     msg = QMessageBox(self)
    #     msg.critical(
    #         self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def fsm_import_data_fdv(self):
        try:
            file_path = QtWidgets.QFileDialog.getExistingDirectory(
                self, "Select FDV Directory:", self.lastOpenDialogPath,
                QtWidgets.QFileDialog.ShowDirsOnly)
            if len(file_path) == 0:
                return
            self.lastOpenDialogPath = file_path

            for a_inst in self.fsmProject.dict_fsm_installs.values():
                if a_inst.install_type in ["Flow Monitor", "Depth Monitor"]:
                    file_spec = os.path.join(
                        file_path, f"{self.fsmProject.get_monitor(a_inst.install_monitor_asset_id).pmac_id}.fdv")
                    if os.path.exists(file_spec):
                        a_inst.get_fdv_data_from_file(file_spec)

            self.update_fsm_project_standard_item_model()
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def fsm_import_data_r(self):

        try:
            file_path = QtWidgets.QFileDialog.getExistingDirectory(
                self, "Select R Directory:", self.lastOpenDialogPath,
                QtWidgets.QFileDialog.ShowDirsOnly)
            if len(file_path) == 0:
                return
            self.lastOpenDialogPath = file_path

            for a_inst in self.fsmProject.dict_fsm_installs.values():
                if a_inst.install_type == "Rain Gauge":
                    file_spec = os.path.join(
                        file_path, f"{self.fsmProject.get_monitor(a_inst.install_monitor_asset_id).pmac_id}.r")
                    if os.path.exists(file_spec):
                        a_inst.get_r_data_from_file(file_spec)

            self.update_fsm_project_standard_item_model()
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def add_fsm_data(self, inst: fsmInstall):

        try:
            if inst.install_type == "Rain Gauge":
                file_spec, _ = QtWidgets.QFileDialog.getOpenFileName(
                    None, "Open Rain Gauge Data File", "", "Rain Gauge Data files (*.r)")
                if not file_spec:
                    return
                if os.path.exists(file_spec):
                    self.lastOpenDialogPath = os.path.dirname(file_spec)
                    inst.get_r_data_from_file(file_spec)

            if inst.install_type in ["Flow Monitor", "Depth Monitor"]:
                file_spec, _ = QtWidgets.QFileDialog.getOpenFileName(
                    None, "Open Flow Monitor Data File", "", "Flow Monitor Data files (*.fdv)")
                if not file_spec:
                    return
                if os.path.exists(file_spec):
                    self.lastOpenDialogPath = os.path.dirname(file_spec)
                    inst.get_fdv_data_from_file(file_spec)

            self.update_fsm_project_standard_item_model()
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    # def add_fsm_data(self, monitor_id: str):

    #     try:
    #         inst = self.fsmProject.get_install_by_monitor(monitor_id)
    #         if inst.install_type == "Rain Gauge":
    #             file_spec, _ = QtWidgets.QFileDialog.getOpenFileName(
    #                 None, "Open Rain Gauge Data File", "", "Rain Gauge Data files (*.r)")
    #             if not file_spec:
    #                 return
    #             if os.path.exists(file_spec):
    #                 self.lastOpenDialogPath = os.path.dirname(file_spec)
    #                 inst.get_r_data_from_file(file_spec)

    #         if inst.install_type in ["Flow Monitor", "Depth Monitor"]:
    #             file_spec, _ = QtWidgets.QFileDialog.getOpenFileName(
    #                 None, "Open Flow Monitor Data File", "", "Flow Monitor Data files (*.fdv)")
    #             if not file_spec:
    #                 return
    #             if os.path.exists(file_spec):
    #                 self.lastOpenDialogPath = os.path.dirname(file_spec)
    #                 inst.get_fdv_data_from_file(file_spec)

    #         self.update_fsm_project_standard_item_model()
    #     except Exception as e:
    #         logger.error('Exception occurred', exc_info=True)
    #         msg = QMessageBox(self)
    #         msg.critical(
    #             self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def fsm_import_data_downloads(self):

        try:
            fileSpec = QtWidgets.QFileDialog.getExistingDirectory(
                self, "Select Direct Downloads Directory:", self.lastOpenDialogPath,
                QtWidgets.QFileDialog.ShowDirsOnly)
            if len(fileSpec) == 0:
                return
            self.lastOpenDialogPath = fileSpec
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    # def bytes_to_text(self, data, encoding='utf-8'):
    #     try:
    #         decoded_text = data.decode(encoding).rstrip('\x00')
    #         return decoded_text
    #     except UnicodeDecodeError:
    #         # If decoding using the specified encoding fails, fallback to ANSI
    #         decoded_text = data.decode('ansi').rstrip('\x00')
    #         return decoded_text

    # # # Function to convert bytes to ASCII text
    # # def bytes_to_ascii(self, data):
    # #     return ''.join(chr(byte) for byte in data)

    # # Function to unpack little endian 16-bit integers
    # def unpack_int(self, data):
    #     return struct.unpack('<H', data)[0]

    # # Function to unpack little endian 16-bit floats
    # def unpack_float(self, data):
    #     return struct.unpack('<f', data)[0]

    # def bytes_to_text(self, data, encoding='utf-8'):
    #     try:
    #         decoded_text = data.decode(encoding).rstrip('\x00')
    #         return decoded_text
    #     except UnicodeDecodeError:
    #         # If decoding using the specified encoding fails, fallback to ANSI
    #         decoded_text = data.decode('ansi').rstrip('\x00')
    #         return decoded_text

    # def read_dat_file(self, filespec):
    #     dt_timestamps = []
    #     i_values = []

    #     with open(filespec, "rb") as file:
    #         s_header = self.bytes_to_text(file.read(30))
    #         i_flag = struct.unpack('<B', file.read(1))[0]
    #         # print(i_flag)
    #         i_year = struct.unpack('<H', file.read(2))[0]
    #         i_month = struct.unpack('<H', file.read(2))[0]
    #         i_day = struct.unpack('<H', file.read(2))[0]
    #         i_hour = struct.unpack('<H', file.read(2))[0]
    #         i_minute = struct.unpack('<H', file.read(2))[0]
    #         i_second = struct.unpack('<H', file.read(2))[0]
    #         # assume in deciseconds?
    #         i_interval = int((struct.unpack('<H', file.read(2))[0])/(10*60))
    #         s_measurement_type = self.bytes_to_text(file.read(15))
    #         s_units = self.bytes_to_text(file.read(10))
    #         f_max_value = struct.unpack('<f', file.read(4))[0]
    #         # print(f_max_value)
    #         f_min_value = struct.unpack('<f', file.read(4))[0]
    #         # print(f_min_value)
    #         start_datetime = datetime(
    #             i_year, i_month, i_day, i_hour, i_minute, i_second)
    #         i = 0
    #         my_pos = 78

    #         # Determine max threshold based on flag
    #         if i_flag == 2:
    #             no_of_bytes = 1
    #             max_threshold = 255
    #         else:
    #             no_of_bytes = 2
    #             max_threshold = 32767

    #         while True:
    #             float_bytes = file.read(no_of_bytes)
    #             my_pos = my_pos + no_of_bytes
    #             if not float_bytes:
    #                 break

    #             try:
    #                 # Extract initial value based on flag
    #                 if i_flag == 2:
    #                     int_value = struct.unpack('<B', float_bytes)[0]
    #                 else:
    #                     int_value = struct.unpack('<H', float_bytes)[0]

    #                 # Check if value exceeds maximum threshold
    #                 if int_value >= max_threshold:
    #                     int_value = np.nan
    #                 else:
    #                     # Normalize and scale the value
    #                     int_value = int_value / max_threshold
    #                     int_value = f_min_value + \
    #                         ((f_max_value - f_min_value) * int_value)

    #                 i_values.append(int_value)
    #                 dt_timestamps.append(
    #                     start_datetime + timedelta(minutes=i * i_interval))

    #             except Exception as e:
    #                 print(f"Error processing value at index {i}: {e}")
    #                 i_values.append(np.nan)
    #                 dt_timestamps.append(
    #                     start_datetime + timedelta(minutes=i * i_interval))

    #             i += 1

    #     # Round i_values to 3 decimal places before returning
    #     i_values = [round(val, 3) if not np.isnan(val)
    #                 else val for val in i_values]

    #     # Return the DataFrame with rounded values
    #     return pd.DataFrame({'Timestamp': dt_timestamps, 'Value': i_values}), s_units

    # def read_06_depth_file(self, filespec):

    #     try:
    #         dt_timestamps = []
    #         i_depths = []
    #         with open(filespec, "rb") as file:
    #             s_header = self.bytes_to_text(file.read(29))
    #             i_unknown = struct.unpack('<H', file.read(2))[0]
    #             i_year = struct.unpack('<H', file.read(2))[0]
    #             i_month = struct.unpack('<H', file.read(2))[0]
    #             i_day = struct.unpack('<H', file.read(2))[0]
    #             i_hour = struct.unpack('<H', file.read(2))[0]
    #             i_minute = struct.unpack('<H', file.read(2))[0]
    #             i_second = struct.unpack('<H', file.read(2))[0]
    #             # assume in deciseconds?
    #             i_interval = int(
    #                 (struct.unpack('<H', file.read(2))[0])/(10*60))
    #             s_measurement_type = self.bytes_to_text(file.read(15))
    #             s_units = self.bytes_to_text(file.read(10))
    #             s_unknown = self.bytes_to_text(file.read(8))
    #             start_datetime = datetime(
    #                 i_year, i_month, i_day, i_hour, i_minute, i_second)
    #             i = 0
    #             while True:
    #                 float_bytes = file.read(2)
    #                 if not float_bytes:
    #                     break
    #                 try:
    #                     # assume in meters
    #                     int_value = int(
    #                         (struct.unpack('e', float_bytes)[0])/1000)
    #                 except:
    #                     print("Check")
    #                 i_depths.append(int_value)
    #                 dt_timestamps.append(
    #                     start_datetime + timedelta(minutes=i * i_interval))
    #                 i += 1

    #         df = pd.DataFrame({'Timestamp': dt_timestamps, 'Depth': i_depths})

    #         check_axis = self.plotCanvasMain.figure.subplots(1)
    #         check_axis.plot(df['Timestamp'], df['Depth'], label="Check Data")

    #         check_axis.margins(0.1)
    #         self.plotCanvasMain.figure.tight_layout()
    #         check_axis.grid(True)
    #         check_axis.tick_params(axis='y', which='major', labelsize=8)
    #         major_tick_format = DateFormatter("%d/%m/%Y %H:%M")
    #         check_axis.xaxis.set_major_locator(MaxNLocator(integer=False))
    #         check_axis.xaxis.set_major_formatter(
    #             FuncFormatter(major_tick_format))
    #         check_axis.set_ylabel('Depths (mm)', fontsize=8)
    #         check_axis.autoscale(enable=True, axis='y', tight=None)
    #         self.plotCanvasMain.figure.autofmt_xdate()
    #         check_axis.tick_params(axis='x', which='major', labelsize=8)

    #         self.plotCanvasMain.figure.subplots_adjust(
    #             left=0.03, right=0.98, bottom=0.15, top=0.94)

    #         check_axis.legend(loc="best", prop={'size': 6})
    #         leg = check_axis.legend(loc="best", prop={'size': 6})
    #     except Exception as e:
    #         logger.error('Exception occurred', exc_info=True)
    #         msg = QMessageBox(self)
    #         msg.critical(
    #             self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def setupMainWindow(self):

        self.mainToolBox.currentChanged.connect(self.mainToolboxChanged)
        self.tabWidgetMainWindow.currentChanged.connect(
            self.mainTabWidgetChanged)
        self.setupGIS()
        self.setupSchematicGraphicsView()
        self.plotCanvasMain.figure.set_dpi(100)
        self.plotCanvasMain.figure.set_figwidth(15.4)
        self.plotCanvasMain.figure.set_figheight(10.0)

    def setupSchematicGraphicsView(self):

        self.schematicGraphicsView._thisApp = self._thisApp
        self.defaultSmoothing = {'Observed': 0.0, 'Predicted': 0.0}
        # Schematic Graphics View
        self.schematicGraphicsView.viewport().installEventFilter(self)
        schematicToolbar = QToolBar()
        schematicToolbarActionGroup = QActionGroup(self)
        schematicToolbarActionGroup.setExclusive(True)

        myIcon = QtGui.QIcon()
        myIcon.addPixmap(QtGui.QPixmap(
            ":/icons/resources/addWwPS.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.schematicAddWwPSAction = QAction(
            myIcon, 'Add WwPS', self, triggered=self.schematicAddWwPS)
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

    def setupGIS(self):
        self.statusbarCoordinates = QtWidgets.QPlainTextEdit()
        self.statusbarCoordinates.setFixedSize(220, 21)
        self.statusbarCoordinates.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.statusbarCoordinates.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.statusbarCoordinates.setLineWrapMode(
            QtWidgets.QPlainTextEdit.NoWrap)
        self.statusbarCoordinates.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByKeyboard | QtCore.Qt.TextSelectableByMouse)

        self.statusbar.addPermanentWidget(self.statusbarCoordinates)
        self.statusbarCrsButton = QPushButton("CRS: Unknown")
        self.statusbarCrsButton.clicked.connect(self.selectCrs)
        self.statusbar.addPermanentWidget(self.statusbarCrsButton)

        self.thisQgsProject = QgsProject.instance()
        self.thisQgsProject.crsChanged.connect(self.updateCrsButton)

        self.thisQgsProject.setCrs(QgsCoordinateReferenceSystem("EPSG:27700"))

        self.mainMapCanvas.setProject(self.thisQgsProject)
        self.mainMapCanvas.setCanvasColor(Qt.white)
        self.mainMapCanvas.enableAntiAliasing(True)
        self.mainMapCanvas.setDestinationCrs(self.thisQgsProject.crs())
        self.mainMapCanvas.xyCoordinates.connect(self.updateCoordinates)

        # In your setup/initialization code:
        self.mainMapCanvas.extentsChanged.connect(self.debugExtentsChanged)

        self.mainMapCanvas.viewport().installEventFilter(self)
        mapToolbar = QToolBar()
        mapToolbarActionGroup = QActionGroup(self)
        mapToolbarActionGroup.setExclusive(True)

        myIcon = QtGui.QIcon()
        myIcon.addPixmap(QtGui.QPixmap(
            ":/icons/resources/toggleImagery.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionMapToggleImagery = QAction(
            myIcon, 'Toggle World Imagery', self, triggered=self.mapToggleWorld_Imagery)
        self.actionMapToggleImagery.setCheckable(False)
        mapToolbar.addAction(self.actionMapToggleImagery)
        mapToolbarActionGroup.addAction(self.actionMapToggleImagery)

        myIcon = QtGui.QIcon()
        myIcon.addPixmap(QtGui.QPixmap(
            ":/icons/resources/toggleStreetMap.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionMapToggleStreetMap = QAction(
            myIcon, 'Toggle World Street Map', self, triggered=self.mapToggleStreet_Map)
        self.actionMapToggleStreetMap.setCheckable(False)
        mapToolbar.addAction(self.actionMapToggleStreetMap)
        mapToolbarActionGroup.addAction(self.actionMapToggleStreetMap)

        mapToolbar.addSeparator()

        myIcon = QtGui.QIcon()
        myIcon.addPixmap(QtGui.QPixmap(
            ":/icons/resources/navPan.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionMapPan = QAction(myIcon, 'Pan Map', self,
                                    triggered=self.setPanMapTool)
        self.actionMapPan.setCheckable(True)
        mapToolbar.addAction(self.actionMapPan)
        mapToolbarActionGroup.addAction(self.actionMapPan)

        myIcon = QtGui.QIcon()
        myIcon.addPixmap(QtGui.QPixmap(
            ":/icons/resources/navZoomIn.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionZoomIn = QAction(myIcon, 'Zoom In', self,
                                    triggered=self.setZoomInTool)
        self.actionZoomIn.setCheckable(True)
        mapToolbar.addAction(self.actionZoomIn)
        mapToolbarActionGroup.addAction(self.actionZoomIn)

        myIcon = QtGui.QIcon()
        myIcon.addPixmap(QtGui.QPixmap(
            ":/icons/resources/navZoomOut.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionZoomOut = QAction(myIcon, 'Zoom Out', self,
                                     triggered=self.setZoomOutTool)
        self.actionZoomOut.setCheckable(True)
        mapToolbar.addAction(self.actionZoomOut)
        mapToolbarActionGroup.addAction(self.actionZoomOut)

        myIcon = QtGui.QIcon()
        myIcon.addPixmap(QtGui.QPixmap(
            ":/icons/resources/navZoomExtents.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionZoomFull = QAction(
            myIcon, 'Zoom Full', self, triggered=self.zoomToFullExtent)
        mapToolbar.addAction(self.actionZoomFull)
        mapToolbarActionGroup.addAction(self.actionZoomFull)

        myIcon = QtGui.QIcon()
        myIcon.addPixmap(QtGui.QPixmap(
            ":/icons/resources/navZoomPrevious.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionZoomPrevious = QAction(
            myIcon, 'Zoom Previous', self, triggered=self.zoomToPreviousExtent)
        mapToolbar.addAction(self.actionZoomPrevious)
        mapToolbarActionGroup.addAction(self.actionZoomPrevious)

        myIcon = QtGui.QIcon()
        myIcon.addPixmap(QtGui.QPixmap(
            ":/icons/resources/navZoomNext.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionZoomNext = QAction(
            myIcon, 'Zoom Next', self, triggered=self.zoomToNextExtent)
        mapToolbar.addAction(self.actionZoomNext)
        mapToolbarActionGroup.addAction(self.actionZoomNext)

        self.tlbMapToolbar.layout().setMenuBar(mapToolbar)

        # Create Layer widget
        self.thisQgsLayerTree = self.thisQgsProject.layerTreeRoot()
        self.thisQgsLayerTreeMapCanvasBridge = QgsLayerTreeMapCanvasBridge(
            self.thisQgsLayerTree, self.mainMapCanvas)
        self.thisQgsLayerTreeModel = QgsLayerTreeModel(self.thisQgsLayerTree)
        self.thisQgsLayerTreeModel.setFlag(QgsLayerTreeModel.AllowNodeReorder)
        self.thisQgsLayerTreeModel.setFlag(QgsLayerTreeModel.AllowNodeRename)
        self.thisQgsLayerTreeModel.setFlag(
            QgsLayerTreeModel.AllowNodeChangeVisibility)
        self.thisQgsLayerTreeModel.setFlag(QgsLayerTreeModel.ShowLegend)
        self.thisQgsLayerTreeView = QgsLayerTreeView()
        self.thisQgsLayerTreeView.setModel(self.thisQgsLayerTreeModel)
        # Create a scroll area to contain the layer tree view
        # scroll_area = QScrollArea()
        # self.scroll_area.setWidgetResizable(True)
        # self.scroll_area.setMaximumWidth(250)
        self.scroll_area.setWidget(self.thisQgsLayerTreeView)

        # total_width = self.map_splitter.width()
        # sizes = [int(total_width * 0.2), int(total_width * 0.8)]
        # self.map_splitter.setSizes(sizes)
        # self.tabMapHBoxLayout.insertWidget(0, scroll_area)
        self.thisQgsLayerTreeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.thisQgsLayerTreeView.customContextMenuRequested[QtCore.QPoint].connect(
            self.openQgsLayerTreeViewContextMenu)

    def setupMainMenu(self):

        self.actionNew_Project.triggered.connect(self.newProject)
        self.actionLoad_Project.triggered.connect(self.loadProject)
        self.actionSave_Project.triggered.connect(self.saveProject)
        self.actionSave_Project_As.triggered.connect(self.saveProjectAs)
        self.actionHelp.triggered.connect(self.showHelpFile)
        self.actionInfo.triggered.connect(self.aboutBox)
        self.actionClose.triggered.connect(self.close)
        # self.actionClose.triggered.connect(self.closeApplication)
        self.action_new_job.triggered.connect(self.create_fsm_project)
        self.action_new_job_batch_import.triggered.connect(self.create_fsm_project_from_csv)
        self.action_new_batch_import_template.triggered.connect(self.create_fsm_job_csv_template)
        self.action_fsm_add_site.triggered.connect(self.add_fsm_site)
        self.action_fsm_add_monitor.triggered.connect(self.add_fsm_monitor)
        # self.action_fsm_import_data_pmac.triggered.connect(self.fsm_import_data_pmac)
        # self.action_fsm_import_data_downloads.triggered.connect(self.fsm_import_data_downloads)
        self.action_fsm_import_data_raw.triggered.connect(
            self.fsm_bulk_import_raw_data)
        self.action_fsm_import_data_fdv.triggered.connect(
            self.fsm_import_data_fdv)
        self.action_fsm_import_data_r.triggered.connect(self.fsm_import_data_r)
        self.action_fsm_export_data_processed.triggered.connect(self.fsm_export_data_processed)
        self.action_fsm_process_raw_data.triggered.connect(
            self.fsm_bulk_process_raw_data)

        self.action_Add_Flow_Monitors.triggered.connect(self.open_FM_files)
        self.action_Add_Rain_Gauges.triggered.connect(self.open_RG_files)
        self.action_Rem_Flow_Monitors.triggered.connect(
            self.remove_all_FM_files)
        self.action_Rem_Rain_Gauges.triggered.connect(self.remove_all_RG_files)
        self.actionICM_Data_Import.triggered.connect(self.importICMModelData)
        self.actionEdit_Monitor_Model_Data.triggered.connect(
            self.updateFlowMonitorModelData)

        self.actionWQ_add_monitor.triggered.connect(self.add_wq_monitor)
        self.actionWQ_rem_monitor.triggered.connect(
            self.remove_all_wq_monitors)

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

        self.actionAddShapefile.triggered.connect(self.addShapefile)
        # self.actionImportFMLocations.triggered.connect(self.importFMLocations)

    def setupMainStatusBar(self):

        self.progressBar = QProgressBar()
        self.statusBar().addPermanentWidget(self.progressBar)
        self.progressBar.setGeometry(30, 40, 200, 25)
        self.progressBar.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.progressBar.hide()
        self._thisApp.processEvents()

    def setupManagementPage(self):

        # self.trw_FlowSurveyManagement.customContextMenuRequested.connect(self.openFSMTreeViewContextMenu)
        # self.trw_FlowSurveyManagement.viewport().installEventFilter(self)
        self.trv_flow_survey_management.customContextMenuRequested.connect(
            self.openFSMTreeViewContextMenu)
        self.trv_flow_survey_management.viewport().installEventFilter(self)
        self.update_fsm_project_standard_item_model()
        self.trv_flow_survey_management.setModel(self.fsm_project_model)
        self.rbnFSMRawValues.toggled.connect(self.update_plot)
        self.rbnFSMProcessedValues.toggled.connect(self.update_plot)
        self.chkShowAdjustments.stateChanged.connect(self.update_plot)
        self.trw_PlottedFSMInstalls.viewport().installEventFilter(self)
        self.trw_PlottedFSMInstalls.customContextMenuRequested.connect(self.openPlottedInstallsTreeViewContextMenu)        

        self.enable_fsm_menu()

        # self.page_fsm_fdv.setVisible(False)
        # self.page_fsm_scattergraphs.setVisible(False)
        # self.page_fsm_rainfall_cum_depth.setVisible(False)
        # self.page_fsm_rainfall_analysis.setVisible(False)
        # self.page_fsm_data_classification.setVisible(False)
        # self.page_fsm_dry_weather_flow.setVisible(False)

    def setupAnalysisPage(self):

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

        self.trw_DWF_Analysis.customContextMenuRequested.connect(
            self.openPlotTreeViewContextMenu)
        self.trw_DWF_Analysis.viewport().installEventFilter(self)

        # Lists for Open Monitors/Gauges:
        self.lst_FlowMonitors.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lst_FlowMonitors.customContextMenuRequested.connect(
            self.openFlowMonitorsListContextMenu)
        self.lst_RainGauges.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lst_RainGauges.customContextMenuRequested.connect(
            self.openRainGaugeListContextMenu)

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

        self.btnEventAdd.clicked.connect(self.addSurveyEvent)
        self.btnEventCapture.clicked.connect(self.captureSurveyEvent)

    def setupVerificationPage(self):

        self.tbxVerification.currentChanged.connect(self.update_plot)

        self.trw_PlottedICMTraces.viewport().installEventFilter(self)
        self.btnTracePrev.clicked.connect(
            lambda: self.updateCurrentTrace(False))
        self.btnTraceNext.clicked.connect(
            lambda: self.updateCurrentTrace(True))

        # Tree Widget for ICM Traces:
        self.trw_PlottedICMTraces.customContextMenuRequested.connect(
            self.openPlottedTraceTreeViewContextMenu)
        self.lst_ICMTraces.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lst_ICMTraces.customContextMenuRequested.connect(
            self.openICMTraceListContextMenu)

    def setupWaterQualityPage(self):

        # self.tbxVerification.currentChanged.connect(self.update_plot)

        self.trw_PlottedWQMonitors.viewport().installEventFilter(self)

        # Tree Widget for WQ Monitors:
        self.trw_PlottedWQMonitors.customContextMenuRequested.connect(
            self.openPlottedWQMonitorsTreeViewContextMenu)
        self.lst_WQMonitors.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lst_WQMonitors.customContextMenuRequested.connect(
            self.openWQMonitorsListContextMenu)

        self.rbnWQRawValues.toggled.connect(self.update_plot)
        self.rbnWQMeanValues.toggled.connect(self.update_plot)
        self.cboWQFrequency.currentIndexChanged.connect(self.update_plot)

    def openQgsLayerTreeViewContextMenu(self, position):

        # level = self.getTreeViewLevel(self.trwSummedFMs)
        if not self.thisQgsLayerTreeView.index2node(self.thisQgsLayerTreeView.indexAt(position)) is None:
            if self.thisQgsLayerTreeView.index2node(self.thisQgsLayerTreeView.indexAt(position)).nodeType() == QgsLayerTreeNode.NodeType.NodeLayer:
                test = self.thisQgsLayerTreeView.index2node(
                    self.thisQgsLayerTreeView.indexAt(position)).layer()
                if type(test) == QgsVectorLayer:
                    menu = QMenu()
                    myCallback = QtWidgets.QAction("Zoom to Layer", menu)
                    myCallback.triggered.connect(
                        lambda: self.zoomToLayer(test))
                    menu.addAction(myCallback)

                    # if test != self.worldImageryLayer and test != self.worldStreetMapLayer:
                    myCallback = QtWidgets.QAction("Remove Layer", menu)
                    myCallback.triggered.connect(
                        lambda: self.removeLayer(test))
                    menu.addAction(myCallback)

                    if not len(menu.actions()) == 0:
                        menu.exec_(
                            self.thisQgsLayerTreeView.mapToGlobal(position))

    def debugExtentsChanged(self):
        """Slot that gets called whenever the map canvas changes its extents."""
        current_extent = self.mainMapCanvas.extent()
        print("Map Canvas extents changed to:", current_extent.toString())

    # def setZoomInTool(self):
    #     if self.actionZoomIn.isChecked() is True:
    #         self.currentMapTool = QgsMapToolZoom(
    #             self.mainMapCanvas, False)  # To zoom in
    #         self.mainMapCanvas.setMapTool(self.currentMapTool)
    #     else:
    #         if self.mainMapCanvas.mapTool() == self.currentMapTool:
    #             self.mainMapCanvas.unsetMapTool(self.currentMapTool)
    #             self.currentMapTool = None

    def setZoomInTool(self):
        if self.actionZoomIn.isChecked():
            self.currentMapTool = QgsMapToolZoom(self.mainMapCanvas, False)  # False => Zoom In
            self.currentMapTool.setAction(self.actionZoomIn)
            self.mainMapCanvas.setMapTool(self.currentMapTool)
        else:
            if self.mainMapCanvas.mapTool() == self.currentMapTool:
                self.mainMapCanvas.unsetMapTool(self.currentMapTool)
                self.currentMapTool = None

    # def setZoomOutTool(self):
    #     if self.actionZoomOut.isChecked() is True:
    #         self.currentMapTool = QgsMapToolZoom(
    #             self.mainMapCanvas, True)  # To zoom out
    #         self.mainMapCanvas.setMapTool(self.currentMapTool)
    #     else:
    #         if self.mainMapCanvas.mapTool() == self.currentMapTool:
    #             self.mainMapCanvas.unsetMapTool(self.currentMapTool)
    #             self.currentMapTool = None

    def setZoomOutTool(self):
        if self.actionZoomOut.isChecked():
            self.currentMapTool = QgsMapToolZoom(self.mainMapCanvas, True)   # True => Zoom Out
            self.currentMapTool.setAction(self.actionZoomOut)
            self.mainMapCanvas.setMapTool(self.currentMapTool)
        else:
            if self.mainMapCanvas.mapTool() == self.currentMapTool:
                self.mainMapCanvas.unsetMapTool(self.currentMapTool)
                self.currentMapTool = None    

    # def setPanMapTool(self):
    #     if self.actionMapPan.isChecked() is True:
    #         self.currentMapTool = QgsMapToolPan(self.mainMapCanvas)  # To pan
    #         self.mainMapCanvas.setMapTool(self.currentMapTool)
    #     else:
    #         if self.mainMapCanvas.mapTool() == self.currentMapTool:
    #             self.mainMapCanvas.unsetMapTool(self.currentMapTool)
    #             self.currentMapTool = None

    def setPanMapTool(self):
        if self.actionMapPan.isChecked():
            self.currentMapTool = QgsMapToolPan(self.mainMapCanvas)
            self.currentMapTool.setAction(self.actionMapPan)
            self.mainMapCanvas.setMapTool(self.currentMapTool)
        else:
            if self.mainMapCanvas.mapTool() == self.currentMapTool:
                self.mainMapCanvas.unsetMapTool(self.currentMapTool)
                self.currentMapTool = None

    # def setZoomInTool(self):
    #     if self.actionZoomIn.isChecked():
    #         zoomInTool = QgsMapToolZoom(self.mainMapCanvas, False)  # False => Zoom In
    #         zoomInTool.setAction(self.actionZoomIn)                  # <--- Link to the QAction
    #         self.currentMapTool = zoomInTool
    #         self.mainMapCanvas.setMapTool(self.currentMapTool)
    #     else:
    #         if self.mainMapCanvas.mapTool() == self.currentMapTool:
    #             self.mainMapCanvas.unsetMapTool(self.currentMapTool)
    #             self.currentMapTool = None

    # def setZoomOutTool(self):
    #     if self.actionZoomOut.isChecked():
    #         zoomOutTool = QgsMapToolZoom(self.mainMapCanvas, True)   # True => Zoom Out
    #         zoomOutTool.setAction(self.actionZoomOut)                # <--- Link to the QAction
    #         self.currentMapTool = zoomOutTool
    #         self.mainMapCanvas.setMapTool(self.currentMapTool)
    #     else:
    #         if self.mainMapCanvas.mapTool() == self.currentMapTool:
    #             self.mainMapCanvas.unsetMapTool(self.currentMapTool)
    #             self.currentMapTool = None

    # def setPanMapTool(self):
    #     if self.actionMapPan.isChecked():
    #         panTool = QgsMapToolPan(self.mainMapCanvas)
    #         panTool.setAction(self.actionMapPan)                     # <--- Link to the QAction
    #         self.currentMapTool = panTool
    #         self.mainMapCanvas.setMapTool(self.currentMapTool)
    #     else:
    #         if self.mainMapCanvas.mapTool() == self.currentMapTool:
    #             self.mainMapCanvas.unsetMapTool(self.currentMapTool)
    #             self.currentMapTool = None

    def zoomToNextExtent(self):
        self.mainMapCanvas.zoomToNextExtent()
        self.refresh()

    def zoomToPreviousExtent(self):
        self.mainMapCanvas.zoomToPreviousExtent()
        self.refresh()

    # def zoomToFullExtent(self):
    #     self.mainMapCanvas.zoomToFullExtent()
    #     self.refresh()

    def zoomToFullExtent(self):
        # 1. Store the old extent (so we can come back to it)
        self.mainMapCanvas.storeCurrentView()
        # 2. Zoom to full
        self.mainMapCanvas.zoomToFullExtent()
        # 3. Store the new extent (so we can go "next" from here if needed)
        self.mainMapCanvas.storeCurrentView()
        self.refresh()

    # def zoomToLayer(self, layer):
    #     self.mainMapCanvas.setExtent(layer.extent())
    #     self.refresh()

    def zoomToLayer(self, layer):
        # 1. Store the old extent
        self.mainMapCanvas.storeCurrentView()    
        # 2. Set a new extent
        self.mainMapCanvas.setExtent(layer.extent())
        # 3. Optionally store the new extent as well
        self.mainMapCanvas.storeCurrentView()
        self.refresh()

    def removeLayer(self, layer):
        self.thisQgsProject.removeMapLayer(layer)
        self.refresh()

    def refresh(self):
        # if not self.thisQgsLayerTreeView.currentLayer() is None:
        #     self.thisQgsLayerTreeView.refreshLayerSymbology(
        #         self.thisQgsLayerTreeView.currentLayer().id())
        # TestLayer:
        # layer = QgsVectorLayer("C:/Temp/ATO_Impermeable_Areas.shp", "Layer Name", "ogr")
        # self.thisQgsProject.addMapLayer(layer)
        # self.thisQgsProject.layerTreeRoot().findLayer(layer.id()).setItemVisibilityChecked(True)
        self.mainMapCanvas.refresh()

    def mapToggleWorld_Imagery(self):
        try:
            logger.debug("Toggling World Imagery Layer")
            if self.worldImageryLayer is None:
                logger.debug(
                    "World Imagery Layer is None, attempting to create it.")
                myUrl = "url='https://server.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer' layer='0'"
                self.worldImageryLayer = QgsRasterLayer(
                    myUrl, "World Imagery", providerType="arcgismapserver")
                logger.debug(f"Created World Imagery Layer with URL: {myUrl}")

                # Set CRS and log it
                self.worldImageryLayer.setCrs(
                    QgsCoordinateReferenceSystem("EPSG:3857"))
                logger.debug("CRS set to EPSG:3857")

                if not self.worldImageryLayer.isValid():
                    logger.error("World Imagery Layer failed to load!")
                else:
                    self.thisQgsProject.addMapLayer(self.worldImageryLayer)
                    logger.debug("World Imagery Layer added to project")
                    self.thisQgsProject.layerTreeRoot().findLayer(
                        self.worldImageryLayer.id()).setItemVisibilityChecked(True)
                    logger.debug("Layer visibility set to True")
            else:
                logger.debug("World Imagery Layer exists, removing it.")
                self.thisQgsProject.removeMapLayer(self.worldImageryLayer)
                self.worldImageryLayer = None
                logger.debug("World Imagery Layer removed.")

            self.refresh()
            logger.debug("Map canvas refreshed.")
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)

    def mapToggleStreet_Map(self):
        try:
            logger.debug("Toggling World Street Map Layer")
            if self.worldStreetMapLayer is None:
                logger.debug(
                    "World Street Map Layer is None, attempting to create it.")
                myUrl = "url='https://server.arcgisonline.com/arcgis/rest/services/World_Street_Map/MapServer' layer='0'"
                self.worldStreetMapLayer = QgsRasterLayer(
                    myUrl, "World Street Map", providerType="arcgismapserver")
                logger.debug(
                    f"Created World Street Map Layer with URL: {myUrl}")

                # Set CRS and log it
                self.worldStreetMapLayer.setCrs(
                    QgsCoordinateReferenceSystem("EPSG:3857"))
                logger.debug("CRS set to EPSG:3857")

                if not self.worldStreetMapLayer.isValid():
                    logger.error("World Street Map Layer failed to load!")
                else:
                    self.thisQgsProject.addMapLayer(self.worldStreetMapLayer)
                    logger.debug("World Street Map Layer added to project")
                    self.thisQgsProject.layerTreeRoot().findLayer(
                        self.worldStreetMapLayer.id()).setItemVisibilityChecked(True)
                    logger.debug("Layer visibility set to True")
            else:
                logger.debug("World Street Map Layer exists, removing it.")
                self.thisQgsProject.removeMapLayer(self.worldStreetMapLayer)
                self.worldStreetMapLayer = None
                logger.debug("World Street Map Layer removed.")

            self.refresh()
            logger.debug("Map canvas refreshed.")
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
    # def mapToggleWorld_Imagery(self):
    #     try:
    #         if self.worldImageryLayer is None:
    #             myUrl = "url='https://server.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer' layer='0'"
    #             self.worldImageryLayer = QgsRasterLayer(
    #                 myUrl, "World Imagery", providerType="arcgismapserver")
    #             self.worldImageryLayer.setCrs(
    #                 QgsCoordinateReferenceSystem("EPSG:3857"))
    #             if not self.worldImageryLayer.isValid():
    #                 print("Layer failed to load!")
    #             else:
    #                 self.thisQgsProject.addMapLayer(self.worldImageryLayer)
    #                 self.thisQgsProject.layerTreeRoot().findLayer(
    #                     self.worldImageryLayer.id()).setItemVisibilityChecked(True)
    #                 # self.worldImageryLayer.setVisibility(True)
    #         else:
    #             self.thisQgsProject.removeMapLayer(self.worldImageryLayer)
    #             self.worldImageryLayer = None
    #         self.refresh()
    #     except Exception as e:
    #         logger.error('Exception occurred', exc_info=True)

    # def mapToggleStreet_Map(self):
    #     try:
    #         if self.worldStreetMapLayer is None:
    #             myUrl = "url='https://server.arcgisonline.com/arcgis/rest/services/World_Street_Map/MapServer' layer='0'"
    #             self.worldStreetMapLayer = QgsRasterLayer(
    #                 myUrl, "World Street Map", providerType="arcgismapserver")
    #             self.worldStreetMapLayer.setCrs(
    #                 QgsCoordinateReferenceSystem("EPSG:3857"))
    #             if not self.worldStreetMapLayer.isValid():
    #                 print("Layer failed to load!")
    #             else:
    #                 self.thisQgsProject.addMapLayer(self.worldStreetMapLayer)
    #                 self.thisQgsProject.layerTreeRoot().findLayer(
    #                     self.worldStreetMapLayer.id()).setItemVisibilityChecked(True)
    #                 # self.worldStreetMapLayer.setVisibility(True)
    #         else:
    #             self.thisQgsProject.removeMapLayer(self.worldStreetMapLayer)
    #             self.worldStreetMapLayer = None
    #         self.refresh()
    #     except Exception as e:
    #         logger.error('Exception occurred', exc_info=True)

    def updateCoordinates(self, pointXY):
        self.statusbarCoordinates.setPlainText(
            "Coordinates: " + str(round(pointXY.x(), 4)) + ", " + str(round(pointXY.y(), 4)))

    def updateCrsButton(self):
        self.mainMapCanvas.setDestinationCrs(self.thisQgsProject.crs())
        self.statusbarCrsButton.setText(
            "CRS: " + self.thisQgsProject.crs().authid())

    def selectCrs(self):
        selectProjectionDlg = fsp_flowbot_projectionDialog()
        selectProjectionDlg.setWindowTitle("Select CRS Dialog")
        selectProjectionDlg.mQgsProjectionSelectionWidget.setCrs(
            self.thisQgsProject.crs())
        ret = selectProjectionDlg.exec()
        if ret == QDialog.Accepted:
            self.thisQgsProject.setCrs(
                selectProjectionDlg.mQgsProjectionSelectionWidget.crs())
            self.mainMapCanvas.setDestinationCrs(self.thisQgsProject.crs())

    def addShapefile(self):
        # Open file dialog to select Shapefile
        shapefile_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Open Shapefile", "", "Shapefiles (*.shp)")
        if not shapefile_path:
            print("No file selected.")
            return
        try:
            # Extract the layer name from the shapefile path
            layer_name = os.path.splitext(os.path.basename(shapefile_path))[0]

            # Load the shapefile using QGIS
            layer = QgsVectorLayer(shapefile_path, layer_name, "ogr")
            if not layer.isValid():
                print("Layer failed to load!")
                return

            # Add the layer to the QGIS project
            QgsProject.instance().addMapLayer(layer)

            # # Refresh the map view or any other necessary updates
            # self.updateMapView()

        except Exception as e:
            print(f"An error occurred while loading the shapefile: {str(e)}")

    # def importFMLocations(self):

    #     feature_classes = []
    #     # Open file dialog to select GeoPackage file
    #     gpkg_file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
    #         None, "Open GeoPackage File", "", "GeoPackage files (*.gpkg)")
    #     if not gpkg_file_path:
    #         print("No file selected.")
    #         return
    #     try:
    #         for layername in fiona.listlayers(gpkg_file_path):
    #             feature_classes.append(layername)

    #         if len(feature_classes) == 0:
    #             print("No feature classes found in the GeoPackage.")
    #             return

    #         # If there's only one feature class, select it automatically
    #         if len(feature_classes) == 1:
    #             selected_feature_class = feature_classes[0]
    #         else:
    #             # If there are multiple feature classes, display a dialog to choose one
    #             selected_feature_class, ok_pressed = QInputDialog.getItem(self, "Select Feature Class", "Choose a feature class:",
    #                                                                       feature_classes, 0, False)
    #             if not ok_pressed:
    #                 print("No feature class selected.")
    #                 return

    #         # Open the GeoPackage file
    #         gdf = gpd.read_file(gpkg_file_path, layer=selected_feature_class)

    #         crs = CRS.from_user_input(gdf.crs)
    #         transformer = Transformer.from_crs(
    #             crs, "epsg:4326", always_xy=True)

    #         # Read the selected feature class from the GeoPackage
    #         # mapped_flow_monitors = gdf[selected_feature_class]

    #         if self.mappedFlowMonitors is None:
    #             self.mappedFlowMonitors = mappedFlowMonitors()

    #         # Now you can iterate through mapped_flow_monitors or perform any other operation as needed
    #         for index, row in gdf.iterrows():
    #             if not row['monitorName'] in self.mappedFlowMonitors.dictMappedFlowMonitors:
    #                 lon, lat = transformer.transform(
    #                     row.geometry.x, row.geometry.y)
    #                 mFM = mappedFlowMonitor(row['monitorName'], lat, lon)
    #                 self.mappedFlowMonitors.addMappedFlowMonitor(mFM)

    #         self.refreshFlowMonitorListWidget()
    #         self.updateMapView()
    #         # print("Mapped flow monitors read successfully.")

    #     except Exception as e:
    #         print(
    #             f"An error occurred while reading the GeoPackage file: {str(e)}")

    # def updateMapView(self, refreshMonitors: bool = False):

    #     if refreshMonitors:
    #         self.flowbotWebMap.mappedFMs = self.mappedFlowMonitors
    #     self.flowbotWebMap.updateMap()
    #     self.webEngineView.load(QUrl.fromLocalFile(
    #         self.flowbotWebMap.mapHTMLFile))

    # def handle_webViewPopup_clicked(self, popupText):
    #     # index = self.station_dropdown.findText(popupText)
    #     # if index != -1:
    #     #     self.station_dropdown.setCurrentIndex(index)
    #     pass

    def showHelpFile(self):

        # os.startfile(os.getcwd()+"/resources/chm/FlowBot User Manual.chm")
        os.startfile(resource_path('resources/chm/FlowBot User Manual.chm'))

    def toCSV_CumulativeRainfall(self):

        if self.openRainGauges is not None:
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
                        'No open Raingauges found', QMessageBox.Ok)

    def toCSV_Scattergraph(self):
        if self.openFlowMonitors is not None:

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
                    scatter.plot_flow_monitor = fm
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
        if self.openFlowMonitors is not None:

            myDict = {}
            fileSpec, filter = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save FDV Graphs to CSV...", self.lastOpenDialogPath, 'csv Files (*.csv)')
            if len(fileSpec) == 0:
                return

            for fm in self.openFlowMonitors.dictFlowMonitors.values():
                myDict.update({f'Date{fm.monitorName}': fm.dateRange.copy(), f'Flow{fm.monitorName}': fm.flowDataRange.copy(
                ), f'Depth{fm.monitorName}': fm.depthDataRange.copy(), f'Vel{fm.monitorName}': fm.velocityDataRange.copy()})

            if self.openRainGauges is not None:

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

        if self.aTraceGraph is not None:
            if self.aTraceGraph.plottedICMTrace is not None:
                if self.aTraceGraph.plottedICMTrace.plotTrace is not None:
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
        if self.openIcmTraces is not None:
            verifSummaryReportDialog = flowbot_dialog_reporting_verificationsummary(
                self.openIcmTraces, self)
            verifSummaryReportDialog.setWindowTitle(
                'Configure Verification Summary Report')
            # verifSummaryReportDialog.show()
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

        if self.openIcmTraces is not None:
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
            # icmTraceReportDialog.show()
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
                    self._thisApp.processEvents()
                pdf.output(icmTraceReportDialog.outputFileSpec, 'F')
                os.startfile(icmTraceReportDialog.outputFileSpec)

                self.progressBar.hide()
                self.statusBar().clearMessage()
                self._thisApp.processEvents()

        else:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.warning(self, 'Warning', 'No open ICM Traces', QMessageBox.Ok)

    def createReport_TraceOutputs(self):
        if self.openIcmTraces is not None:
            tempPlotDir = 'plots'
            try:
                shutil.rmtree(tempPlotDir)
                os.mkdir(tempPlotDir)
            except FileNotFoundError:
                os.mkdir(tempPlotDir)

            icmTraceReportDialog = flowbot_dialog_reporting_icmtrace(
                self.openIcmTraces)
            icmTraceReportDialog.setWindowTitle('Configure ICM Traces Report')
            # icmTraceReportDialog.show()
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
                        if tempTraceGraph.plottedICMTrace.plotTrace is not None:
                            tempTraceGraph.plottedICMTrace.plotTrace.currentLocation = index
                            tempTraceGraph.plottedICMTrace.updatePlottedICMTracesMinMaxValues()
                            tempTraceGraph.update_plot()

                            tempTraceGraph.main_window_plot_widget.figure.savefig(
                                f'{tempPlotDir}/{iFigureNo}.png', dpi=100)
                            iFigureNo += 1
                            self.progressBar.setValue(iFigureNo)
                            self.statusBar().showMessage('Generating ICM Trace: ' + str(iFigureNo))
                            self._thisApp.processEvents()
                pdf = onePagePDF(icmTraceReportDialog.edtReportTitle.text())
                plots_per_page = constructGenericOnePageReport(tempPlotDir)
                self.progressBar.setValue(0)
                self.progressBar.setMaximum(len(plots_per_page))
                iCount = 1

                for elem in plots_per_page:
                    self.progressBar.setValue(iFigureNo)
                    self.statusBar().showMessage('Generating Report Page: ' + str(iCount))
                    self._thisApp.processEvents()
                    pdf.print_page(elem)
                    iCount += 1

                pdf.output(icmTraceReportDialog.outputFileSpec, 'F')
                os.startfile(icmTraceReportDialog.outputFileSpec)

                self.progressBar.hide()
                self.statusBar().clearMessage()
                self._thisApp.processEvents()

                plt.close(tempTraceGraph.main_window_plot_widget.figure)
                tempTraceGraph = None

        else:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.warning(self, 'Warning',
                        'No Open Flow Monitors', QMessageBox.Ok)

    def createReport_FDV(self):

        if self.openFlowMonitors is not None:
            tempPlotDir = 'plots'
            try:
                shutil.rmtree(tempPlotDir)
                os.mkdir(tempPlotDir)
            except FileNotFoundError:
                os.mkdir(tempPlotDir)

            fdvReportDialog = flowbot_dialog_reporting_fdv(
                self.openFlowMonitors, self.openRainGauges, self.identifiedSurveyEvents)
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
                                if fm.hasModelData is True:
                                    if len(fm.modelDataRG) > 0:
                                        if self.openRainGauges is not None:
                                            rg = self.openRainGauges.getRainGauge(
                                                fm.modelDataRG)
                                            if rg is not None:
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
                            self._thisApp.processEvents()

                pdf = onePagePDF(fdvReportDialog.edtReportTitle.text())
                plots_per_page = constructGenericOnePageReport(tempPlotDir)
                self.progressBar.setValue(0)
                self.progressBar.setMaximum(len(plots_per_page))
                iCount = 1

                for elem in plots_per_page:
                    self.progressBar.setValue(iFigureNo)
                    self.statusBar().showMessage('Generating Report Page: ' + str(iCount))
                    self._thisApp.processEvents()
                    pdf.print_page(elem)
                    iCount += 1

                pdf.output(fdvReportDialog.outputFileSpec, 'F')
                os.startfile(fdvReportDialog.outputFileSpec)

                self.progressBar.hide()
                self.statusBar().clearMessage()
                self._thisApp.processEvents()

                plt.close(tempGraph.main_window_plot_widget.figure)
                tempGraph = None
                # self.update_plot()

        else:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.warning(self, 'Warning',
                        'No Open Flow Monitors', QMessageBox.Ok)

    def createReport_VolumeBalance(self):

        if self.openFlowMonitors is not None:

            flowbalReportDialog = flowbot_dialog_reporting_flowbalance(
                self.openFlowMonitors, self.identifiedSurveyEvents)
            flowbalReportDialog.setWindowTitle('Configure Flow Balance Report')
            # flowbalReportDialog.show()
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

                        if fmSchem is not None:
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
                                    if item is not fmSchem:
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

        if self.openFlowMonitors is not None and self.openRainGauges is not None and self.identifiedSurveyEvents is not None:
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
            # esReportDialog.show()
            ret = esReportDialog.exec_()
            if ret == QDialog.Accepted:

                self.statusBar().showMessage('Exporting Event Suitability Graphs: ')
                self.progressBar.setMinimum(0)
                self.progressBar.setValue(0)
                self.progressBar.show()
                self.progressBar.setMaximum(esReportDialog.fmCheckCount)

                tempPW = PlotWidget(self, False, (8.3, 5), 100)
                tempGraph = dataClassification(
                    tempPW, self._thisApp, self, False)

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

                        myPlotFig = createEventSuitabilityEventSummaryTablePlot(
                            se)
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
                    self._thisApp.processEvents()
                    pdf.print_page(pagedata)
                    iCount += 1

                pdf.output(esReportDialog.outputFileSpec, 'F')
                os.startfile(esReportDialog.outputFileSpec)

                self.progressBar.hide()
                self.statusBar().clearMessage()
                self._thisApp.processEvents()

                plt.close(tempGraph2.main_window_plot_widget.figure)
                tempGraph = None
                tempGraph2 = None
        else:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.warning(self, 'Warning',
                        'No open Flow Monitors/Raingauges/Events', QMessageBox.Ok)

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

        if self.openFlowMonitors is not None:
            tempPlotDir = 'plots'
            try:
                shutil.rmtree(tempPlotDir)
                os.mkdir(tempPlotDir)
            except FileNotFoundError:
                os.mkdir(tempPlotDir)

            scatterReportDialog = flowbot_dialog_reporting_scatter(
                self.openFlowMonitors, self.identifiedSurveyEvents)
            scatterReportDialog.setWindowTitle('Configure Scattergraph Report')
            # scatterReportDialog.show()
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
                        tempGraph.plotted_events.addSurveyEvent(self.identifiedSurveyEvents.getSurveyEvent(
                            scatterReportDialog.lst_Events.item(index).text()))

                iFigureNo = 0
                for index in range(scatterReportDialog.lst_FlowMonitors.count()):
                    if scatterReportDialog.lst_FlowMonitors.item(index).checkState() == Qt.Checked:

                        tempGraph.plot_flow_monitor = None

                        fm = self.openFlowMonitors.getFlowMonitor(
                            scatterReportDialog.lst_FlowMonitors.item(index).text())
                        tempGraph.plot_flow_monitor = fm

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
                        tempGraph.plot_velocity_scattergraph = scatterReportDialog.rbnVelocity.isChecked()

                        tempGraph.update_plot()
                        tempGraph.main_window_plot_widget.figure.savefig(
                            f'{tempPlotDir}/{iFigureNo}.png', dpi=100)
                        iFigureNo += 1
                        self.progressBar.setValue(iFigureNo)
                        self.statusBar().showMessage('Generating Scattergraph: ' + str(iFigureNo))
                        self._thisApp.processEvents()

                pdf = onePagePDF(scatterReportDialog.edtReportTitle.text())
                plots_per_page = constructGenericOnePageReport(tempPlotDir)
                self.progressBar.setValue(0)
                self.progressBar.setMaximum(len(plots_per_page))
                iCount = 1

                for elem in plots_per_page:
                    self.progressBar.setValue(iFigureNo)
                    self.statusBar().showMessage('Generating Report Page: ' + str(iCount))
                    self._thisApp.processEvents()
                    pdf.print_page(elem)
                    iCount += 1

                pdf.output(scatterReportDialog.outputFileSpec, 'F')
                os.startfile(scatterReportDialog.outputFileSpec)

                self.progressBar.hide()
                self.statusBar().clearMessage()
                self._thisApp.processEvents()

                plt.close(tempGraph.main_window_plot_widget.figure)
                tempGraph = None

        else:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.warning(self, 'Warning',
                        'No Open Flow Monitors', QMessageBox.Ok)

    def mainToolboxChanged(self):

        if self.mainToolBox.currentWidget().objectName() == 'pageFlowSurveyAnalysis':
            self.tabWidgetMainWindow.setTabVisible(1, True)
        else:
            self.tabWidgetMainWindow.setTabVisible(1, False)
        self.update_plot()

    def mainTabWidgetChanged(self):
        if self.tabWidgetMainWindow.currentWidget().objectName() == 'tabMap':
            if not self.tabMapIsSetup:
                total_width = self.map_splitter.width()
                sizes = [int(total_width * 0.2), int(total_width * 0.8)]
                self.map_splitter.setSizes(sizes)
                self.tabMapIsSetup = True
        elif self.tabWidgetMainWindow.currentWidget().objectName() == 'tabGraphs':
            self.update_plot()

    def setCurrentTrace(self, newLocation: int):
        if self.aTraceGraph is not None:
            if self.aTraceGraph.plottedICMTrace.plotTrace is not None:
                self.aTraceGraph.plottedICMTrace.plotTrace.currentLocation = newLocation
                self.aTraceGraph.plottedICMTrace.updatePlottedICMTracesMinMaxValues()
                self.update_plot()
                self.updateICMTraceButtons()

    def updateCurrentTrace(self, next: bool):

        if self.aTraceGraph is not None:
            if self.aTraceGraph.plottedICMTrace.plotTrace is not None:
                if next:
                    if (self.aTraceGraph.plottedICMTrace.plotTrace.currentLocation <
                            len(self.aTraceGraph.plottedICMTrace.plotTrace.dictLocations) - 1):
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
            self._thisApp.processEvents()
            traceFileSpec = path[i]
            self.statusBar().showMessage('Reading: ' + traceFileSpec)

            self.openIcmTraces.getTracesFromCSVFile(
                traceFileSpec, self.defaultSmoothing)

        self.statusBar().clearMessage()
        self.progressBar.hide()
        self._thisApp.processEvents()
        self.refreshICMTraceListWidget()
        self.lastOpenDialogPath = os.path.dirname(path[0])

    def schematicAddWwPS(self):
        if self.schematicGraphicsView._curretSchematicTool == cstWWPS:
            self._thisApp.instance().restoreOverrideCursor()
            self.schematicGraphicsView._curretSchematicTool = cstNONE
            self.schematicAddWwPSAction.setChecked(False)
        else:
            self._thisApp.instance().restoreOverrideCursor()
            self._thisApp.instance().setOverrideCursor(Qt.CrossCursor)
            self.schematicGraphicsView._curretSchematicTool = cstWWPS

    def schematicAddCSO(self):
        if self.schematicGraphicsView._curretSchematicTool == cstCSO:
            self._thisApp.instance().restoreOverrideCursor()
            self.schematicGraphicsView._curretSchematicTool = cstNONE
            self.schematicAddCSOAction.setChecked(False)
        else:
            self._thisApp.instance().restoreOverrideCursor()
            self._thisApp.instance().setOverrideCursor(Qt.CrossCursor)
            self.schematicGraphicsView._curretSchematicTool = cstCSO

    def schematicAddJunction(self):
        if self.schematicGraphicsView._curretSchematicTool == cstJUNCTION:
            self._thisApp.instance().restoreOverrideCursor()
            self.schematicGraphicsView._curretSchematicTool = cstNONE
            self.schematicAddJuncAction.setChecked(False)
        else:
            self._thisApp.instance().restoreOverrideCursor()
            self._thisApp.instance().setOverrideCursor(Qt.CrossCursor)
            self.schematicGraphicsView._curretSchematicTool = cstJUNCTION

    def schematicAddOutfall(self):
        if self.schematicGraphicsView._curretSchematicTool == cstOUTFALL:
            self._thisApp.instance().restoreOverrideCursor()
            self.schematicGraphicsView._curretSchematicTool = cstNONE
            self.schematicAddOutfallAction.setChecked(False)
        else:
            self._thisApp.instance().restoreOverrideCursor()
            self._thisApp.instance().setOverrideCursor(Qt.CrossCursor)
            self.schematicGraphicsView._curretSchematicTool = cstOUTFALL

    def schematicAddWwTW(self):
        if self.schematicGraphicsView._curretSchematicTool == cstWWTW:
            self._thisApp.instance().restoreOverrideCursor()
            self.schematicGraphicsView._curretSchematicTool = cstNONE
            self.schematicAddWwTWAction.setChecked(False)
        else:
            self._thisApp.instance().restoreOverrideCursor()
            self._thisApp.instance().setOverrideCursor(Qt.CrossCursor)
            self.schematicGraphicsView._curretSchematicTool = cstWWTW

    def schematicAddConnection(self):
        if self.schematicGraphicsView._curretSchematicTool == cstCONNECTION:
            self._thisApp.instance().restoreOverrideCursor()
            self.schematicGraphicsView._curretSchematicTool = cstNONE
            self.schematicAddConnectionAction.setChecked(False)
            self.schematicGraphicsView.clearAllVisibleControlPoints()
            self.schematicGraphicsView.setDragMode(
                QGraphicsView.RubberBandDrag)
        else:
            self._thisApp.instance().restoreOverrideCursor()
            self._thisApp.instance().setOverrideCursor(Qt.CrossCursor)
            self.schematicGraphicsView._curretSchematicTool = cstCONNECTION

    def aboutBox(self):
        # strVersion = "1.0"  # Replace this with your actual version variable
        email = "fergus.graham@tetratech.com"
        bug_report_url = "https://forms.office.com/Pages/ResponsePage.aspx?id=uuQPpMer_kiHkrQ4iZNkAC6AlxSXlp5Bo31NAdQ13QJUNzdTRUg0RUZGWE02SUdOOFgxMjBTRU1CUCQlQCN0PWcu"

        myTxt = f"""<p><b>Flowbot {strVersion}</b></p>
                    <p>Contact: <a href="mailto:{email}">{email}</a></p>
                    <p>Report Bugs: <a href="{bug_report_url}">TAPS Bugs/Issues Report</a></p>"""

        msg = QMessageBox(self)
        msg.setWindowTitle("About")
        # msg.setWindowIcon(self.myIcon)
        msg.setIcon(QMessageBox.Information)
        msg.setTextFormat(1)  # Enables rich text (HTML support)
        msg.setText(myTxt)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    # def aboutBox(self):

    #     myTxt = "Flowbot " + strVersion + "\n" + "\n" + \
    #         + "Contact: fergus.graham@tetratech.com"
    #     msg = QMessageBox(self)
    #     msg.setWindowIcon(self.myIcon)
    #     msg.information(self, 'About', myTxt, QMessageBox.Ok)

    def eventFilter(self, o, e):
        if e.type() == QtCore.QEvent.Type.Drop:
            if ((o == self.trw_PlottedMonitors.viewport()) or
                (o == self.trw_Scattergraph.viewport()) or
                (o == self.trw_CumDepth.viewport()) or
                (o == self.trw_RainfallAnalysis.viewport()) or
                (o == self.trw_DataClassification.viewport()) or
                (o == self.trw_DWF_Analysis.viewport())):
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
            elif (o == self.trw_PlottedWQMonitors.viewport()):
                self.trw_PlottedWQMonitors_drop_action(e)
                return True
            elif (o == self.trw_PlottedFSMInstalls.viewport()):
                self.trw_PlottedFSMInstalls_drop_action(e)
                return True
            else:
                return False

        # if e.type() == QtCore.QEvent.Type.Drag:
        #     if (o == self.trw_PlottedFSMInstalls.viewport()):
        #         self.trw_PlottedFSMInstalls_drag_action(e)
        #         return True
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

        elif e.source() == self.trwEvents:

            source_item = QStandardItemModel()
            source_item.dropMimeData(
                e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

            for i in range(source_item.rowCount()):
                se = self.identifiedSurveyEvents.getSurveyEvent(source_item.item(i, 0).text())
                break

            if se is not None:
                self.schematicGraphicsView.addEvent(se)

    def summedFM_drop_action(self, e):

        if e.source() == self.lst_FlowMonitors:
            target_item = self.trwSummedFMs.itemAt(e.pos())
            if target_item is not None:
                level = 0
                if target_item.parent() is not None:
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
                        if sFM.equivalentFM.monitorName == self.aScattergraph.plot_flow_monitor.monitorName:
                            self.update_plot()

            else:
                if self.summedFMs is None:
                    self.summedFMs = {}

                text, ok = QInputDialog.getText(
                    self, 'New Summed FM', 'Name for Summed FM:')
                if ok:
                    if text not in self.summedFMs:
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
            if self.aFDVGraph is not None:
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
                            if fm.hasModelData is True:
                                if len(fm.modelDataRG) > 0:
                                    if self.openRainGauges is not None:
                                        rg = self.openRainGauges.getRainGauge(
                                            fm.modelDataRG)
                                        if rg is not None:
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
            if self.aScattergraph is not None:
                if e.source() == self.lst_FlowMonitors:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    if source_item.rowCount() > 0:
                        self.aScattergraph.plot_flow_monitor = self.openFlowMonitors.getFlowMonitor(source_item.item(0, 0).text())
                        addedToPlot = True

                elif e.source() == self.trwDummyFMs:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    if source_item.rowCount() > 0:
                        if source_item.item(0, 0).text() in self.dummyFMs:
                            dFM = self.dummyFMs[source_item.item(0, 0).text()]
                            self.aScattergraph.plot_flow_monitor = dFM.equivalentFM
                            addedToPlot = True

                elif e.source() == self.trwEvents:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    for i in range(source_item.rowCount()):
                        if (self.aScattergraph.plotted_events.addSurveyEvent(self.identifiedSurveyEvents.getSurveyEvent(
                                source_item.item(i, 0).text()))):
                            addedToPlot = True

        if self.tbxGraphs.currentWidget().objectName() == "pageRainfallCumDepth":
            if self.aCumDepthGraph is not None:
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
            if self.aRainfallAnalysis is not None:
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
            if self.aDataClassification is not None:
                if e.source() == self.lst_FlowMonitors:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    for i in range(source_item.rowCount()):
                        if (self.aDataClassification.classifiedFMs.addFM(self.openFlowMonitors.getFlowMonitor(
                                source_item.item(i, 0).text()))):
                            addedToPlot = True
                            self.aDataClassification.classificationNeedsRefreshed = True
                    self.aDataClassification.classifiedFMs.updateClassifiedFMsMinMaxValues()
                elif e.source() == self.trwEvents:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    for i in range(source_item.rowCount()):
                        if (self.aDataClassification.plottedEvents.addSurveyEvent(self.identifiedSurveyEvents.getSurveyEvent(
                                source_item.item(i, 0).text()))):
                            addedToPlot = True
                    self.aDataClassification.plottedEvents.updateMinMaxValues()
                else:
                    print("dropped from IDK?")

        if self.tbxGraphs.currentWidget().objectName() == "pageDryWeatherFlow":
            if self.a_dwf_graph is not None:
                if e.source() == self.lst_FlowMonitors:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    if source_item.rowCount() > 0:
                        self.a_dwf_graph.plot_flow_monitor = self.openFlowMonitors.getFlowMonitor(source_item.item(0, 0).text())
                        addedToPlot = True

                elif e.source() == self.trwDummyFMs:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    if source_item.rowCount() > 0:
                        if source_item.item(0, 0).text() in self.dummyFMs:
                            dFM = self.dummyFMs[source_item.item(0, 0).text()]
                            self.a_dwf_graph.plot_flow_monitor = dFM.equivalentFM
                            addedToPlot = True

                elif e.source() == self.trwEvents:

                    source_item = QStandardItemModel()
                    source_item.dropMimeData(
                        e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                    for i in range(source_item.rowCount()):
                        if (self.a_dwf_graph.plotted_events.addSurveyEvent(self.identifiedSurveyEvents.getSurveyEvent(
                                source_item.item(i, 0).text()))):
                            addedToPlot = True
                else:
                    print("dropped from IDK?")                            

        if addedToPlot:
            self.update_plot()

    def tbxVerification_drop_action(self, e):

        addedToPlot = False

        if self.tbxVerification.currentWidget().objectName() == "pageVerificationPlots":
            if self.aTraceGraph is not None:
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

        if not self.db_manager is None:
            self.db_manager.close_all_connections()
            del self.db_manager
            DatabaseManager._instance = None
            gc.collect()
        self.db_manager = DatabaseManager()
        self.aFDVGraph = GraphFDV(self.plotCanvasMain)
        self.aScattergraph = graphScatter(self.plotCanvasMain)
        self.aCumDepthGraph = graphCumulativeDepth(self.plotCanvasMain)
        self.aRainfallAnalysis = graphRainfallAnalysis(self.plotCanvasMain)
        self.aDataClassification = dataClassification(
            self.plotCanvasMain, self._thisApp, self)
        self.aTraceGraph = graphICMTrace(self.plotCanvasMain)
        self.aWQGraph = graphWQGraph(self.plotCanvasMain)
        self.aFSMInstallGraph = graphFSMInstall(self.plotCanvasMain)
        self.a_dwf_graph = graphDWF(self.plotCanvasMain)

        self.openFlowMonitors = None
        self.openRainGauges = None
        self.mappedFlowMonitors = None
        self.identifiedSurveyEvents = None
        self.summedFMs = None
        self.dummyFMs = None
        self.openIcmTraces = None
        self.importedICMData = None
        self.fsmProject = None
        self.openWQMonitors = None

        self.lastOpenDialogPath = ''

        self.refreshFlowMonitorListWidget()
        self.refreshRainGaugeListWidget()
        self.refreshICMTraceListWidget()
        self.refreshWQMonitorListWidget()
        self.updateEventTreeView()
        self.updateSummedFMTreeView()
        self.updateDummyFMTreeView()
        # self.update_fsm_project_treeview()
        self.update_plot()
        self.schematicGraphicsView.createNewScene()
        self.update_fsm_project_standard_item_model()
        self.enable_fsm_menu()
        # self.enableMenuItems()

    # def enableMenuItems(self):
    #     self.actionSaveAs_Project.setEnabled(not self.isDirty)

    def newProject(self):
        msg = QMessageBox(self)
        msg.setWindowIcon(self.myIcon)

        ret = msg.warning(
            self, 'Warning', 'Are you sure you want to start a new project?', QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            self.initialiseAllVariables()
            self.setWindowTitle(f"Flowbot v{strVersion}")

    def getPointListFromString(self, myString):
        newList = []
        myList = myString[1:-2].split("), ")
        for item in myList:
            lhs, rhs = item.split("PyQt5.QtCore.QPointF(")
            lhs, rhs = rhs.split(", ")
            newList.append(QPointF(float(lhs), float(rhs)))
        return newList

    def load_project_v3_from_filespec(self, fileSpec: str):

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
                          "modelDataPipeRef", "modelDataRG", "modelDataPipeLength", "modelDataPipeShape", "modelDataPipeDia",
                          "modelDataPipeHeight", "modelDataPipeRoughness", "modelDataPipeUSInvert", "modelDataPipeDSInvert",
                          "modelDataPipeSystemType"]
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
                    self._thisApp.processEvents()
                    self.progressBar.setValue(iCount)
                else:
                    iCount += 1
                    self.progressBar.setValue(iCount)
                    break
                self._thisApp.processEvents()
            fieldnames = ["dataID", "sumFMName", "fmNo", "fmName", "fmMult"]
            reader = csv.DictReader(f, fieldnames=fieldnames)
            aSFM = None
            for row in reader:
                if row["dataID"] == "SFM":
                    if int(row["fmNo"]) == 0:
                        if aSFM is not None:
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
                self._thisApp.processEvents()
            if aSFM is not None:
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
                self._thisApp.processEvents()
            fieldnames = ["dataID", "eventName",
                          "eventType", "eventStart", "eventEnd"]
            reader = csv.DictReader(f, fieldnames=fieldnames)
            for row in reader:
                if row["dataID"] == "SE":
                    aSE = surveyEvent()
                    aSE.eventName = row["eventName"]
                    aSE.eventType = row["eventType"]
                    aSE.eventStart = datetime.strptime(
                        row["eventStart"], "%d/%m/%Y %H:%M")
                    aSE.eventEnd = datetime.strptime(
                        row["eventEnd"], "%d/%m/%Y %H:%M")
                    self.identifiedSurveyEvents.addSurvEvent(aSE)
                    iCount += 1
                    self.progressBar.setValue(iCount)
                else:
                    iCount += 1
                    self.progressBar.setValue(iCount)
                    break
                self._thisApp.processEvents()
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

                        if fromPoint is not None and toPoint is not None:
                            aConnection = ConnectionPath(
                                fromPoint, toPoint.pos())
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
                self._thisApp.processEvents()
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
                self._thisApp.processEvents()
            fieldnames = ["dataID", "traceID", "index", "isCritical", "isSurcharged", "peaksInitialized", "verifyForFlow",
                          "verifyForDepth", "frac", "peaks_prominance", "peaks_width", "peaks_distance", "verificationDepthComment",
                          "verificationFlowComment", "verificationOverallComment"]
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
                self._thisApp.processEvents()
        self.statusBar().clearMessage()
        self.progressBar.hide()
        self._thisApp.processEvents()
        self.refreshFlowMonitorListWidget()
        self.refreshRainGaugeListWidget()
        self.updateSummedFMTreeView()
        self.updateEventTreeView()
        self.refreshICMTraceListWidget()

        self.saveProjectAs()

    def loadProject(self):

        msg = QMessageBox(self)
        msg.setWindowIcon(self.myIcon)

        ret = msg.warning(
            self, 'Warning', 'Are you sure you want to load a new project?', QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            self.initialiseAllVariables()
            if self.db_manager:
                self.db_manager.close_all_connections()
        else:
            return

        fileSpec, filter = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Load Flowbot Project...",
            self.lastOpenDialogPath,
            'Flowbot v4 Project Files (*.fbsqlite);;Flowbot v3 Project Files (*.fbp)')

        if len(fileSpec) == 0:
            return

        _, file_extension = os.path.splitext(fileSpec)
        if file_extension == '.fbsqlite':
            if self.load_project_from_filespec(fileSpec):
                msg = QMessageBox(self)
                msg.setWindowIcon(self.myIcon)
                msg.information(self, 'Load Project',
                                'Project Loaded Sucessfully', QMessageBox.Ok)
        elif file_extension == '.fbp':
            if self.load_project_v3_from_filespec(fileSpec):
                msg = QMessageBox(self)
                msg.setWindowIcon(self.myIcon)
                msg.information(self, 'Load Project',
                                'Project Loaded Sucessfully', QMessageBox.Ok)

    def update_database(self, conn: sqlite3.Connection):
        c = conn.cursor()
        changes_made = False

        # Check the database version
        try:
            c.execute(f"SELECT * FROM {Tables.FB_VERSION}")
            rows = c.fetchall()
            db_version = rows[0][0] if rows else ''
        except sqlite3.OperationalError:
            db_version = ''

        if db_version == '':
            # conn.execute("PRAGMA foreign_keys=off;")  # Disable foreign key checks if any
            conn.execute(
                f'''CREATE TABLE IF NOT EXISTS {Tables.FB_VERSION} (current_version TEXT PRIMARY KEY)''')
            conn.execute(
                f'''INSERT OR REPLACE INTO {Tables.FB_VERSION} VALUES (?)''', (strVersion,))

            conn.execute(f"ALTER TABLE {Tables.FSM_INTERIM} ADD COLUMN pl_data_review_complete INTEGER DEFAULT 0;")

            conn.execute(f"ALTER TABLE {Tables.FSM_INTERIM_REVIEW} ADD COLUMN pl_complete INTEGER DEFAULT 0;")
            conn.execute(f"ALTER TABLE {Tables.FSM_INTERIM_REVIEW} ADD COLUMN pl_comment TEXT DEFAULT '';")

            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.FSM_INSTALL}_new (
                            install_id TEXT PRIMARY KEY,
                            install_site_id TEXT,
                            install_monitor_asset_id TEXT,
                            install_type TEXT,
                            client_ref TEXT,
                            install_date TEXT,
                            remove_date TEXT,
                            fm_pipe_letter TEXT,
                            fm_pipe_shape TEXT,
                            fm_pipe_height_mm INTEGER,
                            fm_pipe_width_mm INTEGER,
                            fm_pipe_depth_to_invert_mm INTEGER,
                            fm_sensor_offset_mm INTEGER,
                            rg_position TEXT,
                            data BLOB,
                            data_start TEXT,
                            data_end TEXT,
                            data_interval INTEGER,
                            data_date_updated TEXT,
                            install_sheet BLOB,
                            install_sheet_filename TEXT,
                            class_data_ml BLOB,
                            class_data_ml_date_updated TEXT,
                            class_data_user BLOB,
                            class_data_user_date_updated TEXT
                        )''')
            conn.execute(f'''
                INSERT INTO {Tables.FSM_INSTALL}_new (
                    install_id, install_site_id, install_monitor_asset_id, install_type,
                    client_ref, install_date, remove_date, fm_pipe_letter, fm_pipe_shape,
                    fm_pipe_height_mm, fm_pipe_width_mm, fm_pipe_depth_to_invert_mm,
                    fm_sensor_offset_mm, rg_position, data, data_start, data_end,
                    data_interval, data_date_updated, install_sheet, install_sheet_filename,
                    class_data_ml, class_data_ml_date_updated, class_data_user, class_data_user_date_updated
                )
                SELECT CAST(install_id AS TEXT), install_site_id, install_monitor_asset_id, install_type,
                    client_ref, install_date, remove_date, fm_pipe_letter, fm_pipe_shape,
                    fm_pipe_height_mm, fm_pipe_width_mm, fm_pipe_depth_to_invert_mm,
                    fm_sensor_offset_mm, rg_position, data, data_start, data_end,
                    data_interval, data_date_updated, install_sheet, install_sheet_filename,
                    class_data_ml, class_data_ml_date_updated, class_data_user, class_data_user_date_updated
                FROM {Tables.FSM_INSTALL};
            ''')
            conn.execute(f'DROP TABLE {Tables.FSM_INSTALL};')
            conn.execute(f'ALTER TABLE {Tables.FSM_INSTALL}_new RENAME TO {Tables.FSM_INSTALL};')

            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.FSM_INTERIM_REVIEW}_new (
                            interim_review_id INTEGER PRIMARY KEY,
                            interim_id INTEGER,
                            install_id TEXT,
                            dr_data_covered INTEGER,
                            dr_ignore_missing INTEGER,
                            dr_reason_missing TEXT,
                            dr_identifier TEXT,
                            cr_complete INTEGER,
                            cr_comment TEXT,
                            ser_complete INTEGER,
                            ser_comment TEXT,
                            fm_complete INTEGER,
                            fm_comment TEXT,
                            rg_complete INTEGER,
                            rg_comment TEXT,
                            pl_complete INTEGER,
                            pl_comment TEXT                         
                         )''')

            conn.execute(f'''
                INSERT INTO {Tables.FSM_INTERIM_REVIEW}_new (
                    interim_review_id, interim_id, install_id, dr_data_covered, dr_ignore_missing,
                    dr_reason_missing, dr_identifier, cr_complete, cr_comment, ser_complete,
                    ser_comment, fm_complete, fm_comment, rg_complete, rg_comment, 
                    pl_complete, pl_comment
                )
                SELECT interim_review_id, interim_id, CAST(install_id AS TEXT), dr_data_covered,
                    dr_ignore_missing, dr_reason_missing, dr_identifier, cr_complete, cr_comment,
                    ser_complete, ser_comment, fm_complete, fm_comment, rg_complete, rg_comment,
                    pl_complete, pl_comment
                FROM {Tables.FSM_INTERIM_REVIEW};
            ''')

            conn.execute(f'DROP TABLE {Tables.FSM_INTERIM_REVIEW};')
            conn.execute(f'ALTER TABLE {Tables.FSM_INTERIM_REVIEW}_new RENAME TO {Tables.FSM_INTERIM_REVIEW};')

            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.FSM_INSPECTIONS}_new (
                            inspection_id INTEGER PRIMARY KEY,
                            install_id TEXT,
                            inspection_date TEXT,
                            inspection_sheet BLOB,
                            inspection_sheet_filename TEXT,
                            inspection_type TEXT
                        )''')

            conn.execute(f'''
                INSERT INTO {Tables.FSM_INSPECTIONS}_new (
                    inspection_id, install_id, inspection_date, inspection_sheet, inspection_sheet_filename,
                    inspection_type
                )
                SELECT inspection_id, CAST(install_id AS TEXT), inspection_date, inspection_sheet, 
                    inspection_sheet_filename, inspection_type
                FROM {Tables.FSM_INSPECTIONS};
            ''')

            conn.execute(f'DROP TABLE {Tables.FSM_INSPECTIONS};')
            conn.execute(f'ALTER TABLE {Tables.FSM_INSPECTIONS}_new RENAME TO {Tables.FSM_INSPECTIONS};')

            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.FSM_INSTALLPICTURES}_new (
                            picture_id INTEGER PRIMARY KEY,
                            install_id TEXT,
                            picture_taken_date TEXT,
                            picture_type TEXT,
                            picture_comment TEXT,
                            picture BLOB
                        )''')
            conn.execute(f'''
                INSERT INTO {Tables.FSM_INSTALLPICTURES}_new (
                    picture_id, install_id, picture_taken_date, picture_type, picture_comment, picture
                )
                SELECT picture_id, CAST(install_id AS TEXT), picture_taken_date, picture_type, picture_comment, picture
                FROM {Tables.FSM_INSTALLPICTURES};
            ''')
            conn.execute(f'DROP TABLE {Tables.FSM_INSTALLPICTURES};')
            conn.execute(f'ALTER TABLE {Tables.FSM_INSTALLPICTURES}_new RENAME TO {Tables.FSM_INSTALLPICTURES};')

            conn.execute(f"""UPDATE {Tables.FSM_SITE} SET siteType = CASE WHEN siteType = 'Rain Gauge' THEN 'Location' ELSE 'Network Asset' END;""")

            changes_made = True

        if changes_made:
            conn.commit()

        return changes_made

    def load_project_from_filespec(self, fileSpec: str) -> bool:

        self.db_manager.initialize(fileSpec, pool_size=5)
        conn = self.db_manager.get_connection()

        try:

            self.update_database(conn)

            if self.fsmProject is None:

                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (Tables.FSM_PROJECT,))
                exists = cursor.fetchone()

                if exists:
                    self.fsmProject = fsmProject()
                    self.fsmProject.read_from_database(conn)
            if self.openFlowMonitors is None:
                self.openFlowMonitors = flowMonitors()
                self.openFlowMonitors.read_from_database(conn)
            if self.openRainGauges is None:
                self.openRainGauges = rainGauges()
                self.openRainGauges.read_from_database(conn)
            if self.identifiedSurveyEvents is None:
                self.identifiedSurveyEvents = surveyEvents()
                self.identifiedSurveyEvents.read_from_database(conn)
            if self.openIcmTraces is None:
                self.openIcmTraces = icmTraces()
                self.openIcmTraces.read_from_database(conn)
            if self.openWQMonitors is None:
                self.openWQMonitors = fwqMonitors()
                self.openWQMonitors.read_from_database(conn)

            self.read_summedFMs_from_database(conn)
            self.read_schematic_graphics_view_from_database(conn)

            self.refreshFlowMonitorListWidget()
            self.refreshRainGaugeListWidget()
            self.updateSummedFMTreeView()
            self.updateEventTreeView()
            self.refreshICMTraceListWidget()
            self.refreshWQMonitorListWidget()
            self.update_fsm_project_standard_item_model()
            self.enable_fsm_menu()

            self.setWindowTitle(f'Flowbot v{strVersion}: {os.path.basename(self.db_manager.database)}')

        except Exception as e:
            print(f"Error loading project from {fileSpec}: {e}")
            return False
        finally:
            self.db_manager.return_connection(conn)

        return True

    def read_summedFMs_from_database(self, conn: sqlite3.Connection):

        c = conn.cursor()
        try:
            c.execute(
                f"SELECT DISTINCT sumFMName FROM {Tables.SUMMED_FLOW_MONITOR}")
            # c.execute(f"SELECT * FROM {Tables.SUMMED_FLOW_MONITOR}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.SUMMED_FLOW_MONITOR}' does not exist.")
            return  # Return without attempting to fetch rows

        dist_rows = c.fetchall()
        for dist_row in dist_rows:
            summedmonitor = summedFlowMonitor()
            summedmonitor.sumFMName = dist_row[0]

            c.execute(
                f"SELECT * FROM {Tables.SUMMED_FLOW_MONITOR} WHERE sumFMName = '{dist_row[0]}' ORDER BY fmNo")
            rows = c.fetchall()
            for row in rows:
                fm = self.openFlowMonitors.getFlowMonitor(row[2])
                summedmonitor.addFM(fm, float(row[3]))

            if self.summedFMs is None:
                self.summedFMs = {}
            self.summedFMs[summedmonitor.sumFMName] = summedmonitor

    def read_schematic_graphics_view_from_database(self, conn: sqlite3.Connection):

        c = conn.cursor()
        try:
            c.execute(f"SELECT * FROM {Tables.SCHEMATIC_GRAPHICS_VIEW}")
            # c.execute(f"SELECT * FROM {Tables.SUMMED_FLOW_MONITOR}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.SCHEMATIC_GRAPHICS_VIEW}' does not exist.")
            return  # Return without attempting to fetch rows

        rows = c.fetchall()
        for row in rows:

            if row[0] == "FM":
                fm = self.openFlowMonitors.getFlowMonitor(row[1])
                if fm._schematicGraphicItem is None:
                    fm._schematicGraphicItem = self.schematicGraphicsView.addFlowMonitor(
                        fm.monitorName, QPointF(float(row[3]), float(row[4])), 0)
            if row[0] == "RG":
                rg = self.openRainGauges.getRainGauge(row[1])
                if rg._schematicGraphicItem is None:
                    rg._schematicGraphicItem = self.schematicGraphicsView.addRaingauge(
                        rg.gaugeName, QPointF(float(row[3]), float(row[4])), 0)
            if row[0] == cstCSO:
                self.schematicGraphicsView.addCSO(
                    row[1], QPointF(float(row[3]), float(row[4])))
            if row[0] == cstWWPS:
                self.schematicGraphicsView.addWwPS(
                    row[1], QPointF(float(row[3]), float(row[4])), row[2])
            if row[0] == cstWWTW:
                self.schematicGraphicsView.addWwTW(
                    row[1], QPointF(float(row[3]), float(row[4])))
            if row[0] == cstJUNCTION:
                self.schematicGraphicsView.addJunction(
                    row[1], QPointF(float(row[3]), float(row[4])), row[2])
            if row[0] == cstOUTFALL:
                self.schematicGraphicsView.addOutfall(
                    row[1], QPointF(float(row[3]), float(row[4])), row[2])
            if row[0] == cstCONNECTION:
                self.schematicGraphicsView.showAllVisibleControlPoints()
                fromPoint = self.schematicGraphicsView.controlPointAt(
                    QPointF(float(row[3]), float(row[4])))
                toPoint = self.schematicGraphicsView.controlPointAt(
                    QPointF(float(row[5]), float(row[6])))
                if fromPoint is not None and toPoint is not None:
                    aConnection = ConnectionPath(fromPoint, toPoint.pos())
                    aConnection.setDestination(toPoint.pos(), toPoint)
                    aConnection.intermediateVertices = [
                        QPointF(point['x'], point['y']) for point in deserialize_list(row[7])]
                    # if len(row[7]) > 0:
                    #     aConnection.intermediateVertices = [QPointF(point['x'], point['y']) for point in deserialize_list(row[7])]

                    self.schematicGraphicsView.scene().addItem(aConnection)

                    fromPoint.addLine(aConnection)
                    toPoint.addLine(aConnection)

                self.schematicGraphicsView.clearAllVisibleControlPoints()

    # def getPointListFromString(self, myString):
    #     newList = []
    #     myList = myString[1:-2].split("), ")
    #     for item in myList:
    #         lhs, rhs = item.split("PyQt5.QtCore.QPointF(")
    #         lhs, rhs = rhs.split(", ")
    #         newList.append(QPointF(float(lhs), float(rhs)))
    #     return newList

    def saveProjectToDatabase(self):

        result = True
        conn = self.db_manager.get_connection()

        try:
            conn.execute(
                f"""CREATE TABLE IF NOT EXISTS {Tables.FB_VERSION} (current_version TEXT PRIMARY KEY)"""
            )
            conn.execute(
                f"""INSERT OR REPLACE INTO {Tables.FB_VERSION} VALUES (?)""",
                (strVersion,),
            )

            if self.fsmProject is not None:
                if not self.fsmProject.write_to_database(conn):
                    result = False
            if self.openFlowMonitors is not None:
                if not self.openFlowMonitors.write_to_database(conn):
                    result = False
            if self.openRainGauges is not None:
                if not self.openRainGauges.write_to_database(conn):
                    result = False
            if self.identifiedSurveyEvents is not None:
                if not self.identifiedSurveyEvents.write_to_database(conn):
                    result = False
            if self.openIcmTraces is not None:
                if not self.openIcmTraces.write_to_database(conn):
                    result = False
            if self.summedFMs is not None:
                if not self.write_summedFMs_to_database(conn):
                    result = False
            if self.openWQMonitors is not None:
                if not self.openWQMonitors.write_to_database(conn):
                    result = False
            if not self.write_schematic_graphics_view_to_database(conn):
                result = False

            self.setWindowTitle(f'Flowbot v{strVersion}: {os.path.basename(self.db_manager.database)}')

        except Exception as e:
            result = False
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.critical(self, 'Save Project',
                         f"Error saving project: {e}", QMessageBox.Ok)
        finally:
            self.db_manager.return_connection(conn)
            return result

    # def saveProject(self):

    #     if not self.db_manager.is_connected():
    #         fileSpec, filter = QtWidgets.QFileDialog.getSaveFileName(
    #             self, "Save Flowbot Project...", self.lastOpenDialogPath, 'Flowbot Project Files (*.fbsqlite)')
    #         if len(fileSpec) == 0:
    #             return
    #         self.db_manager.close_all_connections()
    #         self.db_manager.initialize(fileSpec, pool_size=5)

    #         if self.saveProjectToDatabase():
    #             msg = QMessageBox(self)
    #             msg.setWindowIcon(self.myIcon)
    #             msg.information(self, 'Save Project',
    #                             'Project Saved Sucessfully', QMessageBox.Ok)
    #         else:
    #             self.db_manager.close_all_connections()
    #     else:
    #         if self.saveProjectToDatabase():
    #             msg = QMessageBox(self)
    #             msg.setWindowIcon(self.myIcon)
    #             msg.information(self, 'Save Project',
    #                             'Project Saved Sucessfully', QMessageBox.Ok)

    def saveProject(self):

        if not self.db_manager.is_connected():

            self.saveProjectAs()
            # fileSpec, filter = QtWidgets.QFileDialog.getSaveFileName(
            #     self, "Save Flowbot Project...", self.lastOpenDialogPath, 'Flowbot Project Files (*.fbsqlite)')
            # if len(fileSpec) == 0:
            #     return

            # # Create a temporary file
            # temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.fbsqlite')
            # temp_file.close()  # Close the file so it can be used by the database manager

            # self.db_manager.close_all_connections()
            # self.db_manager.initialize(temp_file.name, pool_size=5)

            # if self.saveProjectToDatabase():
            #     # If saving was successful, replace the original file with the temp file
            #     self.db_manager.close_all_connections()
            #     os.replace(temp_file.name, fileSpec)
            #     self.db_manager.initialize(fileSpec, pool_size=5)
            #     msg = QMessageBox(self)
            #     msg.setWindowIcon(self.myIcon)
            #     msg.information(self, 'Save Project', 'Project Saved Successfully', QMessageBox.Ok)
            # else:
            #     # If saving failed, delete the temporary file
            #     self.db_manager.close_all_connections()
            #     os.remove(temp_file.name)
            #     msg = QMessageBox(self)
            #     msg.setWindowIcon(self.myIcon)
            #     msg.critical(
            #         self, "Save Project", "Failed to save project", QMessageBox.Ok
            #     )
        else:
            # If already connected, save directly to the existing database
            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".fbsqlite")
            temp_file.close()  # Close the file so it can be used by the database manager            
            currentFileSpec = self.db_manager.database
            self.db_manager.close_all_connections()
            self.db_manager.initialize(temp_file.name, pool_size=5)

            if self.saveProjectToDatabase():
                self.db_manager.close_all_connections()
                os.remove(temp_file.name)
                self.db_manager.initialize(currentFileSpec, pool_size=5)
                self.saveProjectToDatabase()
                msg = QMessageBox(self)
                msg.setWindowIcon(self.myIcon)
                msg.information(self, 'Save Project', 'Project Saved Successfully', QMessageBox.Ok)
            else:
                self.db_manager.initialize(currentFileSpec, pool_size=5)
                msg = QMessageBox(self)
                msg.setWindowIcon(self.myIcon)
                msg.critical(self, 'Save Project', 'Failed to save project', QMessageBox.Ok)

            self.setWindowTitle(f'Flowbot v{strVersion}: {os.path.basename(self.db_manager.database)}')

    def saveProjectAs(self):

        fileSpec, filter = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Flowbot Project...", self.lastOpenDialogPath, 'Flowbot Project Files (*.fbsqlite)')
        if len(fileSpec) == 0:
            return

        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.fbsqlite')
        temp_file.close()  # Close the file so it can be used by the database manager
        self.db_manager.close_all_connections()
        self.db_manager.initialize(temp_file.name, pool_size=5)

        if self.saveProjectToDatabase():
            # If saving was successful, replace the original file with the temp file
            self.db_manager.close_all_connections()
            os.replace(temp_file.name, fileSpec)
            self.db_manager.initialize(fileSpec, pool_size=5)
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.information(self, 'Save Project As', 'Project Saved Successfully', QMessageBox.Ok)
        else:
            # If saving failed, delete the temporary file
            self.db_manager.close_all_connections()
            os.remove(temp_file.name)
            self.db_manager.initialize(fileSpec, pool_size=5)
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.critical(
                self, "Save Project As", "Failed to save project", QMessageBox.Ok
            )

        self.setWindowTitle(f'Flowbot v{strVersion}: {os.path.basename(self.db_manager.database)}')
        # self.db_manager.close_all_connections()
        # self.db_manager.initialize(fileSpec, pool_size=5)

        # self.saveProjectToDatabase(self.db_manager)

        # msg = QMessageBox(self)
        # msg.setWindowIcon(self.myIcon)
        # msg.information(self, 'Save Project As',
        #                 'Project Saved Sucessfully', QMessageBox.Ok)

    # def write_fsmproject_to_database(self, conn: sqlite3.Connection):

    #     c = conn.cursor()
    #     c.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.FSM_PROJECT} (
    #                     job_number TEXT PRIMARY KEY,
    #                     job_name: TEXT,
    #                     client TEXT,
    #                     client_job_ref TEXT
    #                 )''')
    #     c.execute(f'''INSERT OR REPLACE INTO {Tables.FSM_PROJECT} VALUES (?, ?, ?, ?)''',
    #               (self.fsmProject.job_number, self.fsmProject.job_name, self.fsmProject.client,
    #                self.fsmProject.client_job_ref))
    #     conn.commit()

    def write_summedFMs_to_database(self, conn: sqlite3.Connection) -> bool:
        result = False

        try:
            conn.execute(f'''DROP TABLE IF EXISTS {Tables.SUMMED_FLOW_MONITOR}''')
            if len(self.summedFMs) > 0:
                # c = conn.cursor()
                conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.SUMMED_FLOW_MONITOR} (
                                sumFMName TEXT,
                                fmNo INTEGER,
                                fmName TEXT,
                                fmMult REAL,
                                CONSTRAINT pk_summed_flow_monitor PRIMARY KEY (sumFMName, fmNo),
                                FOREIGN KEY (fmName) REFERENCES flow_monitor(monitorName)
                            )''')

                for sfm in self.summedFMs.values():
                    i = 0
                    for fm, mult in sfm.fmCollection.values():
                        # c.execute('''INSERT INTO summed_flow_monitor VALUES (?, ?, ?, ?)''',
                        #           (sfm.sumFMName, i, fm.monitorName, mult))
                        conn.execute(f'''INSERT OR REPLACE INTO {Tables.SUMMED_FLOW_MONITOR} VALUES (?, ?, ?, ?)''',
                                (sfm.sumFMName, i, fm.monitorName, mult))
                        i += 1
                conn.commit()
                result = True
            else:
                result = True

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            conn.rollback()
        except Exception as e:
            print(f"Exception in _query: {e}")
            conn.rollback()
        finally:
            return result                

    def write_schematic_graphics_view_to_database(self, conn: sqlite3.Connection) -> bool:
        result = False
        try:
            conn.execute(
                f'''DROP TABLE IF EXISTS {Tables.SCHEMATIC_GRAPHICS_VIEW}''')
            if len(self.schematicGraphicsView.scene().items()) > 0:
                # c = conn.cursor()
                conn.execute(f'''CREATE TABLE {Tables.SCHEMATIC_GRAPHICS_VIEW} (
                                itemType TEXT,
                                labelName TEXT,
                                systemType TEXT,
                                posX REAL,
                                posY REAL,
                                toPosX REAL,
                                toPosY REAL,
                                vertices TEXT
                            )''')

                sgvConnections = []
                for item in self.schematicGraphicsView.scene().items():
                    if isinstance(item, fmGraphicsItem):
                        conn.execute(f'''INSERT INTO {Tables.SCHEMATIC_GRAPHICS_VIEW} VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', ("FM", item._text, "", item.pos().x(), item.pos().y(), 0, 0, ""))
                    elif isinstance(item, rgGraphicsItem):
                        conn.execute(f'''INSERT INTO {Tables.SCHEMATIC_GRAPHICS_VIEW} VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', ("RG", item._text, "", item.pos().x(), item.pos().y(), 0, 0, ""))
                    elif isinstance(item, csoGraphicsItem):
                        conn.execute(f'''INSERT INTO {Tables.SCHEMATIC_GRAPHICS_VIEW} VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (cstCSO, item._text, "", item.pos().x(), item.pos().y(), 0, 0, ""))
                    elif isinstance(item, wwpsGraphicsItem):
                        conn.execute(f'''INSERT INTO {Tables.SCHEMATIC_GRAPHICS_VIEW} VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (cstWWPS, item._text, item._systemType, item.pos().x(), item.pos().y(), 0, 0, ""))
                    elif isinstance(item, wwtwGraphicsItem):
                        conn.execute(f'''INSERT INTO {Tables.SCHEMATIC_GRAPHICS_VIEW} VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (cstWWTW, item._text, "", item.pos().x(), item.pos().y(), 0, 0, ""))
                    elif isinstance(item, juncGraphicsItem):
                        conn.execute(f'''INSERT INTO {Tables.SCHEMATIC_GRAPHICS_VIEW} VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (cstJUNCTION, "", item._systemType, item.pos().x(), item.pos().y(), 0, 0, ""))
                    elif isinstance(item, outfallGraphicsItem):
                        conn.execute(f'''INSERT INTO {Tables.SCHEMATIC_GRAPHICS_VIEW} VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (cstOUTFALL, "", item._systemType, item.pos().x(), item.pos().y(), 0, 0, ""))
                    elif isinstance(item, ConnectionPath):
                        sgvConnections.append(item)
                    else:
                        pass
                for item in sgvConnections:
                    conn.execute(f'''INSERT INTO {Tables.SCHEMATIC_GRAPHICS_VIEW} VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                            (cstCONNECTION, "", item._systemType, item._sourcePoint.x(), item._sourcePoint.y(),
                            item._destinationPoint.x(), item._destinationPoint.y(),
                            serialize_list([{'x': point.x(), 'y': point.y()} for point in item.intermediateVertices])))

                conn.commit()
                result = True
            else:
                result = True

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            conn.rollback()
        except Exception as e:
            print(f"Exception in _query: {e}")
            conn.rollback()
        finally:
            return result        

    # def write_schematic_graphics_view_to_database(self, conn: sqlite3.Connection):
    #     result = False
    #     try:
    #         if len(self.schematicGraphicsView.scene().items()) > 0:
    #             c = conn.cursor()
    #             c.execute(
    #                 f'''DROP TABLE IF EXISTS {Tables.SCHEMATIC_GRAPHICS_VIEW}''')

    #             c.execute(f'''CREATE TABLE {Tables.SCHEMATIC_GRAPHICS_VIEW} (
    #                             itemType TEXT,
    #                             labelName TEXT,
    #                             systemType TEXT,
    #                             posX REAL,
    #                             posY REAL,
    #                             toPosX REAL,
    #                             toPosY REAL,
    #                             vertices TEXT
    #                         )''')

    #             sgvConnections = []
    #             for item in self.schematicGraphicsView.scene().items():
    #                 if isinstance(item, fmGraphicsItem):
    #                     c.execute(f'''INSERT INTO {Tables.SCHEMATIC_GRAPHICS_VIEW} VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', ("FM",
    #                             item._text, "", item.pos().x(), item.pos().y(), 0, 0, ""))
    #                 elif isinstance(item, rgGraphicsItem):
    #                     c.execute(f'''INSERT INTO {Tables.SCHEMATIC_GRAPHICS_VIEW} VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', ("RG",
    #                             item._text, "", item.pos().x(), item.pos().y(), 0, 0, ""))
    #                 elif isinstance(item, csoGraphicsItem):
    #                     c.execute(f'''INSERT INTO {Tables.SCHEMATIC_GRAPHICS_VIEW} VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (cstCSO,
    #                             item._text, "", item.pos().x(), item.pos().y(), 0, 0, ""))
    #                 elif isinstance(item, wwpsGraphicsItem):
    #                     c.execute(f'''INSERT INTO {Tables.SCHEMATIC_GRAPHICS_VIEW} VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (cstWWPS,
    #                             item._text, item._systemType, item.pos().x(), item.pos().y(), 0, 0, ""))
    #                 elif isinstance(item, wwtwGraphicsItem):
    #                     c.execute(f'''INSERT INTO {Tables.SCHEMATIC_GRAPHICS_VIEW} VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (cstWWTW,
    #                             item._text, "", item.pos().x(), item.pos().y(), 0, 0, ""))
    #                 elif isinstance(item, juncGraphicsItem):
    #                     c.execute(f'''INSERT INTO {Tables.SCHEMATIC_GRAPHICS_VIEW} VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (cstJUNCTION,
    #                             "", item._systemType, item.pos().x(), item.pos().y(), 0, 0, ""))
    #                 elif isinstance(item, outfallGraphicsItem):
    #                     c.execute(f'''INSERT INTO {Tables.SCHEMATIC_GRAPHICS_VIEW} VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (cstOUTFALL,
    #                             "", item._systemType, item.pos().x(), item.pos().y(), 0, 0, ""))
    #                 elif isinstance(item, ConnectionPath):
    #                     sgvConnections.append(item)
    #                 else:
    #                     pass
    #             for item in sgvConnections:
    #                 c.execute(f'''INSERT INTO {Tables.SCHEMATIC_GRAPHICS_VIEW} VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
    #                         (cstCONNECTION, "", item._systemType, item._sourcePoint.x(), item._sourcePoint.y(),
    #                         item._destinationPoint.x(), item._destinationPoint.y(),
    #                         serialize_list([{'x': point.x(), 'y': point.y()} for point in item.intermediateVertices])))

    #             conn.commit()
    #             result = True
    #         else:
    #             result = True

    #     except sqlite3.Error as e:
    #         print(f"Database error: {e}")
    #         conn.rollback()
    #     except Exception as e:
    #         print(f"Exception in _query: {e}")
    #         conn.rollback()
    #     finally:
    #         return result

    #             fieldnames = ["dataID", "itemType", "labelName",
    #                           "systemType", "posX", "posY", "toPosX", "toPosY", "vertices"]
    #             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    #             for i in range(len(sgvData["itemType"])):
    #                 writer.writerow({
    #                                 "dataID": sgvData["dataID"][i],
    #                                 "itemType": sgvData["itemType"][i],
    #                                 "labelName": sgvData["labelName"][i],
    #                                 "systemType": sgvData["systemType"][i],
    #                                 "posX": sgvData["posX"][i],
    #                                 "posY": sgvData["posY"][i],
    #                                 "toPosX": sgvData["toPosX"][i],
    #                                 "toPosY": sgvData["toPosY"][i],
    #                                 "vertices": sgvData["vertices"][i]
    #                                 })

    # def saveProject(self):

    # fmData = self.createFMDataTable()
    # sfmData = self.createSFMDataTable()
    # rgData = self.createRGDataTable()
    # seData = self.createSEDataTable()
    #     sgvData = self.createSGVDataTable()
    #     itrData = self.createITRDataTable()
    #     itlData = self.createITLDataTable()

    #     if (len(fmData["dataID"]) + len(sfmData["dataID"]) + len(rgData["dataID"]) + len(seData["dataID"]) + len(sgvData["dataID"]) +
    #         len(itrData["dataID"]) + len(itlData["dataID"])) > 0:

    #         fileSpec, filter = QtWidgets.QFileDialog.getSaveFileName(
    #             self, "Save Flowbot Project...", self.lastOpenDialogPath, 'fbp Files (*.fbp)')
    #         if len(fileSpec) == 0:
    #             return

    #         with open(fileSpec, 'w', newline='') as csvfile:

    #             fieldnames = ["dataID", "monitorName", "fdvFileSpec", "flowUnits", "depthUnits", "velocityUnits", "rainGaugeName",
    #                           "fmTimestep", "minFlow", "maxFlow", "totalVolume", "minDepth", "maxDepth", "minVelocity", "maxVelocity",
    #                           "hasModelData", "modelDataPipeRef", "modelDataRG", "modelDataPipeLength", "modelDataPipeShape",
    #                           "modelDataPipeDia", "modelDataPipeHeight", "modelDataPipeRoughness", "modelDataPipeUSInvert",
    #                           "modelDataPipeDSInvert", "modelDataPipeSystemType"]
    #             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    #             for i in range(len(fmData["monitorName"])):
    #                 writer.writerow({
    #                                 "dataID": fmData["dataID"][i],
    #                                 "monitorName": fmData["monitorName"][i],
    #                                 "fdvFileSpec": fmData["fdvFileSpec"][i],
    #                                 "flowUnits": fmData["flowUnits"][i],
    #                                 "depthUnits": fmData["depthUnits"][i],
    #                                 "velocityUnits": fmData["velocityUnits"][i],
    #                                 "rainGaugeName": fmData["rainGaugeName"][i],
    #                                 "fmTimestep": fmData["fmTimestep"][i],
    #                                 "minFlow": fmData["minFlow"][i],
    #                                 "maxFlow": fmData["maxFlow"][i],
    #                                 "totalVolume": fmData["totalVolume"][i],
    #                                 "minDepth": fmData["minDepth"][i],
    #                                 "maxDepth": fmData["maxDepth"][i],
    #                                 "minVelocity": fmData["minVelocity"][i],
    #                                 "maxVelocity": fmData["maxVelocity"][i],
    #                                 "hasModelData": fmData["hasModelData"][i],
    #                                 "modelDataPipeRef": fmData["modelDataPipeRef"][i],
    #                                 "modelDataRG": fmData["modelDataRG"][i],
    #                                 "modelDataPipeLength": fmData["modelDataPipeLength"][i],
    #                                 "modelDataPipeShape": fmData["modelDataPipeShape"][i],
    #                                 "modelDataPipeDia": fmData["modelDataPipeDia"][i],
    #                                 "modelDataPipeHeight": fmData["modelDataPipeHeight"][i],
    #                                 "modelDataPipeRoughness": fmData["modelDataPipeRoughness"][i],
    #                                 "modelDataPipeUSInvert": fmData["modelDataPipeUSInvert"][i],
    #                                 "modelDataPipeDSInvert": fmData["modelDataPipeDSInvert"][i],
    #                                 "modelDataPipeSystemType": fmData["modelDataPipeSystemType"][i]
    #                                 })

    #             writer.writerow({"dataID": "FM_END"})

    #             fieldnames = ["dataID", "sumFMName",
    #                           "fmNo", "fmName", "fmMult"]
    #             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    #             for i in range(len(sfmData["sumFMName"])):
    #                 writer.writerow({
    #                                 "dataID": sfmData["dataID"][i],
    #                                 "sumFMName": sfmData["sumFMName"][i],
    #                                 "fmNo": sfmData["fmNo"][i],
    #                                 "fmName": sfmData["fmName"][i],
    #                                 "fmMult": sfmData["fmMult"][i]
    #                                 })

    #             writer.writerow({"dataID": "SFM_END"})

    #             fieldnames = ["dataID", "gaugeName", "rFileSpec", "rgTimestep",
    #                           "minIntensity", "maxIntensity", "totalDepth", "returnPeriod"]
    #             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    #             for i in range(len(rgData["gaugeName"])):
    #                 writer.writerow({
    #                                 "dataID": rgData["dataID"][i],
    #                                 "gaugeName": rgData["gaugeName"][i],
    #                                 "rFileSpec": rgData["rFileSpec"][i],
    #                                 "rgTimestep": rgData["rgTimestep"][i],
    #                                 "minIntensity": rgData["minIntensity"][i],
    #                                 "maxIntensity": rgData["maxIntensity"][i],
    #                                 "totalDepth": rgData["totalDepth"][i],
    #                                 "returnPeriod": rgData["returnPeriod"][i]
    #                                 })

    #             writer.writerow({"dataID": "RG_END"})

    #             fieldnames = ["dataID", "eventName",
    #                           "eventType", "eventStart", "eventEnd"]
    #             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    #             for i in range(len(seData["eventName"])):
    #                 writer.writerow({
    #                                 "dataID": seData["dataID"][i],
    #                                 "eventName": seData["eventName"][i],
    #                                 "eventType": seData["eventType"][i],
    #                                 "eventStart": seData["eventStart"][i].strftime("%d/%m/%Y %H:%M"),
    #                                 "eventEnd": seData["eventEnd"][i].strftime("%d/%m/%Y %H:%M")
    #                                 })

    #             writer.writerow({"dataID": "SE_END"})

    #             fieldnames = ["dataID", "itemType", "labelName",
    #                           "systemType", "posX", "posY", "toPosX", "toPosY", "vertices"]
    #             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    #             for i in range(len(sgvData["itemType"])):
    #                 writer.writerow({
    #                                 "dataID": sgvData["dataID"][i],
    #                                 "itemType": sgvData["itemType"][i],
    #                                 "labelName": sgvData["labelName"][i],
    #                                 "systemType": sgvData["systemType"][i],
    #                                 "posX": sgvData["posX"][i],
    #                                 "posY": sgvData["posY"][i],
    #                                 "toPosX": sgvData["toPosX"][i],
    #                                 "toPosY": sgvData["toPosY"][i],
    #                                 "vertices": sgvData["vertices"][i]
    #                                 })

    #             writer.writerow({"dataID": "SGV_END"})

    #             fieldnames = ["dataID", "traceID", "csvFileSpec"]
    #             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    #             for i in range(len(itrData["traceID"])):
    #                 writer.writerow({
    #                                 "dataID": itrData["dataID"][i],
    #                                 "traceID": itrData["traceID"][i],
    #                                 "csvFileSpec": itrData["csvFileSpec"][i]
    #                                 })

    #             writer.writerow({"dataID": "TR_END"})

    #             fieldnames = ["dataID", "traceID", "index", "isCritical", "isSurcharged", "peaksInitialized", "verifyForFlow",
    #                           "verifyForDepth", "frac", "peaks_prominance", "peaks_width", "peaks_distance",
    #                           "verificationDepthComment", "verificationFlowComment", "verificationOverallComment"]
    #             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    #             for i in range(len(itlData["traceID"])):
    #                 writer.writerow({
    #                                 "dataID": itlData["dataID"][i],
    #                                 "traceID": itlData["traceID"][i],
    #                                 "index": itlData["index"][i],
    #                                 "isCritical": itlData["isCritical"][i],
    #                                 "isSurcharged": itlData["isSurcharged"][i],
    #                                 "peaksInitialized": itlData["peaksInitialized"][i],
    #                                 "verifyForFlow": itlData["verifyForFlow"][i],
    #                                 "verifyForDepth": itlData["verifyForDepth"][i],
    #                                 "frac": itlData["frac"][i],
    #                                 "peaks_prominance": itlData["peaks_prominance"][i],
    #                                 "peaks_width": itlData["peaks_width"][i],
    #                                 "peaks_distance": itlData["peaks_distance"][i],
    #                                 "verificationDepthComment": itlData["verificationDepthComment"][i],
    #                                 "verificationFlowComment": itlData["verificationFlowComment"][i],
    #                                 "verificationOverallComment": itlData["verificationOverallComment"][i]
    #                                 })

    #             writer.writerow({"dataID": "TL_END"})

    #         msg = QMessageBox(self)
    #         msg.setWindowIcon(self.myIcon)
    #         msg.information(self, 'Save Project',
    #                         'Project Saved Sucessfully', QMessageBox.Ok)
    #     else:

    #         msg = QMessageBox(self)
    #         msg.setWindowIcon(self.myIcon)
    #         msg.information(self, 'Save Project',
    #                         'No Data to Save', QMessageBox.Ok)

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
                if isinstance(item, ConnectionPath):
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

        if self.openFlowMonitors is not None:
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

        if self.summedFMs is not None:
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

        if self.openRainGauges is not None:
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

        if self.identifiedSurveyEvents is not None:
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

        if self.openIcmTraces is not None:
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

        if self.openIcmTraces is not None:
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

    # def closeApplication(self):
    #     msg = QMessageBox(self)
    #     msg.setWindowIcon(self.myIcon)
    #     ret = msg.warning(
    #         self, 'Warning', 'Are you sure you want to exit?', QMessageBox.Yes | QMessageBox.No)
    #     if ret == QMessageBox.Yes:
    #         sys.exit()

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
            self._thisApp.processEvents()
        self.statusBar().clearMessage()
        self.progressBar.hide()
        self._thisApp.processEvents()
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
            self._thisApp.processEvents()
        self.statusBar().clearMessage()
        self.progressBar.hide()
        self._thisApp.processEvents()
        self.refreshRainGaugeListWidget()
        self.lastOpenDialogPath = os.path.dirname(path[0])

    def remove_all_FM_files(self):

        if self.aFDVGraph is not None:
            self.aFDVGraph.plotted_fms = plottedFlowMonitors()
        self.aScattergraph = graphScatter(self.plotCanvasMain)
        if self.aDataClassification is not None:
            self.aDataClassification.classifiedFMs = classifiedFlowMonitors()
        self.a_dwf_graph = graphDWF(self.plotCanvasMain)
        self.openFlowMonitors = None
        self.refreshFlowMonitorListWidget()
        self.summedFMs = None
        self.updateSummedFMTreeView()
        self.update_plot()

    def remove_all_RG_files(self):

        if self.aFDVGraph is not None:
            self.aFDVGraph.plotted_rgs = plottedRainGauges()
        if self.aCumDepthGraph is not None:
            self.aCumDepthGraph.plotted_rgs = plottedRainGauges()
        if self.aRainfallAnalysis is not None:
            self.aRainfallAnalysis.plotted_rgs = plottedRainGauges()
        self.update_plot()
        self.openRainGauges = None
        self.refreshRainGaugeListWidget()

    def editRainfallAnalysisParams(self):

        editRainfallAnalysisParamsDialog = flowbot_dialog_event_analysis_params(
            self.aRainfallAnalysis, self)
        editRainfallAnalysisParamsDialog.setWindowTitle(
            'Edit Rainfall Analysis Parameters')
        # editRainfallAnalysisParamsDialog.show()
        ret = editRainfallAnalysisParamsDialog.exec_()
        if ret == QDialog.Accepted:
            self.aRainfallAnalysis.analysisNeedsRefreshed = True
            self.update_plot()

    def editDataClassificationParams(self):

        if self.aDataClassification is not None:
            editDataClassificationParamsDialog = flowbot_dialog_data_classification(
                self.aDataClassification, self)
            editDataClassificationParamsDialog.setWindowTitle(
                'Edit Data Classification Parameters')
            # editDataClassificationParamsDialog.show()
            ret = editDataClassificationParamsDialog.exec_()
            if ret == QDialog.Accepted:
                self.aDataClassification.classificationNeedsRefreshed = True
                self.update_plot()

    def removeFMSPlotItem(self):
        self.aFSMInstallGraph = graphFSMInstall(self.plotCanvasMain)
        self.update_plot()

    def removeTreeItem(self):

        if self.tbxGraphs.currentWidget().objectName() == "pageFDV":
            if self.aFDVGraph is not None:
                item = self.trw_PlottedMonitors.selectedItems()[0]
                if item.parent().text(0) == "Flow Monitors":
                    self.aFDVGraph.plotted_fms.removeFM(item.text(0))
                elif item.parent().text(0) == "Rain Gauges":
                    self.aFDVGraph.plotted_rgs.removeRG(item.text(0))
                elif item.parent().text(0) == "Event":
                    self.aFDVGraph.set_plot_event(None)

        elif self.tbxGraphs.currentWidget().objectName() == "pageScattergraphs":
            if self.aScattergraph is not None:
                item = self.trw_Scattergraph.selectedItems()[0]
                if item.parent().text(0) == "Flow Monitor":
                    self.aScattergraph.plot_flow_monitor = None
                elif item.parent().text(0) == "Events":
                    self.aScattergraph.plotted_events.removeSurveyEvent(
                        item.text(0))

        if self.tbxGraphs.currentWidget().objectName() == "pageRainfallCumDepth":
            if self.aCumDepthGraph is not None:
                item = self.trw_CumDepth.selectedItems()[0]
                if item.parent().text(0) == "Rain Gauges":
                    self.aCumDepthGraph.plotted_rgs.removeRG(item.text(0))
                elif item.parent().text(0) == "Event":
                    self.aCumDepthGraph.set_plot_event(None)

        if self.tbxGraphs.currentWidget().objectName() == "pageRainfallAnalysis":
            if self.aRainfallAnalysis is not None:
                item = self.trw_RainfallAnalysis.selectedItems()[0]
                if item.parent().text(0) == "Rain Gauges":
                    self.aRainfallAnalysis.analysisNeedsRefreshed = True
                    self.aRainfallAnalysis.plotted_rgs.removeRG(item.text(0))

        if self.tbxGraphs.currentWidget().objectName() == "pageDataClassification":
            if self.aDataClassification is not None:
                item = self.trw_DataClassification.selectedItems()[0]
                if item.parent().text(0) == "Flow Monitors":
                    self.aDataClassification.classifiedFMs.removeFM(
                        item.text(0))
                    self.aDataClassification.classificationNeedsRefreshed = True
                elif item.parent().text(0) == "Events":
                    self.aDataClassification.plottedEvents.removeSurveyEvent(
                        item.text(0))

        elif self.tbxGraphs.currentWidget().objectName() == "pageDryWeatherFlow":
            if self.a_dwf_graph is not None:
                item = self.trw_DWF_Analysis.selectedItems()[0]
                if item.parent().text(0) == "Flow Monitor":
                    self.a_dwf_graph.plot_flow_monitor = None
                elif item.parent().text(0) == "Events":
                    self.a_dwf_graph.plotted_events.removeSurveyEvent(
                        item.text(0))                    

        self.update_plot()

    def removeTreeItems(self):

        if self.tbxGraphs.currentWidget().objectName() == "pageFDV":
            if self.aFDVGraph is not None:
                item = self.trw_PlottedMonitors.currentItem()
                if item.text(0) == "Flow Monitors":
                    self.aFDVGraph.plotted_fms = plottedFlowMonitors()
                elif item.text(0) == "Rain Gauges":
                    self.aFDVGraph.plotted_rgs = plottedRainGauges()
                elif item.text(0) == "Event":
                    self.aFDVGraph.set_plot_event(None)

        if self.tbxGraphs.currentWidget().objectName() == "pageScattergraphs":
            if self.aScattergraph is not None:
                item = self.trw_Scattergraph.currentItem()
                if item.text(0) == "Flow Monitor":
                    self.aScattergraph.plot_flow_monitor = None
                elif item.text(0) == "Events":
                    self.aScattergraph.plotted_events = plottedSurveyEvents()

        if self.tbxGraphs.currentWidget().objectName() == "pageRainfallCumDepth":
            if self.aCumDepthGraph is not None:
                item = self.trw_CumDepth.currentItem()
                if item.text(0) == "Rain Gauges":
                    self.aCumDepthGraph.plotted_rgs = plottedRainGauges()
                elif item.text(0) == "Event":
                    self.aCumDepthGraph.set_plot_event(None)

        if self.tbxGraphs.currentWidget().objectName() == "pageRainfallAnalysis":
            if self.aRainfallAnalysis is not None:
                item = self.trw_RainfallAnalysis.currentItem()
                if item.text(0) == "Rain Gauges":
                    self.aRainfallAnalysis.plotted_rgs = plottedRainGauges()
                    self.aRainfallAnalysis.analysisNeedsRefreshed = True

        if self.tbxGraphs.currentWidget().objectName() == "pageDataClassification":
            if self.aDataClassification is not None:
                item = self.trw_DataClassification.currentItem()
                if item.text(0) == "Flow Monitors":
                    self.aDataClassification.classifiedFMs = classifiedFlowMonitors()
                    self.aDataClassification.classificationNeedsRefreshed = True
                elif item.text(0) == "Events":
                    self.aDataClassification.plottedEvents = plottedSurveyEvents()

        if self.tbxGraphs.currentWidget().objectName() == "pageDryWeatherFlow":
            if self.a_dwf_graph is not None:
                item = self.trw_DWF_Analysis.currentItem()
                if item.text(0) == "Flow Monitor":
                    self.a_dwf_graph.plot_flow_monitor = None
                elif item.text(0) == "Events":
                    self.a_dwf_graph.plotted_events = plottedSurveyEvents()

        self.update_plot()

    def openFlowMonitorsListContextMenu(self, position):

        if self.lst_FlowMonitors.currentItem() is not None:
            rightMenu = QMenu(self.lst_FlowMonitors)
            rightMenu.addAction(
                QAction('Remove Monitor(s)', self, triggered=self.remove_FM_file))
            rightMenu.addAction(
                QAction('Model Data', self, triggered=self.editModelData))
            if self.mappedFlowMonitors is not None:
                if self.mappedFlowMonitors.isMapped(self.lst_FlowMonitors.currentItem().text()):
                    rightMenu.addSeparator()
                    rightMenu.addAction(
                        QAction('Zoom to', self, triggered=self.zoomTo))
                    rightMenu.addAction(
                        QAction('Clear Location', self, triggered=self.clearLocation))
            rightMenu.exec_(QCursor.pos())

    # def zoomTo(self):

    #     self.flowbotWebMap.zoomTo(self.mappedFlowMonitors.locationByFMName(
    #         self.lst_FlowMonitors.currentItem().text()), 18)
    #     self.updateMapView()

    def clearLocation(self):
        pass

    def openRainGaugeListContextMenu(self, position):

        if not self.lst_RainGauges.currentItem() is None:
            rightMenu = QMenu(self.lst_RainGauges)
            rightMenu.addAction(
                QAction('Remove Gauge(s)', self, triggered=self.remove_RG_file))
            rightMenu.exec_(QCursor.pos())

    def openPlottedInstallsTreeViewContextMenu(self, position):
        level = self.getTreeViewLevel(self.trw_PlottedFSMInstalls)
        menu = QMenu()
        if level == 1:
            remCallback = QtWidgets.QAction("Remove Plot", menu)
            remCallback.triggered.connect(self.removeFMSPlotItem)
            menu.addAction(remCallback)

        menu.exec_(self.trw_PlottedFSMInstalls.viewport().mapToGlobal(position))

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
        if self.tbxGraphs.currentWidget().objectName() == "pageDryWeatherFlow":
            treeWidget = self.trw_DWF_Analysis

        if treeWidget is not None:
            level = self.getTreeViewLevel(treeWidget)
            menu = QMenu()
            if level == 0:
                if treeWidget.itemAt(position) is not None:
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

            if (self.summedFMs is not None) and (len(self.summedFMs) > 0):

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
            if (self.dummyFMs is not None) and (len(self.dummyFMs) > 0):

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
            remCallback.setChecked(self.aTraceGraph.plottedICMTrace.plotTrace.allVerifiedForDepth()
                                   and self.aTraceGraph.plottedICMTrace.plotTrace.allVerifiedForFlow())
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

            if aLoc.shortTitle not in self.dummyFMs:
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
        # viewFitMeasuresDialog.show()
        viewFitMeasuresDialog.exec_()
        # ret = viewFitMeasuresDialog.exec_()

    def toggleCriticality(self, aLoc: icmTraceLocation):
        aLoc.isCritical = not aLoc.isCritical
        self.update_plot()

    def toggleSurcharged(self, aLoc: icmTraceLocation):
        aLoc.isSurcharged = not aLoc.isSurcharged
        self.update_plot()

    # def toggleVerifBoth(self, aLoc: icmTraceLocation):

    #     if aLoc.verifyForFlow is True and aLoc.verifyForDepth is True:
    #         aLoc.verifyForFlow = False
    #         aLoc.verifyForDepth = False
    #     elif aLoc.verifyForFlow is False and aLoc.verifyForDepth is False:
    #         aLoc.verifyForFlow = True
    #         aLoc.verifyForDepth = True
    #     else:
    #         aLoc.verifyForFlow = True
    #         aLoc.verifyForDepth = True

    #     self.update_plot()

    def toggleVerifBoth(self, aLoc: icmTraceLocation):
        aLoc.verifyForFlow = not (aLoc.verifyForFlow and aLoc.verifyForDepth)
        aLoc.verifyForDepth = aLoc.verifyForFlow
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
        if self.aTraceGraph is not None:
            self.aTraceGraph.plottedICMTrace.plotTrace = None
            self.update_plot()

    def addICMTracePeak(self, aLoc: icmTraceLocation, isFlow: bool = True):

        setPeaksDialog = flowbot_dialog_verification_setpeaks(aLoc, isFlow)
        setPeaksDialog.setWindowTitle('Set Peaks')
        # setPeaksDialog.show()
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
            if text not in self.summedFMs:
                sFM = summedFlowMonitor()
                sFM.sumFMName = text
                self.summedFMs[text] = sFM

                self.updateSummedFMTreeView()

    def summedFM_Rename(self):

        item = self.trwSummedFMs.selectedItems()[0]
        text, ok = QInputDialog.getText(
            self, 'Rename Summed FM', 'Name for Summed FM:')
        if ok:
            if text not in self.summedFMs:
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
        if item.parent() is not None:
            if item.parent().text(0) in self.summedFMs:
                sFM = self.summedFMs[item.parent().text(0)]
                sFM.removeFM(item.text(0))
                self.summedFMs[item.parent().text(0)] = sFM
                self.updateSummedFMTreeView()
                self.update_plot()

    def summedFM_RemoveFM(self, fmName):
        if self.summedFMs:
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
            # editMultipliers.show()
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
                    if sFM.equivalentFM.monitorName == self.aScattergraph.plot_flow_monitor.monitorName:
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

        if self.aFDVGraph is not None:
            self.aFDVGraph.plotted_fms = plottedFlowMonitors()
        self.aScattergraph = graphScatter(self.plotCanvasMain)
        self.a_dwf_graph = graphDWF(self.plotCanvasMain)

        self.dummyFMs.clear()
        self.dummyFMs = None
        self.updateDummyFMTreeView()
        self.update_plot()

    # def remove_FM_file(self):

    #     if self.removeFMFromAllPlots(self.lst_FlowMonitors.currentItem().text()):
    #         self.update_plot()
    #     self.openFlowMonitors.removeFlowMonitor(
    #         self.lst_FlowMonitors.currentItem().text())
    #     self.summedFM_RemoveFM(self.lst_FlowMonitors.currentItem().text())
    #     self.refreshFlowMonitorListWidget()

    def remove_FM_file(self):
        selected_items = self.lst_FlowMonitors.selectedItems()

        if not selected_items:
            return  # Nothing selected, exit early
        plot_affected = False
        for item in selected_items:
            monitor_name = item.text()
            if self.removeFMFromAllPlots(monitor_name):
                plot_affected = True
            self.openFlowMonitors.removeFlowMonitor(monitor_name)
            self.summedFM_RemoveFM(monitor_name)

        if plot_affected:
            self.update_plot()
        self.refreshFlowMonitorListWidget()

    def remove_RG_file(self):
        selected_items = self.lst_RainGauges.selectedItems()

        if not selected_items:
            return  # Nothing selected, exit early
        plot_affected = False
        for item in selected_items:
            raingauge_name = item.text()
            if self.removeRGFromAllPlots(raingauge_name):
                plot_affected = True
            self.openRainGauges.removeRainGauge(raingauge_name)

        if plot_affected:
            self.update_plot()
        self.refreshRainGaugeListWidget()

    def editModelData(self):

        fm = self.openFlowMonitors.getFlowMonitor(
            self.lst_FlowMonitors.currentItem().text())

        editFMDataDialog = flowbot_dialog_fmdataentry(
            fm, self.importedICMData, self)
        editFMDataDialog.setWindowTitle('Edit FM Data Dialog')
        # editFMDataDialog.show()
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
        except Exception as e:
            msg = QMessageBox(self)
            msg.setWindowIcon(self.myIcon)
            msg.critical(self, 'Error', f'Import Abandoned: {str(e)}')

    def dummyFM_AddModelData(self):

        if (self.dummyFMs is not None) and len(self.dummyFMs) > 0:
            self.dlgModelData = flowbot_dialog_modeldata(
                self.dummyFMs, self.importedICMData, self)
            self.dlgModelData.setWindowTitle('Model Data Dialog')
            # self.dlgModelData.show()
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

        if self.openFlowMonitors is not None and self.openFlowMonitors.flowMonitorCount() > 0:
            self.dlgModelData = flowbot_dialog_modeldata(
                self.openFlowMonitors, self.importedICMData, self)
            self.dlgModelData.setWindowTitle('Model Data Dialog')
            # self.dlgModelData.show()
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
        # dlgNewEvent.show()
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
        if self.openFlowMonitors is not None:
            for fm in self.openFlowMonitors.dictFlowMonitors.items():
                self.lst_FlowMonitors.addItem(fm[1].monitorName)
            if self.mappedFlowMonitors is not None:
                for mFM in self.mappedFlowMonitors.dictMappedFlowMonitors.items():
                    if mFM[1].monitorName in self.openFlowMonitors.dictFlowMonitors:
                        myIcon = QtGui.QIcon()
                        # myIcon.addPixmap(QtGui.QPixmap(":/icons/resources/mapPin.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                        pixmap = QtGui.QPixmap(":/icons/resources/mapPin.png")
                        pixmap_resized = pixmap.scaled(16, 16)
                        myIcon.addPixmap(
                            pixmap_resized, QtGui.QIcon.Normal, QtGui.QIcon.Off)
                        self.addIconToItem(
                            self.lst_FlowMonitors, mFM[1].monitorName, myIcon)
                        # self.lst_FlowMonitors.addItem(fm[1].monitorName)

    def addIconToItem(self, listWidget: QListWidget, item_text: str, icon: QtGui.QIcon):
        for index in range(listWidget.count()):
            item = listWidget.item(index)
            if item.text() == item_text:
                item.setIcon(icon)
                break

    def refreshRainGaugeListWidget(self):

        self.lst_RainGauges.clear()
        if self.openRainGauges is not None:
            for rg in self.openRainGauges.dictRainGauges.items():
                self.lst_RainGauges.addItem(rg[1].gaugeName)

    def refreshICMTraceListWidget(self):
        self.lst_ICMTraces.clear()
        if self.openIcmTraces is not None:
            for tr in self.openIcmTraces.dictIcmTraces.items():
                self.lst_ICMTraces.addItem(tr[1].traceID)

    def update_plottedTreeView(self):

        if self.mainToolBox.currentWidget().objectName() == 'pageFlowSurveyAnalysis':
            if self.tbxGraphs.currentWidget().objectName() == "pageFDV":
                if self.aFDVGraph is not None:
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
                if self.aScattergraph is not None:
                    root = self.trw_Scattergraph.invisibleRootItem()
                    child_count = root.childCount()

                    for i in range(child_count):
                        item = root.child(i)

                        if item.text(0) == 'Flow Monitor':
                            for i in range(item.childCount()):
                                item.removeChild(item.child(0))

                            if self.aScattergraph.plot_flow_monitor is not None:
                                it = QtWidgets.QTreeWidgetItem()
                                it.setText(
                                    0, self.aScattergraph.plot_flow_monitor.monitorName)
                                item.addChild(it)

                            if item.childCount() > 0:
                                item.setExpanded(True)

                        elif item.text(0) == 'Events':
                            for i in range(item.childCount()):
                                item.removeChild(item.child(0))

                            for se in self.aScattergraph.plotted_events.plotEvents:
                                it = QtWidgets.QTreeWidgetItem()
                                it.setText(0, se)
                                item.addChild(it)

                            if item.childCount() > 0:
                                item.setExpanded(True)

                        else:
                            root.removeChild(item)

            elif self.tbxGraphs.currentWidget().objectName() == "pageRainfallCumDepth":
                if self.aCumDepthGraph is not None:
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
                if self.aRainfallAnalysis is not None:
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
                if self.aDataClassification is not None:
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

            elif self.tbxGraphs.currentWidget().objectName() == "pageDryWeatherFlow":
                if self.a_dwf_graph is not None:
                    root = self.trw_DWF_Analysis.invisibleRootItem()
                    child_count = root.childCount()

                    for i in range(child_count):
                        item = root.child(i)

                        if item.text(0) == 'Flow Monitor':
                            for i in range(item.childCount()):
                                item.removeChild(item.child(0))

                            if self.a_dwf_graph.plot_flow_monitor is not None:
                                it = QtWidgets.QTreeWidgetItem()
                                it.setText(
                                    0, self.a_dwf_graph.plot_flow_monitor.monitorName)
                                item.addChild(it)

                            if item.childCount() > 0:
                                item.setExpanded(True)

                        elif item.text(0) == 'Events':
                            for i in range(item.childCount()):
                                item.removeChild(item.child(0))

                            for se in self.a_dwf_graph.plotted_events.plotEvents:
                                it = QtWidgets.QTreeWidgetItem()
                                it.setText(0, se)
                                item.addChild(it)

                            if item.childCount() > 0:
                                item.setExpanded(True)

                        else:
                            root.removeChild(item)                        

        elif self.mainToolBox.currentWidget().objectName() == 'pageFlowSurveyAnalysis':
            if self.tbxVerification.currentWidget().objectName() == "pageVerificationPlots":

                if self.aTraceGraph is not None:
                    root = self.trw_PlottedICMTraces.invisibleRootItem()
                    child_count = root.childCount()

                    if child_count > 0:
                        traceItem = root.child(0)
                        if self.aTraceGraph.plottedICMTrace.plotTrace is not None:
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

                    if self.aTraceGraph.plottedICMTrace.plotTrace is not None:
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

        elif self.mainToolBox.currentWidget().objectName() == 'pageWaterQuality':

            if self.aWQGraph is not None:
                root = self.trw_PlottedWQMonitors.invisibleRootItem()
                child_count = root.childCount()

                for i in range(child_count):
                    item = root.child(i)

                    if item.text(0) == 'WQ Monitors':
                        for i in range(item.childCount()):
                            item.removeChild(item.child(0))

                        for wq in self.aWQGraph.plotted_wqs.plotWQs:
                            it = QtWidgets.QTreeWidgetItem()
                            it.setText(0, wq)
                            item.addChild(it)

                        if item.childCount() > 0:
                            item.setExpanded(True)

                    else:
                        root.removeChild(item)

        elif self.mainToolBox.currentWidget().objectName() == 'pageFlowSurveyManagement':

            if self.aFSMInstallGraph is not None:
                root = self.trw_PlottedFSMInstalls.invisibleRootItem()
                child_count = root.childCount()

                for i in range(child_count):
                    item = root.child(i)

                    if item.text(0) == 'Installs':
                        for i in range(item.childCount()):
                            item.removeChild(item.child(0))

                        # for inst in self.aFSMInstallGraph.plotted_installs.plotInstalls.values():
                        #     it = QtWidgets.QTreeWidgetItem()
                        #     it.setText(
                        #         0, f'Site ID: {inst.install_site_id}/Monitor ID: {inst.install_monitor_asset_id}')
                        #     item.addChild(it)
                        if self.aFSMInstallGraph.plotted_install is not None:
                            it = QtWidgets.QTreeWidgetItem()
                            it.setText(
                                0, f'Install ID: {self.aFSMInstallGraph.plotted_install.install_id}')
                            item.addChild(it)

                        if item.childCount() > 0:
                            item.setExpanded(True)

                    else:
                        root.removeChild(item)

    def updateICMTraceButtons(self):
        self.btnTracePrev.setEnabled(False)
        self.btnTraceNext.setEnabled(False)
        if self.aTraceGraph is not None:
            if self.aTraceGraph.plottedICMTrace.plotTrace is not None:
                if self.aTraceGraph.plottedICMTrace.plotTrace.currentLocation == 0:
                    self.btnTracePrev.setEnabled(False)
                    self.btnTraceNext.setEnabled(True)
                elif (self.aTraceGraph.plottedICMTrace.plotTrace.currentLocation ==
                      len(self.aTraceGraph.plottedICMTrace.plotTrace.dictLocations) - 1):
                    self.btnTracePrev.setEnabled(True)
                    self.btnTraceNext.setEnabled(False)
                else:
                    self.btnTracePrev.setEnabled(True)
                    self.btnTraceNext.setEnabled(True)

                root = self.trw_PlottedICMTraces.invisibleRootItem()
                if root.child(0) is not None:
                    item = root.child(0)
                    self.trw_PlottedICMTraces.selectionModel().clearSelection()
                    item.child(
                        self.aTraceGraph.plottedICMTrace.plotTrace.currentLocation).setSelected(True)

    def updateSummedFMTreeView(self):

        self.trwSummedFMs.clear()

        root = self.trwSummedFMs.invisibleRootItem()
        child_count = root.childCount()

        if self.summedFMs is not None:
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

                if self.dummyFMs is not None:
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

        # This is a naff section to disconnect events specific to individual graphs from the shared canvas
        # for conn_id in self.plotCanvasMain.event_connections
        while self.plotCanvasMain.event_connections:
            conn_id = self.plotCanvasMain.event_connections.pop(0)
            self.plotCanvasMain.figure.canvas.mpl_disconnect(conn_id)

        if self.mainToolBox.currentWidget().objectName() == 'pageFlowSurveyAnalysis':
            if self.tbxGraphs.currentWidget().objectName() == "pageFDV":
                if self.aFDVGraph is not None:
                    self.aFDVGraph.update_plot()

            if self.tbxGraphs.currentWidget().objectName() == "pageScattergraphs":
                if self.aScattergraph is not None:
                    self.aScattergraph.update_plot()

            if self.tbxGraphs.currentWidget().objectName() == "pageRainfallCumDepth":
                if self.aCumDepthGraph is not None:
                    self.dteScattergraphStart.setMinimumDateTime(
                        self.aCumDepthGraph.plotted_rgs.plotEarliestStart)
                    self.dteScattergraphStart.setMaximumDateTime(
                        self.aCumDepthGraph.plotted_rgs.plotLatestEnd)
                    self.aCumDepthGraph.startDate = self.dteScattergraphStart.dateTime()
                    self.aCumDepthGraph.update_plot()
            if self.tbxGraphs.currentWidget().objectName() == "pageRainfallAnalysis":
                if self.aRainfallAnalysis is not None:
                    self.dteRainfallAnalysisStart.setMinimumDateTime(
                        self.aRainfallAnalysis.plotted_rgs.plotEarliestStart)
                    self.dteRainfallAnalysisStart.setMaximumDateTime(
                        self.aRainfallAnalysis.plotted_rgs.plotLatestEnd)
                    self.aRainfallAnalysis.startDate = self.dteRainfallAnalysisStart.dateTime()
                    self.aRainfallAnalysis.update_plot()

            if self.tbxGraphs.currentWidget().objectName() == "pageDataClassification":
                if self.aDataClassification is not None:
                    self.aDataClassification.updatePlot()

            if self.tbxGraphs.currentWidget().objectName() == "pageDryWeatherFlow":
                if self.a_dwf_graph is not None:
                    self.a_dwf_graph.update_plot()                    

        elif self.mainToolBox.currentWidget().objectName() == 'pageVerificationAnalysis':
            if self.tbxVerification.currentWidget().objectName() == "pageVerificationPlots":
                if self.aTraceGraph is not None:
                    self.aTraceGraph.update_plot()

                self.updateICMTraceButtons()

        elif self.mainToolBox.currentWidget().objectName() == 'pageWaterQuality':
            if self.aWQGraph is not None:
                self.aWQGraph.update_plot(
                    self.rbnWQRawValues.isChecked(), self.cboWQFrequency.currentText())

        elif self.mainToolBox.currentWidget().objectName() == 'pageFlowSurveyManagement':
            if self.aFSMInstallGraph is not None:
                self.aFSMInstallGraph.update_plot(
                    self.rbnFSMRawValues.isChecked(), self.chkShowAdjustments.isChecked())
            self.chkShowAdjustments.setEnabled(
                self.rbnFSMRawValues.isChecked())

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

        if (startDate is not None) and (endDate is not None):
            dlgNewEvent.dteEventStart.setDateTime(startDate)
            dlgNewEvent.dteEventEnd.setDateTime(endDate)

        # dlgNewEvent.show()
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

        if (self.openFlowMonitors is not None) or ((self.dummyFMs is not None) and (len(self.dummyFMs) > 0)):
            if self.aScattergraph is not None:
                dlgScattergraphOptions = flowbot_dialog_scattergraphoptions(
                    self.aScattergraph)
                dlgScattergraphOptions.setWindowTitle('Scattergraph Dialog')
                # dlgScattergraphOptions.show()
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
        if self.openFlowMonitors is not None:
            if self.aDataClassification is not None:
                self.aDataClassification.updateFlowSurveyDataClassification()
                self.update_plot()

    def exportDataClassification(self):

        if self.openFlowMonitors is not None:
            if self.aDataClassification is not None:
                exportDataClassificationDialog = flowbot_dialog_data_classification_export(
                    self)
                exportDataClassificationDialog.setWindowTitle(
                    'Export Data Classification to Excel')
                # exportDataClassificationDialog.show()
                ret = exportDataClassificationDialog.exec_()
                if ret == QDialog.Accepted:
                    self.aDataClassification.strOutputFileSpec = exportDataClassificationDialog.edtOutputFileSpec.text()
                    self.aDataClassification.exportDataClassificationToExcel()
                    self.update_plot()

    def exportScattergraphs(self):

        if self.openFlowMonitors is not None:
            if self.aScattergraph is not None:
                exportScattergraphDialog = flowbot_dialog_scattergraph_export(
                    self.openFlowMonitors)
                exportScattergraphDialog.setWindowTitle('Export Scattergraphs')
                # exportScattergraphDialog.show()
                ret = exportScattergraphDialog.exec_()
                if ret == QDialog.Accepted:
                    self.statusBar().showMessage('Exporting Scattergraphs: ')
                    self.progressBar.setMinimum(0)
                    self.progressBar.setValue(0)
                    self.progressBar.show()
                    self.progressBar.setMaximum(
                        len(exportScattergraphDialog.lst_FlowMonitors.selectedItems()))

                    currentFM = self.aScattergraph.plot_flow_monitor
                    iCount = 0
                    for fm_name in exportScattergraphDialog.lst_FlowMonitors.selectedItems():
                        self.statusBar().showMessage('Exporting Scattergraphs: ' + fm_name.text())
                        self.aScattergraph.plot_flow_monitor = self.openFlowMonitors.getFlowMonitor(fm_name.text())
                        self.aScattergraph.update_plot()
                        scatFileSpec = exportScattergraphDialog.outputFolder + '/' + fm_name.text() + \
                            '.jpg'
                        self.aScattergraph.main_window_plot_widget.figure.savefig(
                            scatFileSpec)
                        self.progressBar.setValue(iCount)
                        iCount += 1
                        self._thisApp.processEvents()
                    self.aScattergraph.plot_flow_monitor = currentFM
                    self.aScattergraph.update_plot()
                    self.update_plot()

                    self.progressBar.hide()
                    self.statusBar().clearMessage()
                    self._thisApp.processEvents()

    def removeFMFromAllPlots(self, fmName):

        fmRemoved = False

        if self.aFDVGraph is not None:
            fmRemoved = self.aFDVGraph.plotted_fms.removeFM(fmName)

        if self.aScattergraph is not None:
            if self.aScattergraph.plot_flow_monitor is not None:
                if self.aScattergraph.plot_flow_monitor.monitorName == fmName:
                    self.aScattergraph = graphScatter(self.plotCanvasMain)
                    fmRemoved = True
            else:
                fmRemoved = True

        if self.a_dwf_graph is not None:
            if self.a_dwf_graph.plot_flow_monitor is not None:
                if self.a_dwf_graph.plot_flow_monitor.monitorName == fmName:
                    self.a_dwf_graph = graphDWF(self.plotCanvasMain)
                    fmRemoved = True
            else:
                fmRemoved = True

        if self.openFlowMonitors.dictFlowMonitors[fmName]._schematicGraphicItem is not None:
            fm_sgvItem = self.schematicGraphicsView.getSchematicFlowMonitorsByName(fmName)
            self.schematicGraphicsView.deleteItem(fm_sgvItem)
            # fmRemoved = True

        return fmRemoved

    def removeRGFromAllPlots(self, rgName):

        fmRemoved = False

        if self.aFDVGraph is not None:
            rgRemoved = self.aFDVGraph.plotted_rgs.removeRG(rgName)

        if self.aCumDepthGraph is not None:
            if self.aCumDepthGraph.plotted_rgs.removeRG(rgName):
                rgRemoved = True

        if self.aRainfallAnalysis is not None:
            if self.aRainfallAnalysis.plotted_rgs.removeRG(rgName):
                rgRemoved = True

        if self.openRainGauges.dictRainGauges[rgName]._schematicGraphicItem is not None:
            rg_sgvItem = self.schematicGraphicsView.getSchematicRainGaugeByName(rgName)
            self.schematicGraphicsView.deleteItem(rg_sgvItem)
            # rgRemoved = True

        return rgRemoved

    def updateEventTreeView(self):

        root = self.trwEvents.invisibleRootItem()
        child_count = root.childCount()

        for i in range(child_count):
            item = root.child(i)

            if item.text(0) == 'Storm':
                for i in range(item.childCount()):
                    item.removeChild(item.child(0))

                if self.identifiedSurveyEvents is not None:
                    for se in self.identifiedSurveyEvents.survEvents.values():
                        if se.eventType == "Storm":
                            it = QtWidgets.QTreeWidgetItem()
                            it.setText(0, se.eventName)
                            item.addChild(it)

                if item.childCount() > 0:
                    item.setExpanded(True)

            elif item.text(0) == 'DWF':
                for i in range(item.childCount()):
                    item.removeChild(item.child(0))

                if self.identifiedSurveyEvents is not None:
                    for se in self.identifiedSurveyEvents.survEvents.values():
                        if se.eventType == "DWF":
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
            aStart, aEnd = mpl_dates.num2date(
                self.aFDVGraph.plot_axis_rg.get_xlim())

        elif self.tbxGraphs.currentWidget().objectName() == "pageRainfallCumDepth":
            aStart, aEnd = mpl_dates.num2date(
                self.aCumDepthGraph.plotAxisCumDepth.get_xlim())

        elif self.tbxGraphs.currentWidget().objectName() == "pageRainfallAnalysis":
            aStart, aEnd = mpl_dates.num2date(
                self.aRainfallAnalysis.plotAxisIntensity.get_xlim())

        return aStart, aEnd

    def getStartEndDateFromCurrentRGs(self):

        if self.openRainGauges is not None:
            return self.openRainGauges.rgsEarliestStart, self.openRainGauges.rgsLatestEnd
        else:
            return None, None

    # def add_wq_monitor(self):

    #     path, _ = QtWidgets.QFileDialog.getOpenFileNames(
    #         self, 'Please locate the WQ Monitor files', self.lastOpenDialogPath, 'WQ CSV Files (*.csv)')
    #     if not path:
    #         return

    #     if self.openWQMonitors is None:
    #         self.openWQMonitors = fwqMonitors()

    #     self.progressBar.setMinimum(0)
    #     self.progressBar.setMaximum(len(path))
    #     self.progressBar.setValue(0)
    #     self.progressBar.show()

    #     for i in range(len(path)):
    #         self.progressBar.setValue(i)
    #         wqFileSpec = path[i]
    #         self.statusBar().showMessage('Reading: ' + wqFileSpec)
    #         if not self.openWQMonitors.alreadyOpen(wqFileSpec):
    #             self.openWQMonitors.add_monitor_from_file(wqFileSpec)
    #         self._thisApp.processEvents()
    #     self.statusBar().clearMessage()
    #     self.progressBar.hide()
    #     self.refreshWQMonitorListWidget()
    #     self.lastOpenDialogPath = os.path.dirname(path[0])

    def add_wq_monitor(self):
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, 'Please locate the WQ Monitor files', self.lastOpenDialogPath, 'WQ CSV Files (*.csv)')
        if not paths:
            return

        if self.openWQMonitors is None:
            self.openWQMonitors = fwqMonitors()

        # Read monitor IDs and fields from all files
        monitor_mappings = []
        for path in paths:
            df_id = pd.read_csv(path, nrows=1, header=None)
            monitor_id = df_id.iloc[0, 0]
            df = pd.read_csv(path, skiprows=[0, 2])
            fields = df.columns.tolist()
            auto_mapping = fwqMonitor.auto_map_fields(fields)
            monitor_mappings.append((monitor_id, fields, auto_mapping))

        # Open the dialog to allow the user to adjust mappings
        dialog = MappingDialog(monitor_mappings)
        if dialog.exec_():
            mappings = dialog.get_mappings()

            # Process each file with the selected mappings
            self.progressBar.setMinimum(0)
            self.progressBar.setMaximum(len(paths))
            self.progressBar.setValue(0)
            self.progressBar.show()

            for i, (path, (_, mapping)) in enumerate(zip(paths, mappings)):
                self.progressBar.setValue(i)
                if not self.openWQMonitors.alreadyOpen(path):
                    self.openWQMonitors.add_monitor_from_file(path, mapping)
                self._thisApp.processEvents()

            self.statusBar().clearMessage()
            self.progressBar.hide()
            self._thisApp.processEvents()
            self.refreshWQMonitorListWidget()

            self.lastOpenDialogPath = os.path.dirname(paths[0])

        self.set_active_page_by_name('Water Quality')

    def remove_all_wq_monitors(self):
        if self.aWQGraph is not None:
            self.aWQGraph.plotted_wqs = plottedWQMonitors()
        self.openWQMonitors = None
        self.refreshWQMonitorListWidget()
        self.update_plot()

    def remove_wq_monitor(self):

        if self.aWQGraph is not None:
            if self.aWQGraph.plotted_wqs.removeWQ(self.lst_WQMonitors.currentItem().text()):
                self.update_plot()
        self.openWQMonitors.remove_monitor(
            self.lst_WQMonitors.currentItem().text())
        self.refreshWQMonitorListWidget()

    # def trw_PlottedFSMInstalls_drag_action(self, e, s):

    #     index = self.trv_flow_survey_management.indexAt(e.pos())
    #     if index.isValid():
    #         mimeData = s.model().mimeData([index])
    #         drag = QDrag(s)
    #         drag.setMimeData(mimeData)
    #         drag.exec_(Qt.MoveAction)

    def trw_PlottedFSMInstalls_drop_action(self, e):
        addedToPlot = False

        if self.aFSMInstallGraph is not None:
            if e.source() == self.trv_flow_survey_management:

                source_item = QStandardItemModel()
                source_item.dropMimeData(
                    e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())                

                if source_item.rowCount() == 1:
                    item_text = source_item.item(0, 0).text()
                    if item_text.startswith("Install ID: "):

                        match = re.search(r'Install ID:\s*(.+)', item_text)  # Capture everything after "Install ID:"

                        if match:
                            install_id = match.group(1).strip()  # Extract and remove leading/trailing spaces
                            a_inst = self.fsmProject.dict_fsm_installs[install_id]
                            self.aFSMInstallGraph.plotted_install = a_inst
                            self.aFSMInstallGraph.plotted_raw = self.fsmProject.get_raw_data_by_install(a_inst.install_id)
                            addedToPlot = True                            

                    # if item_text.startswith("Site ID: "):

                    #     match = re.search(r'Site ID:\s*([A-Za-z0-9_]+)(?:\s*\(Install ID:\s*(\d+)\))?', item_text)
                    #     if match:
                    #         site_id = match.group(1)  # Capture the Monitor ID
                    #         install_id = match.group(2) if match.group(2) else None

                    #     if install_id:
                    #         a_inst = self.fsmProject.dict_fsm_installs[int(install_id)]
                    #         self.aFSMInstallGraph.plotted_install = a_inst
                    #         self.aFSMInstallGraph.plotted_raw = self.fsmProject.get_raw_data_by_install(a_inst.install_id)
                    #         addedToPlot = True
                    #     elif site_id:
                    #         a_inst = self.fsmProject.get_current_install_by_site(site_id)
                    #         self.aFSMInstallGraph.plotted_install = a_inst
                    #         self.aFSMInstallGraph.plotted_raw = self.fsmProject.get_raw_data_by_install(a_inst.install_id)
                    #         addedToPlot = True

                    # elif item_text.startswith("Monitor ID: "):

                    #     match = re.search(r"Monitor ID:\s*([A-Za-z0-9_]+)(?:\s*\(Install ID:\s*(\d+)\))?", item_text)
                    #     if match:
                    #         monitor_id = match.group(1)  # Capture the Monitor ID
                    #         install_id = match.group(2) if match.group(2) else None

                    #     if install_id:
                    #         a_inst = self.fsmProject.dict_fsm_installs[int(install_id)]
                    #         self.aFSMInstallGraph.plotted_install = a_inst
                    #         self.aFSMInstallGraph.plotted_raw = self.fsmProject.get_raw_data_by_install(a_inst.install_id)
                    #         addedToPlot = True
                    #     elif monitor_id:
                    #         a_inst = self.fsmProject.get_current_install_by_monitor(monitor_id)
                    #         self.aFSMInstallGraph.plotted_install = a_inst
                    #         self.aFSMInstallGraph.plotted_raw = self.fsmProject.get_raw_data_by_install(a_inst.install_id)
                    #         addedToPlot = True

            else:
                print("dropped from IDK?")

        if addedToPlot:
            self.update_plot()

    def trw_PlottedWQMonitors_drop_action(self, e):
        addedToPlot = False

        if self.aWQGraph is not None:
            if e.source() == self.lst_WQMonitors:

                source_item = QStandardItemModel()
                source_item.dropMimeData(
                    e.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())

                if source_item.rowCount() == 1:
                    self.aWQGraph.plotted_wqs = plottedWQMonitors()
                    addedToPlot = True

                for i in range(source_item.rowCount()):
                    wq = self.openWQMonitors.get_monitor(
                        source_item.item(i, 0).text())
                    if self.aWQGraph.plotted_wqs.addWQMonitor(wq):
                        addedToPlot = True

            else:
                print("dropped from IDK?")

        if addedToPlot:
            self.update_plot()

    def refreshWQMonitorListWidget(self):
        self.lst_WQMonitors.clear()
        if self.openWQMonitors is not None:
            for wqm in self.openWQMonitors.dictfwqMonitors.items():
                self.lst_WQMonitors.addItem(wqm[1].monitor_id)

    def openPlottedWQMonitorsTreeViewContextMenu(self, position):

        level = self.getTreeViewLevel(self.trw_PlottedWQMonitors)
        menu = QMenu()
        if level == 0:
            if self.trw_PlottedWQMonitors.itemAt(position).childCount() > 0:
                remCallback = QtWidgets.QAction("Remove All", menu)
                remCallback.triggered.connect(self.removeWQTreeItems)
                menu.addAction(remCallback)
        elif level == 1:
            remCallback = QtWidgets.QAction("Remove", menu)
            remCallback.triggered.connect(self.removeWQTreeItem)
            menu.addAction(remCallback)

        if not len(menu.actions()) == 0:
            menu.exec_(
                self.trw_PlottedWQMonitors.viewport().mapToGlobal(position))

    def openWQMonitorsListContextMenu(self, position):

        if self.lst_WQMonitors.currentItem() is not None:
            rightMenu = QMenu(self.lst_WQMonitors)
            rightMenu.addAction(
                QAction('Remove Monitor', self, triggered=self.remove_wq_monitor))
            rightMenu.exec_(QCursor.pos())

    def removeWQTreeItem(self):
        if self.aWQGraph is not None:
            item = self.trw_PlottedWQMonitors.selectedItems()[0]
            self.aWQGraph.plotted_wqs.removeWQ(item.text(0))

        self.update_plot()

    def removeWQTreeItems(self):
        if self.aWQGraph is not None:
            self.aWQGraph.plotted_wqs = plottedWQMonitors()

        self.update_plot()
