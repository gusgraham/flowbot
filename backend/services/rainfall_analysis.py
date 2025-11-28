import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from sqlmodel import Session, select
from domain.analysis import AnalysisTimeSeries, AnalysisDataset

class RainfallAnalysisService:
    def __init__(self, session: Session):
        self.session = session

    def analyze_events(self, dataset_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze rainfall events for a given dataset based on provided parameters.
        
        Params:
            rainfallDepthTolerance (float): mm
            precedingDryDays (int): days
            consecZero (int): timesteps
            requiredDepth (float): mm
            requiredIntensity (float): mm/hr
            requiredIntensityDuration (int): mins
            partialPercent (int): %
            useConsecutiveIntensities (bool): True/False
        """
        # 1. Fetch data
        timeseries = self._get_timeseries_data(dataset_id)
        if not timeseries:
            return {"events": [], "stats": {}, "error": "No data found"}
            
        # 2. Prepare DataFrame
        df = pd.DataFrame(timeseries)
        df['rain_datetime'] = pd.to_datetime(df['timestamp'])
        df['rain_date'] = df['rain_datetime'].dt.date
        # Assuming stored value is intensity (mm/hr). Calculate depth (mm).
        # We need the timestep to calculate depth from intensity.
        # Estimate timestep from data
        if len(df) > 1:
            time_diffs = df['rain_datetime'].diff().dropna()
            # Get most common time difference in minutes
            timestep_mins = time_diffs.dt.total_seconds().mode()[0] / 60
        else:
            timestep_mins = 2 # Default to 2 mins if single point
            
        # If value is intensity (mm/hr), depth = value * (timestep_mins / 60)
        # Note: Legacy code assumes input is intensity.
        df['rainfall'] = df['value'] # Intensity
        df['rainfall_mm'] = df['value'] * (timestep_mins / 60) # Depth
        
        # 3. Run Analysis
        # A. Dry Days Analysis
        df_daily = df.groupby('rain_date', as_index=False)['rainfall_mm'].sum()
        dry_days = self._get_list_of_dry_days(
            df_daily, 
            params.get('rainfallDepthTolerance', 0), 
            params.get('precedingDryDays', 4)
        )
        
        # B. Event Detection (WAPUG)
        events, event_dates = self._get_potential_wapug_events_nm(
            df, 
            timestep_mins, 
            params
        )
        
        # 4. Compile Results
        return {
            "events": events.to_dict('records') if not events.empty else [],
            "dry_days": [d.isoformat() for d in dry_days],
            "stats": {
                "total_events": len(events),
                "total_rainfall_depth": df['rainfall_mm'].sum(),
                "analyzed_period_start": df['rain_datetime'].min().isoformat(),
                "analyzed_period_end": df['rain_datetime'].max().isoformat(),
            }
        }

    def _get_timeseries_data(self, dataset_id: int) -> List[Dict]:
        stmt = select(AnalysisTimeSeries).where(
            AnalysisTimeSeries.dataset_id == dataset_id
        ).order_by(AnalysisTimeSeries.timestamp)
        results = self.session.exec(stmt).all()
        return [{"timestamp": r.timestamp, "value": r.value} for r in results]

    def _get_list_of_dry_days(self, df_daily: pd.DataFrame, tolerance: float, preceding_days: int) -> List[Any]:
        lst_dry_days = []
        dry_day_count = 0
        
        # df_daily columns: rain_date, rainfall_mm
        # Assuming rain_date is sorted
        
        for i in range(len(df_daily)):
            daily_rain = df_daily.iloc[i]['rainfall_mm']
            date = df_daily.iloc[i]['rain_date']
            
            if daily_rain <= tolerance:
                dry_day_count += 1
                if dry_day_count > preceding_days:
                    lst_dry_days.append(date)
            else:
                dry_day_count = 0
                
        return lst_dry_days

    def _get_potential_wapug_events_nm(self, df: pd.DataFrame, time_step: float, params: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Any]]:
        """
        Ported from flowbot_graphing.py getPotentialWAPUGEventsNM
        """
        rainfall = df['rainfall'].values # Intensity
        dates = df['rain_datetime'].values
        
        required_depth = params.get('requiredDepth', 5)
        required_intensity = params.get('requiredIntensity', 6)
        required_intensity_duration = params.get('requiredIntensityDuration', 4)
        consec_zero = params.get('consecZero', 5)
        partial_percent = params.get('partialPercent', 20)
        use_consecutive_intensities = params.get('useConsecutiveIntensities', True)
        
        rain_block_df = pd.DataFrame(
            columns=["Start", "End", "Depth", "Intensity_Count", "Passed"]
        )
        hist_dates = []
        
        # State
        state = {
            "running_depth": 0.0,
            "consecutive_zeros": 0,
            "intensity_count": 0,
            "partial_intensity_count": 0,
            "cumulative_sum": [],
            "potential_event_start_index": 0,
        }
        
        def _reset_state():
            state["running_depth"] = 0.0
            state["consecutive_zeros"] = 0
            state["intensity_count"] = 0
            state["partial_intensity_count"] = 0
            state["cumulative_sum"] = []

        def _check_event_criteria(running_depth, intensity_count) -> float:
            # Full event
            if (running_depth > required_depth and intensity_count >= required_intensity_duration):
                return 1.0
            
            # Partial criteria
            partial_depth_cond = (
                running_depth >= (((100 - partial_percent) / 100) * required_depth)
                and running_depth < required_depth
            )
            partial_int_cond = (
                intensity_count >= (((100 - partial_percent) / 100) * required_intensity_duration)
                and intensity_count < required_intensity_duration
            )
            
            if (
                (partial_depth_cond and partial_int_cond) or
                (partial_depth_cond and intensity_count >= required_intensity_duration) or
                (partial_int_cond and running_depth > required_depth) or
                (state["partial_intensity_count"] >= required_intensity_duration 
                 and use_consecutive_intensities 
                 and running_depth > required_depth)
            ):
                return 0.5
                
            return 0.0

        for i, rainfall_val in enumerate(rainfall):
            if rainfall_val == 0:
                state["consecutive_zeros"] += 1
            else:
                state["consecutive_zeros"] = 0
                # Calculate depth added in this timestep: intensity * hours
                # Legacy code: state["running_depth"] += rainfall_val / (60 / time_step)
                # which is rainfall_val * (time_step / 60)
                state["running_depth"] += rainfall_val * (time_step / 60)
                state["cumulative_sum"].append(float(state["running_depth"]))
                
                # Intensity tracking
                if use_consecutive_intensities:
                    if rainfall_val > required_intensity:
                        # Check next N steps
                        steps_needed = int(required_intensity_duration / time_step)
                        # Ensure we don't go out of bounds
                        end_idx = min(i + steps_needed, len(rainfall))
                        items = rainfall[i : end_idx]
                        
                        state["partial_intensity_count"] += time_step
                        
                        # Only count as full intensity duration if we have enough data points
                        # and all exceed threshold
                        if len(items) >= steps_needed and all(item > required_intensity for item in items):
                            state["intensity_count"] = required_intensity_duration
                else:
                    if rainfall_val > required_intensity:
                        state["intensity_count"] += time_step

            # Check for event end
            if state["consecutive_zeros"] >= consec_zero:
                if state["cumulative_sum"]:
                    last_depth = state["cumulative_sum"][-1]
                    event_status = _check_event_criteria(state["running_depth"], state["intensity_count"])
                    
                    if event_status > 0:
                        event_start_idx = state["potential_event_start_index"]
                        event_end_idx = i
                        event_start = dates[event_start_idx]
                        event_end = dates[event_end_idx]
                        
                        # Add to events
                        new_event = pd.DataFrame([{
                            "Start": event_start,
                            "End": event_end,
                            "Depth": last_depth,
                            "Intensity_Count": state["intensity_count"],
                            "Passed": event_status
                        }])
                        
                        # Clean empty columns before concat to avoid warnings
                        rain_block_df = pd.concat([rain_block_df, new_event], ignore_index=True)
                        
                        # Add dates for histogram/gantt
                        # Legacy code generates 2min freq dates between start and end
                        # We can just store start/end for now, frontend can visualize
                        
                # Reset
                state["potential_event_start_index"] = i
                _reset_state()
                
        return rain_block_df, hist_dates
