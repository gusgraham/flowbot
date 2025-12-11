from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import io
import json
from datetime import datetime
from sqlmodel import Session, select
from services.timeseries import TimeSeriesService
from infra.storage import StorageService
from domain.wq import (
    WaterQualityProject, 
    WQMonitor, 
    WQTimeSeries, 
    WaterQualityDataset,
    WQMonitorCreate,
    WaterQualityProjectCreate
)

class WQService:
    def __init__(self, session: Session):
        self.session = session
        self.storage = StorageService()

    def create_project(self, project_data: WaterQualityProjectCreate, owner_id: int) -> WaterQualityProject:
        project = WaterQualityProject.model_validate(project_data)
        project.owner_id = owner_id
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return project

    def list_projects(self, user_id: int, is_admin: bool = False, offset: int = 0, limit: int = 100) -> List[WaterQualityProject]:
        if is_admin:
            return self.session.exec(select(WaterQualityProject).offset(offset).limit(limit)).all()
        # Add filtering logic for ownership/collaboration here if needed
        return self.session.exec(select(WaterQualityProject).where(WaterQualityProject.owner_id == user_id).offset(offset).limit(limit)).all()

    def get_project(self, project_id: int) -> Optional[WaterQualityProject]:
        return self.session.get(WaterQualityProject, project_id)

    def delete_project(self, project_id: int) -> bool:
        project = self.session.get(WaterQualityProject, project_id)
        if not project:
            return False
        self.session.delete(project)
        self.session.commit()
        return True

    def list_monitors(self, project_id: int) -> List[WQMonitor]:
        return self.session.exec(select(WQMonitor).where(WQMonitor.project_id == project_id)).all()

    def create_dataset(self, project_id: int, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        1. Save raw file.
        2. Create Dataset record.
        3. Parse headers and extract default monitor name (Legacy Format).
           - Row 0: Monitor Name
           - Row 1: Headers
           - Row 2: Units (Skip)
        """
        # Save file
        file_path = self.storage.save_file(file_content, filename, subfolder=f"wq/projects/{project_id}/raw")
        
        monitor_name = None
        headers = []

        try:
            # 1. Extract Monitor Name (Row 0)
            # Read just the first line as a dataframe
            df_monitor = pd.read_csv(io.BytesIO(file_content), header=None, nrows=1)
            if not df_monitor.empty:
                val = df_monitor.iloc[0, 0]
                # Handle potential quoting or extra chars
                monitor_name = str(val).strip()
            
            # 2. Extract Headers (Row 1)
            # Use header=1 to explicitly say "Row 1 is the header", skipping Row 0 automatically.
            df_headers = pd.read_csv(io.BytesIO(file_content), header=1, nrows=0)
            headers = df_headers.columns.tolist()

        except Exception as e:
            print(f"Parsing error: {e}")
            # Fallback
            if not headers:
                 try:
                    df_fallback = pd.read_csv(io.BytesIO(file_content), nrows=0)
                    headers = df_fallback.columns.tolist()
                 except:
                    pass
            if not monitor_name:
                monitor_name = filename.split('.')[0]

        # Create Record
        dataset = WaterQualityDataset(
            name=filename,
            project_id=project_id,
            file_path=file_path,
            original_filename=filename,
            status="pending",
            metadata_json={"headers": headers, "extracted_monitor_name": monitor_name}
        )
        self.session.add(dataset)
        self.session.commit()
        self.session.refresh(dataset)
        
        return {
            "dataset_id": dataset.id,
            "headers": headers,
            "filename": filename,
            "details": {
                "detected_monitor_name": monitor_name
            }
        }

    def process_dataset(self, dataset_id: int, mapping: Dict[str, str], monitor_name: str, monitor_id: Optional[int] = None) -> WQMonitor:
        """
        1. Load dataset file.
        2. Apply mapping.
        3. Create/Get Monitor.
        4. Save TimeSeries.
        """
        dataset = self.session.get(WaterQualityDataset, dataset_id)
        if not dataset:
            raise ValueError("Dataset not found")
            
        # 1. Load Data
        # We need to read the file from storage. 
        # Since storage saves to disk, we can read from disk if we know the path.
        # Assuming file_path is absolute or relative to storage root.
        # Ideally storage service provides a 'read' method, but for now we'll assume local path or read via pandas.
        # If storage is S3-like, we need a read method. 
        # Using self.storage.base_path to construct full path if simple local storage.
        
        # Hack: Assuming local file storage for this implementation
        import os
        full_path = dataset.file_path
        if not os.path.exists(full_path):
             # Try prepending base path if it's relative
             # But storage returns full path usually? Let's check storage service... 
             # For now, let's assume standard pandas read works if path is valid.
             pass

        try:
            # Legacy Format:
            # Row 0: Monitor Name -> Skipped automatically because header=1
            # Row 1: Headers -> header=1
            # Row 2: Units -> Skip (skiprows=[2])
            # Data starts Row 3
            df = pd.read_csv(full_path, header=1, skiprows=[2])
        except Exception as e:
            dataset.status = "error"
            self.session.add(dataset)
            self.session.commit()
            raise ValueError(f"Could not read file: {e}")

        # 2. Get/Create Monitor
        if monitor_id:
            monitor = self.session.get(WQMonitor, monitor_id)
            if not monitor:
                 raise ValueError("Monitor not found")
        else:
            # Create new monitor
            monitor = WQMonitor(
                project_id=dataset.project_id,
                name=monitor_name
            )
            self.session.add(monitor)
            self.session.commit()
            self.session.refresh(monitor)

        # 3. Process each mapped variable
        # Mapping: { "StandardVarName": "CsvColumnName" }
        # Special key: "Date" for timestamp
        
        date_col = mapping.get("Date") or mapping.get("Timestamp")
        if not date_col or date_col not in df.columns:
             # Try auto-detect
             # Or fail
             dataset.status = "error"
             self.session.add(dataset)
             self.session.commit()
             raise ValueError("Date column mapping missing or invalid")

        df[date_col] = pd.to_datetime(df[date_col], dayfirst=True) # Assume dayfirst for UK/AU/etc if ambiguous, or use inference
        df = df.sort_values(date_col)
        
        start_time = df[date_col].min().to_pydatetime()
        end_time = df[date_col].max().to_pydatetime()

        created_ts = []

        for std_var, csv_col in mapping.items():
            if std_var in ["Date", "Timestamp"] or not csv_col or csv_col == "None":
                continue
            
            if csv_col not in df.columns:
                continue

            # Extract series
            series_df = df[[date_col, csv_col]].copy()
            series_df.columns = ['time', 'value']
            # Drop NaNs
            series_df = series_df.dropna()

            if series_df.empty:
                continue

            # Save Parquet
            parquet_filename = f"wq_{dataset.id}_{monitor.id}_{std_var}.parquet"
            buf = io.BytesIO()
            series_df.to_parquet(buf, index=False)
            buf.seek(0)
            
            saved_path = self.storage.save_file(
                buf.getvalue(), 
                parquet_filename, 
                subfolder=f"wq/timeseries/{dataset.project_id}"
            )
            
            # Create TimeSeries Record
            ts = WQTimeSeries(
                monitor_id=monitor.id,
                dataset_id=dataset.id,
                variable=std_var,
                start_time=start_time,
                end_time=end_time,
                filename=saved_path
            )
            self.session.add(ts)
            created_ts.append(ts)

        dataset.status = "processed"
        self.session.add(dataset)
        self.session.commit()
        
        return monitor

    def get_graph_data(self, monitor_id: int, variables: Optional[List[str]] = None, points: int = 500, resample: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve data for a monitor. 
        Downsample to ~points using simple decimation or binning.
        If resample is provided (e.g. 'D', 'W', 'M', 'A'), use pandas resample mean.
        """
        stmt = select(WQTimeSeries).where(WQTimeSeries.monitor_id == monitor_id)
        if variables:
            stmt = stmt.where(WQTimeSeries.variable.in_(variables))
            
        ts_records = self.session.exec(stmt).all()
        
        result = {}
        for ts in ts_records:
            try:
                df = pd.read_parquet(ts.filename)
                
                # Prepare Raw Data (Downsampled)
                df_raw = df.copy()
                if len(df_raw) > points:
                    step = len(df_raw) // points
                    df_raw = df_raw.iloc[::step]
                
                raw_list = []
                for _, row in df_raw.iterrows():
                    raw_list.append({
                        "time": row['time'].isoformat(),
                        "value": row['value']
                    })
                result[ts.variable] = raw_list

                # Calculate Mean Data if requested
                if resample:
                     try:
                        df_mean = df.copy()
                        df_mean['time'] = pd.to_datetime(df_mean['time'])
                        df_mean = df_mean.set_index('time')
                        df_mean = df_mean.resample(resample).mean().dropna().reset_index()
                        
                        mean_list = []
                        for _, row in df_mean.iterrows():
                            mean_list.append({
                                "time": row['time'].isoformat(),
                                "value": row['value']
                            })
                        result[f"{ts.variable}_mean"] = mean_list
                     except Exception as e:
                        print(f"Resampling error for {ts.variable}: {e}")
            except Exception as e:
                print(f"Error reading TS {ts.id}: {e}")
                continue
                
        return result
