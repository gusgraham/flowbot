from typing import List, Dict, Any
import pandas as pd
import io
from sqlmodel import Session
from services.timeseries import TimeSeriesService
from infra.storage import StorageService
from domain.events import TimeSeries

class WQService:
    def __init__(self, session: Session):
        self.session = session
        self.ts_service = TimeSeriesService(session)
        self.storage = StorageService()

    def import_wq_data(self, monitor_id: int, file_content: bytes, filename: str) -> List[TimeSeries]:
        """
        Imports WQ data.
        Assumes CSV format: Date, pH, Ammonia, TSS, etc.
        """
        # 1. Save file to disk
        file_path = self.storage.save_file(file_content, filename, subfolder=f"wq/{monitor_id}")
        
        # 2. Parse CSV
        try:
            df = pd.read_csv(file_path)
            if 'Date' not in df.columns:
                raise ValueError("CSV must have a 'Date' column")
                
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
            df = df.sort_values('Date')
            
            start_time = df['Date'].iloc[0].to_pydatetime()
            end_time = df['Date'].iloc[-1].to_pydatetime()
            
            # Calculate interval (mode of diff)
            if len(df) > 1:
                interval = int(df['Date'].diff().mode()[0].total_seconds() / 60)
            else:
                interval = 0
            
            created_records = []
            
            # 3. Process each column (excluding Date)
            for col in df.columns:
                if col == 'Date':
                    continue
                    
                # Extract series
                series_df = df[['Date', col]].copy()
                series_df.columns = ['time', 'value']
                
                # Save as Parquet
                parquet_filename = f"{filename}_{col}.parquet"
                buf = io.BytesIO()
                series_df.to_parquet(buf, index=False)
                buf.seek(0)
                
                saved_path = self.storage.save_file(
                    buf.getvalue(), 
                    parquet_filename, 
                    subfolder=f"timeseries/monitors/{monitor_id}"
                )
                
                # 4. Create TimeSeries record
                # We use TimeSeriesRepository directly via ts_service.repo
                ts = TimeSeries(
                    monitor_id=monitor_id,
                    variable=col,
                    data_type="WQ_Sample",
                    start_time=start_time,
                    end_time=end_time,
                    interval_minutes=interval,
                    filename=saved_path
                )
                created_records.append(self.ts_service.repo.create(ts))
        
            return created_records
            
        except Exception as e:
            print(f"Error processing WQ file {filename}: {e}")
            raise e

    def get_wq_timeseries(self, monitor_id: int) -> List[Dict[str, Any]]:
        """
        Returns WQ data points for frontend.
        """
        ts_records = self.ts_service.list_by_monitor(monitor_id)
        wq_records = [ts for ts in ts_records if ts.data_type == "WQ_Sample"]
        
        result = []
        for record in wq_records:
            try:
                df = pd.read_parquet(record.filename)
                # Convert to list of dicts
                # { "variable": "pH", "data": [{time, value}, ...] }
                data_points = df.to_dict('records')
                result.append({
                    "variable": record.variable,
                    "data": data_points
                })
            except:
                continue
                
        return result

    def correlate_wq_flow(self, monitor_id: int) -> Dict[str, Any]:
        """
        Correlates WQ samples with Flow data.
        """
        # 1. Get WQ records
        ts_records = self.ts_service.list_by_monitor(monitor_id)
        wq_records = [ts for ts in ts_records if ts.data_type == "WQ_Sample"]
        
        # 2. Get Flow record
        flow_record = next((ts for ts in ts_records if ts.variable.lower() == "flow"), None)
        
        if not flow_record:
            return {"error": "No flow data found for this monitor"}
            
        try:
            flow_df = pd.read_parquet(flow_record.filename)
            flow_df['time'] = pd.to_datetime(flow_df['time'])
            flow_df = flow_df.sort_values('time')
        except:
            return {"error": "Could not read flow data"}
            
        correlations = {}
        
        for wq_rec in wq_records:
            try:
                wq_df = pd.read_parquet(wq_rec.filename)
                wq_df['time'] = pd.to_datetime(wq_df['time'])
                
                # Merge using merge_asof to find nearest flow value
                # direction='nearest' or 'backward'
                merged = pd.merge_asof(
                    wq_df.sort_values('time'), 
                    flow_df, 
                    on='time', 
                    direction='nearest',
                    tolerance=pd.Timedelta('15min') # Max 15 min difference
                )
                
                # Rename columns: value_x is WQ, value_y is Flow
                merged = merged.rename(columns={'value_x': 'wq_value', 'value_y': 'flow_value'})
                
                # Filter out rows where flow wasn't found (NaN)
                merged = merged.dropna(subset=['flow_value'])
                
                correlations[wq_rec.variable] = merged[['time', 'wq_value', 'flow_value']].to_dict('records')
                
            except Exception as e:
                print(f"Error correlating {wq_rec.variable}: {e}")
                continue
                
        return {
            "monitor_id": monitor_id,
            "correlations": correlations
        }
