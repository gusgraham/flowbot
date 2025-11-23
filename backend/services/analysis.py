import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlmodel import Session
from services.timeseries import TimeSeriesService
from domain.events import TimeSeries
        
        total_duration_minutes = 0
        covered_duration_minutes = 0
        
        sorted_records = sorted(ts_records, key=lambda x: x.start_time)
        if not sorted_records:
             return {"completeness": 0.0}

        global_start = sorted_records[0].start_time
        global_end = sorted_records[-1].end_time
        total_duration_minutes = (global_end - global_start).total_seconds() / 60
        
        if total_duration_minutes == 0:
            return {"completeness": 100.0}

        for record in sorted_records:
            duration = (record.end_time - record.start_time).total_seconds() / 60
            covered_duration_minutes += duration
            
        completeness = (covered_duration_minutes / total_duration_minutes) * 100
        return {
            "completeness": round(min(completeness, 100.0), 2),
            "gap_minutes": total_duration_minutes - covered_duration_minutes
        }

class EventService:
    def __init__(self, session: Session):
        self.session = session
        self.ts_service = TimeSeriesService(session)
        self.rainfall_service = RainfallService(session)

    def detect_storms(self, monitor_id: int, inter_event_time_hours: int = 6, min_total_mm: float = 2.0) -> List[Dict[str, Any]]:
        """
        Groups rainfall tips into storm events.
        inter_event_time_hours: Minimum time between tips to separate events.
        min_total_mm: Minimum total rainfall to qualify as a storm.
        """
        # 1. Get all rainfall data
        ts_records = self.ts_service.list_by_monitor(monitor_id)
        rain_records = [ts for ts in ts_records if ts.variable.lower() in ["rain", "rainfall", "precip"]]
        
        if not rain_records:
            return []

        all_data = []
        for record in rain_records:
            try:
                df = pd.read_parquet(record.filename)
                if not df.empty:
                    all_data.append(df)
            except:
                continue
        
        if not all_data:
            return []
            
        # Combine and sort
        full_df = pd.concat(all_data).sort_values('time')
        
        # 2. Group into events
        # Calculate time difference between consecutive tips
        full_df['time_diff'] = full_df['time'].diff().dt.total_seconds() / 3600
        
        # New event if time diff > inter_event_time
        full_df['new_event'] = (full_df['time_diff'] > inter_event_time_hours).cumsum()
        
        events = []
        for event_id, group in full_df.groupby('new_event'):
            total_rain = group['value'].sum()
            if total_rain >= min_total_mm:
                events.append({
                    "event_id": int(event_id), # Cast to int for JSON serialization
                    "start_time": group['time'].iloc[0],
                    "end_time": group['time'].iloc[-1],
                    "total_mm": round(total_rain, 2),
                    "duration_hours": round((group['time'].iloc[-1] - group['time'].iloc[0]).total_seconds() / 3600, 2)
                })
                
        return events

    def detect_dry_days(self, monitor_id: int, threshold_mm: float = 0.1) -> List[Dict[str, Any]]:
        """
        Identifies days with total rainfall less than threshold.
        """
        # Similar logic to above, but group by day
        ts_records = self.ts_service.list_by_monitor(monitor_id)
        rain_records = [ts for ts in ts_records if ts.variable.lower() in ["rain", "rainfall", "precip"]]
        
        if not rain_records:
            return []

        all_data = []
        for record in rain_records:
            try:
                df = pd.read_parquet(record.filename)
                if not df.empty:
                    all_data.append(df)
            except:
                continue
        
        if not all_data:
            return []
            
        full_df = pd.concat(all_data).sort_values('time')
        
        # Resample to daily sum
        daily_rain = full_df.set_index('time').resample('D')['value'].sum()
        
        dry_days = []
        for date, total in daily_rain.items():
            if total < threshold_mm:
                dry_days.append({
                    "date": date.date(),
                    "total_mm": round(total, 3)
                })
                
        return dry_days

class FDVService:
    def __init__(self, session: Session):
        self.session = session
        self.ts_service = TimeSeriesService(session)

    def get_scatter_data(self, monitor_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Returns Depth vs Velocity pairs for scatter plots.
        """
        ts_records = self.ts_service.list_by_monitor(monitor_id)
        
        # Load Depth and Velocity
        depth_df = pd.DataFrame()
        velocity_df = pd.DataFrame()
        
        for record in ts_records:
            try:
                if record.variable.lower() == "depth":
                    df = pd.read_parquet(record.filename)
                    if not df.empty:
                        depth_df = pd.concat([depth_df, df])
                elif record.variable.lower() == "velocity":
                    df = pd.read_parquet(record.filename)
                    if not df.empty:
                        velocity_df = pd.concat([velocity_df, df])
            except:
                continue
                
        if depth_df.empty or velocity_df.empty:
            return []
            
        # Rename columns for merge
        depth_df = depth_df.rename(columns={'value': 'depth'})
        velocity_df = velocity_df.rename(columns={'value': 'velocity'})
        
        # Merge on time (inner join to ensure matched pairs)
        merged = pd.merge(depth_df, velocity_df, on='time', how='inner')
        
        # Filter by date
        if start_date:
            merged = merged[merged['time'] >= start_date]
        if end_date:
            merged = merged[merged['time'] <= end_date]
            
        # Return as list of dicts
        # Limit points for performance if needed?
        # For now return all
        return merged[['time', 'depth', 'velocity']].to_dict('records')

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
