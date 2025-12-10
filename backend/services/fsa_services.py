"""
FSA Service Adapters
These classes wrap the existing Flow Survey Analysis to work with FSA domain models.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlmodel import Session, select
from domain.fsa import FsaDataset, FsaTimeSeries

# Import existing services
from services.analysis import RainfallService as BaseRainfallService
from services.analysis import EventService as BaseEventService
from services.analysis import FDVService as BaseFDVService


class FsaRainfallService(BaseRainfallService):
    """Adapter for RainfallService to work with FSA models"""
    
    def get_dataset(self, dataset_id: int) -> FsaDataset:
        return self.session.get(FsaDataset, dataset_id)
    
    def get_cumulative_depth(self, dataset_id: int) -> Dict[str, Any]:
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return {"dataset_id": dataset_id, "data": []}
        
        dataset_name = dataset.name
        
        try:
            # Query FSA timeseries data from database
            stmt = select(FsaTimeSeries).where(
                FsaTimeSeries.dataset_id == dataset_id
            ).order_by(FsaTimeSeries.timestamp)
            
            timeseries = self.session.exec(stmt).all()
            
            if not timeseries or len(timeseries) == 0:
                print(f"No timeseries data in database for dataset {dataset_id}")
                return {"dataset_id": dataset_id, "data": []}
            
            # Use parent class logic with FSA timeseries
            import numpy as np
            times = np.array([ts.timestamp for ts in timeseries])
            values = np.array([ts.value for ts in timeseries])
            
            times_dt = times.astype('datetime64[ns]')
            time_deltas = np.diff(times_dt).astype('timedelta64[s]').astype(float) / 3600.0
            avg_intensities = (values[1:] + values[:-1]) / 2.0
            inc_depths = avg_intensities * time_deltas
            cumulative_depths = np.concatenate([[0.0], np.cumsum(inc_depths)])
            
            result = []
            for i in range(len(timeseries)):
                result.append({
                    "time": timeseries[i].timestamp.isoformat(),
                    "cumulative_depth": round(float(cumulative_depths[i]), 3)
                })

            # Downsample if needed
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
            stmt = select(FsaTimeSeries).where(
                FsaTimeSeries.dataset_id == dataset_id
            ).order_by(FsaTimeSeries.timestamp)
            
            timeseries = self.session.exec(stmt).all()
            
            if timeseries:
                return [{"time": ts.timestamp.isoformat(), "value": ts.value} for ts in timeseries]
            
            return []
            
        except Exception as e:
            print(f"Error getting timeseries: {e}")
            return []


class FsaEventService(BaseEventService):
    """Adapter for EventService to work with FSA models"""
    
    def get_dataset(self, dataset_id: int) -> FsaDataset:
        return self.session.get(FsaDataset, dataset_id)


class FsaFDVService(BaseFDVService):
    """Adapter for FDVService to work with FSA models"""
    
    def get_dataset(self, dataset_id: int) -> FsaDataset:
        return self.session.get(FsaDataset, dataset_id)
    
    def get_scatter_data(self, dataset_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return []
            
        try:
            # Query FSA timeseries from database
            stmt = select(FsaTimeSeries).where(
                FsaTimeSeries.dataset_id == dataset_id
            ).order_by(FsaTimeSeries.timestamp)
            
            if start_date:
                stmt = stmt.where(FsaTimeSeries.timestamp >= start_date)
            if end_date:
                stmt = stmt.where(FsaTimeSeries.timestamp <= end_date)
                
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

            return []
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
            # Query FSA timeseries from database
            stmt = select(FsaTimeSeries).where(
                FsaTimeSeries.dataset_id == dataset_id
            )
            timeseries = self.session.exec(stmt).all()
            
            if not timeseries:
                return {}
            
            import pandas as pd
            data_list = [
                {
                    "time": ts.timestamp,
                    "depth": ts.depth if ts.depth is not None else 0.0,
                    "velocity": ts.velocity if ts.velocity is not None else 0.0,
                    "flow": ts.flow if ts.flow is not None else 0.0
                }
                for ts in timeseries
            ]
            df = pd.DataFrame(data_list)
            
            # Extract pipe parameters from dataset metadata
            import json
            try:
                metadata = json.loads(dataset.metadata_json)
            except:
                metadata = {}
            
            # Default params
            pipe_params = {
                "diameter": metadata.get("pipe_diameter", 300),
                "shape": metadata.get("pipe_shape", "CIRC"),
                "roughness": metadata.get("roughness", 1.5),
                "gradient": metadata.get("gradient", 0.01),
                "length": metadata.get("pipe_length", 100),
                "us_invert": metadata.get("us_invert", 0),
                "ds_invert": metadata.get("ds_invert", 0),
                "height": metadata.get("pipe_height", 300),
                "width": metadata.get("pipe_width", 300)
            }
            
            # Calculate gradient if inverts are available
            if pipe_params["us_invert"] > 0 and pipe_params["ds_invert"] > 0 and pipe_params["length"] > 0:
                pipe_params["gradient"] = max((pipe_params["us_invert"] - pipe_params["ds_invert"]) / pipe_params["length"], 0.00001)

            # Use parent class methods for calculations
            target_points = 3000
            if len(df) > target_points:
                scatter_data = self._downsample_scatter_data(df, target_points)
            else:
                scatter_data = df[['depth', 'velocity', 'flow']].to_dict('records')

            cbw_curve = self._calculate_cbw_curve(pipe_params)

            if plot_mode == "velocity":
                iso_curves = self._calculate_iso_q_curves(pipe_params, iso_min, iso_max, iso_count, df)
                iso_type = "flow"
            else:
                iso_curves = self._calculate_iso_v_curves(pipe_params, iso_min, iso_max, iso_count, df)
                iso_type = "velocity"

            pipe_profile = self._calculate_pipe_profile(pipe_params, scatter_data, cbw_curve, plot_mode)

            return {
                "scatter_data": scatter_data,
                "cbw_curve": cbw_curve,
                "iso_curves": iso_curves,
                "iso_type": iso_type,
                "pipe_params": pipe_params,
                "pipe_profile": pipe_profile,
                "plot_mode": plot_mode
            }
        except Exception as e:
            print(f"Error generating scatter graph data: {e}")
            import traceback
            traceback.print_exc()
            return {}
