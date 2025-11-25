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

    def get_cumulative_depth(self, dataset_id: int) -> Dict[str, Any]:
        """
        Calculate cumulative rainfall depth over time.
        Matches legacy graphCumulativeDepth implementation.
        """
        # Get dataset info from DB first
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return {"dataset_id": dataset_id, "data": []}
        
        # Extract needed info before file I/O
        file_path = dataset.file_path
        dataset_name = dataset.name
        
        # Now do file I/O (session can be released by FastAPI)
        try:
            data = import_r_file(file_path)
            df = pd.DataFrame(data['data'])
            df['time'] = pd.to_datetime(df['time'])
            df = df.sort_values('time')
            
            # Calculate cumulative depth using trapezoidal integration
            # cum_depth[i] = cum_depth[i-1] + avg_intensity * time_delta
            cumulative_depths = []
            cum_depth = 0.0
            
            for i in range(len(df)):
                if i == 0:
                    cumulative_depths.append(0.0)
                else:
                    # Time delta in hours
                    time_delta = (df.iloc[i]['time'] - df.iloc[i-1]['time']).total_seconds() / 3600.0
                    # Average intensity (mm/hr)
                    avg_intensity = (df.iloc[i]['rainfall'] + df.iloc[i-1]['rainfall']) / 2.0
                    # Incremental depth (mm)
                    inc_depth = avg_intensity * time_delta
                    cum_depth += inc_depth
                    cumulative_depths.append(cum_depth)
            
            # Build response
            result = []
            for i in range(len(df)):
                result.append({
                    "time": df.iloc[i]['time'].isoformat(),
                    "cumulative_depth": round(cumulative_depths[i], 3)
                })
            
            return {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "data": result
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"dataset_id": dataset_id, "data": [], "error": str(e)}

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
            data = import_fdv_file(dataset.file_path)
            
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
            df = pd.DataFrame(data['data'])
            
            # Downsample if too many points
            target_points = 3000
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
        Downsample scatter data using a grid-based approach to preserve the visual envelope.
        """
        try:
            # Calculate grid size based on target points (approx sqrt)
            # We want roughly target_points bins. 
            # Aspect ratio of V vs D is roughly 2:1 or 3:2 usually, but let's assume square grid for simplicity
            # or fixed grid size.
            
            # Let's try a fixed grid size that yields approx target_points
            # If we have 100k points, we want to reduce to 3k.
            
            # Determine bounds
            v_min, v_max = df['velocity'].min(), df['velocity'].max()
            d_min, d_max = df['depth'].min(), df['depth'].max()
            
            if v_min == v_max or d_min == d_max:
                return df[['depth', 'velocity', 'flow']].head(target_points).to_dict('records')

            # Create bins
            # We want approx target_points filled bins.
            # Let's try a 60x50 grid (3000 cells)
            v_bins = 60
            d_bins = 50
            
            df['v_bin'] = pd.cut(df['velocity'], bins=v_bins, labels=False)
            df['d_bin'] = pd.cut(df['depth'], bins=d_bins, labels=False)
            
            # Group by bins and keep the point with max flow (or just first, or max depth?)
            # Keeping max flow might be interesting, or maybe just random/first to show density.
            # Actually, to show the "envelope", we want points on the edges.
            # A simple way is to take the max flow in each bin, which usually correlates with max velocity/depth in that bin.
            # Or we can take the first point.
            # Let's take the point with the maximum Flow in each bin to prioritize high-flow events?
            # Or maybe just the first one is faster and sufficient for "density".
            # Let's try max flow.
            
            downsampled = df.loc[df.groupby(['v_bin', 'd_bin'])['flow'].idxmax()].dropna()
            
            return downsampled[['depth', 'velocity', 'flow']].to_dict('records')
            
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
