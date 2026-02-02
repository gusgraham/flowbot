import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, time, timedelta
from sqlmodel import Session, select, delete
import numpy as np
from scipy.signal import savgol_filter

from domain.fsa import FsaDataset, FsaTimeSeries, SurveyEvent, FsaMonitorExcludedDryDay, FsaDWFMonitorSettings

class FsaDWFService:
    def __init__(self, session: Session):
        self.session = session

    def get_sg_settings(self, dataset_id: int) -> Dict[str, Any]:
        """Get saved SG filter settings for a dataset, with defaults if not set."""
        settings = self.session.exec(
            select(FsaDWFMonitorSettings).where(FsaDWFMonitorSettings.dataset_id == dataset_id)
        ).first()
        
        if settings:
            return {
                "sg_enabled": settings.sg_enabled,
                "sg_window": settings.sg_window,
                "sg_order": settings.sg_order
            }
        else:
            return {
                "sg_enabled": False,
                "sg_window": 21,
                "sg_order": 3
            }

    def get_dry_days_status(self, dataset_id: int, project_id: int) -> List[Dict[str, Any]]:
        """
        Get all dry day events for the project, marking which are excluded for the dataset.
        Results: List of events with 'enabled' boolean.
        """
        # 1. Get all Dry Day / Dry Period events for the project
        events_stmt = select(SurveyEvent).where(
            SurveyEvent.project_id == project_id,
            (SurveyEvent.event_type == "Dry Day") | (SurveyEvent.event_type == "Dry Period")
        ).order_by(SurveyEvent.start_time)
        project_events = self.session.exec(events_stmt).all()

        # 2. Get exclusions for this dataset
        exclusion_stmt = select(FsaMonitorExcludedDryDay).where(
            FsaMonitorExcludedDryDay.dataset_id == dataset_id
        )
        exclusions = self.session.exec(exclusion_stmt).all()
        excluded_event_ids = {e.event_id for e in exclusions}

        # 3. Merge
        results = []
        for event in project_events:
            results.append({
                "id": event.id,
                "name": event.name,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "event_type": event.event_type,
                "enabled": event.id not in excluded_event_ids
            })
        
        return results

    def toggle_dry_day(self, dataset_id: int, event_id: int, enabled: bool):
        """
        Set enabled status. 
        If enabled=True, remove from exclusion table.
        If enabled=False, add to exclusion table.
        """
        stmt = select(FsaMonitorExcludedDryDay).where(
            FsaMonitorExcludedDryDay.dataset_id == dataset_id,
            FsaMonitorExcludedDryDay.event_id == event_id
        )
        existing = self.session.exec(stmt).first()

        if enabled:
            if existing:
                self.session.delete(existing)
                self.session.commit()
        else:
            if not existing:
                exclusion = FsaMonitorExcludedDryDay(dataset_id=dataset_id, event_id=event_id)
                self.session.add(exclusion)
                self.session.commit()

    def compute_dwf_analysis(self, dataset_id: int, project_id: int, candidate_event_ids: Optional[List[int]] = None, sg_enabled: bool = False, sg_window: int = 21, sg_order: int = 3) -> Dict[str, Any]:
        """
        Compute avg/min/max flow, depth, velocity profiles based on enabled dry days.
        candidate_event_ids: If provided, only consider these events as potential candidates.
                             Data for ALL candidates is returned (traces), but only ENABLED candidates contribute to the profile (avg/min/max).
        """
        # 1. Get events
        status_list = self.get_dry_days_status(dataset_id, project_id)
        
        # Filter by candidates if provided
        events_to_process = status_list
        if candidate_event_ids is not None:
            candidate_set = set(candidate_event_ids)
            events_to_process = [e for e in status_list if e['id'] in candidate_set]
            
        if not events_to_process:
             # Return empty structure if no events
            return {"profile": [], "traces": [], "stats": {}}

        # Identify enabled events for profile calculation
        enabled_event_ids = {e['id'] for e in events_to_process if e['enabled']}
        
        # 2. Get dataset data for ALL processed events (enabled or disabled) so we can show traces for excluded ones
        from sqlalchemy import or_
        
        time_filters = []
        for event in events_to_process:
            time_filters.append(
                (FsaTimeSeries.timestamp >= event['start_time']) & 
                (FsaTimeSeries.timestamp <= event['end_time'])
            )
        
        if not time_filters:
            return {"profile": [], "traces": [], "stats": {}}

        stmt = select(FsaTimeSeries).where(
            FsaTimeSeries.dataset_id == dataset_id,
            or_(*time_filters)
        ).order_by(FsaTimeSeries.timestamp)
        
        data_points = self.session.exec(stmt).all()
        
        if not data_points:
            return {"profile": [], "traces": [], "stats": {}}

        # 3. Process with Pandas
        df = pd.DataFrame([
            {
                "timestamp": dp.timestamp,
                "flow": dp.flow,
                "depth": dp.depth,
                "velocity": dp.velocity
            }
            for dp in data_points
        ])
        
        # Add TimeOfDay column (seconds since midnight)
        df['time_of_day_seconds'] = df['timestamp'].dt.hour * 3600 + \
                                    df['timestamp'].dt.minute * 60 + \
                                    df['timestamp'].dt.second
                                    
        # Prepare individual day traces (for ALL events)
        traces = []
        df['date'] = df['timestamp'].dt.date
        
        # We need to tag data points with event IDs to filter for profile calculation
        # Naive approach: check date/range again.
        # Efficient approach: we have disjoint ranges usually.
        # Let's add 'event_id' column to df? 
        # Or filter df for profile calculation 
        
        # Let's reconstruct filters for profile DF
        # It's faster to just use the timestamp ranges of ENABLED events to filter the main DF
        
        mask_enabled = pd.Series(False, index=df.index)
        
        for event in events_to_process:
            # Mask for this event
            # Ensure timestamps are localized/naive consistent. Assume consistency.
            event_mask = (df['timestamp'] >= event['start_time']) & (df['timestamp'] <= event['end_time'])
            
            # If enabled, add to global mask
            if event['id'] in enabled_event_ids:
                mask_enabled = mask_enabled | event_mask
                
            # Add trace
            # Note: Groupby date might split an event if it crosses midnight? Dry days usually don't or are 24h.
            # If event crosses midnight (e.g. 09:00 to 09:00 next day), 'date' grouping splits it.
            # DWF analysis usually aligns to "Time of Day" 0-24h.
            # The previous logic grouped by 'date'. 
            # If we want 0-24h traces defined by event start/end, we should group by 'event' not 'date'.
            # But let's stick to existing logic for now unless broken.
            # Assuming 'date' is sufficient for "Dry Day".
            
            # Wait, better logic for traces:
            # Extract data for this specific event window directly.
            event_data = df[event_mask].copy()
            


            if not event_data.empty:
                traces.append({
                    "date": event['start_time'].date().isoformat(), # Use event start date as label
                    "event_id": event['id'], # Pass ID to help frontend matching
                    "data": event_data[['time_of_day_seconds', 'flow', 'depth', 'velocity']].replace({np.nan: None}).to_dict('records')
                })

        # Calculate Profile using ONLY enabled data
        df_enabled = df[mask_enabled]
        
        if df_enabled.empty:
            profile = []
            stats = {}
        else:
            grouped = df_enabled.groupby('time_of_day_seconds').agg({
                'flow': ['mean', 'min', 'max', 'count'],
                'depth': ['mean', 'min', 'max'],
                'velocity': ['mean', 'min', 'max']
            })
            
            # Flatten columns
            grouped.columns = ['_'.join(col).strip() for col in grouped.columns.values]
            grouped = grouped.reset_index()
            grouped = grouped.sort_values('time_of_day_seconds')
            
            # Apply SG Filter to profile if enabled
            if sg_enabled and not grouped.empty:
                 w = sg_window if sg_window % 2 == 1 else sg_window + 1
                 if w > len(grouped): w = len(grouped) if len(grouped) % 2 == 1 else len(grouped) - 1
                 
                 if w > sg_order:
                     cols_to_smooth = [c for c in grouped.columns if c != 'time_of_day_seconds' and not c.endswith('_count')]
                     for col in cols_to_smooth:
                         try:
                             # Use wrap for profile (daily cycle)
                             grouped[col] = savgol_filter(grouped[col], w, sg_order, mode='wrap')
                         except Exception:
                             pass
            
            profile = grouped.replace({np.nan: None}).to_dict('records')
            
            stats = {
                "flow_avg": float(grouped['flow_mean'].mean()) if not grouped.empty else 0,
                "flow_max": float(grouped['flow_max'].max()) if not grouped.empty else 0,
                "depth_avg": float(grouped['depth_mean'].mean()) if not grouped.empty else 0,
                "depth_max": float(grouped['depth_max'].max()) if not grouped.empty else 0,
                "velocity_avg": float(grouped['velocity_mean'].mean()) if not grouped.empty else 0,
                "velocity_max": float(grouped['velocity_max'].max()) if not grouped.empty else 0,
                "total_days": len(enabled_event_ids)
            }
        
        return {
            "profile": profile, 
            "traces": traces,   
            "stats": stats
        }

    def export_infoworks(self, project_id: int, dataset_ids: List[int], start_date: datetime, variable: str = "Flow", profile_line: str = "mean", sg_enabled: bool = False, sg_window: int = 21, sg_order: int = 3) -> str:
        """
        Generate InfoWorks CSV content (HYQ/HYD/HYV).
        variable: 'Flow', 'Depth', 'Velocity'
        profile_line: 'mean', 'min', 'max'
        """
        
        # 1. Determine file type and units
        # InfoWorks types: HYQ (Flow), HYD (Depth/Level), HYV (Velocity)
        if variable == 'Flow':
            iw_type = 'HYQ'
            units = 'm3/s' 
            conversion_factor = 0.001 
        elif variable == 'Depth':
            iw_type = 'HYD'
            units = 'm'
            conversion_factor = 0.001
        elif variable == 'Velocity':
            iw_type = 'HYV'
            units = 'm/s'
            conversion_factor = 1.0
        else:
            iw_type = 'HYQ'
            units = 'm3/s'
            conversion_factor = 0.001

        # 2. Get Datasets
        stmt = select(FsaDataset).where(FsaDataset.id.in_(dataset_ids))
        datasets = self.session.exec(stmt).all()
        dataset_map = {d.id: d for d in datasets}
        
        # Sort datasets by name for column order
        sorted_dataset_ids = sorted(dataset_ids, key=lambda id: dataset_map[id].name if id in dataset_map else "")
        
        # 3. Compute profiles for each dataset (using per-monitor SG settings)
        profiles = {} # dataset_id -> list of float (length 720 for 1 day at 2min)
        
        # Determine which field to extract based on profile_line
        line_suffix = profile_line  # 'mean', 'min', or 'max'
        
        for ds_id in sorted_dataset_ids:
            # Get this monitor's saved SG settings
            monitor_sg = self.get_sg_settings(ds_id)
            
            res = self.compute_dwf_analysis(
                ds_id, project_id, 
                sg_enabled=monitor_sg["sg_enabled"], 
                sg_window=monitor_sg["sg_window"], 
                sg_order=monitor_sg["sg_order"]
            )
            if "error" in res:
                profiles[ds_id] = [0.0] * 720
            else:
                dense_profile = [0.0] * 720
                
                if 'profile' in res:
                    for entry in res['profile']:
                        sec = entry['time_of_day_seconds']
                        idx = int(round(sec / 120.0))
                        if 0 <= idx < 720:
                            field_name = f"{variable.lower()}_{line_suffix}"
                            val = entry.get(field_name, 0)
                            
                            if val is None: val = 0
                            dense_profile[idx] = float(val) * conversion_factor
                
                profiles[ds_id] = dense_profile

        # 4. Build CSV
        lines = []
        
        # Header
        lines.append(f"!Version=1,type={iw_type},encoding=MBCS")
        
        if variable == 'Depth':
             lines.append("UserSettings,U_LEVEL,U_CONDHEIGHT,U_VALUES,U_DATETIME")
             lines.append(f"UserSettingsValues,m AD,mm,{units},dd-mm-yyyy hh:mm")
        else:
             lines.append("UserSettings,U_VALUES,U_DATETIME")
             lines.append(f"UserSettingsValues,{units},dd-mm-yyyy hh:mm")
             
        # G_START
        start_str = start_date.strftime("%d/%m/%Y %H:%M:%S")
        lines.append("G_START,G_TS,G_NPROFILES")
        lines.append(f"{start_str},120,{len(sorted_dataset_ids)}")
        
        # Link IDs
        if variable == 'Depth':
            lines.append("L_LINKID,L_INVERTLEVEL,L_CONDHEIGHT,L_GROUNDLEVEL,L_PTITLE")
            for ds_id in sorted_dataset_ids:
                name = dataset_map[ds_id].name
                lines.append(f"     {name},0,    0,0,")
        elif variable == 'Velocity':
            lines.append("L_LINKID,L_PTITLE")
            for ds_id in sorted_dataset_ids:
                name = dataset_map[ds_id].name
                lines.append(f"     {name},Avg")
        else:  # Flow
            lines.append("L_LINKID,L_CONDCAPACITY,L_PTITLE")
            for ds_id in sorted_dataset_ids:
                name = dataset_map[ds_id].name
                lines.append(f"     {name},0,")

        # P_DATETIME header
        indices = ",".join([str(i+1) for i in range(len(sorted_dataset_ids))])
        lines.append(f"P_DATETIME,{indices}")
        
        # Data rows
        # Loop 0 to 719
        current_time = start_date
        one_step = timedelta(minutes=2)
        
        for i in range(720):
            row_items = []
            time_str = current_time.strftime("%d/%m/%Y %H:%M:%S")
            row_items.append(time_str)
            
            for ds_id in sorted_dataset_ids:
                val = profiles[ds_id][i]
                # Format float?
                row_items.append(f"{val:.6f}")
            
            lines.append(",".join(row_items))
            current_time += one_step
            
        return "\n".join(lines)

    def export_generic_csv(self, project_id: int, dataset_ids: List[int], start_date: datetime, variable: str = "Flow", profile_line: str = "mean", sg_enabled: bool = False, sg_window: int = 21, sg_order: int = 3) -> str:
        """
        Generate a simple flat CSV with headers.
        Format: Time,Monitor1,Monitor2,...
        """
        # Get Datasets
        stmt = select(FsaDataset).where(FsaDataset.id.in_(dataset_ids))
        datasets = self.session.exec(stmt).all()
        dataset_map = {d.id: d for d in datasets}
        
        # Sort datasets by name for column order
        sorted_dataset_ids = sorted(dataset_ids, key=lambda id: dataset_map[id].name if id in dataset_map else "")
        
        # Determine units based on variable
        if variable == 'Flow':
            units = 'l/s'  # Keep l/s for generic CSV (more intuitive)
            conversion_factor = 1.0
        elif variable == 'Depth':
            units = 'mm'
            conversion_factor = 1.0
        elif variable == 'Velocity':
            units = 'm/s'
            conversion_factor = 1.0
        else:
            units = ''
            conversion_factor = 1.0
        
        # Determine which field to extract
        line_suffix = profile_line  # 'mean', 'min', or 'max'
        
        # Compute profiles for each dataset (using per-monitor SG settings)
        profiles = {}
        
        for ds_id in sorted_dataset_ids:
            # Get this monitor's saved SG settings
            monitor_sg = self.get_sg_settings(ds_id)
            
            res = self.compute_dwf_analysis(
                ds_id, project_id, 
                sg_enabled=monitor_sg["sg_enabled"], 
                sg_window=monitor_sg["sg_window"], 
                sg_order=monitor_sg["sg_order"]
            )
            if "error" in res:
                profiles[ds_id] = [0.0] * 720
            else:
                dense_profile = [0.0] * 720
                
                if 'profile' in res:
                    for entry in res['profile']:
                        sec = entry['time_of_day_seconds']
                        idx = int(round(sec / 120.0))
                        if 0 <= idx < 720:
                            field_name = f"{variable.lower()}_{line_suffix}"
                            val = entry.get(field_name, 0)
                            
                            if val is None: val = 0
                            dense_profile[idx] = float(val) * conversion_factor
                
                profiles[ds_id] = dense_profile

        # Build CSV
        lines = []
        
        # Header row
        header = ["Time"]
        for ds_id in sorted_dataset_ids:
            name = dataset_map[ds_id].name
            header.append(f"{name} ({units})")
        lines.append(",".join(header))
        
        # Data rows
        current_time = start_date
        one_step = timedelta(minutes=2)
        
        for i in range(720):
            row_items = []
            time_str = current_time.strftime("%Y-%m-%d %H:%M")
            row_items.append(time_str)
            
            for ds_id in sorted_dataset_ids:
                val = profiles[ds_id][i]
                row_items.append(f"{val:.4f}")
            
            lines.append(",".join(row_items))
            current_time += one_step
            
        return "\n".join(lines)
