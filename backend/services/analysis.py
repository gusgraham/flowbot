from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np
from sqlmodel import Session
from services.importers import import_fdv_file, import_r_file
from domain.fsa import FsaDataset as AnalysisDataset, FsaTimeSeries as AnalysisTimeSeries

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

    def get_cumulative_depth(self, dataset_id: int) -> Dict[str, Any]:
        """
        Calculate cumulative rainfall depth over time.
        Matches legacy graphCumulativeDepth implementation.
        """
        # Get dataset info from DB first
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return {"dataset_id": dataset_id, "data": []}
        
        dataset_name = dataset.name
        
        # Try to query timeseries from database (fast!)
        # from domain.analysis import AnalysisTimeSeries
        from sqlmodel import select
        
        try:
            # Query timeseries data from database
            stmt = select(AnalysisTimeSeries).where(
                AnalysisTimeSeries.dataset_id == dataset_id
            ).order_by(AnalysisTimeSeries.timestamp)
            
            timeseries = self.session.exec(stmt).all()
            
            if not timeseries or len(timeseries) == 0:
                # Fall back to file parsing if no data in database
                print(f"No timeseries data in database for dataset {dataset_id}, falling back to file parsing")
                return self._get_cumulative_depth_from_file(dataset_id, dataset.file_path, dataset_name)
            
            # Convert to numpy arrays for vectorized calculation
            times = np.array([ts.timestamp for ts in timeseries])
            values = np.array([ts.value for ts in timeseries])
            
            # Calculate cumulative depth using vectorized operations
            # Convert timestamps to numpy datetime64
            times_dt = times.astype('datetime64[ns]')
            
            # Calculate time deltas in hours (vectorized)
            time_deltas = np.diff(times_dt).astype('timedelta64[s]').astype(float) / 3600.0
            
            # Calculate average intensities (vectorized)
            avg_intensities = (values[1:] + values[:-1]) / 2.0
            
            # Calculate incremental depths (vectorized)
            inc_depths = avg_intensities * time_deltas
            
            # Calculate cumulative sum
            cumulative_depths = np.concatenate([[0.0], np.cumsum(inc_depths)])
            
            # Build response
            result = []
            for i in range(len(timeseries)):
                result.append({
                    "time": timeseries[i].timestamp.isoformat(),
                    "cumulative_depth": round(float(cumulative_depths[i]), 3)
                })

            # Downsample data if too many points (e.g., > 500)
            max_points = 500
            if len(result) > max_points:
                step = max(1, len(result) // max_points)
                downsampled = [result[i] for i in range(0, len(result), step)]
                # Ensure the last point is included
                if downsampled[-1] != result[-1]:
                    downsampled.append(result[-1])
                result = downsampled
            
            return {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "data": result
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            # Fall back to file parsing on error
            print(f"Error querying database: {e}, falling back to file parsing")
            return self._get_cumulative_depth_from_file(dataset_id, dataset.file_path, dataset_name)
    
    def _get_cumulative_depth_from_file(self, dataset_id: int, file_path: str, dataset_name: str) -> Dict[str, Any]:
        """Fallback method to calculate cumulative depth from file parsing"""
        try:
            data = import_r_file(file_path)
            df = pd.DataFrame(data['data'])
            df['time'] = pd.to_datetime(df['time'])
            df = df.sort_values('time')
            
            # Calculate cumulative depth using vectorized operations
            times = df['time'].values
            rainfall = df['rainfall'].values
            
            # Calculate time deltas in hours (vectorized)
            time_deltas = np.diff(times).astype('timedelta64[s]').astype(float) / 3600.0
            
            # Calculate average intensities (vectorized)
            avg_intensities = (rainfall[1:] + rainfall[:-1]) / 2.0
            
            # Calculate incremental depths (vectorized)
            inc_depths = avg_intensities * time_deltas
            
            # Calculate cumulative sum
            cumulative_depths = np.concatenate([[0.0], np.cumsum(inc_depths)])
            
            # Build response
            result = []
            for i in range(len(df)):
                result.append({
                    "time": df.iloc[i]['time'].isoformat(),
                    "cumulative_depth": round(float(cumulative_depths[i]), 3)
                })

            # Downsample data if too many points
            max_points = 500
            if len(result) > max_points:
                step = max(1, len(result) // max_points)
                downsampled = [result[i] for i in range(0, len(result), step)]
                if downsampled[-1] != result[-1]:
                    downsampled.append(result[-1])
                result = downsampled
            
            return {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "data": result
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"dataset_id": dataset_id, "data": [], "error": str(e)}

    def get_rainfall_timeseries(self, dataset_id: int) -> List[Dict[str, Any]]:
        """Get raw rainfall timeseries data"""
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return []
            
        try:
            # Try DB first
            # from domain.analysis import AnalysisTimeSeries
            from sqlmodel import select
            
            stmt = select(AnalysisTimeSeries).where(
                AnalysisTimeSeries.dataset_id == dataset_id
            ).order_by(AnalysisTimeSeries.timestamp)
            
            timeseries = self.session.exec(stmt).all()
            
            if timeseries:
                return [{"time": ts.timestamp.isoformat(), "value": ts.value} for ts in timeseries]
                
            # Fallback to file
            data = import_r_file(dataset.file_path)
            df = pd.DataFrame(data['data'])
            df['time'] = pd.to_datetime(df['time'])
            df = df.sort_values('time')
            
            return [{"time": row['time'].isoformat(), "value": row['rainfall']} for _, row in df.iterrows()]
            
        except Exception as e:
            print(f"Error getting timeseries: {e}")
            return []

class EventService:
    def __init__(self, session: Session):
        self.session = session

    def get_dataset(self, dataset_id: int) -> AnalysisDataset:
        return self.session.get(AnalysisDataset, dataset_id)

    def detect_storms(
        self, 
        dataset_id: int, 
        inter_event_minutes: int = 10, # Default 10 minutes
        min_total_mm: float = 2.0,
        min_intensity: float = 0.0,
        min_intensity_duration: int = 0,
        partial_percent: float = 20.0,
        use_consecutive_intensities: bool = True
    ) -> List[Dict[str, Any]]:
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return []
            
        try:
            # Try DB first
            from domain.fsa import FsaTimeSeries as AnalysisTimeSeries
            from sqlmodel import select
            
            stmt = select(AnalysisTimeSeries).where(
                AnalysisTimeSeries.dataset_id == dataset_id
            ).order_by(AnalysisTimeSeries.timestamp)
            
            timeseries = self.session.exec(stmt).all()
            
            if timeseries:
                data_list = [{"time": ts.timestamp, "value": ts.value} for ts in timeseries]
                df = pd.DataFrame(data_list)
            else:
                # Fallback to file
                data = import_r_file(dataset.file_path)
                df = pd.DataFrame(data['data'])
                df['time'] = pd.to_datetime(df['time'])
                df['value'] = df['rainfall']
            
            if df.empty:
                return []

            # Sort and prepare numpy arrays
            df = df.sort_values('time')
            rain = df['value'].to_numpy(dtype=np.float32, copy=False)
            times = df['time'].to_numpy(copy=False)
            
            if rain.size == 0:
                return []
                
            # Calculate time step in minutes
            if len(times) > 1:
                # Mode of differences
                diffs = np.diff(times).astype('timedelta64[m]').astype(int)
                # Filter out large gaps (likely separate files or errors) to find base step
                valid_diffs = diffs[diffs > 0]
                if valid_diffs.size > 0:
                    time_step_min = int(np.bincount(valid_diffs).argmax())
                else:
                    time_step_min = 1 # Default
            else:
                time_step_min = 1
                
            # Calculate consecZero based on inter_event_minutes
            consec_zero = max(1, int(inter_event_minutes / time_step_min))
            
            # Legacy _runs_of_zeros_separators logic
            # Find indices where a run of >= consec_zero zeros ends
            # Uses sliding window to find all positions with consec_zero consecutive zeros
            
            if consec_zero <= 0:
                seps = np.empty(0, dtype=np.int64)
            elif consec_zero == 1:
                # Any zero is a separator
                seps = np.where(rain == 0)[0]
            else:
                # Sliding window approach
                is_zero = (rain == 0)
                if len(rain) < consec_zero:
                    seps = np.empty(0, dtype=np.int64)
                else:
                    from numpy.lib.stride_tricks import sliding_window_view
                    # Check if each window of consec_zero elements are all zeros
                    w = sliding_window_view(is_zero, consec_zero).all(axis=1)
                    # Return indices of the LAST zero in each window
                    seps = np.where(w)[0] + (consec_zero - 1)
            
            # Create event boundaries using separators
            # Legacy: starts = np.r_[0, seps + 1], ends = np.r_[seps, len(rain) - 1]
            if len(seps) > 0:
                starts = np.r_[0, seps + 1]
                ends = np.r_[seps, len(rain) - 1]
                
                # Filter out invalid ranges (where start > end)
                valid = starts <= ends
                starts, ends = starts[valid], ends[valid]
            else:
                # No separators, entire dataset is one event
                starts = np.array([0])
                ends = np.array([len(rain) - 1])
            
            d_min = ((100 - partial_percent) / 100.0) * min_total_mm
            i_min = int(round(((100 - partial_percent) / 100.0) * min_intensity_duration))
            k = max(1, int(round(min_intensity_duration / max(1, time_step_min))))
            
            events = []
            event_counter = 1
            
            for s, e in zip(starts, ends):
                # Ensure indices are within bounds
                s = max(0, min(s, len(rain)-1))
                e = max(0, min(e, len(rain)-1))
                
                r = rain[s:e + 1]
                if r.size == 0 or float(r.max(initial=0.0)) == 0.0:
                    continue
                    
                # Depth over the whole block
                depth = float((r * (time_step_min / 60.0)).sum())
                
                # Intensity Tests
                above = (r > min_intensity)
                
                if use_consecutive_intensities:
                    if k <= r.size:
                        from numpy.lib.stride_tricks import sliding_window_view
                        w = sliding_window_view(above, k)
                        has_consec = bool(w.all(axis=1).any())
                    else:
                        has_consec = False
                        
                    intensity_count = min_intensity_duration if has_consec else 0
                    total_minutes_above = int(above.sum() * time_step_min)
                else:
                    total_minutes_above = int(above.sum() * time_step_min)
                    intensity_count = min_intensity_duration if total_minutes_above >= min_intensity_duration else 0
                    
                # Classification
                status = "No Event"
                passed = 0.0
                
                # Full event
                if depth > min_total_mm and intensity_count >= min_intensity_duration:
                    passed = 1.0
                    status = "Event"
                else:
                    # Partial scenarios
                    cond1 = (d_min <= depth < min_total_mm) and (intensity_count >= min_intensity_duration)
                    cond2 = (depth >= min_total_mm) and (i_min <= intensity_count < min_intensity_duration)
                    
                    cond3 = False
                    if use_consecutive_intensities:
                        cond3 = (depth > min_total_mm) and (total_minutes_above >= min_intensity_duration)
                        
                    if cond1 or cond2 or cond3:
                        passed = 0.5
                        status = "Partial Event"
                
                
                # Always append events, including "No Event"
                events.append({
                    "event_id": event_counter,
                    "start_time": pd.Timestamp(times[s]),
                    "end_time": pd.Timestamp(times[e]),
                    "total_mm": round(depth, 3),
                    "duration_hours": round((pd.Timestamp(times[e]) - pd.Timestamp(times[s])).total_seconds() / 3600, 2),
                    "peak_intensity": float(r.max()) if r.size > 0 else 0.0,
                    "status": status,
                    "passed": passed
                })
                event_counter += 1
                    
            return events
            
        except Exception as e:
            print(f"Error detecting storms: {e}")
            import traceback
            traceback.print_exc()
            return []

    def detect_dry_days(self, dataset_id: int, threshold_mm: float = 0.1, preceding_dry_days: int = 4) -> List[Dict[str, Any]]:
        """
        Return list of dates that are part of runs of dry days longer than 'preceding_dry_days'.
        Uses legacy vectorized logic.
        """
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return []
            
        try:
            # Try DB first
            from domain.fsa import FsaTimeSeries as AnalysisTimeSeries
            from sqlmodel import select
            
            stmt = select(AnalysisTimeSeries).where(
                AnalysisTimeSeries.dataset_id == dataset_id
            ).order_by(AnalysisTimeSeries.timestamp)
            
            timeseries = self.session.exec(stmt).all()
            
            if timeseries:
                data_list = [{"time": ts.timestamp, "value": ts.value} for ts in timeseries]
                df = pd.DataFrame(data_list)
            else:
                # Fallback to file
                data = import_r_file(dataset.file_path)
                df = pd.DataFrame(data['data'])
                df['time'] = pd.to_datetime(df['time'])
                df['value'] = df['rainfall']
            
            if df.empty:
                return []
                
            df['time'] = pd.to_datetime(df['time'])
            
            # Resample to daily totals
            df_per_diem = df.set_index('time').resample('D')['value'].sum().reset_index()
            df_per_diem.columns = ['rain_date', 'rainfall_mm']
            
            if df_per_diem.empty:
                return []
            
            # Legacy vectorized logic
            is_dry = df_per_diem["rainfall_mm"].to_numpy(copy=False) <= threshold_mm
            
            # Group runs of dry days using transitions in ~is_dry
            groups = np.cumsum(~is_dry)  # increments when wet encountered
            
            # Cumulative count within each group
            dry_runs = pd.Series(is_dry, dtype="int32").groupby(groups).cumsum().to_numpy()
            
            # Mask for days that are part of runs longer than preceding_dry_days
            mask = is_dry & (dry_runs > preceding_dry_days)
            
            # Extract matching dates
            dry_day_dates = pd.to_datetime(df_per_diem.loc[mask, "rain_date"]).dt.date.tolist()
            
            # Format as list of dicts with date and total_mm
            dry_days = []
            for idx in df_per_diem[mask].index:
                dry_days.append({
                    "date": df_per_diem.loc[idx, "rain_date"].date(),
                    "total_mm": round(df_per_diem.loc[idx, "rainfall_mm"], 3)
                })
            
            return dry_days
            
        except Exception as e:
            print(f"Error detecting dry days: {e}")
            import traceback
            traceback.print_exc()
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
            # Try to query timeseries from database
            # from domain.analysis import AnalysisTimeSeries
            from sqlmodel import select
            
            stmt = select(AnalysisTimeSeries).where(
                AnalysisTimeSeries.dataset_id == dataset_id
            ).order_by(AnalysisTimeSeries.timestamp)
            
            if start_date:
                stmt = stmt.where(AnalysisTimeSeries.timestamp >= start_date)
            if end_date:
                stmt = stmt.where(AnalysisTimeSeries.timestamp <= end_date)
                
            timeseries = self.session.exec(stmt).all()
            
            if timeseries:
                return [
                    {
                        "time": ts.timestamp,
                        "depth": ts.depth if ts.depth is not None else 0.0,
                        "velocity": ts.velocity if ts.velocity is not None else 0.0,
                        "flow": ts.flow if ts.flow is not None else 0.0
                    }
                    for ts in timeseries
                ]

            # Fallback to file parsing
            data = import_fdv_file(dataset.file_path)
            df = pd.DataFrame(data['data'])
            df['time'] = pd.to_datetime(df['time'])
            
            if start_date:
                df = df[df['time'] >= start_date]
            if end_date:
                df = df[df['time'] <= end_date]
                
            # Return time, depth, velocity, flow
            return df[['time', 'depth', 'velocity', 'flow']].to_dict('records')
        except Exception as e:
            print(f"Error getting scatter data: {e}")
            return []

    def get_scatter_graph_data(
        self, 
        dataset_id: int, 
        plot_mode: str = "velocity",
        iso_min: float = None,
        iso_max: float = None,
        iso_count: int = 2
    ) -> Dict[str, Any]:
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return {}

        try:
            # Try to query timeseries from database
            # from domain.analysis import AnalysisTimeSeries
            from sqlmodel import select
            
            # Optimize: Fetch only needed columns to avoid ORM overhead
            stmt = select(
                AnalysisTimeSeries.timestamp,
                AnalysisTimeSeries.depth,
                AnalysisTimeSeries.velocity,
                AnalysisTimeSeries.flow
            ).where(
                AnalysisTimeSeries.dataset_id == dataset_id
            )
            results = self.session.exec(stmt).all()
            
            data = {} # Placeholder for file data if we use DB
            
            if results:
                data_list = [
                    {
                        "time": r[0],
                        "depth": r[1] if r[1] is not None else 0.0,
                        "velocity": r[2] if r[2] is not None else 0.0,
                        "flow": r[3] if r[3] is not None else 0.0
                    }
                    for r in results
                ]
                df = pd.DataFrame(data_list)
            else:
                # Fallback to file parsing
                data = import_fdv_file(dataset.file_path)
                df = pd.DataFrame(data['data'])
            
            # Extract pipe parameters from dataset metadata, falling back to data file or defaults
            import json
            try:
                metadata = json.loads(dataset.metadata_json)
            except:
                metadata = {}
            
            # Default params if not found
            pipe_params = {
                "diameter": metadata.get("pipe_diameter") or data.get("pipe_diameter", 300), # mm
                "shape": metadata.get("pipe_shape") or data.get("pipe_shape", "CIRC"),
                "roughness": metadata.get("roughness") or data.get("roughness", 1.5), # mm
                "gradient": metadata.get("gradient") or data.get("gradient", 0.01), # m/m
                "length": metadata.get("pipe_length") or data.get("length", 100), # m
                "us_invert": metadata.get("us_invert") or data.get("us_invert", 0),
                "ds_invert": metadata.get("ds_invert") or data.get("ds_invert", 0),
                "height": metadata.get("pipe_height") or data.get("pipe_height", 300), # mm
                "width": metadata.get("pipe_width") or data.get("pipe_width", 300) # mm
            }
            
            # Calculate gradient if inverts are available
            if pipe_params["us_invert"] > 0 and pipe_params["ds_invert"] > 0 and pipe_params["length"] > 0:
                pipe_params["gradient"] = max((pipe_params["us_invert"] - pipe_params["ds_invert"]) / pipe_params["length"], 0.00001)

            # 1. Scatter Data
            # 1. Scatter Data
            # df is already created above
            
            # Downsample if too many points
            target_points = 2000
            if len(df) > target_points:
                scatter_data = self._downsample_scatter_data(df, target_points)
            else:
                scatter_data = df[['depth', 'velocity', 'flow']].to_dict('records')

            # 2. Colebrook-White Curve
            cbw_curve = self._calculate_cbw_curve(pipe_params)

            # 3. Iso-curves based on plot mode
            if plot_mode == "velocity":
                # Depth vs Velocity: Iso-Q curves (constant flow)
                iso_curves = self._calculate_iso_q_curves(pipe_params, iso_min, iso_max, iso_count, df)
                iso_type = "flow"
            else:
                # Depth vs Flow: Iso-V curves (constant velocity)
                iso_curves = self._calculate_iso_v_curves(pipe_params, iso_min, iso_max, iso_count, df)
                iso_type = "velocity"

            # 4. Pipe Profile
            pipe_profile = self._calculate_pipe_profile(pipe_params, scatter_data, cbw_curve, plot_mode)

            return {
                "scatter_data": scatter_data,
                "cbw_curve": cbw_curve,
                "iso_curves":iso_curves,
                "iso_type": iso_type,
                "pipe_params": pipe_params,
                "pipe_profile": pipe_profile,
                "plot_mode": plot_mode
            }
        except Exception as e:
            print(f"Error generating scatter graph data: {e}")
            return {}

    def _downsample_scatter_data(self, df: pd.DataFrame, target_points: int) -> List[Dict[str, Any]]:
        """
        Downsample scatter data using simple random sampling.
        This is faster than grid-based methods and statistically preserves density.
        """
        try:
            if len(df) <= target_points:
                return df[['depth', 'velocity', 'flow']].to_dict('records')
            
            # Simple random sample
            return df.sample(n=target_points).to_dict('records')
            
        except Exception as e:
            print(f"Downsampling error: {e}")
            return df[['depth', 'velocity', 'flow']].head(target_points).to_dict('records')

    def _calculate_cbw_curve(self, params: Dict[str, Any]) -> List[Dict[str, float]]:
        import math
        
        diameter_mm = params["diameter"]
        roughness_mm = params["roughness"]
        gradient = params["gradient"]
        
        if diameter_mm <= 0 or gradient <= 0:
            return []

        diameter_m = diameter_mm / 1000.0
        roughness_m = roughness_mm / 1000.0
        g = 9.807
        nu = 1.004e-6  # Kinematic viscosity m^2/s

        depth_proportions = [
            0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.15, 0.2, 0.25, 
            0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 
            0.75, 0.8, 0.85, 0.9, 0.95, 0.96, 0.97, 0.98, 0.99, 1.0
        ]

        curve = [{"depth": 0, "velocity": 0, "flow": 0}]  # Start at zero
        
        for ratio in depth_proportions:
            depth_m = diameter_m * ratio
            
            # Calculate theta (angle subtended by water surface)
            try:
                theta = 2 * math.acos(1 - 2 * ratio)
            except ValueError:
                curve.append({"depth": depth_m * 1000, "velocity": 0, "flow": 0})
                continue

            # Flow Area and Wetted Perimeter  
            # For circular segment: A = (D²/8) * (θ - sin(θ))
            area = (diameter_m**2 / 8) * (theta - math.sin(theta))
            # For circular segment: P = D * θ / 2
            perimeter = diameter_m * theta / 2

            if area <= 0 or perimeter <= 0:
                curve.append({"depth": depth_m * 1000, "velocity": 0, "flow": 0})
                continue

            # Hydraulic Radius and Hydraulic Diameter
            R = area / perimeter
            Dh = 4.0 * R

            # Iterative friction factor calculation
            tol = 1e-6
            max_iters = 50
            omega = 0.5  # Under-relaxation factor
            f = 0.02  # Initial guess

            for _ in range(max_iters):
                # Calculate velocity with current friction factor
                V = math.sqrt(8.0 * g * R * gradient / f) if f > 0 else 0.0
                
                # Reynolds number
                Re = (V * Dh) / nu
                
                # New friction factor
                if Re < 2300:  # Laminar
                    f_new = 64.0 / max(Re, 1e-12)
                else:  # Turbulent - Swamee-Jain
                    term = (roughness_m / (3.7 * Dh)) + (5.74 / (Re ** 0.9))
                    f_new = 0.25 / (math.log10(term)) ** 2
                
                # Under-relaxation
                f_u = (1 - omega) * f + omega * f_new
                
                # Check convergence
                if abs(f_u - f) / max(f, 1e-12) < tol:
                    f = f_u
                    break
                f = f_u

            # Final velocity and flow with converged friction factor
            V = math.sqrt(8.0 * g * R * gradient / f) if f > 0 else 0.0
            Q = area * V

            curve.append({
                "depth": depth_m * 1000,  # mm
                "velocity": V,  # m/s
                "flow": Q * 1000  # L/s
            })
            
        return curve


    def _calculate_iso_q_curves(
        self, 
        params: Dict[str, Any],
        iso_min: float = None,
        iso_max: float = None,
        iso_count: int = 2,
        df: pd.DataFrame = None
    ) -> List[Dict[str, Any]]:
        # Generate curves for constant Flow (Q)
        import math
        diameter_mm = params["diameter"]
        if diameter_mm <= 0:
            return []
            
        diameter_m = diameter_mm / 1000.0
        
        # Determine Q values based on data if not provided
        if iso_min is None or iso_max is None:
            if df is not None and 'flow' in df.columns:
                flow_data = df[df['flow'] > 0]['flow']
                if not flow_data.empty:
                    if iso_min is None:
                        iso_min = float(flow_data.min())
                    if iso_max is None:
                        iso_max = float(flow_data.max())
        
        # Defaults if still None
        if iso_min is None:
            iso_min = 10
        if iso_max is None:
            iso_max = 100
            
        # Generate Q values
        if iso_count <= 1:
            q_values = [iso_max]
        else:
            q_values = [iso_min + (iso_max - iso_min) * i / (iso_count - 1) for i in range(iso_count)]
        
        curves = []
        depth_proportions = [
            0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 
            0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0
        ]
        
        for q_val in q_values:
            points = []
            q_m3s = q_val / 1000.0
            
            for ratio in depth_proportions:
                try:
                    theta = 2 * math.acos(1 - 2 * ratio)
                    area = (diameter_m**2 / 8) * (theta - math.sin(theta))
                    
                    if area > 0:
                        velocity = q_m3s / area
                        points.append({
                            "depth": ratio * diameter_mm,
                            "velocity": velocity,
                            "flow": q_val
                        })
                except:
                    continue
            
            if points:
                curves.append({
                    "value": q_val,
                    "points": points
                })
                
        return curves
    
    def _calculate_iso_v_curves(
        self,
        params: Dict[str, Any],
        iso_min: float = None,
        iso_max: float = None,
        iso_count: int = 2,
        df: pd.DataFrame = None
    ) -> List[Dict[str, Any]]:
        # Generate curves for constant Velocity (V)
        # For Depth vs Flow plot, we show constant velocity lines
        import math
        diameter_mm = params["diameter"]
        if diameter_mm <= 0:
            return []
            
        diameter_m = diameter_mm / 1000.0
        
        # Determine V values based on data if not provided
        if iso_min is None or iso_max is None:
            if df is not None and 'velocity' in df.columns:
                velocity_data = df[df['velocity'] > 0]['velocity']
                if not velocity_data.empty:
                    if iso_min is None:
                        iso_min = float(velocity_data.min())
                    if iso_max is None:
                        iso_max = float(velocity_data.max())
        
        # Defaults if still None
        if iso_min is None:
            iso_min = 0.1
        if iso_max is None:
            iso_max = 1.0
            
        # Generate V values
        if iso_count <= 1:
            v_values = [iso_max]
        else:
            v_values = [iso_min + (iso_max - iso_min) * i / (iso_count - 1) for i in range(iso_count)]
        
        curves = []
        depth_proportions = [
            0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 
            0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0
        ]
        
        for v_val in v_values:
            points = []
            
            for ratio in depth_proportions:
                try:
                    theta = 2 * math.acos(1 - 2 * ratio)
                    area = (diameter_m**2 / 8) * (theta - math.sin(theta))
                    
                    if area > 0:
                        # Q = A * V
                        flow_m3s = area * v_val
                        flow_ls = flow_m3s * 1000
                        
                        points.append({
                            "depth": ratio * diameter_mm,
                            "flow": flow_ls,
                            "velocity": v_val
                        })
                except:
                    continue
            
            if points:
                curves.append({
                    "value": v_val,
                    "points": points
                })
                
        return curves
    
    def _calculate_pipe_profile(
        self,
        params: Dict[str, Any],
        scatter_data: List[Dict[str, Any]],
        cbw_curve: List[Dict[str, Any]],
        plot_mode: str = "velocity"
    ) -> List[List[Dict[str, float]]]:
        """
        Generate pipe profile lines matching the legacy Python implementation.
        Returns a list of line segments, where each segment is a list of {x, y} points.
        """
        import math
        
        diameter_mm = params.get("diameter", 0)
        shape = params.get("shape", "CIRC")
        
        if diameter_mm <= 0 or shape != "CIRC":
            return []
        
        # Determine X variable based on plot mode
        x_var = "velocity" if plot_mode == "velocity" else "flow"
        
        # Calculate data extents (scatter ∪ CBW)
        all_x = []
        all_y = []
        
        for point in scatter_data:
            if x_var in point and 'depth' in point:
                all_x.append(point[x_var])
                all_y.append(point['depth'])
        
        for point in cbw_curve:
            if x_var in point and 'depth' in point:
                all_x.append(point[x_var])
                all_y.append(point['depth'])
        
        if not all_x or not all_y:
            return []
        
        data_x_min = min(all_x)
        data_x_max = max(all_x)
        data_y_min = min(all_y + [0.0])  # Include 0
        data_y_max = max(all_y + [diameter_mm])  # Include pipe diameter
        
        # Calculate axis ratio (prevents distortion)
        # Matches legacy: axisRatio = ((y_max - y_min) / (x_max - x_min)) / fig_aspect
        x_rng = max(1e-12, data_x_max - data_x_min)
        y_rng = max(1e-12, data_y_max - data_y_min)
        
        # Assume figure aspect ratio (height/width) ~ 500/800 = 0.625
        fig_aspect = 0.625
        axis_ratio = max((y_rng / x_rng) / fig_aspect, 1e-12)
        
        # Pipe anchors span the data window
        pipe_in_station = data_x_min
        pipe_out_station = data_x_max
        
        # Pipe exaggeration factor
        pipe_exag = 0.1
        
        # Pipe "half width" in X-axis units (adjusted by axis ratio)
        char_half_width_base = diameter_mm / 2.0
        char_half_width = (char_half_width_base / axis_ratio) * pipe_exag
        
        # Generate depth proportions
        pipe_profile_depth_prop = [i / 50.0 for i in range(51)]
        
        # Generate circular pipe profile lines
        lines = []
        
        # Back outline (connects outlet to inlet)
        back_outline = []
        for prop in pipe_profile_depth_prop:
            angle = (prop * 360 + 180) * math.pi / 180
            x_offset = math.sin(angle) * char_half_width
            back_outline.append({"x": x_offset + pipe_out_station, "y": prop * diameter_mm})
        
        for prop in reversed(pipe_profile_depth_prop):
            angle = (prop * 360 + 180) * math.pi / 180
            x_offset = math.sin(angle) * char_half_width
            back_outline.append({"x": x_offset + pipe_in_station, "y": prop * diameter_mm})
        
        back_outline.append({"x": pipe_out_station, "y": 0})
        lines.append(back_outline)
        
        # Front top half (outlet)
        front_top = []
        for i in range(len(pipe_profile_depth_prop) // 2 + 1):
            prop = pipe_profile_depth_prop[i]
            angle = prop * 360 * math.pi / 180
            x_offset = math.sin(angle) * char_half_width
            front_top.append({"x": x_offset + pipe_out_station, "y": prop * diameter_mm})
        lines.append(front_top)
        
        # Front bottom half (inlet)
        front_bottom = []
        for i in range(len(pipe_profile_depth_prop) - 1, len(pipe_profile_depth_prop) // 2 - 1, -1):
            prop = pipe_profile_depth_prop[i]
            angle = prop * 360 * math.pi / 180
            x_offset = math.sin(angle) * char_half_width
            front_bottom.append({"x": x_offset + pipe_in_station, "y": prop * diameter_mm})
        lines.append(front_bottom)
        
        # Inlet cap (end view)
        inlet_cap = []
        for prop in pipe_profile_depth_prop:
            angle = (prop * 180 + 180) * math.pi / 180
            x_offset = char_half_width * math.sin(angle)
            y_offset = char_half_width + (char_half_width * math.cos(angle))
            inlet_cap.append({"x": x_offset + pipe_in_station, "y": y_offset})
        lines.append(inlet_cap)
        
        return lines


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
