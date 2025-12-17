"""
ICM Trace Parser Service

Parses ICM CSV exports containing observed vs predicted time series data
for hydraulic model verification.
"""
import os
import re
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ParsedMonitorTrace:
    """Data class representing a single monitor's trace data from an ICM export."""
    page_index: int
    page_title: str
    obs_location_name: str
    pred_location_name: str
    upstream_end: bool
    timestep_minutes: int
    dates: List[datetime]
    obs_flow: List[float]
    pred_flow: List[float]
    obs_depth: List[float]
    pred_depth: List[float]
    obs_velocity: List[float]
    pred_velocity: List[float]
    # Optional: rainfall data if present
    rainfall: Optional[List[float]] = None
    # Predicted profile name (if multiple profiles in file)
    pred_profile_name: Optional[str] = None


@dataclass
class TraceParseResult:
    """Result of parsing an ICM trace file."""
    trace_id: str  # Usually filename without extension
    source_file: str
    monitors: List[ParsedMonitorTrace]
    predicted_profiles: List[str]  # List of unique predicted profile names found
    errors: List[str]
    warnings: List[str]


class ICMTraceParser:
    """
    Parser for ICM Time Series Graph export CSV files.
    
    Expected format:
    - Line 1: Page title (e.g., 'Page title is, "Flow Survey Location (Obs.) F01, Model Location (Pred.) D/S SJ24658202.1, Rainfall Profile: 5"')
    - Line 2: Column headers
    - Lines 3+: Data rows
    - Repeated for each page/monitor in the file
    """
    
    # Regex patterns for parsing page titles
    PAGE_TITLE_PATTERN = re.compile(
        r'Page title is,\s*"Flow Survey Location\s*\(Obs\.\)\s*([^,]+),\s*'
        r'Model Location\s*\(Pred\.\)\s*(U/S|D/S)\s*([^,"]+)'
    )
    
    def __init__(self, storage_base_path: str = "data/verification"):
        self.storage_base_path = Path(storage_base_path)
        self.storage_base_path.mkdir(parents=True, exist_ok=True)
    
    def parse_file(self, file_path: str, selected_profile_index: int = 0) -> TraceParseResult:
        """
        Parse an ICM trace CSV file.
        
        Args:
            file_path: Path to the CSV file
            selected_profile_index: Which predicted profile to use if multiple exist (0-indexed)
            
        Returns:
            TraceParseResult containing all parsed monitor traces
        """
        errors = []
        warnings = []
        monitors = []
        predicted_profiles = set()
        
        file_path = Path(file_path)
        trace_id = file_path.stem
        
        try:
            # First pass: identify page breaks and predicted profiles
            pages, profiles = self._identify_pages_and_profiles(file_path)
            predicted_profiles = profiles
            
            if not pages:
                errors.append("No valid page titles found in file")
                return TraceParseResult(
                    trace_id=trace_id,
                    source_file=str(file_path),
                    monitors=[],
                    predicted_profiles=list(predicted_profiles),
                    errors=errors,
                    warnings=warnings
                )
            
            # Read the full file
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            
            # Parse each page
            for i, (page_start, page_end, page_title) in enumerate(pages):
                try:
                    monitor = self._parse_page(
                        lines[page_start:page_end],
                        page_index=i,
                        page_title=page_title,
                        selected_profile_index=selected_profile_index,
                        num_profiles=len(predicted_profiles) if predicted_profiles else 1
                    )
                    if monitor:
                        monitors.append(monitor)
                except Exception as e:
                    errors.append(f"Error parsing page {i+1} ({page_title}): {str(e)}")
                    
        except Exception as e:
            errors.append(f"Error reading file: {str(e)}")
        
        return TraceParseResult(
            trace_id=trace_id,
            source_file=str(file_path),
            monitors=monitors,
            predicted_profiles=list(predicted_profiles),
            errors=errors,
            warnings=warnings
        )
    
    def _identify_pages_and_profiles(self, file_path: Path) -> Tuple[List[Tuple[int, int, str]], set]:
        """
        First pass to identify page breaks and predicted profile names.
        
        Returns:
            Tuple of (list of (start_line, end_line, page_title), set of profile names)
        """
        pages = []
        profiles = set()
        
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        
        page_starts = []
        for i, line in enumerate(lines):
            if line.strip().startswith('Page title is'):
                page_starts.append((i, line.strip()))
        
        # Determine page boundaries
        for idx, (start, title) in enumerate(page_starts):
            if idx < len(page_starts) - 1:
                end = page_starts[idx + 1][0]
            else:
                end = len(lines)
            pages.append((start, end, title))
        
        # Extract profile names from header row (line after page title)
        if page_starts:
            header_line_idx = page_starts[0][0] + 1
            if header_line_idx < len(lines):
                header = lines[header_line_idx]
                # Look for patterns like "Predicted Flow, Event A>Event A (Flow (m3/s))"
                profile_matches = re.findall(r'Predicted (?:Flow|Depth|Velocity),\s*([^>]+)>', header)
                profiles.update(profile_matches)
        
        return pages, profiles
    
    def _parse_page(self, lines: List[str], page_index: int, page_title: str, 
                    selected_profile_index: int, num_profiles: int) -> Optional[ParsedMonitorTrace]:
        """Parse a single page from the ICM export."""
        
        # Parse page title
        obs_name, upstream_end, pred_name = self._parse_page_title(page_title)
        if not obs_name:
            return None
        
        # Find header line (line after page title)
        if len(lines) < 2:
            return None
            
        header_line = lines[1].strip()
        headers = self._parse_header(header_line)
        
        if not headers:
            return None
        
        # Parse data rows
        data_rows = []
        for line in lines[2:]:
            line = line.strip()
            if not line or line.startswith('Page title'):
                break
            try:
                values = line.split(',')
                if len(values) >= len(headers):
                    data_rows.append(values[:len(headers)])
            except:
                continue
        
        if not data_rows:
            return None
        
        # Create DataFrame
        df = pd.DataFrame(data_rows, columns=headers)
        
        # Identify column indices
        obs_cols = self._identify_observed_columns(headers)
        pred_cols = self._identify_predicted_columns(headers, selected_profile_index, num_profiles)
        
        # Parse dates
        dates = self._parse_dates(df, obs_cols)
        if not dates:
            return None
        
        # Calculate timestep
        if len(dates) >= 2:
            timestep_minutes = int((dates[1] - dates[0]).total_seconds() / 60)
        else:
            timestep_minutes = 2  # Default
        
        # Extract data series
        obs_flow = self._extract_series(df, obs_cols.get('flow'))
        obs_depth = self._extract_series(df, obs_cols.get('depth'))
        obs_velocity = self._extract_series(df, obs_cols.get('velocity'))
        pred_flow = self._extract_series(df, pred_cols.get('flow'))
        pred_depth = self._extract_series(df, pred_cols.get('depth'))
        pred_velocity = self._extract_series(df, pred_cols.get('velocity'))
        rainfall = self._extract_series(df, obs_cols.get('rainfall'))
        
        return ParsedMonitorTrace(
            page_index=page_index,
            page_title=page_title,
            obs_location_name=obs_name,
            pred_location_name=pred_name,
            upstream_end=upstream_end,
            timestep_minutes=timestep_minutes,
            dates=dates,
            obs_flow=obs_flow,
            pred_flow=pred_flow,
            obs_depth=obs_depth,
            pred_depth=pred_depth,
            obs_velocity=obs_velocity,
            pred_velocity=pred_velocity,
            rainfall=rainfall if rainfall else None
        )
    
    def _parse_page_title(self, title: str) -> Tuple[Optional[str], bool, Optional[str]]:
        """
        Parse the page title to extract monitor info.
        
        Returns:
            Tuple of (obs_location_name, upstream_end, pred_location_name)
        """
        match = self.PAGE_TITLE_PATTERN.search(title)
        if match:
            obs_name = match.group(1).strip()
            is_upstream = match.group(2) == 'U/S'
            pred_name = match.group(3).strip()
            return obs_name, is_upstream, pred_name
        
        # Try simple extraction if pattern doesn't match
        if 'Flow Survey Location' in title:
            try:
                # Extract obs location
                obs_match = re.search(r'\(Obs\.\)\s*([^,]+)', title)
                obs_name = obs_match.group(1).strip() if obs_match else None
                
                # Check U/S or D/S
                is_upstream = 'U/S' in title
                
                # Extract pred location
                pred_match = re.search(r'(U/S|D/S)\s*([^,"]+)', title)
                pred_name = pred_match.group(2).strip() if pred_match else None
                
                return obs_name, is_upstream, pred_name
            except:
                pass
        
        return None, False, None
    
    def _parse_header(self, header_line: str) -> List[str]:
        """Parse the header line, handling quoted fields."""
        headers = []
        current = ''
        in_quotes = False
        
        for char in header_line:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                headers.append(current.strip().strip('"'))
                current = ''
            else:
                current += char
        
        if current:
            headers.append(current.strip().strip('"'))
        
        return headers
    
    def _identify_observed_columns(self, headers: List[str]) -> Dict[str, int]:
        """
        Identify column indices for observed data.
        
        Key insight: Different data columns may have their own Date/Time pairs.
        Each Date/Time pair applies to subsequent data columns until the next Date/Time pair.
        For example:
        - Date, Time, Rainfall (timebase 1)
        - Date, Time, Obs Velocity, Obs Flow, Obs Depth (timebase 2)
        """
        cols = {}
        column_groups = self._identify_column_groups(headers)
        
        # Find which group contains each data type and store both the data column
        # and its associated date/time columns
        for group in column_groups:
            for data_col in group.get('data_cols', []):
                col_type = data_col['type']
                col_idx = data_col['index']
                
                if col_type == 'rainfall' and 'rainfall' not in cols:
                    cols['rainfall'] = col_idx
                    cols['rainfall_date'] = group['date_col']
                    cols['rainfall_time'] = group['time_col']
                elif col_type == 'obs_velocity' and 'velocity' not in cols:
                    cols['velocity'] = col_idx
                    cols['date'] = group['date_col']  # Primary date/time for FDV
                    cols['time'] = group['time_col']
                elif col_type == 'obs_flow' and 'flow' not in cols:
                    cols['flow'] = col_idx
                    if 'date' not in cols:
                        cols['date'] = group['date_col']
                        cols['time'] = group['time_col']
                elif col_type == 'obs_depth' and 'depth' not in cols:
                    cols['depth'] = col_idx
                    if 'date' not in cols:
                        cols['date'] = group['date_col']
                        cols['time'] = group['time_col']
        
        # Fallback: if no date/time found via groups, try simple detection
        if 'date' not in cols:
            for i, h in enumerate(headers):
                h_lower = h.lower().strip()
                if h_lower == 'date':
                    cols['date'] = i
                    if i + 1 < len(headers) and headers[i + 1].lower().strip() == 'time':
                        cols['time'] = i + 1
                    break
        
        return cols
    
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
                    if current_group and current_group.get('data_cols'):
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
        if current_group and current_group.get('data_cols'):
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
            elif 'predicted' in header_lower:
                return 'pred_flow'
            else:
                return 'obs_flow'  # Default to observed
        elif 'depth' in header_lower:
            if 'observed' in header_lower:
                return 'obs_depth'
            elif 'predicted' in header_lower:
                return 'pred_depth'
            else:
                return 'obs_depth'
        elif 'velocity' in header_lower:
            if 'observed' in header_lower:
                return 'obs_velocity'
            elif 'predicted' in header_lower:
                return 'pred_velocity'
            else:
                return 'obs_velocity'
        return 'unknown'
    
    def _identify_predicted_columns(self, headers: List[str], profile_index: int, num_profiles: int) -> Dict[str, int]:
        """
        Identify column indices for predicted data, handling multiple profiles.
        Uses column groups to find the correct Date/Time columns for predicted data.
        """
        cols = {}
        column_groups = self._identify_column_groups(headers)
        
        # Find predicted columns and their groups
        pred_velocity_indices = []
        pred_flow_indices = []
        pred_depth_indices = []
        pred_date_col = None
        pred_time_col = None
        
        for group in column_groups:
            for data_col in group.get('data_cols', []):
                col_type = data_col['type']
                col_idx = data_col['index']
                
                if col_type == 'pred_velocity':
                    pred_velocity_indices.append(col_idx)
                    if pred_date_col is None:
                        pred_date_col = group['date_col']
                        pred_time_col = group['time_col']
                elif col_type == 'pred_flow':
                    pred_flow_indices.append(col_idx)
                    if pred_date_col is None:
                        pred_date_col = group['date_col']
                        pred_time_col = group['time_col']
                elif col_type == 'pred_depth':
                    pred_depth_indices.append(col_idx)
                    if pred_date_col is None:
                        pred_date_col = group['date_col']
                        pred_time_col = group['time_col']
        
        # Select the appropriate profile index
        if pred_velocity_indices and profile_index < len(pred_velocity_indices):
            cols['velocity'] = pred_velocity_indices[profile_index]
        elif pred_velocity_indices:
            cols['velocity'] = pred_velocity_indices[0]
            
        if pred_flow_indices and profile_index < len(pred_flow_indices):
            cols['flow'] = pred_flow_indices[profile_index]
        elif pred_flow_indices:
            cols['flow'] = pred_flow_indices[0]
            
        if pred_depth_indices and profile_index < len(pred_depth_indices):
            cols['depth'] = pred_depth_indices[profile_index]
        elif pred_depth_indices:
            cols['depth'] = pred_depth_indices[0]
        
        # Store predicted date/time columns
        if pred_date_col is not None:
            cols['date'] = pred_date_col
            cols['time'] = pred_time_col
        
        return cols
    
    def _parse_dates(self, df: pd.DataFrame, obs_cols: Dict[str, int]) -> List[datetime]:
        """Parse date/time columns into datetime objects."""
        dates = []
        
        date_col = obs_cols.get('date')
        time_col = obs_cols.get('time')
        
        if date_col is None:
            # Try to find date column by position (usually first)
            date_col = 0
            time_col = 1
        
        col_names = df.columns.tolist()
        
        for _, row in df.iterrows():
            try:
                date_str = str(row.iloc[date_col])
                time_str = str(row.iloc[time_col]) if time_col is not None else '00:00:00'
                
                # Handle various date formats
                datetime_str = f"{date_str} {time_str}".strip()
                
                # Try common formats
                for fmt in ['%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']:
                    try:
                        dt = datetime.strptime(datetime_str, fmt)
                        dates.append(dt)
                        break
                    except ValueError:
                        continue
            except:
                continue
        
        return dates
    
    def _extract_series(self, df: pd.DataFrame, col_idx: Optional[int]) -> List[float]:
        """Extract a numeric series from the dataframe."""
        if col_idx is None:
            return []
        
        values = []
        col_name = df.columns[col_idx]
        
        for val in df[col_name]:
            try:
                values.append(float(val))
            except (ValueError, TypeError):
                values.append(0.0)
        
        return values
    
    def save_to_parquet(self, monitor: ParsedMonitorTrace, project_id: int, 
                        trace_set_id: int, monitor_id: int) -> Dict[str, str]:
        """
        Save monitor trace data to parquet files.
        
        Returns:
            Dictionary mapping series_type to parquet file path
        """
        output_dir = self.storage_base_path / f"project_{project_id}" / f"traceset_{trace_set_id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        paths = {}
        
        series_data = [
            ('obs_flow', monitor.obs_flow),
            ('pred_flow', monitor.pred_flow),
            ('obs_depth', monitor.obs_depth),
            ('pred_depth', monitor.pred_depth),
            ('obs_velocity', monitor.obs_velocity),
            ('pred_velocity', monitor.pred_velocity),
        ]
        
        for series_type, values in series_data:
            if values:
                df = pd.DataFrame({
                    'time': monitor.dates[:len(values)],
                    'value': values
                })
                
                filename = f"monitor_{monitor_id}_{series_type}.parquet"
                filepath = output_dir / filename
                df.to_parquet(filepath, index=False)
                paths[series_type] = str(filepath)
        
        return paths


# Convenience function for quick parsing
def parse_icm_trace(file_path: str, profile_index: int = 0) -> TraceParseResult:
    """Quick parse of an ICM trace file."""
    parser = ICMTraceParser()
    return parser.parse_file(file_path, profile_index)
