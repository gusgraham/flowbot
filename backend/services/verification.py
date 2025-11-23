from typing import List, Dict, Any
from sqlmodel import Session
from services.timeseries import TimeSeriesService
from infra.storage import StorageService
from domain.events import TimeSeries

class VerificationService:
    def __init__(self, session: Session):
        self.session = session
        self.ts_service = TimeSeriesService(session)
        self.storage = StorageService()

    def import_model_results(self, monitor_id: int, file_content: bytes, filename: str) -> List[TimeSeries]:
        """
        Imports model results as TimeSeries with data_type="Model".
        """
        # 1. Save file to disk
        file_path = self.storage.save_file(file_content, filename, subfolder=f"models/{monitor_id}")
        
        # 2. Process file using TimeSeriesService
        # We assume model results follow the same CSV format (Date, Flow, Depth, Velocity)
        # If format differs, we'd need a specific parser here.
        # Passing data_type="Model"
        return self.ts_service.process_upload(
            file_path=file_path, 
            original_filename=filename, 
            monitor_id=monitor_id, 
            data_type="Model"
        )

    def get_comparison_data(self, monitor_id: int, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Fetches and aligns Observed (Raw/Processed) vs Modelled data.
        """
        import pandas as pd
        
        # 1. Fetch all TimeSeries for this monitor
        ts_records = self.ts_service.list_by_monitor(monitor_id)
        
        obs_data = {} # {variable: pd.DataFrame}
        model_data = {} # {variable: pd.DataFrame}
        
        # 2. Load data into dataframes
        for record in ts_records:
            try:
                df = pd.read_parquet(record.filename)
                if df.empty: continue
                
                # Normalize columns
                df = df.rename(columns={'value': 'value', 'time': 'time'})
                df['time'] = pd.to_datetime(df['time'])
                
                # Filter by date
                if start_date:
                    df = df[df['time'] >= pd.to_datetime(start_date)]
                if end_date:
                    df = df[df['time'] <= pd.to_datetime(end_date)]
                    
                if df.empty: continue
                
                var_name = record.variable.lower()
                
                if record.data_type == "Model":
                    if var_name not in model_data:
                        model_data[var_name] = df
                    else:
                        model_data[var_name] = pd.concat([model_data[var_name], df])
                else:
                    # Prefer Processed over Raw if we had that logic, for now just take what's there
                    if var_name not in obs_data:
                        obs_data[var_name] = df
                    else:
                        obs_data[var_name] = pd.concat([obs_data[var_name], df])
                        
            except Exception as e:
                print(f"Error loading {record.filename}: {e}")
                continue
                
        # 3. Align and Format for Frontend
        # We want a structure like: { "flow": [{time, obs, model}], "depth": ... }
        
        result = {}
        
        for var in ['flow', 'depth', 'velocity']:
            if var in obs_data or var in model_data:
                # Merge
                obs_df = obs_data.get(var, pd.DataFrame(columns=['time', 'value'])).rename(columns={'value': 'obs'})
                model_df = model_data.get(var, pd.DataFrame(columns=['time', 'value'])).rename(columns={'value': 'model'})
                
                if obs_df.empty and model_df.empty:
                    continue
                    
                # Outer join to keep all timestamps
                merged = pd.merge(obs_df, model_df, on='time', how='outer').sort_values('time')
                
                # Fill NaNs with None for JSON
                merged = merged.where(pd.notnull(merged), None)
                
                result[var] = merged.to_dict('records')
                
        return {
            "monitor_id": monitor_id,
            "comparison": result
        }

    def calculate_scores(self, monitor_id: int, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Calculates goodness-of-fit scores (NSE, R2, Peak Error, Volume Error).
        """
        import numpy as np
        
        # 1. Get aligned data
        comparison = self.get_comparison_data(monitor_id, start_date, end_date)
        data = comparison.get("comparison", {})
        
        scores = {}
        
        for var, records in data.items():
            if not records:
                continue
                
            # Extract arrays, filtering out None
            valid_records = [r for r in records if r['obs'] is not None and r['model'] is not None]
            if not valid_records:
                continue
                
            obs = np.array([r['obs'] for r in valid_records], dtype=float)
            model = np.array([r['model'] for r in valid_records], dtype=float)
            
            if len(obs) < 2:
                continue
                
            # NSE
            mean_obs = np.mean(obs)
            numerator = np.sum((obs - model) ** 2)
            denominator = np.sum((obs - mean_obs) ** 2)
            nse = 1 - (numerator / denominator) if denominator != 0 else 0.0
            
            # Peak Error
            max_obs = np.max(obs)
            max_model = np.max(model)
            peak_error = (max_model - max_obs) / max_obs if max_obs != 0 else 0.0
            
            # Volume Error
            sum_obs = np.sum(obs)
            sum_model = np.sum(model)
            vol_error = (sum_model - sum_obs) / sum_obs if sum_obs != 0 else 0.0
            
            scores[var] = {
                "nse": round(float(nse), 3),
                "peak_error_percent": round(float(peak_error * 100), 1),
                "volume_error_percent": round(float(vol_error * 100), 1),
                "max_obs": round(float(max_obs), 3),
                "max_model": round(float(max_model), 3)
            }
            
        return {
            "monitor_id": monitor_id,
            "scores": scores
        }
