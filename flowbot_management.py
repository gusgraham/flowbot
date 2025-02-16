import os
from typing import Dict, Optional, List
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import numpy as np
import math
from sklearn.utils.class_weight import compute_class_weight
from scipy.stats import entropy, skew, kurtosis
from scipy.signal import welch
import joblib
from flowbot_helper import resource_path

# models
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from catboost import CatBoostClassifier
from scipy import interpolate
# from contextlib import closing

from flowbot_database import Tables
# from flowbot_dialog_fsm_install import flowbot_dialog_fsm_install
# from flowbot_dialog_fsm_uninstall import flowbot_dialog_fsm_uninstall

from PyQt5.QtWidgets import QDialog, QMessageBox


class fsmMonitor(object):

    def __init__(self):
        self.monitor_asset_id: str = ''
        self.monitor_type: str = 'Flow Monitor'
        self.pmac_id: str = ''
        self.monitor_sub_type: str = "Detec"

    # def from_database_row(self, row):
    #     self.monitor_asset_id = row[0]
    #     self.monitor_type = row[1]
    #     self.pmac_id = row[2]
    #     self.monitor_sub_type = row[3]

    def from_database_row_dict(self, row_dict: Dict):
        self.monitor_asset_id = row_dict.get('monitor_asset_id')
        self.monitor_type = row_dict.get('monitor_type', self.monitor_type)
        self.pmac_id = row_dict.get('pmac_id')
        self.monitor_sub_type = row_dict.get('monitor_sub_type', self.monitor_sub_type)


# class fsmInstall(object):

#     def __init__(self):
#         self.install_id: int = 1
#         self.install_site_id: str = ''
#         self.install_monitor_asset_id: str = ''
#         self.install_type: str = 'Flow Monitor'
#         self.client_ref: str = ''
#         self.install_date: datetime = datetime.strptime(
#             '2172-05-12', '%Y-%m-%d')
#         self.remove_date: datetime = datetime.strptime(
#             '1972-05-12', '%Y-%m-%d')
#         self.fm_pipe_letter: str = "A"
#         self.fm_pipe_shape: str = "Circular"
#         self.fm_pipe_height_mm: int = 225
#         self.fm_pipe_width_mm: int = 225
#         self.fm_pipe_depth_to_invert_mm: int = 2000
#         self.fm_sensor_offset_mm: int = 0
#         self.rg_position: str = 'Ground'
#         self.data: Optional[pd.DataFrame] = None
#         self.data_start: datetime = datetime.strptime('2172-05-12', '%Y-%m-%d')
#         self.data_end: datetime = datetime.strptime('2172-05-12', '%Y-%m-%d')
#         self.data_interval: int = 0
#         self.data_date_updated: datetime = datetime.strptime(
#             '1972-05-12', '%Y-%m-%d')
#         self.install_sheet: Optional[bytes] = None
#         self.install_sheet_filename: str = ''
#         self.class_data_ml: Optional[pd.DataFrame] = None
#         self.class_data_ml_date_updated: datetime = datetime.strptime(
#             '1972-05-12', '%Y-%m-%d')
#         self.class_data_user: Optional[pd.DataFrame] = None
#         self.class_data_user_date_updated: datetime = datetime.strptime(
#             '1972-05-12', '%Y-%m-%d')

#     def from_database_row_dict(self, row_dict: Dict):
#         self.install_id = row_dict.get('install_id', self.install_id)
#         self.install_site_id = row_dict.get('install_site_id', self.install_site_id)
#         self.install_monitor_asset_id = row_dict.get('install_monitor_asset_id', self.install_monitor_asset_id)
#         self.install_type = row_dict.get('install_type', self.install_type)
#         self.client_ref = row_dict.get('client_ref', self.client_ref)

#         if isinstance(row_dict.get('install_date'), str):
#             self.install_date = datetime.fromisoformat(row_dict['install_date'])

#         if isinstance(row_dict.get('remove_date'), str):
#             self.remove_date = datetime.fromisoformat(row_dict['remove_date'])

#         self.fm_pipe_letter = row_dict.get('fm_pipe_letter', self.fm_pipe_letter)
#         self.fm_pipe_shape = row_dict.get('fm_pipe_shape', self.fm_pipe_shape)
#         self.fm_pipe_height_mm = row_dict.get('fm_pipe_height_mm', self.fm_pipe_height_mm)
#         self.fm_pipe_width_mm = row_dict.get('fm_pipe_width_mm', self.fm_pipe_width_mm)
#         self.fm_pipe_depth_to_invert_mm = row_dict.get('fm_pipe_depth_to_invert_mm', self.fm_pipe_depth_to_invert_mm)
#         self.fm_sensor_offset_mm = row_dict.get('fm_sensor_offset_mm', self.fm_sensor_offset_mm)
#         self.rg_position = row_dict.get('rg_position', self.rg_position)

#         if row_dict.get('data') is not None:
#             self.data = pickle.loads(row_dict['data'])

#         if isinstance(row_dict.get('data_start'), str):
#             self.data_start = datetime.fromisoformat(row_dict['data_start'])

#         if isinstance(row_dict.get('data_end'), str):
#             self.data_end = datetime.fromisoformat(row_dict['data_end'])

#         self.data_interval = row_dict.get('data_interval', self.data_interval)

#         if isinstance(row_dict.get('data_date_updated'), str):
#             self.data_date_updated = datetime.fromisoformat(row_dict['data_date_updated'])

#         if row_dict.get('install_sheet') is not None:
#             self.install_sheet = row_dict['install_sheet']

#         self.install_sheet_filename = row_dict.get('install_sheet_filename', self.install_sheet_filename)

#         if row_dict.get('class_data_ml') is not None:
#             self.class_data_ml = pickle.loads(row_dict['class_data_ml'])

#         if isinstance(row_dict.get('class_data_ml_date_updated'), str):
#             self.class_data_ml_date_updated = datetime.fromisoformat(row_dict['class_data_ml_date_updated'])

#         if row_dict.get('class_data_user') is not None:
#             self.class_data_user = pickle.loads(row_dict['class_data_user'])

#         if isinstance(row_dict.get('class_data_user_date_updated'), str):
#             self.class_data_user_date_updated = datetime.fromisoformat(row_dict['class_data_user_date_updated'])

#     # def from_database_row(self, row):
#     #     self.install_id = row[0]
#     #     self.install_site_id = row[1]
#     #     self.install_monitor_asset_id = row[2]
#     #     self.install_type = row[3]
#     #     self.client_ref = row[4]
#     #     self.install_date = datetime.fromisoformat(row[5])
#     #     self.remove_date = datetime.fromisoformat(row[6])
#     #     self.fm_pipe_letter = row[7]
#     #     self.fm_pipe_shape = row[8]
#     #     self.fm_pipe_height_mm = row[9]
#     #     self.fm_pipe_width_mm = row[10]
#     #     self.fm_pipe_depth_to_invert_mm = row[11]
#     #     self.fm_sensor_offset_mm = row[12]
#     #     self.rg_position = row[13]
#     #     if row[14] is not None:
#     #         self.data = pickle.loads(row[14])
#     #     if isinstance(row[15], str):
#     #         self.data_start = datetime.fromisoformat(row[15])
#     #     if isinstance(row[16], str):
#     #         self.data_end = datetime.fromisoformat(row[16])
#     #     self.data_interval = row[17]
#     #     if isinstance(row[18], str):
#     #         self.data_date_updated = datetime.fromisoformat(row[18])
#     #     self.install_sheet = row[19]
#     #     self.install_sheet_filename = row[20]
#     #     if row[21] is not None:
#     #         self.class_data_ml = pickle.loads(row[21])
#     #     if isinstance(row[22], str):
#     #         self.class_data_ml_date_updated = datetime.fromisoformat(row[22])
#     #     if row[23] is not None:
#     #         self.class_data_user = pickle.loads(row[23])
#     #     if isinstance(row[24], str):
#     #         self.class_data_user_date_updated = datetime.fromisoformat(row[24])

#     def get_fdv_data_from_file(self, fileSpec: str):

#         dateRange: List[datetime] = []
#         flowDataRange: List[float] = []
#         depthDataRange: List[float] = []
#         velocityDataRange: List[float] = []

#         with open(fileSpec, 'r', encoding='utf-8') as org_data:
#             # self.fdvFileSpec = fileSpec
#             in_data_section = False
#             # org_data.readline()
#             previous_line = ""
#             i_data_count = 0
#             for line in org_data:
#                 if in_data_section:
#                     if line.startswith('*END'):
#                         break
#                     if line.strip() and line[3:6] != "":
#                         dateRange.append(self.data_start +
#                                          timedelta(minutes=i_data_count * self.data_interval))
#                         flowDataRange.append(float(line[0:5]))
#                         depthDataRange.append(float(line[5:10]))
#                         velocityDataRange.append(float(line[10:15]))
#                         i_data_count += 1
#                         if line[16:20]:
#                             dateRange.append(self.data_start +
#                                              timedelta(minutes=i_data_count * self.data_interval))
#                             flowDataRange.append(float(line[15:20]))
#                             depthDataRange.append(float(line[20:25]))
#                             velocityDataRange.append(float(line[25:30]))
#                             i_data_count += 1
#                         if line[31:35]:
#                             dateRange.append(self.data_start +
#                                              timedelta(minutes=i_data_count * self.data_interval))
#                             flowDataRange.append(float(line[30:35]))
#                             depthDataRange.append(float(line[35:40]))
#                             velocityDataRange.append(float(line[40:45]))
#                             i_data_count += 1
#                         if line[46:50]:
#                             dateRange.append(self.data_start +
#                                              timedelta(minutes=i_data_count * self.data_interval))
#                             flowDataRange.append(float(line[45:50]))
#                             depthDataRange.append(float(line[50:55]))
#                             velocityDataRange.append(float(line[55:60]))
#                             i_data_count += 1
#                         if line[61:65]:
#                             dateRange.append(self.data_start +
#                                              timedelta(minutes=i_data_count * self.data_interval))
#                             flowDataRange.append(float(line[60:65]))
#                             depthDataRange.append(float(line[65:70]))
#                             velocityDataRange.append(float(line[70:75]))
#                             i_data_count += 1

#                 elif line.startswith('*CEND'):
#                     start_timestamp, end_timestamp, interval_minutes = map(
#                         int, previous_line.split())
#                     try:
#                         self.data_start = datetime.strptime(
#                             str(start_timestamp), "%y%m%d%H%M"
#                         )
#                     except ValueError:
#                         self.data_start = datetime.strptime(
#                             str(start_timestamp), "%Y%m%d%H%M"
#                         )
#                     try:
#                         self.data_end = datetime.strptime(
#                             str(end_timestamp), "%y%m%d%H%M"
#                         )
#                     except ValueError:
#                         self.data_end = datetime.strptime(
#                             str(end_timestamp), "%Y%m%d%H%M"
#                         )
#                     self.data_interval = interval_minutes
#                     in_data_section = True
#                 else:
#                     previous_line = line
#                     continue

#         data = {
#             'Date': dateRange,
#             'FlowData': flowDataRange,
#             'DepthData': depthDataRange,
#             'VelocityData': velocityDataRange
#         }

#         self.data = pd.DataFrame(data)
#         self.data_date_updated = datetime.now()

#     def get_r_data_from_file(self, fileSpec: str):
#         dateRange: List[datetime] = []
#         intensityDataRange: List[float] = []

#         with open(fileSpec, 'r', encoding='utf-8') as org_data:
#             print(fileSpec)
#             in_data_section = False
#             previous_line = ""
#             i_data_count = 0

#             for line in org_data:
#                 if in_data_section:
#                     if line.startswith('*END'):
#                         break
#                     # /line = line.strip()
#                     if line:
#                         # Process the line in chunks of 15 characters
#                         for i in range(0, len(line), 15):
#                             chunk = line[i:i+15].strip()
#                             if chunk:  # Only process non-empty chunks
#                                 try:
#                                     value = float(chunk)
#                                     dateRange.append(
#                                         self.data_start + timedelta(minutes=i_data_count * self.data_interval))
#                                     intensityDataRange.append(value)
#                                     i_data_count += 1
#                                 except ValueError:
#                                     # Handle the case where chunk is not a valid float
#                                     print(
#                                         f"Warning: Unable to convert chunk to float: {chunk}")
#                 elif line.startswith('*CEND'):
#                     # Extract start timestamp, end timestamp, and interval from the previous line
#                     previous_line = previous_line.strip()
#                     if previous_line:
#                         start_timestamp, end_timestamp, interval_minutes = previous_line.split()
#                         self.data_start = datetime.strptime(
#                             start_timestamp, '%y%m%d%H%M')
#                         self.data_end = datetime.strptime(
#                             end_timestamp, '%y%m%d%H%M')
#                         self.data_interval = int(interval_minutes)
#                         in_data_section = True
#                 else:
#                     previous_line = line

#         data = {
#             'Date': dateRange,
#             'IntensityData': intensityDataRange
#         }

#         self.data = pd.DataFrame(data)
#         self.data_date_updated = datetime.now()

#     def get_peak_intensity_as_str(self, dt_start: datetime, dt_end: datetime) -> str:
#         if self.install_type == 'Rain Gauge':
#             if (self.data_start <= dt_start) and (self.data_end >= dt_end):
#                 # Filter the DataFrame for the given date range
#                 mask = (self.data['Date'] >= dt_start) & (
#                     self.data['Date'] <= dt_end)
#                 filtered_data = self.data.loc[mask]

#                 # Find the peak intensity
#                 peak_intensity = filtered_data['IntensityData'].max()

#                 return f"{peak_intensity:.1f}"
#             else:
#                 return '-'
#         else:
#             return '-'

#     def get_total_depth_as_str(self, dt_start: datetime, dt_end: datetime) -> float:
#         if self.install_type == 'Rain Gauge':
#             if (self.data_start <= dt_start) and (self.data_end >= dt_end):
#                 # Filter the DataFrame for the given date range
#                 mask = (self.data['Date'] >= dt_start) & (
#                     self.data['Date'] <= dt_end)
#                 filtered_data = self.data.loc[mask].copy()

#                 filtered_data['depth_in_mm'] = filtered_data['IntensityData'] * \
#                     (self.data_interval / 60)

#                 total_depth = filtered_data['depth_in_mm'].sum()

#                 return f"{total_depth:.2f}"
#             else:
#                 return '-'
#         else:
#             return '-'

#     def get_combined_classification_by_date(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:

#         if self.class_data_ml is not None:
#             df_class_ml_filtered = self.class_data_ml[(self.class_data_ml['Date'] >= start_date)
#                                                       & (self.class_data_ml['Date'] <= end_date)]
#         else:
#             df_class_ml_filtered = pd.DataFrame(
#                 columns=['Date', 'Classification', 'Confidence'])

#         if self.class_data_user is not None:
#             df_class_user_filtered = self.class_data_user[(self.class_data_user['Date'] >= start_date)
#                                                           & (self.class_data_user['Date'] <= end_date)]
#         else:
#             df_class_user_filtered = pd.DataFrame(
#                 columns=['Date', 'Classification', 'Confidence'])

#         if not df_class_ml_filtered.empty or not df_class_user_filtered.empty:
#             combined = pd.concat(
#                 [df_class_user_filtered, df_class_ml_filtered])
#             df_class_combined_filtered = combined.drop_duplicates(
#                 subset='Date', keep='first')
#         else:
#             df_class_combined_filtered = pd.DataFrame(
#                 columns=['Date', 'Classification', 'Confidence'])

#         return df_class_combined_filtered

#     def get_combined_classification(self) -> pd.DataFrame:

#         if self.class_data_ml is not None and self.class_data_user is not None:
#             combined = pd.concat([self.class_data_user, self.class_data_ml])
#             df_class_combined = combined.drop_duplicates(
#                 subset='Date', keep='first')
#         else:
#             df_class_combined = pd.DataFrame(
#                 columns=['Date', 'Classification', 'Confidence'])

#         return df_class_combined


class fsmInstall(object):

    def __init__(self):
        self.install_id: str = "1"
        self.install_site_id: str = ""
        self.install_monitor_asset_id: str = ""
        self.install_type: str = "Flow Monitor"
        self.client_ref: str = ""
        self.install_date: datetime = datetime.strptime("2172-05-12", "%Y-%m-%d")
        self.remove_date: datetime = datetime.strptime("1972-05-12", "%Y-%m-%d")
        self.fm_pipe_letter: str = "A"
        self.fm_pipe_shape: str = "Circular"
        self.fm_pipe_height_mm: int = 225
        self.fm_pipe_width_mm: int = 225
        self.fm_pipe_depth_to_invert_mm: int = 2000
        self.fm_sensor_offset_mm: int = 0
        self.rg_position: str = "Ground"
        self.data: Optional[pd.DataFrame] = None
        self.data_start: datetime = datetime.strptime("2172-05-12", "%Y-%m-%d")
        self.data_end: datetime = datetime.strptime("2172-05-12", "%Y-%m-%d")
        self.data_interval: int = 0
        self.data_date_updated: datetime = datetime.strptime("1972-05-12", "%Y-%m-%d")
        self.install_sheet: Optional[bytes] = None
        self.install_sheet_filename: str = ""
        self.class_data_ml: Optional[pd.DataFrame] = None
        self.class_data_ml_date_updated: datetime = datetime.strptime(
            "1972-05-12", "%Y-%m-%d"
        )
        self.class_data_user: Optional[pd.DataFrame] = None
        self.class_data_user_date_updated: datetime = datetime.strptime(
            "1972-05-12", "%Y-%m-%d"
        )

    def from_database_row_dict(self, row_dict: Dict):
        self.install_id = row_dict.get("install_id", self.install_id)
        self.install_site_id = row_dict.get("install_site_id", self.install_site_id)
        self.install_monitor_asset_id = row_dict.get(
            "install_monitor_asset_id", self.install_monitor_asset_id
        )
        self.install_type = row_dict.get("install_type", self.install_type)
        self.client_ref = row_dict.get("client_ref", self.client_ref)

        if isinstance(row_dict.get("install_date"), str):
            self.install_date = datetime.fromisoformat(row_dict["install_date"])

        if isinstance(row_dict.get("remove_date"), str):
            self.remove_date = datetime.fromisoformat(row_dict["remove_date"])

        self.fm_pipe_letter = row_dict.get("fm_pipe_letter", self.fm_pipe_letter)
        self.fm_pipe_shape = row_dict.get("fm_pipe_shape", self.fm_pipe_shape)
        self.fm_pipe_height_mm = row_dict.get(
            "fm_pipe_height_mm", self.fm_pipe_height_mm
        )
        self.fm_pipe_width_mm = row_dict.get("fm_pipe_width_mm", self.fm_pipe_width_mm)
        self.fm_pipe_depth_to_invert_mm = row_dict.get(
            "fm_pipe_depth_to_invert_mm", self.fm_pipe_depth_to_invert_mm
        )
        self.fm_sensor_offset_mm = row_dict.get(
            "fm_sensor_offset_mm", self.fm_sensor_offset_mm
        )
        self.rg_position = row_dict.get("rg_position", self.rg_position)

        if row_dict.get("data") is not None:
            self.data = pickle.loads(row_dict["data"])

        if isinstance(row_dict.get("data_start"), str):
            self.data_start = datetime.fromisoformat(row_dict["data_start"])

        if isinstance(row_dict.get("data_end"), str):
            self.data_end = datetime.fromisoformat(row_dict["data_end"])

        self.data_interval = row_dict.get("data_interval", self.data_interval)

        if isinstance(row_dict.get("data_date_updated"), str):
            self.data_date_updated = datetime.fromisoformat(
                row_dict["data_date_updated"]
            )

        if row_dict.get("install_sheet") in (None, b''):
            self.install_sheet = None
        else:
            self.install_sheet = row_dict["install_sheet"]

        self.install_sheet_filename = row_dict.get(
            "install_sheet_filename", self.install_sheet_filename
        )

        if row_dict.get("class_data_ml") is not None:
            self.class_data_ml = pickle.loads(row_dict["class_data_ml"])

        if isinstance(row_dict.get("class_data_ml_date_updated"), str):
            self.class_data_ml_date_updated = datetime.fromisoformat(
                row_dict["class_data_ml_date_updated"]
            )

        if row_dict.get("class_data_user") is not None:
            self.class_data_user = pickle.loads(row_dict["class_data_user"])

        if isinstance(row_dict.get("class_data_user_date_updated"), str):
            self.class_data_user_date_updated = datetime.fromisoformat(
                row_dict["class_data_user_date_updated"]
            )

    # def from_database_row(self, row):
    #     self.install_id = row[0]
    #     self.install_site_id = row[1]
    #     self.install_monitor_asset_id = row[2]
    #     self.install_type = row[3]
    #     self.client_ref = row[4]
    #     self.install_date = datetime.fromisoformat(row[5])
    #     self.remove_date = datetime.fromisoformat(row[6])
    #     self.fm_pipe_letter = row[7]
    #     self.fm_pipe_shape = row[8]
    #     self.fm_pipe_height_mm = row[9]
    #     self.fm_pipe_width_mm = row[10]
    #     self.fm_pipe_depth_to_invert_mm = row[11]
    #     self.fm_sensor_offset_mm = row[12]
    #     self.rg_position = row[13]
    #     if row[14] is not None:
    #         self.data = pickle.loads(row[14])
    #     if isinstance(row[15], str):
    #         self.data_start = datetime.fromisoformat(row[15])
    #     if isinstance(row[16], str):
    #         self.data_end = datetime.fromisoformat(row[16])
    #     self.data_interval = row[17]
    #     if isinstance(row[18], str):
    #         self.data_date_updated = datetime.fromisoformat(row[18])
    #     self.install_sheet = row[19]
    #     self.install_sheet_filename = row[20]
    #     if row[21] is not None:
    #         self.class_data_ml = pickle.loads(row[21])
    #     if isinstance(row[22], str):
    #         self.class_data_ml_date_updated = datetime.fromisoformat(row[22])
    #     if row[23] is not None:
    #         self.class_data_user = pickle.loads(row[23])
    #     if isinstance(row[24], str):
    #         self.class_data_user_date_updated = datetime.fromisoformat(row[24])

    def get_fdv_data_from_file(self, fileSpec: str):

        dateRange: List[datetime] = []
        flowDataRange: List[float] = []
        depthDataRange: List[float] = []
        velocityDataRange: List[float] = []

        with open(fileSpec, "r", encoding="utf-8") as org_data:
            # self.fdvFileSpec = fileSpec
            in_data_section = False
            # org_data.readline()
            previous_line = ""
            i_data_count = 0
            for line in org_data:
                if in_data_section:
                    if line.startswith("*END"):
                        break
                    if line.strip() and line[3:6] != "":
                        dateRange.append(
                            self.data_start
                            + timedelta(minutes=i_data_count * self.data_interval)
                        )
                        flowDataRange.append(float(line[0:5]))
                        depthDataRange.append(float(line[5:10]))
                        velocityDataRange.append(float(line[10:15]))
                        i_data_count += 1
                        if line[16:20]:
                            dateRange.append(
                                self.data_start
                                + timedelta(minutes=i_data_count * self.data_interval)
                            )
                            flowDataRange.append(float(line[15:20]))
                            depthDataRange.append(float(line[20:25]))
                            velocityDataRange.append(float(line[25:30]))
                            i_data_count += 1
                        if line[31:35]:
                            dateRange.append(
                                self.data_start
                                + timedelta(minutes=i_data_count * self.data_interval)
                            )
                            flowDataRange.append(float(line[30:35]))
                            depthDataRange.append(float(line[35:40]))
                            velocityDataRange.append(float(line[40:45]))
                            i_data_count += 1
                        if line[46:50]:
                            dateRange.append(
                                self.data_start
                                + timedelta(minutes=i_data_count * self.data_interval)
                            )
                            flowDataRange.append(float(line[45:50]))
                            depthDataRange.append(float(line[50:55]))
                            velocityDataRange.append(float(line[55:60]))
                            i_data_count += 1
                        if line[61:65]:
                            dateRange.append(
                                self.data_start
                                + timedelta(minutes=i_data_count * self.data_interval)
                            )
                            flowDataRange.append(float(line[60:65]))
                            depthDataRange.append(float(line[65:70]))
                            velocityDataRange.append(float(line[70:75]))
                            i_data_count += 1

                elif line.startswith("*CEND"):
                    start_timestamp, end_timestamp, interval_minutes = map(
                        int, previous_line.split()
                    )
                    try:
                        self.data_start = datetime.strptime(
                            str(start_timestamp), "%y%m%d%H%M"
                        )
                    except ValueError:
                        self.data_start = datetime.strptime(
                            str(start_timestamp), "%Y%m%d%H%M"
                        )
                    try:
                        self.data_end = datetime.strptime(
                            str(end_timestamp), "%y%m%d%H%M"
                        )
                    except ValueError:
                        self.data_end = datetime.strptime(
                            str(end_timestamp), "%Y%m%d%H%M"
                        )
                    self.data_interval = interval_minutes
                    in_data_section = True
                else:
                    previous_line = line
                    continue

        data = {
            "Date": dateRange,
            "FlowData": flowDataRange,
            "DepthData": depthDataRange,
            "VelocityData": velocityDataRange,
        }

        self.data = pd.DataFrame(data)
        self.data_date_updated = datetime.now()

    def get_r_data_from_file(self, fileSpec: str):
        dateRange: List[datetime] = []
        intensityDataRange: List[float] = []

        with open(fileSpec, "r", encoding="utf-8") as org_data:
            print(fileSpec)
            in_data_section = False
            previous_line = ""
            i_data_count = 0

            for line in org_data:
                if in_data_section:
                    if line.startswith("*END"):
                        break
                    # /line = line.strip()
                    if line:
                        # Process the line in chunks of 15 characters
                        for i in range(0, len(line), 15):
                            chunk = line[i : i + 15].strip()
                            if chunk:  # Only process non-empty chunks
                                try:
                                    value = float(chunk)
                                    dateRange.append(
                                        self.data_start
                                        + timedelta(
                                            minutes=i_data_count * self.data_interval
                                        )
                                    )
                                    intensityDataRange.append(value)
                                    i_data_count += 1
                                except ValueError:
                                    # Handle the case where chunk is not a valid float
                                    print(
                                        f"Warning: Unable to convert chunk to float: {chunk}"
                                    )
                elif line.startswith("*CEND"):
                    # Extract start timestamp, end timestamp, and interval from the previous line
                    previous_line = previous_line.strip()
                    if previous_line:
                        start_timestamp, end_timestamp, interval_minutes = (
                            previous_line.split()
                        )
                        self.data_start = datetime.strptime(
                            start_timestamp, "%y%m%d%H%M"
                        )
                        self.data_end = datetime.strptime(end_timestamp, "%y%m%d%H%M")
                        self.data_interval = int(interval_minutes)
                        in_data_section = True
                else:
                    previous_line = line

        data = {"Date": dateRange, "IntensityData": intensityDataRange}

        self.data = pd.DataFrame(data)
        self.data_date_updated = datetime.now()

    def get_peak_intensity_as_str(self, dt_start: datetime, dt_end: datetime) -> str:
        if self.install_type == "Rain Gauge":
            if (self.data_start <= dt_start) and (self.data_end >= dt_end):
                # Filter the DataFrame for the given date range
                mask = (self.data["Date"] >= dt_start) & (self.data["Date"] <= dt_end)
                filtered_data = self.data.loc[mask]

                # Find the peak intensity
                peak_intensity = filtered_data["IntensityData"].max()

                return f"{peak_intensity:.1f}"
            else:
                return "-"
        else:
            return "-"

    def get_total_depth_as_str(self, dt_start: datetime, dt_end: datetime) -> float:
        if self.install_type == "Rain Gauge":
            if (self.data_start <= dt_start) and (self.data_end >= dt_end):
                # Filter the DataFrame for the given date range
                mask = (self.data["Date"] >= dt_start) & (self.data["Date"] <= dt_end)
                filtered_data = self.data.loc[mask].copy()

                filtered_data["depth_in_mm"] = filtered_data["IntensityData"] * (
                    self.data_interval / 60
                )

                total_depth = filtered_data["depth_in_mm"].sum()

                return f"{total_depth:.2f}"
            else:
                return "-"
        else:
            return "-"

    def get_combined_classification_by_date(
        self, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:

        if self.class_data_ml is not None:
            df_class_ml_filtered = self.class_data_ml[
                (self.class_data_ml["Date"] >= start_date)
                & (self.class_data_ml["Date"] <= end_date)
            ]
        else:
            df_class_ml_filtered = pd.DataFrame(
                columns=["Date", "Classification", "Confidence"]
            )

        if self.class_data_user is not None:
            df_class_user_filtered = self.class_data_user[
                (self.class_data_user["Date"] >= start_date)
                & (self.class_data_user["Date"] <= end_date)
            ]
        else:
            df_class_user_filtered = pd.DataFrame(
                columns=["Date", "Classification", "Confidence"]
            )

        if not df_class_ml_filtered.empty or not df_class_user_filtered.empty:
            combined = pd.concat([df_class_user_filtered, df_class_ml_filtered])
            df_class_combined_filtered = combined.drop_duplicates(
                subset="Date", keep="first"
            )
        else:
            df_class_combined_filtered = pd.DataFrame(
                columns=["Date", "Classification", "Confidence"]
            )

        return df_class_combined_filtered

    def get_combined_classification(self) -> pd.DataFrame:

        if self.class_data_ml is not None and self.class_data_user is not None:
            combined = pd.concat([self.class_data_user, self.class_data_ml])
            df_class_combined = combined.drop_duplicates(subset="Date", keep="first")
        else:
            df_class_combined = pd.DataFrame(
                columns=["Date", "Classification", "Confidence"]
            )

        return df_class_combined


# class fsmRawData(object):

#     def __init__(self):
#         self.rawdata_id: int = 1
#         self.install_id: int = 0
#         self.rg_tb_depth: float = 0.2
#         self.rg_data: Optional[pd.DataFrame] = None
#         self.rg_data_start: datetime = datetime.strptime(
#             '2172-05-12', '%Y-%m-%d')
#         self.rg_data_end: datetime = datetime.strptime(
#             '2172-05-12', '%Y-%m-%d')
#         self.rg_timing_corr: Optional[pd.DataFrame] = None
#         self.dep_data: Optional[pd.DataFrame] = None
#         self.dep_data_start: datetime = datetime.strptime(
#             '2172-05-12', '%Y-%m-%d')
#         self.dep_data_end: datetime = datetime.strptime(
#             '2172-05-12', '%Y-%m-%d')
#         self.dep_corr: Optional[pd.DataFrame] = None
#         self.vel_data: Optional[pd.DataFrame] = None
#         self.vel_data_start: datetime = datetime.strptime(
#             '2172-05-12', '%Y-%m-%d')
#         self.vel_data_end: datetime = datetime.strptime(
#             '2172-05-12', '%Y-%m-%d')
#         self.vel_corr: Optional[pd.DataFrame] = None
#         self.dv_timing_corr: Optional[pd.DataFrame] = None
#         self.bat_data: Optional[pd.DataFrame] = None
#         self.bat_data_start: datetime = datetime.strptime(
#             '2172-05-12', '%Y-%m-%d')
#         self.bat_data_end: datetime = datetime.strptime(
#             '2172-05-12', '%Y-%m-%d')
#         self.pl_data: Optional[pd.DataFrame] = None
#         self.pl_data_start: datetime = datetime.strptime(
#             '2172-05-12', '%Y-%m-%d')
#         self.pl_data_end: datetime = datetime.strptime(
#             '2172-05-12', '%Y-%m-%d')
#         self.pl_timing_corr: Optional[pd.DataFrame] = None
#         self.pl_added_onoffs: Optional[pd.DataFrame] = None
#         self.pipe_shape: str = 'CIRC'
#         self.pipe_width: int = 225
#         self.pipe_height: int = 225
#         self.pipe_shape_def: Optional[pd.DataFrame] = None
#         self.silt_levels: Optional[pd.DataFrame] = None
#         self.pipe_shape_intervals: int = 20
#         self.file_path: str = ''
#         self.rainfall_file_format: str = '{pmac_id}_02.dat'
#         self.depth_file_format: str = '{pmac_id}_06.dat'
#         self.velocity_file_format: str = '{pmac_id}_07.dat'
#         self.battery_file_format: str = '{pmac_id}_08.dat'
#         self.pumplogger_file_format: str = '{pmac_id}.csv'

#     # def from_database_row(self, row):
#     #     self.rawdata_id = row[0]
#     #     self.install_id = row[1]
#     #     self.rg_tb_depth = row[2]
#     #     if row[3] is not None:
#     #         self.rg_data = pickle.loads(row[3])
#     #     if isinstance(row[4], str):
#     #         self.rg_data_start = datetime.fromisoformat(row[4])
#     #     if isinstance(row[5], str):
#     #         self.rg_data_end = datetime.fromisoformat(row[5])
#     #     if row[6] is not None:
#     #         self.rg_timing_corr = pickle.loads(row[6])
#     #     if row[7] is not None:
#     #         self.dep_data = pickle.loads(row[7])
#     #     if isinstance(row[8], str):
#     #         self.dep_data_start = datetime.fromisoformat(row[8])
#     #     if isinstance(row[9], str):
#     #         self.dep_data_end = datetime.fromisoformat(row[9])
#     #     if row[10] is not None:
#     #         self.dep_corr = pickle.loads(row[10])
#     #     if row[11] is not None:
#     #         self.vel_data = pickle.loads(row[11])
#     #     if isinstance(row[12], str):
#     #         self.vel_data_start = datetime.fromisoformat(row[12])
#     #     if isinstance(row[13], str):
#     #         self.vel_data_end = datetime.fromisoformat(row[13])
#     #     if row[14] is not None:
#     #         self.vel_corr = pickle.loads(row[14])
#     #     if row[15] is not None:
#     #         self.dv_timing_corr = pickle.loads(row[15])
#     #     if row[16] is not None:
#     #         self.bat_data = pickle.loads(row[16])
#     #     if isinstance(row[17], str):
#     #         self.bat_data_start = datetime.fromisoformat(row[17])
#     #     if isinstance(row[18], str):
#     #         self.bat_data_end = datetime.fromisoformat(row[18])
#     #     if row[19] is not None:
#     #         self.pl_data = pickle.loads(row[19])
#     #     if isinstance(row[20], str):
#     #         self.pl_data_start = datetime.fromisoformat(row[20])
#     #     if isinstance(row[21], str):
#     #         self.pl_data_end = datetime.fromisoformat(row[21])
#     #     if row[22] is not None:
#     #         self.pl_timing_corr = pickle.loads(row[22])
#     #     self.pipe_shape = row[23]
#     #     self.pipe_width = row[24]
#     #     self.pipe_height = row[25]
#     #     if row[26] is not None:
#     #         self.pipe_shape_def = pickle.loads(row[26])
#     #     if row[27] is not None:
#     #         self.silt_levels = pickle.loads(row[27])
#     #     self.pipe_shape_intervals = row[28]
#     #     self.file_path = row[29]
#     #     self.rainfall_file_format = row[30]
#     #     self.depth_file_format = row[31]
#     #     self.velocity_file_format = row[32]
#     #     self.battery_file_format = row[33]
#     #     self.pumplogger_file_format = row[34]

#     def from_database_row_dict(self, row_dict:Dict):
#         self.rawdata_id = row_dict.get('rawdata_id')
#         self.install_id = row_dict.get('install_id')
#         self.rg_tb_depth = row_dict.get('rg_tb_depth')

#         if row_dict.get('rg_data') is not None:
#             self.rg_data = pickle.loads(row_dict['rg_data'])

#         if isinstance(row_dict.get('rg_data_start'), str):
#             self.rg_data_start = datetime.fromisoformat(row_dict['rg_data_start'])

#         if isinstance(row_dict.get('rg_data_end'), str):
#             self.rg_data_end = datetime.fromisoformat(row_dict['rg_data_end'])

#         if row_dict.get('rg_timing_corr') is not None:
#             self.rg_timing_corr = pickle.loads(row_dict['rg_timing_corr'])

#         if row_dict.get('dep_data') is not None:
#             self.dep_data = pickle.loads(row_dict.get('dep_data'))

#         if isinstance(row_dict.get('dep_data_start'), str):
#             self.dep_data_start = datetime.fromisoformat(row_dict['dep_data_start'])

#         if isinstance(row_dict.get('dep_data_end'), str):
#             self.dep_data_end = datetime.fromisoformat(row_dict['dep_data_end'])

#         if row_dict.get('dep_corr') is not None:
#             self.dep_corr = pickle.loads(row_dict.get('dep_corr'))

#         if row_dict.get('vel_data') is not None:
#             self.vel_data = pickle.loads(row_dict.get('vel_data'))

#         if isinstance(row_dict.get('vel_data_start'), str):
#             self.vel_data_start = datetime.fromisoformat(row_dict['vel_data_start'])

#         if isinstance(row_dict.get('vel_data_end'), str):
#             self.vel_data_end = datetime.fromisoformat(row_dict['vel_data_end'])

#         if row_dict.get('vel_corr') is not None:
#             self.vel_corr = pickle.loads(row_dict.get('vel_corr'))

#         if row_dict.get('dv_timing_corr') is not None:
#             self.dv_timing_corr = pickle.loads(row_dict.get('dv_timing_corr'))

#         if row_dict.get('bat_data') is not None:
#             self.bat_data = pickle.loads(row_dict.get('bat_data'))

#         if isinstance(row_dict.get('bat_data_start'), str):
#             self.bat_data_start = datetime.fromisoformat(row_dict['bat_data_start'])

#         if isinstance(row_dict.get('bat_data_end'), str):
#             self.bat_data_end = datetime.fromisoformat(row_dict['bat_data_end'])

#         if row_dict.get('pl_data') is not None:
#             self.pl_data = pickle.loads(row_dict.get('pl_data'))

#         if isinstance(row_dict.get('pl_data_start'), str):
#             self.pl_data_start = datetime.fromisoformat(row_dict['pl_data_start'])

#         if isinstance(row_dict.get('pl_data_end'), str):
#             self.pl_data_end = datetime.fromisoformat(row_dict['pl_data_end'])

#         if row_dict.get('pl_timing_corr') is not None:
#             self.pl_timing_corr = pickle.loads(row_dict.get('pl_timing_corr'))

#         if row_dict.get('pl_added_onoffs') is not None:
#             self.pl_added_onoffs = pickle.loads(row_dict.get('pl_added_onoffs'))

#         self.pipe_shape = row_dict.get('pipe_shape')
#         self.pipe_width = row_dict.get('pipe_width')
#         self.pipe_height = row_dict.get('pipe_height')

#         if row_dict.get('pipe_shape_def') is not None:
#             self.pipe_shape_def = pickle.loads(row_dict.get('pipe_shape_def'))

#         if row_dict.get("silt_levels") is not None:
#             self.silt_levels = pickle.loads(row_dict.get('silt_levels'))

#         self.pipe_shape_intervals = row_dict.get('pipe_shape_intervals')
#         self.file_path = row_dict.get('file_path')
#         self.rainfall_file_format = row_dict.get('rainfall_file_format')
#         self.depth_file_format = row_dict.get('depth_file_format')
#         self.velocity_file_format = row_dict.get('velocity_file_format')
#         self.battery_file_format = row_dict.get('battery_file_format')
#         self.pumplogger_file_format = row_dict.get('pumplogger_file_format')

class fsmRawData(object):

    def __init__(self):
        self.rawdata_id: int = 1
        self.install_id: str = ""
        self.rg_tb_depth: float = 0.2
        self.rg_data: Optional[pd.DataFrame] = None
        self.rg_data_start: datetime = datetime.strptime(
            '2172-05-12', '%Y-%m-%d')
        self.rg_data_end: datetime = datetime.strptime(
            '2172-05-12', '%Y-%m-%d')
        self.rg_timing_corr: Optional[pd.DataFrame] = None
        self.dep_data: Optional[pd.DataFrame] = None
        self.dep_data_start: datetime = datetime.strptime(
            '2172-05-12', '%Y-%m-%d')
        self.dep_data_end: datetime = datetime.strptime(
            '2172-05-12', '%Y-%m-%d')
        self.dep_corr: Optional[pd.DataFrame] = None
        self.vel_data: Optional[pd.DataFrame] = None
        self.vel_data_start: datetime = datetime.strptime(
            '2172-05-12', '%Y-%m-%d')
        self.vel_data_end: datetime = datetime.strptime(
            '2172-05-12', '%Y-%m-%d')
        self.vel_corr: Optional[pd.DataFrame] = None
        self.dv_timing_corr: Optional[pd.DataFrame] = None
        self.bat_data: Optional[pd.DataFrame] = None
        self.bat_data_start: datetime = datetime.strptime(
            '2172-05-12', '%Y-%m-%d')
        self.bat_data_end: datetime = datetime.strptime(
            '2172-05-12', '%Y-%m-%d')
        self.pl_data: Optional[pd.DataFrame] = None
        self.pl_data_start: datetime = datetime.strptime(
            '2172-05-12', '%Y-%m-%d')
        self.pl_data_end: datetime = datetime.strptime(
            '2172-05-12', '%Y-%m-%d')
        self.pl_timing_corr: Optional[pd.DataFrame] = None
        self.pl_added_onoffs: Optional[pd.DataFrame] = None
        self.pipe_shape: str = 'CIRC'
        self.pipe_width: int = 225
        self.pipe_height: int = 225
        self.pipe_shape_def: Optional[pd.DataFrame] = None
        self.silt_levels: Optional[pd.DataFrame] = None
        self.pipe_shape_intervals: int = 20
        self.file_path: str = ''
        self.rainfall_file_format: str = '{pmac_id}_02.dat'
        self.depth_file_format: str = '{pmac_id}_06.dat'
        self.velocity_file_format: str = '{pmac_id}_07.dat'
        self.battery_file_format: str = '{pmac_id}_08.dat'
        self.pumplogger_file_format: str = '{pmac_id}.csv'

    def from_database_row_dict(self, row_dict:Dict):
        self.rawdata_id = row_dict.get('rawdata_id')
        self.install_id = row_dict.get('install_id')
        self.rg_tb_depth = row_dict.get('rg_tb_depth')

        if row_dict.get('rg_data') is not None:
            self.rg_data = pickle.loads(row_dict['rg_data'])

        if isinstance(row_dict.get('rg_data_start'), str):
            self.rg_data_start = datetime.fromisoformat(row_dict['rg_data_start'])

        if isinstance(row_dict.get('rg_data_end'), str):
            self.rg_data_end = datetime.fromisoformat(row_dict['rg_data_end'])

        if row_dict.get('rg_timing_corr') is not None:
            self.rg_timing_corr = pickle.loads(row_dict['rg_timing_corr'])

        if row_dict.get('dep_data') is not None:
            self.dep_data = pickle.loads(row_dict.get('dep_data'))

        if isinstance(row_dict.get('dep_data_start'), str):
            self.dep_data_start = datetime.fromisoformat(row_dict['dep_data_start'])

        if isinstance(row_dict.get('dep_data_end'), str):
            self.dep_data_end = datetime.fromisoformat(row_dict['dep_data_end'])

        if row_dict.get('dep_corr') is not None:
            self.dep_corr = pickle.loads(row_dict.get('dep_corr'))

        if row_dict.get('vel_data') is not None:
            self.vel_data = pickle.loads(row_dict.get('vel_data'))

        if isinstance(row_dict.get('vel_data_start'), str):
            self.vel_data_start = datetime.fromisoformat(row_dict['vel_data_start'])

        if isinstance(row_dict.get('vel_data_end'), str):
            self.vel_data_end = datetime.fromisoformat(row_dict['vel_data_end'])

        if row_dict.get('vel_corr') is not None:
            self.vel_corr = pickle.loads(row_dict.get('vel_corr'))

        if row_dict.get('dv_timing_corr') is not None:
            self.dv_timing_corr = pickle.loads(row_dict.get('dv_timing_corr'))

        if row_dict.get('bat_data') is not None:
            self.bat_data = pickle.loads(row_dict.get('bat_data'))

        if isinstance(row_dict.get('bat_data_start'), str):
            self.bat_data_start = datetime.fromisoformat(row_dict['bat_data_start'])

        if isinstance(row_dict.get('bat_data_end'), str):
            self.bat_data_end = datetime.fromisoformat(row_dict['bat_data_end'])

        if row_dict.get('pl_data') is not None:
            self.pl_data = pickle.loads(row_dict.get('pl_data'))

        if isinstance(row_dict.get('pl_data_start'), str):
            self.pl_data_start = datetime.fromisoformat(row_dict['pl_data_start'])

        if isinstance(row_dict.get('pl_data_end'), str):
            self.pl_data_end = datetime.fromisoformat(row_dict['pl_data_end'])

        if row_dict.get('pl_timing_corr') is not None:
            self.pl_timing_corr = pickle.loads(row_dict.get('pl_timing_corr'))

        if row_dict.get('pl_added_onoffs') is not None:
            self.pl_added_onoffs = pickle.loads(row_dict.get('pl_added_onoffs'))

        self.pipe_shape = row_dict.get('pipe_shape')
        self.pipe_width = row_dict.get('pipe_width')
        self.pipe_height = row_dict.get('pipe_height')

        if row_dict.get('pipe_shape_def') is not None:
            self.pipe_shape_def = pickle.loads(row_dict.get('pipe_shape_def'))

        if row_dict.get("silt_levels") is not None:
            self.silt_levels = pickle.loads(row_dict.get('silt_levels'))

        self.pipe_shape_intervals = row_dict.get('pipe_shape_intervals')
        self.file_path = row_dict.get('file_path')
        self.rainfall_file_format = row_dict.get('rainfall_file_format')
        self.depth_file_format = row_dict.get('depth_file_format')
        self.velocity_file_format = row_dict.get('velocity_file_format')
        self.battery_file_format = row_dict.get('battery_file_format')
        self.pumplogger_file_format = row_dict.get('pumplogger_file_format')

# class fsmInspection(object):

#     def __init__(self):
#         self.inspection_id: int = 1
#         self.install_id: int = 0
#         self.inspection_date: datetime = datetime.strptime(
#             '2172-05-12', '%Y-%m-%d')
#         self.inspection_sheet: Optional[bytes] = None
#         self.inspection_sheet_filename: str = ''
#         self.inspection_type: str = ''

#     def from_database_row(self, row):
#         self.inspection_id = row[0]
#         self.install_id = row[1]
#         self.inspection_date = datetime.fromisoformat(row[2])
#         self.inspection_sheet = row[3]
#         self.inspection_sheet_filename = row[4]
#         self.inspection_type = row[5]

class fsmInspection(object):

    def __init__(self):
        self.inspection_id: int = 1
        self.install_id: str = ""
        self.inspection_date: datetime = datetime.strptime(
            '2172-05-12', '%Y-%m-%d')
        self.inspection_sheet: Optional[bytes] = None
        self.inspection_sheet_filename: str = ''
        self.inspection_type: str = ''

    # def from_database_row(self, row):
    #     self.inspection_id = row[0]
    #     self.install_id = row[1]
    #     self.inspection_date = datetime.fromisoformat(row[2])
    #     self.inspection_sheet = row[3]
    #     self.inspection_sheet_filename = row[4]
    #     self.inspection_type = row[5]

    def from_database_row_dict(self, row_dict:Dict):

        self.inspection_id = row_dict.get('inspection_id')
        self.install_id = row_dict.get('install_id')
        if isinstance(row_dict.get("inspection_date"), str):
            self.inspection_date = datetime.fromisoformat(row_dict['inspection_date'])
        if row_dict.get("inspection_sheet") in (None, b''):
            self.inspection_sheet = None
        else:
            self.inspection_sheet = row_dict["inspection_sheet"]            
        self.inspection_sheet_filename = row_dict.get('inspection_sheet_filename')
        self.inspection_type = row_dict.get('inspection_type')

class fsmSite(object):

    def __init__(self):
        self.siteID: str = ''
        self.siteType: str = 'Flow Monitor'
        self.address: str = ''
        self.mh_ref: str = ''
        self.w3w: str = ''
        self.easting: float = 0.0
        self.northing: float = 0.0

    # def from_database_row(self, row):
    #     self.siteID = row[0]
    #     self.siteType = row[1]
    #     self.address = row[2]
    #     self.mh_ref = row[3]
    #     self.w3w = row[4]
    #     self.easting = row[5]
    #     self.northing = row[6]

    def from_database_row_dict(self, row_dict:Dict):
        self.siteID = row_dict.get('siteID')
        self.siteType = row_dict.get('siteType')
        self.address = row_dict.get('address')
        self.mh_ref = row_dict.get('mh_ref')
        self.w3w = row_dict.get('w3w')
        self.easting = row_dict.get('easting')
        self.northing = row_dict.get('northing')


class fsmInterim(object):

    def __init__(self):
        self.interimID: int = 1
        self.interim_start_date: datetime = datetime.strptime(
            '2172-05-12', '%Y-%m-%d')
        self.interim_end_date: datetime = datetime.strptime(
            '2172-05-12', '%Y-%m-%d')
        self.data_import_complete: bool = False
        self.site_inspection_review_complete: bool = False
        self.fm_data_review_complete: bool = False
        self.rg_data_review_complete: bool = False
        self.pl_data_review_complete: bool = False
        self.data_classification_complete: bool = False
        self.report_complete: bool = False
        self.identify_events_complete: bool = False
        self.interim_summary_text: str = ''

    # def from_database_row(self, row):

    #     self.interimID = row[0]
    #     self.interim_start_date = datetime.fromisoformat(row[1])
    #     self.interim_end_date = datetime.fromisoformat(row[2])
    #     self.data_import_complete = bool(row[3])
    #     self.site_inspection_review_complete = bool(row[4])
    #     self.fm_data_review_complete = bool(row[5])
    #     self.rg_data_review_complete = bool(row[6])
    #     self.pl_data_review_complete = bool(row[7])
    #     self.data_classification_complete = bool(row[8])
    #     self.report_complete = bool(row[9])
    #     self.identify_events_complete = bool(row[10])
    #     self.interim_summary_text = row[11]

    def from_database_row_dict(self, row_dict:Dict):

        self.interimID = row_dict.get('interimID')
        if isinstance(row_dict.get('interim_start_date'), str):
            self.interim_start_date = datetime.fromisoformat(row_dict['interim_start_date'])
        if isinstance(row_dict.get('interim_end_date'), str):
            self.interim_end_date = datetime.fromisoformat(row_dict['interim_end_date'])
        self.data_import_complete = bool(row_dict.get('data_import_complete'))
        self.site_inspection_review_complete = bool(row_dict.get('site_inspection_review_complete'))
        self.fm_data_review_complete = bool(row_dict.get('fm_data_review_complete'))
        self.rg_data_review_complete = bool(row_dict.get('rg_data_review_complete'))
        self.pl_data_review_complete = bool(row_dict.get('pl_data_review_complete'))
        self.data_classification_complete = bool(row_dict.get('data_classification_complete'))
        self.report_complete = bool(row_dict.get('report_complete'))
        self.identify_events_complete = bool(row_dict.get('identify_events_complete'))
        self.interim_summary_text = row_dict.get('interim_summary_text')


class fsmInterimReview(object):

    def __init__(self):
        self.interim_review_id: int = 1
        self.interim_id: int = None
        self.install_id: str = None
        self.dr_data_covered: bool = False
        self.dr_ignore_missing: bool = False
        self.dr_reason_missing: str = ''
        self.dr_identifier: str = ''
        self.cr_complete: bool = False
        self.cr_comment: str = ''
        self.ser_complete: bool = False
        self.ser_comment: str = ''
        self.fm_complete: bool = False
        self.fm_comment: str = ''
        self.rg_complete: bool = False
        self.rg_comment: str = ''
        self.pl_complete: bool = False
        self.pl_comment: str = ''        

    # def from_database_row(self, row):

    #     self.interim_review_id = row[0]
    #     self.interim_id = row[1]
    #     self.install_id = row[2]
    #     self.dr_data_covered = bool(row[3])
    #     self.dr_ignore_missing = bool(row[4])
    #     self.dr_reason_missing = row[5]
    #     self.dr_identifier = row[6]
    #     self.cr_complete = bool(row[7])
    #     self.cr_comment = row[8]
    #     self.ser_complete = bool(row[9])
    #     self.ser_comment = row[10]
    #     self.fm_complete = bool(row[11])
    #     self.fm_comment = row[12]
    #     self.rg_complete = bool(row[13])
    #     self.rg_comment = row[14]
    #     self.pl_complete = bool(row[15])
    #     self.pl_comment = row[16]

    def from_database_row_dict(self, row_dict:Dict):

        self.interim_review_id = row_dict.get('interim_review_id')
        self.interim_id = row_dict.get('interim_id')
        self.install_id = row_dict.get('install_id')
        self.dr_data_covered = bool(row_dict.get('dr_data_covered'))
        self.dr_ignore_missing = bool(row_dict.get('dr_ignore_missing'))
        self.dr_reason_missing = row_dict.get('dr_reason_missing')
        self.dr_identifier = row_dict.get('dr_identifier')
        self.cr_complete = bool(row_dict.get('cr_complete'))
        self.cr_comment = row_dict.get('cr_comment')
        self.ser_complete = bool(row_dict.get('ser_complete'))
        self.ser_comment = row_dict.get('ser_comment')
        self.fm_complete = bool(row_dict.get('fm_complete'))
        self.fm_comment = row_dict.get('fm_comment')
        self.rg_complete = bool(row_dict.get('rg_complete'))
        self.rg_comment = row_dict.get('rg_comment')
        self.pl_complete = bool(row_dict.get('pl_complete'))
        self.pl_comment = row_dict.get('pl_comment')

class fsmInstallPictures(object):

    def __init__(self):
        self.picture_id: int
        self.install_id: int
        self.picture_taken_date: datetime = datetime.strptime(
            '1972-05-12', '%Y-%m-%d')
        self.picture_type: str = ''
        self.picture_comment: str = ''
        self.picture: Optional[bytes] = None

    # def from_database_row(self, row):
    #     self.picture_id = row[0]
    #     self.install_id = row[1]
    #     self.picture_taken_date = datetime.fromisoformat(row[2])
    #     self.picture_type = row[3]
    #     self.picture_comment = row[4]
    #     self.picture = row[5]

    def from_database_row_dict(self, row_dict:Dict):

        self.picture_id = row_dict.get('picture_id')
        self.install_id = row_dict.get('install_id')
        self.picture_taken_date = datetime.fromisoformat(row[2])
        if isinstance(row_dict.get('picture_taken_date'), str):
            self.picture_taken_date = datetime.fromisoformat(row_dict['picture_taken_date'])
        self.picture_type = row_dict.get('picture_type')
        self.picture_comment = row_dict.get('picture_comment')
        if row_dict.get("picture") in (None, b''):
            self.picture = None
        else:
            self.picture = row_dict["picture"]

# class fsmInterimDataReview(object):

#     def __init__(self):
#         self.interim_data_review_id: int = 1
#         self.interim_id: int = None
#         self.install_id: int = None
#         self.data_covered: bool = False
#         self.ignore_missing: bool = False
#         self.reason_missing: str = ''
#         self.identifier: str = ''

#     def from_database_row(self, row):

#         self.interim_data_review_id = row[0]
#         self.interim_id = row[1]
#         self.install_id = row[2]
#         self.data_covered = bool(row[3])
#         self.ignore_missing = bool(row[4])
#         self.reason_missing = row[5]
#         self.identifier = row[6]

# class fsmInterimClassificationReview(object):

#     def __init__(self):
#         self.interim_class_review_id: int = 1
#         self.interim_id: int = None
#         self.install_id: int = None
#         self.complete: bool = False
#         self.review_comment: str = ''

#     def from_database_row(self, row):

#         self.interim_class_review_id = row[0]
#         self.interim_id = row[1]
#         self.install_id = row[2]
#         self.complete = bool(row[3])
#         self.review_comment = row[4]


class fsmStormEvent(object):

    def __init__(self):
        self.storm_event_id: str = ''
        self.se_start: datetime = datetime.strptime('2172-05-12', '%Y-%m-%d')
        self.se_end: datetime = datetime.strptime('2172-05-12', '%Y-%m-%d')

    # def from_database_row(self, row):

    #     self.storm_event_id = row[0]
    #     self.se_start = datetime.fromisoformat(row[1])
    #     self.se_end = datetime.fromisoformat(row[2])

    def from_database_row_dict(self, row_dict:Dict):

        self.storm_event_id = row_dict.get('storm_event_id')
        self.se_start = datetime.fromisoformat(row[1])
        self.se_end = datetime.fromisoformat(row[2])
        if isinstance(row_dict.get('se_start'), str):
            self.se_start = datetime.fromisoformat(row_dict['se_start'])
        if isinstance(row_dict.get('se_end'), str):
            self.se_end = datetime.fromisoformat(row_dict['se_end'])

# class fsmClassification(object):

#     def __init__(self):
#         self.class_id: int = 1
#         self.monitor_asset_id: str = ''
#         self.class_data_ml: Optional[pd.DataFrame] = None
#         self.class_data_user: Optional[pd.DataFrame] = None
#         # self.class_date: datetime = datetime.strptime('2172-05-12', '%Y-%m-%d')
#         # self.class_value_ml: str = ''
#         # self.class_confidence_ml: float = 0.0
#         # self.class_value_user: str = ''

#     def from_database_row(self, row):

#         self.class_id = row[0]
#         self.monitor_asset_id = row[1]
#         if row[2] is not None:
#             self.class_data_ml = pickle.loads(row[2])
#         if row[3] is not None:
#             self.class_data_user = pickle.loads(row[3])
#         # self.class_date = datetime.fromisoformat(row[2])
#         # self.class_value_ml = row[3]
#         # self.class_confidence_ml = row[4]
#         # self.class_value_user = row[5]


class fsmProject(object):

    def __init__(self):
        self.job_number: str = ''
        self.job_name: str = ''
        self.client: str = ''
        self.client_job_ref: str = ''
        self.survey_start_date: Optional[datetime] = None
        self.survey_end_date: Optional[datetime] = None
        self.survey_complete: bool = False
        self.dict_fsm_sites: Dict[str, fsmSite] = {}
        self.dict_fsm_monitors: Dict[str, fsmMonitor] = {}
        self.dict_fsm_installs: Dict[str, fsmInstall] = {}
        self.dict_fsm_rawdata: Dict[int, fsmRawData] = {}
        self.dict_fsm_inspections: Dict[int, fsmInspection] = {}
        self.dict_fsm_interims: Dict[int, fsmInterim] = {}
        self.dict_fsm_interim_reviews: Dict[int, fsmInterimReview] = {}
        # self.dict_fsm_interim_data_reviews: Dict[int, fsmInterimDataReview] = {}
        # self.dict_fsm_classifications: Dict[int, fsmClassification] = {}
        # self.dict_fsm_interim_class_reviews: Dict[int, fsmInterimClassificationReview] = {}
        self.dict_fsm_stormevents: Dict[str, fsmStormEvent] = {}
        self.dict_fsm_install_pictures: Dict[int, fsmInstallPictures] = {}

    def read_from_database(self, conn: sqlite3.Connection):
        c = conn.cursor()
        try:
            c.execute(f"SELECT * FROM {Tables.FSM_PROJECT}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.FSM_PROJECT}' does not exist.")
            return  # Return without attempting to fetch rows

        rows = c.fetchall()
        for row in rows:
            column_names = [description[0] for description in c.description]
            row_dict = dict(zip(column_names, row))

        self.from_database_row_dict(row_dict)

        try:
            c.execute(f"SELECT * FROM {Tables.FSM_SITE}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.FSM_SITE}' does not exist.")
            return  # Return without attempting to fetch rows

        rows = c.fetchall()
        for row in rows:
            column_names = [description[0] for description in c.description]
            row_dict = dict(zip(column_names, row))            
            site = fsmSite()
            site.from_database_row_dict(row_dict)
            self.dict_fsm_sites[site.siteID] = site

        try:
            c.execute(f"SELECT * FROM {Tables.FSM_MONITOR}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.FSM_MONITOR}' does not exist.")
            return  # Return without attempting to fetch rows

        rows = c.fetchall()
        for row in rows:
            column_names = [description[0] for description in c.description]
            row_dict = dict(zip(column_names, row))                
            mon = fsmMonitor()
            mon.from_database_row_dict(row_dict)
            # mon.from_database_row(row)
            self.dict_fsm_monitors[mon.monitor_asset_id] = mon

        try:
            c.execute(f"SELECT * FROM {Tables.FSM_INSTALL}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.FSM_INSTALL}' does not exist.")
            return  # Return without attempting to fetch rows

        # rows = c.fetchall()
        # for row in rows:
        #     inst = fsmInstall()
        #     inst.from_database_row(row)
        #     self.dict_fsm_installs[inst.install_id] = inst

        rows = c.fetchall()
        for row in rows:
            column_names = [description[0] for description in c.description]
            row_dict = dict(zip(column_names, row))
            inst = fsmInstall()
            inst.from_database_row_dict(row_dict)
            self.dict_fsm_installs[inst.install_id] = inst

        try:
            c.execute(f"SELECT * FROM {Tables.FSM_RAWDATA}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.FSM_RAWDATA}' does not exist.")
            return  # Return without attempting to fetch rows

        # rows = c.fetchall()
        # for row in rows:
        #     raw = fsmRawData()
        #     raw.from_database_row(row)
        #     self.dict_fsm_rawdata[raw.rawdata_id] = raw
        rows = c.fetchall()
        for row in rows:
            column_names = [description[0] for description in c.description]
            row_dict = dict(zip(column_names, row))
            rawdata = fsmRawData()
            rawdata.from_database_row_dict(row_dict)
            self.dict_fsm_rawdata[rawdata.rawdata_id] = rawdata

        try:
            c.execute(f"SELECT * FROM {Tables.FSM_INTERIM}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.FSM_INTERIM}' does not exist.")
            return  # Return without attempting to fetch rows

        rows = c.fetchall()
        for row in rows:
            column_names = [description[0] for description in c.description]
            row_dict = dict(zip(column_names, row))                
            interim = fsmInterim()
            interim.from_database_row_dict(row_dict)
            self.dict_fsm_interims[interim.interimID] = interim

        try:
            c.execute(f"SELECT * FROM {Tables.FSM_INTERIM_REVIEW}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.FSM_INTERIM_REVIEW}' does not exist.")
            return  # Return without attempting to fetch rows

        rows = c.fetchall()
        for row in rows:
            column_names = [description[0] for description in c.description]
            row_dict = dict(zip(column_names, row))               
            interim_rev = fsmInterimReview()
            interim_rev.from_database_row_dict(row_dict)
            self.dict_fsm_interim_reviews[interim_rev.interim_review_id] = interim_rev

        try:
            c.execute(f"SELECT * FROM {Tables.FSM_STORMEVENTS}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.FSM_STORMEVENTS}' does not exist.")
            return  # Return without attempting to fetch rows

        rows = c.fetchall()
        for row in rows:
            column_names = [description[0] for description in c.description]
            row_dict = dict(zip(column_names, row))                
            storm_event = fsmStormEvent()
            storm_event.from_database_row_dict(row_dict)
            self.dict_fsm_stormevents[storm_event.storm_event_id] = storm_event

        try:
            c.execute(f"SELECT * FROM {Tables.FSM_INSPECTIONS}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.FSM_INSPECTIONS}' does not exist.")
            return  # Return without attempting to fetch rows

        rows = c.fetchall()
        for row in rows:
            column_names = [description[0] for description in c.description]
            row_dict = dict(zip(column_names, row))            
            insp = fsmInspection()
            insp.from_database_row_dict(row_dict)
            self.dict_fsm_inspections[insp.inspection_id] = insp

        try:
            c.execute(f"SELECT * FROM {Tables.FSM_INSTALLPICTURES}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.FSM_INSPECTIONS}' does not exist.")
            return  # Return without attempting to fetch rows

        rows = c.fetchall()
        for row in rows:
            column_names = [description[0] for description in c.description]
            row_dict = dict(zip(column_names, row))
            inst_pic = fsmInstallPictures()
            inst_pic.from_database_row_dict(row_dict)
            self.dict_fsm_install_pictures[inst_pic.picture_id] = inst_pic

    # def from_database_row(self, row):
    #     self.job_number = row[0]
    #     self.job_name = row[1]
    #     self.client = row[2]
    #     self.client_job_ref = row[3]
    #     self.survey_start_date = datetime.fromisoformat(row[4])
    #     self.survey_end_date = datetime.fromisoformat(row[5])
    #     self.survey_complete = bool(row[6])

    def from_database_row_dict(self, row_dict:Dict):

        self.job_number = row_dict.get('job_number')
        self.job_name = row_dict.get('job_name')
        self.client = row_dict.get('client')
        self.client_job_ref = row_dict.get('client_job_ref')
        if isinstance(row_dict.get('survey_start_date'), str):
            self.survey_start_date = datetime.fromisoformat(row_dict['survey_start_date'])
        if isinstance(row_dict.get('survey_end_date'), str):
            self.survey_end_date = datetime.fromisoformat(row_dict['survey_end_date'])
        self.survey_complete = bool(row_dict.get('survey_complete'))

    def write_to_database(self, conn: sqlite3.Connection) -> bool:
        result = False

        try:
            # Drop existing tables to clear old data
            conn.execute(f"DROP TABLE IF EXISTS {Tables.FSM_PROJECT}")
            conn.execute(f"DROP TABLE IF EXISTS {Tables.FSM_SITE}")
            conn.execute(f"DROP TABLE IF EXISTS {Tables.FSM_MONITOR}")
            conn.execute(f"DROP TABLE IF EXISTS {Tables.FSM_INSTALL}")
            conn.execute(f"DROP TABLE IF EXISTS {Tables.FSM_INTERIM}")
            conn.execute(f"DROP TABLE IF EXISTS {Tables.FSM_INTERIM_REVIEW}")
            conn.execute(f"DROP TABLE IF EXISTS {Tables.FSM_STORMEVENTS}")
            conn.execute(f"DROP TABLE IF EXISTS {Tables.FSM_INSPECTIONS}")
            conn.execute(f"DROP TABLE IF EXISTS {Tables.FSM_INSTALLPICTURES}")
            conn.execute(f"DROP TABLE IF EXISTS {Tables.FSM_RAWDATA}")

            # conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.FSM_PROJECT} (
            #                 job_number TEXT PRIMARY KEY,
            #                 job_name TEXT,
            #                 client TEXT,
            #                 client_job_ref TEXT,
            #                 survey_start_date TEXT,
            #                 survey_end_date TEXT,
            #                 survey_complete INTEGER
            #             )''')
            # conn.execute(f'''INSERT OR REPLACE INTO {Tables.FSM_PROJECT} VALUES (?, ?, ?, ?, ?, ?, ?)''',
            #              (self.job_number, self.job_name, self.client, self.client_job_ref,
            #               self.survey_start_date.isoformat(), self.survey_end_date.isoformat(), self.survey_complete))

            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.FSM_PROJECT} (
                            job_number TEXT PRIMARY KEY,
                            job_name TEXT,
                            client TEXT,
                            client_job_ref TEXT,
                            survey_start_date TEXT,
                            survey_end_date TEXT,
                            survey_complete INTEGER
                        )''')
            conn.execute(f'''INSERT OR REPLACE INTO {Tables.FSM_PROJECT} VALUES (?, ?, ?, ?, ?, ?, ?)''',
                         (self.job_number, self.job_name, self.client, self.client_job_ref,
                          self.survey_start_date.isoformat(), self.survey_end_date.isoformat(), self.survey_complete))
            
            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.FSM_SITE} (
                            siteID TEXT PRIMARY KEY,
                            siteType TEXT,
                            address TEXT,
                            mh_ref TEXT,
                            w3w TEXT,
                            easting REAL,
                            northing REAL
                        )''')
            for site in self.dict_fsm_sites.values():
                conn.execute(f'''INSERT OR REPLACE INTO {Tables.FSM_SITE} VALUES (?, ?, ?, ?, ?, ?, ?)''',
                             (site.siteID, site.siteType, site.address, site.mh_ref, site.w3w, site.easting, site.northing))

            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.FSM_MONITOR} (
                            monitor_asset_id TEXT PRIMARY KEY,
                            monitor_type TEXT,
                            pmac_id TEXT,
                            monitor_sub_type TEXT
                        )''')
            for mon in self.dict_fsm_monitors.values():
                conn.execute(f'''INSERT OR REPLACE INTO {Tables.FSM_MONITOR} VALUES (?, ?, ?, ?)''',
                             (mon.monitor_asset_id, mon.monitor_type, mon.pmac_id, mon.monitor_sub_type))

            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.FSM_INSTALL} (
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
            for inst in self.dict_fsm_installs.values():
                conn.execute(f'''INSERT OR REPLACE INTO {Tables.FSM_INSTALL} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (inst.install_id,  inst.install_site_id, inst.install_monitor_asset_id, inst.install_type,
                              inst.client_ref, inst.install_date.isoformat(
                              ), inst.remove_date.isoformat(), inst.fm_pipe_letter,
                              inst.fm_pipe_shape, int(inst.fm_pipe_height_mm), int(
                                  inst.fm_pipe_width_mm),
                              int(inst.fm_pipe_depth_to_invert_mm), int(
                                  inst.fm_sensor_offset_mm), inst.rg_position,
                              pickle.dumps(inst.data), inst.data_start.isoformat(
                              ), inst.data_end.isoformat(),
                              inst.data_interval, inst.data_date_updated.isoformat(
                              ), inst.install_sheet, inst.install_sheet_filename,
                              pickle.dumps(
                                  inst.class_data_ml), inst.class_data_ml_date_updated.isoformat(),
                              pickle.dumps(inst.class_data_user), inst.class_data_user_date_updated.isoformat()))

            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.FSM_INTERIM} (
                            interim_id INTEGER PRIMARY KEY,
                            interim_start_date TEXT,
                            interim_end_date TEXT,
                            data_import_complete INTEGER,
                            site_inspection_review_complete INTEGER,
                            fm_data_review_complete INTEGER,
                            rg_data_review_complete INTEGER,
                            pl_data_review_complete INTEGER,
                            data_classification_complete INTEGER,
                            report_complete INTEGER,
                            identify_events_complete INTEGER,
                            interim_summary_text TEXT
                        )''')
            for a_int in self.dict_fsm_interims.values():
                conn.execute(f'''INSERT OR REPLACE INTO {Tables.FSM_INTERIM} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (a_int.interimID, a_int.interim_start_date.isoformat(), a_int.interim_end_date.isoformat(),
                              int(a_int.data_import_complete), int(
                                  a_int.site_inspection_review_complete),
                              int(a_int.fm_data_review_complete), int(
                                  a_int.rg_data_review_complete), int(a_int.pl_data_review_complete),
                              int(a_int.data_classification_complete), int(
                                  a_int.report_complete), int(a_int.identify_events_complete),
                              a_int.interim_summary_text))

            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.FSM_INTERIM_REVIEW} (
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
            for a_int_rev in self.dict_fsm_interim_reviews.values():
                conn.execute(f'''INSERT OR REPLACE INTO {Tables.FSM_INTERIM_REVIEW} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (int(a_int_rev.interim_review_id), int(a_int_rev.interim_id), a_int_rev.install_id,
                              int(a_int_rev.dr_data_covered), int(
                                  a_int_rev.dr_ignore_missing), a_int_rev.dr_reason_missing,
                              a_int_rev.dr_identifier, int(
                                  a_int_rev.cr_complete), a_int_rev.cr_comment,
                              int(a_int_rev.ser_complete), a_int_rev.ser_comment,
                              int(a_int_rev.fm_complete), a_int_rev.fm_comment,
                              int(a_int_rev.rg_complete), a_int_rev.rg_comment,
                              int(a_int_rev.pl_complete), a_int_rev.pl_comment))

            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.FSM_STORMEVENTS} (
                            storm_event_id TEXT PRIMARY KEY,
                            se_start TEXT,
                            se_end TEXT
                         )''')
            for a_se in self.dict_fsm_stormevents.values():
                conn.execute(f'''INSERT OR REPLACE INTO {Tables.FSM_STORMEVENTS} VALUES (?, ?, ?)''',
                             (a_se.storm_event_id, a_se.se_start.isoformat(), a_se.se_end.isoformat()))

            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.FSM_INSPECTIONS} (
                            inspection_id INTEGER PRIMARY KEY,
                            install_id TEXT,
                            inspection_date TEXT,
                            inspection_sheet BLOB,
                            inspection_sheet_filename TEXT,
                            inspection_type TEXT
                        )''')

            for insp in self.dict_fsm_inspections.values():
                conn.execute(f'''INSERT OR REPLACE INTO {Tables.FSM_INSPECTIONS} VALUES (?, ?, ?, ?, ?, ?)''',
                             (int(insp.inspection_id), insp.install_id, insp.inspection_date.isoformat(),
                              insp.inspection_sheet, insp.inspection_sheet_filename, insp.inspection_type))

            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.FSM_INSTALLPICTURES} (
                            picture_id INTEGER PRIMARY KEY,
                            install_id TEXT,
                            picture_taken_date TEXT,
                            picture_type TEXT,
                            picture_comment TEXT,
                            picture BLOB
                        )''')
            for in_pic in self.dict_fsm_install_pictures.values():
                conn.execute(f'''INSERT OR REPLACE INTO {Tables.FSM_INSTALLPICTURES} VALUES (?, ?, ?, ?, ?, ?)''',
                             (int(in_pic.picture_id), in_pic.install_id, in_pic.picture_taken_date.isoformat(),
                              in_pic.picture_type, in_pic.picture_comment, in_pic.picture))

            conn.execute(
                f"""CREATE TABLE IF NOT EXISTS {Tables.FSM_RAWDATA} (
                            rawdata_id INTEGER PRIMARY KEY,
                            install_id TEXT,
                            rg_tb_depth REAL,
                            rg_data BLOB,
                            rg_data_start TEXT,
                            rg_data_end TEXT,
                            rg_timing_corr BLOB,
                            dep_data BLOB,
                            dep_data_start TEXT,
                            dep_data_end TEXT,
                            dep_corr BLOB,
                            vel_data BLOB,
                            vel_data_start TEXT,
                            vel_data_end TEXT,
                            vel_corr BLOB,
                            dv_timing_corr BLOB,
                            bat_data BLOB,
                            bat_data_start TEXT,
                            bat_data_end TEXT,
                            pl_data BLOB,
                            pl_data_start TEXT,
                            pl_data_end TEXT,
                            pl_timing_corr BLOB,
                            pl_added_onoffs BLOB,
                            pipe_shape TEXT,
                            pipe_width INTEGER,
                            pipe_height INTEGER,
                            pipe_shape_def BLOB,
                            silt_levels BLOB,
                            pipe_shape_intervals INTEGER,
                            file_path TEXT,
                            rainfall_file_format TEXT,
                            depth_file_format TEXT,
                            velocity_file_format TEXT,
                            battery_file_format TEXT,
                            pumplogger_file_format TEXT
                        )"""
            )

            for rawdata in self.dict_fsm_rawdata.values():
                conn.execute(
                    f"""INSERT OR REPLACE INTO {Tables.FSM_RAWDATA} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        int(rawdata.rawdata_id),
                        rawdata.install_id,
                        float(rawdata.rg_tb_depth),
                        pickle.dumps(rawdata.rg_data),
                        rawdata.rg_data_start.isoformat(),
                        rawdata.rg_data_end.isoformat(),
                        pickle.dumps(rawdata.rg_timing_corr),
                        pickle.dumps(rawdata.dep_data),
                        rawdata.dep_data_start.isoformat(),
                        rawdata.dep_data_end.isoformat(),
                        pickle.dumps(rawdata.dep_corr),
                        pickle.dumps(rawdata.vel_data),
                        rawdata.vel_data_start.isoformat(),
                        rawdata.vel_data_end.isoformat(),
                        pickle.dumps(rawdata.vel_corr),
                        pickle.dumps(rawdata.dv_timing_corr),
                        pickle.dumps(rawdata.bat_data),
                        rawdata.bat_data_start.isoformat(),
                        rawdata.bat_data_end.isoformat(),
                        pickle.dumps(rawdata.pl_data),
                        rawdata.pl_data_start.isoformat(),
                        rawdata.pl_data_end.isoformat(),
                        pickle.dumps(rawdata.pl_timing_corr),
                        pickle.dumps(rawdata.pl_added_onoffs),
                        rawdata.pipe_shape,
                        int(rawdata.pipe_width),
                        int(rawdata.pipe_height),
                        pickle.dumps(rawdata.pipe_shape_def),
                        pickle.dumps(rawdata.silt_levels),
                        int(rawdata.pipe_shape_intervals),
                        rawdata.file_path,
                        rawdata.rainfall_file_format,
                        rawdata.depth_file_format,
                        rawdata.velocity_file_format,
                        rawdata.battery_file_format,
                        rawdata.pumplogger_file_format,
                    ),
                )
            conn.commit()

            result = True

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            msg = QMessageBox()
            msg.critical(None, 'Save Project',
                         f"Database error: {e}", QMessageBox.Ok)
            conn.rollback()
        except Exception as e:
            msg = QMessageBox()
            msg.critical(None, 'Save Project',
                         f"Exception in _query: {e}", QMessageBox.Ok)
            print(f"Exception in _query: {e}")
            conn.rollback()
        finally:
            return result
        #     conn.close()

    def add_site(self, objSite: fsmSite) -> bool:

        if objSite.siteID not in self.dict_fsm_sites:
            self.dict_fsm_sites[objSite.siteID] = objSite
            return True
        return False

    def get_site(self, site_id: str) -> Optional[fsmSite]:

        if site_id in self.dict_fsm_sites:
            return self.dict_fsm_sites[site_id]

    def remove_site(self, siteID: str):

        if siteID in self.dict_fsm_sites:
            self.dict_fsm_sites.pop(siteID)

    def add_monitor(self, objMon: fsmMonitor) -> bool:

        if objMon.monitor_asset_id not in self.dict_fsm_monitors:
            self.dict_fsm_monitors[objMon.monitor_asset_id] = objMon
            return True
        return False

    def get_monitor(self, monitor_id: str) -> Optional[fsmMonitor]:

        if monitor_id in self.dict_fsm_monitors:
            return self.dict_fsm_monitors[monitor_id]

    def remove_monitor(self, monitor_id: str):

        if monitor_id in self.dict_fsm_monitors:
            self.dict_fsm_monitors.pop(monitor_id)

    def delete_install(self, install_id: str) -> bool:
        """Remove an install record by its ID."""
        if install_id in self.dict_fsm_installs:
            self.delete_inspections_by_install_id(install_id)
            self.delete_install_pictures_by_install_id(install_id)
            self.delete_interim_reviews_by_install_id(install_id)
            del self.dict_fsm_installs[install_id]
            return True
        return False

    def delete_inspections_by_install_id(self, install_id: str):
        # Collect keys to delete
        keys_to_delete = []
        for inspection_id, inspection in self.dict_fsm_inspections.items():
            if inspection.install_id == install_id:
                keys_to_delete.append(inspection_id)

        # Delete collected keys
        for key in keys_to_delete:
            del self.dict_fsm_inspections[key]

    def delete_install_pictures_by_install_id(self, install_id: str):
        # Collect keys to delete
        keys_to_delete = []
        for picture_id, install_picture in self.dict_fsm_install_pictures.items():
            if install_picture.install_id == install_id:
                keys_to_delete.append(picture_id)

        # Delete collected keys
        for key in keys_to_delete:
            del self.dict_fsm_install_pictures[key]

    def delete_interim_reviews_by_install_id(self, install_id: str):
        # Collect keys to delete
        keys_to_delete = []
        for interim_review_id, interim_review in self.dict_fsm_interim_reviews.items():
            if interim_review.install_id == install_id:
                keys_to_delete.append(interim_review_id)

        # Delete collected keys
        for key in keys_to_delete:
            del self.dict_fsm_interim_reviews[key]

    # def get_installed_monitor(self, site_id: str) -> Optional[fsmMonitor]:
    #     if site_id in self.dict_fsm_sites:
    #         for monitor_id, monitor in self.dict_fsm_monitors.items():
    #             if monitor.install_site == site_id:
    #                 return monitor

    def get_available_monitor_id_list(self, mon_types: List[str]) -> List[str]:

        all_monitor_ids = set(monitor_id for monitor_id, monitor in self.dict_fsm_monitors.items()
                              if monitor.monitor_type in mon_types)
        # installed_monitor_ids = set(install.install_monitor_asset_id for install in self.dict_fsm_installs.values())
        installed_monitor_ids = {install.install_monitor_asset_id for install in self.dict_fsm_installs.values() if install.install_date >= install.remove_date or install.remove_date is None}
        uninstalled_monitor_ids = all_monitor_ids - installed_monitor_ids
        return sorted(uninstalled_monitor_ids)

    def get_available_site_id_list(self, site_type) -> List[str]:

        all_site_ids = set(site_id for site_id, site in self.dict_fsm_sites.items(
        ) if site.siteType == site_type)
        return sorted(all_site_ids)
        # # installed_site_ids = set(
        # #     install.install_site_id for install in self.dict_fsm_installs.values())
        # installed_site_ids = {install.install_site_id for install in self.dict_fsm_installs.values() if install.install_date >= install.remove_date or install.remove_date is None}
        # uninstalled_site_ids = all_site_ids - installed_site_ids
        # return sorted(uninstalled_site_ids)

    # def get_next_install_id(self) -> str:
    #     if self.dict_fsm_installs:
    #         return max(self.dict_fsm_installs.keys()) + 1
    #     else:
    #         return 1

    def get_next_inspection_id(self) -> int:
        if self.dict_fsm_inspections:
            return max(self.dict_fsm_inspections.keys()) + 1
        else:
            return 1

    def get_install_by_monitor(self, monitor_id: str) -> Optional[fsmInstall]:
        for install in self.dict_fsm_installs.values():
            if install.install_monitor_asset_id == monitor_id:
                return install

    def get_current_install_by_monitor(self, monitor_id: str) -> Optional[fsmInstall]:
        for install in self.dict_fsm_installs.values():
            if install.install_monitor_asset_id == monitor_id:
                if install.install_date > install.remove_date:
                    return install

    # def get_install_by_interim_cr(self, interim_cr_id: int) -> Optional[fsmInstall]:
    #     for install in self.dict_fsm_installs.values():
    #         if install.install_monitor_asset_id == monitor_id:
    #             return install

    def get_install_by_site(self, site_id: str) -> Optional[fsmInstall]:
        for install in self.dict_fsm_installs.values():
            if install.install_site_id == site_id:
                return install

    def get_current_install_by_site(self, site_id: str) -> Optional[fsmInstall]:

        for install in self.dict_fsm_installs.values():
            if install.install_site_id == site_id:
                if install.install_date > install.remove_date:
                    return install

    def add_interim(self, objInt: fsmInterim) -> bool:

        if objInt.interimID not in self.dict_fsm_interims:
            self.dict_fsm_interims[objInt.interimID] = objInt
            return True
        return False

    def get_next_interim_id(self) -> int:
        if self.dict_fsm_interims:
            return max(self.dict_fsm_interims.keys()) + 1
        else:
            return 1

    def get_interim(self, interim_id: int) -> Optional[fsmInterim]:

        if interim_id in self.dict_fsm_interims:
            return self.dict_fsm_interims[interim_id]

    def get_next_interim_date(self) -> Optional[datetime]:
        if self.dict_fsm_interims:
            next_int_id = self.get_next_interim_id()
            if next_int_id > 1:
                prev_int_id = next_int_id - 1
                return self.dict_fsm_interims[prev_int_id].interim_end_date
            else:
                return self.survey_start_date
        else:
            return self.survey_start_date

    def get_interim_review(self, interim_review_id: Optional[int] = None, interim_id: Optional[int] = None, install_id: Optional[int] = None) -> Optional[fsmInterimReview]:
        if interim_review_id is not None:
            # Case 1: interim_review_id is provided
            return self.dict_fsm_interim_reviews.get(interim_review_id)
        elif interim_id is not None and install_id is not None:
            # Case 2: interim_id and site_id are provided
            for a_int_rev in self.dict_fsm_interim_reviews.values():
                if a_int_rev.interim_id == interim_id and a_int_rev.install_id == install_id:
                    return a_int_rev
        return None

    def get_next_interim_review_id(self):
        if self.dict_fsm_interim_reviews:
            return max(self.dict_fsm_interim_reviews.keys()) + 1
        else:
            return 1

    def add_storm_event(self, obj_se: fsmStormEvent) -> bool:

        if obj_se.storm_event_id not in self.dict_fsm_stormevents:
            self.dict_fsm_stormevents[obj_se.storm_event_id] = obj_se
            return True
        return False

    def get_column_list(self, interim_id: int):
        col_list = []
        a_int = self.dict_fsm_interims[interim_id]
        current_date = a_int.interim_start_date
        a_count = 0
        while current_date < a_int.interim_end_date:
            col_list.append(a_count)
            a_count += 1
            current_date += timedelta(days=1)
        return col_list

    def get_week_number(self, date):
        # Calculate the difference in days between the given date and the start date
        delta_days = (date - self.survey_start_date).days

        # Check if the difference is a multiple of 7
        if delta_days % 7 == 0:
            # Calculate the week number
            week_number = 1 + (delta_days // 7)
            return str(week_number)
        else:
            return ""

    def get_week_list(self, interim_id: int):
        week_list = []
        a_int = self.dict_fsm_interims[interim_id]
        current_date = a_int.interim_start_date
        while current_date < a_int.interim_end_date:
            week_number = self.get_week_number(current_date)
            week_list.append(week_number)
            current_date += timedelta(days=1)

        return week_list

    def get_day_list(self, interim_id: int):
        day_list = []
        a_int = self.dict_fsm_interims[interim_id]
        current_date = a_int.interim_start_date
        while current_date < a_int.interim_end_date:
            day_list.append(current_date.strftime('%a'))
            current_date += timedelta(days=1)

        return day_list

    def get_date_list(self, interim_id: int):
        date_list = []
        a_int = self.dict_fsm_interims[interim_id]
        current_date = a_int.interim_start_date
        while current_date < a_int.interim_end_date:
            date_list.append(current_date.strftime('%d/%m/%Y'))
            current_date += timedelta(days=1)

        return date_list

    def get_class_list(self, interim_id: int, install_id: str):
        class_list = []
        a_int = self.dict_fsm_interims[interim_id]
        a_inst = self.dict_fsm_installs[install_id]
        current_date = a_int.interim_start_date
        while current_date < a_int.interim_end_date:
            if a_inst.class_data_user is not None:
                df_class = a_inst.class_data_user.loc[a_inst.class_data_user['Date'].dt.date == current_date.date(
                ), 'Classification']
            else:
                df_class = pd.DataFrame(
                    columns=['Date', 'Classification', 'Confidence'])
            if not df_class.empty:
                class_list.append(df_class.values[0])
            else:
                df_class = a_inst.class_data_ml.loc[a_inst.class_data_ml['Date'].dt.date == current_date.date(
                ), 'Classification']
                if not df_class.empty:
                    class_list.append(df_class.values[0])
                else:
                    class_list.append('')
            current_date += timedelta(days=1)

        return class_list

    def no_of_installs_by_interim(self, interim_id: int):
        result = 0
        for install in self.dict_fsm_installs.values():
            if install.install_id == interim_id:
                result += 1
        return result

    def update_install_id(self, orig_id: str, new_id: str) -> bool:

        try:
            for a_rd in self.dict_fsm_rawdata.values():
                if a_rd.install_id == orig_id:
                    a_rd.install_id = new_id

            for a_insp in self.dict_fsm_inspections.values():
                if a_insp.install_id == orig_id:
                    a_insp.install_id = new_id

            for a_ir in self.dict_fsm_interim_reviews.values():
                if a_ir.install_id == orig_id:
                    a_ir.install_id = new_id

            for a_ip in self.dict_fsm_install_pictures.values():
                if a_ip.install_id == orig_id:
                    a_ip.install_id = new_id
            return True
        except:
            return False

    def get_pipe_shape_code(self, pipe_text: str) -> str:
        if pipe_text in ['Circular', 'Egg', 'Oval', 'Rectangular']:
            return pipe_text[0]
        else:
            return 'X'

    def get_rg_position_code(self, position_text: str) -> str:
        if position_text == 'Ground':
            return 'G'
        elif position_text == 'Roof (First Floor)':
            return 'F'
        elif position_text == 'Roof (Higher)':
            return 'H'
        elif position_text == 'Post':
            return 'P'
        else:
            return '-'

    def get_interim_monitor_comment(self, interim_id: int, install_id: str, mon_type: str = 'Flow Monitor') -> str:

        for ir in self.dict_fsm_interim_reviews.values():
            if ir.interim_id == interim_id and ir.install_id == install_id:
                if mon_type == 'Rain Gauge':
                    return ir.rg_comment
                else:
                    return ir.fm_comment

    def get_next_install_picture_id(self) -> int:
        if self.dict_fsm_install_pictures:
            return max(self.dict_fsm_install_pictures.keys()) + 1
        else:
            return 1

    # def get_next_storm_event_id(self):
    #     if self.dict_fsm_stormevents:
    #         return max(self.dict_fsm_stormevents.keys()) + 1
    #     else:
    #         return 1

    # def get_interim_data_review(self, interim_dr_id: Optional[int] = None, interim_id: Optional[int] = None, install_id: Optional[int] = None) -> Optional[fsmInterimDataReview]:
    #         if interim_dr_id is not None:
    #             # Case 1: interim_review_id is provided
    #             return self.dict_fsm_interim_data_reviews.get(interim_dr_id)
    #         elif interim_id is not None and install_id is not None:
    #             # Case 2: interim_id and site_id are provided
    #             for a_int_rev in self.dict_fsm_interim_data_reviews.values():
    #                 if a_int_rev.interim_id == interim_id and a_int_rev.install_id == install_id:
    #                     return a_int_rev
    #         return None

    # def get_next_interim_data_review_id(self):
    #     if self.dict_fsm_interim_data_reviews:
    #         return max(self.dict_fsm_interim_data_reviews.keys()) + 1
    #     else:
    #         return 1

    # def get_interim_class_review(self, interim_cr_id: Optional[int] = None, interim_id: Optional[int] = None, install_id: Optional[int] = None) -> Optional[fsmInterimClassificationReview]:
    #         if interim_cr_id is not None:
    #             # Case 1: interim_review_id is provided
    #             return self.dict_fsm_interim_class_reviews.get(interim_cr_id)
    #         elif interim_id is not None and install_id is not None:
    #             # Case 2: interim_id and site_id are provided
    #             for a_int_rev in self.dict_fsm_interim_class_reviews.values():
    #                 if a_int_rev.interim_id == interim_id and a_int_rev.install_id == install_id:
    #                     return a_int_rev
    #         return None

    # def get_next_interim_class_review_id(self):
    #     if self.dict_fsm_interim_class_reviews:
    #         return max(self.dict_fsm_interim_class_reviews.keys()) + 1
    #     else:
    #         return 1

    def filter_interim_reviews_by_interim_id(self, interim_id: int) -> Dict[int, fsmInterimReview]:
        return {key: review for key, review in self.dict_fsm_interim_reviews.items() if review.interim_id == interim_id}

    # def filter_interim_classification_reviews_by_interim_id(self, interim_id: int) -> Dict[int, fsmInterimClassificationReview]:
    #     return {key: review for key, review in self.dict_fsm_interim_class_reviews.items() if review.interim_id == interim_id}

    def add_interim_review(self, objIntRev: fsmInterimReview) -> bool:

        if objIntRev.interim_review_id not in self.dict_fsm_interim_reviews:
            self.dict_fsm_interim_reviews[objIntRev.interim_review_id] = objIntRev
            return True
        return False

    # def add_interim_class_review(self, objIntRev: fsmInterimClassificationReview) -> bool:

    #     if objIntRev.interim_class_review_id not in self.dict_fsm_interim_class_reviews:
    #         self.dict_fsm_interim_class_reviews[objIntRev.interim_class_review_id] = objIntRev
    #         return True
    #     return False

    # def create_fsm_install(self):

    #     dlg_inst = flowbot_dialog_fsm_install(None, None, None)
    #     dlg_inst.setWindowTitle('New Install')
    #     ret = dlg_inst.exec_()

    #     if ret == QDialog.Accepted:

    #         inst = fsmInstall()

    #         inst.install_id = self.get_next_install_id()
    #         inst.install_site_id = dlg_inst.a_site.siteID
    #         inst.install_monitor_asset_id = dlg_inst.a_mon.monitor_asset_id
    #         inst.install_type = dlg_inst.install_type
    #         inst.client_ref = dlg_inst.txt_client_ref.text() or ''
    #         inst.install_date = dlg_inst.dte_install_date.dateTime().toPyDateTime()

    #         if dlg_inst.install_type == 'Flow Monitor':
    #             inst.fm_pipe_letter = dlg_inst.cbo_fm_pipe_letter.currentText() or ''
    #             inst.fm_pipe_shape = dlg_inst.cbo_fm_pipe_shape.currentText() or ''
    #             inst.fm_pipe_height_mm = int(dlg_inst.txt_fm_pipe_height_mm.text() or '0')
    #             inst.fm_pipe_width_mm = int(dlg_inst.txt_fm_pipe_width_mm.text() or '0')
    #             inst.fm_pipe_depth_to_invert_mm = int(dlg_inst.txt_fm_pipe_depth_to_invert_mm.text() or 0)
    #             inst.fm_sensor_offset_mm = int(dlg_inst.txt_fm_sensor_offset_mm.text() or 0)
    #         else:
    #             inst.rg_position = dlg_inst.cbo_rg_position.currentText()

    #         inst.install_sheet = dlg_inst.install_sheet
    #         inst.install_sheet_filename = dlg_inst.txt_install_sheet.text()

    #         self.dict_fsm_installs[inst.install_id] = inst

    # def install_fsm_monitor(self, site_id: str, mon_id: str):

    #     monitor = self.dict_fsm_monitors[mon_id]
    #     site = self.dict_fsm_sites[site_id]

    #     dlg_inst = flowbot_dialog_fsm_install(None, monitor, site)

    #     monitor_type = monitor.monitor_type
    #     rain_gauge = monitor_type == 'Rain Gauge'

    #     dlg_inst.setWindowTitle(f'Install {monitor_type}')

    #     dlg_inst.cbo_fm_pipe_letter.setEnabled(not rain_gauge)
    #     dlg_inst.cbo_fm_pipe_shape.setEnabled(not rain_gauge)
    #     dlg_inst.txt_fm_pipe_height_mm.setEnabled(not rain_gauge)
    #     dlg_inst.txt_fm_pipe_width_mm.setEnabled(not rain_gauge)
    #     dlg_inst.txt_fm_pipe_depth_to_invert_mm.setEnabled(not rain_gauge)
    #     dlg_inst.txt_fm_sensor_offset_mm.setEnabled(not rain_gauge)
    #     dlg_inst.cbo_rg_position.setEnabled(rain_gauge)

    #     ret = dlg_inst.exec_()

    #     if ret == QDialog.Accepted:

    #         inst = fsmInstall()

    #         inst.install_id = self.get_next_install_id()
    #         inst.install_site_id = site_id
    #         inst.install_monitor_asset_id = mon_id
    #         inst.install_type = monitor_type
    #         inst.client_ref = dlg_inst.txt_client_ref.text() or ''
    #         inst.install_date = dlg_inst.dte_install_date.dateTime().toPyDateTime()

    #         if not rain_gauge:
    #             inst.fm_pipe_letter = dlg_inst.cbo_fm_pipe_letter.currentText() or ''
    #             inst.fm_pipe_shape = dlg_inst.cbo_fm_pipe_shape.currentText() or ''
    #             inst.fm_pipe_height_mm = int(dlg_inst.txt_fm_pipe_height_mm.text() or '0')
    #             inst.fm_pipe_width_mm = int(dlg_inst.txt_fm_pipe_width_mm.text() or '0')
    #             inst.fm_pipe_depth_to_invert_mm = int(dlg_inst.txt_fm_pipe_depth_to_invert_mm.text() or 0)
    #             inst.fm_sensor_offset_mm = int(dlg_inst.txt_fm_sensor_offset_mm.text() or 0)
    #         else:
    #             inst.rg_position = dlg_inst.cbo_rg_position.currentText()

    #         inst.install_sheet = dlg_inst.install_sheet
    #         inst.install_sheet_filename = dlg_inst.txt_install_sheet.text()

    #         self.dict_fsm_installs[inst.install_id] = inst

    def site_has_install(self, site_id: str) -> bool:

        for key, inst in self.dict_fsm_installs.items():
            if inst.install_site_id == site_id:
                if inst.remove_date < inst.install_date:
                    return True
        return False

    def monitor_is_installed(self, mon_id: str) -> bool:

        for key, inst in self.dict_fsm_installs.items():
            if inst.install_monitor_asset_id == mon_id:
                if inst.remove_date < inst.install_date:
                    return True
        return False

    def uninstalled(self, inst_id: int) -> bool:

        return self.dict_fsm_installs[inst_id].remove_date > self.dict_fsm_installs[inst_id].install_date

    def get_raw_data_by_install(self, inst_id: str) -> Optional[fsmRawData]:

        for raw in self.dict_fsm_rawdata.values():
            if raw.install_id == inst_id:
                return raw

    def get_next_rawdata_id(self) -> int:
        if self.dict_fsm_rawdata:
            return max(self.dict_fsm_rawdata.keys()) + 1
        else:
            return 1

    def add_rawdata(self, objRaw: fsmRawData) -> bool:

        if objRaw.rawdata_id not in self.dict_fsm_rawdata:
            self.dict_fsm_rawdata[objRaw.rawdata_id] = objRaw
            return True
        return False

    # def install_fsm_monitor(self, site_id: str, mon_id: str):

    #     dlg_inst = flowbot_dialog_fsm_install()
    #     dlg_inst.setWindowTitle('Install Monitor')
    #     ret = dlg_inst.exec_()
    #     if ret == QDialog.Accepted:
    #         a_mon = self.dict_fsm_monitors[mon_id]
    #         dlg_inst.txt_fm_pipe_letter.setEnabled(not a_mon.monitor_type == 'Rain Gauge')
    #         dlg_inst.cbo_fm_pipe_shape.setEnabled(not a_mon.monitor_type == 'Rain Gauge')
    #         dlg_inst.txt_fm_pipe_height_mm.setEnabled(not a_mon.monitor_type == 'Rain Gauge')
    #         dlg_inst.txt_fm_pipe_width_mm.setEnabled(not a_mon.monitor_type == 'Rain Gauge')
    #         dlg_inst.txt_fm_pipe_depth_to_invert_mm.setEnabled(not a_mon.monitor_type == 'Rain Gauge')
    #         dlg_inst.txt_fm_sensor_offset_mm.setEnabled(not a_mon.monitor_type == 'Rain Gauge')
    #         dlg_inst.cbo_rg_position.setEnabled(a_mon.monitor_type == 'Rain Gauge')

    #         a_mon.install_site = site_id
    #         a_mon.install_date = dlg_inst.dte_install_date.dateTime().toPyDateTime()

    #         if not a_mon.monitor_type == 'Rain Gauge':
    #             a_mon.fm_pipe_letter = dlg_inst.txt_fm_pipe_letter.text() or ''
    #             a_mon.fm_pipe_shape = dlg_inst.cbo_fm_pipe_shape.currentText() or ''
    #             try:
    #                 a_mon.fm_pipe_height_mm = int(dlg_inst.txt_fm_pipe_height_mm.text() or '0')
    #             except ValueError:
    #                 a_mon.fm_pipe_height_mm = 0
    #             try:
    #                 a_mon.fm_pipe_width_mm = int(dlg_inst.txt_fm_pipe_width_mm.text() or '0')
    #             except ValueError:
    #                 a_mon.fm_pipe_width_mm = 0
    #             try:
    #                 a_mon.fm_pipe_depth_to_invert_mm = int(dlg_inst.txt_fm_pipe_depth_to_invert_mm.text() or 0)
    #             except ValueError:
    #                 a_mon.fm_pipe_depth_to_invert_mm = 0
    #             try:
    #                 a_mon.fm_sensor_offset_mm = int(dlg_inst.txt_fm_sensor_offset_mm.text() or 0)
    #             except ValueError:
    #                 a_mon.fm_sensor_offset_mm = 0
    #             a_mon.install_sheet = dlg_inst.install_sheet
    #             a_mon.install_sheet_filename = dlg_inst.txt_install_sheet.text()
    #         else:
    #             a_mon.rg_position = dlg_inst.cbo_rg_position.currentText()

    #         self.dict_fsm_monitors[mon_id] = a_mon
    #         self.dict_fsm_sites[site_id].installed = True

    # msg = QMessageBox(self)
    # msg.setWindowIcon(self.myIcon)
    # msg.information(self, 'Information', 'Monitor Installed')

    # def get_interim_review(self, interim_review_id: int) -> Optional[fsmInterimDataReview]:

    #     if interim_review_id in self.dict_fsm_interim_data_reviews:
    #         return self.dict_fsm_interim_data_reviews[interim_review_id]

    # def get_interim_review(self, interim_id: int, site_id: int) -> Optional[fsmInterimDataReview]:

    #     for a_int_rev in self.dict_fsm_interim_data_reviews.values():
    #         if a_int_rev.interim_id == interim_id and a_int_rev.site_id == site_id:
    #             return a_int_rev
    # def remove_monitor(self, monitor_id: str):

    #     if monitor_id in self.dict_fsm_monitors:
    #         self.dict_fsm_monitors.pop(monitor_id)


class fsmDataClassification(object):

    # INPUTS: provide data for one sensor
    def __init__(self):

        self.DM_MODEL_PATH = resource_path(
            "resources\\classifier\\models\\DM_model.pkl")
        self.RG_MODEL_PATH = resource_path(
            "resources\\classifier\\models\\RG_model.pkl")
        self.FM_MODEL_PATH = resource_path(
            "resources\\classifier\\models\\FM_model.cbm")

    def run_classification(self, aInst: fsmInstall):

        results_list = []

        current_date = aInst.data_start
        while current_date <= aInst.data_end:
            features = pd.DataFrame()
            data = aInst.data[(aInst.data['Date'] >= current_date) & (
                aInst.data['Date'] < current_date + timedelta(days=1))]

            if aInst.install_type == 'Depth Monitor':

                # data = self.read_data(self.RAW_DATA_PATH, self.DATE)

                features = pd.DataFrame(columns=['depth_entropy'])
                features.loc[0, f'depth_entropy'] = entropy(data['DepthData'])
                with pd.option_context("future.no_silent_downcasting", True):
                    features.fillna(0, inplace=True)
                with pd.option_context("future.no_silent_downcasting", True):
                    features.replace([np.inf, -np.inf], 1000000, inplace=True)

                model = joblib.load(self.DM_MODEL_PATH)

            elif aInst.install_type == "Flow Monitor":

                features = pd.DataFrame(columns=['month'])
                features.loc[0, 'month'] = current_date.month

                try:
                    area = int(aInst.fm_pipe_height_mm) * \
                        int(aInst.fm_pipe_width_mm)
                except:
                    area = np.NaN

                features.loc[0, "area"] = area

                features.loc[0, 'flow_entropy'] = entropy(data['FlowData'])
                features.loc[0, 'depth_range'] = data['DepthData'].max(
                ) - data['DepthData'].min()
                features.loc[0, 'depth_skewness'] = data['DepthData'].skew()
                features.loc[0, 'depth_entropy'] = entropy(data['DepthData'])
                features.loc[0, 'velocity_iqr'] = data['VelocityData'].quantile(
                    0.75) - data['VelocityData'].quantile(0.25)
                features.loc[0, 'velocity_entropy'] = entropy(
                    data['VelocityData'])

                try:
                    frequencies, psd, psd_normalized, low_freq_power, medium_freq_power, high_freq_power, total_power = self.frequencies(
                        data, 'FlowData')
                    features.loc[0, 'flow_power_low_freq_ratio'] = low_freq_power / total_power
                    features.loc[0, 'flow_power_medium_freq_ratio'] = medium_freq_power / total_power
                except:
                    features.loc[0, 'flow_power_low_freq_ratio'] = np.NaN
                    features.loc[0, 'flow_power_medium_freq_ratio'] = np.NaN

                try:
                    frequencies, psd, psd_normalized, low_freq_power, medium_freq_power, high_freq_power, total_power = self.frequencies(
                        data, 'DepthData')
                    features.loc[0, 'depth_power_skewness'] = skew(psd)
                    features.loc[0, 'depth_power_low_freq_ratio'] = low_freq_power / total_power
                    features.loc[0, 'depth_power_high_freq_ratio'] = high_freq_power / total_power
                except:
                    features.loc[0, 'depth_power_skewness'] = np.NaN
                    features.loc[0, 'depth_power_low_freq_ratio'] = np.NaN
                    features.loc[0, 'depth_power_high_freq_ratio'] = np.NaN

                try:
                    frequencies, psd, psd_normalized, low_freq_power, medium_freq_power, high_freq_power, total_power = self.frequencies(
                        data, 'VelocityData')
                    features.loc[0, 'velocity_dom_freq'] = frequencies[np.argmax(
                        psd)]
                    features.loc[0, 'velocity_shannon_entropy'] = - \
                        np.sum(psd_normalized * np.log2(psd_normalized))
                except:
                    features.loc[0, 'velocity_dom_freq'] = np.NaN
                    features.loc[0, 'velocity_shannon_entropy'] = np.NaN

                features.loc[0, 'velocity_to_flow'] = data.VelocityData.mean(
                ) / data.FlowData.mean()
                features.loc[0, 'depth_to_flow'] = data.DepthData.mean(
                ) / data.FlowData.mean()
                features.loc[0, 'velocity_to_depth'] = data.VelocityData.mean(
                ) / data.DepthData.mean()
                features.loc[0, 'depth_to_depth'] = data.DepthData.mean(
                ) / aInst.fm_pipe_depth_to_invert_mm
                features.loc[0, 'depth_max_to_depth'] = data.DepthData.max(
                ) / aInst.fm_pipe_depth_to_invert_mm
                features.loc[0, 'depth_to_area'] = data.DepthData.mean() / area
                features.loc[0, 'velocity_to_area'] = data.VelocityData.mean() / \
                    area

                features.loc[0, 'pipe_B'] = aInst.fm_pipe_letter == "B"
                features.loc[0, 'pipe_D'] = aInst.fm_pipe_letter == "D"
                features.loc[0, 'pipe_E'] = aInst.fm_pipe_letter == "E"
                features.loc[0, 'pipe_Y'] = aInst.fm_pipe_letter == "Y"
                features.loc[0, 'pipe_Z'] = aInst.fm_pipe_letter == "Z"

                features.loc[0, 'shape_C'] = aInst.fm_pipe_shape == "Circular"

                with pd.option_context("future.no_silent_downcasting", True):
                    features.replace([np.inf, -np.inf], 1000000, inplace=True)

                model = CatBoostClassifier()
                model.load_model(self.FM_MODEL_PATH)

            elif aInst.install_type == 'Rain Gauge':

                features = pd.DataFrame(columns=['month'])
                features.loc[0, 'month'] = current_date.month
                features.loc[0, 'rain_median'] = data['IntensityData'].median()
                features.loc[0, 'rain_skewness'] = data['IntensityData'].skew()
                features.loc[0, 'rain_percentile_25'] = data['IntensityData'].quantile(
                    0.25)
                features.loc[0, 'rain_percentile_75'] = data['IntensityData'].quantile(
                    0.75)
                features.loc[0, 'rain_entropy'] = entropy(
                    data['IntensityData'])
                try:
                    frequencies, psd, psd_normalized, low_freq_power, medium_freq_power, high_freq_power, \
                        total_power = self.frequencies(data, 'IntensityData')

                    features.loc[0,
                                 'rain_dom_freq'] = frequencies[np.argmax(psd)]
                    features.loc[0, 'rain_power_peak'] = np.max(psd)
                    features.loc[0, 'rain_power_skewness'] = skew(psd)
                    features.loc[0, 'rain_power_kurtosis'] = kurtosis(psd)
                    features.loc[0, 'rain_power_low_freq_ratio'] = low_freq_power / total_power
                    features.loc[0, 'rain_power_high_freq_ratio'] = high_freq_power / total_power
                except:
                    features.loc[0, 'rain_dom_freq'] = np.NaN
                    features.loc[0, 'rain_power_peak'] = np.NaN
                    features.loc[0, 'rain_power_skewness'] = np.NaN
                    features.loc[0, 'rain_power_kurtosis'] = np.NaN
                    features.loc[0, 'rain_power_low_freq_ratio'] = np.NaN
                    features.loc[0, 'rain_power_high_freq_ratio'] = np.NaN

                with pd.option_context("future.no_silent_downcasting", True):
                    features.replace([np.inf, -np.inf], 1000000, inplace=True)

                model = joblib.load(self.RG_MODEL_PATH)

            # make predictions
            # prints only string without numpy arrays
            PREDICTION = model.predict(features)[0][0]
            # finds index of prediction of all possible classes
            index = list(model.classes_).index(PREDICTION)
            # gets confidence score of this class only. can remove [index] to get confidence for each class
            CONFIDENCE = model.predict_proba(features)[0][index]

            # Store results in a list
            results_list.append({'date': datetime(current_date.year, current_date.month, current_date.day), 'prediction': PREDICTION, 'confidence': CONFIDENCE})

            # Move to the next day
            current_date += timedelta(days=1)

        # Convert results list to DataFrame
        results = pd.DataFrame(results_list)
        results = results.rename(columns={
                                 'date': 'Date', 'prediction': 'Classification', 'confidence': 'Confidence'})
        # results['Date'] = pd.to_datetime(results['Date']).dt.strftime('%d/%m/%Y')
        # # Convert column types
        # results['Date'] = results['Date'].astype(datetime)
        # results['Classification'] = results['Classification'].astype(str)
        # results['Confidence'] = results['Confidence'].astype(float)

        return results

    # def run_classification(self, aMon: fsmMonitor, aSite: fsmSite, startDate: datetime, endDate: datetime):

    #     results_list = []

    #     current_date = startDate
    #     while current_date <= endDate:
    #         features = pd.DataFrame()
    #         data = aMon.data[(aMon.data['Date'] >= current_date) & (aMon.data['Date'] < current_date + timedelta(days=1))]

    #         if aSite.siteType == 'Depth Monitor':

    #             # data = self.read_data(self.RAW_DATA_PATH, self.DATE)

    #             features = pd.DataFrame(columns=['depth_entropy'])
    #             features.loc[0, f'depth_entropy'] = entropy(data['DepthData'])
    #             with pd.option_context("future.no_silent_downcasting", True):
    #                 features.fillna(0, inplace=True)
    #             with pd.option_context("future.no_silent_downcasting", True):
    #                 features.replace([np.inf, -np.inf], 1000000, inplace=True)

    #             model = joblib.load(self.DM_MODEL_PATH)

    #         elif aSite.siteType == "Flow Monitor":

    #             features = pd.DataFrame(columns=['month'])
    #             features.loc[0, 'month'] = current_date.month

    #             try:
    #                 area = int(aMon.fm_pipe_height_mm) * int(aMon.fm_pipe_width_mm)
    #             except:
    #                 area = np.NaN

    #             features.loc[0, "area"] = area

    #             features.loc[0, 'flow_entropy'] = entropy(data['FlowData'])
    #             features.loc[0, 'depth_range'] = data['DepthData'].max() - data['DepthData'].min()
    #             features.loc[0, 'depth_skewness'] = data['DepthData'].skew()
    #             features.loc[0, 'depth_entropy'] = entropy(data['DepthData'])
    #             features.loc[0, 'velocity_iqr'] = data['VelocityData'].quantile(0.75) - data['VelocityData'].quantile(0.25)
    #             features.loc[0, 'velocity_entropy'] = entropy(data['VelocityData'])

    #             try:
    #                 frequencies, psd, psd_normalized, low_freq_power, medium_freq_power, high_freq_power, total_power = self.frequencies(
    #                     data, 'FlowData')
    #                 features.loc[0, 'flow_power_low_freq_ratio'] = low_freq_power / total_power
    #                 features.loc[0, 'flow_power_medium_freq_ratio'] = medium_freq_power / total_power
    #             except:
    #                 features.loc[0, 'flow_power_low_freq_ratio'] = np.NaN
    #                 features.loc[0, 'flow_power_medium_freq_ratio'] = np.NaN

    #             try:
    #                 frequencies, psd, psd_normalized, low_freq_power, medium_freq_power, high_freq_power, total_power = self.frequencies(
    #                     data, 'DepthData')
    #                 features.loc[0, 'depth_power_skewness'] = skew(psd)
    #                 features.loc[0, 'depth_power_low_freq_ratio'] = low_freq_power / total_power
    #                 features.loc[0, 'depth_power_high_freq_ratio'] = high_freq_power / total_power
    #             except:
    #                 features.loc[0, 'depth_power_skewness'] = np.NaN
    #                 features.loc[0, 'depth_power_low_freq_ratio'] = np.NaN
    #                 features.loc[0, 'depth_power_high_freq_ratio'] = np.NaN

    #             try:
    #                 frequencies, psd, psd_normalized, low_freq_power, medium_freq_power, high_freq_power, total_power = self.frequencies(
    #                     data, 'VelocityData')
    #                 features.loc[0, 'velocity_dom_freq'] = frequencies[np.argmax(psd)]
    #                 features.loc[0, 'velocity_shannon_entropy'] = -np.sum(psd_normalized * np.log2(psd_normalized))
    #             except:
    #                 features.loc[0, 'velocity_dom_freq'] = np.NaN
    #                 features.loc[0, 'velocity_shannon_entropy'] = np.NaN

    #             features.loc[0, 'velocity_to_flow'] = data.VelocityData.mean() / data.FlowData.mean()
    #             features.loc[0, 'depth_to_flow'] = data.DepthData.mean() / data.FlowData.mean()
    #             features.loc[0, 'velocity_to_depth'] = data.VelocityData.mean() / data.DepthData.mean()
    #             features.loc[0, 'depth_to_depth'] = data.DepthData.mean() / aMon.fm_pipe_depth_to_invert_mm
    #             features.loc[0, 'depth_max_to_depth'] = data.DepthData.max() / aMon.fm_pipe_depth_to_invert_mm
    #             features.loc[0, 'depth_to_area'] = data.DepthData.mean() / area
    #             features.loc[0, 'velocity_to_area'] = data.VelocityData.mean() / area

    #             features.loc[0, 'pipe_B'] = aMon.fm_pipe_letter == "B"
    #             features.loc[0, 'pipe_D'] = aMon.fm_pipe_letter == "D"
    #             features.loc[0, 'pipe_E'] = aMon.fm_pipe_letter == "E"
    #             features.loc[0, 'pipe_Y'] = aMon.fm_pipe_letter == "Y"
    #             features.loc[0, 'pipe_Z'] = aMon.fm_pipe_letter == "Z"

    #             features.loc[0, 'shape_C'] = aMon.fm_pipe_shape == "C"

    #             with pd.option_context("future.no_silent_downcasting", True):
    #                 features.replace([np.inf, -np.inf], 1000000, inplace=True)

    #             model = CatBoostClassifier()
    #             model.load_model(self.FM_MODEL_PATH)

    #         elif aSite.siteType == 'Rain Gauge':

    #             features = pd.DataFrame(columns=['month'])
    #             features.loc[0, 'month'] = current_date.month
    #             features.loc[0, 'rain_median'] = data['IntensityData'].median()
    #             features.loc[0, 'rain_skewness'] = data['IntensityData'].skew()
    #             features.loc[0, 'rain_percentile_25'] = data['IntensityData'].quantile(0.25)
    #             features.loc[0, 'rain_percentile_75'] = data['IntensityData'].quantile(0.75)
    #             features.loc[0, 'rain_entropy'] = entropy(data['IntensityData'])
    #             try:
    #                 frequencies, psd, psd_normalized, low_freq_power, medium_freq_power, high_freq_power, \
    #                     total_power = self.frequencies(data, 'IntensityData')

    #                 features.loc[0, 'rain_dom_freq'] = frequencies[np.argmax(psd)]
    #                 features.loc[0, 'rain_power_peak'] = np.max(psd)
    #                 features.loc[0, 'rain_power_skewness'] = skew(psd)
    #                 features.loc[0, 'rain_power_kurtosis'] = kurtosis(psd)
    #                 features.loc[0, 'rain_power_low_freq_ratio'] = low_freq_power / total_power
    #                 features.loc[0, 'rain_power_high_freq_ratio'] = high_freq_power / total_power
    #             except:
    #                 features.loc[0, 'rain_dom_freq'] = np.NaN
    #                 features.loc[0, 'rain_power_peak'] = np.NaN
    #                 features.loc[0, 'rain_power_skewness'] = np.NaN
    #                 features.loc[0, 'rain_power_kurtosis'] = np.NaN
    #                 features.loc[0, 'rain_power_low_freq_ratio'] = np.NaN
    #                 features.loc[0, 'rain_power_high_freq_ratio'] = np.NaN

    #             with pd.option_context("future.no_silent_downcasting", True):
    #                 features.replace([np.inf, -np.inf], 1000000, inplace=True)

    #             model = joblib.load(self.RG_MODEL_PATH)

    #         # make predictions
    #         PREDICTION = model.predict(features)[0][0]  # prints only string without numpy arrays
    #         index = list(model.classes_).index(PREDICTION)  # finds index of prediction of all possible classes
    #         # gets confidence score of this class only. can remove [index] to get confidence for each class
    #         CONFIDENCE = model.predict_proba(features)[0][index]

    #         # Store results in a list
    #         results_list.append({'date': current_date, 'prediction': PREDICTION, 'confidence': CONFIDENCE})

    #         # Move to the next day
    #         current_date += timedelta(days=1)

    #     # Convert results list to DataFrame
    #     results = pd.DataFrame(results_list)

    #     return results

    # def read_data(self, aDataPath, aDate):
    #     data = pd.read_csv(aDataPath)
    #     data.Date = pd.to_datetime(data.Date, format="%d/%m/%Y %H:%M:%S")
    #     data = data[(data['Date'] >= aDate) & (data['Date'] < aDate + timedelta(days=1))]
    #     return data

    def frequencies(self, data: pd.DataFrame, column: str):
        segments = 10
        sr = 60 / data.Date.diff().mean().total_seconds()
        nperseg = 2 * data.shape[0] * sr / segments
        frequencies, psd = welch(data[column], fs=sr, nperseg=nperseg)
        psd_normalized = psd / np.sum(psd)
        freq_range = frequencies[-1] - frequencies[0]
        low_band = frequencies[0] + freq_range / 3
        high_band = frequencies[-1] - freq_range / 3
        low_freq_power = np.sum(psd[frequencies < low_band])
        medium_freq_power = np.sum(
            psd[(frequencies > low_band) & (frequencies < high_band)])
        high_freq_power = np.sum(psd[frequencies > high_band])
        total_power = np.sum(psd)

        return frequencies, psd, psd_normalized, low_freq_power, medium_freq_power, high_freq_power, total_power


class MonitorDataFlowCalculator:

    def __init__(self, a_raw: fsmRawData):
        """
        Initialize flow calculator with optional correction parameters.
        """
        self.raw_data: fsmRawData = a_raw
        self.shape_definition = a_raw.pipe_shape_def
        self.shape_type = a_raw.pipe_shape
        self.shape_width = a_raw.pipe_width
        self.shape_height = a_raw.pipe_height
        self.silt_data = a_raw.silt_levels
        self.sensor_offset_data = a_raw.dep_corr
        self.depth_correction_data = a_raw.dep_corr
        # self.depth_timing_corrections = a_raw.dv_timing_corr
        # self.velocity_timing_corrections = a_raw.dv_timing_corr
        self.dv_timing_corrections = a_raw.dv_timing_corr
        self.velocity_multiplier_data = a_raw.vel_corr

    def _interpolate_correction_data(self, correction_data, timestamps):
        """
        Interpolate correction data for given timestamps, applying the last value beyond its timestamp.

        Parameters:
        ----------
        correction_data : pandas.DataFrame or None
            A DataFrame with columns 'DateTime' and 'correction', or None if no corrections exist.
        timestamps : array-like
            Timestamps for which corrections need to be applied.

        Returns:
        --------
        numpy.ndarray
            Interpolated correction values for the given timestamps.
        """
        if correction_data is None or correction_data.empty:
            return np.zeros_like(timestamps, dtype=float)

        # Ensure timestamps are in pandas DateTime format
        timestamps = pd.to_datetime(timestamps)

        # Sort the correction data by DateTime
        correction_data = correction_data.sort_values(by='DateTime')

        # Extract values and times
        correction_values = correction_data['correction'].values
        correction_times = pd.to_datetime(correction_data['DateTime']).values

        # Handle single correction value (constant adjustment)
        if len(correction_values) == 1:
            correction_array = np.where(
                timestamps >= correction_times[0], correction_values[0], 0)
            return correction_array

        # Handle multiple correction values (interpolation + flat adjustment)
        interp_func = interpolate.interp1d(
            correction_times.astype(np.int64),
            correction_values,
            kind='linear',
            bounds_error=False,
            # Extrapolate flat
            fill_value=(correction_values[0], correction_values[-1])
        )

        return interp_func(timestamps.astype(np.int64))

    def calculate_corrected_depth(self, depths, timestamps):
        """
        Apply sensor offset and depth corrections to input depths.

        Parameters:
        ----------
        depths : array-like
            Depth values to be corrected (in meters).
        timestamps : array-like
            Corresponding timestamps for the depth values.

        Returns:
        --------
        corrected_depths : numpy.ndarray
            Corrected depth values (in meters), ensuring no negative depths.
        """
        if self.sensor_offset_data is None and self.depth_correction_data is None:
            return depths

        depths = np.array(depths)
        timestamps = pd.to_datetime(timestamps)

        # Extract necessary columns for interpolation
        if self.sensor_offset_data is not None:
            sensor_offset_df = self.sensor_offset_data[['DateTime', 'InvertOffset']].rename(
                columns={'InvertOffset': 'correction'})
        else:
            sensor_offset_df = None

        if self.depth_correction_data is not None:
            depth_correction_df = self.depth_correction_data[['DateTime', 'DepthCorr']].rename(
                columns={'DepthCorr': 'correction'})
        else:
            depth_correction_df = None

        # Interpolate corrections
        sensor_offsets = self._interpolate_correction_data(
            sensor_offset_df, timestamps)
        depth_corrections = self._interpolate_correction_data(
            depth_correction_df, timestamps)

        # Convert corrections from millimeters to meters
        sensor_offsets = sensor_offsets / 1000 if sensor_offsets is not None else 0
        depth_corrections = depth_corrections / \
            1000 if depth_corrections is not None else 0

        # Apply corrections and ensure depths are non-negative
        corrected_depths = depths + sensor_offsets + depth_corrections
        return np.maximum(corrected_depths, 0)

    def calculate_corrected_velocities(self, velocities, timestamps):
        """
        Apply velocity multipliers to the original velocity values.

        Parameters:
        ----------
        velocities : array-like
            Original velocity values corresponding to the timestamps.
        timestamps : array-like
            Timestamps for the velocity values.

        Returns:
        --------
        corrected_velocities : numpy.ndarray
            Corrected velocity values after applying the velocity multipliers.
        """
        if self.velocity_multiplier_data is None or self.velocity_multiplier_data.empty:
            return np.array(velocities)

        # Ensure timestamps are in pandas DateTime format
        timestamps = pd.to_datetime(timestamps)

        # Extract necessary columns for interpolation
        velocity_multiplier_df = self.velocity_multiplier_data[[
            'DateTime', 'FloatValue']].rename(columns={'FloatValue': 'correction'})

        # Interpolate multipliers for the given timestamps
        multipliers = self._interpolate_correction_data(
            velocity_multiplier_df, timestamps)

        # Apply the multipliers to the original velocities
        corrected_velocities = np.array(velocities) * multipliers
        return corrected_velocities

    # def calculate_flow_area(self, depth, silt_depth):
    #     """
    #     Calculate cross-sectional flow area, accounting for silt and corrections.

    #     Parameters:
    #     ----------
    #     depth : float
    #         Depth of the water.
    #     silt_depth : float, optional
    #         Depth of the silt (default is 0).

    #     Returns:
    #     --------
    #     float
    #         Cross-sectional flow area.
    #     """
    #     if self.shape_type == 'CIRC':
    #         silt_area = self._calculate_circ_area(silt_depth)
    #         water_area = self._calculate_circ_area(depth)
    #     elif self.shape_type == 'RECT':
    #         silt_area = self._calculate_rect_area(silt_depth)
    #         water_area = self._calculate_rect_area(depth)
    #     else:
    #         silt_area = 0
    #         water_area = 0
    #         if silt_depth > 0:
    #             silt_area = self._calculate_custom_area(silt_depth)
    #         if depth > 0:
    #             water_area = self._calculate_custom_area(depth)

    #     return max(0, water_area - silt_area)

    # def _calculate_circ_area(self, depth):

    #     shape_height_m = self.shape_height / 1000

    #     radius = shape_height_m / 2

    #     if depth == 0:
    #         return 0

    #     if depth >= shape_height_m:
    #         return math.pi * radius**2

    #     theta = 2 * math.acos((radius - depth) / radius)
    #     return (radius**2 / 2) * (theta - math.sin(theta))

    # def _calculate_rect_area(self, depth):
    #     if depth == 0:
    #         return 0

    #     shape_height_m = self.shape_height / 1000
    #     shape_width_m = self.shape_width / 1000

    #     if depth >= shape_height_m:
    #         return shape_height_m * shape_width_m

    #     return shape_width_m * depth

    # def _calculate_custom_area(self, depth):
    #     """
    #     Calculate the area for a custom shape defined by (width, height) pairs in millimeters (mm).

    #     The area is calculated as the cumulative area of all segments up to the requested depth,
    #     using the average width of each segment. The area is returned in square meters (m²).

    #     Parameters:
    #     -----------
    #     depth : float
    #         Requested water depth in meters (m).

    #     Returns:
    #     --------
    #     float
    #         Cross-sectional area in square meters (m²).
    #     """
    #     # Convert depth from meters to millimeters for comparison
    #     depth_mm = depth * 1000
    #     # Sort shape by height in mm to ensure proper area calculation
    #     sorted_shape = self.shape_definition.sort_values(by='Height')
    #     # Check if depth_mm is less than the smallest height
    #     if depth_mm <= sorted_shape.iloc[0]['Height']:
    #         return 0.0
    #     total_area_mm2 = 0.0  # Area in square millimeters
    #     # Traverse the shape and accumulate the area
    #     for i in range(len(sorted_shape) - 1):
    #         w1_mm = sorted_shape.iloc[i]['Width']
    #         h1_mm = sorted_shape.iloc[i]['Height']
    #         w2_mm = sorted_shape.iloc[i + 1]['Width']
    #         h2_mm = sorted_shape.iloc[i + 1]['Height']
    #         # If the entire segment is below the requested depth, add the entire segment's area
    #         if depth_mm >= h2_mm:
    #             segment_area_mm2 = (w1_mm + w2_mm) / 2 * (h2_mm - h1_mm)
    #             total_area_mm2 += segment_area_mm2
    #         # If the segment is partially below the requested depth, calculate the partial area
    #         elif h1_mm <= depth_mm < h2_mm:
    #             # Interpolate width at the requested depth
    #             interpolated_width_mm = w1_mm + \
    #                 (w2_mm - w1_mm) * (depth_mm - h1_mm) / (h2_mm - h1_mm)
    #             segment_area_mm2 = (
    #                 w1_mm + interpolated_width_mm) / 2 * (depth_mm - h1_mm)
    #             total_area_mm2 += segment_area_mm2
    #             break
    #     # Convert area from mm² to m² before returning
    #     total_area_m2 = total_area_mm2 / 1_000_000
    #     return total_area_m2

    def _calculate_circ_area_vectorized(self, depths):
        """
        Calculate cross-sectional area of a circular shape for multiple depths.

        Parameters:
        -----------
        depths : np.ndarray
            Array of water depths in meters.

        Returns:
        --------
        np.ndarray
            Array of cross-sectional areas in square meters.
        """
        shape_height_m = self.shape_height / 1000
        radius = shape_height_m / 2

        # Initialize result array
        areas = np.zeros_like(depths)

        # Full area where depth >= diameter
        full_mask = depths >= shape_height_m
        areas[full_mask] = math.pi * radius**2

        # Partial area where 0 < depth < diameter
        partial_mask = (depths > 0) & (depths < shape_height_m)
        partial_depths = depths[partial_mask]
        theta = 2 * np.arccos((radius - partial_depths) / radius)
        partial_areas = (radius**2 / 2) * (theta - np.sin(theta))
        areas[partial_mask] = partial_areas

        return areas

    def _calculate_rect_area_vectorized(self, depths):
        """
        Calculate cross-sectional area of a rectangular shape for multiple depths.

        Parameters:
        -----------
        depths : np.ndarray
            Array of water depths in meters.

        Returns:
        --------
        np.ndarray
            Array of cross-sectional areas in square meters.
        """
        shape_height_m = self.shape_height / 1000
        shape_width_m = self.shape_width / 1000

        # Full area where depth >= shape height
        areas = np.minimum(depths, shape_height_m) * shape_width_m

        return areas

    def _calculate_custom_area_vectorized(self, depths):
        """
        Calculate areas for custom shapes for multiple depths using vectorized operations.

        Parameters:
        -----------
        depths : np.ndarray
            Array of water depths in meters.

        Returns:
        --------
        np.ndarray
            Array of cross-sectional areas in square meters.
        """
        depths_mm = depths * 1000  # Convert to mm
        sorted_shape = self.shape_definition.sort_values(
            by="Height").to_numpy()
        heights = sorted_shape[:, 1]  # Assuming second column is 'Height'
        widths = sorted_shape[:, 0]   # Assuming first column is 'Width'

        # Initialize an array to store results
        areas = np.zeros_like(depths)

        # Vectorized calculations
        for i in range(len(heights) - 1):
            w1 = widths[i]
            h1 = heights[i]
            w2 = widths[i + 1]
            h2 = heights[i + 1]

            # Full segment areas
            full_mask = depths_mm >= h2
            areas[full_mask] += (w1 + w2) / 2 * (h2 - h1)

            # Partial segment areas
            partial_mask = (depths_mm > h1) & (depths_mm < h2)
            interpolated_width = w1 + \
                (w2 - w1) * (depths_mm[partial_mask] - h1) / (h2 - h1)
            areas[partial_mask] += (w1 + interpolated_width) / \
                2 * (depths_mm[partial_mask] - h1)

        # Convert mm² to m²
        return areas / 1_000_000

    def apply_timing_corrections(self, timestamps):
        """
        Apply timing corrections to timestamps based on dv_timing_corrections.
        The corrections are defined in a DataFrame with DateTime and FloatValue columns.

        Parameters:
        ----------
        timestamps : array-like
            Original timestamps as pandas DateTime objects.

        Returns:
        --------
        corrected_timestamps : pandas.Series
            Adjusted timestamps based on timing corrections.
        """
        if self.dv_timing_corrections is None:
            return timestamps

        # Ensure timestamps and timing corrections are pandas DateTime
        timestamps = pd.to_datetime(timestamps)
        corrections = self.dv_timing_corrections.copy()
        corrections['DateTime'] = pd.to_datetime(corrections['DateTime'])

        # Sort corrections by DateTime to ensure proper application
        corrections = corrections.sort_values(by='DateTime')

        # Initialize corrected timestamps as a copy of the original
        corrected_timestamps = pd.Series(timestamps)

        # Apply timing corrections iteratively
        for _, row in corrections.iterrows():
            cutoff_time = row['DateTime']
            offset_minutes = row['FloatValue']
            # Apply offset to all timestamps greater than or equal to the cutoff
            corrected_timestamps.loc[corrected_timestamps >=
                                     cutoff_time] += pd.to_timedelta(offset_minutes, unit='m')

        return corrected_timestamps

    def calculate_flow(self):
        """
        Calculate flow rates from depth and velocity DataFrames generated by `read_dat_file`.
        """
        # Extract data from raw inputs
        timestamps = pd.to_datetime(self.raw_data.dep_data['Timestamp'])
        original_depths = self.raw_data.dep_data['Value'].values
        original_velocities = self.raw_data.vel_data['Value'].values

        # Apply corrections
        corrected_timestamps = self.apply_timing_corrections(timestamps)
        corrected_depths = self.calculate_corrected_depth(
            original_depths, corrected_timestamps)
        corrected_velocities = self.calculate_corrected_velocities(
            original_velocities, corrected_timestamps)

        # Interpolate silt depths once for the entire time series
        # Initialize with zeros (in meters)
        silt_depths = np.zeros(len(corrected_timestamps))
        if self.silt_data is not None:
            # Extract and rename necessary columns
            silt_data_df = self.silt_data[['DateTime', 'FloatValue']].rename(
                columns={'FloatValue': 'correction'}
            )
            # Interpolate silt depths
            silt_depths = self._interpolate_correction_data(
                silt_data_df, corrected_timestamps)
            # Convert from mm to m
            silt_depths = silt_depths / 1000

        # Calculate flows using vectorized area calculation
        corrected_depths_m = corrected_depths  # Ensure units are meters
        silt_depths_m = silt_depths  # Ensure units are meters

        if self.shape_type == 'CIRC':
            silt_areas = self._calculate_circ_area_vectorized(silt_depths_m)
            water_areas = self._calculate_circ_area_vectorized(
                corrected_depths_m)
        elif self.shape_type == 'RECT':
            silt_areas = self._calculate_rect_area_vectorized(silt_depths_m)
            water_areas = self._calculate_rect_area_vectorized(
                corrected_depths_m)
        else:
            silt_areas = self._calculate_custom_area_vectorized(silt_depths_m)
            water_areas = self._calculate_custom_area_vectorized(
                corrected_depths_m)

        # Subtract silt areas from water areas and calculate flows
        flows = (water_areas - silt_areas).clip(min=0) * corrected_velocities

        # # Calculate flows
        # flows = np.array([(self.calculate_flow_area(depth, silt_depth) * velocity)
        #                   for depth, silt_depth, velocity in zip(corrected_depths, silt_depths, corrected_velocities)
        #                   ])
        # Prepare result DataFrame
        result_df = pd.DataFrame({
            'Date': corrected_timestamps,
            'FlowData': flows,
            'DepthData': corrected_depths * 1000,
            'VelocityData': corrected_velocities
        })

        return result_df

class PumpLoggerDataCalculator:

    def __init__(self, a_raw: fsmRawData):
        """
        Initialize calculator with optional correction parameters.
        """
        self.raw_data: fsmRawData = a_raw
        self.pl_timing_corrections = a_raw.pl_timing_corr
        self.pl_added_onoffs = a_raw.pl_added_onoffs

    def apply_timing_corrections(self, timestamps):
        """
        Apply timing corrections to timestamps based on dv_timing_corrections.
        The corrections are defined in a DataFrame with DateTime and FloatValue columns.

        Parameters:
        ----------
        timestamps : array-like
            Original timestamps as pandas DateTime objects.

        Returns:
        --------
        corrected_timestamps : pandas.Series
            Adjusted timestamps based on timing corrections.
        """
        if self.pl_timing_corrections is None:
            return timestamps

        # Ensure timestamps and timing corrections are pandas DateTime
        timestamps = pd.to_datetime(timestamps)
        corrections = self.pl_timing_corrections.copy()
        corrections['DateTime'] = pd.to_datetime(corrections['DateTime'])

        # Sort corrections by DateTime to ensure proper application
        corrections = corrections.sort_values(by='DateTime')

        # Initialize corrected timestamps as a copy of the original
        corrected_timestamps = pd.Series(timestamps)

        # Apply timing corrections iteratively
        for _, row in corrections.iterrows():
            cutoff_time = row['DateTime']
            offset_minutes = row['FloatValue']
            # Apply offset to all timestamps greater than or equal to the cutoff
            corrected_timestamps.loc[corrected_timestamps >=
                                     cutoff_time] += pd.to_timedelta(offset_minutes, unit='m')

        return corrected_timestamps
    
    def apply_additional_onoffs(self, timestamps):
        pass
        # """
        # Apply timing corrections to timestamps based on dv_timing_corrections.
        # The corrections are defined in a DataFrame with DateTime and FloatValue columns.

        # Parameters:
        # ----------
        # timestamps : array-like
        #     Original timestamps as pandas DateTime objects.

        # Returns:
        # --------
        # corrected_timestamps : pandas.Series
        #     Adjusted timestamps based on timing corrections.
        # """
        # if self.pl_timing_corrections is None:
        #     return timestamps

        # # Ensure timestamps and timing corrections are pandas DateTime
        # timestamps = pd.to_datetime(timestamps)
        # corrections = self.pl_timing_corrections.copy()
        # corrections['DateTime'] = pd.to_datetime(corrections['DateTime'])

        # # Sort corrections by DateTime to ensure proper application
        # corrections = corrections.sort_values(by='DateTime')

        # # Initialize corrected timestamps as a copy of the original
        # corrected_timestamps = pd.Series(timestamps)

        # # Apply timing corrections iteratively
        # for _, row in corrections.iterrows():
        #     cutoff_time = row['DateTime']
        #     offset_minutes = row['FloatValue']
        #     # Apply offset to all timestamps greater than or equal to the cutoff
        #     corrected_timestamps.loc[corrected_timestamps >=
        #                              cutoff_time] += pd.to_timedelta(offset_minutes, unit='m')

        # return corrected_timestamps    

    def calculate_pumplog(self):
        """
        Calculate flow rates from depth and velocity DataFrames generated by `read_dat_file`.
        """
        # Extract data from raw inputs
        timestamps = pd.to_datetime(self.raw_data.pl_data['Timestamp'])
        original_onoffs = self.raw_data.pl_data['Value'].values

        # Apply corrections
        corrected_timestamps = self.apply_timing_corrections(timestamps)

        result_df = pd.DataFrame({
            'Date': corrected_timestamps,
            'OnOffData': original_onoffs
        })

        return result_df

def plot_fdv_data(testData: pd.DataFrame):

    filespec = "C:/Temp/Flowbot/Flowbot Test Data/PMAC Data/4122.FDV"
    filename = os.path.basename(filespec)
    # testData = get_fdv_data_from_file(filespec)
    # testData
    i_soffit_mm = 225

    # import matplotlib.pyplot as plt

    # Calculate the time interval between the first two data points
    time_interval_seconds = (
        testData['Date'].iloc[1] - testData['Date'].iloc[0]).total_seconds()
    # Calculate total volume of flow in m³
    # Assuming flow values are in liters per second
    total_flow_volume_m3 = (
        testData['Flow'].sum() * time_interval_seconds) / 1000

    # Create a figure and subplots
    fig, axs = plt.subplots(3, 1, figsize=(16, 12), sharex=True)

    # Plotting Flow vs Date
    flow_min = testData['Flow'].min()
    flow_max = testData['Flow'].max()
    flow_range = flow_max - flow_min
    flow_avg = testData['Flow'].mean()

    axs[0].plot(testData['Date'], testData['Flow'], color='blue')
    axs[0].set_ylabel('Flow (l/sec)')
    axs[0].set_title(f'Flow: {filename}', loc='left',
                     fontsize=16)  # Adding filename to title

    # Add statistics to the right of the plot
    flow_stats_text = f"Min: {flow_min:.2f}\nMax: {flow_max:.2f}\nRange: {flow_range:.2f}\nAverage: {flow_avg:.2f}\nTotal Volume: {total_flow_volume_m3:.1f} m³"
    axs[0].text(1.02, 0.5, flow_stats_text,
                transform=axs[0].transAxes, verticalalignment='center')

    # Plotting Depth vs Date
    depth_min = testData['Depth'].min()
    depth_max = testData['Depth'].max()
    depth_range = depth_max - depth_min
    depth_avg = testData['Depth'].mean()

    i_soffit_mm_array = np.full(len(testData), i_soffit_mm)
    axs[1].plot(testData['Date'], testData['Depth'], color='red')
    axs[1].plot(testData['Date'], i_soffit_mm_array,
                color='darkblue', label='Soffit')
    axs[1].set_ylabel('Depth (mm)')
    axs[1].set_title('Depth', loc='left', fontsize=16)

    # Add Soffit height label
    axs[1].text(testData['Date'].iloc[0], i_soffit_mm - 10,
                f"Soffit Height = {i_soffit_mm}mm", color='darkblue', verticalalignment='top', horizontalalignment='left')

    # Add statistics to the right of the plot
    axs[1].text(1.02, 0.5, f"Min: {depth_min:.2f}\nMax: {depth_max:.2f}\nRange: {depth_range:.2f}\nAverage: {depth_avg:.2f}",
                transform=axs[1].transAxes, verticalalignment='center')

    # Plotting Velocity vs Date
    velocity_min = testData['Velocity'].min()
    velocity_max = testData['Velocity'].max()
    velocity_range = velocity_max - velocity_min
    velocity_avg = testData['Velocity'].mean()

    axs[2].plot(testData['Date'], testData['Velocity'], color='green')
    axs[2].set_ylabel('Velocity (m/sec)')
    axs[2].set_title('Velocity', loc='left', fontsize=16)
    axs[2].set_xlabel('Date')

    # Add statistics to the right of the plot
    axs[2].text(1.02, 0.5, f"Min: {velocity_min:.2f}\nMax: {velocity_max:.2f}\nRange: {velocity_range:.2f}\nAverage: {velocity_avg:.2f}",
                transform=axs[2].transAxes, verticalalignment='center')

    # Rotate the x-axis labels for better readability
    plt.xticks(rotation=45)

    # Adjust layout
    plt.tight_layout()

    # Show plot
    plt.show()

# class fsmSites():

#     def __init__(self):
#         self.dict_fsm_sites: Dict[str, fsmSite] = {}

#     def read_from_database(self, conn: sqlite3.Connection):
#         c = conn.cursor()
#         try:
#             c.execute(f"SELECT * FROM {Tables.FSM_SITE}")
#         except sqlite3.OperationalError as e:
#             print(f"Table '{Tables.FSM_SITE}' does not exist.")
#             return  # Return without attempting to fetch rows

#         rows = c.fetchall()
#         for row in rows:
#             site = fsmSite()
#             site.from_database_row(row)
#             self.dict_fsm_sites[site.siteID] = site

#     def write_to_database(self, conn: sqlite3.Connection):
#         c = conn.cursor()
#         c.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.FSM_SITE} (
#                         siteID TEXT PRIMARY KEY,
#                         siteType TEXT,
#                         address TEXT,
#                         mh_ref TEXT,
#                         w3w TEXT,
#                         easting REAL,
#                         northing REAL,
#                         installed INTEGER
#                     )''')
#         for site in self.dict_fsm_sites.values():
#             c.execute(f'''INSERT OR REPLACE INTO {Tables.FSM_SITE} VALUES (?, ?, ?, ?, ?, ?, ?)''',
#                       (site.siteID, site.siteType, site.address, site.mh_ref, site.w3w, site.easting,
#                        site.northing, int(site.installed)))
#         conn.commit()

#     def add_site(self, objSite: fsmSite) -> bool:

#         if objSite.siteID not in self.dict_fsm_sites:
#             self.dict_fsm_sites[objSite.siteID] = objSite
#             return True
#         return False

#     def get_site(self, site_id: str) -> Optional[fsmSite]:

#         if site_id in self.dict_fsm_sites:
#             return self.dict_fsm_sites[site_id]

#     def remove_site(self, siteID: str):

#         if siteID in self.dict_fsm_sites:
#             self.dict_fsm_sites.pop(siteID)
