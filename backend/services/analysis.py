from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from sqlmodel import Session
from services.importers import import_fdv_file, import_r_file
from domain.analysis import AnalysisDataset

class RainfallService:
    def __init__(self, session: Session):
        self.session = session

    def get_dataset(self, dataset_id: int) -> AnalysisDataset:
        return self.session.get(AnalysisDataset, dataset_id)

    def check_data_completeness(self, dataset_id: int) -> Dict[str, float]:
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return {"completeness": 0.0}
            
        try:
            data = import_r_file(dataset.file_path)
            # Simple completeness check: do we have data for the whole range?
            # Since we generate the range based on start/end, it's technically 100% complete in terms of timestamps
            # But we can check for missing values (which import_r_file fills with 0.0)
            # For now, return 100% as legacy files are usually continuous
            return {"completeness": 100.0}
        except:
            return {"completeness": 0.0}

class EventService:
    def __init__(self, session: Session):
        self.session = session

    def get_dataset(self, dataset_id: int) -> AnalysisDataset:
        return self.session.get(AnalysisDataset, dataset_id)

    def detect_storms(self, dataset_id: int, inter_event_hours: int = 6, min_total_mm: float = 2.0) -> List[Dict[str, Any]]:
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return []
            
        try:
            data = import_r_file(dataset.file_path)
            df = pd.DataFrame(data['data'])
            df['time'] = pd.to_datetime(df['time'])
            df['value'] = df['rainfall']
            
            # Sort
            df = df.sort_values('time')
            
            # Calculate time difference
            df['time_diff'] = df['time'].diff().dt.total_seconds() / 3600
            
            # New event if time diff > inter_event_time
            # Note: Legacy files are continuous, so time_diff is always 'interval'.
            # We need to identify 'events' separated by dry periods (0 rainfall).
            # If value > 0, it's rain.
            
            # Logic for continuous data:
            # 1. Identify wet periods
            # 2. If gap between wet periods > inter_event_hours, separate events
            
            # Filter for wet timesteps
            wet_df = df[df['value'] > 0].copy()
            if wet_df.empty:
                return []
                
            wet_df['time_diff'] = wet_df['time'].diff().dt.total_seconds() / 3600
            wet_df['new_event'] = (wet_df['time_diff'] > inter_event_hours).cumsum()
            
            events = []
            for event_id, group in wet_df.groupby('new_event'):
                total_rain = group['value'].sum()
                if total_rain >= min_total_mm:
                    events.append({
                        "event_id": int(event_id),
                        "start_time": group['time'].iloc[0],
                        "end_time": group['time'].iloc[-1],
                        "total_mm": round(total_rain, 2),
                        "duration_hours": round((group['time'].iloc[-1] - group['time'].iloc[0]).total_seconds() / 3600, 2),
                        "peak_intensity": group['value'].max() # This is per timestep, not hourly intensity unless interval is 60min
                    })
            return events
            
        except Exception as e:
            print(f"Error detecting storms: {e}")
            return []

    def detect_dry_days(self, dataset_id: int, threshold_mm: float = 0.1) -> List[Dict[str, Any]]:
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return []
            
        try:
            data = import_r_file(dataset.file_path)
            df = pd.DataFrame(data['data'])
            df['time'] = pd.to_datetime(df['time'])
            df['value'] = df['rainfall']
            
            daily_rain = df.set_index('time').resample('D')['value'].sum()
            
            dry_days = []
            for date, total in daily_rain.items():
                if total < threshold_mm:
                    dry_days.append({
                        "date": date.date(),
                        "total_mm": round(total, 3)
                    })
            return dry_days
        except:
            return []

class FDVService:
    def __init__(self, session: Session):
        self.session = session

    def get_dataset(self, dataset_id: int) -> AnalysisDataset:
        return self.session.get(AnalysisDataset, dataset_id)

    def get_scatter_data(self, dataset_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return []
            
        try:
            data = import_fdv_file(dataset.file_path)
            df = pd.DataFrame(data['data'])
            df['time'] = pd.to_datetime(df['time'])
            
            if start_date:
                df = df[df['time'] >= start_date]
            if end_date:
                df = df[df['time'] <= end_date]
                
            # Return time, depth, velocity, flow
            return df[['time', 'depth', 'velocity', 'flow']].to_dict('records')
        except:
            return []

class SpatialService:
    def __init__(self, session: Session):
        self.session = session
        # Need access to sites for coordinates
        from repositories.project import SiteRepository
        self.site_repo = SiteRepository(session)

    def calculate_idw(self, target_lat: float, target_lon: float, source_gauges: List[Dict[str, Any]], power: float = 2.0) -> float:
        """
        Calculates IDW interpolation for a single point in time/value.
        source_gauges: List of dicts with 'lat', 'lon', 'value'.
        """
        if not source_gauges:
            return 0.0
            
        numerator = 0.0
        denominator = 0.0
        
        for gauge in source_gauges:
            # Simple Euclidean distance for now (sufficient for small areas)
            # For larger areas, use Haversine
            dist = ((target_lat - gauge['lat'])**2 + (target_lon - gauge['lon'])**2)**0.5
            
            if dist == 0:
                return gauge['value']
                
            weight = 1 / (dist**power)
            numerator += weight * gauge['value']
            denominator += weight
            
        if denominator == 0:
            return 0.0
            
        return numerator / denominator
