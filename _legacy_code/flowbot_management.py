import os
from collections import namedtuple
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
from flowbot_helper import resource_path, parse_file, parse_date, write_header, write_constants, write_fsm_rg_payload, write_fsm_fm_payload
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from catboost import CatBoostClassifier
from scipy import interpolate
from flowbot_database import Tables
from PyQt5.QtWidgets import QDialog, QMessageBox
from flowbot_logging import get_logger

logger = get_logger('flowbot_logger')


class fsmMonitor(object):

    def __init__(self):
        self.monitor_asset_id: str = ''
        self.monitor_type: str = 'Flow Monitor'
        self.pmac_id: str = ''
        self.monitor_sub_type: str = "Detec"

    def from_database_row_dict(self, row_dict: Dict):
        self.monitor_asset_id = row_dict.get('monitor_asset_id')
        self.monitor_type = row_dict.get('monitor_type', self.monitor_type)
        self.pmac_id = row_dict.get('pmac_id')
        self.monitor_sub_type = row_dict.get('monitor_sub_type', self.monitor_sub_type)


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
        self.fm_pipe_depth_to_invert_mm: int = 0
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


    def get_fdv_data_from_file(self, fileSpec: str):

        try:
            with open(fileSpec, 'r') as org_data:

                file_data = parse_file(fileSpec)

                all_units = [unit for record in file_data["payload"] for unit in record]

                constants = file_data["constants"]

                # Parse the START and END dates using the helper.
                start_dt = parse_date(constants["START"])
                end_dt = parse_date(constants["END"])
                duration_mins = (end_dt - start_dt).total_seconds() / 60

                # Get the INTERVAL (assumed to be in minutes)
                interval_minutes = int(constants["INTERVAL"])
                interval = timedelta(minutes=interval_minutes)

                dateRange: List[datetime] = np.arange(start_dt, end_dt + interval, interval).tolist()                    

                no_of_records = int(duration_mins / interval_minutes) + 1
                i_record = 0

                flowDataRange: List[float] = []
                depthDataRange: List[float] = []
                velocityDataRange: List[float] = []
                # for unit in all_units:
                #     i_record += 1
                #     if i_record <= no_of_records:
                #         flowDataRange.append(float(unit["FLOW"]))
                #         depthDataRange.append(float(unit["DEPTH"]))
                #         velocityDataRange.append(float(unit["VELOCITY"]))

                for unit in all_units:
                    i_record += 1
                    if i_record <= no_of_records:
                        flow = unit.get("FLOW")
                        if flow is not None:
                            flowDataRange.append(float(flow))
                        else:
                            flowDataRange.append(0.0)

                        depth = unit.get("DEPTH")
                        if depth is not None:
                            depthDataRange.append(float(depth))
                        else:
                            depthDataRange.append(0.0)

                        velocity = unit.get("VELOCITY")
                        if velocity is not None:
                            velocityDataRange.append(float(velocity))
                        else:
                            velocityDataRange.append(0.0)                        

                # Check that the number of dates matches the number of data units.
                if len(dateRange) != len(flowDataRange):
                    print("Warning: Mismatch in number of timestamps and data points!")

                self.data_start = start_dt
                self.data_end = end_dt
                self.data_interval = interval_minutes

            data = {
                "Date": dateRange,
                "FlowData": flowDataRange,
                "DepthData": depthDataRange,
                "VelocityData": velocityDataRange,
            }

            self.data = pd.DataFrame(data)
            self.data_date_updated = datetime.now()

        except Exception as e:  # Capture the exception details
            QMessageBox.critical(
                None,
                'Error Parsing FDV Data',
                f"Error parsing: {os.path.basename(fileSpec)}\n\nException: {str(e)}",
                QMessageBox.Ok
            )

    def get_r_data_from_file(self, fileSpec: str):

        try:
            with open(fileSpec, 'r', encoding="utf-8") as org_data:

                file_data = parse_file(fileSpec)

                all_units = [unit for record in file_data["payload"] for unit in record]

                constants = file_data["constants"]

                # Parse the START and END dates using the helper.
                start_dt = parse_date(constants["START"])
                end_dt = parse_date(constants["END"])
                # duration_hrs = (end_dt - start_dt).total_seconds() / 3600
                duration_mins = (end_dt - start_dt).total_seconds() / 60

                # Get the INTERVAL (assumed to be in minutes)
                interval_minutes = int(constants["INTERVAL"])
                interval = timedelta(minutes=interval_minutes)

                # Generate the date range.
                # import numpy as np
                dateRange: List[datetime] = np.arange(start_dt, end_dt + interval, interval).tolist()

                no_of_records = int(duration_mins / interval_minutes) + 1
                i_record = 0

                intensityDataRange: List[float] = []
                for unit in all_units:
                    i_record += 1
                    if i_record <= no_of_records:
                        intensityDataRange.append(float(unit["INTENSITY"]))

                # Check that the number of dates matches the number of data units.
                if len(dateRange) != len(intensityDataRange):
                    print("Warning: Mismatch in number of timestamps and data points!")

                self.data_start = start_dt
                self.data_end = end_dt
                self.data_interval = interval_minutes
                
            data = {"Date": dateRange, "IntensityData": intensityDataRange}

            self.data = pd.DataFrame(data)
            self.data_date_updated = datetime.now()            

        except Exception as e:  # Capture the exception details
            QMessageBox.critical(
                None,
                'Error Parsing FDV Data',
                f"Error parsing: {os.path.basename(fileSpec)}\n\nException: {str(e)}",
                QMessageBox.Ok
            )        

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

    def writeRFileFromProcessedData(self, file_path: str):
            
        # Define the header values.
        header = {
            "DATA_FORMAT": "1,ASCII",
            "IDENTIFIER": f"1,{self.client_ref}",
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
            Constant('START', 'GMT', self.data['Date'].iloc[0]),
            # Constant('END', 'GMT', rg.dateRange[-1] + timedelta(minutes=rg.rgTimestep)),
            Constant('END', 'GMT', self.data['Date'].iloc[-1]),
            Constant('INTERVAL', 'MIN', self.data_interval)
        ]
        
        # Build the constants block.
        constants_lines = write_constants(constants, constants_format)
        
        # RECORD_LENGTH: here we extract the numeric width from the header.
        record_length = int(header["RECORD_LENGTH"].split(",")[1].strip())
        # payload_lines = write_rg_payload(rg, header["FORMAT"], record_length, header["FIELD"])
        payload_lines = write_fsm_rg_payload(self, header["FORMAT"], record_length)
        
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
        file_spec = os.path.join(file_path, f"{self.client_ref}.r")

        if os.path.exists(file_spec):
            print(f"File {file_spec} already exists.")
        else:
            with open(file_spec, "w", encoding="utf-8") as f:
                for line in file_lines:
                    f.write(line + "\n")        

    def writeFDVFileFromProcessedData(self, file_path: str):

        # Define the header values.
        header = {
            "DATA_FORMAT": "1,ASCII",
            "IDENTIFIER": f"1,{self.client_ref}",
            "FIELD": "3,FLOW,DEPTH,VELOCITY",
            "UNITS": "3,L/S,MM,M/S",
            "FORMAT": "4,I5,I5,F5.2,[5]",
            "RECORD_LENGTH": "I2,75"
        }
        header_lines = write_header(header)

        constants_format = '8,I6,F7.3,2X,A20/D10,2X,D10,I4'
        
        Constant = namedtuple('Constant', ['name', 'units', 'value'])

        constants = [
            Constant('HEIGHT', 'MM', self.fm_pipe_height_mm),  #Need some code here to convert the x,y to a national grid reference 
            Constant('MIN_VEL', 'M/S', min(self.data['VelocityData'])),
            Constant('MANHOLE_NO', '', ''),
            Constant('START', 'GMT', self.data['Date'].iloc[0]),
            Constant('END', 'GMT', self.data['Date'].iloc[-1]),
            Constant('INTERVAL', 'MIN', self.data_interval)
        ]

        # Build the constants block.
        constants_lines = write_constants(constants, constants_format)
        
        # RECORD_LENGTH: here we extract the numeric width from the header.
        record_length = int(header["RECORD_LENGTH"].split(",")[1].strip())
        # payload_lines = write_fm_payload(fm, header["FORMAT"], record_length, header["FIELD"])
        payload_lines = write_fsm_fm_payload(self, header["FORMAT"], record_length)
        
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
        file_spec = os.path.join(file_path, f"{self.client_ref}.fdv")

        if os.path.exists(file_spec):
            print(f"File {file_spec} already exists.")
        else:
            with open(file_spec, "w", encoding="utf-8") as f:
                for line in file_lines:
                    f.write(line + "\n")

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
        # self.rainfall_file_format: str = '{inst_id}_02.dat'
        # self.depth_file_format: str = '{inst_id}_06.dat'
        # self.velocity_file_format: str = '{inst_id}_07.dat'
        # self.battery_file_format: str = '{inst_id}_08.dat'
        # self.pumplogger_file_format: str = '{inst_id}.csv'
        self.rainfall_file_format: str = '{ast_id}_02.dat'
        self.depth_file_format: str = '{ast_id}_06.dat'
        self.velocity_file_format: str = '{ast_id}_07.dat'
        self.battery_file_format: str = '{ast_id}_08.dat'
        self.pumplogger_file_format: str = '{ast_id}.csv'

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


class fsmInspection(object):

    def __init__(self):
        self.inspection_id: int = 1
        self.install_id: str = ""
        self.inspection_date: datetime = datetime.strptime(
            '2172-05-12', '%Y-%m-%d')
        self.inspection_sheet: Optional[bytes] = None
        self.inspection_sheet_filename: str = ''
        self.inspection_type: str = ''

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
        self.interim_id: int = 1
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

    def from_database_row_dict(self, row_dict:Dict):

        self.interim_id = row_dict.get('interim_id')
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

    def from_database_row_dict(self, row_dict:Dict):

        self.picture_id = row_dict.get('picture_id')
        self.install_id = row_dict.get('install_id')
        # self.picture_taken_date = datetime.fromisoformat(row[2])
        if isinstance(row_dict.get('picture_taken_date'), str):
            self.picture_taken_date = datetime.fromisoformat(row_dict['picture_taken_date'])
        self.picture_type = row_dict.get('picture_type')
        self.picture_comment = row_dict.get('picture_comment')
        if row_dict.get("picture") in (None, b''):
            self.picture = None
        else:
            self.picture = row_dict["picture"]


class fsmStormEvent(object):

    def __init__(self):
        self.storm_event_id: str = ''
        self.se_start: datetime = datetime.strptime('2172-05-12', '%Y-%m-%d')
        self.se_end: datetime = datetime.strptime('2172-05-12', '%Y-%m-%d')

    def from_database_row_dict(self, row_dict:Dict):

        self.storm_event_id = row_dict.get('storm_event_id')
        if isinstance(row_dict.get('se_start'), str):
            self.se_start = datetime.fromisoformat(row_dict['se_start'])
        if isinstance(row_dict.get('se_end'), str):
            self.se_end = datetime.fromisoformat(row_dict['se_end'])


class fsmProject(object):

    def __init__(self):
        self.job_number: str = ''
        self.job_name: str = ''
        self.client: str = ''
        self.client_job_ref: str = ''
        self.survey_start_date: Optional[datetime] = datetime.now()
        self.survey_end_date: Optional[datetime] = datetime.min
        self.survey_complete: bool = False
        self.dict_fsm_sites: Dict[str, fsmSite] = {}
        self.dict_fsm_monitors: Dict[str, fsmMonitor] = {}
        self.dict_fsm_installs: Dict[str, fsmInstall] = {}
        self.dict_fsm_rawdata: Dict[int, fsmRawData] = {}
        self.dict_fsm_inspections: Dict[int, fsmInspection] = {}
        self.dict_fsm_interims: Dict[int, fsmInterim] = {}
        self.dict_fsm_interim_reviews: Dict[int, fsmInterimReview] = {}
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
            self.dict_fsm_monitors[mon.monitor_asset_id] = mon

        try:
            c.execute(f"SELECT * FROM {Tables.FSM_INSTALL}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.FSM_INSTALL}' does not exist.")
            return  # Return without attempting to fetch rows

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
            self.dict_fsm_interims[interim.interim_id] = interim

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
                             (a_int.interim_id, a_int.interim_start_date.isoformat(), a_int.interim_end_date.isoformat(),
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
            logger.debug("fsmProject.write_to_database Completed")

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

    def add_install(self, objInstall: fsmInstall) -> bool:

        if objInstall.install_id not in self.dict_fsm_installs:
            self.dict_fsm_installs[objInstall.install_id] = objInstall
            return True
        return False

    def get_install(self, install_id: str) -> Optional[fsmInstall]:

        if install_id in self.dict_fsm_installs:
            return self.dict_fsm_installs[install_id]
        
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

    def delete_interim_reviews_by_interim_id(self, interim_id: str):
        # Collect keys to delete
        keys_to_delete = []
        for interim_review_id, interim_review in self.dict_fsm_interim_reviews.items():
            if interim_review.interim_id == interim_id:
                keys_to_delete.append(interim_review_id)
        # Delete collected keys
        for key in keys_to_delete:
            del self.dict_fsm_interim_reviews[key]

    def delete_interim(self, interim_id: str) -> bool:
        """Remove an interim record by its ID."""
        if interim_id in self.dict_fsm_interims:
            self.delete_interim_reviews_by_interim_id(interim_id)
            del self.dict_fsm_interims[interim_id]
            return True
        return False

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
                    return installl

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

        if objInt.interim_id not in self.dict_fsm_interims:
            self.dict_fsm_interims[objInt.interim_id] = objInt
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

    def get_interim_review(self, interim_review_id: Optional[int] = None, interim_id: Optional[int] = None,
                           install_id: Optional[str] = None) -> Optional[fsmInterimReview]:
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
                if a_inst.class_data_ml is not None:
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
        if pipe_text in ['Circular', 'Rectangular', 'Arched', 'Egg', 'Egg 2', 'Oval', 'U-Shaped']:
            return pipe_text[0]
        elif pipe_text in ['Cunette']:
            return 'Cn'
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

    def filter_interim_reviews_by_interim_id(self, interim_id: int) -> Dict[int, fsmInterimReview]:
        return {key: review for key, review in self.dict_fsm_interim_reviews.items() if review.interim_id == interim_id}

    def add_interim_review(self, objIntRev: fsmInterimReview) -> bool:

        if objIntRev.interim_review_id not in self.dict_fsm_interim_reviews:
            self.dict_fsm_interim_reviews[objIntRev.interim_review_id] = objIntRev
            return True
        return False

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

    def uninstalled(self, inst_id: str) -> bool:

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

        return results

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
        # Convert timestamps to datetime
        depth_timestamps = pd.to_datetime(self.raw_data.dep_data["Timestamp"])
        velocity_timestamps = pd.to_datetime(self.raw_data.vel_data["Timestamp"])

        # Find overlapping timestamps
        common_timestamps = np.intersect1d(depth_timestamps, velocity_timestamps)

        # Filter data to keep only the overlapping timestamps
        depth_mask = depth_timestamps.isin(common_timestamps)
        velocity_mask = velocity_timestamps.isin(common_timestamps)

        # Convert timestamps back to a consistent array
        timestamps = pd.to_datetime(common_timestamps)
        original_depths = self.raw_data.dep_data.loc[depth_mask, "Value"].values
        original_velocities = self.raw_data.vel_data.loc[velocity_mask, "Value"].values
                
        # timestamps = pd.to_datetime(self.raw_data.dep_data['Timestamp'])
        # original_depths = self.raw_data.dep_data['Value'].values
        # original_velocities = self.raw_data.vel_data['Value'].values

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

        result_df = pd.DataFrame({
            'Date': corrected_timestamps,
            'FlowData': flows * 1000,
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