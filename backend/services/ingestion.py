import struct
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Tuple, List, Optional

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
        
        if isinstance(file_source, str):
            if not os.path.exists(file_source):
                raise FileNotFoundError(f"File not found: {file_source}")
            file = open(file_source, "rb")
            should_close = True
        else:
            file = file_source
            should_close = False

        try:
            # Header parsing
            s_header = bytes_to_text(file.read(30))
            if not s_header:
                 raise ValueError("Empty file or invalid header")
                 
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
            tip_timestamps = []

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
                            tip_timestamps.append(tip_time)
                except Exception as e:
                    print(f"Error processing value at index {i}: {e}")
                
                i += 1
        finally:
            if should_close:
                file.close()

        if i_flag == 17:
            df = pd.DataFrame({'Timestamp': tip_timestamps})
        else:
            i_values = [round(val, 3) if not np.isnan(val) else val for val in i_values]
            df = pd.DataFrame({'Timestamp': dt_timestamps, 'Value': i_values})
        
        if since is not None:
            df = df[df['Timestamp'] > since]
            
        return df, s_units

class CSVParser:
    @staticmethod
    def parse_hobo_csv(file_path: str) -> pd.DataFrame:
        # Placeholder for HOBO CSV parsing
        pass

class IngestionService:
    def __init__(self, session=None):
        self.session = session

    def ingest_raw_file(self, file_path: str) -> pd.DataFrame:
        if file_path.lower().endswith('.dat'):
            df, units = BinaryParser.parse_dat_file(file_path)
            return df
        elif file_path.lower().endswith('.csv'):
            return pd.DataFrame()
        else:
            raise ValueError("Unsupported file type")

    def ingest_raw_data(self, install_id: int, file_content: bytes, data_type: str):
        import io
        from domain.fsm import RawData
        
        file_obj = io.BytesIO(file_content)
        # Try parsing as DAT first (legacy default)
        try:
            df, units = BinaryParser.parse_dat_file(file_obj)
        except Exception:
            # Fallback to CSV if DAT fails (or check extension if provided)
            # For now assume DAT
            raise ValueError("Failed to parse DAT file")
            
        # Convert to JSON compatible dict
        # Timestamps to ISO string
        df['Timestamp'] = df['Timestamp'].apply(lambda x: x.isoformat())
        data_dict = df.to_dict(orient='list')
        
        # Update or Create RawData
        # We need to find existing RawData for this install or create new
        if self.session:
            from sqlmodel import select
            statement = select(RawData).where(RawData.install_id == install_id)
            results = self.session.exec(statement)
            raw_data = results.first()
            
            if not raw_data:
                raw_data = RawData(install_id=install_id)
                
            if data_type == 'depth':
                raw_data.dep_data = data_dict
            elif data_type == 'velocity':
                raw_data.vel_data = data_dict
                
            self.session.add(raw_data)
            self.session.commit()
            self.session.refresh(raw_data)
            return raw_data
            
        return data_dict
