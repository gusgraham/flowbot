"""
Dry Day Analysis Service

Provides functionality for:
- Importing full-period observed data (flow, depth, velocity, rainfall)
- Detecting dry days based on rainfall criteria
- Computing 24-hour flow statistics with SG filter smoothing
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from sqlmodel import Session, select, delete
import pandas as pd
import numpy as np
from pathlib import Path
import io

from domain.verification_models import (
    VerificationFullPeriodImport, VerificationFullPeriodImportCreate,
    VerificationFullPeriodMonitor,
    VerificationDryDay, VerificationDryDayUpdate,
    VerificationTimeSeries,
    VerificationFlowMonitor,
    VerificationDWFProfile
)
from services.peak_detector import PeakDetector


class DryDayService:
    """
    Service for dry day analysis in the verification module.
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.peak_detector = PeakDetector()
    
    def get_full_period_imports(self, project_id: int) -> List[VerificationFullPeriodImport]:
        """List all full-period imports for a project."""
        stmt = select(VerificationFullPeriodImport).where(
            VerificationFullPeriodImport.project_id == project_id
        ).order_by(VerificationFullPeriodImport.imported_at.desc())
        return list(self.session.exec(stmt).all())
    
    def get_full_period_import(self, import_id: int) -> Optional[VerificationFullPeriodImport]:
        """Get a specific full-period import."""
        return self.session.get(VerificationFullPeriodImport, import_id)
    
    def preview_full_period_import(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Preview a full-period import CSV to detect available columns.
        Returns summary of detected columns, date range, and sample data.
        
        Supports two formats:
        1. ICM Trace format (starts with "Page title is")
        2. Standard CSV with timestamp/flow/rainfall columns
        """
        try:
            content_str = file_content.decode('utf-8-sig')
            
            # Check if this is an ICM trace file
            if content_str.strip().startswith('Page title is'):
                return self._preview_icm_trace(file_content, filename)
            
            # Standard CSV parsing
            df = pd.read_csv(io.BytesIO(file_content))
            
            if df.empty:
                return {"error": "CSV file is empty"}
            
            # Detect timestamp column (case-insensitive, flexible matching)
            timestamp_col = None
            timestamp_keywords = ['timestamp', 'time', 'datetime', 'date']
            
            for col in df.columns:
                col_lower = col.lower().strip()
                # First try exact matches
                if col_lower in timestamp_keywords:
                    timestamp_col = col
                    break
            
            # If not found, try partial matches
            if not timestamp_col:
                for col in df.columns:
                    col_lower = col.lower().strip()
                    for keyword in timestamp_keywords:
                        if keyword in col_lower:
                            timestamp_col = col
                            break
                    if timestamp_col:
                        break
            
            if not timestamp_col:
                # Return error with all column names for debugging
                return {
                    "error": f"No timestamp column found. Available columns: {list(df.columns)}. Expected column name containing 'timestamp', 'time', 'datetime', or 'date'."
                }
            
            # Parse timestamps with flexible format detection
            try:
                df[timestamp_col] = pd.to_datetime(df[timestamp_col], dayfirst=True)
            except Exception as e:
                return {"error": f"Could not parse timestamps in column '{timestamp_col}': {str(e)}"}
            
            # Detect data columns (case-insensitive matching)
            columns_found = {
                'timestamp': timestamp_col,
                'flow': None,
                'depth': None,
                'velocity': None,
                'rainfall': None
            }
            
            for col in df.columns:
                col_lower = col.lower().strip()
                if ('flow' in col_lower or 'q' == col_lower) and not columns_found['flow']:
                    columns_found['flow'] = col
                elif 'depth' in col_lower and not columns_found['depth']:
                    columns_found['depth'] = col
                elif ('velocity' in col_lower or 'vel' in col_lower) and not columns_found['velocity']:
                    columns_found['velocity'] = col
                elif ('rain' in col_lower or 'precip' in col_lower) and not columns_found['rainfall']:
                    columns_found['rainfall'] = col
            
            # Calculate timestep
            if len(df) > 1:
                time_diff = (df[timestamp_col].iloc[1] - df[timestamp_col].iloc[0]).total_seconds() / 60
                timestep_minutes = int(round(time_diff))
            else:
                timestep_minutes = 5
            
            return {
                "filename": filename,
                "row_count": len(df),
                "columns_found": columns_found,
                "all_columns": list(df.columns),
                "start_time": df[timestamp_col].min().isoformat(),
                "end_time": df[timestamp_col].max().isoformat(),
                "timestep_minutes": timestep_minutes,
                "has_flow": columns_found['flow'] is not None,
                "has_depth": columns_found['depth'] is not None,
                "has_velocity": columns_found['velocity'] is not None,
                "has_rainfall": columns_found['rainfall'] is not None,
                "format": "csv"
            }
            
        except Exception as e:
            import traceback
            return {"error": f"Error reading CSV: {str(e)}\n{traceback.format_exc()}"}
    
    def _preview_icm_trace(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Preview an ICM full-period trace file.
        
        ICM trace files have a specific format:
        - Line 1: Page title (e.g., 'Page title is, "Flow Survey Location..."')
        - Line 2: Header row with columns (Date, Time, Data columns...)
        - Lines 3+: Data rows
        
        Key insight: Each data column group may have its own Date/Time columns.
        For example:
        - Date, Time, Rainfall (one timebase)
        - Date, Time, Obs Velocity, Obs Flow, Obs Depth (another timebase)
        - Date, Time, Pred Velocity, Pred Flow, Pred Depth (third timebase)
        """
        try:
            lines = file_content.decode('utf-8-sig').strip().split('\n')
            
            if len(lines) < 3:
                return {"error": "File too short - needs page title, header, and data"}
            
            # Parse header row (second line)
            header_line = lines[1].strip()
            
            # Parse headers handling quoted values
            headers = self._parse_csv_header(header_line)
            
            # Identify column groups (Date/Time pairs and their associated data columns)
            column_groups = self._identify_column_groups(headers)
            
            # Parse a sample of data to get info
            sample_data = []
            for line in lines[2:min(102, len(lines))]:  # Sample first 100 data rows
                if line.strip() and not line.strip().startswith('Page title'):
                    row = self._parse_csv_row(line.strip())
                    if row:
                        sample_data.append(row)
            
            if not sample_data:
                return {"error": "No data rows found in file"}
            
            # Determine what columns are available
            has_flow = any('flow' in h.lower() and 'observed' in h.lower() for h in headers)
            has_depth = any('depth' in h.lower() and 'observed' in h.lower() for h in headers)
            has_velocity = any('velocity' in h.lower() and 'observed' in h.lower() for h in headers)
            has_rainfall = any('rain' in h.lower() for h in headers)
            
            # Parse timestamps from first group to get date range
            first_group = column_groups[0] if column_groups else None
            min_time = None
            max_time = None
            timestep_minutes = 2
            
            if first_group:
                date_col = first_group['date_col']
                time_col = first_group['time_col']
                
                for row in sample_data:
                    if len(row) > max(date_col, time_col):
                        try:
                            dt = pd.to_datetime(f"{row[date_col]} {row[time_col]}", dayfirst=True)
                            if min_time is None or dt < min_time:
                                min_time = dt
                            if max_time is None or dt > max_time:
                                max_time = dt
                        except:
                            pass
                
                # Calculate timestep from first two rows
                if len(sample_data) >= 2 and min_time and max_time:
                    try:
                        dt1 = pd.to_datetime(f"{sample_data[0][date_col]} {sample_data[0][time_col]}", dayfirst=True)
                        dt2 = pd.to_datetime(f"{sample_data[1][date_col]} {sample_data[1][time_col]}", dayfirst=True)
                        timestep_minutes = int((dt2 - dt1).total_seconds() / 60)
                    except:
                        timestep_minutes = 2
            
            return {
                "filename": filename,
                "row_count": len(lines) - 2,  # Exclude page title and header
                "column_groups": len(column_groups),
                "columns_found": {
                    "timestamp": "Date + Time",
                    "flow": "Observed Flow" if has_flow else None,
                    "depth": "Observed Depth" if has_depth else None,
                    "velocity": "Observed Velocity" if has_velocity else None,
                    "rainfall": "Observed Rainfall" if has_rainfall else None
                },
                "all_columns": headers,
                "start_time": min_time.isoformat() if min_time else None,
                "end_time": max_time.isoformat() if max_time else None,
                "timestep_minutes": timestep_minutes,
                "has_flow": has_flow,
                "has_depth": has_depth,
                "has_velocity": has_velocity,
                "has_rainfall": has_rainfall,
                "format": "icm_trace"
            }
            
        except Exception as e:
            import traceback
            return {"error": f"Error parsing ICM trace: {str(e)}\n{traceback.format_exc()}"}
    
    def _parse_csv_header(self, header_line: str) -> List[str]:
        """Parse CSV header, handling quoted values with commas."""
        import csv
        reader = csv.reader([header_line])
        return list(next(reader))
    
    def _parse_csv_row(self, row_line: str) -> List[str]:
        """Parse a CSV data row."""
        import csv
        try:
            reader = csv.reader([row_line])
            return list(next(reader))
        except:
            return row_line.split(',')
    
    def _identify_column_groups(self, headers: List[str]) -> List[Dict]:
        """
        Identify Date/Time column pairs and which data columns they apply to.
        
        Each Date/Time pair applies to subsequent columns until the next Date/Time pair.
        """
        groups = []
        current_group = None
        
        for i, header in enumerate(headers):
            header_lower = header.lower().strip()
            
            if header_lower == 'date':
                # Start new group - look for Time in next column
                if i + 1 < len(headers) and headers[i + 1].lower().strip() == 'time':
                    if current_group and current_group['data_cols']:
                        groups.append(current_group)
                    current_group = {
                        'date_col': i,
                        'time_col': i + 1,
                        'data_cols': []
                    }
            elif header_lower == 'time':
                # Skip - already handled with Date
                continue
            elif current_group is not None:
                # This is a data column for the current group
                current_group['data_cols'].append({
                    'index': i,
                    'name': header,
                    'type': self._classify_column(header)
                })
        
        # Add final group if it has data columns
        if current_group and current_group['data_cols']:
            groups.append(current_group)
        
        return groups
    
    def _classify_column(self, header: str) -> str:
        """Classify a column as flow, depth, velocity, rainfall, or unknown."""
        header_lower = header.lower()
        
        if 'rain' in header_lower:
            return 'rainfall'
        elif 'flow' in header_lower:
            if 'observed' in header_lower:
                return 'obs_flow'
            else:
                return 'pred_flow'
        elif 'depth' in header_lower:
            if 'observed' in header_lower:
                return 'obs_depth'
            else:
                return 'pred_depth'
        elif 'velocity' in header_lower:
            if 'observed' in header_lower:
                return 'obs_velocity'
            else:
                return 'pred_velocity'
        return 'unknown'
    
    def import_full_period_data(
        self,
        project_id: int,
        file_content: bytes,
        filename: str,
        name: str,
        column_mapping: Optional[Dict[str, str]] = None,
        day_rainfall_threshold_mm: float = 0.0,
        antecedent_threshold_mm: float = 1.0
    ) -> VerificationFullPeriodImport:
        """
        Import full-period data from CSV and store as parquet time series.
        
        Supports two formats:
        1. ICM Trace format (starts with "Page title is")
        2. Standard CSV with timestamp/flow/rainfall columns
        """
        content_str = file_content.decode('utf-8-sig')
        
        # Check if this is an ICM trace file
        if content_str.strip().startswith('Page title is'):
            return self._import_icm_trace(
                project_id, file_content, filename, name,
                day_rainfall_threshold_mm, antecedent_threshold_mm
            )
        
        # Standard CSV import
        return self._import_standard_csv(
            project_id, file_content, filename, name, column_mapping,
            day_rainfall_threshold_mm, antecedent_threshold_mm
        )
    
    def _import_icm_trace(
        self,
        project_id: int,
        file_content: bytes,
        filename: str,
        name: str,
        day_rainfall_threshold_mm: float,
        antecedent_threshold_mm: float
    ) -> VerificationFullPeriodImport:
        """
        Import ICM trace format file with per-monitor data.
        
        Uses ICMTraceParser which handles:
        - Multi-page format (each page = one monitor)
        - Different timebases for different columns (rainfall vs flow/depth/velocity)
        
        Creates:
        - One VerificationFullPeriodImport record
        - One VerificationFullPeriodMonitor record per parsed monitor
        - Parquet files per monitor with project subfolder structure
        """
        import tempfile
        from services.trace_parser import ICMTraceParser
        
        # Write to temp file for parser
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as f:
            f.write(file_content)
            temp_path = f.name
        
        try:
            parser = ICMTraceParser()
            result = parser.parse_file(temp_path)
            
            if result.errors:
                raise ValueError(f"ICM trace parse error: {'; '.join(result.errors)}")
            
            if not result.monitors:
                raise ValueError("No monitor data found in ICM trace file")
            
            # Determine overall time range and flags from all monitors
            min_time = None
            max_time = None
            has_flow = False
            has_depth = False
            has_velocity = False
            has_rainfall = False
            timestep_minutes = 2
            
            for monitor in result.monitors:
                if monitor.dates:
                    m_min = min(monitor.dates)
                    m_max = max(monitor.dates)
                    if min_time is None or m_min < min_time:
                        min_time = m_min
                    if max_time is None or m_max > max_time:
                        max_time = m_max
                    timestep_minutes = monitor.timestep_minutes
                
                if monitor.obs_flow:
                    has_flow = True
                if monitor.obs_depth:
                    has_depth = True
                if monitor.obs_velocity:
                    has_velocity = True
                if monitor.rainfall:
                    has_rainfall = True
            
            if min_time is None:
                raise ValueError("No date data found in ICM trace")
            
            # Create import record
            import_record = VerificationFullPeriodImport(
                project_id=project_id,
                name=name,
                source_file=filename,
                start_time=min_time,
                end_time=max_time,
                has_flow=has_flow,
                has_depth=has_depth,
                has_velocity=has_velocity,
                has_rainfall=has_rainfall,
                timestep_minutes=timestep_minutes,
                day_rainfall_threshold_mm=day_rainfall_threshold_mm,
                antecedent_threshold_mm=antecedent_threshold_mm
            )
            self.session.add(import_record)
            self.session.commit()
            self.session.refresh(import_record)
            
            # Create parquet storage directory (project subfolder structure)
            data_dir = Path(f"data/verification/project_{project_id}/fullperiod_{import_record.id}")
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Process each monitor
            for parsed_monitor in result.monitors:
                # Find or create the VerificationFlowMonitor
                existing_monitor = self.session.exec(
                    select(VerificationFlowMonitor).where(
                        VerificationFlowMonitor.project_id == project_id,
                        VerificationFlowMonitor.name == parsed_monitor.obs_location_name
                    )
                ).first()
                
                if existing_monitor:
                    monitor = existing_monitor
                else:
                    # Create new monitor if it doesn't exist
                    monitor = VerificationFlowMonitor(
                        project_id=project_id,
                        name=parsed_monitor.obs_location_name,
                        icm_node_reference=parsed_monitor.pred_location_name,
                        is_critical=False,
                        is_surcharged=False
                    )
                    self.session.add(monitor)
                    self.session.commit()
                    self.session.refresh(monitor)
                
                # Create VerificationFullPeriodMonitor record
                fp_monitor = VerificationFullPeriodMonitor(
                    import_id=import_record.id,
                    monitor_id=monitor.id
                )
                
                # Save parquet files for each data type
                n = len(parsed_monitor.dates) if parsed_monitor.dates else 0
                
                if parsed_monitor.obs_flow and n > 0:
                    flow_df = pd.DataFrame({
                        'time': parsed_monitor.dates[:n],
                        'value': parsed_monitor.obs_flow[:n]
                    })
                    flow_path = data_dir / f"monitor_{monitor.id}_flow.parquet"
                    flow_df.to_parquet(str(flow_path), index=False)
                    fp_monitor.flow_parquet_path = str(flow_path)
                
                if parsed_monitor.obs_depth and n > 0:
                    depth_df = pd.DataFrame({
                        'time': parsed_monitor.dates[:n],
                        'value': parsed_monitor.obs_depth[:n]
                    })
                    depth_path = data_dir / f"monitor_{monitor.id}_depth.parquet"
                    depth_df.to_parquet(str(depth_path), index=False)
                    fp_monitor.depth_parquet_path = str(depth_path)
                
                if parsed_monitor.obs_velocity and n > 0:
                    velocity_df = pd.DataFrame({
                        'time': parsed_monitor.dates[:n],
                        'value': parsed_monitor.obs_velocity[:n]
                    })
                    velocity_path = data_dir / f"monitor_{monitor.id}_velocity.parquet"
                    velocity_df.to_parquet(str(velocity_path), index=False)
                    fp_monitor.velocity_parquet_path = str(velocity_path)
                
                if parsed_monitor.rainfall and n > 0:
                    rainfall_df = pd.DataFrame({
                        'time': parsed_monitor.dates[:n],
                        'value': parsed_monitor.rainfall[:n]
                    })
                    rainfall_path = data_dir / f"monitor_{monitor.id}_rainfall.parquet"
                    rainfall_df.to_parquet(str(rainfall_path), index=False)
                    fp_monitor.rainfall_parquet_path = str(rainfall_path)
                
                self.session.add(fp_monitor)
                print(f"[IMPORT DEBUG] Created FP monitor record for {parsed_monitor.obs_location_name}")
            
            self.session.commit()
            self.session.refresh(import_record)
            
            return import_record
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def _import_standard_csv(
        self,
        project_id: int,
        file_content: bytes,
        filename: str,
        name: str,
        column_mapping: Optional[Dict[str, str]],
        day_rainfall_threshold_mm: float,
        antecedent_threshold_mm: float
    ) -> VerificationFullPeriodImport:
        """Import standard CSV format file."""
        df = pd.read_csv(io.BytesIO(file_content))
        
        # Detect timestamp column
        timestamp_col = None
        for col in df.columns:
            if col.lower() in ['timestamp', 'time', 'datetime', 'date']:
                timestamp_col = col
                break
        
        if not timestamp_col:
            raise ValueError("No timestamp column found")
        
        df[timestamp_col] = pd.to_datetime(df[timestamp_col], dayfirst=True)
        df = df.sort_values(timestamp_col)
        
        # Use provided mapping or auto-detect
        if column_mapping is None:
            column_mapping = {}
            for col in df.columns:
                col_lower = col.lower()
                if 'flow' in col_lower and 'flow' not in column_mapping:
                    column_mapping['flow'] = col
                elif 'depth' in col_lower and 'depth' not in column_mapping:
                    column_mapping['depth'] = col
                elif ('velocity' in col_lower or 'vel' in col_lower) and 'velocity' not in column_mapping:
                    column_mapping['velocity'] = col
                elif 'rain' in col_lower and 'rainfall' not in column_mapping:
                    column_mapping['rainfall'] = col
        
        # Calculate timestep
        if len(df) > 1:
            time_diff = (df[timestamp_col].iloc[1] - df[timestamp_col].iloc[0]).total_seconds() / 60
            timestep_minutes = int(round(time_diff))
        else:
            timestep_minutes = 5
        
        # Create import record
        import_record = VerificationFullPeriodImport(
            project_id=project_id,
            name=name,
            source_file=filename,
            start_time=df[timestamp_col].min(),
            end_time=df[timestamp_col].max(),
            has_flow='flow' in column_mapping,
            has_depth='depth' in column_mapping,
            has_velocity='velocity' in column_mapping,
            has_rainfall='rainfall' in column_mapping,
            timestep_minutes=timestep_minutes,
            day_rainfall_threshold_mm=day_rainfall_threshold_mm,
            antecedent_threshold_mm=antecedent_threshold_mm
        )
        self.session.add(import_record)
        self.session.commit()
        self.session.refresh(import_record)
        
        # Create parquet storage directory
        data_dir = Path("data/verification/dryday")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Save each series as parquet
        for series_type, col_name in column_mapping.items():
            if col_name and col_name in df.columns:
                series_df = df[[timestamp_col, col_name]].copy()
                series_df.columns = ['time', 'value']
                series_df = series_df.dropna(subset=['value'])
                
                # Save parquet
                parquet_path = data_dir / f"import_{import_record.id}_{series_type}.parquet"
                series_df.to_parquet(str(parquet_path), index=False)
        
        self.session.commit()
        self.session.refresh(import_record)
        
        return import_record
    
    def detect_dry_days(
        self,
        import_id: int,
        day_threshold_mm: Optional[float] = None,
        antecedent_threshold_mm: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Detect dry days based on rainfall criteria for each monitor.
        
        A dry day is any calendar day where:
        - Day rainfall <= day_threshold_mm (default 0mm)
        - Previous calendar day rainfall < antecedent_threshold_mm (default 1mm)
        
        Creates VerificationDryDay records per monitor (each monitor has own rainfall data).
        
        Args:
            import_id: Full period import ID
            day_threshold_mm: Override for day rainfall threshold
            antecedent_threshold_mm: Override for antecedent threshold
        
        Returns:
            Dict with summary of detected dry days per monitor
        """
        import_record = self.get_full_period_import(import_id)
        if not import_record:
            raise ValueError(f"Import {import_id} not found")
        
        # Use provided thresholds or fall back to import defaults
        day_threshold = day_threshold_mm if day_threshold_mm is not None else import_record.day_rainfall_threshold_mm
        antecedent_threshold = antecedent_threshold_mm if antecedent_threshold_mm is not None else import_record.antecedent_threshold_mm
        
        # Update thresholds on import record if changed
        if day_threshold != import_record.day_rainfall_threshold_mm or antecedent_threshold != import_record.antecedent_threshold_mm:
            import_record.day_rainfall_threshold_mm = day_threshold
            import_record.antecedent_threshold_mm = antecedent_threshold
            self.session.add(import_record)
        
        # Get all full-period monitors for this import
        fp_monitors = self.session.exec(
            select(VerificationFullPeriodMonitor).where(
                VerificationFullPeriodMonitor.import_id == import_id
            )
        ).all()
        
        if not fp_monitors:
            raise ValueError("No monitors found for this import")
        
        results = {"monitors": [], "total_dry_days": 0}
        
        for fp_monitor in fp_monitors:
            # Get the monitor name for logging
            monitor = self.session.get(VerificationFlowMonitor, fp_monitor.monitor_id)
            monitor_name = monitor.name if monitor else f"Monitor {fp_monitor.monitor_id}"
            
            # Check if rainfall data exists
            if not fp_monitor.rainfall_parquet_path or not Path(fp_monitor.rainfall_parquet_path).exists():
                print(f"[DRY DAY DEBUG] No rainfall data for {monitor_name}")
                results["monitors"].append({
                    "monitor_id": fp_monitor.monitor_id,
                    "monitor_name": monitor_name,
                    "dry_days_count": 0,
                    "error": "No rainfall data"
                })
                continue
            
            # Load rainfall data
            rain_df = pd.read_parquet(fp_monitor.rainfall_parquet_path)
            rain_df['time'] = pd.to_datetime(rain_df['time'])
            rain_df['date'] = rain_df['time'].dt.date
            
            # Aggregate to daily totals
            daily_rain = rain_df.groupby('date')['value'].sum().reset_index()
            daily_rain.columns = ['date', 'total_mm']
            daily_rain = daily_rain.sort_values('date')
            
            # Calculate previous day's rainfall
            daily_rain['prev_day_mm'] = daily_rain['total_mm'].shift(1).fillna(0)
            
            print(f"[DRY DAY DEBUG] {monitor_name}: {len(daily_rain)} days, zero rain days: {(daily_rain['total_mm'] == 0).sum()}")
            
            # Find dry days
            dry_mask = (daily_rain['total_mm'] <= day_threshold) & (daily_rain['prev_day_mm'] < antecedent_threshold)
            dry_day_rows = daily_rain[dry_mask]
            
            # Clear existing dry days for this fp_monitor
            existing = self.session.exec(
                select(VerificationDryDay).where(VerificationDryDay.fp_monitor_id == fp_monitor.id)
            ).all()
            for dd in existing:
                self.session.delete(dd)
            
            # Create new dry day records
            dry_days_created = 0
            for _, row in dry_day_rows.iterrows():
                dd = VerificationDryDay(
                    fp_monitor_id=fp_monitor.id,
                    date=datetime.combine(row['date'], datetime.min.time()),
                    day_rainfall_mm=float(row['total_mm']),
                    antecedent_rainfall_mm=float(row['prev_day_mm']),
                    is_included=True
                )
                self.session.add(dd)
                dry_days_created += 1
            
            results["monitors"].append({
                "monitor_id": fp_monitor.monitor_id,
                "monitor_name": monitor_name,
                "dry_days_count": dry_days_created
            })
            results["total_dry_days"] += dry_days_created
            print(f"[DRY DAY DEBUG] {monitor_name}: Created {dry_days_created} dry day records")
        
        self.session.commit()
        
        return results
    
    def get_fp_monitors(self, import_id: int) -> List[Dict[str, Any]]:
        """Get all full-period monitors for an import with their monitor names."""
        fp_monitors = self.session.exec(
            select(VerificationFullPeriodMonitor).where(
                VerificationFullPeriodMonitor.import_id == import_id
            )
        ).all()
        
        result = []
        for fpm in fp_monitors:
            monitor = self.session.get(VerificationFlowMonitor, fpm.monitor_id)
            result.append({
                "id": fpm.id,
                "import_id": fpm.import_id,
                "monitor_id": fpm.monitor_id,
                "monitor_name": monitor.name if monitor else None,
                "has_flow": fpm.flow_parquet_path is not None,
                "has_depth": fpm.depth_parquet_path is not None,
                "has_velocity": fpm.velocity_parquet_path is not None,
                "has_rainfall": fpm.rainfall_parquet_path is not None
            })
        return result
    
    def get_dry_days(self, fp_monitor_id: int) -> List[VerificationDryDay]:
        """Get all dry days for a specific full-period monitor."""
        stmt = select(VerificationDryDay).where(
            VerificationDryDay.fp_monitor_id == fp_monitor_id
        ).order_by(VerificationDryDay.date)
        return list(self.session.exec(stmt).all())
    
    def get_dry_days_for_import(self, import_id: int) -> Dict[int, List[VerificationDryDay]]:
        """Get all dry days for all monitors in an import, grouped by fp_monitor_id."""
        fp_monitors = self.session.exec(
            select(VerificationFullPeriodMonitor).where(
                VerificationFullPeriodMonitor.import_id == import_id
            )
        ).all()
        
        result = {}
        for fpm in fp_monitors:
            result[fpm.id] = self.get_dry_days(fpm.id)
        return result
    
    def update_dry_day(self, dry_day_id: int, update: VerificationDryDayUpdate) -> VerificationDryDay:
        """Update a dry day (typically to toggle is_included)."""
        dd = self.session.get(VerificationDryDay, dry_day_id)
        if not dd:
            raise ValueError(f"Dry day {dry_day_id} not found")
        
        if update.is_included is not None:
            dd.is_included = update.is_included
        if update.notes is not None:
            dd.notes = update.notes
        
        self.session.add(dd)
        self.session.commit()
        self.session.refresh(dd)
        return dd
    
    def get_monitor_dry_day_chart(
        self,
        fp_monitor_id: int,
        series_type: str = 'flow', # flow, depth, velocity
        day_filter: str = 'all', # all, weekday, weekend
        smoothing_frac: float = 0.0
    ) -> Dict[str, Any]:
        """
        Get 24-hour chart data for a specific monitor and series type.
        
        Returns data aligned to a common 00:00-24:00 axis with:
        - Individual day traces (for detected dry days)
        - Min/Max/Mean envelopes
        
        Args:
            fp_monitor_id: Full Period Monitor ID
            series_type: 'flow', 'depth', or 'velocity'
            smoothing_frac: SG filter smoothing fraction (0-1)
        
        Returns:
            Dictionary with chart data
        """
        # Get FP Monitor
        fp_monitor = self.session.get(VerificationFullPeriodMonitor, fp_monitor_id)
        if not fp_monitor:
            raise ValueError(f"Monitor {fp_monitor_id} not found")
        
        # Determine parquet path based on series type
        parquet_path = None
        if series_type == 'flow':
            parquet_path = fp_monitor.flow_parquet_path
        elif series_type == 'depth':
            parquet_path = fp_monitor.depth_parquet_path
        elif series_type == 'velocity':
            parquet_path = fp_monitor.velocity_parquet_path
            
        if not parquet_path or not Path(parquet_path).exists():
            return {
                "message": f"No {series_type} data for this monitor",
                "day_traces": [],
                "envelope": {"minutes": [], "min": [], "max": [], "mean": []}
            }
        
        # Load time series data
        df = pd.read_parquet(str(parquet_path))
        df['time'] = pd.to_datetime(df['time'])
        df['date'] = df['time'].dt.date
        
        # Get included dry days for this monitor
        dry_days = self.session.exec(
            select(VerificationDryDay).where(
                VerificationDryDay.fp_monitor_id == fp_monitor_id,
                VerificationDryDay.is_included == True
            )
        ).all()
        
        if not dry_days:
            return {
                "message": "No included dry days",
                "day_traces": [],
                "envelope": {"minutes": [], "min": [], "max": [], "mean": []}
            }
        
        dry_day_dates = set(dd.date.date() for dd in dry_days)
        
        # Apply Day Filter
        if day_filter == "weekday":
            # Monday(0) to Friday(4)
            dry_day_dates = {d for d in dry_day_dates if d.weekday() < 5}
        elif day_filter == "weekend":
            # Saturday(5), Sunday(6)
            dry_day_dates = {d for d in dry_day_dates if d.weekday() >= 5}
        
        if not dry_day_dates:
             return {
                "message": f"No included dry days for filter {day_filter}",
                "day_traces": [],
                "envelope": {"minutes": [], "min": [], "max": [], "mean": []}
            }
        
        # Filter to dry days only
        dry_df = df[df['date'].isin(dry_day_dates)].copy()
        
        # Calculate minutes since midnight for each timestamp
        dry_df['minutes'] = (
            dry_df['time'].dt.hour * 60 + 
            dry_df['time'].dt.minute +
            dry_df['time'].dt.second / 60
        )
        
        # Round to timestep (get from import record)
        import_record = fp_monitor.full_period_import
        timestep = import_record.timestep_minutes if import_record else 2
        
        dry_df['minutes_rounded'] = (dry_df['minutes'] / timestep).round() * timestep
        dry_df['minutes_rounded'] = dry_df['minutes_rounded'].clip(0, 24 * 60 - timestep)
        
        # Build individual day traces
        day_traces = []
        for day_date in sorted(dry_day_dates):
            day_data = dry_df[dry_df['date'] == day_date].sort_values('minutes_rounded')
            if not day_data.empty:
                day_traces.append({
                    "date": str(day_date),
                    "values": [
                        {"minutes": int(row['minutes_rounded']), "value": float(row['value'])}
                        for _, row in day_data.iterrows()
                    ]
                })
        
        # Compute envelope (min/max/mean) per minute bin
        envelope_df = dry_df.groupby('minutes_rounded')['value'].agg(['min', 'max', 'mean']).reset_index()
        envelope_df = envelope_df.sort_values('minutes_rounded')
        
        minutes_arr = envelope_df['minutes_rounded'].values
        min_arr = envelope_df['min'].values
        max_arr = envelope_df['max'].values
        mean_arr = envelope_df['mean'].values
        
        # Apply smoothing if requested
        if smoothing_frac > 0:
            min_arr = self.peak_detector.smooth_series(min_arr.tolist(), smoothing_frac)
            max_arr = self.peak_detector.smooth_series(max_arr.tolist(), smoothing_frac)
            mean_arr = self.peak_detector.smooth_series(mean_arr.tolist(), smoothing_frac)
        
        return {
            "fp_monitor_id": fp_monitor_id,
            "series_type": series_type,
            "dry_day_count": len(dry_day_dates),
            "smoothing_frac": smoothing_frac,
            "day_traces": day_traces,
            "envelope": {
                "minutes": [int(m) for m in minutes_arr],
                "min": [float(v) for v in min_arr],
                "max": [float(v) for v in max_arr],
                "mean": [float(v) for v in mean_arr]
            }
        }
    
    def delete_full_period_import(self, import_id: int) -> bool:
        """Delete a full-period import and all associated data."""
        import_record = self.get_full_period_import(import_id)
        if not import_record:
            return False
        
        # Find all FP monitors
        fp_monitors = self.session.exec(
            select(VerificationFullPeriodMonitor).where(
                VerificationFullPeriodMonitor.import_id == import_id
            )
        ).all()
        
        monitor_ids = [m.id for m in fp_monitors]
        
        if monitor_ids:
            # Delete dry days
            from sqlalchemy import text
            self.session.exec(
                text(f"DELETE FROM ver_dryday WHERE fp_monitor_id IN ({','.join(map(str, monitor_ids))})")
            )
            
            # Delete FP monitors
            self.session.exec(
                text(f"DELETE FROM ver_fullperiodmonitor WHERE import_id = :iid"),
                params={"iid": import_id}
            )
            
        # Delete parquet folder
        import shutil
        project_id = import_record.project_id
        import_dir = Path(f"data/verification/project_{project_id}/fullperiod_{import_id}")
        if import_dir.exists():
            try:
                shutil.rmtree(import_dir)
            except Exception as e:
                print(f"[DELETE ERROR] Failed to delete {import_dir}: {e}")
        
        # Delete import record
        self.session.delete(import_record)
        self.session.commit()
        return True

    def save_dwf_profiles(self, fp_monitor_id: int) -> int:
        """
        Calculate and persist DWF profiles (All, Weekday, Weekend) for Flow, Depth, and Velocity.
        Returns the number of profiles created.
        """
        # Delete existing profiles for this monitor
        self.session.exec(delete(VerificationDWFProfile).where(VerificationDWFProfile.fp_monitor_id == fp_monitor_id))
        
        profiles_to_create = []
        monitor = self.session.get(VerificationFullPeriodMonitor, fp_monitor_id)
        if not monitor:
            return 0
            
        series_types = []
        if monitor.has_flow: series_types.append("flow")
        if monitor.has_depth: series_types.append("depth")
        if monitor.has_velocity: series_types.append("velocity")
        
        filters = ["all", "weekday", "weekend"]
        
        for s_type in series_types:
            for d_filter in filters:
                # Calculate chart data internally (no smoothing for storage usually, or minimal default?)
                # We store raw statistics usually, but if user applied smoothing in UI, we don't capture that here 
                # unless we passed it. For benchmarks, raw or standard smoothing is best. using 0.0 here.
                chart_data = self.get_monitor_dry_day_chart(fp_monitor_id, series_type=s_type, day_filter=d_filter, smoothing_frac=0.0)
                
                envelope = chart_data.get("envelope", {})
                if not envelope or not envelope.get("minutes"):
                    continue
                    
                # Store only the envelope arrays
                profile_data = {
                    "minutes": envelope["minutes"],
                    "min": envelope["min"],
                    "max": envelope["max"],
                    "mean": envelope["mean"],
                    "count": chart_data.get("dry_day_count", 0)
                }
                
                profiles_to_create.append(VerificationDWFProfile(
                    fp_monitor_id=fp_monitor_id,
                    profile_type=d_filter,
                    series_type=s_type,
                    data=profile_data
                ))
        
        self.session.add_all(profiles_to_create)
        self.session.commit()
        return len(profiles_to_create)
        
        return True
