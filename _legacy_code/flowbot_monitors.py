import os
# from datetime import datetime
from typing import List, Optional, Dict, Tuple, Any
import time
import calendar
from datetime import datetime, timedelta, timezone
from statistics import mean
import numpy as np
# import pandas as pd
import sqlite3
import math
from collections import namedtuple

from PyQt5 import QtGui
from PyQt5.QtWidgets import (QMessageBox)
from PyQt5.QtCore import (QVariant)
from PyQt5.QtGui import QColor, QFont

from flowbot_schematic import rgGraphicsItem, fmGraphicsItem
from flowbot_verification import icmTraceLocation
from flowbot_helper import serialize_list, deserialize_list, serialize_item, deserialize_item, parse_file, parse_date, write_header, write_constants, write_rg_payload, write_fm_payload
from flowbot_database import Tables
from flowbot_survey_events import surveyEvent
# from contextlib import closing
from qgis.core import (QgsCoordinateReferenceSystem, QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsPointXY, QgsRectangle, QgsFeatureRequest, QgsMarkerSymbol, QgsRasterLayer, QgsRasterFileWriter, QgsWkbTypes, Qgis, QgsRasterBlock, QgsColorRampShader, QgsSingleBandPseudoColorRenderer, QgsRasterShader, QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsTextFormat, QgsTextBufferSettings)
# from qgis import processing
import tempfile
from scipy.spatial import cKDTree
from bisect import bisect_left, bisect_right

from flowbot_logging import get_logger
logger = get_logger('flowbot_logger')

class flowMonitor(object):

    def __init__(self):
        self.fdvFileSpec: str = ''
        self.monitorName: str = ''
        self.flowUnits: str = ''
        self.depthUnits: str = ''
        self.velocityUnits: str = ''
        self.rainGaugeName: str = ''
        self.fmTimestep: float = 0.0
        self.dateRange: List[datetime] = []
        self.flowDataRange: List[float] = []
        self.depthDataRange: List[float] = []
        self.velocityDataRange: List[float] = []
        self.minFlow: float = 0
        self.maxFlow: float = 0
        self.totalVolume: float = 0
        self.minDepth: float = 0
        self.maxDepth: float = 0
        self.minVelocity: float = 0
        self.maxVelocity: float = 0
        self.hasModelData: bool = False
        self.modelDataPipeRef: str = ''
        self.modelDataRG: str = ''
        self.modelDataPipeLength: float = 0
        self.modelDataPipeShape: str = 'CIRC'
        self.modelDataPipeDia: float = 0
        self.modelDataPipeHeight: float = 0
        self.modelDataPipeRoughness: float = 0
        self.modelDataPipeUSInvert: float = 0.0
        self.modelDataPipeDSInvert: float = 0.0
        self.modelDataPipeSystemType: str = 'Unknown'
        self._schematicGraphicItem: Optional[fmGraphicsItem] = None
        self.x: float = 0.0
        self.y: float = 0.0

    def from_database_row_dict(self, row_dict: Dict):
        self.fdvFileSpec = row_dict.get("fdvFileSpec", self.fdvFileSpec)
        self.monitorName = row_dict.get("monitorName", self.monitorName)
        self.flowUnits = row_dict.get("flowUnits", self.flowUnits)
        self.depthUnits = row_dict.get("depthUnits", self.depthUnits)
        self.velocityUnits = row_dict.get("velocityUnits", self.velocityUnits)
        self.rainGaugeName = row_dict.get("rainGaugeName", self.rainGaugeName)
        self.fmTimestep = row_dict.get("fmTimestep", self.fmTimestep)
        self.dateRange = deserialize_list(row_dict.get("dateRange", self.dateRange))
        self.flowDataRange = deserialize_list(row_dict.get("flowDataRange", self.flowDataRange))
        self.depthDataRange = deserialize_list(row_dict.get("depthDataRange", self.depthDataRange))
        self.velocityDataRange = deserialize_list(row_dict.get("velocityDataRange", self.velocityDataRange))
        self.minFlow = row_dict.get("minFlow", self.minFlow)
        self.maxFlow = row_dict.get("maxFlow", self.maxFlow)
        self.totalVolume = row_dict.get("totalVolume", self.totalVolume)
        self.minDepth = row_dict.get("minDepth", self.minDepth)
        self.maxDepth = row_dict.get("maxDepth", self.maxDepth)
        self.minVelocity = row_dict.get("minVelocity", self.minVelocity)
        self.maxVelocity = row_dict.get("maxVelocity", self.maxVelocity)
        self.hasModelData = bool(row_dict.get("hasModelData", self.hasModelData))
        self.modelDataPipeRef = row_dict.get("modelDataPipeRef", self.modelDataPipeRef)
        self.modelDataRG = row_dict.get("modelDataRG", self.modelDataRG)
        self.modelDataPipeLength = row_dict.get("modelDataPipeLength", self.modelDataPipeLength)
        self.modelDataPipeShape = row_dict.get("modelDataPipeShape", self.modelDataPipeShape)
        self.modelDataPipeDia = row_dict.get("modelDataPipeDia", self.modelDataPipeDia)
        self.modelDataPipeHeight = row_dict.get("modelDataPipeHeight", self.modelDataPipeHeight)
        self.modelDataPipeRoughness = row_dict.get("modelDataPipeRoughness", self.modelDataPipeRoughness)
        self.modelDataPipeUSInvert = row_dict.get("modelDataPipeUSInvert", self.modelDataPipeUSInvert)
        self.modelDataPipeDSInvert = row_dict.get("modelDataPipeDSInvert", self.modelDataPipeDSInvert)
        self.modelDataPipeSystemType = row_dict.get("modelDataPipeSystemType", self.modelDataPipeSystemType)
        self.x = row_dict.get("x", self.x)
        self.y = row_dict.get("y", self.y)

    def getFlowVolumeBetweenDates(self, fromDate: datetime, toDate: datetime) -> int:
        start_time = calendar.timegm(self.dateRange[0].timetuple())
        end_time = calendar.timegm(self.dateRange[-1].timetuple())
        from_time = calendar.timegm(fromDate.timetuple())
        to_time = calendar.timegm(toDate.timetuple())

        if (start_time < from_time) and (from_time < end_time):
            unix_rounded_xmin_python_datetime = calendar.timegm(
                self.dateRange[0].timetuple())
            unix_rounded_xmax_python_datetime = calendar.timegm(
                fromDate.timetuple())
            unix_diff_mins = (
                (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)
            min_row = int(unix_diff_mins / self.fmTimestep)
        else:
            min_row = 0

        if (start_time < to_time) and (to_time < end_time):
            unix_rounded_xmin_python_datetime = calendar.timegm(
                self.dateRange[0].timetuple())
            unix_rounded_xmax_python_datetime = to_time
            unix_diff_mins = (
                (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)
            max_row = int(unix_diff_mins / self.fmTimestep)
        else:
            max_row = len(self.flowDataRange)

        return round(((sum(self.flowDataRange[min_row:max_row]))/1000) * int(self.fmTimestep) * 60, 1)

class flowMonitors():

    dictFlowMonitors: Dict[str, flowMonitor] = {}

    def __init__(self):
        self.dictFlowMonitors = {}

    def read_from_database(self, conn: sqlite3.Connection):
        c = conn.cursor()
        try:
            c.execute(f"SELECT * FROM {Tables.FLOW_MONITOR}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.FLOW_MONITOR}' does not exist.")
            return  # Return without attempting to fetch rows

        rows = c.fetchall()
        column_names = [description[0] for description in c.description]
        for row in rows:
            row_dict = dict(zip(column_names, row))
            monitor = flowMonitor()
            monitor.from_database_row_dict(row_dict)
            self.dictFlowMonitors[monitor.monitorName] = monitor

    def write_to_database(self, conn: sqlite3.Connection) -> bool:
        result = False
        try:
            # with closing(conn.cursor()) as c:
            conn.execute(f'''DROP TABLE IF EXISTS {Tables.FLOW_MONITOR}''')
            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.FLOW_MONITOR} (
                            fdvFileSpec TEXT,
                            monitorName TEXT PRIMARY KEY,
                            flowUnits TEXT,
                            depthUnits TEXT,
                            velocityUnits TEXT,
                            rainGaugeName TEXT,
                            fmTimestep REAL,
                            dateRange TEXT,
                            flowDataRange TEXT,
                            depthDataRange TEXT,
                            velocityDataRange TEXT,
                            minFlow REAL,
                            maxFlow REAL,
                            totalVolume REAL,
                            minDepth REAL,
                            maxDepth REAL,
                            minVelocity REAL,
                            maxVelocity REAL,
                            hasModelData INTEGER,
                            modelDataPipeRef TEXT,
                            modelDataRG TEXT,
                            modelDataPipeLength REAL,
                            modelDataPipeShape TEXT,
                            modelDataPipeDia REAL,
                            modelDataPipeHeight REAL,
                            modelDataPipeRoughness REAL,
                            modelDataPipeUSInvert REAL,
                            modelDataPipeDSInvert REAL,
                            modelDataPipeSystemType TEXT,
                            x REAL,
                            y REAL                         
                        )''')
            for monitor in self.dictFlowMonitors.values():
                conn.execute(f'''INSERT OR REPLACE INTO {Tables.FLOW_MONITOR} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (monitor.fdvFileSpec, monitor.monitorName, monitor.flowUnits, monitor.depthUnits,
                              monitor.velocityUnits, monitor.rainGaugeName, monitor.fmTimestep,
                              serialize_list(monitor.dateRange), serialize_list(
                                  monitor.flowDataRange),
                              serialize_list(monitor.depthDataRange), serialize_list(
                                  monitor.velocityDataRange),
                              monitor.minFlow, monitor.maxFlow, monitor.totalVolume, monitor.minDepth, monitor.maxDepth,
                              monitor.minVelocity, monitor.maxVelocity, int(
                                  monitor.hasModelData), monitor.modelDataPipeRef,
                              monitor.modelDataRG, monitor.modelDataPipeLength, monitor.modelDataPipeShape,
                              monitor.modelDataPipeDia, monitor.modelDataPipeHeight, monitor.modelDataPipeRoughness,
                              monitor.modelDataPipeUSInvert, monitor.modelDataPipeDSInvert, monitor.modelDataPipeSystemType, monitor.x, monitor.y))
            conn.commit()
            result = True
            logger.debug("flowMonitors.write_to_database Completed")

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            conn.rollback()
        except Exception as e:
            print(f"Exception in _query: {e}")
            conn.rollback()
        finally:
            return result
        #     conn.close()

    def addFlowMonitor(self, fileSpec: str):
        if not self.alreadyOpen(fileSpec):
            objFM = self.getFlowMonitorFromFDVFile(fileSpec)
            if objFM is not None:
                self.dictFlowMonitors[objFM.monitorName] = objFM

    def flowMonitorCount(self) -> int:

        return len(self.dictFlowMonitors)

    def getFlowMonitor(self, nameFM: str) -> Optional[flowMonitor]:

        if nameFM in self.dictFlowMonitors:
            return self.dictFlowMonitors[nameFM]

    def removeFlowMonitor(self, nameFM: str):

        if nameFM in self.dictFlowMonitors:
            self.dictFlowMonitors.pop(nameFM)

    def alreadyOpen(self, fileSpec: str):

        for fm in self.dictFlowMonitors.items():
            if fm[1].fdvFileSpec == fileSpec:
                reply = QMessageBox.question(None, 'FDV file opened already!',
                                             fm[1].monitorName +
                                             ' was added with that FDV file.\n\nDo you want to replace it?',
                                             QMessageBox.Yes | QMessageBox.No,
                                             QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.dictFlowMonitors.pop(fm[1].monitorName)
                    return False
                else:
                    return True

        return False

    # def getFlowMonitorFromFDVFile(self, fileSpec: str) -> flowMonitor:

    #     with open(fileSpec, 'r') as org_data:

    #         myFM = flowMonitor()
    #         myFM.fdvFileSpec = fileSpec

    #         dynamicDateRange = []

    #         lines = []
    #         countCEND = 0

    #         myFM.dateRange = []
    #         myFM.flowDataRange = []
    #         myFM.depthDataRange = []
    #         myFM.velocityDataRange = []

    #         dataAppend = False

    #         for line in org_data:

    #             lines.append(line)

    #         for i in range(len(lines)):

    #             if (lines[i])[:13] == "**IDENTIFIER:":

    #                 rawMonitorName = lines[i]

    #                 strippedRawMonitorName = rawMonitorName.replace(
    #                     " ", "").strip()

    #                 myFM.monitorName = strippedRawMonitorName[15:36]

    #             if (lines[i])[:8] == "**UNITS:":

    #                 myFM.flowUnits = 'Flow '+(lines[i])[31:34]
    #                 myFM.depthUnits = 'Depth '+(lines[i])[35:37]
    #                 myFM.velocityUnits = 'Velocity '+(lines[i])[38:41]

    #             if (lines[i])[:11] == "**C_FORMAT:":
    #                 myFM.rainGaugeName = (lines[i])[60:65]
    #             if (lines[i])[:5] == "*CEND":

    #                 countCEND += 1

    #                 rawDates = (lines[i-1])

    #                 strippedRawDates = rawDates.replace(" ", "")
    #                 # ____________________________________________________________________________________________________________________________________
    #                 # ____________________________________________________________________________________________________________________________________
    #                 # This section is to acount for when there is a break in the data, and it is restarted, acounting for and missing time with Zeros

    #                 if len(strippedRawDates) == 22 or len(strippedRawDates) == 23:
    #                     myFM.fmTimestep = float(strippedRawDates[20:-1])
    #                     strippedRawDatesStartDate = strippedRawDates[0:10]
    #                     strippedStartDate = strippedRawDatesStartDate[4:6]+'/'+strippedRawDatesStartDate[2:4]+'/' + '20' + \
    #                         strippedRawDatesStartDate[0:2]+' ' + \
    #                         strippedRawDatesStartDate[6:8] + \
    #                         ":"+strippedRawDatesStartDate[8:10]
    #                     d1Working = datetime.strptime(
    #                         strippedStartDate, "%d/%m/%Y %H:%M")

    #                 elif len(strippedRawDates) == 26 or len(strippedRawDates) == 27:
    #                     myFM.fmTimestep = float(strippedRawDates[24:-1])
    #                     strippedRawDatesStartDate = strippedRawDates[0:12]
    #                     strippedStartDate = strippedRawDatesStartDate[6:8]+'/'+strippedRawDatesStartDate[4:6]+'/' + \
    #                         strippedRawDatesStartDate[0:4]+' '+strippedRawDatesStartDate[8:10] + \
    #                         ":"+strippedRawDatesStartDate[10:12]
    #                     d1Working = datetime.strptime(
    #                         strippedStartDate, "%d/%m/%Y %H:%M")

    #                 if countCEND == 1:

    #                     dynamicDateRange.append(d1Working)
    #                     d1 = d1Working

    #                 if countCEND > 1:

    #                     # the d1 working is the start of the current, dynamic is the generated date range
    #                     if d1Working > (dynamicDateRange[-1]):

    #                         gapDiff = (
    #                             (d1Working - timedelta(minutes=myFM.fmTimestep)) - d2)

    #                         rowsToAdd = (
    #                             gapDiff/timedelta(minutes=myFM.fmTimestep))

    #                         z = 0
    #                         # Append ZEROS to list
    #                         while z < rowsToAdd:

    #                             myFM.flowDataRange.append(0)
    #                             myFM.depthDataRange.append(0)
    #                             myFM.velocityDataRange.append(0)

    #                             # dynamicDateRange.append(dynamicDateRange[-1] + timedelta(minutes=ts))########

    #                             z += 1

    #                     elif (d1Working - timedelta(minutes=myFM.fmTimestep)) == d2:

    #                         gapDiff = (
    #                             (d1Working - timedelta(minutes=myFM.fmTimestep)) - d2)

    #                 if len(strippedRawDates) == 22 or len(strippedRawDates) == 23:
    #                     # myFM.fmTimestep = float(strippedRawDates[20:-1])
    #                     strippedRawDatesEndDate = strippedRawDates[10:20]
    #                     strippedEndDate = strippedRawDatesEndDate[4:6]+'/'+strippedRawDatesEndDate[2:4]+'/'+'20' + \
    #                         strippedRawDatesEndDate[0:2]+' ' + \
    #                         strippedRawDatesEndDate[6:8] + \
    #                         ":"+strippedRawDatesEndDate[8:10]
    #                     d2 = datetime.strptime(
    #                         strippedEndDate, "%d/%m/%Y %H:%M")

    #                 elif len(strippedRawDates) == 26 or len(strippedRawDates) == 27:
    #                     # myFM.fmTimestep = float(strippedRawDates[24:-1])
    #                     strippedRawDatesEndDate = strippedRawDates[12:24]
    #                     strippedEndDate = strippedRawDatesEndDate[6:8]+'/'+strippedRawDatesEndDate[4:6]+'/' + \
    #                         strippedRawDatesEndDate[0:4]+' '+strippedRawDatesEndDate[8:10] + \
    #                         ":"+strippedRawDatesEndDate[10:12]
    #                     d2 = datetime.strptime(
    #                         strippedEndDate, "%d/%m/%Y %H:%M")

    #                 startRow = i+1
    #                 dataAppend = True

    #             if (lines[i])[:4] == "*END" or (lines[i])[:2] == "*$":

    #                 # end_row = i-1
    #                 dataAppend = False

    #             if dataAppend == True and (lines[i])[3:6] != "" and i >= startRow:

    #                 if (lines[i])[1:5] != '':
    #                     myFM.flowDataRange.append(float((lines[i])[0:5]))  # 1
    #                     myFM.depthDataRange.append(float((lines[i])[5:10]))
    #                     myFM.velocityDataRange.append(float((lines[i])[10:15]))

    #                     # dynamicDateRange.append(dynamicDateRange[-1] + timedelta(minutes=ts))########

    #                 if (lines[i])[16:20] != '':
    #                     myFM.flowDataRange.append(
    #                         float((lines[i])[15:20]))  # 2
    #                     myFM.depthDataRange.append(float((lines[i])[20:25]))
    #                     myFM.velocityDataRange.append(float((lines[i])[25:30]))

    #                     # dynamicDateRange.append(dynamicDateRange[-1] + timedelta(minutes=ts))########

    #                 if (lines[i])[31:35] != '':
    #                     myFM.flowDataRange.append(
    #                         float((lines[i])[30:35]))  # 3
    #                     myFM.depthDataRange.append(float((lines[i])[35:40]))
    #                     myFM.velocityDataRange.append(float((lines[i])[40:45]))

    #                     # dynamicDateRange.append(dynamicDateRange[-1] + timedelta(minutes=ts))########

    #                 if (lines[i])[46:50] != '':
    #                     myFM.flowDataRange.append(
    #                         float((lines[i])[45:50]))  # 4
    #                     myFM.depthDataRange.append(float((lines[i])[50:55]))
    #                     myFM.velocityDataRange.append(float((lines[i])[55:60]))

    #                     # dynamicDateRange.append(dynamicDateRange[-1] + timedelta(minutes=ts))########

    #                 if (lines[i])[61:65] != '':
    #                     myFM.flowDataRange.append(
    #                         float((lines[i])[60:65]))  # 5
    #                     myFM.depthDataRange.append(float((lines[i])[65:70]))
    #                     myFM.velocityDataRange.append(float((lines[i])[70:75]))

    #                     # dynamicDateRange.append(dynamicDateRange[-1] + timedelta(minutes=ts))########

    #         # ___________________________________________________________
    #         # This re-formates the datetime from the file & creates the list of dates between the start & end dates

    #         delta = d2 - d1

    #         # _____________________________________________________
    #         for i in range(len(myFM.flowDataRange)):

    #             # print(d1 + timedelta(minutes=i))
    #             myFM.dateRange.append(
    #                 d1 + timedelta(minutes=i*myFM.fmTimestep))

    #         dateRangeStart = myFM.dateRange[0]
    #         dateRangeEnd = myFM.dateRange[len(myFM.dateRange)-1]

    #         # ____________________________________________________________________
    #         #####################################################################
    #         ##### THESE WILL ONLY NEED TO BE CALCULATED FOR INTIALLY SELECTED#####

    #         myFM.minFlow = (min(myFM.flowDataRange))
    #         myFM.maxFlow = (max(myFM.flowDataRange))
    #         myFM.totalVolume = round(
    #             ((sum(myFM.flowDataRange))/1000)*myFM.fmTimestep*60, 1)

    #         myFM.minDepth = (min(myFM.depthDataRange))
    #         myFM.maxDepth = (max(myFM.depthDataRange))

    #         myFM.minVelocity = (min(myFM.velocityDataRange))
    #         myFM.maxVelocity = (max(myFM.velocityDataRange))

    #         # This allows for the combination of the flow, depth and velocity data with the dates into a list
    #         fdvZipListDates = []
    #         fdvZipList = []

    #         for i in range(len(myFM.dateRange)):
    #             fdvZipListDates.append(
    #                 myFM.dateRange[i].strftime("%d/%m/%Y %H:%M"))

    #         fdvZipList = list(zip(fdvZipListDates, myFM.flowDataRange,
    #                           myFM.depthDataRange, myFM.velocityDataRange))

    #         # myFM.fdvDataframe = pd.DataFrame(fdvZipList, columns=['Date', 'Flow', 'Depth', 'Velocity'])

    #         return myFM

        #     try:
        #     if not self.alreadyOpen(fileSpec):

        #         start_old = time.perf_counter()
        #         objRG = self.getRainGaugeFromRFile(fileSpec)
        #         end_old = time.perf_counter()

        #         start_new = time.perf_counter()
        #         objRG_alt = self.getRainGaugeFromRFile_NEW(fileSpec)
        #         end_new = time.perf_counter()

        #         time_old = end_old - start_old
        #         time_new = end_new - start_new

        #         print(f"Old method time: {time_old:.6f} seconds")
        #         print(f"New method time: {time_new:.6f} seconds")
        #         print(f"Time difference (new - old): {time_new - time_old:.6f} seconds")

        #         if objRG is not None:
        #             self.dictRainGauges[objRG.gaugeName] = objRG
        #             self.updateRGsMinMaxValues()
        # except Exception as e:  # Capture the exception details
        #     QMessageBox.critical(
        #         None,
        #         'Error Adding Rain Gauge',
        #         f"Error parsing: {os.path.basename(fileSpec)}\n\nException: {str(e)}",
        #         QMessageBox.Ok
        #     )
        

    def getFlowMonitorFromFDVFile(self, fileSpec: str) -> flowMonitor:

        try:
            with open(fileSpec, 'r') as org_data:

                file_data = parse_file(fileSpec)

                all_units = [unit for record in file_data["payload"] for unit in record]

                myFM = flowMonitor()
                myFM.fdvFileSpec = fileSpec

                constants = file_data["constants"]

                # Parse the START and END dates using the helper.
                start_dt = parse_date(constants["START"])
                end_dt = parse_date(constants["END"])
                duration_mins = (end_dt - start_dt).total_seconds() / 60

                # Get the INTERVAL (assumed to be in minutes)
                interval_minutes = int(constants["INTERVAL"])
                myFM.fmTimestep = interval_minutes
                interval = timedelta(minutes=interval_minutes)

                # Generate the date range.
                myFM.dateRange = []
                current_dt = start_dt
                while current_dt <= end_dt:
                    myFM.dateRange.append(current_dt)
                    current_dt += interval

                no_of_records = int(duration_mins / interval_minutes) + 1
                i_record = 0

                myFM.flowDataRange = []
                myFM.depthDataRange = []
                myFM.velocityDataRange = []

                for unit in all_units:
                    i_record += 1                    
                    if i_record <= no_of_records:
                        flow = unit.get("FLOW")
                        if flow is not None:
                            myFM.flowDataRange.append(float(flow))
                        else:
                            myFM.flowDataRange.append(0.0)

                        depth = unit.get("DEPTH")
                        if depth is not None:
                            myFM.depthDataRange.append(float(depth))
                        else:
                            myFM.depthDataRange.append(0.0)

                        velocity = unit.get("VELOCITY")
                        if velocity is not None:
                            myFM.velocityDataRange.append(float(velocity))
                        else:
                            myFM.velocityDataRange.append(0.0)
                # (Optional) Check that the number of dates matches the number of data units.
                if len(myFM.dateRange) != len(myFM.flowDataRange):
                    print("Warning: Mismatch in number of timestamps and data points!")

                record_line = file_data['header'].get('IDENTIFIER', '')
                if record_line:
                    parts = [p.strip() for p in record_line.split(',')]
                    if len(parts) >= 2:
                        myFM.monitorName = parts[1]

                record_line = file_data['header'].get('UNITS', '')
                if record_line:
                    parts = [p.strip() for p in record_line.split(',')]
                    if len(parts) >= 4:
                        myFM.flowUnits = f'Flow {parts[1]}'
                        myFM.depthUnits = f'Depth {parts[2]}'
                        myFM.velocityUnits = f'Velocity {parts[3]}'

                if 'RAINGAUGE' in constants:
                    myFM.rainGaugeName = constants['RAINGAUGE']

                myFM.minFlow = (min(myFM.flowDataRange))
                myFM.maxFlow = (max(myFM.flowDataRange))
                myFM.totalVolume = round(((sum(myFM.flowDataRange))/1000)*myFM.fmTimestep*60, 1)
                myFM.minDepth = (min(myFM.depthDataRange))
                myFM.maxDepth = (max(myFM.depthDataRange))
                myFM.minVelocity = (min(myFM.velocityDataRange))
                myFM.maxVelocity = (max(myFM.velocityDataRange))
         
                return myFM
        except Exception as e:  # Capture the exception details
            QMessageBox.critical(
                None,
                'Error Adding Flow Monitor',
                f"Error parsing: {os.path.basename(fileSpec)}\n\nException: {str(e)}",
                QMessageBox.Ok
            )

    def writeFDVFileFromFlowMonitor(self, file_path: str, fm_name: str):

            """
            Given a rainGauge object (rg) with at least the following attributes:
            - rg.data_format (e.g. "rainGauge")
            - rg.gaugeName (name of the gauge)
            - rg.dateRange (list of datetime objects)
            - rg.rgTimestep (the interval in minutes, as an int)
            - rg.rainfallDataRange (list of float intensity values)
            This function writes a raingauge data file using a fixed format.
            """
            fm = self.dictFlowMonitors[fm_name]
            if fm is None:
                return
            
            # Define the header values.
            header = {
                "DATA_FORMAT": "1,ASCII",
                "IDENTIFIER": f"1,{fm.monitorName}",
                "FIELD": "3,FLOW,DEPTH,VELOCITY",
                "UNITS": "3,L/S,MM,M/S",
                "FORMAT": "4,I5,I5,F5.2,[5]",
                "RECORD_LENGTH": "I2,75"
            }
            header_lines = write_header(header)

            constants_format = '8,I6,F7.3,2X,A20/D10,2X,D10,I4'
            
            Constant = namedtuple('Constant', ['name', 'units', 'value'])

            constants = [
                Constant('HEIGHT', 'MM', fm.modelDataPipeHeight),  #Need some code here to convert the x,y to a national grid reference 
                Constant('MIN_VEL', 'M/S', min(fm.velocityDataRange)),
                Constant('MANHOLE_NO', '', ''),
                Constant('START', 'GMT', fm.dateRange[0]),
                Constant('END', 'GMT', fm.dateRange[-1]),
                Constant('INTERVAL', 'MIN', fm.fmTimestep)
            ]

            # Build the constants block.
            constants_lines = write_constants(constants, constants_format)
            
            # RECORD_LENGTH: here we extract the numeric width from the header.
            record_length = int(header["RECORD_LENGTH"].split(",")[1].strip())
            # payload_lines = write_fm_payload(fm, header["FORMAT"], record_length, header["FIELD"])
            payload_lines = write_fm_payload(fm, header["FORMAT"], record_length)
            
            # Assemble the file lines.

            file_lines = []
            file_lines.extend(header_lines)
            file_lines.extend(constants_lines[0])
            file_lines.append("*CSTART")
            file_lines.extend(constants_lines[1])
            file_lines.append("*CEND")
            file_lines.extend(payload_lines)
            file_lines.append("*END")

            # Write the lines to the file.
            file_spec = os.path.join(file_path, f"{fm.monitorName}.fdv")

            if os.path.exists(file_spec):
                print(f"File {file_spec} already exists.")
            else:
                with open(file_spec, "w", encoding="utf-8") as f:
                    for line in file_lines:
                        f.write(line + "\n")

class plottedFlowMonitors():

    plotFMs: Dict[str, flowMonitor] = {}
    plotEarliestStart: datetime = datetime.strptime('2172-05-12', '%Y-%m-%d')
    plotLatestEnd: datetime = datetime.strptime('1972-05-12', '%Y-%m-%d')
    __plotCurrentStart: datetime = datetime.strptime('2172-05-12', '%Y-%m-%d')
    __plotCurrentEnd: datetime = datetime.strptime('1972-05-12', '%Y-%m-%d')
    plotMinFlow: float = 9999
    plotAvgFlow: float = 0
    plotMaxFlow: float = 0
    plotMinDepth: float = 9999
    plotAvgDepth: float = 0
    plotMaxDepth: float = 0
    plotMinVelocity: float = 9999
    plotAvgVelocity: float = 0
    plotMaxVelocity: float = 0
    plotTotalVolume: float = 0

    def __init__(self):
        self.plotFMs = {}

    def setPlotDateLimits(self, startDate: datetime, endDate: datetime):
        if startDate is None:
            self.__plotCurrentStart = datetime.strptime(
                '2172-05-12', '%Y-%m-%d')
        else:
            self.__plotCurrentStart = startDate
        if endDate is None:
            self.__plotCurrentEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')
        else:
            self.__plotCurrentEnd = endDate
        self.updatePlottedFMsMinMaxValues()

    def clear(self):
        self.plotFMs.clear()
        self.updatePlottedFMsMinMaxValues()

    def getPlotCurrentStart(self) -> datetime:
        return self.__plotCurrentStart

    def getPlotCurrentEnd(self) -> datetime:
        return self.__plotCurrentEnd

    def addFM(self, objFM: flowMonitor, updateMaxMin: bool = True) -> bool:

        if objFM.monitorName not in self.plotFMs:

            self.plotFMs[objFM.monitorName] = objFM
            if updateMaxMin:
                self.updatePlottedFMsMinMaxValues()

            return True

        else:

            return False

    def removeFM(self, nameFM: str) -> bool:

        if nameFM in self.plotFMs:
            self.plotFMs.pop(nameFM)
            self.updatePlottedFMsMinMaxValues()
            return True
        return False

    def updatePlottedFMsMinMaxValues(self):
        self.reset_plot_values()

        fmCount = 0
        for fm in self.plotFMs.values():
            self.update_earliest_start(fm)
            self.update_latest_end(fm)

            min_row, max_row = self.calculate_min_max_rows(fm)

            self.update_flow_values(fm, min_row, max_row, fmCount)
            self.update_depth_values(fm, min_row, max_row, fmCount)
            self.update_velocity_values(fm, min_row, max_row, fmCount)
            fmCount += 1

    def reset_plot_values(self):
        self.plotEarliestStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
        self.plotLatestEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')
        # self.plotMinFlow = float('inf')
        self.plotMinFlow = 9999
        self.plotAvgFlow = 0
        self.plotMaxFlow = 0
        # self.plotMinDepth = float('inf')
        self.plotMinDepth = 9999
        self.plotAvgDepth = 0
        self.plotMaxDepth = 0
        # self.plotMinVelocity = float('inf')
        self.plotMinVelocity = 9999
        self.plotAvgVelocity = 0
        self.plotMaxVelocity = 0
        self.plotTotalVolume = 0

    def update_earliest_start(self, fm):
        self.plotEarliestStart = min(self.plotEarliestStart, fm.dateRange[0])

    def update_latest_end(self, fm):
        self.plotLatestEnd = max(self.plotLatestEnd, fm.dateRange[-1])

    def calculate_min_max_rows(self, fm):
        min_row, max_row = 0, len(fm.flowDataRange)

        if self.should_update_row(fm.dateRange[0], self.getPlotCurrentStart(), fm.dateRange[-1]):
            min_row = self.calculate_row(
                fm.dateRange[0], self.getPlotCurrentStart(), fm.fmTimestep)
        if self.should_update_row(fm.dateRange[0], self.getPlotCurrentEnd(), fm.dateRange[-1]):
            max_row = self.calculate_row(
                fm.dateRange[0], self.getPlotCurrentEnd(), fm.fmTimestep)

        return min_row, max_row

    def should_update_row(self, start_date, plot_date, end_date):
        return calendar.timegm(start_date.timetuple()) < calendar.timegm(plot_date.timetuple()) < calendar.timegm(end_date.timetuple())

    def calculate_row(self, start_date, plot_date, fm_timestep):
        return int((calendar.timegm(plot_date.timetuple()) - calendar.timegm(start_date.timetuple())) / 60 / fm_timestep)

    def update_flow_values(self, fm, min_row, max_row, fmCount):
        flow_data_mean = mean(fm.flowDataRange[min_row:max_row])
        self.plotMaxFlow = max(self.plotMaxFlow, max(
            fm.flowDataRange[min_row:max_row]))
        self.plotAvgFlow = mean(
            [self.plotAvgFlow, flow_data_mean]) if fmCount > 0 else flow_data_mean
        self.plotMinFlow = min(self.plotMinFlow, min(
            fm.flowDataRange[min_row:max_row]))
        volume = round(
            ((sum(fm.flowDataRange[min_row:max_row])) / 1000) * int(fm.fmTimestep) * 60, 1)
        self.plotTotalVolume += volume

    def update_depth_values(self, fm, min_row, max_row, fmCount):
        depth_data_mean = mean(fm.depthDataRange[min_row:max_row])
        self.plotMaxDepth = max(self.plotMaxDepth, max(
            fm.depthDataRange[min_row:max_row]))
        self.plotAvgDepth = mean(
            [self.plotAvgDepth, depth_data_mean]) if fmCount > 0 else depth_data_mean
        self.plotMinDepth = min(self.plotMinDepth, min(
            fm.depthDataRange[min_row:max_row]))

    def update_velocity_values(self, fm, min_row, max_row, fmCount):
        vel_data_mean = mean(fm.velocityDataRange[min_row:max_row])
        self.plotMaxVelocity = max(self.plotMaxVelocity, max(
            fm.velocityDataRange[min_row:max_row]))
        self.plotAvgVelocity = mean(
            [self.plotAvgVelocity, vel_data_mean]) if fmCount > 0 else vel_data_mean
        self.plotMinVelocity = min(self.plotMinVelocity, min(
            fm.velocityDataRange[min_row:max_row]))

    # def updatePlottedFMsMinMaxValues(self):

    #     self.plotEarliestStart = dt.strptime('2172-05-12', '%Y-%m-%d')
    #     self.plotLatestEnd = dt.strptime('1972-05-12', '%Y-%m-%d')
    #     self.plotMinFlow = 9999
    #     self.plotAvgFlow = 0
    #     self.plotMaxFlow = 0
    #     self.plotMinDepth = 9999
    #     self.plotAvgDepth = 0
    #     self.plotMaxDepth = 0
    #     self.plotMinVelocity = 9999
    #     self.plotAvgVelocity = 0
    #     self.plotMaxVelocity = 0
    #     self.plotTotalVolume = 0

    #     fmCount = 0
    #     for fm in self.plotFMs.values():

    #         if self.plotEarliestStart > fm.dateRange[0]:
    #             self.plotEarliestStart = fm.dateRange[0]
    #         if self.plotLatestEnd < fm.dateRange[len(fm.dateRange)-1]:
    #             self.plotLatestEnd = fm.dateRange[len(fm.dateRange)-1]

    #         if (calendar.timegm(fm.dateRange[0].timetuple()) < calendar.timegm(self.getPlotCurrentStart().timetuple())) and (calendar.timegm(self.getPlotCurrentStart().timetuple()) < calendar.timegm(fm.dateRange[len(fm.dateRange)-1].timetuple())):
    #             unix_rounded_xmin_python_datetime = calendar.timegm(
    #                 fm.dateRange[0].timetuple())
    #             unix_rounded_xmax_python_datetime = calendar.timegm(
    #                 self.getPlotCurrentStart().timetuple())
    #             unix_diff_mins = (
    #                 (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)
    #             min_row = int(unix_diff_mins / fm.fmTimestep)
    #         else:
    #             min_row = 0

    #         if (calendar.timegm(fm.dateRange[0].timetuple()) < calendar.timegm(self.getPlotCurrentEnd().timetuple())) and (calendar.timegm(self.getPlotCurrentEnd().timetuple()) < calendar.timegm(fm.dateRange[len(fm.dateRange)-1].timetuple())):
    #             unix_rounded_xmin_python_datetime = calendar.timegm(
    #                 fm.dateRange[0].timetuple())
    #             unix_rounded_xmax_python_datetime = calendar.timegm(
    #                 self.getPlotCurrentEnd().timetuple())
    #             unix_diff_mins = (
    #                 (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)
    #             max_row = int(unix_diff_mins / fm.fmTimestep)
    #         else:
    #             max_row = len(fm.flowDataRange)

    #         self.plotMaxFlow = max(self.plotMaxFlow, max(
    #             fm.flowDataRange[min_row:max_row]))
    #         self.plotAvgFlow = mean([self.plotAvgFlow, mean(fm.flowDataRange[min_row:max_row])]) if fmCount > 0 else mean(fm.flowDataRange[min_row:max_row])
    #         self.plotMinFlow = min(self.plotMinFlow, min(
    #             fm.flowDataRange[min_row:max_row]))
    #         volume = round(
    #             ((sum(fm.flowDataRange[min_row:max_row]))/1000) * int(fm.fmTimestep) * 60, 1)
    #         self.plotTotalVolume = self.plotTotalVolume + volume

    #         self.plotMaxDepth = max(self.plotMaxDepth, max(
    #             fm.depthDataRange[min_row:max_row]))
    #         self.plotAvgDepth = mean([self.plotAvgDepth, mean(
    #             fm.depthDataRange[min_row:max_row])]) if fmCount > 0 else mean(fm.depthDataRange[min_row:max_row])
    #         self.plotMinDepth = min(self.plotMinDepth, min(
    #             fm.depthDataRange[min_row:max_row]))

    #         self.plotMaxVelocity = max(self.plotMaxVelocity, max(
    #             fm.velocityDataRange[min_row:max_row]))
    #         self.plotAvgVelocity = mean([self.plotAvgVelocity, mean(
    #             fm.velocityDataRange[min_row:max_row])]) if fmCount > 0 else mean(fm.velocityDataRange[min_row:max_row])
    #         self.plotMinVelocity = min(self.plotMinVelocity, min(
    #             fm.velocityDataRange[min_row:max_row]))

    #         fmCount += 1

class classifiedFlowMonitors():

    classFMs: Dict[str, flowMonitor] = {}
    classEarliestStart: datetime = datetime.strptime('2172-05-12', '%Y-%m-%d')
    classLatestEnd: datetime = datetime.strptime('1972-05-12', '%Y-%m-%d')
    __classCurrentStart: datetime = datetime.strptime('2172-05-12', '%Y-%m-%d')
    __classCurrentEnd: datetime = datetime.strptime('1972-05-12', '%Y-%m-%d')
    classMinFlow: float = 9999
    classMaxFlow: float = 0
    classMinDepth: float = 9999
    classMaxDepth: float = 0
    classMinVelocity: float = 9999
    classMaxVelocity: float = 0
    classTotalVolume: float = 0

    def __init__(self):
        self.classFMs = {}

    def setClassDateLimits(self, startDate: datetime, endDate: datetime):
        if startDate is None:
            self.__classCurrentStart = datetime.strptime(
                '2172-05-12', '%Y-%m-%d')
        else:
            self.__classCurrentStart = startDate
        if startDate is None:
            self.__classCurrentEnd = datetime.strptime(
                '1972-05-12', '%Y-%m-%d')
        else:
            self.__classCurrentEnd = endDate
        self.updateClassifiedFMsMinMaxValues()

    def getClassCurrentStart(self) -> datetime:
        return self.__classCurrentStart

    def getClassCurrentEnd(self) -> datetime:
        return self.__classCurrentEnd

    def addFM(self, objFM: flowMonitor, updateMinMax: bool = True) -> bool:

        if objFM.monitorName not in self.classFMs:

            self.classFMs[objFM.monitorName] = objFM
            if updateMinMax:
                self.updateClassifiedFMsMinMaxValues()

            return True

        else:

            return False

    def removeFM(self, nameFM: str) -> bool:

        if nameFM in self.classFMs:
            self.classFMs.pop(nameFM)
            self.updateClassifiedFMsMinMaxValues()
            return True
        return False

    def updateClassifiedFMsMinMaxValues(self):

        self.classEarliestStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
        self.classLatestEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')
        self.classMinFlow = 9999
        self.classMaxFlow = 0
        self.classMinDepth = 9999
        self.classMaxDepth = 0
        self.classMinVelocity = 9999
        self.classMaxVelocity = 0
        self.classTotalVolume = 0

        for fm in self.classFMs.values():

            if self.classEarliestStart > fm.dateRange[0]:
                self.classEarliestStart = fm.dateRange[0]
            if self.classLatestEnd < fm.dateRange[len(fm.dateRange)-1]:
                self.classLatestEnd = fm.dateRange[len(fm.dateRange)-1]

            start_time = calendar.timegm(fm.dateRange[0].timetuple())
            end_time = calendar.timegm(fm.dateRange[-1].timetuple())
            class_start_time = calendar.timegm(
                self.getClassCurrentStart().timetuple())
            class_end_time = calendar.timegm(
                self.getClassCurrentEnd().timetuple())

            if (start_time < class_start_time) and (class_start_time < end_time):
                unix_rounded_xmin_python_datetime = calendar.timegm(
                    fm.dateRange[0].timetuple())
                unix_rounded_xmax_python_datetime = calendar.timegm(
                    self.getClassCurrentStart().timetuple())
                unix_diff_mins = (
                    (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)
                min_row = int(unix_diff_mins / fm.fmTimestep)
            else:
                min_row = 0

            if (start_time < class_end_time) and (class_end_time < end_time):
                unix_rounded_xmin_python_datetime = calendar.timegm(
                    fm.dateRange[0].timetuple())
                unix_rounded_xmax_python_datetime = calendar.timegm(
                    self.getClassCurrentEnd().timetuple())
                unix_diff_mins = (
                    (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)
                max_row = int(unix_diff_mins / fm.fmTimestep)
            else:
                max_row = len(fm.flowDataRange)

            self.classMaxFlow = max(self.classMaxFlow, max(
                fm.flowDataRange[min_row:max_row]))
            self.classMinFlow = min(self.classMinFlow, min(
                fm.flowDataRange[min_row:max_row]))
            volume = round(
                ((sum(fm.flowDataRange[min_row:max_row]))/1000) * int(fm.fmTimestep) * 60, 1)
            self.classTotalVolume = self.classTotalVolume + volume

            self.classMaxDepth = max(self.classMaxDepth, max(
                fm.depthDataRange[min_row:max_row]))
            self.classMinDepth = min(self.classMinDepth, min(
                fm.depthDataRange[min_row:max_row]))

            self.classMaxVelocity = max(self.classMaxVelocity, max(
                fm.velocityDataRange[min_row:max_row]))
            self.classMinVelocity = min(self.classMinVelocity, min(
                fm.velocityDataRange[min_row:max_row]))

class summedFlowMonitor():

    sumFMName: str = ""
    equivalentFM: Optional[flowMonitor] = None
    fmCollection: Dict[str, tuple[flowMonitor, float]] = {}

    def __init__(self):
        self.sumFMName = ""
        self.equivalentFM = flowMonitor()
        self.fmCollection = {}

    def containsFM(self, fmName: str) -> bool:
        if fmName in self.fmCollection:
            return True
        else:
            return False

    def addFM(self, objFM: flowMonitor, multFM: float) -> bool:

        if objFM.monitorName not in self.fmCollection:

            self.fmCollection[objFM.monitorName] = (objFM, multFM)
            self.updateEquivalentFM()

            return True

        else:

            return False

    def removeFM(self, nameFM: str) -> bool:

        if nameFM.find("(", 0) > -1:
            fmName = nameFM[0:nameFM.find("(", 0)]
        else:
            fmName = nameFM

        if fmName in self.fmCollection:
            self.fmCollection.pop(fmName)
            self.updateEquivalentFM()
            return True
        return False

    def getSummedMonitorByItemText(self, nameFM: str) -> Optional[tuple[flowMonitor, float]]:
        if nameFM.find("(", 0) > -1:
            fmName = nameFM[0:nameFM.find("(", 0)]
        else:
            fmName = nameFM
        for fm, mult in self.fmCollection.values():

            if fm.monitorName == fmName:
                return fm, mult

    def updateEquivalentFM(self):

        monitorCount = 1
        latestStart = datetime.strptime('1972-05-12', '%Y-%m-%d')
        earliestEnd = datetime.strptime('2172-05-12', '%Y-%m-%d')

        for fm, mult in self.fmCollection.values():

            if latestStart < fm.dateRange[0]:
                latestStart = fm.dateRange[0]
            if earliestEnd > fm.dateRange[len(fm.dateRange)-1]:
                earliestEnd = fm.dateRange[len(fm.dateRange)-1]

        for fm, mult in self.fmCollection.values():

            indStart = fm.dateRange.index(latestStart)
            indEnd = fm.dateRange.index(earliestEnd)

            if monitorCount == 1:

                self.equivalentFM.monitorName = "*" + self.sumFMName
                self.equivalentFM.flowUnits = fm.flowUnits
                self.equivalentFM.depthUnits = fm.depthUnits
                self.equivalentFM.velocityUnits = fm.velocityUnits
                self.equivalentFM.rainGaugeName = ''
                self.equivalentFM.fmTimestep = fm.fmTimestep
                self.equivalentFM.dateRange = fm.dateRange[indStart:indEnd]

                flowDataRange = np.array(
                    fm.flowDataRange[indStart:indEnd]) * mult
                velocityDataRange = np.array(
                    fm.flowDataRange[indStart:indEnd]) * 0
                depthDataRange = np.array(
                    fm.flowDataRange[indStart:indEnd]) * 0

            else:

                flowDataRange = np.add(flowDataRange, np.array(
                    fm.flowDataRange[indStart:indEnd]) * mult)

            monitorCount += 1

        if len(self.fmCollection) > 0:
            self.equivalentFM.flowDataRange = flowDataRange.tolist()
            self.equivalentFM.velocityDataRange = velocityDataRange.tolist()
            self.equivalentFM.depthDataRange = depthDataRange.tolist()

class dummyFlowMonitor():

    dumFMName: str = ""
    equivalentFM: Optional[flowMonitor] = None

    def __init__(self):
        self.dumFMName = ""  # strName
        self.equivalentFM = flowMonitor()

    def updateEquivalentFMFromTraceLocation(self, aLoc: icmTraceLocation):

        # latestStart = dt.strptime('1972-05-12', '%Y-%m-%d')
        # earliestEnd = dt.strptime('2172-05-12', '%Y-%m-%d')

        # indStart = aLoc.dates[aLoc.iPredFlow].index(latestStart)
        # indEnd = aLoc.dates[aLoc.iPredFlow].index(earliestEnd)
        self.dumFMName = "*" + aLoc.shortTitle
        self.equivalentFM.monitorName = "*" + aLoc.shortTitle
        self.equivalentFM.flowUnits = "m3/s"
        self.equivalentFM.depthUnits = "m"
        self.equivalentFM.velocityUnits = "m/s"
        self.equivalentFM.rainGaugeName = ''
        self.equivalentFM.fmTimestep = aLoc.trTimestep
        self.equivalentFM.dateRange = [i for i in aLoc.dates.copy()]
        # self.equivalentFM.dateRange = [
        #     i.to_pydatetime() for i in aLoc.dates.copy()]
        self.equivalentFM.flowDataRange = [
            i * 1000 for i in aLoc.rawData[aLoc.iPredFlow].copy()]
        self.equivalentFM.velocityDataRange = aLoc.rawData[aLoc.iPredVelocity].copy(
        )
        self.equivalentFM.depthDataRange = [
            i * 1000 for i in aLoc.rawData[aLoc.iPredDepth].copy()]
        self.equivalentFM.modelDataPipeRef = aLoc.predLocation

class rainGauge():

    def __init__(self):
        # self.rDataframe = pd.DataFrame()
        self.gaugeName = ''
        self.rFileSpec = ''
        self.dateRange = []
        self.rainfallDataRange = []
        self.rgTimestep = 0.0
        self.minIntensity = 0
        self.maxIntensity = 0
        self.totalDepth = 0
        self.returnPeriod = 0
        self._schematicGraphicItem = None
        self.x: float = 0.0
        self.y: float = 0.0

    def from_database_row_dict(self, row_dict: Dict):

        self.gaugeName = row_dict.get("gaugeName", self.gaugeName)
        self.rFileSpec = row_dict.get("rFileSpec", self.rFileSpec)
        self.dateRange = deserialize_list(row_dict.get("dateRange", self.dateRange))
        self.rainfallDataRange = deserialize_list(row_dict.get("rainfallDataRange", self.rainfallDataRange))
        self.rgTimestep = row_dict.get("rgTimestep", self.rgTimestep)
        self.minIntensity = row_dict.get("minIntensity", self.minIntensity)
        self.maxIntensity = row_dict.get("maxIntensity", self.maxIntensity)
        self.totalDepth = row_dict.get("totalDepth", self.totalDepth)
        self.returnPeriod = row_dict.get("returnPeriod", self.returnPeriod)
        self.x = row_dict.get("x", self.x)
        self.y = row_dict.get("y", self.y)

    # def statsBetweenDates(self, startDate: Optional[datetime], endDate: Optional[datetime]):
    #     if startDate is None:
    #         startDate = datetime.strptime('2172-05-12', '%Y-%m-%d')
    #     if endDate is None:
    #         endDate = datetime.strptime('1972-05-12', '%Y-%m-%d')

    #     minIntensity = 0
    #     maxIntensity = 0
    #     totalDepth = 0
    #     returnPeriod = 0

    #     min_row, max_row = self.getDataRangeFromDates(startDate, endDate)

    #     maxIntensity = max(self.rainfallDataRange[min_row:max_row])
    #     minIntensity = min(self.rainfallDataRange[min_row:max_row])
    #     totalDepth = round(
    #         (sum(self.rainfallDataRange[min_row:max_row]))/(60/self.rgTimestep), 1)

    #     unix_rounded_xmin_python_datetime = calendar.timegm(
    #         startDate.timetuple())
    #     unix_rounded_xmax_python_datetime = calendar.timegm(
    #         endDate.timetuple())
    #     # unix_diff_days = (((unix_rounded_xmax_python_datetime -
    #     #                   unix_rounded_xmin_python_datetime)/60)/60)/24
    #     unix_diff_mins = ((unix_rounded_xmax_python_datetime -
    #                       unix_rounded_xmin_python_datetime)/60)
    #     duration_hrs = unix_diff_mins / 60
    #     returnPeriod = round(
    #         10/(1.25*duration_hrs*(((0.0394*totalDepth)+0.1)**-3.55)), 2)

    #     # returnPeriod = round(
    #     #     (0.00494*(totalDepth+2.54)**3.55)/unix_diff_mins, 2)

    #     return {'minInt': minIntensity, 'maxInt': maxIntensity, 'totDepth': totalDepth, 'retPer': returnPeriod}

    # def getDataRangeFromDates(self, startDate: Optional[datetime], endDate: Optional[datetime]):
    #     if startDate is None:
    #         startDate = datetime.strptime('2172-05-12', '%Y-%m-%d')
    #     if endDate is None:
    #         endDate = datetime.strptime('1972-05-12', '%Y-%m-%d')

    #     start_time = calendar.timegm(self.dateRange[0].timetuple())
    #     end_time = calendar.timegm(self.dateRange[-1].timetuple())
    #     target_start_time = calendar.timegm(startDate.timetuple())
    #     target_end_time = calendar.timegm(endDate.timetuple())

    #     if (start_time < target_start_time) and (target_start_time < end_time):
    #         unix_rounded_xmin_python_datetime = calendar.timegm(
    #             self.dateRange[0].timetuple())
    #         unix_rounded_xmax_python_datetime = calendar.timegm(
    #             startDate.timetuple())
    #         unix_diff_mins = (
    #             (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)
    #         min_row = int(unix_diff_mins / self.rgTimestep)
    #     else:
    #         min_row = 0

    #     if (start_time < target_end_time) and (target_end_time < end_time):
    #         unix_rounded_xmin_python_datetime = calendar.timegm(
    #             self.dateRange[0].timetuple())
    #         unix_rounded_xmax_python_datetime = calendar.timegm(
    #             endDate.timetuple())
    #         unix_diff_mins = (
    #             (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)
    #         max_row = int(unix_diff_mins / self.rgTimestep)
    #     else:
    #         max_row = len(self.rainfallDataRange)

    #     return (min_row, max_row)

    # def eventStatsBetweenDates(self, startDate: datetime, endDate: datetime):
    #     """Calculates basic rainfalls stats for the gauge based on the given date range

    #         Parameters
    #         ----------
    #         startDate: datetime
    #             The start date for the date range
    #         endDate: datetime
    #             The end date for the date range

    #         Returns
    #         -------
    #         Tuple(float, float, float, float)
    #             Duration: time in minutes for which there were non-zero rainfall intensity values within the specified date range
    #             Total Depth: total rainfall depth in mm within the specified date range
    #             Peak Intensity: Maximum rainfall intensity in mm/hr within the specified date range
    #             Period Greater Than 6mm/hr: time in minutes for which there were rainfall intensity values
    #             greater than or equal to 6mm/hr within the specified date range
    #         """

    #     rgName: str = ''
    #     startTime: str = ''
    #     duration: float = 0
    #     totalDepth: float = 0
    #     peakIntensity: float = 0
    #     periodGreaterThan6mmhr: float = 0

    #     min_row, max_row = self.getDataRangeFromDates(startDate, endDate)

    #     rgName = self.gaugeName
    #     index_first_match = None
    #     for index, item in enumerate(self.rainfallDataRange[min_row:max_row]):
    #         if item != 0:
    #             index_first_match = index
    #             break
    #     if index_first_match is not None:
    #         startTime = datetime.strftime(
    #             self.dateRange[min_row:max_row][index_first_match], "%H:%M")
    #     duration = self.rgTimestep * \
    #         sum(i > 0 for i in self.rainfallDataRange[min_row:max_row])
    #     totalDepth = round(
    #         (sum(self.rainfallDataRange[min_row:max_row]))/(60/self.rgTimestep), 1)
    #     peakIntensity = max(self.rainfallDataRange[min_row:max_row])
    #     periodGreaterThan6mmhr = self.rgTimestep * \
    #         sum(i > 6 for i in self.rainfallDataRange[min_row:max_row])

    #     return (rgName, startTime, duration, totalDepth, peakIntensity, periodGreaterThan6mmhr)

# from bisect import bisect_left, bisect_right
# from datetime import datetime
# from typing import Optional, Tuple, Dict, Any

    def _validate_parallel_series(self) -> None:
        if not getattr(self, "dateRange", None) or not getattr(self, "rainfallDataRange", None):
            raise ValueError("dateRange and rainfallDataRange must be populated.")
        if len(self.dateRange) != len(self.rainfallDataRange):
            raise ValueError("dateRange and rainfallDataRange must be the same length.")
        # assume self.dateRange is sorted ascending

    # def getDataRangeFromDates(
    #     self,
    #     startDate: Optional[datetime],
    #     endDate: Optional[datetime],
    # ) -> Tuple[int, int]:
    #     """
    #     Returns (i, j) indices into self.dateRange / self.rainfallDataRange,
    #     where i is inclusive and j is exclusive. If there is no overlap with the
    #     data window, returns (-1, -1).
    #     """
    #     self._validate_parallel_series()

    #     dr = self.dateRange
    #     data_start, data_end = dr[0], dr[-1]

    #     # Sensible defaults: clamp to data edges if None supplied
    #     a = startDate if startDate is not None else data_start
    #     b = endDate   if endDate   is not None else data_end

    #     # Ensure a <= b
    #     if b < a:
    #         a, b = b, a

    #     # No overlap at all
    #     if b < data_start or a > data_end:
    #         return (-1, -1)

    #     # Clamp to the data bounds
    #     a = max(a, data_start)
    #     b = min(b, data_end)

    #     # Find slice [i:j) covering all points in [a, b]
    #     i = bisect_left(dr, a)
    #     j = bisect_right(dr, b)

    #     # Safety: if the clamp collapsed
    #     if i >= j:
    #         return (-1, -1)

    #     return (i, j)

    def getDataRangeFromDates(
        self,
        startDate: Optional[datetime],
        endDate: Optional[datetime],
    ) -> Tuple[int, int]:
        """
        Returns (i, j) indices into self.dateRange / self.rainfallDataRange,
        where i is inclusive and j is exclusive. If there is no overlap with the
        data window, returns (-1, -1).
        """
        self._validate_parallel_series()

        # helper to make sure any datetime is UTC aware
        def to_utc(dt: datetime) -> datetime:
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)

        dr = [to_utc(d) for d in self.dateRange]
        data_start, data_end = dr[0], dr[-1]

        a = to_utc(startDate) if startDate else data_start
        b = to_utc(endDate)   if endDate   else data_end

        if b < a:
            a, b = b, a

        if b < data_start or a > data_end:
            return (-1, -1)

        a = max(a, data_start)
        b = min(b, data_end)

        i = bisect_left(dr, a)
        j = bisect_right(dr, b)

        if i >= j:
            return (-1, -1)
        return (i, j)

    def statsBetweenDates(
        self,
        startDate: Optional[datetime],
        endDate: Optional[datetime],
    ) -> Dict[str, Any]:
        """
        Returns dict with:
        minInt, maxInt (mm/hr), totDepth (mm), retPer (float or None)
        If no overlap with data, returns {'minInt': None, 'maxInt': None, 'totDepth': 0.0, 'retPer': None}
        """
        self._validate_parallel_series()

        min_i, max_j = self.getDataRangeFromDates(startDate, endDate)
        if (min_i, max_j) == (-1, -1):
            return {'minInt': None, 'maxInt': None, 'totDepth': 0.0, 'retPer': None}

        slice_vals = self.rainfallDataRange[min_i:max_j]
        if not slice_vals:
            return {'minInt': None, 'maxInt': None, 'totDepth': 0.0, 'retPer': None}

        # Intensities are mm/hr; depth over the window is sum(intensity)*dt(hours)
        dt_hours = self.rgTimestep / 60.0
        totalDepth = round(sum(slice_vals) * dt_hours, 1)

        minIntensity = min(slice_vals)
        maxIntensity = max(slice_vals)

        # Duration in hours based on the requested (clamped) timestamps, not just count*dt
        a = self.dateRange[min_i]
        b = self.dateRange[max_j - 1]
        duration_hrs = max((b - a).total_seconds() / 3600.0, 0.0)

        # Your empirical return period formula (guard against zero divisions)
        # RP = 10/(1.25*duration_hrs*(((0.0394*totalDepth)+0.1)**-3.55))
        if duration_hrs > 0 and totalDepth >= 0:
            denom = 1.25 * duration_hrs * ((0.0394 * totalDepth + 0.1) ** -3.55)
            retPer = round(10.0 / denom, 2) if denom != 0 else None
        else:
            retPer = None

        return {'minInt': minIntensity, 'maxInt': maxIntensity, 'totDepth': totalDepth, 'retPer': retPer}

    def eventStatsBetweenDates(
        self,
        startDate: datetime,
        endDate: datetime
    ):
        """
        Returns:
        (rgName, startTime_str_HHMM, duration_minutes_nonzero, totalDepth_mm, peakIntensity_mmhr, minutes_ge_6mmhr)
        If no overlap or all-zero slice, startTime becomes '' and metrics become 0.
        """
        self._validate_parallel_series()

        min_i, max_j = self.getDataRangeFromDates(startDate, endDate)
        rgName = getattr(self, "gaugeName", "")

        if (min_i, max_j) == (-1, -1):
            return (rgName, '', 0, 0.0, 0.0, 0)

        vals = self.rainfallDataRange[min_i:max_j]
        times = self.dateRange[min_i:max_j]

        if not vals:
            return (rgName, '', 0, 0.0, 0.0, 0)

        # First non-zero start time
        startTime = ''
        for v, t in zip(vals, times):
            if v != 0:
                startTime = datetime.strftime(t, "%H:%M")
                break

        # Duration with non-zero intensity
        duration_minutes = int(self.rgTimestep * sum(v > 0 for v in vals))

        # Depth over the window (mm)
        dt_hours = self.rgTimestep / 60.0
        totalDepth = round(sum(vals) * dt_hours, 1)

        peakIntensity = max(vals)
        period_ge_6 = int(self.rgTimestep * sum(v >= 6 for v in vals))

        return (rgName, startTime, duration_minutes, totalDepth, peakIntensity, period_ge_6)
                
class rainGauges:

    dictRainGauges: Dict[str, rainGauge] = {}
    rgsEarliestStart: datetime
    rgsLatestEnd: datetime

    def __init__(self):
        self.dictRainGauges = {}
        self.rgsEarliestStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
        self.rgsLatestEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')

    def read_from_database(self, conn: sqlite3.Connection):
        c = conn.cursor()
        try:
            c.execute(f"SELECT * FROM {Tables.RAIN_GAUGE}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.RAIN_GAUGE}' does not exist.")
            return  # Return without attempting to fetch rows

        rows = c.fetchall()
        column_names = [description[0] for description in c.description]
        for row in rows:
            row_dict = dict(zip(column_names, row))
            gauge = rainGauge()
            gauge.from_database_row_dict(row_dict)
            self.dictRainGauges[gauge.gaugeName] = gauge

        # rows = c.fetchall()
        # for row in rows:
        #     gauge = rainGauge()
        #     gauge.from_database_row(row)
        #     self.dictRainGauges[gauge.gaugeName] = gauge

    def write_to_database(self, conn: sqlite3.Connection) -> bool:
        result = False
        try:
            conn.execute(f'''DROP TABLE IF EXISTS {Tables.RAIN_GAUGE}''')
            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.RAIN_GAUGE} (
                            gaugeName TEXT PRIMARY KEY,
                            rFileSpec TEXT,
                            dateRange TEXT,
                            rainfallDataRange TEXT,
                            rgTimestep REAL,
                            minIntensity REAL,
                            maxIntensity REAL,
                            totalDepth REAL,
                            returnPeriod REAL,
                            x REAL,
                            y REAL
                        )''')
            for gauge in self.dictRainGauges.values():
                conn.execute(f'''INSERT OR REPLACE INTO {Tables.RAIN_GAUGE} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (gauge.gaugeName, gauge.rFileSpec, serialize_list(gauge.dateRange),
                              serialize_list(
                                  gauge.rainfallDataRange), gauge.rgTimestep, gauge.minIntensity,
                              gauge.maxIntensity, gauge.totalDepth, gauge.returnPeriod, gauge.x, gauge.y))
            conn.commit()
            result = True
            logger.debug("rainGauges.write_to_database Completed")

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            conn.rollback()
        except Exception as e:
            print(f"Exception in _query: {e}")
            conn.rollback()
        finally:
            return result
        #     conn.close()

    # def addRainGauge(self, fileSpec: str):

    #     try:
    #         if not self.alreadyOpen(fileSpec):

    #             objRG = self.getRainGaugeFromRFile(fileSpec)
    #             if objRG is not None:
    #                 self.dictRainGauges[objRG.gaugeName] = objRG
    #                 self.updateRGsMinMaxValues()
    #     except Exception as e:  # Capture the exception details
    #         QMessageBox.critical(
    #             None,
    #             'Error Adding Rain Gauge',
    #             f"Error parsing: {os.path.basename(fileSpec)}\n\nException: {str(e)}",
    #             QMessageBox.Ok
    #         )

    # def addRainGauge(self, fileSpec: str):

    #     try:
    #         if not self.alreadyOpen(fileSpec):

    #             start_old = time.perf_counter()
    #             objRG = self.getRainGaugeFromRFile(fileSpec)
    #             end_old = time.perf_counter()

    #             start_new = time.perf_counter()
    #             objRG_alt = self.getRainGaugeFromRFile_NEW(fileSpec)
    #             end_new = time.perf_counter()

    #             time_old = end_old - start_old
    #             time_new = end_new - start_new

    #             print(f"Old method time: {time_old:.6f} seconds")
    #             print(f"New method time: {time_new:.6f} seconds")
    #             print(f"Time difference (new - old): {time_new - time_old:.6f} seconds")

    #             if objRG is not None:
    #                 self.dictRainGauges[objRG.gaugeName] = objRG
    #                 self.updateRGsMinMaxValues()
    #     except Exception as e:  # Capture the exception details
    #         QMessageBox.critical(
    #             None,
    #             'Error Adding Rain Gauge',
    #             f"Error parsing: {os.path.basename(fileSpec)}\n\nException: {str(e)}",
    #             QMessageBox.Ok
    #         )

    def addRainGauge(self, fileSpec: str):

        try:
            if not self.alreadyOpen(fileSpec):

                objRG = self.getRainGaugeFromRFile(fileSpec)

                if objRG is not None:
                    self.dictRainGauges[objRG.gaugeName] = objRG
                    self.updateRGsMinMaxValues()
        except Exception as e:  # Capture the exception details
            QMessageBox.critical(
                None,
                'Error Adding Rain Gauge',
                f"Error parsing: {os.path.basename(fileSpec)}\n\nException: {str(e)}",
                QMessageBox.Ok
            )

    def updateRGsMinMaxValues(self):

        self.rgsEarliestStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
        self.rgsLatestEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')

        for rg in self.dictRainGauges.values():

            if self.rgsEarliestStart > rg.dateRange[0]:
                self.rgsEarliestStart = rg.dateRange[0]
            if self.rgsLatestEnd < rg.dateRange[len(rg.dateRange)-1]:
                self.rgsLatestEnd = rg.dateRange[len(rg.dateRange)-1]

    def getRainGauge(self, nameRG: str):

        if nameRG in self.dictRainGauges:
            return self.dictRainGauges[nameRG]

    def removeRainGauge(self, nameRG: str):
        if nameRG in self.dictRainGauges:
            self.dictRainGauges.pop(nameRG)
            self.updateRGsMinMaxValues()

    def alreadyOpen(self, fileSpec: str):

        for rg in self.dictRainGauges.items():
            if rg[1].rFileSpec == fileSpec:
                reply = QMessageBox.question(None, 'R file opened already!',
                                             rg[1].gaugeName +
                                             'was added with that R file.\n\nDo you want to replace it?',
                                             QMessageBox.Yes | QMessageBox.No,
                                             QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.dictRainGauges.pop(rg[1].gaugeName)
                    return False
                else:
                    return True

        return False

    # def _parse_raw_date(self, raw_date: str) -> datetime:
    #     stripped_date = raw_date.replace(" ", "")
    #     year = stripped_date[:2]
    #     month = stripped_date[2:4]
    #     day = stripped_date[4:6]
    #     hour = stripped_date[6:8]
    #     minute = stripped_date[8:10]
    #     return datetime.strptime(f"20{year}-{month}-{day} {hour}:{minute}", "%Y-%m-%d %H:%M")

    # # def _process_date_range(self, start_date: datetime, end_date: datetime) -> Tuple[List[datetime], datetime, datetime]:
    # #     dynamic_date_range = []
    # #     d1 = start_date
    # #     d2 = end_date
    # #     for i in range(len(self.rainfallDataRange)):
    # #         dynamic_date_range.append(d1 + timedelta(minutes=i * self.rgTimestep))
    # #     return dynamic_date_range, d1, d2

    # def _process_date_range(self, rg: rainGauge, start_date: datetime, end_date: datetime) -> List[datetime]:
    #     dynamic_date_range = []
    #     d1 = start_date
    #     # d2 = end_date
    #     for i in range(len(rg.rainfallDataRange)):
    #         dynamic_date_range.append(d1 + timedelta(minutes=i * rg.rgTimestep))
    #     return dynamic_date_range

    # def _extract_rainfall_data(self, rg: rainGauge, lines: List[str], start_row: int) -> None:
    #     for i in range(start_row, len(lines)):
    #         if lines[i][:5] in ("*END", "*$"):
    #             break
    #         for j in range(5):
    #             data = lines[i][9 + j * 15:15 + j * 15]
    #             if data.strip():
    #                 rg.rainfallDataRange.append(float(data))

    # def getRainGaugeFromRFile(self, fileSpec: str) -> Optional[rainGauge]:

    #     with open(fileSpec, 'r') as org_data:
    #         lines = org_data.readlines()

    #     myRG = rainGauge()
    #     myRG.rFileSpec = fileSpec

    #     for i, line in enumerate(lines):
    #         if line.startswith("**IDENTIFIER:"):
    #             rawRGName = lines[i]
    #             strippedRawRGName = rawRGName.replace(" ", "").strip()
    #             raw_RG_name = line[15:36].strip()
    #             myRG.gaugeName = raw_RG_name or os.path.splitext(os.path.basename(fileSpec))[0]
    #             if os.path.basename(fileSpec).split('.')[0] != myRG.gaugeName:
    #                 # Issue warning if the identifier does not match the file name
    #                 return None
    #         elif line.startswith("*CEND"):
    #             raw_dates = lines[i - 1]
    #             myRG.rgTimestep = float(raw_dates[-2:])
    #             start_row = i + 1
    #             break

    #     if myRG.gaugeName == "":
    #         # Set gauge name to file name if identifier not found
    #         myRG.gaugeName = os.path.splitext(os.path.basename(fileSpec))[0]

    #     dynamic_date_range = self._process_date_range(myRG, self._parse_raw_date(raw_dates), datetime.now())

    #     self._extract_rainfall_data(myRG, lines, start_row)

    #     myRG.dateRange = dynamic_date_range
    #     myRG.maxIntensity = max(myRG.rainfallDataRange)
    #     myRG.totalDepth = round(sum(myRG.rainfallDataRange) / (60 / myRG.rgTimestep), 1)

    #     unix_rounded_xmin_python_datetime = dynamic_date_range[0].timestamp()
    #     unix_rounded_xmax_python_datetime = dynamic_date_range[-1].timestamp()
    #     # unix_diff_days = ((unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime) / 60 / 60 / 24)
    #     unix_diff_mins = (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime) / 60

    #     if unix_diff_mins > 0:
    #         duration_hrs = unix_diff_mins / 60
    #         myRG.returnPeriod = round(10 / (1.25 * duration_hrs * (((0.0394 * myRG.totalDepth) + 0.1) ** -3.55)), 2)

    #     rainZipList = [(date.strftime("%d/%m/%Y %H:%M"), rainfall) for date, rainfall in zip(myRG.dateRange, myRG.rainfallDataRange)]
    #     myRG.rDataframe = pd.DataFrame(rainZipList, columns=["rain_date", "rainfall"])

    #     return myRG

    # def getRainGaugeFromRFile(self, fileSpec: str):

    #     with open(fileSpec, 'r', encoding="utf-8") as org_data:

    #         myRG = rainGauge()
    #         myRG.rFileSpec = fileSpec

    #         dynamicDateRange = []

    #         lines = []
    #         countCEND = 0

    #         myRG.rainfallDataRange = []
    #         myRG.dateRange = []
    #         rainDataAppend = False

    #         for line in org_data:

    #             lines.append(line)

    #         for i in range(len(lines)):

    #             if (lines[i])[:13] == "**IDENTIFIER:":

    #                 rawRGName = lines[i]

    #                 strippedRawRGName = rawRGName.replace(" ", "").strip()

    #                 myRG.gaugeName = strippedRawRGName[15:36]
    #                 if len(myRG.gaugeName) == 0:
    #                     myRG.gaugeName = os.path.splitext(
    #                         os.path.basename(fileSpec))[0]
    #                 if not os.path.basename(fileSpec).split('.')[0] == myRG.gaugeName:
    #                     QMessageBox.warning(None, 'Identifier Problem',
    #                                         'Internal Identifier: ' + myRG.gaugeName +
    #                                         ' does not match the file name.\n\nIt has not been added to the available gauges',
    #                                         QMessageBox.Ok)
    #                     return None

    #             if (lines[i])[:5] == "*CEND":

    #                 countCEND += 1

    #                 rawRainDates = (lines[i-1])
    #                 strippedRawRainDates = rawRainDates.replace(" ", "")
    #                 myRG.rgTimestep = float(strippedRawRainDates[-2:])
    #                 # ____________________________________________________________________________________________________________________________________
    #                 # This section is to acount for when there is a break in the data, and it is restarted, acounting for and missing time with
    #                 #  Zeros
    #                 if len(strippedRawRainDates) == 22:
    #                     strippedRawRainDatesStartDate = strippedRawRainDates[0:10]
    #                     strippedRainStartDate = strippedRawRainDatesStartDate[4:6]+'/'+strippedRawRainDatesStartDate[2:4]+'/' + '20' + \
    #                         strippedRawRainDatesStartDate[0:2]+' ' + \
    #                         strippedRawRainDatesStartDate[6:8] + \
    #                         ":"+strippedRawRainDatesStartDate[8:10]
    #                     d1Working = datetime.strptime(
    #                         strippedRainStartDate, "%d/%m/%Y %H:%M")

    #                 if len(strippedRawRainDates) == 26:
    #                     strippedRawRainDatesStartDate = strippedRawRainDates[0:12]
    #                     strippedRainStartDate = strippedRawRainDatesStartDate[6:8]+'/'+strippedRawRainDatesStartDate[4:6]+'/' + '20' + \
    #                         strippedRawRainDatesStartDate[2:4]+' '+strippedRawRainDatesStartDate[8:10] + \
    #                         ":"+strippedRawRainDatesStartDate[10:12]
    #                     d1Working = datetime.strptime(
    #                         strippedRainStartDate, "%d/%m/%Y %H:%M")

    #                 if countCEND == 1:

    #                     dynamicDateRange.append(d1Working)
    #                     d1 = d1Working

    #                 if countCEND > 1:

    #                     # the d1 working is the start of the current, dynamic is the generated date range
    #                     if d1Working > (dynamicDateRange[-1]):

    #                         gapDiff = (d1Working - (dynamicDateRange[-1]))

    #                         rowsToAdd = (
    #                             gapDiff/timedelta(minutes=myRG.rgTimestep))

    #                         z = 0
    #                         # Append ZEROS to list
    #                         while z < rowsToAdd:

    #                             myRG.rainfallDataRange.append(0)

    #                             # dynamicDateRange.append(dynamicDateRange[-1] + timedelta(minutes=myRG.rgTimestep))########

    #                             z += 1

    #                     elif (d1Working - timedelta(minutes=myRG.rgTimestep)) == d2:

    #                         gapDiff = (
    #                             (d1Working - timedelta(minutes=myRG.rgTimestep)) - d2)

    #                 if len(strippedRawRainDates) == 22:
    #                     strippedRawRainDatesEndDate = strippedRawRainDates[10:20]
    #                     strippedRainEndDate = strippedRawRainDatesEndDate[4:6]+'/'+strippedRawRainDatesEndDate[2:4]+'/'+'20' + \
    #                         strippedRawRainDatesEndDate[0:2]+' ' + \
    #                         strippedRawRainDatesEndDate[6:8] + \
    #                         ":"+strippedRawRainDatesEndDate[8:10]
    #                     d2 = datetime.strptime(
    #                         strippedRainEndDate, "%d/%m/%Y %H:%M")

    #                 elif len(strippedRawRainDates) == 26:
    #                     strippedRawRainDatesEndDate = strippedRawRainDates[12:24]
    #                     strippedRainEndDate = strippedRawRainDatesEndDate[6:8]+'/'+strippedRawRainDatesEndDate[4:6]+'/'+'20' + \
    #                         strippedRawRainDatesEndDate[2:4]+' '+strippedRawRainDatesEndDate[8:10] + \
    #                         ":"+strippedRawRainDatesEndDate[10:12]
    #                     d2 = datetime.strptime(
    #                         strippedRainEndDate, "%d/%m/%Y %H:%M")

    #                 startRow = i+1
    #                 rainDataAppend = True

    #             if (lines[i])[:4] == "*END" or (lines[i])[:2] == "*$":

    #                 # end_row = i-1
    #                 rainDataAppend = False

    #             if rainDataAppend is True and (lines[i])[3:6] != "" and i >= startRow:

    #                 if (lines[i])[9:15] != '':
    #                     myRG.rainfallDataRange.append(
    #                         float((lines[i])[9:15]))  # 1

    #                 if (lines[i])[24:30] != '':
    #                     myRG.rainfallDataRange.append(
    #                         float((lines[i])[24:30]))  # 2

    #                 if (lines[i])[39:45] != '':
    #                     myRG.rainfallDataRange.append(
    #                         float((lines[i])[39:45]))  # 3

    #                 if (lines[i])[54:60] != '':
    #                     myRG.rainfallDataRange.append(
    #                         float((lines[i])[54:60]))  # 4

    #                 if (lines[i])[69:75] != '':
    #                     myRG.rainfallDataRange.append(
    #                         float((lines[i])[69:75]))  # 5

    #         # __________________________
    #         # RG date range extract

    #         delta = d2 - d1

    #         for w in range(len(myRG.rainfallDataRange)):

    #             myRG.dateRange.append(
    #                 d1 + timedelta(minutes=w * myRG.rgTimestep))

    #         rainDateRangeStart = myRG.dateRange[0]
    #         rainDateRangeEnd = myRG.dateRange[len(myRG.dateRange)-1]

    #         myRG.maxIntensity = (max(myRG.rainfallDataRange))
    #         myRG.totalDepth = round(
    #             (sum(myRG.rainfallDataRange))/(60/myRG.rgTimestep), 1)

    #         unix_rounded_xmin_python_datetime = calendar.timegm(
    #             rainDateRangeStart.timetuple())
    #         unix_rounded_xmax_python_datetime = calendar.timegm(
    #             rainDateRangeEnd.timetuple())
    #         unix_diff_days = (
    #             ((unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)/60)/24
    #         unix_diff_mins = (
    #             (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)

    #         if unix_diff_mins > 0:
    #             # myRG.returnPeriod = round(
    #             #     (0.00494*(myRG.totalDepth+2.54)**3.55)/unix_diff_mins, 2)
    #             duration_hrs = unix_diff_mins / 60
    #             myRG.returnPeriod = round(
    #                 10/(1.25*duration_hrs*(((0.0394*myRG.totalDepth)+0.1)**-3.55)), 2)

    #         rainZipList = []
    #         rainZipListDates = []

    #         for i in range(len(myRG.dateRange)):
    #             rainZipListDates.append(
    #                 myRG.dateRange[i].strftime("%d/%m/%Y %H:%M"))

    #         # This combines the rainfall date range an rainfall data into a list of 2 columns to be convert to dataframe later
    #         rainZipList = list(zip(rainZipListDates, myRG.rainfallDataRange))

    #         # myRG.rDataframe = pd.DataFrame(
    #         #     rainZipList, columns=["rain_date", "rainfall"])

    #         return myRG

    def getRainGaugeFromRFile(self, fileSpec: str):

        with open(fileSpec, 'r', encoding="utf-8") as org_data:

            file_data = parse_file(fileSpec)

            all_units = [unit for record in file_data["payload"] for unit in record]

            myRG = rainGauge()
            myRG.rFileSpec = fileSpec

            constants = file_data["constants"]

            # Parse the START and END dates using the helper.
            start_dt = parse_date(constants["START"])
            end_dt = parse_date(constants["END"])
            duration_hrs = (end_dt - start_dt).total_seconds() / 3600
            duration_mins = (end_dt - start_dt).total_seconds() / 60

            # Get the INTERVAL (assumed to be in minutes)
            interval_minutes = int(constants["INTERVAL"])
            myRG.rgTimestep = interval_minutes
            interval = timedelta(minutes=interval_minutes)

            # Generate the date range.
            myRG.dateRange = np.arange(start_dt, end_dt + interval, interval).tolist()

            no_of_records = int(duration_mins / interval_minutes) + 1
            i_record = 0

            myRG.rainfallDataRange = []
            for unit in all_units:
                i_record += 1
                if i_record <= no_of_records:
                    intensity = unit.get("INTENSITY")
                    if intensity is not None:
                        myRG.rainfallDataRange.append(float(intensity))
                    else:
                        myRG.rainfallDataRange.append(0.0)

            # Check that the number of dates matches the number of data units.
            if len(myRG.dateRange) != len(myRG.rainfallDataRange):
                print("Warning: Mismatch in number of timestamps and data points!")

            record_line = file_data['header'].get('IDENTIFIER', '')
            if record_line:
                parts = [p.strip() for p in record_line.split(',')]
                if len(parts) >= 2:
                    myRG.gaugeName = parts[1]

            myRG.maxIntensity = (max(myRG.rainfallDataRange))
            myRG.totalDepth = round((sum(myRG.rainfallDataRange))/(60/myRG.rgTimestep), 1)
            myRG.returnPeriod = round(10/(1.25*duration_hrs*(((0.0394*myRG.totalDepth)+0.1)**-3.55)), 2)

            return myRG
        
    def writeRFileFromRainGauge(self, file_path: str, gauge_name: str):

            """
            Given a rainGauge object (rg) with at least the following attributes:
            - rg.data_format (e.g. "rainGauge")
            - rg.gaugeName (name of the gauge)
            - rg.dateRange (list of datetime objects)
            - rg.rgTimestep (the interval in minutes, as an int)
            - rg.rainfallDataRange (list of float intensity values)
            This function writes a raingauge data file using a fixed format.
            """
            rg = self.dictRainGauges[gauge_name]
            if rg is None:
                return
            
            # Define the header values.
            header = {
                "DATA_FORMAT": "1,ASCII",
                "IDENTIFIER": f"1,{rg.gaugeName}",
                "FIELD": "1,INTENSITY",
                "UNITS": "1,MM/HR",
                "FORMAT": "2,F15.1,[5]",
                "RECORD_LENGTH": "I2,75"
            }
            header_lines = write_header(header)

            constants_format = '8,A20,F7.2/15F5.1/15F5.1/D10,2X,D10,I4'
            
            Constant = namedtuple('Constant', ['name', 'units', 'value'])

            constants = [
                Constant('LOCATION', '', 'UNKNOWN'),  #Need some code here to convert the x,y to a national grid reference 
                Constant('0_ANT_RAIN', 'MM', -1),
                Constant('1_ANT_RAIN', 'MM', -1),
                Constant('2_ANT_RAIN', 'MM', -1),
                Constant('3_ANT_RAIN', 'MM', -1),
                Constant('4_ANT_RAIN', 'MM', -1),
                Constant('5_ANT_RAIN', 'MM', -1),
                Constant('6_ANT_RAIN', 'MM', -1),
                Constant('7_ANT_RAIN', 'MM', -1),
                Constant('8_ANT_RAIN', 'MM', -1),
                Constant('9_ANT_RAIN', 'MM', -1),
                Constant('10_ANT_RAIN', 'MM', -1),
                Constant('11_ANT_RAIN', 'MM', -1),
                Constant('12_ANT_RAIN', 'MM', -1),
                Constant('13_ANT_RAIN', 'MM', -1),
                Constant('14_ANT_RAIN', 'MM', -1),
                Constant('15_ANT_RAIN', 'MM', -1),
                Constant('16_ANT_RAIN', 'MM', -1),
                Constant('17_ANT_RAIN', 'MM', -1),
                Constant('18_ANT_RAIN', 'MM', -1),
                Constant('19_ANT_RAIN', 'MM', -1),
                Constant('20_ANT_RAIN', 'MM', -1),
                Constant('21_ANT_RAIN', 'MM', -1),
                Constant('22_ANT_RAIN', 'MM', -1),
                Constant('23_ANT_RAIN', 'MM', -1),
                Constant('24_ANT_RAIN', 'MM', -1),
                Constant('25_ANT_RAIN', 'MM', -1),
                Constant('26_ANT_RAIN', 'MM', -1),
                Constant('27_ANT_RAIN', 'MM', -1),
                Constant('28_ANT_RAIN', 'MM', -1),
                Constant('29_ANT_RAIN', 'MM', -1),
                Constant('30_ANT_RAIN', 'MM', -1),
                Constant('START', 'GMT', rg.dateRange[0]),
                # Constant('END', 'GMT', rg.dateRange[-1] + timedelta(minutes=rg.rgTimestep)),
                Constant('END', 'GMT', rg.dateRange[-1]),
                Constant('INTERVAL', 'MIN', rg.rgTimestep)
            ]

            # Build the constants block.
            constants_lines = write_constants(constants, constants_format)
            
            # RECORD_LENGTH: here we extract the numeric width from the header.
            record_length = int(header["RECORD_LENGTH"].split(",")[1].strip())
            # payload_lines = write_rg_payload(rg, header["FORMAT"], record_length, header["FIELD"])
            payload_lines = write_rg_payload(rg, header["FORMAT"], record_length)
            
            # Assemble the file lines.

            file_lines = []
            file_lines.extend(header_lines)
            file_lines.extend(constants_lines[0])
            file_lines.append("*CSTART")
            file_lines.extend(constants_lines[1])
            file_lines.append("*CEND")
            file_lines.extend(payload_lines)
            file_lines.append("*END")

            # Write the lines to the file.
            file_spec = os.path.join(file_path, f"{rg.gaugeName}.r")

            if os.path.exists(file_spec):
                print(f"File {file_spec} already exists.")
            else:
                with open(file_spec, "w", encoding="utf-8") as f:
                    for line in file_lines:
                        f.write(line + "\n")
        
class plottedRainGauges():

    plotRGs: Dict[str, rainGauge]
    plotEarliestStart: datetime = datetime.strptime('2172-05-12', '%Y-%m-%d')
    plotLatestEnd: datetime = datetime.strptime('1972-05-12', '%Y-%m-%d')
    __plotCurrentStart: datetime = datetime.strptime('2172-05-12', '%Y-%m-%d')
    __plotCurrentEnd: datetime = datetime.strptime('1972-05-12', '%Y-%m-%d')
    plotMinIntensity = 0
    plotMaxIntensity = 0
    plotTotalDepth = 0
    plotReturnPeriod = 0

    def __init__(self):
        self.plotRGs = {}

    def setPlotDateLimits(self, startDate: Optional[datetime], endDate: Optional[datetime]):
        if startDate is None:
            self.__plotCurrentStart = datetime.strptime(
                '2172-05-12', '%Y-%m-%d')
        else:
            self.__plotCurrentStart = startDate
        if endDate is None:
            self.__plotCurrentEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')
        else:
            self.__plotCurrentEnd = endDate
        self.updatePlottedRGsMinMaxValues()

    def getPlotCurrentStart(self):
        return self.__plotCurrentStart

    def getPlotCurrentEnd(self):
        return self.__plotCurrentEnd

    def clear(self):

        self.plotRGs.clear()
        self.updatePlottedRGsMinMaxValues()

    def addRG(self, objRG: rainGauge, updateMaxMin: bool = True):

        if objRG.gaugeName not in self.plotRGs:

            self.plotRGs[objRG.gaugeName] = objRG
            if updateMaxMin:
                self.updatePlottedRGsMinMaxValues()

            return True

        else:

            return False

    def removeRG(self, nameRG: str):

        if nameRG in self.plotRGs:
            self.plotRGs.pop(nameRG)
            self.updatePlottedRGsMinMaxValues()
            return True
        return False

    def getRGTimestep(self, nameRG: str):

        if nameRG in self.plotRGs:
            return self.plotRGs[nameRG].rgTimestep

    def updatePlottedRGsMinMaxValues(self):

        self.plotEarliestStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
        self.plotLatestEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')
        self.plotMinIntensity = 0
        self.plotMaxIntensity = 0
        self.plotTotalDepth = 0
        self.plotReturnPeriod = 0

        for rg in self.plotRGs.values():

            if self.plotEarliestStart > rg.dateRange[0]:
                self.plotEarliestStart = rg.dateRange[0]
            if self.plotLatestEnd < rg.dateRange[len(rg.dateRange)-1]:
                self.plotLatestEnd = rg.dateRange[len(rg.dateRange)-1]

            rg_start_time = calendar.timegm(rg.dateRange[0].timetuple())
            rg_end_time = calendar.timegm(rg.dateRange[-1].timetuple())
            start_time = calendar.timegm(
                self.getPlotCurrentStart().timetuple())
            end_time = calendar.timegm(self.getPlotCurrentEnd().timetuple())

            if (rg_start_time < start_time) and (start_time < rg_end_time):
                unix_rounded_xmin_python_datetime = calendar.timegm(
                    rg.dateRange[0].timetuple())
                unix_rounded_xmax_python_datetime = calendar.timegm(
                    self.getPlotCurrentStart().timetuple())
                unix_diff_mins = (
                    (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)
                min_row = int(unix_diff_mins / rg.rgTimestep)
            else:
                min_row = 0

            if (rg_start_time < end_time) and (end_time < rg_end_time):
                unix_rounded_xmin_python_datetime = calendar.timegm(
                    rg.dateRange[0].timetuple())
                unix_rounded_xmax_python_datetime = end_time
                unix_diff_mins = (
                    (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)
                max_row = int(unix_diff_mins / rg.rgTimestep)
            else:
                max_row = len(rg.rainfallDataRange)

            self.plotMaxIntensity = max(rg.rainfallDataRange[min_row:max_row])
            self.plotMinIntensity = min(rg.rainfallDataRange[min_row:max_row])
            totalDepth = round(
                (sum(rg.rainfallDataRange[min_row:max_row]))/(60/rg.rgTimestep), 1)
            self.plotTotalDepth = self.plotTotalDepth + totalDepth

            unix_rounded_xmin_python_datetime = calendar.timegm(
                self.__plotCurrentStart.timetuple())
            unix_rounded_xmax_python_datetime = calendar.timegm(
                self.__plotCurrentEnd.timetuple())
            # unix_diff_days = (
            #     ((unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)/60)/24
            unix_diff_mins = (
                (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)

            # self.plotReturnPeriod = round(
            #     (0.00494*(self.plotTotalDepth+2.54)**3.55)/unix_diff_mins, 2)
            duration_hrs = unix_diff_mins / 60
            self.plotReturnPeriod = round(
                10/(1.25*duration_hrs*(((0.0394*self.plotTotalDepth)+0.1)**-3.55)), 2)

# class qgisFlowMonitors(flowMonitors):

#     vlFlowMonitors = None

#     def __init__(self, myCrs=QgsCoordinateReferenceSystem("EPSG:27700")):
#         super().__init__()

#         self.vlFlowMonitors = QgsVectorLayer("Point?crs=" + myCrs.authid(), "flowbot Flow Monitors", "memory")
#         self.vlFlowMonitors.setReadOnly(True)
#         pr = self.vlFlowMonitors.dataProvider()

#         pr.addAttributes([QgsField('dataID', QVariant.String),
#                           QgsField('fdvFileSpec', QVariant.String),
#                           QgsField('monitorName', QVariant.String),
#                           QgsField('flowUnits', QVariant.String),
#                           QgsField('depthUnits', QVariant.String),
#                           QgsField('velocityUnits', QVariant.String),
#                           QgsField('rainGaugeName', QVariant.String),
#                           QgsField('fmTimestep', QVariant.Double),
#                           QgsField('dateRange', QVariant.String),
#                           QgsField('flowDataRange', QVariant.String),
#                           QgsField('depthDataRange', QVariant.String),
#                           QgsField('velocityDataRange', QVariant.String),
#                           QgsField('minFlow', QVariant.Double),
#                           QgsField('maxFlow', QVariant.Double),
#                           QgsField('totalVolume', QVariant.Double),
#                           QgsField('minDepth', QVariant.Double),
#                           QgsField('maxDepth', QVariant.Double),
#                           QgsField('minVelocity', QVariant.Double),
#                           QgsField('maxVelocity', QVariant.Double),
#                           QgsField('hasModelData', QVariant.Bool),
#                           QgsField('modelDataPipeRef', QVariant.String),
#                           QgsField('modelDataRG', QVariant.String),
#                           QgsField('modelDataPipeLength', QVariant.Double),
#                           QgsField('modelDataPipeShape', QVariant.String),
#                           QgsField('modelDataPipeDia', QVariant.Double),
#                           QgsField('modelDataPipeHeight', QVariant.Double),
#                           QgsField('modelDataPipeRoughness', QVariant.Double),
#                           QgsField('modelDataPipeUSInvert', QVariant.Double),
#                           QgsField('modelDataPipeDSInvert', QVariant.Double),
#                           QgsField('modelDataPipeSystemType', QVariant.String)])

#         self.vlFlowMonitors.updateFields()
#         QgsProject.instance().addMapLayer(self.vlFlowMonitors)

#     def __del__(self):

#         if not self.vlFlowMonitors is None:
#             QgsProject.instance().removeMapLayer(self.vlFlowMonitors)

#     def updateGISLocation(self, fm_name, pPoint=None, _x=None, _y=None):

#         qFM = self.getFlowMonitor(fm_name)
#         qFM.__class__ = qgisFlowMonitor

#         if not pPoint is None:
#             qFM.myX = pPoint.x()
#             qFM.myY = pPoint.y()
#             f = QgsFeature()
#             f.setGeometry(QgsGeometry.fromPointXY(pPoint))
#         else:
#             qFM.myX = _x
#             qFM.myY = _y
#             f = QgsFeature()
#             f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(_x, _y)))

#         f.setAttributes(['FM',
#                          qFM.fdvFileSpec,
#                          qFM.monitorName,
#                          qFM.flowUnits,
#                          qFM.depthUnits,
#                          qFM.velocityUnits,
#                          qFM.rainGaugeName,
#                          qFM.fmTimestep,
#                          '',
#                          '',
#                          '',
#                          '',
#                          qFM.minFlow,
#                          qFM.maxFlow,
#                          qFM.totalVolume,
#                          qFM.minDepth,
#                          qFM.maxDepth,
#                          qFM.minVelocity,
#                          qFM.maxVelocity,
#                          qFM.hasModelData,
#                          qFM.modelDataPipeRef,
#                          qFM.modelDataRG,
#                          qFM.modelDataPipeLength,
#                          qFM.modelDataPipeShape,
#                          qFM.modelDataPipeDia,
#                          qFM.modelDataPipeHeight,
#                          qFM.modelDataPipeRoughness,
#                          qFM.modelDataPipeUSInvert,
#                          qFM.modelDataPipeDSInvert,
#                          qFM.modelDataPipeSystemType])

#         pr = self.vlFlowMonitors.dataProvider()
#         pr.addFeature(f)
#         self.vlFlowMonitors.updateExtents()

#         self.dictFlowMonitors[qFM.monitorName] = qFM

#     def removeGISLocation(self, fm_name):

#         qFM = self.getFlowMonitor(fm_name)
#         qFM.__class__ = flowMonitor

#         for f in self.vlFlowMonitors.getFeatures():
#             if f.attribute("monitorName") == qFM.monitorName:
#                 self.vlFlowMonitors.dataProvider().deleteFeatures([f.id()])
#                 self.vlFlowMonitors.updateExtents()
#                 break

#         self.dictFlowMonitors[qFM.monitorName] = qFM

#     def removeGISLayer(self):

# class mappedFlowMonitor(flowMonitor):
#     def __init__(self, mFMName: str, latitude: float = 0.0, longitude: float = 0.0):
#         super().__init__()
#         self.monitorName = mFMName
#         self.latitude: float = latitude
#         self.longitude: float = longitude

# class mappedFlowMonitors():
#     def __init__(self):
#         self.dictMappedFlowMonitors: Dict[str, flowMonitor] = {}
#         self.vl_flow_monitors: QgsVectorLayer = None

#     def addMappedFlowMonitor(self, monitor: flowMonitor):
#         if monitor is not None:
#             if monitor.monitorName not in self.dictMappedFlowMonitors:
#                 self.dictMappedFlowMonitors[monitor.monitorName] = monitor

#     def updateFlowMonitorLocation(self, fmName: str, x: float, y: float):
#         if fmName in self.dictMappedFlowMonitors:
#             self.dictMappedFlowMonitors[fmName].x = x
#             self.dictMappedFlowMonitors[fmName].y = y
#         else:
#             print(f"Flow monitor {fmName} not found.")

#     def getMappedFlowMonitor(self, nameFM: str) -> Optional[flowMonitor]:
#         return self.dictMappedFlowMonitors.get(nameFM)

#     def removeMappedFlowMonitor(self, fmName: str):
#         if fmName in self.dictMappedFlowMonitors:
#             del self.dictMappedFlowMonitors[fmName]
#         else:
#             print(f"Mapped flow monitor {fmName} not found.")

#     def isMapped(self, fmName: str):
#         return fmName in self.dictMappedFlowMonitors

#     def locationByFMName(self, fmName: str) -> Optional[List[float]]:
#         if fmName in self.dictMappedFlowMonitors:
#             return [self.dictMappedFlowMonitors[fmName].x, self.dictMappedFlowMonitors[fmName].y]

class mappedFlowMonitors():
    def __init__(self, qgs_app):
        self._thisQgsApp = qgs_app
        self.dictMappedFlowMonitors: Dict[str, flowMonitor] = {}
        self.vl_flow_monitors: QgsVectorLayer = None
        self.initialize_vector_layer()

    def initialize_vector_layer(self):

        crs = QgsCoordinateReferenceSystem("EPSG:27700")  # Set to BNG (EPSG:27700)

        """Initialize the QgsVectorLayer with appropriate fields for flow monitor data."""
        self.vl_flow_monitors = QgsVectorLayer(
            "Point?crs=EPSG:27700",  # Specify the CRS here
            "Flow Monitors",
            "memory"
        )
        provider = self.vl_flow_monitors.dataProvider()
        
        # Add fields corresponding to flowMonitor attributes
        provider.addAttributes([QgsField("monitor_name", QVariant.String)])
        self.vl_flow_monitors.updateFields()
        self.vl_flow_monitors.setCrs(crs)

        symbol = QgsMarkerSymbol.createSimple({'name': 'square', 'color': 'red', 'outline_color': 'black', 'outline_width': '0.2', 'size': '3'})
        self.vl_flow_monitors.renderer().setSymbol(symbol)
        
        # Create a label for each point
        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = '"monitor_name"'
        label_settings.isExpression = True
        label_settings.placement = Qgis.LabelPlacement.AroundPoint
        label_settings.enabled = True
        
        # Set text format
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", 10))
        text_format.setSize(10)
        text_format.setColor(QColor("black"))

        buffer_settings = QgsTextBufferSettings()
        buffer_settings.setEnabled(True)
        buffer_settings.setSize(1)
        buffer_settings.setColor(QColor("white"))

        text_format.setBuffer(buffer_settings)
                
        label_settings.setFormat(text_format)

        # Apply label settings
        label = QgsVectorLayerSimpleLabeling(label_settings)
        self.vl_flow_monitors.setLabelsEnabled(True)
        self.vl_flow_monitors.setLabeling(label)

    def addMappedFlowMonitor(self, monitor: flowMonitor):
        """Add a flow monitor to both the dictionary and the vector layer."""
        if monitor is not None:
            if monitor.monitorName not in self.dictMappedFlowMonitors:
                # Add to dictionary
                self.dictMappedFlowMonitors[monitor.monitorName] = monitor
                
                # Add to vector layer
                self._add_monitor_to_layer(monitor)
    
    def _add_monitor_to_layer(self, monitor: flowMonitor):
        """Helper method to add a single monitor to the vector layer."""
        if self.vl_flow_monitors is None:
            self.initialize_vector_layer()
            
        provider = self.vl_flow_monitors.dataProvider()
        
        # Create a new feature
        feature = QgsFeature()
        
        # Set geometry from x and y coordinates
        point = QgsPointXY(monitor.x, monitor.y)
        feature.setGeometry(QgsGeometry.fromPointXY(point))
        
        # # Set attributes
        # feature.setAttributes([
        #     monitor.monitorName,
        #     monitor.flowUnits,
        #     monitor.depthUnits,
        #     monitor.velocityUnits,
        #     monitor.fmTimestep,
        #     monitor.fdvFileSpec
        # ])
        
        # Set attributes
        feature.setAttributes([monitor.monitorName])
        
        # Add the feature to the layer
        provider.addFeature(feature)
        self.vl_flow_monitors.updateExtents()
        self.vl_flow_monitors.triggerRepaint()

    def updateFlowMonitorLocation(self, fmName: str, x: float, y: float):
        """Update the location of a flow monitor in both the dictionary and vector layer."""
        if fmName in self.dictMappedFlowMonitors:
            # Update in dictionary
            self.dictMappedFlowMonitors[fmName].x = x
            self.dictMappedFlowMonitors[fmName].y = y
            
            # Update in vector layer
            self._update_monitor_in_layer(fmName)
        else:
            print(f"Flow monitor {fmName} not found.")

    def _update_monitor_in_layer(self, fmName: str):
        """Helper method to update a monitor in the vector layer."""
        if self.vl_flow_monitors is None:
            return
            
        # Find the feature with the given monitor name
        features = self.vl_flow_monitors.getFeatures(f"monitor_name = '{fmName}'")
        
        for feature in features:
            # Get monitor from dictionary
            monitor = self.dictMappedFlowMonitors[fmName]
            
            # Update geometry
            point = QgsPointXY(monitor.x, monitor.y)
            
            # Update the feature's geometry
            self.vl_flow_monitors.dataProvider().changeGeometryValues({
                feature.id(): QgsGeometry.fromPointXY(point)
            })
            
            # # Update attributes if needed
            # attrs = {
            #     0: monitor.monitorName,
            #     1: monitor.flowUnits,
            #     2: monitor.depthUnits,
            #     3: monitor.velocityUnits,
            #     4: monitor.fmTimestep,
            #     5: monitor.fdvFileSpec
            # }
            
            # self.vl_flow_monitors.dataProvider().changeAttributeValues({
            #     feature.id(): attrs
            # })
            
        self.vl_flow_monitors.updateExtents()
        self.vl_flow_monitors.triggerRepaint()

    def getMappedFlowMonitor(self, nameFM: str) -> Optional[flowMonitor]:
        """Get a flow monitor by name from the dictionary."""
        return self.dictMappedFlowMonitors.get(nameFM)

    def removeMappedFlowMonitor(self, fmName: str):
        """Remove a flow monitor from both the dictionary and vector layer."""
        if fmName in self.dictMappedFlowMonitors:
            # Remove from dictionary
            del self.dictMappedFlowMonitors[fmName]
            
            # Remove from vector layer
            if self.vl_flow_monitors is not None:
                # Find and remove the feature with the given monitor name
                features = self.vl_flow_monitors.getFeatures(f"monitor_name = '{fmName}'")
                feature_ids = [feature.id() for feature in features]
                
                if feature_ids:
                    self.vl_flow_monitors.dataProvider().deleteFeatures(feature_ids)
                    self.vl_flow_monitors.updateExtents()
                    self.vl_flow_monitors.triggerRepaint()
        else:
            print(f"Mapped flow monitor {fmName} not found.")

    def isMapped(self, fmName: str):
        """Check if a flow monitor is mapped."""
        return fmName in self.dictMappedFlowMonitors

    def locationByFMName(self, fmName: str) -> Optional[List[float]]:
        """Get the location of a flow monitor by name."""
        if fmName in self.dictMappedFlowMonitors:
            return [self.dictMappedFlowMonitors[fmName].x, self.dictMappedFlowMonitors[fmName].y]
        return None
        
    def syncVectorLayer(self):
        """Rebuild the vector layer from the dictionary data (useful after bulk operations)."""
        if self.vl_flow_monitors is None:
            self.initialize_vector_layer()
            
        # Clear existing features
        self.vl_flow_monitors.dataProvider().truncate()
        
        # Add all monitors from dictionary
        features = []
        for name, monitor in self.dictMappedFlowMonitors.items():
            feature = QgsFeature()
            point = QgsPointXY(monitor.x, monitor.y)
            feature.setGeometry(QgsGeometry.fromPointXY(point))
            
            # feature.setAttributes([
            #     monitor.monitorName,
            #     monitor.flowUnits,
            #     monitor.depthUnits,
            #     monitor.velocityUnits,
            #     monitor.fmTimestep,
            #     monitor.fdvFileSpec
            # ])

            feature.setAttributes([monitor.monitorName])            

            features.append(feature)
            
        # Add all features at once
        if features:
            self.vl_flow_monitors.dataProvider().addFeatures(features)
            self.vl_flow_monitors.updateExtents()
            self.vl_flow_monitors.triggerRepaint()
            
    def getFlowMonitorsInBoundingBox(self, xMin: float, yMin: float, xMax: float, yMax: float) -> List[str]:
        """Get names of flow monitors within a bounding box (spatial query)."""
        if self.vl_flow_monitors is None:
            return []
            
        # Create a bounding box geometry
        bbox = QgsGeometry.fromRect(QgsRectangle(xMin, yMin, xMax, yMax))
        
        # Query features within the bounding box
        request = QgsFeatureRequest().setFilterRect(bbox.boundingBox())
        features = self.vl_flow_monitors.getFeatures(request)
        
        # Extract monitor names
        result = []
        for feature in features:
            monitor_name = feature["monitor_name"]
            if monitor_name:
                result.append(monitor_name)
                
        return result
          
# class mappedRainGauges():
#     def __init__(self):
#         self.dictMappedRainGauges: Dict[str, rainGauge] = {}
#         self.vl_rain_gauges: QgsVectorLayer = None

#     def addMappedRainGauge(self, rg: rainGauge):
#         if rg is not None:
#             if rg.gaugeName not in self.dictMappedRainGauges:
#                 self.dictMappedRainGauges[rg.gaugeName] = rg

#     def updateRainGaugeLocation(self, rgName: str, x: float, y: float):
#         if rgName in self.dictMappedRainGauges:
#             self.dictMappedRainGauges[rgName].x = x
#             self.dictMappedRainGauges[rgName].y = y
#         else:
#             print(f"Mapped rain gauge {rgName} not found.")

#     def getMappedRainGauge(self, rgName: str) -> Optional[rainGauge]:
#         return self.dictMappedRainGauges.get(rgName)

#     def removeMappedRainGauge(self, rgName: str):
#         if rgName in self.dictMappedRainGauges:
#             del self.dictMappedRainGauges[rgName]
#         else:
#             print(f"Mapped rain gauge {rgName} not found.")

#     def isMapped(self, rgName: str):
#         return rgName in self.dictMappedRainGauges

#     def locationByRainGaugeName(self, rgName: str) -> Optional[List[float]]:
#         if rgName in self.dictMappedRainGauges:
#             return [self.dictMappedRainGauges[rgName].x, self.dictMappedRainGauges[rgName].y]
        
# from typing import Dict, List, Optional
# from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsField, QgsProject, QgsRectangle, QgsFeatureRequest
# from PyQt5.QtCore import QVariant


class mappedRainGauges():
    def __init__(self, qgs_app):
        self._thisQgsApp = qgs_app
        self.dictMappedRainGauges: Dict[str, rainGauge] = {}
        self.vl_rain_gauges: Optional[QgsVectorLayer] = None
        self.rl_total_depth: Optional[QgsRasterLayer] = None
        self._current_event: Optional[surveyEvent] = None
        self.initialize_vector_layer()

    @property
    def current_event(self):
        return self._current_event

    @current_event.setter
    def current_event(self, new_event: surveyEvent):
        if self._current_event != new_event:
            self._current_event = new_event
            self.on_current_event_changed()

    def on_current_event_changed(self):
        """This function runs whenever current_event is changed."""
        
        if not self.vl_rain_gauges or not self.vl_rain_gauges.isValid():
            print("Vector layer is not valid or not set.")
            return

        self.vl_rain_gauges.startEditing()  # Enable editing mode

        for rg in self.dictMappedRainGauges.values():
            # Get all features and find the matching one
            for feature in self.vl_rain_gauges.getFeatures():
                if feature["gauge_name"] == rg.gaugeName:
                    
                    if self.current_event is not None:
                        stats = rg.statsBetweenDates(self.current_event.eventStart, self.current_event.eventEnd)
                        totDepth = stats['totDepth']
                    else:
                        totDepth = rg.totalDepth

                    # Update feature attributes
                    # feature.setAttribute("gauge_name", rg.gaugeName)  # Ensure this is correct
                    feature.setAttribute("total_depth", totDepth)  # Ensure the field name matches
                    
                    # Commit changes
                    self.vl_rain_gauges.updateFeature(feature)

        self.vl_rain_gauges.commitChanges()  # Save changes
        # self.vl_rain_gauges.triggerRepaint()  # Refresh the layer

        if self.rl_total_depth is not None:
            new_extent = self.get_maximum_of_extents(self.rl_total_depth.extent(), self.vl_rain_gauges.extent())
            self.update_total_depth_raster_layer(new_extent)        

    def initialize_vector_layer(self):
        """Initialize the QgsVectorLayer with appropriate fields for rain gauge data."""
        
        crs = QgsCoordinateReferenceSystem("EPSG:27700")  # Set to BNG (EPSG:27700)
        
        # Create the vector layer with the correct CRS
        self.vl_rain_gauges = QgsVectorLayer(
            "Point?crs=EPSG:27700",  # Specify the CRS here
            "Rain Gauges",
            "memory"
        )
        
        provider = self.vl_rain_gauges.dataProvider()
        
        # Add fields corresponding to rain gauge attributes
        provider.addAttributes([
            QgsField("gauge_name", QVariant.String),
            QgsField("total_depth", QVariant.Double)
        ])
        
        self.vl_rain_gauges.updateFields()
        
        # Ensure the layer is set to the correct CRS
        self.vl_rain_gauges.setCrs(crs)

        symbol = QgsMarkerSymbol.createSimple({'name': 'triangle', 'color': 'blue', 'outline_color': 'black', 'outline_width': '0.2', 'size': '3'})
        self.vl_rain_gauges.renderer().setSymbol(symbol)
   
        # Create a label for each point
        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = '"gauge_name" || \'\n\' || \'(\'  || "total_depth"  || \'mm)\''
        label_settings.isExpression = True
        label_settings.placement = Qgis.LabelPlacement.AroundPoint
        label_settings.enabled = True
        
        # Set text format
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", 10))
        text_format.setSize(10)
        text_format.setColor(QColor("black"))

        buffer_settings = QgsTextBufferSettings()
        buffer_settings.setEnabled(True)
        buffer_settings.setSize(1)
        buffer_settings.setColor(QColor("white"))

        text_format.setBuffer(buffer_settings)
                
        label_settings.setFormat(text_format)

        # Apply label settings
        label = QgsVectorLayerSimpleLabeling(label_settings)
        self.vl_rain_gauges.setLabelsEnabled(True)
        self.vl_rain_gauges.setLabeling(label)

    def addMappedRainGauge(self, rg: rainGauge):
        """Add a rain gauge to both the dictionary and the vector layer."""
        if rg is not None:
            if rg.gaugeName not in self.dictMappedRainGauges:
                # Add to dictionary
                self.dictMappedRainGauges[rg.gaugeName] = rg
                
                # Add to vector layer
                self._add_gauge_to_layer(rg)
    
    def _add_gauge_to_layer(self, rg: rainGauge):
        """Helper method to add a single rain gauge to the vector layer."""
        if self.vl_rain_gauges is None:
            self.initialize_vector_layer()
            
        provider = self.vl_rain_gauges.dataProvider()
        
        # Create a new feature
        feature = QgsFeature()
        
        # Set geometry from x and y coordinates
        point = QgsPointXY(rg.x, rg.y)
        feature.setGeometry(QgsGeometry.fromPointXY(point))
        
        # # Set attributes (adjust these based on your rainGauge class properties)
        # feature.setAttributes([
        #     rg.gaugeName,
        #     rg.rainUnits,
        #     rg.rgTimestep,
        #     rg.rainfallFileSpec
        # ])
        
        # Set attributes (adjust these based on your rainGauge class properties)
        if self.current_event is not None:
            stats = rg.statsBetweenDates(self.current_event.eventStart, self.current_event.eventEnd)
            totDepth = stats['totDepth']
        else:
            totDepth = rg.totalDepth

        feature.setAttributes([rg.gaugeName, totDepth])

        # Add the feature to the layer
        provider.addFeature(feature)
        self.vl_rain_gauges.updateExtents()
        # self.vl_rain_gauges.triggerRepaint()
        if self.rl_total_depth is not None:
            new_extent = self.get_maximum_of_extents(self.rl_total_depth.extent(), self.vl_rain_gauges.extent())
            self.update_total_depth_raster_layer(new_extent)

    def updateRainGaugeLocation(self, rgName: str, x: float, y: float):
        """Update the location of a rain gauge in both the dictionary and vector layer."""
        if rgName in self.dictMappedRainGauges:
            # Update in dictionary
            self.dictMappedRainGauges[rgName].x = x
            self.dictMappedRainGauges[rgName].y = y
            
            # Update in vector layer
            self._update_gauge_in_layer(rgName)

        else:
            print(f"Mapped rain gauge {rgName} not found.")

    def _update_gauge_in_layer(self, rgName: str):
        """Helper method to update a rain gauge in the vector layer."""
        if self.vl_rain_gauges is None:
            return
            
        # Find the feature with the given gauge name
        features = self.vl_rain_gauges.getFeatures(f"gauge_name = '{rgName}'")
        
        for feature in features:
            # Get gauge from dictionary
            rg = self.dictMappedRainGauges[rgName]
            
            # Update geometry
            point = QgsPointXY(rg.x, rg.y)
            
            # Update the feature's geometry
            self.vl_rain_gauges.dataProvider().changeGeometryValues({
                feature.id(): QgsGeometry.fromPointXY(point)
            })
                                    
        self.vl_rain_gauges.updateExtents()

        if self.rl_total_depth is not None:
            new_extent = self.get_maximum_of_extents(self.rl_total_depth.extent(), self.vl_rain_gauges.extent())
            self.update_total_depth_raster_layer(new_extent)        
        # self.vl_rain_gauges.triggerRepaint()

    def getMappedRainGauge(self, rgName: str) -> Optional[rainGauge]:
        """Get a rain gauge by name from the dictionary."""
        return self.dictMappedRainGauges.get(rgName)

    def removeMappedRainGauge(self, rgName: str):
        """Remove a rain gauge from both the dictionary and vector layer."""
        if rgName in self.dictMappedRainGauges:
            # Remove from dictionary
            del self.dictMappedRainGauges[rgName]
            
            # Remove from vector layer
            if self.vl_rain_gauges is not None:
                # Find and remove the feature with the given gauge name
                features = self.vl_rain_gauges.getFeatures(f"gauge_name = '{rgName}'")
                feature_ids = [feature.id() for feature in features]
                
                if feature_ids:
                    self.vl_rain_gauges.dataProvider().deleteFeatures(feature_ids)
                    self.vl_rain_gauges.updateExtents()
                    self.vl_rain_gauges.triggerRepaint()

            if self.rl_total_depth is not None:
                new_extent = self.get_maximum_of_extents(self.rl_total_depth.extent(), self.vl_rain_gauges.extent())
                self.update_total_depth_raster_layer(new_extent)

        else:
            print(f"Mapped rain gauge {rgName} not found.")

    def isMapped(self, rgName: str):
        """Check if a rain gauge is mapped."""
        return rgName in self.dictMappedRainGauges

    def locationByRainGaugeName(self, rgName: str) -> Optional[List[float]]:
        """Get the location of a rain gauge by name."""
        if rgName in self.dictMappedRainGauges:
            return [self.dictMappedRainGauges[rgName].x, self.dictMappedRainGauges[rgName].y]
        return None
        
    def syncVectorLayer(self):
        """Rebuild the vector layer from the dictionary data (useful after bulk operations)."""
        if self.vl_rain_gauges is None:
            self.initialize_vector_layer()
            
        # Clear existing features
        self.vl_rain_gauges.dataProvider().truncate()
        
        # Add all gauges from dictionary
        features = []
        for name, rg in self.dictMappedRainGauges.items():
            feature = QgsFeature()
            point = QgsPointXY(rg.x, rg.y)
            feature.setGeometry(QgsGeometry.fromPointXY(point))
            
            # feature.setAttributes([
            #     rg.gaugeName,
            #     rg.rainUnits,
            #     rg.rgTimestep,
            #     rg.rainfallFileSpec
            # ])

            if self.current_event is not None:
                stats = rg.statsBetweenDates(self.current_event.eventStart, self.current_event.eventEnd)
                totDepth = stats['totDepth']
            else:
                totDepth = rg.totalDepth

            feature.setAttributes([rg.gaugeName, totDepth])

            features.append(feature)
            
        # Add all features at once
        if features:
            self.vl_rain_gauges.dataProvider().addFeatures(features)
            self.vl_rain_gauges.updateExtents()
            self.vl_rain_gauges.triggerRepaint()
            
    def getRainGaugesInBoundingBox(self, xMin: float, yMin: float, xMax: float, yMax: float) -> List[str]:
        """Get names of rain gauges within a bounding box (spatial query)."""
        if self.vl_rain_gauges is None:
            return []
            
        # Create a bounding box geometry
        bbox = QgsRectangle(xMin, yMin, xMax, yMax)
        
        # Query features within the bounding box
        request = QgsFeatureRequest().setFilterRect(bbox)
        features = self.vl_rain_gauges.getFeatures(request)
        
        # Extract gauge names
        result = []
        for feature in features:
            gauge_name = feature["gauge_name"]
            if gauge_name:
                result.append(gauge_name)
                
        return result
        
    def getGaugesWithinDistance(self, x: float, y: float, distance: float) -> List[str]:
        """Get names of rain gauges within a specified distance of a point."""
        if self.vl_rain_gauges is None:
            return []
        
        center_point = QgsPointXY(x, y)
        center_geom = QgsGeometry.fromPointXY(center_point)
        
        # Get all gauges from the layer
        features = self.vl_rain_gauges.getFeatures()
        
        # Filter by distance
        result = []
        for feature in features:
            if feature.geometry().distance(center_geom) <= distance:
                gauge_name = feature["gauge_name"]
                if gauge_name:
                    result.append(gauge_name)
                    
        return result
    
    def idw_interpolation(self, x, y, z, xi, yi, power=2):
        """
        Performs IDW interpolation on scattered points.
        - x, y, z: Input point coordinates and values
        - xi, yi: Grid points for interpolation
        - power: Inverse distance weighting exponent
        """
        tree = cKDTree(np.c_[x, y])

        # Ensure we don't request more neighbors than available
        # max_k = min(6, len(x))  # Limit k to available data points
        max_k = len(x)  # Limit k to available data points        

        dist, idx = tree.query(np.c_[xi, yi], k=max_k)

        # Prevent division by zero
        dist = np.maximum(dist, 1e-10)

        # Compute inverse distance weights
        weights = 1 / (dist ** power)
        weights /= weights.sum(axis=1, keepdims=True)  # Normalize weights

        # Compute weighted sum
        zi = np.sum(weights * z[idx], axis=1)

        return zi

    def save_numpy_as_qgis_raster(self, array, x_min, y_max, pixel_size, output_path, crs_epsg=27700):

        rows, cols = array.shape
        x_max = x_min + cols * pixel_size
        y_min = y_max - rows * pixel_size

        # Create raster layer with given extent
        extent = QgsRectangle(x_min, y_min, x_max, y_max)
        crs = QgsCoordinateReferenceSystem(crs_epsg)

        # Create Raster File Writer
        writer = QgsRasterFileWriter(output_path)
        writer.setOutputFormat('GTiff')  # Save as GeoTIFF
        # writer.setDestinationCrs(crs)

        # Create Raster Data Provider
        provider = writer.createOneBandRaster(Qgis.DataType.Float32, cols, rows, extent, crs)

        # Convert NumPy array to QgsRasterBlock
        raster_block = QgsRasterBlock(Qgis.DataType.Float32, cols, rows)
        for row in range(rows):
            for col in range(cols):
                raster_block.setValue(row, col, float(array[row, col]))

        # Write block to raster provider
        provider.setEditable(True)
        provider.writeBlock(raster_block, 1, 0, 0)
        provider.setEditable(False)
        # provider.dataChanged()
        
        return output_path

    def update_total_depth_raster_layer(self, output_extent: QgsRectangle = None):

        x_coords, y_coords, values = [], [], []
        
        # Extract rainfall station points
        feature_count = 0
        for feature in self.vl_rain_gauges.getFeatures():
            geom = feature.geometry()
            # if not geom.isEmpty() and geom.isPoint():
            if not geom.isEmpty() and geom.wkbType() == QgsWkbTypes.Point:
                x_coords.append(geom.asPoint().x())
                y_coords.append(geom.asPoint().y())
                values.append(feature['total_depth'])
                feature_count += 1

        if feature_count > 1:
            # Define interpolation extent
            if output_extent is None:
                output_extent = self.vl_rain_gauges.extent()
                
            x_min, x_max = output_extent.xMinimum(), output_extent.xMaximum()
            y_min, y_max = output_extent.yMinimum(), output_extent.yMaximum()

            pixel_size = 50  # Define pixel size in CRS units (e.g., meters)
            
            # Compute number of rows and columns based on pixel size
            cols = int((x_max - x_min) / pixel_size)
            rows = int((y_max - y_min) / pixel_size)

            # # Generate mesh grid using pixel-based spacing
            xi, yi = np.meshgrid(
                np.linspace(x_min, x_max, cols),
                np.linspace(y_max, y_min, rows)
            )

            # Perform IDW interpolation
            zi = self.idw_interpolation(
                np.array(x_coords), np.array(y_coords), np.array(values),
                xi.ravel(), yi.ravel()
            ).reshape(xi.shape)

            # Save raster to a temporary file
            temp_raster = tempfile.NamedTemporaryFile(suffix=".tif", delete=False).name
            self.save_numpy_as_qgis_raster(zi, x_min, y_max, pixel_size, temp_raster)
   
            if self.rl_total_depth:
                self.rl_total_depth.setDataSource(temp_raster, "IDW_TotalDepth", "gdal")
            else:
                self.rl_total_depth = QgsRasterLayer(temp_raster, "IDW_TotalDepth", "gdal")

            self.style_total_depth_raster_layer()

        # # Apply styling
        # stats = raster_layer.dataProvider().bandStatistics(1)  # Get min/max values
        # min_val, max_val = stats.minimumValue, stats.maximumValue

        # color_ramp = QgsGradientColorRamp(QColor(255, 0, 0), QColor(0, 128, 0))  # RdYlGn-like ramp
        # shader = QgsColorRampShader(colorRamp=color_ramp)
        # shader.setColorRampType(QgsColorRampShader.Interpolated)
        # # shader.setColorRamp(color_ramp)
        # shader.setClassificationMode(QgsColorRampShader.Continuous)
        # shader.setMinimumValue(min_val)
        # shader.setMaximumValue(max_val)

        # raster_shader = QgsRasterShader()
        # raster_shader.setRasterShaderFunction(shader)

        # renderer = QgsSingleBandPseudoColorRenderer(raster_layer.dataProvider(), 1, raster_shader)
        # raster_layer.setRenderer(renderer)
        # # raster_layer.triggerRepaint()

        # return raster_layer

    def style_total_depth_raster_layer(self):       
        
        # Get raster statistics
        provider = self.rl_total_depth.dataProvider()
        stats = provider.bandStatistics(1)  # Assuming first band

        if stats.minimumValue is None or stats.maximumValue is None:
            print("Unable to retrieve raster statistics")
            return

        min_val = stats.minimumValue
        max_val = stats.maximumValue
        value_range = max_val - min_val

        # Determine interval based on value range
        if value_range < 1:
            interval = 0.1
        elif value_range < 2:
            interval = 0.2
        elif value_range < 5:
            interval = 0.5
        elif value_range < 10:
            interval = 1
        elif value_range < 20:
            interval = 2
        elif value_range < 50:
            interval = 5
        else:
            interval = 10

        # Round min and max values to nearest interval
        rounded_min = math.ceil(min_val / interval) * interval
        rounded_max = math.floor(max_val / interval) * interval

        # Generate classification values including min and max
        classification_values = []
        value = rounded_min

        while value <= rounded_max:
            classification_values.append(value)
            value += interval

        classification_values.append(max_val)

        fcn = QgsColorRampShader()
        fcn.setColorRampType(QgsColorRampShader.Discrete)
        
        color_list = []
        i_count = 0
        for value in classification_values:
            # Interpolate color from green (low) to red (high)
            ratio = (value - min_val) / value_range if value_range > 0 else 0
            color = QColor.fromHsvF((1 - ratio) * 0.33, 1.0, 1.0)  # 0.33 (green) to 0.0 (red)
            # Create a labeled color ramp item
            if i_count == 0:
                label = f"<={value:.1f}"  # Format the label as an integer string
            elif i_count == len(classification_values) - 1:
                label = f">{prev_val:.1f}"  # Format the label as an integer string
            else:
                label = f"{prev_val:.1f} - {value:.1f}"  # Format the label as an integer string
                
            color_list.append(QgsColorRampShader.ColorRampItem(value, color, label))
            i_count += 1
            prev_val = value

        fcn.setColorRampItemList(color_list)
        shader = QgsRasterShader()
        shader.setRasterShaderFunction(fcn)

        renderer = QgsSingleBandPseudoColorRenderer(self.rl_total_depth.dataProvider(), 1, shader)
        self.rl_total_depth.setRenderer(renderer)
        self.rl_total_depth.triggerRepaint()
        # raster_layer.triggerRepaint()

    def get_maximum_of_extents(self, extent1: QgsRectangle, extent2: QgsRectangle) -> QgsRectangle:
        min_x = min(extent1.xMinimum(), extent2.xMinimum())
        min_y = min(extent1.yMinimum(), extent2.yMinimum())
        max_x = max(extent1.xMaximum(), extent2.xMaximum())
        max_y = max(extent1.yMaximum(), extent2.yMaximum())

        return QgsRectangle(min_x, min_y, max_x, max_y)
    
    def create_virtual_raingauge(self, x: float, y: float, gaugeName: str) -> rainGauge:
        """
        Creates a virtual rain gauge at the specified location using IDW interpolation
        on the existing rain gauge data, using vectorized NumPy operations.
        """
        if not self.dictMappedRainGauges:
            raise ValueError("No mapped rain gauges available for interpolation.")

        # Extract coordinates and data
        gauges = list(self.dictMappedRainGauges.values())
        x_coords = np.array([rg.x for rg in gauges])
        y_coords = np.array([rg.y for rg in gauges])

        # Ensure all rain gauges have time series data
        if not all(rg.dateRange and rg.rainfallDataRange for rg in gauges):
            raise ValueError("Some rain gauges lack time series data.")

        # Determine common available date range across all rain gauges
        start_dates = [rg.dateRange[0] for rg in gauges]
        end_dates = [rg.dateRange[-1] for rg in gauges]

        common_start = max(start_dates)  # Latest start date
        common_end = min(end_dates)      # Earliest end date

        # Generate the common date range
        date_range = [date for date in gauges[0].dateRange if common_start <= date <= common_end]

        # Convert rainfall data into a NumPy matrix, only keeping data within the common range
        rainfall_matrix = np.array([
            [rg.rainfallDataRange[i] for i, date in enumerate(rg.dateRange) if common_start <= date <= common_end]
            for rg in gauges
        ])        

        # Build KDTree for nearest neighbors
        tree = cKDTree(np.c_[x_coords, y_coords])

        # Find nearest neighbors
        # max_k = min(6, len(x_coords))  # Limit to available data points
        max_k = len(x_coords)  # Limit to available data points
        dist, idx = tree.query([[x, y]], k=max_k)

        # Prevent division by zero
        dist = np.maximum(dist, 1e-10)

        # Compute IDW weights (shape: [max_k])
        power = 2
        weights = 1 / (dist ** power)
        weights /= np.sum(weights)  # Normalize weights

        # **Vectorized interpolation**: weighted sum of nearest rain gauge rainfall data
        weighted_rainfall_series = np.dot(weights[0], rainfall_matrix[idx[0]])

        # Create the virtual rain gauge
        virtual_gauge = rainGauge()
        virtual_gauge.gaugeName = gaugeName
        virtual_gauge.x = x
        virtual_gauge.y = y
        virtual_gauge.dateRange = date_range
        virtual_gauge.rainfallDataRange = weighted_rainfall_series.tolist()
        virtual_gauge.rgTimestep = 2
        # virtual_gauge.totalDepth = weighted_rainfall_series.sum()
        virtual_gauge.maxIntensity = (max(virtual_gauge.rainfallDataRange))
        virtual_gauge.totalDepth = round((sum(virtual_gauge.rainfallDataRange))/(60/virtual_gauge.rgTimestep), 1)
        duration_hrs = (common_end - common_start).total_seconds() / 3600
        virtual_gauge.returnPeriod = round(10/(1.25*duration_hrs*(((0.0394*virtual_gauge.totalDepth)+0.1)**-3.55)), 2)        

        return virtual_gauge
