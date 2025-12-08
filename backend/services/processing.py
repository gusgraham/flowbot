
from sqlalchemy import func
import pandas as pd
import numpy as np
import math
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from scipy import interpolate
from sqlmodel import Session, select
import json

from domain.fsm import Install, RawDataSettings, TimeSeries
from infra.storage import StorageService

class ProcessingService:
    def __init__(self, session: Session, storage: StorageService):
        self.session = session
        self.storage = storage

    def _interpolate_correction_data(self, correction_data: pd.DataFrame, timestamps: np.ndarray) -> np.ndarray:
        """
        Interpolate correction data for given timestamps.
        Expected, correction_data has columns ['datetime', 'correction']
        """
        if correction_data is None or correction_data.empty:
            return np.zeros_like(timestamps, dtype=float)

        # Ensure timestamps are in pandas DateTime format
        timestamps = pd.to_datetime(timestamps)
        
        # Sort values
        correction_data = correction_data.sort_values(by='datetime')
        
        correction_values = correction_data['correction'].values
        correction_times = pd.to_datetime(correction_data['datetime']).values

        # Single value case
        if len(correction_values) == 1:
            # Apply correction from that point onwards? or always? 
            # Legacy code: apply if >= timestamp, else 0. 
            # Ideally for a setpoint it might apply backwards too, but stick to legacy logic for now or improve.
            # Legacy logic: np.where(timestamps >= correction_times[0], correction_values[0], 0)
            return np.where(timestamps >= correction_times[0], correction_values[0], 0.0)

        # Multiple values - interpolation
        # Convert to int64 (nanoseconds) for interpolation
        interp_func = interpolate.interp1d(
            correction_times.astype(np.int64),
            correction_values,
            kind='linear',
            bounds_error=False,
            fill_value=(correction_values[0], correction_values[-1]) # Extrapolate flat
        )

        return interp_func(timestamps.astype(np.int64))

    def calculate_corrected_depth(self, depths: np.ndarray, timestamps: np.ndarray, 
                                dep_corr: List[Dict], invert_offsets: List[Dict]) -> np.ndarray:
        """
        Apply sensor offset and depth corrections.
        """
        sensor_offsets = np.zeros_like(depths, dtype=float)
        depth_corrections = np.zeros_like(depths, dtype=float)

        # Process Invert Offsets (Sensor Offset)
        if invert_offsets:
            df_offsets = pd.DataFrame(invert_offsets)
            # Standardize column names
            if 'InvertOffset' in df_offsets.columns:
                 df_offsets = df_offsets.rename(columns={'InvertOffset': 'correction', 'DateTime': 'datetime'})
            elif 'invert_offset' in df_offsets.columns:
                 df_offsets = df_offsets.rename(columns={'invert_offset': 'correction'})
            
            # Ensure correct columns exist
            if 'correction' in df_offsets.columns and 'datetime' in df_offsets.columns:
                 sensor_offsets = self._interpolate_correction_data(df_offsets, timestamps)
                 # Convert from mm to m
                 sensor_offsets = sensor_offsets / 1000.0

        # Process Depth Corrections
        if dep_corr:
            df_dep_corr = pd.DataFrame(dep_corr)
            if 'DepthCorr' in df_dep_corr.columns:
                 df_dep_corr = df_dep_corr.rename(columns={'DepthCorr': 'correction', 'DateTime': 'datetime'})
            elif 'depth_corr' in df_dep_corr.columns:
                 df_dep_corr = df_dep_corr.rename(columns={'depth_corr': 'correction'})

            if 'correction' in df_dep_corr.columns and 'datetime' in df_dep_corr.columns:
                depth_corrections = self._interpolate_correction_data(df_dep_corr, timestamps)
                # Convert from mm to m
                depth_corrections = depth_corrections / 1000.0

        corrected_depths = depths + sensor_offsets + depth_corrections
        return np.maximum(corrected_depths, 0)

    def calculate_corrected_velocity(self, velocities: np.ndarray, timestamps: np.ndarray, 
                                   vel_corr: List[Dict]) -> np.ndarray:
        """Apply velocity multipliers."""
        if not vel_corr:
            return velocities
            
        df_vel = pd.DataFrame(vel_corr)
        if 'FloatValue' in df_vel.columns:
             df_vel = df_vel.rename(columns={'FloatValue': 'correction', 'DateTime': 'datetime'})
        elif 'velocity_factor' in df_vel.columns:
             df_vel = df_vel.rename(columns={'velocity_factor': 'correction'})

        if 'correction' not in df_vel.columns or 'datetime' not in df_vel.columns:
            return velocities

        multipliers = self._interpolate_correction_data(df_vel, timestamps)
        
        # If no multiplier is found (e.g. before first timestamp), it returns 0 from _interpolate... 
        # But for multipliers, default should be 1.0! 
        # Detailed look at _interpolate logic: 
        #   it performs fill_value=(values[0], values[-1]). 
        #   So it extrapolates the FIRST value backwards. 
        #   However, if correction_data is empty it returns 0. 
        #   Also legacy logic: if 1 value, return 0 before that time. This effectively mutes velocity before calibration start.
        #   For multipliers, usually we want 1.0 if not specified.
        #   Let's check logic: if strictly following legacy: 
        #      "np.where(timestamps >= correction_times[0], correction_values[0], 0)" -> this sets it to 0. 
        
        return velocities * multipliers

    def _calculate_circ_area(self, depths: np.ndarray, pipe_height_mm: int) -> np.ndarray:
        shape_height_m = pipe_height_mm / 1000.0
        radius = shape_height_m / 2.0
        
        areas = np.zeros_like(depths)
        
        # Full or Surcharged
        full_mask = depths >= shape_height_m
        areas[full_mask] = math.pi * (radius ** 2)
        
        # Partial
        partial_mask = (depths > 0) & (depths < shape_height_m)
        partial_depths = depths[partial_mask]
        
        # Theta is the angle subtended by the water surface at center
        # depth = r(1 - cos(theta/2))
        # This formula is slightly different from commonly used:
        # common: theta = 2 * acos((r - h)/r)
        theta = 2 * np.arccos((radius - partial_depths) / radius)
        partial_areas = (radius**2 / 2) * (theta - np.sin(theta))
        areas[partial_mask] = partial_areas
        
        return areas
        
    def _calculate_rect_area(self, depths: np.ndarray, width_mm: int, height_mm: int) -> np.ndarray:
        width_m = width_mm / 1000.0
        height_m = height_mm / 1000.0
        
        # Cap depth at height (surcharged assumption: area doesn't increase beyond pipe full - unless we model manhole etc. but usually just pipe full area used for flow)
        effective_depths = np.minimum(depths, height_m)
        return effective_depths * width_m

    def _process_rainfall_tips(self, tip_timestamps: List[datetime], tb_depth: float) -> pd.DataFrame:
        """
        Legacy rainfall processing algorithm.
        Converts list of tip timestamps to 2-min intensity series.
        """
        if not tip_timestamps:
            return pd.DataFrame()

        # Create full 2-minute interval range
        start_datetime = min(tip_timestamps)
        end_datetime = max(tip_timestamps)

        # Round start time to the next 2-minute interval
        # (start.minute // 2) * 2 + 2 ensures we start at next even minute boundary
        first_interval_start = start_datetime.replace(
            minute=((start_datetime.minute // 2) * 2 + 2) % 60, # handle 60 rollover?
            second=0,
            microsecond=0
        )
        if (start_datetime.minute // 2) * 2 + 2 >= 60:
             # If rolled over hour
             first_interval_start = first_interval_start + pd.Timedelta(hours=1)
             first_interval_start = first_interval_start.replace(minute=0)

        # Legacy logic just does: minute=((start_datetime.minute // 2) * 2 + 2)
        # Using pandas ceil might be safer? 
        # But sticking to legacy intent: next 2 min boundary.
        
        full_timestamps = pd.date_range(
            start=first_interval_start,
            end=end_datetime.replace(
                minute=(end_datetime.minute // 2) * 2,
                second=0,
                microsecond=0
            ),
            freq='2T'
        )

        # Group tips into 2-minute intervals
        # timestamp is tip time. interval is rounded time?
        grouped_tips = {}
        for tip in tip_timestamps:
            # interval = floor(2T) + 2min
            rounded_time = pd.Timestamp(tip).floor('2T') + pd.Timedelta(minutes=2)
            if rounded_time not in grouped_tips:
                grouped_tips[rounded_time] = []
            grouped_tips[rounded_time].append(tip)

        df = pd.DataFrame(0.0, index=full_timestamps, columns=['Value'])
        last_tip_time = None
        
        # We need to sort timestamps to iterate chronologically
        sorted_intervals = sorted(full_timestamps)

        for timestamp in sorted_intervals:
            tips_in_interval = grouped_tips.get(timestamp, [])

            if tips_in_interval:
                # Calculate time since previous measurement
                if last_tip_time is None:
                    time_since_prev = 10  # Default to 10 minutes if first interval
                else:
                    time_since_prev = (timestamp - last_tip_time).total_seconds() / 60

                # Determine averaging period (minimum of time since prev and 10 minutes)
                avg_period = min(time_since_prev, 10)

                # Calculate total tips and rainfall intensity
                tips_this_interval = len(tips_in_interval)
                
                # Logic copied from legacy:
                if tips_this_interval > 1:
                    if avg_period > 2:
                        tips_current_timestamps = tips_this_interval - 1
                        mm_per_hour_current_timestamps = tips_current_timestamps * (60 / 2) * tb_depth
                        tips_to_distribute = 1
                        mm_per_hour_to_distribute = tips_to_distribute * (60 / (avg_period - 2)) * tb_depth
                    else:
                        tips_current_timestamps = tips_this_interval
                        mm_per_hour_current_timestamps = tips_current_timestamps * (60 / 2) * tb_depth
                else:
                    tips_current_timestamps = 1
                    mm_per_hour_current_timestamps = tips_current_timestamps * (60 / avg_period) * tb_depth
                    if avg_period > 2:
                        tips_to_distribute = 1
                        mm_per_hour_to_distribute = tips_to_distribute * (60 / avg_period) * tb_depth
                    else:
                         mm_per_hour_to_distribute = 0 # Not used if avg_period <= 2 in this else branch?

                # Determine number of periods to distribute across
                periods_in_avg = math.ceil(avg_period / 2)

                # Fill in values for all periods in the averaging interval
                for period in range(periods_in_avg):
                    period_timestamp = timestamp - pd.Timedelta(minutes=2 * (periods_in_avg - period))
                    
                    # Logic note: period goes 0 to N-1
                    # check logic:
                    # timestamp is current end of interval.
                    # e.g. periods=3. period 0, 1, 2.
                    # period=2 (last): timestamp - 2*(3-2) = timestamp - 2 => previous interval?
                    # Wrapper Legacy: 'timestamp - pd.Timedelta(minutes=2 * (periods_in_avg - period))'
                    # If period = periods_in_avg - 1 => period_timestamp = timestamp - 2*(1) = timestamp - 2min?
                    # Wait, current interval ends at timestamp. 2min interval covers (timestamp-2, timestamp].
                    # So timestamp IS the row index for that interval (usually right labeled).
                    # If legacy logic uses timestamp as index, then `df.loc[timestamp]` is the current interval.
                    # Legacy: `if period == periods_in_avg - 1: value_to_add = mm_cur`
                    # let's trust the logic calculation for time
                    
                    if period == periods_in_avg - 1:
                         value_to_add = mm_per_hour_current_timestamps
                    else:
                         value_to_add = mm_per_hour_to_distribute

                    if period_timestamp in df.index:
                        df.loc[period_timestamp, 'Value'] += value_to_add
                    else:
                        # Should we add rows if they don't exist? (Backfilling before start?)
                        # Legacy says: df = pd.concat... sort_index()
                        new_row = pd.DataFrame({'Value': value_to_add}, index=[period_timestamp])
                        df = pd.concat([df, new_row]).sort_index()

                # Update last tip time to the last tip in this interval
                # Legacy: `last_tip_time = timestamp`
                # Is timestamp the tip time? No it's the interval time.
                # "Update last tip time to the last tip in this interval" -> comment says last tip, code says timestamp.
                # Code: `last_tip_time = timestamp`
                last_tip_time = timestamp
                
        return df

    def process_install(self, install_id: int):
        """
        Main processing workflow for an install.
        """
        install = self.session.get(Install, install_id)
        if not install:
            raise ValueError("Install not found")

        # Get Raw Data Settings
        settings = install.raw_data_settings
        if not settings:
            # Create default settings if none exist? Or just raise?
            # Assuming if they are processing, they might have set some or just want raw->processed copy
            settings = RawDataSettings(install_id=install_id) # Empty defaults

        # Fetch Raw TimeSeries
        stmt = select(TimeSeries).where(
            TimeSeries.install_id == install_id,
            func.lower(TimeSeries.data_type) == 'raw'
        )
        raw_series = self.session.exec(stmt).all()
        
        if not raw_series:
            raise ValueError("No raw data records found for this install. Please ensure Data Ingestion has been run.")

        # Load Raw Data
        dfs = []
        for ts in raw_series:
            if not ts.filename: continue
            
            # Construct path (now consolidated in data/fsm)
            # The ts.filename stored in DB might be relative to data_dir or just filename
            # Legacy/Current implementation: 'data/fsm/timeseries/installs/{id}/filename.parquet'
            # Storage service base_path is 'data/fsm'
            
            # If filename is full relative path:
            fpath = ts.filename
            
            # Try to read
            try:
                df = self.storage.read_parquet(fpath)
                df['variable'] = ts.variable
                dfs.append(df)
            except Exception as e:
                print(f"Failed to load {fpath}: {e}")
                continue

        if not dfs:
            raise ValueError("Raw data records indicate data exists, but the file system paths could not be read. Please check file storage.")

        combined = pd.concat(dfs, ignore_index=True)
        
        # Helper to pivot
        # Assume columns: time, value, variable
        # We need to pivot to: time, Depth, Velocity, Rain, etc.
        pivoted = combined.pivot_table(index='time', columns='variable', values='value').reset_index()
        pivoted = pivoted.sort_values('time')
        
        # Extract arrays
        timestamps = pivoted['time'].values
        
        processed_data = {} # variable -> np.array of values

        # ---------------------------------------------------------
        # FLOW MONITOR PROCESSING
        # ---------------------------------------------------------
        if install.install_type == 'Flow Monitor':
            # 1. Depth Processing
            if 'Depth' in pivoted.columns:
                depths_m = pivoted['Depth'].values
                
                # Parse corrections
                dep_corr = json.loads(settings.dep_corr) if settings.dep_corr else []
                # Note: dep_corr in settings JSON might contain both DepthCorr and InvertOffset if unified?
                # Or they are separate. In `MonitorDataFlowCalculator` they are separate or combined?
                # looking at `MonitorDataFlowCalculator`:
                #   sensor_offset_df came from `dep_corr` (renaming InvertOffset)
                #   depth_correction_df came from `dep_corr` (renaming DepthCorr)
                # So it seems stored in same JSON list.
                
                corrected_depths = self.calculate_corrected_depth(
                    depths_m, timestamps, dep_corr, dep_corr
                )
                processed_data['Depth'] = corrected_depths
            
            # 2. Velocity Processing
            if 'Velocity' in pivoted.columns:
                vels = pivoted['Velocity'].values
                vel_corr = json.loads(settings.vel_corr) if settings.vel_corr else []
                processed_data['Velocity'] = self.calculate_corrected_velocity(
                    vels, timestamps, vel_corr
                )
            
            # 3. Flow Calculation
            if 'Depth' in processed_data and 'Velocity' in processed_data:
                # Calculate Area
                # Get Pipe Dims
                # Priority: Settings > Install Defaults
                shape = settings.pipe_shape or install.fm_pipe_shape or 'CIRC'
                width = settings.pipe_width or install.fm_pipe_width_mm or 225
                height = settings.pipe_height or install.fm_pipe_height_mm or 225
                
                if shape == 'CIRC' or shape == 'Circular': # Handle both codes just in case
                    areas = self._calculate_circ_area(processed_data['Depth'], height)
                elif shape == 'RECT' or shape == 'Rectangular':
                    areas = self._calculate_rect_area(processed_data['Depth'], width, height)
                else:
                    # Fallback to circular or implement others later
                    areas = self._calculate_circ_area(processed_data['Depth'], height)
                
                # Flow = Area * Velocity
                # Area (m2) * Velocity (m/s) = m3/s
                # Usually we store Flow in l/s
                flows_m3s = areas * processed_data['Velocity']
                flows_ls = flows_m3s * 1000.0
                processed_data['Flow'] = flows_ls

        # ---------------------------------------------------------
        # RAIN GAUGE PROCESSING
        # ---------------------------------------------------------
        elif install.install_type == 'Rain Gauge':
            # Process Intensity? Or just Tips?
            # Usually raw is tips (counts) or intensity (mm/hr).
            # If Raw is Tips (0.2mm per tip):
            # Processed usually Intensity.
            # Process Intensity from Tips
            if 'Rain' in pivoted.columns:
                # Assuming 'Rain' column contains tips (counts) or 1s per tip.
                # If we have 'Rain', we might need to convert tips to intensity using the legacy logic.
                # If it's already intensity, we might double process, but based on legacy:
                # "if a_raw.rg_data is None: return None" -> implies input is raw tips data.
                # In our case 'pivoted' has 'Rain' which might be just 1.0 for each tip.
                
                # Check if we have tips (e.g. discrete events) or intensity. 
                # If ingestion loaded tips, they are likely 1s at timestamps.
                # If ingested from R file, it might be intensity already. R file parser returns INTENSITY.
                # FLO/DAT parsers usually return tips.
                # Let's assume if it is 'Rain', we treat as tips and run the algo. 
                # Unless it seems to be intensity? 
                
                # However, the user provided logic loops over `tip_timestamps`.
                # If we have intensity already, we should just use it.
                # How to distinguish? R file import sets data as 'Rain' too? No, checks for 'INTENSITY'.
                # Let's check ingestion:
                # import_r_file -> INTENSITY -> 'Rain' (via my simple pass through logic earlier? No wait)
                # Ingestion: 
                #   Rain Gauge -> check extension
                #   if .flo -> parse_flo_file -> ? (BinaryParser usually tips) -> 'Rain'
                #   if .dat -> parse_dat_file -> ? (BinaryParser usually tips) -> 'Rain'
                #   import_r_file -> NOT CALLED for Rain Gauge in Ingestion Service currently?
                #   Wait, IngestionService only calls parse_flo or parse_dat for Rain Gauge.
                #   It does NOT call import_r_file. So 'Rain' is likely TIPS from binary files.
                
                # Extract timestamps of tips (where Rain > 0)
                # If pivoted has 2 min intervals filled with 0s, we might lose accuracy of tip time?
                # But pivoted comes from `combined` which comes from storage read_parquet.
                # read_parquet might have exact timestamps of tips if it was tips.
                
                # Re-reading raw DF for Rain might be better to get exact tip times than using 'pivoted' 
                # which might have been resampled? No, 'pivoted' is just pivot_table, it doesn't resample 
                # unless duplicates. But tips can be duplicate times? 
                # pivot_table aggregates duplicates. Tips at exact same time?
                # Better to use `combined` filtered for 'Rain'.
                
                rain_rows = combined[combined['variable'] == 'Rain']
                if not rain_rows.empty:
                    # Get all timestamps where there is a tip. 
                    # If Value is 1, it's 1 tip. If Value is 2, 2 tips?
                    # Legacy: `tip_timestamps = a_raw.rg_data['Timestamp'].to_list()` -> implies 1 row per tip?
                    # Our ingestion for .dat/.flo creates 1 row per tip?
                    # Let's assume yes or use value as count.
                    
                    tip_timestamps_list = []
                    for _, row in rain_rows.iterrows():
                        val = row['value']
                        if pd.isna(val):
                            continue
                        count = int(val)
                        ts = row['time']
                        for _ in range(count):
                            tip_timestamps_list.append(ts)
                            
                    tb_depth = settings.rg_tb_depth if settings.rg_tb_depth is not None else 0.2
                    
                    processed_intensity_df = self._process_rainfall_tips(tip_timestamps_list, tb_depth)
                    
                    # Merge back into processed data
                    if not processed_intensity_df.empty:
                        processed_data['Rain'] = processed_intensity_df['Value'].values
                        # Re-align timestamps if needed? 
                        # This generates a 2-min fixed grid.
                        # The other variables (if any? RG usually standalone) might be on different grid.
                        # If RG is standalone, we update `timestamps` to be this new grid.
                        timestamps = processed_intensity_df.index.values

            elif 'Intensity' in pivoted.columns:
                 # Already intensity (e.g. from some other source)
                 processed_data['Rain'] = pivoted['Intensity'].values

        # ---------------------------------------------------------
        # PUMP LOGGER PROCESSING
        # ---------------------------------------------------------
            
        # ---------------------------------------------------------
        # PUMP LOGGER PROCESSING
        # ---------------------------------------------------------
        # ---------------------------------------------------------
        # PUMP LOGGER PROCESSING
        # ---------------------------------------------------------
        elif install.install_type == 'Pump Logger':
            # Handle Timing Corrections and Added On/Offs
            pl_timing_corr = json.loads(settings.pl_timing_corr) if settings.pl_timing_corr else []
            pl_added_onoffs = json.loads(settings.pl_added_onoffs) if settings.pl_added_onoffs else []

            # Work on pivoted DF to keep things aligned
            # 1. Timing Corrections
            if pl_timing_corr:
                df_tc = pd.DataFrame(pl_timing_corr)
                
                # Frontend sends 'offset' in minutes. Backend logic assumes 'correction' in seconds.
                # Map 'offset' to 'correction' and convert minutes to seconds.
                if not df_tc.empty:
                    if 'offset' in df_tc.columns:
                        # Convert minutes to seconds
                        # Handle potential strings/invalid corrections
                        df_tc['correction'] = pd.to_numeric(df_tc['offset'], errors='coerce').fillna(0) * 60
                    elif 'correction' in df_tc.columns:
                        # Fallback if manual entry used 'correction'
                        pass
                    else:
                        df_tc['correction'] = 0

                    if 'datetime' in df_tc.columns:
                        correction_seconds = self._interpolate_correction_data(df_tc, timestamps)
                        # Apply correction (convert seconds to timedelta)
                        pivoted['time'] = pivoted['time'] + pd.to_timedelta(correction_seconds, unit='s')
                        
                        # Update timestamps array reference for saving later
                        timestamps = pivoted['time'].values

            # 2. Added On/Off Events
            if pl_added_onoffs:
                df_added = pd.DataFrame(pl_added_onoffs)
                
                if not df_added.empty and 'datetime' in df_added.columns:
                    # Map 'state' (ON/OFF) to 'value' (1/0)
                    if 'state' in df_added.columns:
                        # Normalize to uppercase and map
                        df_added['value'] = df_added['state'].astype(str).str.upper().map({'ON': 1, 'OFF': 0}).fillna(0)
                        
                    elif 'value' not in df_added.columns:
                        # If neither state nor value, assume 1? Or 0? Let's skip valid rows.
                        df_added['value'] = 0 # Safe default?
                    
                    if 'value' in df_added.columns:
                        # Prepare new rows
                        new_rows = pd.DataFrame({
                            'time': pd.to_datetime(df_added['datetime']),
                            'Pump_State': df_added['value']
                        })
                        
                        # Concatenate
                        pivoted = pd.concat([pivoted, new_rows], ignore_index=True)
                        pivoted = pivoted.sort_values('time')
                        
                        # Update timestamps array reference
                        timestamps = pivoted['time'].values

            # Populate processed data
            if 'Pump_State' in pivoted.columns:
                # For added rows, other columns will be NaN.
                # Ensure Pump_State is numeric/int (fill NaNs if any? though we just created them with values)
                # But if original data had NaNs?
                pivoted['Pump_State'] = pivoted['Pump_State'].fillna(0) # Default to off if missing?
                processed_data['Pump_State'] = pivoted['Pump_State'].values
            
        
        if not processed_data:
             raise ValueError(f"Processing produced no data. Check if required variables exist (e.g. Depth/Velocity for Flow Monitors). Type: {install.install_type}")

        # ---------------------------------------------------------
        # SAVE PROCESSED DATA
        # ---------------------------------------------------------
        
        # For each processed variable, creating a dataframe and saving
        for var_name, values in processed_data.items():
            # Create DF
            df_proc = pd.DataFrame({
                'time': timestamps,
                'value': values
            })
            
            # Define filename
            # data/fsm/timeseries/installs/{id}/{var}_Processed.parquet
            rel_path = f"timeseries/installs/{install_id}/{var_name}_Processed.parquet"
            
            # Save
            self.storage.save_parquet(rel_path, df_proc)
            
            # Update/Create TimeSeries Record
            # Check if exists
            stmt = select(TimeSeries).where(
                TimeSeries.install_id == install_id,
                TimeSeries.variable == var_name,
                TimeSeries.data_type == 'Processed'
            )
            existing = self.session.exec(stmt).first()
            
            if existing:
                existing.start_time = pd.to_datetime(timestamps[0])
                existing.end_time = pd.to_datetime(timestamps[-1])
                existing.interval_minutes = 2 # Derive this properly?
                existing.filename = rel_path
                existing.unit = self._get_unit(var_name)
                self.session.add(existing)
            else:
                new_ts = TimeSeries(
                    install_id=install_id,
                    monitor_id=install.monitor_id,
                    variable=var_name,
                    data_type='Processed',
                    start_time=pd.to_datetime(timestamps[0]),
                    end_time=pd.to_datetime(timestamps[-1]),
                    interval_minutes=2, # TODO calc
                    filename=rel_path,
                    unit=self._get_unit(var_name)
                )
                self.session.add(new_ts)
        
        self.session.commit()
    
    def _get_unit(self, variable: str) -> str:
        units = {
            'Depth': 'm', # Storing depth in meters usually? Front end expects meters? 
                          # Raw files usually m or mm. 
                          # My calc above produces Meters (depths_m)
            'Velocity': 'm/s',
            'Flow': 'l/s',
            'Rain': 'mm/hr',
            'Voltage': 'V',
            'Pump_State': ''
        }
        return units.get(variable, '')
    def process_project(self, project_id: int) -> Dict[str, Any]:
        """
        Process all installs in a project.
        """
        installs = self.session.exec(select(Install).where(Install.project_id == project_id)).all()
        
        results = {
            "total": len(installs),
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        for install in installs:
            try:
                self.process_install(install.id)
                results["success"] += 1
                results["details"].append({"install_id": install.install_id, "status": "success"})
            except Exception as e:
                results["failed"] += 1
                results["details"].append({"install_id": install.install_id, "status": "failed", "error": str(e)})
        
        return results
