import os
# from datetime import datetime
from typing import List, Optional, Dict
import time
import calendar
from datetime import datetime, timedelta
from statistics import mean
import numpy as np
# import pandas as pd
import sqlite3

from PyQt5 import QtGui
from PyQt5.QtWidgets import (QMessageBox)

from flowbot_schematic import rgGraphicsItem, fmGraphicsItem
from flowbot_verification import icmTraceLocation
from flowbot_helper import serialize_list, deserialize_list, serialize_item, deserialize_item, parse_file, parse_date
from flowbot_database import Tables
# from contextlib import closing


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

    def from_database_row(self, row):
        self.fdvFileSpec = row[0]
        self.monitorName = row[1]
        self.flowUnits = row[2]
        self.depthUnits = row[3]
        self.velocityUnits = row[4]
        self.rainGaugeName = row[5]
        self.fmTimestep = row[6]
        self.dateRange = deserialize_list(row[7])
        self.flowDataRange = deserialize_list(row[8])
        self.depthDataRange = deserialize_list(row[9])
        self.velocityDataRange = deserialize_list(row[10])
        self.minFlow = row[11]
        self.maxFlow = row[12]
        self.totalVolume = row[13]
        self.minDepth = row[14]
        self.maxDepth = row[15]
        self.minVelocity = row[16]
        self.maxVelocity = row[17]
        self.hasModelData = bool(row[18])
        self.modelDataPipeRef = row[19]
        self.modelDataRG = row[20]
        self.modelDataPipeLength = row[21]
        self.modelDataPipeShape = row[22]
        self.modelDataPipeDia = row[23]
        self.modelDataPipeHeight = row[24]
        self.modelDataPipeRoughness = row[25]
        self.modelDataPipeUSInvert = row[26]
        self.modelDataPipeDSInvert = row[27]
        self.modelDataPipeSystemType = row[28]
        # self._schematicGraphicItem = deserialize_item(row[29])

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
            c.execute(f"SELECT * FROM {Tables.FLOW_MONIOTOR}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.FLOW_MONIOTOR}' does not exist.")
            return  # Return without attempting to fetch rows

        rows = c.fetchall()
        for row in rows:
            monitor = flowMonitor()
            monitor.from_database_row(row)
            self.dictFlowMonitors[monitor.monitorName] = monitor

    def write_to_database(self, conn: sqlite3.Connection) -> bool:
        result = False
        try:
            # with closing(conn.cursor()) as c:
            conn.execute(f'''DROP TABLE IF EXISTS {Tables.FLOW_MONIOTOR}''')
            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.FLOW_MONIOTOR} (
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
                            modelDataPipeSystemType TEXT
                        )''')
            for monitor in self.dictFlowMonitors.values():
                conn.execute(f'''INSERT OR REPLACE INTO {Tables.FLOW_MONIOTOR} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
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
                              monitor.modelDataPipeUSInvert, monitor.modelDataPipeDSInvert, monitor.modelDataPipeSystemType))
            conn.commit()
            result = True

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

    # def addFlowMonitor(self, fileSpec: str):

    #     if not self.alreadyOpen(fileSpec):

    #         start_old = time.perf_counter()
    #         objFM = self.getFlowMonitorFromFDVFile(fileSpec)
    #         end_old = time.perf_counter()

    #         start_new = time.perf_counter()
    #         objFM_alt = self.getFlowMonitorFromFDVFile_NEW(fileSpec)
    #         end_new = time.perf_counter()

    #         time_old = end_old - start_old
    #         time_new = end_new - start_new

    #         print(f"Old method time: {time_old:.6f} seconds")
    #         print(f"New method time: {time_new:.6f} seconds")
    #         print(f"Time difference (new - old): {time_new - time_old:.6f} seconds")

    #     if objFM is not None:
    #         self.dictFlowMonitors[objFM.monitorName] = objFM

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
                # myFM.dateRange = []

                # myFM.flowDataRange = [float(unit["FLOW"]) for unit in all_units]
                # myFM.depthDataRange = [float(unit["DEPTH"]) for unit in all_units]
                # myFM.velocityDataRange = [float(unit["VELOCITY"]) for unit in all_units]

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
                        myFM.flowDataRange.append(float(unit["FLOW"]))
                        myFM.depthDataRange.append(float(unit["DEPTH"]))
                        myFM.velocityDataRange.append(float(unit["VELOCITY"]))

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


# class qgisFlowMonitors(flowMonitors):

#     vlFlowMonitors = None

#     def __init__(self, myCrs=QgsCoordinateReferenceSystem("EPSG:27700")):
#         super().__init__()

#         self.vlFlowMonitors = QgsVectorLayer(
#             "Point?crs=" + myCrs.authid(), "flowbot Flow Monitors", "memory")
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

class mappedFlowMonitor(flowMonitor):
    def __init__(self, mFMName: str, latitude: float = 0.0, longitude: float = 0.0):
        super().__init__()
        self.monitorName = mFMName
        self.latitude: float = latitude
        self.longitude: float = longitude


class mappedFlowMonitors():
    def __init__(self):
        self.dictMappedFlowMonitors: Dict[str, mappedFlowMonitor] = {}

    def addMappedFlowMonitor(self, monitor: mappedFlowMonitor):
        if monitor is not None:
            if monitor.monitorName not in self.dictMappedFlowMonitors:
                self.dictMappedFlowMonitors[monitor.monitorName] = monitor

    def updateFlowMonitorLocation(self, fmName: str, latitude: float, longitude: float):
        if fmName in self.dictMappedFlowMonitors:
            self.dictMappedFlowMonitors[fmName].latitude = latitude
            self.dictMappedFlowMonitors[fmName].longitude = longitude
        else:
            print("Flow monitor {} not found.".format(fmName))

    def getMappedFlowMonitor(self, nameFM: str) -> Optional[mappedFlowMonitor]:
        return self.dictMappedFlowMonitors.get(nameFM)

    def removeMappedFlowMonitor(self, fmName: str):
        if fmName in self.dictMappedFlowMonitors:
            del self.dictMappedFlowMonitors[fmName]
        else:
            print("Mapped flow monitor {} not found.".format(fmName))

    def isMapped(self, fmName: str):
        return fmName in self.dictMappedFlowMonitors

    def locationByFMName(self, fmName: str) -> Optional[List[float]]:
        if fmName in self.dictMappedFlowMonitors:
            return [self.dictMappedFlowMonitors[fmName].latitude, self.dictMappedFlowMonitors[fmName].longitude]


class rainGauge():

    # rDataframe: pd.DataFrame
    # gaugeName: str = ''
    # rFileSpec: str = ''
    # dateRange = []
    # rainfallDataRange = []
    # rgTimestep: float = 0.0
    # minIntensity: float = 0
    # maxIntensity: float = 0
    # totalDepth: float = 0
    # returnPeriod: float = 0
    # _schematicGraphicItem: Optional[rgGraphicsItem] = None

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

    def from_database_row(self, row):
        self.gaugeName = row[0]
        self.rFileSpec = row[1]
        self.dateRange = deserialize_list(row[2])
        self.rainfallDataRange = deserialize_list(row[3])
        self.rgTimestep = row[4]
        self.minIntensity = row[5]
        self.maxIntensity = row[6]
        self.totalDepth = row[7]
        self.returnPeriod = row[8]

    # def statsBetweenDates(self, startDate: datetime = dt.strptime('2172-05-12', '%Y-%m-%d'),
        # endDate: datetime = dt.strptime('1972-05-12', '%Y-%m-%d')):
    def statsBetweenDates(self, startDate: Optional[datetime], endDate: Optional[datetime]):
        if startDate is None:
            startDate = datetime.strptime('2172-05-12', '%Y-%m-%d')
        if endDate is None:
            endDate = datetime.strptime('1972-05-12', '%Y-%m-%d')

        minIntensity = 0
        maxIntensity = 0
        totalDepth = 0
        returnPeriod = 0

        min_row, max_row = self.getDataRangeFromDates(startDate, endDate)

        maxIntensity = max(self.rainfallDataRange[min_row:max_row])
        minIntensity = min(self.rainfallDataRange[min_row:max_row])
        totalDepth = round(
            (sum(self.rainfallDataRange[min_row:max_row]))/(60/self.rgTimestep), 1)

        unix_rounded_xmin_python_datetime = calendar.timegm(
            startDate.timetuple())
        unix_rounded_xmax_python_datetime = calendar.timegm(
            endDate.timetuple())
        # unix_diff_days = (((unix_rounded_xmax_python_datetime -
        #                   unix_rounded_xmin_python_datetime)/60)/60)/24
        unix_diff_mins = ((unix_rounded_xmax_python_datetime -
                          unix_rounded_xmin_python_datetime)/60)
        duration_hrs = unix_diff_mins / 60
        returnPeriod = round(
            10/(1.25*duration_hrs*(((0.0394*totalDepth)+0.1)**-3.55)), 2)

        # returnPeriod = round(
        #     (0.00494*(totalDepth+2.54)**3.55)/unix_diff_mins, 2)

        return {'minInt': minIntensity, 'maxInt': maxIntensity, 'totDepth': totalDepth, 'retPer': returnPeriod}

    def getDataRangeFromDates(self, startDate: Optional[datetime], endDate: Optional[datetime]):
        if startDate is None:
            startDate = datetime.strptime('2172-05-12', '%Y-%m-%d')
        if endDate is None:
            endDate = datetime.strptime('1972-05-12', '%Y-%m-%d')

        start_time = calendar.timegm(self.dateRange[0].timetuple())
        end_time = calendar.timegm(self.dateRange[-1].timetuple())
        target_start_time = calendar.timegm(startDate.timetuple())
        target_end_time = calendar.timegm(endDate.timetuple())

        if (start_time < target_start_time) and (target_start_time < end_time):
            unix_rounded_xmin_python_datetime = calendar.timegm(
                self.dateRange[0].timetuple())
            unix_rounded_xmax_python_datetime = calendar.timegm(
                startDate.timetuple())
            unix_diff_mins = (
                (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)
            min_row = int(unix_diff_mins / self.rgTimestep)
        else:
            min_row = 0

        if (start_time < target_end_time) and (target_end_time < end_time):
            unix_rounded_xmin_python_datetime = calendar.timegm(
                self.dateRange[0].timetuple())
            unix_rounded_xmax_python_datetime = calendar.timegm(
                endDate.timetuple())
            unix_diff_mins = (
                (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)
            max_row = int(unix_diff_mins / self.rgTimestep)
        else:
            max_row = len(self.rainfallDataRange)

        return (min_row, max_row)

    def eventStatsBetweenDates(self, startDate: datetime, endDate: datetime):
        """Calculates basic rainfalls stats for the gauge based on the given date range

            Parameters
            ----------
            startDate: datetime
                The start date for the date range
            endDate: datetime
                The end date for the date range

            Returns
            -------
            Tuple(float, float, float, float)
                Duration: time in minutes for which there were non-zero rainfall intensity values within the specified date range
                Total Depth: total rainfall depth in mm within the specified date range
                Peak Intensity: Maximum rainfall intensity in mm/hr within the specified date range
                Period Greater Than 6mm/hr: time in minutes for which there were rainfall intensity values
                greater than or equal to 6mm/hr within the specified date range
            """

        rgName: str = ''
        startTime: str = ''
        duration: float = 0
        totalDepth: float = 0
        peakIntensity: float = 0
        periodGreaterThan6mmhr: float = 0

        min_row, max_row = self.getDataRangeFromDates(startDate, endDate)

        rgName = self.gaugeName
        index_first_match = None
        for index, item in enumerate(self.rainfallDataRange[min_row:max_row]):
            if item != 0:
                index_first_match = index
                break
        if index_first_match is not None:
            startTime = datetime.strftime(
                self.dateRange[min_row:max_row][index_first_match], "%H:%M")
        duration = self.rgTimestep * \
            sum(i > 0 for i in self.rainfallDataRange[min_row:max_row])
        totalDepth = round(
            (sum(self.rainfallDataRange[min_row:max_row]))/(60/self.rgTimestep), 1)
        peakIntensity = max(self.rainfallDataRange[min_row:max_row])
        periodGreaterThan6mmhr = self.rgTimestep * \
            sum(i > 6 for i in self.rainfallDataRange[min_row:max_row])

        return (rgName, startTime, duration, totalDepth, peakIntensity, periodGreaterThan6mmhr)


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
        for row in rows:
            gauge = rainGauge()
            gauge.from_database_row(row)
            self.dictRainGauges[gauge.gaugeName] = gauge

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
                            returnPeriod REAL
                        )''')
            for gauge in self.dictRainGauges.values():
                conn.execute(f'''INSERT OR REPLACE INTO {Tables.RAIN_GAUGE} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (gauge.gaugeName, gauge.rFileSpec, serialize_list(gauge.dateRange),
                              serialize_list(
                                  gauge.rainfallDataRange), gauge.rgTimestep, gauge.minIntensity,
                              gauge.maxIntensity, gauge.totalDepth, gauge.returnPeriod))
            conn.commit()
            result = True

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

    def addRainGauge(self, fileSpec: str):

        try:
            if not self.alreadyOpen(fileSpec):

                start_old = time.perf_counter()
                objRG = self.getRainGaugeFromRFile(fileSpec)
                end_old = time.perf_counter()

                start_new = time.perf_counter()
                objRG_alt = self.getRainGaugeFromRFile_NEW(fileSpec)
                end_new = time.perf_counter()

                time_old = end_old - start_old
                time_new = end_new - start_new

                print(f"Old method time: {time_old:.6f} seconds")
                print(f"New method time: {time_new:.6f} seconds")
                print(f"Time difference (new - old): {time_new - time_old:.6f} seconds")

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

    def getRainGaugeFromRFile(self, fileSpec: str):

        with open(fileSpec, 'r', encoding="utf-8") as org_data:

            myRG = rainGauge()
            myRG.rFileSpec = fileSpec

            dynamicDateRange = []

            lines = []
            countCEND = 0

            myRG.rainfallDataRange = []
            myRG.dateRange = []
            rainDataAppend = False

            for line in org_data:

                lines.append(line)

            for i in range(len(lines)):

                if (lines[i])[:13] == "**IDENTIFIER:":

                    rawRGName = lines[i]

                    strippedRawRGName = rawRGName.replace(" ", "").strip()

                    myRG.gaugeName = strippedRawRGName[15:36]
                    if len(myRG.gaugeName) == 0:
                        myRG.gaugeName = os.path.splitext(
                            os.path.basename(fileSpec))[0]
                    if not os.path.basename(fileSpec).split('.')[0] == myRG.gaugeName:
                        QMessageBox.warning(None, 'Identifier Problem',
                                            'Internal Identifier: ' + myRG.gaugeName +
                                            ' does not match the file name.\n\nIt has not been added to the available gauges',
                                            QMessageBox.Ok)
                        return None

                if (lines[i])[:5] == "*CEND":

                    countCEND += 1

                    rawRainDates = (lines[i-1])
                    strippedRawRainDates = rawRainDates.replace(" ", "")
                    myRG.rgTimestep = float(strippedRawRainDates[-2:])
                    # ____________________________________________________________________________________________________________________________________
                    # This section is to acount for when there is a break in the data, and it is restarted, acounting for and missing time with
                    #  Zeros
                    if len(strippedRawRainDates) == 22:
                        strippedRawRainDatesStartDate = strippedRawRainDates[0:10]
                        strippedRainStartDate = strippedRawRainDatesStartDate[4:6]+'/'+strippedRawRainDatesStartDate[2:4]+'/' + '20' + \
                            strippedRawRainDatesStartDate[0:2]+' ' + \
                            strippedRawRainDatesStartDate[6:8] + \
                            ":"+strippedRawRainDatesStartDate[8:10]
                        d1Working = datetime.strptime(
                            strippedRainStartDate, "%d/%m/%Y %H:%M")

                    if len(strippedRawRainDates) == 26:
                        strippedRawRainDatesStartDate = strippedRawRainDates[0:12]
                        strippedRainStartDate = strippedRawRainDatesStartDate[6:8]+'/'+strippedRawRainDatesStartDate[4:6]+'/' + '20' + \
                            strippedRawRainDatesStartDate[2:4]+' '+strippedRawRainDatesStartDate[8:10] + \
                            ":"+strippedRawRainDatesStartDate[10:12]
                        d1Working = datetime.strptime(
                            strippedRainStartDate, "%d/%m/%Y %H:%M")

                    if countCEND == 1:

                        dynamicDateRange.append(d1Working)
                        d1 = d1Working

                    if countCEND > 1:

                        # the d1 working is the start of the current, dynamic is the generated date range
                        if d1Working > (dynamicDateRange[-1]):

                            gapDiff = (d1Working - (dynamicDateRange[-1]))

                            rowsToAdd = (
                                gapDiff/timedelta(minutes=myRG.rgTimestep))

                            z = 0
                            # Append ZEROS to list
                            while z < rowsToAdd:

                                myRG.rainfallDataRange.append(0)

                                # dynamicDateRange.append(dynamicDateRange[-1] + timedelta(minutes=myRG.rgTimestep))########

                                z += 1

                        elif (d1Working - timedelta(minutes=myRG.rgTimestep)) == d2:

                            gapDiff = (
                                (d1Working - timedelta(minutes=myRG.rgTimestep)) - d2)

                    if len(strippedRawRainDates) == 22:
                        strippedRawRainDatesEndDate = strippedRawRainDates[10:20]
                        strippedRainEndDate = strippedRawRainDatesEndDate[4:6]+'/'+strippedRawRainDatesEndDate[2:4]+'/'+'20' + \
                            strippedRawRainDatesEndDate[0:2]+' ' + \
                            strippedRawRainDatesEndDate[6:8] + \
                            ":"+strippedRawRainDatesEndDate[8:10]
                        d2 = datetime.strptime(
                            strippedRainEndDate, "%d/%m/%Y %H:%M")

                    elif len(strippedRawRainDates) == 26:
                        strippedRawRainDatesEndDate = strippedRawRainDates[12:24]
                        strippedRainEndDate = strippedRawRainDatesEndDate[6:8]+'/'+strippedRawRainDatesEndDate[4:6]+'/'+'20' + \
                            strippedRawRainDatesEndDate[2:4]+' '+strippedRawRainDatesEndDate[8:10] + \
                            ":"+strippedRawRainDatesEndDate[10:12]
                        d2 = datetime.strptime(
                            strippedRainEndDate, "%d/%m/%Y %H:%M")

                    startRow = i+1
                    rainDataAppend = True

                if (lines[i])[:4] == "*END" or (lines[i])[:2] == "*$":

                    # end_row = i-1
                    rainDataAppend = False

                if rainDataAppend is True and (lines[i])[3:6] != "" and i >= startRow:

                    if (lines[i])[9:15] != '':
                        myRG.rainfallDataRange.append(
                            float((lines[i])[9:15]))  # 1

                    if (lines[i])[24:30] != '':
                        myRG.rainfallDataRange.append(
                            float((lines[i])[24:30]))  # 2

                    if (lines[i])[39:45] != '':
                        myRG.rainfallDataRange.append(
                            float((lines[i])[39:45]))  # 3

                    if (lines[i])[54:60] != '':
                        myRG.rainfallDataRange.append(
                            float((lines[i])[54:60]))  # 4

                    if (lines[i])[69:75] != '':
                        myRG.rainfallDataRange.append(
                            float((lines[i])[69:75]))  # 5

            # __________________________
            # RG date range extract

            delta = d2 - d1

            for w in range(len(myRG.rainfallDataRange)):

                myRG.dateRange.append(
                    d1 + timedelta(minutes=w * myRG.rgTimestep))

            rainDateRangeStart = myRG.dateRange[0]
            rainDateRangeEnd = myRG.dateRange[len(myRG.dateRange)-1]

            myRG.maxIntensity = (max(myRG.rainfallDataRange))
            myRG.totalDepth = round(
                (sum(myRG.rainfallDataRange))/(60/myRG.rgTimestep), 1)

            unix_rounded_xmin_python_datetime = calendar.timegm(
                rainDateRangeStart.timetuple())
            unix_rounded_xmax_python_datetime = calendar.timegm(
                rainDateRangeEnd.timetuple())
            unix_diff_days = (
                ((unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)/60)/24
            unix_diff_mins = (
                (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)

            if unix_diff_mins > 0:
                # myRG.returnPeriod = round(
                #     (0.00494*(myRG.totalDepth+2.54)**3.55)/unix_diff_mins, 2)
                duration_hrs = unix_diff_mins / 60
                myRG.returnPeriod = round(
                    10/(1.25*duration_hrs*(((0.0394*myRG.totalDepth)+0.1)**-3.55)), 2)

            rainZipList = []
            rainZipListDates = []

            for i in range(len(myRG.dateRange)):
                rainZipListDates.append(
                    myRG.dateRange[i].strftime("%d/%m/%Y %H:%M"))

            # This combines the rainfall date range an rainfall data into a list of 2 columns to be convert to dataframe later
            rainZipList = list(zip(rainZipListDates, myRG.rainfallDataRange))

            # myRG.rDataframe = pd.DataFrame(
            #     rainZipList, columns=["rain_date", "rainfall"])

            return myRG

    def getRainGaugeFromRFile_NEW(self, fileSpec: str):

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
            # import numpy as np

            myRG.dateRange = np.arange(start_dt, end_dt + interval, interval).tolist()
            # myRG.dateRange = []
            # current_dt = start_dt
            # while current_dt <= end_dt:
            #     myRG.dateRange.append(current_dt)
            #     current_dt += interval

            no_of_records = int(duration_mins / interval_minutes) + 1
            i_record = 0

            myRG.rainfallDataRange = []
            for unit in all_units:
                i_record += 1
                if i_record <= no_of_records:
                    myRG.rainfallDataRange.append(float(unit["INTENSITY"]))

            # myRG.rainfallDataRange = [float(unit["INTENSITY"]) for unit in all_units]

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
