import struct
import os
import io
import csv
from datetime import datetime, timedelta, date, time
import pandas as pd
import numpy as np
from typing import Tuple, List, Optional
from sqlmodel import Session, select
from domain.fsm import FsmProject, Install, Monitor, RawDataSettings
from services.timeseries import TimeSeriesService

def bytes_to_text(data: bytes, encoding='utf-8') -> str:
    try:
        decoded_text = data.decode(encoding).rstrip('\x00')
        return decoded_text
    except UnicodeDecodeError:
        decoded_text = data.decode('ansi').rstrip('\x00')
        return decoded_text

class BinaryParser:
    @staticmethod
    def parse_dat_file(file_source, since: Optional[datetime] = None) -> Tuple[pd.DataFrame, str]:
        dt_timestamps = []
        i_values = []
        should_close = False
        
        if isinstance(file_source, str):
            if not os.path.exists(file_source):
                return pd.DataFrame(), "" # or raise?
            file = open(file_source, "rb")
            should_close = True
        else:
            file = file_source

        try:
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0, 0)
            
            # Header parsing
            s_header_bytes = file.read(30)
            if not s_header_bytes:
                 return pd.DataFrame(), ""
            
            s_header = bytes_to_text(s_header_bytes)
                 
            i_flag = struct.unpack('<B', file.read(1))[0]
            i_year = struct.unpack('<H', file.read(2))[0]
            i_month = struct.unpack('<H', file.read(2))[0]
            i_day = struct.unpack('<H', file.read(2))[0]
            i_hour = struct.unpack('<H', file.read(2))[0]
            i_minute = struct.unpack('<H', file.read(2))[0]
            i_second = struct.unpack('<H', file.read(2))[0]
            
            interval_bytes = file.read(2)
            i_interval = int((struct.unpack('<H', interval_bytes)[0])/(10*60))
            
            s_measurement_type = bytes_to_text(file.read(15))
            s_units = bytes_to_text(file.read(10))
            f_max_value = struct.unpack('<f', file.read(4))[0]
            f_min_value = struct.unpack('<f', file.read(4))[0]
            
            start_datetime = datetime(i_year, i_month, i_day, i_hour, i_minute, i_second)
            
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
            else:
                no_of_bytes = 1
                max_threshold = 255

            i = 0
            file.seek(78) # Fixed header size? Legacy says my_pos = 78

            while True:
                float_bytes = file.read(no_of_bytes)
                if not float_bytes or len(float_bytes) < no_of_bytes:
                    break

                try:
                    if i_flag == 2:
                        int_value = struct.unpack('<B', float_bytes)[0]
                    elif i_flag == 8:
                        int_value = struct.unpack('<H', float_bytes)[0]
                    elif i_flag == 17:
                        int_value = struct.unpack('<I', float_bytes)[0]
                    
                    if i_flag != 17:
                        if int_value >= max_threshold:
                            val = np.nan
                        else:
                            val = int_value / max_threshold
                            val = f_min_value + ((f_max_value - f_min_value) * val)
                        
                        i_values.append(val)
                        dt_timestamps.append(start_datetime + timedelta(minutes=i * i_interval))
                    else:
                        if int_value < 4294967295:
                            tip_time = start_datetime + timedelta(seconds=int_value)
                            # For Rain Gauge (flag 17), we store timestamps of tips
                            dt_timestamps.append(tip_time) 
                            # Value is just 1 tip? Or accumulator? 
                            # Legacy returns just timestamps for flag 17.
                except Exception as e:
                    print(f"Error processing value at index {i}: {e}")
                
                i += 1
        finally:
            if should_close:
                file.close()

        if i_flag == 17:
            # Rain Gauge Dat format - only timestamps
            df = pd.DataFrame({'Timestamp': dt_timestamps})
            # Add value column? Legacy just returns timestamp DF for tips
            # But TimeSeriesService expects 'time' and 'value'.
            # We'll set value to 1 for each tip, or use generic structure.
            df['Value'] = 1.0 
        else:
            i_values = [round(val, 3) if not np.isnan(val) else val for val in i_values]
            df = pd.DataFrame({'Timestamp': dt_timestamps, 'Value': i_values})
        
        if since is not None:
            df = df[df['Timestamp'] > since]
            
        return df, s_units

    @staticmethod
    def parse_flo_file(file_source, since: Optional[datetime] = None) -> Tuple[pd.DataFrame, str]:
        tip_timestamps = []
        should_close = False
        
        if isinstance(file_source, str):
            if not os.path.exists(file_source):
                 return pd.DataFrame(), ""
            file = open(file_source, "rb")
            should_close = True
        else:
            file = file_source

        try:
            file.seek(0, 2)
            file_size = file.tell()
            
            file.seek(133, 0)
            i_year = struct.unpack('<B', file.read(1))[0]
            full_year = 2000 + i_year
            
            file.seek(136, 0)
            i_day = struct.unpack('<B', file.read(1))[0]
            i_month = struct.unpack('<B', file.read(1))[0]
            
            start_date = date(full_year, i_month, i_day)
            current_date = start_date
            
            my_pos = 138
            file.seek(138, 0)

            while True:
                if my_pos >= file_size:
                    break
                    
                byte_val = file.read(1)
                if not byte_val: 
                    break
                    
                i_hour = struct.unpack('<B', byte_val)[0]
                my_pos += 1

                if i_hour == 254:
                    current_date = current_date + timedelta(days=1)
                    continue

                if my_pos >= file_size:
                    break
                
                byte_val = file.read(1)
                if not byte_val:
                    break
                    
                i_minute = struct.unpack('<B', byte_val)[0]
                my_pos += 1

                tip_time = time(i_hour, i_minute)
                tip_datetime = datetime.combine(current_date, tip_time)
                tip_timestamps.append(tip_datetime)

        finally:
            if should_close:
                file.close()

        df = pd.DataFrame({'Timestamp': tip_timestamps})
        df['Value'] = 1.0 # Each row is a tip
        
        if since is not None:
            df = df[df['Timestamp'] > since]
            
        return df, ''

class CSVParser:
    @staticmethod
    def parse_hobo_csv(file_path: str, since: Optional[datetime] = None) -> pd.DataFrame:
        if not os.path.exists(file_path):
            return pd.DataFrame()
            
        dt_timestamps = []
        i_values = []
        
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            # Legacy looks like it processes all rows? 
            # "rows = list(reader)" then "for row in reader" -> reader is exhausted if one reads it first? 
            # Legacy code: rows = list(reader); file.seek(0); ... for row in reader
            
            # Skip header if needed? Legacy just iterates.
            # But line 2004 tries to parse float(row[2]). 
            # We'll assume standard HOBO format.
            
            for row in reader:
                if len(row) < 3:
                     continue
                if not row[0]: # empty first col usually index?
                    continue
                    
                try:
                    # Row[1] is Date, Row[2] is Value
                    # Legacy: datetime.strptime(row[1].strip(), "%m/%d/%y %I:%M:%S %p")
                    ts_str = row[1].strip()
                    try:
                        a_datetime = datetime.strptime(ts_str, "%m/%d/%y %I:%M:%S %p")
                    except ValueError:
                         # Try other formats?
                         continue
                         
                    value = float(row[2].strip())
                    
                    dt_timestamps.append(a_datetime)
                    i_values.append(value)
                    
                except (ValueError, IndexError):
                    continue
                    
        df = pd.DataFrame({'Timestamp': dt_timestamps, 'Value': i_values})
        if since is not None:
            df = df[df['Timestamp'] > since]
            
        return df

class IngestionService:
    def __init__(self, session: Session):
        self.session = session
        self.ts_service = TimeSeriesService(session)

    def decode_file_format(self, file_format: str, install: Install) -> str:
        if not file_format:
            return ""
            
        decoded = file_format
        
        # We need to access related objects. Setup eager loading or assume lazy loading works in session.
        # {pmac_id}
        if '{pmac_id}' in decoded:
            if install.monitor and install.monitor.pmac_id:
                decoded = decoded.replace('{pmac_id}', install.monitor.pmac_id)
            else:
                 # What if no monitor?
                 pass
                 
        # {inst_id}
        if '{inst_id}' in decoded:
            decoded = decoded.replace('{inst_id}', str(install.install_id)) # install_id is string field
            
        # {ast_id}
        if '{ast_id}' in decoded:
            if install.monitor:
                decoded = decoded.replace('{ast_id}', install.monitor.monitor_asset_id)
                
        # {cl_ref}
        if '{cl_ref}' in decoded:
            decoded = decoded.replace('{cl_ref}', install.client_ref or "")
            
        # {site_id}
        if '{site_id}' in decoded:
             # install.site_id is int foreign key. install.site.site_id is string.
             # Legacy used install.install_site_id which implies it might be denormalized or related.
             if install.site:
                 decoded = decoded.replace('{site_id}', install.site.site_id)
                 
        # {prj_id}
        if '{prj_id}' in decoded:
            if install.project:
                decoded = decoded.replace('{prj_id}', install.project.job_number)
                
        return decoded

    def get_since_timestamp(self, install_id: int, variable: str) -> Optional[datetime]:
        # Query last TimeSeries end_time for this install & variable
        # But we create new TimeSeries records for chunks. 
        # So we want the MAX end_time of all TimeSeries for this variable.
        # Legacy tracked it in RawData.dep_data_end etc.
        # New system: Query TimeSeries table.
        from domain.fsm import TimeSeries
        
        stmt = select(TimeSeries).where(
            TimeSeries.install_id == install_id,
            TimeSeries.variable == variable
        ).order_by(TimeSeries.end_time.desc()).limit(1)
        
        result = self.session.exec(stmt).first()
        if result:
            return result.end_time
        return None

    def ingest_project(self, project_id: int):
        project = self.session.get(FsmProject, project_id)
        if not project:
            return
            
        default_path = project.default_download_path
        
        # Iterate all installs
        for install in project.installs:
            self.ingest_install(install, default_path)
            
        # Update last ingestion date
        project.last_ingestion_date = datetime.now()
        self.session.add(project)
        self.session.commit()
    
    def ingest_install_by_id(self, install_id: int):
        """
        Ingest a single install by ID. Fetches the install and its project's default path.
        """
        install = self.session.get(Install, install_id)
        if not install:
            print(f"Install {install_id} not found")
            return
        
        # Get project's default path as fallback
        default_path = None
        if install.project:
            default_path = install.project.default_download_path
        
        # Call the main ingest_install method
        self.ingest_install(install, default_path)

    def ingest_install(self, install: Install, default_path: Optional[str]):
        settings = install.raw_data_settings
        
        # Determine base path
        # If settings is None, or file_path is None/Empty/Invalid, try default_path
        base_path = settings.file_path if settings else None
        if not base_path or not os.path.isdir(base_path):
            base_path = default_path
            
        if not base_path or not os.path.isdir(base_path):
            return # No valid path
            
        # Helper to process a specific file type
        def process_file_type(format_template: str, parser_func, variable: str, parsing_args: dict = {}):
            if not format_template:
                return
                
            filename = self.decode_file_format(format_template, install)
            full_path = os.path.join(base_path, filename)
            
            if not os.path.exists(full_path):
                return
                
            # Determine 'since'
            since = self.get_since_timestamp(install.id, variable)
            
            # Parse
            try:
                result = parser_func(full_path, since=since, **parsing_args)
                # Unwrap tuple if parser returns (df, units)
                units = None
                if isinstance(result, tuple):
                    df = result[0]
                    units = result[1]
                else:
                    df = result
                    
                if not df.empty:
                    # Save
                    self.ts_service.save_dataframe(
                        df, 
                        install.id, 
                        variable, 
                        monitor_id=install.monitor_id, 
                        unit=units
                    )
            except Exception as e:
                print(f"Error ingesting {variable} for install {install.id}: {e}")

        # Rain Gauge
        if install.install_type == 'Rain Gauge':
            # Check extension to decide flo vs dat
            template = settings.rainfall_file_format if settings else None
            if not template:
                template = '{ast_id}_02.dat'
                
            if template:
                fname = self.decode_file_format(template, install)
                if fname.lower().endswith('.flo'):
                    process_file_type(template, BinaryParser.parse_flo_file, 'Rain')
                else:
                    process_file_type(template, BinaryParser.parse_dat_file, 'Rain')

        # Flow / Depth Monitor
        if install.install_type in ['Flow Monitor', 'Depth Monitor']:
             depth_fmt = (settings.depth_file_format if settings else None) or '{ast_id}_06.dat'
             vel_fmt = (settings.velocity_file_format if settings else None) or '{ast_id}_07.dat'
             
             process_file_type(depth_fmt, BinaryParser.parse_dat_file, 'Depth')
             process_file_type(vel_fmt, BinaryParser.parse_dat_file, 'Velocity')

        # Battery
        batt_fmt = (settings.battery_file_format if settings else None) or '{ast_id}_08.dat'
        process_file_type(batt_fmt, BinaryParser.parse_dat_file, 'Voltage')
        
        # Pump Logger
        if install.install_type == 'Pump Logger':
             # Wrapper for CSV to match signature
             def csv_wrapper(path, since=None):
                 return CSVParser.parse_hobo_csv(path, since=since), ""
             
             pl_fmt = (settings.pumplogger_file_format if settings else None) or '{ast_id}.hobo'
             process_file_type(pl_fmt, csv_wrapper, 'Pump_State')
