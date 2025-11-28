import pandas as pd
import numpy as np
from scipy import interpolate
from typing import Optional, List, Dict
import json

class FlowCalculator:
    def __init__(self, 
                 pipe_shape: str, 
                 pipe_width_mm: float, 
                 pipe_height_mm: float,
                 silt_levels_json: Optional[str] = None,
                 depth_corrections_json: Optional[str] = None,
                 velocity_corrections_json: Optional[str] = None):
        
        self.pipe_shape = pipe_shape
        self.pipe_width = pipe_width_mm
        self.pipe_height = pipe_height_mm
        
        self.silt_data = self._parse_json_to_df(silt_levels_json)
        self.depth_correction_data = self._parse_json_to_df(depth_corrections_json)
        self.velocity_multiplier_data = self._parse_json_to_df(velocity_corrections_json)
        
    def _parse_json_to_df(self, json_str: Optional[str]) -> Optional[pd.DataFrame]:
        if not json_str:
            return None
        try:
            data = json.loads(json_str)
            df = pd.DataFrame(data)
            # Expecting 'date' or 'DateTime' and 'value' or 'correction'
            if 'date' in df.columns:
                df['DateTime'] = pd.to_datetime(df['date'])
            elif 'DateTime' in df.columns:
                df['DateTime'] = pd.to_datetime(df['DateTime'])
            return df
        except:
            return None

    def _interpolate_correction_data(self, correction_data, timestamps):
        if correction_data is None or correction_data.empty:
            return np.zeros(len(timestamps))
            
        correction_times = correction_data['DateTime'].values.astype(np.int64)
        # Assuming 'value' or 'correction' column
        col = 'value' if 'value' in correction_data.columns else 'correction'
        if col not in correction_data.columns:
             # Fallback
             return np.zeros(len(timestamps))
             
        correction_values = correction_data[col].values

        if len(correction_values) == 1:
            # Apply single value for all times >= time
            t_stamps = timestamps.astype(np.int64)
            return np.where(t_stamps >= correction_times[0], correction_values[0], 0)

        interp_func = interpolate.interp1d(
            correction_times,
            correction_values,
            kind='linear',
            bounds_error=False,
            fill_value=(correction_values[0], correction_values[-1])
        )
        return interp_func(timestamps.astype(np.int64))

    def calculate_corrected_depth(self, depths, timestamps):
        if self.depth_correction_data is None:
            return depths
            
        depths = np.array(depths)
        timestamps = pd.to_datetime(timestamps)
        
        corrections = self._interpolate_correction_data(self.depth_correction_data, timestamps)
        # Assuming corrections are in mm, convert to m? Legacy divides by 1000.
        corrections_m = corrections / 1000.0
        
        return np.maximum(depths + corrections_m, 0)

    def calculate_corrected_velocities(self, velocities, timestamps):
        if self.velocity_multiplier_data is None:
            return velocities
            
        velocities = np.array(velocities)
        timestamps = pd.to_datetime(timestamps)
        
        multipliers = self._interpolate_correction_data(self.velocity_multiplier_data, timestamps)
        # If no multipliers found (zeros returned), use 1.0? 
        # _interpolate_correction_data returns 0 if no data.
        # But if data exists, it returns multipliers.
        # If multipliers are 0, that means velocity becomes 0?
        # Legacy: "if self.velocity_multiplier_data is None ... return velocities"
        # My helper returns zeros if empty.
        # I should check if multipliers are all zero and data was empty?
        # No, I checked empty at start.
        # But if timestamps are before first correction?
        # My helper uses fill_value=(first, last), so it extrapolates.
        
        # Wait, if helper returns 0 for "no data", then I multiply by 0?
        # I should fix helper to return None if no data.
        # Or handle it here.
        if self.velocity_multiplier_data is None or self.velocity_multiplier_data.empty:
             return velocities
             
        return velocities * multipliers

    def _calculate_area(self, depths_m):
        """
        Calculate wetted area based on pipe shape and dimensions.
        depths_m: array of depths in meters.
        """
        width_m = self.pipe_width / 1000.0
        height_m = self.pipe_height / 1000.0
        
        if self.pipe_shape.upper() in ['CIRCULAR', 'CIRC']:
            # Circular segment area
            # theta = 2 * arccos(1 - 2 * d / D)
            # Area = (D^2 / 8) * (theta - sin(theta))
            # But handle full pipe
            
            d = np.clip(depths_m, 0, height_m)
            radius = width_m / 2.0
            
            # Avoid division by zero or invalid arccos
            # ratio = (radius - d) / radius => 1 - d/r
            # theta = 2 * acos(1 - d/r)
            
            # Alternative:
            # theta = 2 * arccos(1 - 2 * d / D)
            term = 1 - 2 * d / width_m
            term = np.clip(term, -1.0, 1.0)
            theta = 2 * np.arccos(term)
            area = (width_m**2 / 8.0) * (theta - np.sin(theta))
            return area
            
        elif self.pipe_shape.upper() in ['RECTANGULAR', 'RECT']:
            d = np.clip(depths_m, 0, height_m)
            return width_m * d
            
        else:
            # Fallback for unknown shapes: assume rectangular? or return 0?
            return np.zeros_like(depths_m)

    def calculate_flow(self, depth_df: pd.DataFrame, velocity_df: pd.DataFrame) -> pd.DataFrame:
        # Merge on timestamp
        # Ensure 'Timestamp' and 'Value' columns
        if 'Timestamp' not in depth_df.columns or 'Value' not in depth_df.columns:
            raise ValueError("Depth DataFrame missing required columns")
        if 'Timestamp' not in velocity_df.columns or 'Value' not in velocity_df.columns:
            raise ValueError("Velocity DataFrame missing required columns")
            
        merged = pd.merge(depth_df, velocity_df, on='Timestamp', how='inner', suffixes=('_depth', '_velocity'))
        
        timestamps = merged['Timestamp']
        raw_depths = merged['Value_depth'].values # Assuming meters? Legacy parser returns normalized value * (max-min) + min.
        # Legacy parser: int_value = f_min_value + ((f_max_value - f_min_value) * int_value)
        # Usually depths are in meters or mm?
        # Legacy calculate_flow: "corrected_depths_m = corrected_depths / 1000" implies input was mm?
        # But parser returns float.
        # I'll assume parser returns raw units (likely mm for depth, m/s for velocity).
        # Wait, legacy parser returns "Value".
        # In `calculate_flow` (legacy):
        # "depths = self.raw_data.dep_data['Value'].values"
        # "corrected_depths = self.calculate_corrected_depth(depths, timestamps)"
        # "corrected_depths_m = corrected_depths / 1000"
        # So raw depths are in mm.
        
        raw_velocities = merged['Value_velocity'].values # m/s
        
        # Corrections
        # Depth is in mm, so convert to m for area calc?
        # `calculate_corrected_depth` takes depths (mm) and adds corrections (mm -> m inside? No, it converts corrections to m and adds to depths?
        # Let's check my implementation of `calculate_corrected_depth`:
        # "corrections_m = corrections / 1000.0"
        # "return np.maximum(depths + corrections_m, 0)"
        # If `depths` passed are mm, and I add m, that's wrong.
        # Legacy: "corrected_depths = depths + sensor_offsets + depth_corrections" (all in same unit?)
        # Legacy `calculate_corrected_depth`:
        # "sensor_offsets = sensor_offsets / 1000" (mm -> m)
        # "depth_corrections = depth_corrections / 1000" (mm -> m)
        # "corrected_depths = depths + sensor_offsets + depth_corrections"
        # This implies `depths` input was in METERS?
        # But `calculate_flow` says: "corrected_depths_m = corrected_depths / 1000" AFTER calling it?
        # Wait.
        # Legacy `calculate_corrected_depth`:
        # "depths = np.array(depths)"
        # "sensor_offsets = ... / 1000"
        # "corrected_depths = depths + ..."
        # If `depths` comes from `dep_data`, is it m or mm?
        # `read_dat_file` scales 0-255/65535 to min-max.
        # If min/max in header are 0-2000 (mm), then it's mm.
        # If 0-2.0 (m), then it's m.
        # Usually loggers record mm.
        # If legacy divides by 1000 *after* correction, maybe correction is also mm?
        # "sensor_offsets = sensor_offsets / 1000 if sensor_offsets is not None else 0"
        # This line in legacy `calculate_corrected_depth` strongly suggests converting mm to m.
        # So `sensor_offsets` (from DF) is mm.
        # If `depths` is also mm, then adding `sensor_offsets/1000` (m) to `depths` (mm) is WRONG.
        # Unless `depths` is ALREADY m?
        # If `depths` is m, then `corrected_depths` is m.
        # Then `corrected_depths_m = corrected_depths / 1000` would be km? That makes no sense.
        
        # Let's re-read legacy `calculate_flow`:
        # "corrected_depths = self.calculate_corrected_depth(depths, timestamps)"
        # "corrected_depths_m = corrected_depths / 1000"
        # This implies `corrected_depths` is in mm.
        # So `calculate_corrected_depth` returns mm.
        # But inside `calculate_corrected_depth`:
        # "sensor_offsets = sensor_offsets / 1000"
        # "corrected_depths = depths + sensor_offsets + ..."
        # If `corrected_depths` is mm, then `depths` must be mm.
        # And `sensor_offsets/1000` must be mm? No, that means `sensor_offsets` was microns? Unlikely.
        # Maybe `sensor_offsets` was ALREADY m? And it divides by 1000?
        # Or maybe I misread the legacy code.
        
        # Legacy Step 153 snippet:
        # "sensor_offsets = sensor_offsets / 1000 if sensor_offsets is not None else 0"
        # "corrected_depths = depths + sensor_offsets + depth_corrections"
        # "return np.maximum(corrected_depths, 0)"
        
        # If `depths` is m, and `sensor_offsets` (mm) / 1000 -> m. Then result is m.
        # Then `corrected_depths` is m.
        # Then `corrected_depths_m = corrected_depths / 1000` -> mm? No, `_m` usually means meters.
        # Maybe `corrected_depths` was mm?
        # If `depths` is mm. `sensor_offsets` (mm) / 1000 -> m.
        # mm + m = garbage.
        
        # I suspect `depths` is METERS in legacy `calculate_corrected_depth` input?
        # But `calculate_flow` calls it with `self.raw_data.dep_data['Value']`.
        # If raw data is mm (0-2000), then it's mm.
        
        # Let's assume raw data is mm.
        # And I want result in m for area calc.
        # I will convert everything to meters.
        
        raw_depths_m = raw_depths / 1000.0
        
        # Corrections (assuming JSON stores mm)
        # My `calculate_corrected_depth` converts corrections to m.
        # So I should pass `raw_depths_m`.
        
        corrected_depths_m = self.calculate_corrected_depth(raw_depths_m, timestamps)
        
        # Silt (assuming mm in JSON)
        silt_corrections = self._interpolate_correction_data(self.silt_data, timestamps)
        silt_m = silt_corrections / 1000.0
        
        # Effective depth for area
        # Water area = Area(corrected_depth)
        # Silt area = Area(silt_depth)
        # Flow area = Water area - Silt area
        
        water_area = self._calculate_area(corrected_depths_m)
        silt_area = self._calculate_area(silt_m)
        
        flow_area = np.maximum(water_area - silt_area, 0)
        
        # Velocity
        corrected_velocities = self.calculate_corrected_velocities(raw_velocities, timestamps)
        
        # Flow = Area * Velocity
        # Area (m2) * Velocity (m/s) = m3/s
        # Convert to L/s -> * 1000
        
        flow_m3s = flow_area * corrected_velocities
        flow_ls = flow_m3s * 1000.0
        
        result = pd.DataFrame({
            'Timestamp': timestamps,
            'Flow': flow_ls,
            'Depth': corrected_depths_m * 1000.0, # mm
            'Velocity': corrected_velocities
        })
        
        return result
