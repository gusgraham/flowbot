from typing import Dict, Optional
from datetime import datetime
import pandas as pd
import sqlite3
import pickle
from flowbot_database import Tables
from flowbot_helper import resource_path
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHBoxLayout)
from PyQt5.QtCore import Qt
from flowbot_logging import get_logger
logger = get_logger('flowbot_logger')

class fwqMonitor(object):

    def __init__(self):
        self.monitor_id: str = ''
        self.csv_filespec: str = ''
        self.data_start: datetime = datetime.strptime('2172-05-12', '%Y-%m-%d')
        self.data_end: datetime = datetime.strptime('2172-05-12', '%Y-%m-%d')
        self.data_interval: int = 0
        self.data_cond: Optional[pd.DataFrame] = None
        self.data_do: Optional[pd.DataFrame] = None
        self.data_do_sat: Optional[pd.DataFrame] = None
        self.data_nh4: Optional[pd.DataFrame] = None
        self.data_ph: Optional[pd.DataFrame] = None
        self.data_temp: Optional[pd.DataFrame] = None

    def from_database_row(self, row):
        self.monitor_id = row[0]
        self.csv_filespec = row[1]
        self.data_start = datetime.fromisoformat(row[2])
        self.data_end = datetime.fromisoformat(row[3])
        self.data_interval = row[4]
        if row[5] is not None:
            self.data_cond = pickle.loads(row[5])
        if row[6] is not None:
            self.data_do = pickle.loads(row[6])
        if row[7] is not None:
            self.data_do_sat = pickle.loads(row[7])
        if row[8] is not None:
            self.data_nh4 = pickle.loads(row[8])
        if row[9] is not None:
            self.data_ph = pickle.loads(row[9])
        if row[10] is not None:
            self.data_temp = pickle.loads(row[10])

    @staticmethod
    def from_file_with_mapping(file_path: str, mapping: dict):
        df_id = pd.read_csv(file_path, nrows=1, header=None)
        monitor_id = df_id.iloc[0, 0]
        df = pd.read_csv(file_path, skiprows=[0, 2], parse_dates=[
                         'DateTime'], date_format='%d/%m/%Y %H:%M:%S')

        monitor = fwqMonitor()
        monitor.monitor_id = monitor_id
        monitor.csv_filespec = file_path
        monitor.data_start = df['DateTime'].min()
        monitor.data_end = df['DateTime'].max()

        # Apply selected mappings to the DataFrame columns
        monitor.data_cond = df[['DateTime', mapping['COND']]
                               ].copy() if mapping['COND'] else None
        monitor.data_do = df[['DateTime', mapping['DO']]
                             ].copy() if mapping['DO'] else None
        monitor.data_do_sat = df[['DateTime', mapping['DO_SAT']]].copy(
        ) if mapping['DO_SAT'] else None
        monitor.data_nh4 = df[['DateTime', mapping['NH4']]
                              ].copy() if mapping['NH4'] else None
        monitor.data_ph = df[['DateTime', mapping['PH']]
                             ].copy() if mapping['PH'] else None
        monitor.data_temp = df[['DateTime', mapping['TEMP']]
                               ].copy() if mapping['TEMP'] else None

        return monitor

    # @staticmethod
    # def from_file_with_mapping(file_path: str):
    #     # Step 1: Load CSV and extract field names
    #     df_id = pd.read_csv(file_path, nrows=1, header=None)
    #     monitor_id = df_id.iloc[0, 0]
    #     df = pd.read_csv(file_path, skiprows=[0, 2], parse_dates=[
    #                      'DateTime'], date_format='%d/%m/%Y %H:%M:%S')
    #     fields = df.columns.tolist()

    #     # Step 2: Automatically map fields where possible
    #     mapping = fwqMonitor.auto_map_fields(fields)

    #     # Step 3: Open Dialog for user to adjust mappings
    #     dialog = MappingDialog(fields, mapping)
    #     if dialog.exec_():
    #         mapping = dialog.get_mapping()

    #     # Step 4: Use the selected mappings to create the monitor object
    #     monitor = fwqMonitor()
    #     monitor.monitor_id = monitor_id
    #     monitor.csv_filespec = file_path
    #     monitor.data_start = df['DateTime'].min()
    #     monitor.data_end = df['DateTime'].max()

    #     # Apply selected mappings to the DataFrame columns
    #     monitor.data_cond = df[['DateTime', mapping['COND']]].copy()
    #     monitor.data_do = df[['DateTime', mapping['DO']]].copy()
    #     monitor.data_do_sat = df[['DateTime', mapping['DO_SAT']]].copy()
    #     monitor.data_nh4 = df[['DateTime', mapping['NH4']]].copy()
    #     monitor.data_ph = df[['DateTime', mapping['PH']]].copy()
    #     monitor.data_temp = df[['DateTime', mapping['TEMP']]].copy()

    #     return monitor

    @staticmethod
    def auto_map_fields(fields):
        # Auto-mapping based on keyword matching
        mapping = {
            'COND': None,
            'DO': None,
            'DO_SAT': None,
            'NH4': None,
            'PH': None,
            'TEMP': None
        }
        keywords = {
            'COND': 'COND',
            'DO': 'DO',
            'DO_SAT': 'DO_SAT',
            'NH4': 'NH4',
            'PH': 'PH',
            'TEMP': 'TEMP'
        }

        # Auto-map by checking for keyword presence in field names
        for key, keyword in keywords.items():
            for field in fields:
                if keyword.lower() in field.lower():
                    mapping[key] = field
                    break

        return mapping


class fwqMonitors:
    def __init__(self):
        # Dictionary to hold fwqMonitor objects, keyed by monitor ID
        self.dictfwqMonitors: Dict[str, fwqMonitor] = {}

    def add_monitor(self, monitor: fwqMonitor):
        """Add a new fwqMonitor to the dictionary."""
        self.dictfwqMonitors[monitor.monitor_id] = monitor

    def add_monitor_from_file(self, file_path: str, mapping: dict):
        """Add a new fwqMonitor from a CSV file."""
        monitor = fwqMonitor.from_file_with_mapping(file_path, mapping)
        self.add_monitor(monitor)

    def remove_monitor(self, monitor_id: str):
        """Remove an fwqMonitor from the dictionary by its monitor_id."""
        if monitor_id in self.dictfwqMonitors:
            del self.dictfwqMonitors[monitor_id]
        else:
            print(f"Monitor with ID {monitor_id} does not exist.")

    def get_monitor(self, monitor_id: str) -> Optional[fwqMonitor]:
        """Retrieve an fwqMonitor by its monitor_id."""
        return self.dictfwqMonitors.get(monitor_id, None)

    def list_monitors(self):
        """List all monitor IDs currently in the dictionary."""
        return list(self.dictfwqMonitors.keys())

    def alreadyOpen(self, fileSpec: str):

        for wq in self.dictfwqMonitors.items():
            if wq[1].csv_filespec == fileSpec:
                reply = QMessageBox.question(None, 'WQ CSV file opened already!',
                                             wq[1].monitor_id +
                                             ' was added with that CSV file.\n\nDo you want to replace it?',
                                             QMessageBox.Yes | QMessageBox.No,
                                             QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.dictfwqMonitors.pop(wq[1].monitor_id)
                    return False
                else:
                    return True

        return False

    def read_from_database(self, conn: sqlite3.Connection):
        c = conn.cursor()
        try:
            c.execute(f"SELECT * FROM {Tables.WQ_MONITOR}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.WQ_MONITOR}' does not exist.")
            return  # Return without attempting to fetch rows

        rows = c.fetchall()
        for row in rows:
            monitor = fwqMonitor()
            monitor.from_database_row(row)
            self.dictfwqMonitors[monitor.monitor_id] = monitor

    def write_to_database(self, conn: sqlite3.Connection) -> bool:
        result = False
        try:
            conn.execute(f'''DROP TABLE IF EXISTS {Tables.WQ_MONITOR}''')
            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.WQ_MONITOR} (
                            monitor_id TEXT PRIMARY KEY,
                            csv_filespec TEXT,
                            data_start TEXT,
                            data_end TEXT,
                            data_interval INTEGER,
                            data_cond TEXT,
                            data_do TEXT,
                            data_do_sat TEXT,
                            data_nh4 TEXT,
                            data_ph TEXT,
                            data_temp TEXT
                        )''')
            for monitor in self.dictfwqMonitors.values():
                conn.execute(f'''INSERT OR REPLACE INTO {Tables.WQ_MONITOR} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (monitor.monitor_id, monitor.csv_filespec, monitor.data_start.isoformat(), monitor.data_end.isoformat(), int(monitor.data_interval), pickle.dumps(monitor.data_cond), pickle.dumps(monitor.data_do), pickle.dumps(monitor.data_do_sat), pickle.dumps(monitor.data_nh4), pickle.dumps(monitor.data_ph), pickle.dumps(monitor.data_temp)))
            conn.commit()
            result = True
            logger.debug("fwqMonitors.write_to_database Completed")

        except sqlite3.Error as e:
            logger.error(f"fwqMonitors.write_to_database: Database error: {e}")
            # print(f"Database error: {e}")
            conn.rollback()
        except Exception as e:
            logger.error(f"fwqMonitors.write_to_database: Exception in _query: {e}")
            # print(f"Exception in _query: {e}")
            conn.rollback()
        finally:
            return result


class plottedWQMonitors():

    plotWQs: Dict[str, fwqMonitor]
    plotEarliestStart: datetime = datetime.strptime('2172-05-12', '%Y-%m-%d')
    plotLatestEnd: datetime = datetime.strptime('1972-05-12', '%Y-%m-%d')
    __plotCurrentStart: datetime = datetime.strptime('2172-05-12', '%Y-%m-%d')
    __plotCurrentEnd: datetime = datetime.strptime('1972-05-12', '%Y-%m-%d')

    def __init__(self):
        self.plotWQs = {}

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
        self.updatePlottedWQsMinMaxValues()

    def getPlotCurrentStart(self):
        return self.__plotCurrentStart

    def getPlotCurrentEnd(self):
        return self.__plotCurrentEnd

    def clear(self):

        self.plotWQs.clear()
        self.updatePlottedWQsMinMaxValues()

    def addWQMonitor(self, objWQ: fwqMonitor, updateMaxMin: bool = True):

        if objWQ.monitor_id not in self.plotWQs:

            self.plotWQs[objWQ.monitor_id] = objWQ
            if updateMaxMin:
                self.updatePlottedWQsMinMaxValues()
            return True
        else:
            return False

    def removeWQ(self, nameWQ: str):

        if nameWQ in self.plotWQs:
            self.plotWQs.pop(nameWQ)
            self.updatePlottedWQsMinMaxValues()
            return True
        return False

    def getWQTimestep(self, nameWQ: str):

        if nameWQ in self.plotWQs:
            return self.plotWQs[nameWQ].data_interval

    def updatePlottedWQsMinMaxValues(self):

        pass

        # self.plotEarliestStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
        # self.plotLatestEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')

        # for wq in self.plotWQs.values():

        #     if self.plotEarliestStart > rg.dateRange[0]:
        #         self.plotEarliestStart = rg.dateRange[0]
        #     if self.plotLatestEnd < rg.dateRange[len(rg.dateRange)-1]:
        #         self.plotLatestEnd = rg.dateRange[len(rg.dateRange)-1]

        #     rg_start_time = calendar.timegm(rg.dateRange[0].timetuple())
        #     rg_end_time = calendar.timegm(rg.dateRange[-1].timetuple())
        #     start_time = calendar.timegm(
        #         self.getPlotCurrentStart().timetuple())
        #     end_time = calendar.timegm(self.getPlotCurrentEnd().timetuple())

        #     if (rg_start_time < start_time) and (start_time < rg_end_time):
        #         unix_rounded_xmin_python_datetime = calendar.timegm(
        #             rg.dateRange[0].timetuple())
        #         unix_rounded_xmax_python_datetime = calendar.timegm(
        #             self.getPlotCurrentStart().timetuple())
        #         unix_diff_mins = (
        #             (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)
        #         min_row = int(unix_diff_mins / rg.rgTimestep)
        #     else:
        #         min_row = 0

        #     if (rg_start_time < end_time) and (end_time < rg_end_time):
        #         unix_rounded_xmin_python_datetime = calendar.timegm(
        #             rg.dateRange[0].timetuple())
        #         unix_rounded_xmax_python_datetime = end_time
        #         unix_diff_mins = (
        #             (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)
        #         max_row = int(unix_diff_mins / rg.rgTimestep)
        #     else:
        #         max_row = len(rg.rainfallDataRange)

        #     self.plotMaxIntensity = max(rg.rainfallDataRange[min_row:max_row])
        #     self.plotMinIntensity = min(rg.rainfallDataRange[min_row:max_row])
        #     totalDepth = round(
        #         (sum(rg.rainfallDataRange[min_row:max_row]))/(60/rg.rgTimestep), 1)
        #     self.plotTotalDepth = self.plotTotalDepth + totalDepth

        #     unix_rounded_xmin_python_datetime = calendar.timegm(
        #         self.__plotCurrentStart.timetuple())
        #     unix_rounded_xmax_python_datetime = calendar.timegm(
        #         self.__plotCurrentEnd.timetuple())
        #     # unix_diff_days = (
        #     #     ((unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)/60)/24
        #     unix_diff_mins = (
        #         (unix_rounded_xmax_python_datetime - unix_rounded_xmin_python_datetime)/60)

        #     # self.plotReturnPeriod = round(
        #     #     (0.00494*(self.plotTotalDepth+2.54)**3.55)/unix_diff_mins, 2)
        #     duration_hrs = unix_diff_mins / 60
        #     self.plotReturnPeriod = round(
        #         10/(1.25*duration_hrs*(((0.0394*self.plotTotalDepth)+0.1)**-3.55)), 2)


class MappingDialog(QDialog):
    def __init__(self, monitor_mappings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select File Mappings")  # Set window title
        myIcon: QtGui.QIcon = QtGui.QIcon()
        myIcon.addPixmap(QtGui.QPixmap(resource_path(
            "resources\\Flowbot.ico")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(myIcon)  # Set app icon

        self.monitor_mappings = monitor_mappings

        # Create layout
        layout = QVBoxLayout()

        # Create table for monitor mappings
        self.table = QTableWidget()
        self.table.setRowCount(len(monitor_mappings))
        self.table.setColumnCount(7)  # 1 column for ID and 6 for parameters
        self.table.setHorizontalHeaderLabels(
            ['Monitor ID', 'COND', 'DO', 'DO_SAT', 'NH4', 'PH', 'TEMP'])

        # Populate table
        for i, (monitor_id, fields, mapping) in enumerate(monitor_mappings):
            item = QTableWidgetItem(monitor_id)
            # Make Monitor ID read-only
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 0, item)
            for j, param in enumerate(['COND', 'DO', 'DO_SAT', 'NH4', 'PH', 'TEMP']):
                combo = QComboBox()
                combo.addItem("None")
                combo.addItems(fields)
                combo.setCurrentText(
                    mapping[param] if mapping[param] else "None")
                self.table.setCellWidget(i, j + 1, combo)

        layout.addWidget(self.table)

        # Create button layout
        button_layout = QHBoxLayout()  # Horizontal layout for buttons

        # Add spacer to push buttons to the right
        button_layout.addStretch()  # Spacer added here

        # OK Button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)

        # Cancel Button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)  # Connect to reject
        button_layout.addWidget(cancel_button)

        # Add button layout to main layout
        layout.addLayout(button_layout)

        # Adjust window size to fit the table width
        table_width = self.table.horizontalHeader().length(
        ) + self.table.verticalScrollBar().sizeHint().width()
        self.resize(table_width, self.table.sizeHint().height() + 100)

        self.setLayout(layout)

    def get_mappings(self):
        mappings = []
        for i in range(self.table.rowCount()):
            monitor_id = self.table.item(i, 0).text()
            mapping = {param: self.table.cellWidget(
                i, j+1).currentText() for j, param in enumerate(['COND', 'DO', 'DO_SAT', 'NH4', 'PH', 'TEMP'])}
            mappings.append((monitor_id, mapping))
        return mappings

# class MappingDialog(QDialog):
#     def __init__(self, monitor_mappings, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Select File Mappings")  # Set window title
#         myIcon: QtGui.QIcon = QtGui.QIcon()
#         myIcon.addPixmap(QtGui.QPixmap(resource_path(
#             "resources\\Flowbot.ico")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
#         self.setWindowIcon(myIcon)  # Set app icon

#         self.monitor_mappings = monitor_mappings

#         # Create layout
#         layout = QVBoxLayout()

#         # Create table for monitor mappings
#         self.table = QTableWidget()
#         self.table.setRowCount(len(monitor_mappings))
#         self.table.setColumnCount(7)  # 1 column for ID and 6 for parameters
#         self.table.setHorizontalHeaderLabels(
#             ['Monitor ID', 'COND', 'DO', 'DO_SAT', 'NH4', 'PH', 'TEMP'])

#         # Populate table
#         for i, (monitor_id, fields, mapping) in enumerate(monitor_mappings):
#             item = QTableWidgetItem(monitor_id)
#             # Make Monitor ID read-only
#             item.setFlags(item.flags() & ~Qt.ItemIsEditable)
#             self.table.setItem(i, 0, item)
#             for j, param in enumerate(['COND', 'DO', 'DO_SAT', 'NH4', 'PH', 'TEMP']):
#                 combo = QComboBox()
#                 combo.addItem("None")
#                 combo.addItems(fields)
#                 combo.setCurrentText(
#                     mapping[param] if mapping[param] else "None")
#                 self.table.setCellWidget(i, j + 1, combo)

#         layout.addWidget(self.table)

#         # Create button layout
#         button_layout = QHBoxLayout()  # Horizontal layout for buttons

#         # OK Button
#         ok_button = QPushButton("OK")
#         ok_button.clicked.connect(self.accept)
#         button_layout.addWidget(ok_button)

#         # Cancel Button
#         cancel_button = QPushButton("Cancel")
#         cancel_button.clicked.connect(self.reject)  # Connect to reject
#         button_layout.addWidget(cancel_button)

#         # Add button layout to main layout
#         layout.addLayout(button_layout)

#         # Add stretch to push buttons to the bottom right
#         layout.addStretch()  # This will push the button layout to the bottom

#         self.setLayout(layout)

#         # Adjust window size to fit the table
#         # Adjust height as needed
#         self.resize(self.table.sizeHint().width(),
#                     self.table.sizeHint().height() + 100)

#     def get_mappings(self):
#         mappings = []
#         for i in range(self.table.rowCount()):
#             monitor_id = self.table.item(i, 0).text()
#             mapping = {param: self.table.cellWidget(
#                 i, j+1).currentText() for j, param in enumerate(['COND', 'DO', 'DO_SAT', 'NH4', 'PH', 'TEMP'])}
#             mappings.append((monitor_id, mapping))
#         return mappings
