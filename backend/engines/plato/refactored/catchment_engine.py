"""
Catchment-based storage analysis engine.

This module handles multi-tank catchment analysis where storage is optimized
across multiple CSOs with upstream/downstream relationships and pass-forward flow constraints.

Key features:
- Multiple tanks analyzed together timestep-by-timestep
- Delta propagation from upstream to downstream CSOs
- Model 1: Independent draindown (local capacity)
- Model 2: Coordinated draindown (wait for downstream tanks to empty)
"""

import logging
import numpy as np
import pandas as pd
from datetime import timedelta, datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class CSOState:
    """Runtime state for a CSO during simulation."""
    name: str
    current_stored_volume: float = 0.0
    storage_volume_n: float = 0.0
    spill_count: int = -1
    stop_iteration: bool = False
    insufficient_storage_volumes: List[float] = field(
        default_factory=lambda: [0])
    excessive_storage_volumes: List[float] = field(default_factory=list)
    spill_count_exceeded_prior: bool = False
    storage_volume_increase: float = -1

    # Model 2 coordination flags
    tank_full: bool = False
    full_ds: bool = False

    # Iteration history for gradient-based convergence (storage_volume, spill_count)
    iteration_history: List[Tuple[float, int]] = field(default_factory=list)

    # Spill events DataFrame for intelligent augmentation
    last_spill_events: Optional[pd.DataFrame] = None


class CatchmentAnalysisEngine:
    """
    Catchment-based storage optimization engine.

    Key differences from CSO engine (Method 1):
    - Multiple tanks analyzed together
    - Upstream/downstream CSO relationships
    - Pass-forward flow (PFF) augmentation
    - Hierarchical position levels
    - Tank interactions and constraints
    """

    def __init__(self, overflow_data: pd.DataFrame, flow_data: pd.DataFrame, depth_data: pd.DataFrame,
                 master_directory: str, timestep_length: timedelta, progress_callback=None,
                 data_folder: str = None, file_type: str = 'csv', date_kwargs: dict = None):
        """
        Initialize catchment analysis engine.

        Args:
            overflow_data: DataFrame with CSO configuration (one row per CSO)
            flow_data: Time series flow data for all CSOs
            depth_data: Time series depth data for continuation links
            master_directory: Output directory path
            timestep_length: Simulation timestep as timedelta
            progress_callback: Optional callback function for progress updates
            data_folder: Optional path to data folder (needed for effective links)
            file_type: Optional data file type (default: 'csv')
            date_kwargs: Optional date parsing kwargs for building effective links
        """
        self.overflow_data = overflow_data
        self.flow_data = flow_data
        self.depth_data = depth_data
        self.master_directory = master_directory
        self.timestep_length = timestep_length
        self.timestep_seconds = timestep_length.total_seconds()
        self.progress_callback = progress_callback

        # Parse CSO objects from configuration
        self.csos = self._initialize_csos()

        # Build effective links if needed and we have data_folder
        if data_folder and date_kwargs:
            self._build_effective_links(data_folder, file_type, date_kwargs)

        # Create runtime state for each CSO
        self.cso_states = {cso['Name']: CSOState(
            name=cso['Name']) for cso in self.csos}

        self._log(f"Initialized catchment engine with {len(self.csos)} CSOs")
        for cso in self.csos:
            self._log(
                f"{cso['Display_Name']} - {cso['Name']} (Level {cso['Level']})")

    def _log(self, message: str):
        """Log message to both logging system and progress callback."""
        logging.info(message)
        if self.progress_callback:
            self.progress_callback(message)

    def _initialize_csos(self) -> List[Dict]:
        """Parse overflow data into CSO configuration objects."""
        csos = []

        for idx, row in self.overflow_data.iterrows():
            # Skip parent/grouping rows - they don't have valid CSO configuration
            if pd.isna(row.get('CSO Name')) or pd.isna(row.get('Continuation Link')):
                continue

            cso = {
                'Display_Name': row['CSO Display Name'],
                'Name': row['CSO Name'],
                'Continuation_Link': row['Continuation Link'],
                'Spill_Target': int(row['Spill Target (Entire Period)']),
                'PFF_Increase': row.get('PFF Increase (m3/s)', 0) or 0,
                'Tank_Volume': row.get('Tank Volume (m3)', None) if pd.notna(row.get('Tank Volume (m3)')) else None,
                'Pumping_Mode': row['Pumping Mode'],
                'Pump_Rate': row.get('Pump Rate (m3/s)', None) if row['Pumping Mode'] == 'Fixed' else None,
                'Flow_Return_Threshold': row['Flow Return Threshold (m3/s)'],
                'Depth_Return_Threshold': row['Depth Return Threshold (m)'],
                'Time_Delay': timedelta(hours=int(row['Time Delay (hours)'])),
                'Spill_Flow_Threshold': row['Spill Flow Threshold (m3/s)'],
                'Spill_Volume_Threshold': row['Spill Volume Threshold (m3)'],
                'Level': None,  # Will be calculated from relationships
                'Upstream_CSOs': None,
                'Downstream_CSO': None,
                'Max_PFF': None,
                'Distance': None,
                'Average_Velocity': None,
                'Time_Shift': None
            }

            # Parse upstream CSO relationships
            upstream_value = row.get('Upstream CSOs')
            has_upstream = (upstream_value is not None and
                            upstream_value != [] and
                            (isinstance(upstream_value, str) or len(upstream_value) > 0))

            if has_upstream:
                # Handle both string (comma-separated) and list formats
                if isinstance(upstream_value, str):
                    cso['Upstream_CSOs'] = [x.strip()
                                            for x in upstream_value.split(",") if x.strip()]
                else:
                    cso['Upstream_CSOs'] = upstream_value

                max_pff = row.get('Maximum Pass Forward Flow (m3/s)')
                if pd.notna(max_pff) and max_pff != 'Unknown':
                    cso['Max_PFF'] = float(max_pff)
                else:
                    cso['Max_PFF'] = 'Unknown'

            # Parse downstream CSO relationship (singular)
            downstream_value = row.get('Downstream CSO')
            if downstream_value is not None and pd.notna(downstream_value):
                cso['Downstream_CSO'] = downstream_value
                distance = row.get('Distance (m)')
                velocity = row.get('Average Velocity (m/s)')

                # Only set distance/velocity if they're valid (not None)
                if distance is not None and pd.notna(distance):
                    cso['Distance'] = distance
                if velocity is not None and pd.notna(velocity):
                    cso['Average_Velocity'] = velocity

                # Calculate time shift only if both distance and velocity are available
                if cso['Distance'] is not None and cso['Average_Velocity'] is not None:
                    time_shift_seconds = cso['Distance'] / \
                        cso['Average_Velocity']
                    # Round to nearest timestep
                    time_shift_steps = round(
                        time_shift_seconds / self.timestep_seconds)
                    cso['Time_Shift'] = timedelta(
                        seconds=time_shift_steps * self.timestep_seconds)

            csos.append(cso)

        # Calculate position levels using topological sort
        self._calculate_position_levels(csos)

        # Sort by position level descending (higher levels = upstream, processed first)
        csos.sort(key=lambda x: x['Level'], reverse=True)

        return csos

    def _calculate_position_levels(self, csos: List[Dict]) -> None:
        """
        Calculate position levels using topological sort.

        Position level determines processing order (matches legacy convention):
        - Level 1: No downstream CSOs (most downstream/outlets)
        - Level N: min(downstream levels) + 1 (increases going upstream)

        CSOs are sorted in descending order, so higher levels (upstream) are processed first.
        This ensures upstream CSOs are always processed before downstream ones.
        """
        # Create lookup by name
        cso_dict = {cso['Name']: cso for cso in csos}

        def calculate_level(cso_name: str, visited: set) -> int:
            """Recursively calculate level for a CSO."""
            if cso_name in visited:
                raise ValueError(
                    f"Circular dependency detected involving CSO '{cso_name}'")

            cso = cso_dict[cso_name]

            # If already calculated, return it
            if cso['Level'] is not None:
                return cso['Level']

            # If no downstream CSO, level is 1 (outlet)
            if not cso['Downstream_CSO']:
                cso['Level'] = 1
                return 1

            # Calculate level based on downstream CSO
            visited.add(cso_name)
            downstream_name = cso['Downstream_CSO']
            if downstream_name not in cso_dict:
                raise ValueError(
                    f"Downstream CSO '{downstream_name}' referenced by '{cso_name}' not found")
            downstream_level = calculate_level(downstream_name, visited)
            visited.remove(cso_name)

            cso['Level'] = downstream_level + 1
            return cso['Level']

        # Calculate level for all CSOs
        for cso in csos:
            calculate_level(cso['Name'], set())

    @staticmethod
    def infer_upstream_from_downstream(overflow_data: pd.DataFrame) -> pd.DataFrame:
        """
        Infer 'Upstream CSOs' column from 'Downstream CSO' relationships.

        This allows users to define only downstream relationships in the graphical
        editor, and automatically populate the upstream relationships.

        Args:
            overflow_data: DataFrame with 'Downstream CSO' column

        Returns:
            DataFrame with 'Upstream CSOs' column populated
        """
        # Create a copy to avoid modifying original
        df = overflow_data.copy()

        # Initialize Upstream CSOs column if not exists
        if 'Upstream CSOs' not in df.columns:
            df['Upstream CSOs'] = None

        # Build upstream relationships from downstream
        upstream_map = {}
        for idx, row in df.iterrows():
            cso_name = row['CSO Name']
            downstream = row.get('Downstream CSO')

            if pd.notna(downstream):
                if downstream not in upstream_map:
                    upstream_map[downstream] = []
                upstream_map[downstream].append(cso_name)

        # Populate upstream CSOs
        for idx, row in df.iterrows():
            cso_name = row['CSO Name']
            if cso_name in upstream_map:
                df.at[idx, 'Upstream CSOs'] = ', '.join(upstream_map[cso_name])

        return df

    def _build_effective_links(self, data_folder: str, file_type: str, date_kwargs: dict):
        """
        Build effective link series for any continuation links that use Effective(...) syntax.
        Modifies self.flow_data in place by adding effective link columns.

        Args:
            data_folder: Path to folder containing CSV data files
            file_type: Type of data files ('csv')
            date_kwargs: Date parsing kwargs for pd.read_csv
        """
        import glob
        import os

        # Find all effective links in CSO configuration
        effective_links_to_build = {}

        for cso in self.csos:
            cont_link = cso['Continuation_Link']

            # Check if this is an effective link definition
            if cont_link.startswith('Effective(') and cont_link.endswith(')'):
                # Check if we already have this column in flow_data
                if cont_link not in self.flow_data.columns:
                    # Parse component links
                    # Remove "Effective(" and ")"
                    components_str = cont_link[10:-1]
                    components = [c.strip() for c in components_str.split(',')]
                    effective_links_to_build[cont_link] = components

        if not effective_links_to_build:
            return  # No effective links to build

        # Collect all component links we need
        all_components = set()
        for components in effective_links_to_build.values():
            all_components.update(components)

        self._log(
            f"Building {len(effective_links_to_build)} effective link(s) "
            f"from {len(all_components)} component(s)..."
        )

        # Load flow data for all component links
        if file_type == 'csv':
            # Look for both standard (_Q) and ICM default (_us_flow) naming
            flow_files = sorted(
                glob.glob(os.path.join(data_folder, "*_Q.csv")))
            flow_files += sorted(glob.glob(os.path.join(data_folder, "*_us_flow.csv")))

            # Load only the component columns we need
            component_dfs = []
            for f in flow_files:
                available_cols = pd.read_csv(f, nrows=0).columns.tolist()
                needed_cols = ['Time'] + \
                    [c for c in all_components if c in available_cols]

                if len(needed_cols) > 1:  # Has Time + at least one component
                    df = pd.read_csv(f, usecols=needed_cols, **date_kwargs)
                    component_dfs.append(df)

            if not component_dfs:
                raise ValueError(
                    f"Component links not found in data: {all_components}")

            # Merge all component data
            component_data = component_dfs[0]
            for df in component_dfs[1:]:
                component_data = component_data.merge(
                    df, on='Time', how='outer')

            component_data.sort_values('Time', inplace=True)
            component_data.drop_duplicates(
                subset=['Time'], keep='first', inplace=True)
        else:
            raise NotImplementedError(
                f"File type {file_type} not yet supported")

        # Build effective series
        effective_df = pd.DataFrame({'Time': component_data['Time']})

        for effective_name, components in effective_links_to_build.items():
            # Verify all components exist
            missing = [c for c in components if c not in component_data.columns]
            if missing:
                raise ValueError(
                    f"Components for {effective_name} not found in data: {missing}")

            # Sum component flows
            effective_df[effective_name] = component_data[components].sum(
                axis=1)
            self._log(
                f"  Created {effective_name} from {len(components)} component(s)")

        # Merge effective series into flow_data
        self.flow_data = self.flow_data.merge(
            effective_df, on='Time', how='left')

    def run_analysis(self, start_date: str, end_date: str, model_id: int = 1,
                     bathing_season_start: Optional[str] = None, bathing_season_end: Optional[str] = None) -> Dict:
        """
        Run catchment-based storage analysis for multiple CSOs.

        LEGACY APPROACH: All CSOs simulated together timestep-by-timestep with
        delta propagation from upstream to downstream tanks.

        Args:
            start_date: Analysis start date (dd/mm/yyyy HH:MM:SS)
            end_date: Analysis end date (dd/mm/yyyy HH:MM:SS)
            model_id: Model type (1=local capacity draindown, 2=all downstream empty)
            bathing_season_start: Bathing season start (dd/mm)
            bathing_season_end: Bathing season end (dd/mm)

        Returns:
            Dictionary with results for each CSO
        """
        self._log("=" * 80)
        self._log("CATCHMENT ANALYSIS")
        self._log("=" * 80)
        self._log(
            f"Model ID: {model_id} ({'Independent' if model_id == 1 else 'Coordinated'} draindown)")
        self._log(f"Date Range: {start_date} to {end_date}")
        self._log(f"Number of CSOs: {len(self.csos)}")

        # Parse dates
        start_dt = datetime.strptime(start_date, "%d/%m/%Y %H:%M:%S")
        end_dt = datetime.strptime(end_date, "%d/%m/%Y %H:%M:%S")

        # Parse bathing season if provided
        bathing_season = None
        if bathing_season_start and bathing_season_end:
            start_d, start_m = map(int, bathing_season_start.split('/'))
            end_d, end_m = map(int, bathing_season_end.split('/'))
            bathing_season = ((start_m, start_d), (end_m, end_d))

        # Initialize each CSO with timeseries data
        self._log("\nProcessing CSO timeseries data...")
        for cso in self.csos:
            self._process_cso_data(cso, start_dt, end_dt)

        # Run initial spill counts (no storage, no PFF increase)
        self._log("\n" + "=" * 60)
        self._log("INITIAL CONDITIONS (No storage, No PFF increase)")
        self._log("=" * 60)
        for cso in self.csos:
            spill_count, bathing_count, _ = self._count_spills(
                cso, bathing_season)
            self._log(
                f"{cso['Display_Name']}: {spill_count} spills ({bathing_count} bathing)")

        # Main iteration loop
        max_iterations = 50
        iteration = -1
        continue_iteration = True

        # Check if any CSO has PFF increase
        has_pff_increase = any(cso['PFF_Increase'] > 0 for cso in self.csos)

        while continue_iteration:
            iteration += 1

            # Skip iteration 0 if no PFF increases, but initialize storage for iteration 1
            if iteration == 0 and not has_pff_increase:
                iteration = 1
                self._log("\n" + "=" * 60)
                self._log("ITERATION 0 SKIPPED (No PFF increase)")
                self._log("=" * 60)

                # Initialize storage volumes for iteration 1 based on initial conditions
                for cso in self.csos:
                    state = self.cso_states[cso['Name']]
                    if cso['Tank_Volume'] is not None:
                        # Fixed tank volume
                        state.storage_volume_n = cso['Tank_Volume']
                    else:
                        # Calculate initial storage needed based on initial spill count
                        # Use the initial conditions spill count (from iteration -1)
                        initial_spill_count, _, initial_spill_events = self._count_spills(
                            cso, bathing_season)

                        if initial_spill_count > cso['Spill_Target'] and len(initial_spill_events) > cso['Spill_Target']:
                            # Calculate initial storage from the Nth largest spill
                            # Sort by volume descending and take the Nth largest (last allowed)
                            sorted_spills = initial_spill_events.sort_values(
                                'Spill Volume (m3)', ascending=False)
                            nth_spill = sorted_spills.iloc[cso['Spill_Target'] - 1]
                            initial_increase = nth_spill['Spill Volume (m3)']
                            state.storage_volume_n = initial_increase
                            self._log(f"  {cso['Display_Name']}: Initial storage set to {initial_increase:.1f} m³ "
                                      f"(Nth largest spill, {initial_spill_count} initial spills)")
                        else:
                            # Target already met with no storage
                            state.storage_volume_n = 0.0
                            state.stop_iteration = True
                            self._log(
                                f"  {cso['Display_Name']}: Target already met (no storage needed)")

            self._log("\n" + "=" * 60)
            self._log(f"ITERATION {iteration}")
            self._log("=" * 60)

            # Reset CSO states for this iteration
            for cso in self.csos:
                state = self.cso_states[cso['Name']]
                state.stop_iteration = False
                state.current_stored_volume = 0.0
                state.tank_full = False
                state.full_ds = False
                # Reset timeseries to original
                cso['Timeseries_Data'] = cso['Timeseries_Data_Original'].copy()

            # Simulate all CSOs together, timestep by timestep
            self._simulate_iteration(start_dt, end_dt, model_id)

            # Count spills for all CSOs
            self._log("\nResults:")
            for cso in self.csos:
                state = self.cso_states[cso['Name']]
                spill_count, bathing_count, spill_events = self._count_spills(
                    cso, bathing_season)
                state.spill_count = spill_count
                state.last_spill_events = spill_events  # Store for augmentation method

                # Record iteration history for gradient-based convergence
                state.iteration_history.append(
                    (state.storage_volume_n, spill_count))

                # self._log(
                #     f"  {cso['Name']}: {spill_count} spills, {state.storage_volume_n:.1f} m³ storage")
                self._log(
                    f"  {cso['Display_Name']}: {spill_count} spills, {state.storage_volume_n:.1f} m³ storage")

                # Calculate storage increase needed (Nth largest spill volume)
                if spill_count > cso['Spill_Target'] and len(spill_events) > cso['Spill_Target']:
                    # Use volume of the Nth largest spill
                    # Sort by volume descending and take the Nth largest (last allowed)
                    sorted_spills = spill_events.sort_values(
                        'Spill Volume (m3)', ascending=False)
                    nth_spill = sorted_spills.iloc[cso['Spill_Target'] - 1]
                    state.storage_volume_increase = nth_spill['Spill Volume (m3)']
                else:
                    state.storage_volume_increase = 0.0

            # Adjust storage volumes for next iteration
            for cso in self.csos:
                state = self.cso_states[cso['Name']]
                old_volume = state.storage_volume_n

                # Check if target met or fixed tank
                if (state.spill_count <= cso['Spill_Target'] and state.storage_volume_n == 0):
                    state.stop_iteration = True
                elif state.spill_count == cso['Spill_Target']:
                    state.stop_iteration = True
                # I believe we shouldn't have any None values due to validation controls
                # elif cso['Tank_Volume'] is not None:
                #     state.storage_volume_n = cso['Tank_Volume']
                #     state.stop_iteration = True
                # Target exceeded
                elif state.spill_count > cso['Spill_Target'] and not state.spill_count_exceeded_prior:
                    state.insufficient_storage_volumes.append(
                        state.storage_volume_n)
                    state.storage_volume_n = self._augment_storage(
                        cso['Display_Name'],
                        state.storage_volume_n,
                        state.storage_volume_increase,
                        state.last_spill_events,
                        cso['Spill_Target'],
                        state.iteration_history)
                # Target undershot (first time)
                elif state.spill_count < cso['Spill_Target'] and not state.spill_count_exceeded_prior:
                    state.spill_count_exceeded_prior = True
                    state.excessive_storage_volumes.append(
                        state.storage_volume_n)
                    state.storage_volume_n = 0.5 * (
                        max(state.insufficient_storage_volumes) +
                        min(state.excessive_storage_volumes)
                    )
                # Target exceeded (bisection)
                elif state.spill_count > cso['Spill_Target']:
                    state.insufficient_storage_volumes.append(
                        state.storage_volume_n)
                    state.storage_volume_n = 0.5 * (
                        max(state.insufficient_storage_volumes) +
                        min(state.excessive_storage_volumes)
                    )
                # Target undershot (bisection)
                elif state.spill_count < cso['Spill_Target']:
                    state.excessive_storage_volumes.append(
                        state.storage_volume_n)
                    state.storage_volume_n = 0.5 * (
                        max(state.insufficient_storage_volumes) +
                        min(state.excessive_storage_volumes)
                    )

                # Check convergence (volume change < 1 m³)
                volume_change = abs(old_volume - state.storage_volume_n)
                if 0 < volume_change < 1:
                    state.stop_iteration = True
                    self._log(
                        f"  {cso['Display_Name']}: Converged (volume change < 1 m³)")

            # Check if all CSOs should stop
            if all(self.cso_states[cso['Name']].stop_iteration for cso in self.csos):
                self._log("\n✓ All CSOs meet target or converged")
                continue_iteration = False

            # Check max iterations
            if iteration >= max_iterations:
                self._log(
                    f"\n⚠ Maximum iterations ({max_iterations}) reached")
                continue_iteration = False

        # Compile final results
        results = {}
        for cso in self.csos:
            state = self.cso_states[cso['Name']]
            spill_count, bathing_count, spill_events = self._count_spills(
                cso, bathing_season)

            # Prepare timeseries with original flow column for plotting
            timeseries_output = cso['Timeseries_Data'].copy()
            cso_name = cso['Name']
            cso_flow_col = cso_name + '_Flow'

            # Add CSO_Flow_Original from the unmodified original data
            if cso_flow_col in cso['Timeseries_Data_Original'].columns:
                timeseries_output['CSO_Flow_Original'] = cso['Timeseries_Data_Original'][cso_flow_col].copy(
                )

            results[cso['Name']] = {
                'storage_volume': state.storage_volume_n,
                'spill_count': spill_count,
                'bathing_spill_count': bathing_count,
                'iterations': iteration,
                'converged': state.stop_iteration,
                'spill_events': spill_events,
                'timeseries': timeseries_output
            }

        self._log("\n" + "=" * 80)
        self._log("CATCHMENT ANALYSIS COMPLETE")
        self._log("=" * 80)

        return results

    def _process_cso_data(self, cso: Dict, start_date: datetime, end_date: datetime):
        """Process and filter timeseries data for a CSO."""
        cso_name = cso['Name']
        cont_link = cso['Continuation_Link']

        # Filter flow and depth data to date range
        flow_mask = (self.flow_data['Time'] >= start_date) & (
            self.flow_data['Time'] <= end_date)
        depth_mask = (self.depth_data['Time'] >= start_date) & (
            self.depth_data['Time'] <= end_date)

        # Create combined timeseries
        timeseries = pd.DataFrame()
        timeseries['Time'] = self.flow_data.loc[flow_mask,
                                                'Time'].reset_index(drop=True)
        timeseries[cso_name + '_Flow'] = self.flow_data.loc[flow_mask,
                                                            cso_name].reset_index(drop=True)
        timeseries[cont_link + '_Flow'] = self.flow_data.loc[flow_mask,
                                                             cont_link].reset_index(drop=True)

        # Store original continuation flow for plotting comparison (before storage modifications)
        # This matches the single CSO engine's 'Cont_Flow_Original' column
        timeseries['Cont_Flow_Original'] = timeseries[cont_link + '_Flow'].copy()

        # Add depth if available
        depth_col = cont_link + '_Depth'
        if depth_col in self.depth_data.columns:
            timeseries[depth_col] = self.depth_data.loc[depth_mask,
                                                        depth_col].reset_index(drop=True)
        else:
            timeseries[depth_col] = 0.0

        # Initialize working columns
        timeseries['Tank Volume'] = 0.0
        timeseries['Outgoing Delta'] = 0.0
        timeseries['Incoming Delta'] = 0.0

        # Calculate time delay (for draindown check)
        time_delay_steps = int(
            cso['Time_Delay'].total_seconds() / self.timestep_seconds)
        if time_delay_steps > 0:
            timeseries['Max Flow in Time Delay'] = (
                timeseries[cont_link + '_Flow']
                .rolling(window=time_delay_steps, min_periods=1)
                .max()
            )
        else:
            timeseries['Max Flow in Time Delay'] = 0.0

        # Store original and working copies
        cso['Timeseries_Data_Original'] = timeseries.copy()
        cso['Timeseries_Data'] = timeseries.copy()

    def _simulate_iteration(self, start_date: datetime, end_date: datetime, model_id: int):
        """
        Simulate all CSOs together, timestep by timestep.

        This is the core catchment simulation loop where:
        1. Deltas propagate from upstream to downstream
        2. Tanks fill and drain according to model rules
        3. All CSOs interact at each timestep

        OPTIMIZED: Uses numpy arrays for fast column access instead of pandas .at[]
        """
        timesteps = pd.date_range(
            start_date, end_date, freq=self.timestep_length)
        n_timesteps = len(timesteps)

        # Pre-convert DataFrames to numpy arrays for MUCH faster access
        # Dictionary to store arrays for each CSO
        cso_arrays = {}
        for cso in self.csos:
            ts = cso['Timeseries_Data']
            cso_name = cso['Name']
            cso_flow_col = cso_name + '_Flow'
            cont_flow_col = cso['Continuation_Link'] + '_Flow'
            cont_depth_col = cso['Continuation_Link'] + '_Depth'

            # Extract to numpy arrays (views, not copies)
            cso_arrays[cso_name] = {
                'cso_flow': ts[cso_flow_col].values,
                'cont_flow': ts[cont_flow_col].values,
                'cont_depth': ts[cont_depth_col].values,
                'incoming_delta': ts['Incoming Delta'].values,
                'tank_volume': ts['Tank Volume'].values,
                'outgoing_delta': ts['Outgoing Delta'].values,
                'max_flow_delay': ts['Max Flow in Time Delay'].values,
                'time': ts['Time'].values
            }

        # Also extract original continuation flow for delta calculation
        for cso in self.csos:
            cso_name = cso['Name']
            ts_orig = cso['Timeseries_Data_Original']
            cont_flow_col = cso['Continuation_Link'] + '_Flow'
            cso_arrays[cso_name]['cont_flow_orig'] = ts_orig[cont_flow_col].values

        for t_idx in range(n_timesteps):
            t = timesteps[t_idx]

            # Progress indicator
            if t.day == 1 and t.hour == 0 and t.minute == 0:
                logging.debug(f"  Processing {t.strftime('%Y-%m-%d')}")

            # Process each CSO in order (upstream to downstream)
            for cso in self.csos:
                state = self.cso_states[cso['Name']]
                cso_name = cso['Name']
                arrays = cso_arrays[cso_name]

                # Get current values from arrays
                cso_flow = arrays['cso_flow'][t_idx]
                cont_flow = arrays['cont_flow'][t_idx]
                cont_depth = arrays['cont_depth'][t_idx]

                # STEP 1: Apply incoming deltas from upstream CSOs
                if cso['Upstream_CSOs']:
                    delta = 0.0
                    for upstream_name in cso['Upstream_CSOs']:
                        upstream_cso = next(
                            c for c in self.csos if c['Name'] == upstream_name)
                        time_shift = upstream_cso.get('Time_Shift')

                        # Check if time-shifted timestep is available
                        if time_shift and t > start_date + time_shift:
                            # Calculate shifted index
                            shift_steps = int(
                                time_shift.total_seconds() / self.timestep_seconds)
                            shifted_idx = t_idx - shift_steps

                            if shifted_idx >= 0:
                                upstream_arrays = cso_arrays[upstream_name]
                                delta += upstream_arrays['outgoing_delta'][shifted_idx]

                    if delta > 0:
                        arrays['incoming_delta'][t_idx] = delta

                        # If CSO is spilling, add delta to spill
                        if cso_flow > 0:
                            cso_flow += delta
                            arrays['cso_flow'][t_idx] = cso_flow
                        else:
                            # Not spilling: add to continuation up to Max PFF
                            if cso['Max_PFF'] and cso['Max_PFF'] != 'Unknown':
                                extra_capacity = cso['Max_PFF'] - cont_flow
                                if extra_capacity > 0:
                                    additional_pff = min(extra_capacity, delta)
                                    cont_flow += additional_pff
                                    arrays['cont_flow'][t_idx] = cont_flow
                                    # Excess goes to spill
                                    if delta > additional_pff:
                                        cso_flow += (delta - additional_pff)
                                        arrays['cso_flow'][t_idx] = cso_flow
                                else:
                                    # No capacity, all delta goes to spill
                                    cso_flow += delta
                                    arrays['cso_flow'][t_idx] = cso_flow
                            else:
                                # No Max PFF defined, all delta goes to spill
                                cso_flow += delta
                                arrays['cso_flow'][t_idx] = cso_flow

                # Re-read current values after potential delta updates
                cso_flow = arrays['cso_flow'][t_idx]
                cont_flow = arrays['cont_flow'][t_idx]

                # STEP 2: Check draindown conditions
                if state.current_stored_volume > 0:
                    # Local draindown conditions (both models)
                    local_empty = (
                        cso_flow == 0 and
                        cont_flow < cso['Flow_Return_Threshold'] and
                        cont_depth < cso['Depth_Return_Threshold'] and
                        arrays['max_flow_delay'][t_idx] < cso['Flow_Return_Threshold']
                    )

                    # Check downstream conditions for Model 2
                    if model_id == 2 and cso['Downstream_CSO']:
                        ds_state = self.cso_states[cso['Downstream_CSO']]
                        empty_downstream = not ds_state.full_ds and not ds_state.tank_full
                    else:
                        empty_downstream = True

                    # Drain if conditions met
                    if local_empty and empty_downstream:
                        stored_before = state.current_stored_volume

                        if cso['Pumping_Mode'] == 'Fixed':
                            drain_rate = cso['Pump_Rate']
                        else:
                            # Variable: return at threshold minus current flow
                            drain_rate = cso['Flow_Return_Threshold'] - cont_flow

                        drain_volume = drain_rate * self.timestep_seconds

                        if drain_volume >= state.current_stored_volume:
                            state.current_stored_volume = 0.0
                        else:
                            state.current_stored_volume -= drain_volume

                        # Return drained volume to continuation link
                        returned_flow = (
                            stored_before - state.current_stored_volume) / self.timestep_seconds
                        cont_flow += returned_flow
                        arrays['cont_flow'][t_idx] = cont_flow

                # Re-read after draindown
                cso_flow = arrays['cso_flow'][t_idx]

                # STEP 3: Fill tank
                if state.current_stored_volume < state.storage_volume_n and cso_flow > 0:
                    inflow_volume = cso_flow * self.timestep_seconds
                    state.current_stored_volume += inflow_volume

                    if state.current_stored_volume <= state.storage_volume_n:
                        # All stored
                        arrays['cso_flow'][t_idx] = 0.0
                    else:
                        # Tank overflow
                        overflow_volume = state.current_stored_volume - state.storage_volume_n
                        state.current_stored_volume = state.storage_volume_n
                        arrays['cso_flow'][t_idx] = overflow_volume / \
                            self.timestep_seconds

                # Record tank volume
                arrays['tank_volume'][t_idx] = state.current_stored_volume

                # STEP 4: Calculate outgoing delta
                arrays['outgoing_delta'][t_idx] = (
                    arrays['cont_flow'][t_idx] -
                    arrays['cont_flow_orig'][t_idx]
                )

                # STEP 5: Update Model 2 coordination flags
                if model_id == 2:
                    state.tank_full = (state.current_stored_volume > 0)

                    if cso['Downstream_CSO']:
                        ds_state = self.cso_states[cso['Downstream_CSO']]
                        state.full_ds = ds_state.full_ds or ds_state.tank_full

    # def _count_spills(self, cso: Dict, bathing_season: Optional[Tuple]) -> Tuple[int, int, pd.DataFrame]:
    #     """
    #     Count spills for a CSO using 12/24 hour method.

    #     OPTIMIZED: Uses numpy arrays for faster iteration (matches default engine approach).
    #     """
    #     ts = cso['Timeseries_Data']
    #     cso_flow_col = cso['Name'] + '_Flow'
    #     flow_threshold = cso['Spill_Flow_Threshold']
    #     volume_threshold = cso['Spill_Volume_Threshold']

    #     # Filter by threshold (zero out flows below threshold)
    #     spill_flow_filtered = ts[cso_flow_col].where(
    #         ts[cso_flow_col] > flow_threshold, 0)

    #     # Rolling windows
    #     timestep_hours = self.timestep_seconds / 3600
    #     half_day = int(12 / timestep_hours)
    #     full_day = int(24 / timestep_hours)

    #     # Pre-calculate rolling spill volumes
    #     spill_vol_12hr = (
    #         spill_flow_filtered
    #         .rolling(window=half_day, min_periods=1, closed='left')
    #         .sum() * self.timestep_seconds
    #     )
    #     spill_vol_24hr = (
    #         spill_flow_filtered
    #         .rolling(window=full_day, min_periods=1, closed='left')
    #         .sum() * self.timestep_seconds
    #     )

    #     # OPTIMIZATION: Extract to numpy arrays for fast iteration
    #     spill_flow_arr = spill_flow_filtered.values
    #     time_arr = ts['Time'].values
    #     spill_vol_12hr_arr = spill_vol_12hr.values
    #     spill_vol_24hr_arr = spill_vol_24hr.values
    #     n_rows = len(ts)

    #     # Pre-calculate bathing season flags if needed
    #     in_bathing_arr = None
    #     if bathing_season:
    #         month_arr = ts['Time'].dt.month.values
    #         day_arr = ts['Time'].dt.day.values
    #         in_bathing_arr = np.array([
    #             self._is_in_season(
    #                 (month_arr[i], day_arr[i]), bathing_season[0], bathing_season[1])
    #             for i in range(n_rows)
    #         ])

    #     # Count spills using 12/24 hour method (matches legacy algorithm)
    #     spill_events = []
    #     EAcount = 0
    #     cooldown = 0
    #     spill24 = 0.0

    #     for idx in range(n_rows):
    #         spill_flow = spill_flow_arr[idx]

    #         if EAcount == 0:  # No spill has occurred
    #             if spill_flow > 0:
    #                 EAcount = 1
    #             else:
    #                 EAcount = 0

    #         else:
    #             if EAcount < half_day:  # 12/24 hour count is mid progress
    #                 EAcount += 1
    #                 if cooldown > 0:
    #                     spill24 += spill_flow

    #             elif EAcount == half_day:  # Count is at 12 hours
    #                 if cooldown == 0:  # This is first 12 hours of spill
    #                     if spill_vol_12hr_arr[idx] >= volume_threshold:
    #                         spill_start_idx = max(0, idx - half_day)
    #                         spill_start_time = pd.Timestamp(
    #                             time_arr[spill_start_idx])

    #                         in_bathing = in_bathing_arr[idx] if in_bathing_arr is not None else False

    #                         spill_events.append({
    #                             'DateTime': spill_start_time,
    #                             'Spill Volume (m3)': spill_vol_12hr_arr[idx],
    #                             'Duration (hours)': 12.0,
    #                             'In Bathing Season': in_bathing
    #                         })

    #                         cooldown = 1  # Initiates first 24hour period
    #                         EAcount = 1
    #                         spill24 = 0.0
    #                         spill24 = spill_flow
    #                 elif cooldown > 0:
    #                     EAcount += 1
    #                     spill24 += spill_flow

    #             elif EAcount == full_day:  # At 24 hours
    #                 if spill24 > 0:  # Spill in the 24 hour cooldown - continuation
    #                     cooldown += 1  # Start a new 24 hour cooldown
    #                     EAcount = 1
    #                     spill24 = 0.0

    #                     # Create NEW spill event for continuation (matches default engine)
    #                     spill_start_idx = max(0, idx - full_day)
    #                     spill_start_time = pd.Timestamp(
    #                         time_arr[spill_start_idx])

    #                     in_bathing = in_bathing_arr[idx] if in_bathing_arr is not None else False

    #                     spill_events.append({
    #                         'DateTime': spill_start_time,
    #                         'Spill Volume (m3)': spill_vol_24hr_arr[idx],
    #                         'Duration (hours)': 24.0,
    #                         'In Bathing Season': in_bathing
    #                     })
    #                 else:  # No spill in 24 hours - event ended
    #                     cooldown = 0
    #                     EAcount = 0
    #                     spill24 = 0.0

    #             else:  # Count is between half day & full day
    #                 EAcount += 1
    #                 spill24 += spill_flow

    #     spill_df = pd.DataFrame(spill_events)
    #     entire_count = len(spill_df)
    #     bathing_count = len(spill_df[spill_df['In Bathing Season']]) if bathing_season and len(
    #         spill_df) > 0 else 0

    #     return entire_count, bathing_count, spill_df

    def _count_spills(self, cso: Dict, bathing_season: Optional[Tuple]) -> Tuple[int, int, pd.DataFrame]:
        # def _count_spills_equiv_to_default(self, cso: Dict, bathing_season: Optional[Tuple]) -> Tuple[int, int, pd.DataFrame]:
        """
        Equivalent to the SECOND function's logic (12/24 legacy with post filter on volume for ALL events),
        but takes the FIRST function's inputs and returns the FIRST function's outputs.
        - Inputs: cso dict (expects cso['Timeseries_Data'], cso['Name']+'_Flow', thresholds), bathing_season tuple
        - Output: (entire_count, bathing_count, spill_df)
        spill_df columns: ['DateTime','Spill Volume (m3)','Duration (hours)','In Bathing Season']
        """
        from datetime import timedelta
        import numpy as np
        import pandas as pd

        ts = cso['Timeseries_Data']
        cso_flow_col = cso['Name'] + '_Flow'
        flow_threshold = cso['Spill_Flow_Threshold']
        volume_threshold = cso['Spill_Volume_Threshold']

        # Filter by flow threshold: zero flows <= threshold
        spill_flow_filtered = ts[cso_flow_col].where(
            ts[cso_flow_col] > flow_threshold, 0)

        # Timestep & windows
        timestep_sec = self.timestep_seconds
        half_day = int((12 * 3600) / timestep_sec)   # 12 hours in timesteps
        full_day = int((24 * 3600) / timestep_sec)   # 24 hours in timesteps

        # Rolling volumes (left-closed to exclude current timestep, as per second function)
        spill_vol_12hr = (
            spill_flow_filtered
            .rolling(window=half_day, min_periods=1, closed='left')
            .sum() * timestep_sec
        )
        spill_vol_24hr = (
            spill_flow_filtered
            .rolling(window=full_day, min_periods=1, closed='left')
            .sum() * timestep_sec
        )

        # Arrays for fast looping
        spill_flow_arr = spill_flow_filtered.values
        time_arr = ts['Time'].values
        spill_vol_12hr_arr = spill_vol_12hr.values
        spill_vol_24hr_arr = spill_vol_24hr.values
        n_rows = len(ts)

        # Optional bathing-season flags sampled at the window END (policy used in your first function)
        in_bathing_arr = None
        if bathing_season:
            month_arr = ts['Time'].dt.month.values
            day_arr = ts['Time'].dt.day.values
            start, end = bathing_season
            in_bathing_arr = np.array([
                self._is_in_season(
                    (int(month_arr[i]), int(day_arr[i])), start, end)
                for i in range(n_rows)
            ])

        # State (matches the second function’s logic)
        EAcount = 0
        cooldown = 0
        spill24 = 0.0

        # Collect candidates: (start_time, volume, window_hours, end_index)
        candidates = []

        for i in range(n_rows):
            spill_flow = spill_flow_arr[i]

            if EAcount == 0:
                # No active counting; start if spilling
                if spill_flow > 0:
                    EAcount = 1
                else:
                    EAcount = 0
            else:
                if EAcount < half_day:
                    EAcount += 1
                    if cooldown > 0:
                        spill24 += spill_flow
                elif EAcount == half_day:
                    # First 12h window
                    if cooldown == 0:
                        spill_time = pd.Timestamp(
                            time_arr[i]) - timedelta(hours=12)
                        spill_volume = float(spill_vol_12hr_arr[i])
                        candidates.append((spill_time, spill_volume, 12.0, i))
                        cooldown = 1
                        EAcount = 1
                        spill24 = spill_flow  # reset & seed
                    elif cooldown > 0:
                        EAcount += 1
                        spill24 += spill_flow
                elif EAcount == full_day:
                    # 24h continuation window
                    if spill24 > 0:
                        cooldown += 1
                        EAcount = 1
                        spill24 = 0.0
                        spill_time = pd.Timestamp(
                            time_arr[i]) - timedelta(hours=24)
                        spill_volume = float(spill_vol_24hr_arr[i])
                        candidates.append((spill_time, spill_volume, 24.0, i))
                    else:
                        # End of event (24h with no spill)
                        EAcount = 0
                        spill24 = 0.0
                        cooldown = 0
                else:
                    # Between 12h and 24h
                    EAcount += 1
                    spill24 += spill_flow

        # Build output rows, applying the SECOND function's post-filter:
        # keep ONLY events with volume >= volume_threshold (applies to both 12h and 24h windows)
        spill_events = []
        for start_time, volume_m3, window_hours, end_idx in candidates:
            if volume_m3 >= volume_threshold:
                in_bathing = False
                if in_bathing_arr is not None:
                    # season sampled at window end
                    in_bathing = bool(in_bathing_arr[end_idx])
                spill_events.append({
                    'DateTime': start_time,
                    'Spill Volume (m3)': volume_m3,
                    # window duration (12 or 24)
                    'Duration (hours)': window_hours,
                    'In Bathing Season': in_bathing
                })

        # Handle empty case
        if spill_events:
            spill_df = pd.DataFrame(spill_events).sort_values(
                'DateTime').reset_index(drop=True)
        else:
            # Create empty DataFrame with correct columns
            spill_df = pd.DataFrame(columns=[
                'DateTime', 'Spill Volume (m3)',
                'Duration (hours)', 'In Bathing Season'
            ])

        entire_count = len(spill_df)
        bathing_count = int(spill_df['In Bathing Season'].sum()) if (
            bathing_season and entire_count > 0) else 0

        return entire_count, bathing_count, spill_df

    def _augment_storage(self, display_name: str, current_storage: float,
                         increase: float, spill_events: pd.DataFrame, target: int, iteration_history: List[Tuple[float, int]]) -> float:
        """
        Calculate next storage volume using intelligent extrapolation.

        Strategy (in order of preference):
        1. Gradient method: Use Δspills/Δstorage from recent iterations
        2. Spill statistics: Use 75th percentile of excess spill volumes
        3. Scaling factor: Reduce increase as we approach target
        4. Minimum progress: Ensure at least 5%/10m³ growth

        Args:
            current_storage: Current storage volume (m³)
            increase: Suggested increase from median spill analysis (m³)
            spill_events: DataFrame of all spill events with volumes
            target: Target number of spills
            iteration_history: List of (storage_volume, spill_count) tuples

        Returns:
            New storage volume (m³)
        """
        # Strategy 1: Gradient-based extrapolation (requires 2+ iterations)
        if len(iteration_history) >= 2:
            # Get last two points
            (vol_prev, count_prev) = iteration_history[-2]
            (vol_curr, count_curr) = iteration_history[-1]

            delta_vol = vol_curr - vol_prev
            # Note: inverted (less spills = progress)
            delta_count = count_prev - count_curr

            # Only use gradient if we're making progress and gradient is reasonable
            if delta_count > 0 and delta_vol > 0:
                # Calculate gradient: m³ of storage per spill reduced
                gradient = delta_vol / delta_count

                # Extrapolate: how much storage to eliminate remaining spills
                remaining_spills = count_curr - target
                if remaining_spills > 0:
                    # Use gradient but be conservative (don't overshoot)
                    estimated_increase = gradient * remaining_spills

                    # Damping factor: reduce increase as we get closer to target
                    # (prevents oscillation near convergence)
                    damping = min(1.0, remaining_spills / max(target, 1))
                    # 50-100% of estimate
                    estimated_increase *= (0.5 + 0.5 * damping)

                    # Use gradient estimate if it's reasonable (between 10m³ and 5x current storage)
                    if 10 <= estimated_increase <= 5 * current_storage:
                        new_storage = current_storage + estimated_increase
                        self._log(f"    {display_name}: Using gradient method: +{estimated_increase:.1f} m³ "
                                  f"(gradient={gradient:.1f} m³/spill, {remaining_spills} spills remaining)")
                        return new_storage

        # Strategy 2: Spill statistics (use 75th percentile for conservatism)
        if increase > 0 and len(spill_events) > target:
            spills_over = spill_events.iloc[target:]
            if len(spills_over) > 0:
                # Use 75th percentile instead of median (more conservative)
                percentile_75 = spills_over['Spill Volume (m3)'].quantile(0.75)

                # Scale by proximity to target
                count_curr = len(spill_events)
                remaining_spills = count_curr - target
                scaling = min(1.0, remaining_spills / max(target, 1))

                adjusted_increase = percentile_75 * \
                    (0.7 + 0.3 * scaling)  # 70-100% of p75

                # Ensure minimum progress
                adjusted_increase = max(adjusted_increase,
                                        max(0.05 * current_storage, 10))

                new_storage = current_storage + adjusted_increase
                self._log(f"    {display_name}: Using spill statistics: +{adjusted_increase:.1f} m³ "
                          f"(p75={percentile_75:.1f} m³, scaling={scaling:.2f})")
                return new_storage

        # Strategy 3: Fallback to legacy heuristic (5%/10m³ minimum)
        min_increase = max(0.05 * current_storage, 10)

        if increase > min_increase:
            # Use calculated increase (median spill volume)
            new_storage = current_storage + increase
            self._log(
                f"    {display_name}: Using median increase: +{increase:.1f} m³")
        else:
            # Use minimum growth (5% or 10m³, whichever is larger)
            new_storage = max(1.05 * current_storage, current_storage + 10)
            self._log(
                f"    {display_name}: Using minimum increase: {new_storage - current_storage:.1f} m³")

        return new_storage

    def _filter_dates(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Filter flow data to specified date range."""
        start = pd.to_datetime(start_date, dayfirst=True)
        end = pd.to_datetime(end_date, dayfirst=True)

        mask = (self.flow_data['Time'] >= start) & (
            self.flow_data['Time'] <= end)
        return self.flow_data[mask].copy()

    def _prepare_cso_flow_data(self, flow_data: pd.DataFrame, cso: Dict,
                               prior_results: Dict) -> pd.DataFrame:
        """
        Prepare flow data for a specific CSO, incorporating upstream impacts.
        """
        # Extract relevant columns for this CSO
        required_cols = ['Time', cso['Name'], cso['Continuation_Link']]

        # Check for upstream CSO impacts
        if cso['Upstream_CSOs']:
            for upstream_name in cso['Upstream_CSOs']:
                if upstream_name in prior_results:
                    # Apply upstream storage impacts (simplified)
                    logging.info(
                        f"    Incorporating upstream CSO: {upstream_name}")

        return flow_data

    def _augment_pff(self, flow_data: pd.DataFrame, cso: Dict) -> pd.DataFrame:
        """
        Augment pass-forward flow for a CSO.

        Similar to FFT augmentation but for CSO continuation links.
        """
        pff_increase = cso['PFF_Increase']
        spill_col = cso['Name']
        cont_col = cso['Continuation_Link']

        # Where spilling less than PFF increase, add spill to continuation
        flow_data[cont_col] = flow_data[cont_col].where(
            flow_data[spill_col] > pff_increase,
            flow_data[cont_col] + flow_data[spill_col]
        )

        # Reduce spills by PFF increase
        flow_data[spill_col] = flow_data[spill_col] - pff_increase

        # Where still spilling, add PFF increase to continuation
        flow_data[cont_col] = flow_data[cont_col].where(
            flow_data[spill_col] < 0,
            flow_data[cont_col] + pff_increase
        )

        # Zero out negative spills
        flow_data[spill_col] = flow_data[spill_col].where(
            flow_data[spill_col] > 0.0001, 0
        )

        return flow_data

    def _optimize_cso_storage(self, flow_data: pd.DataFrame, cso: Dict,
                              bathing_season, max_iterations: int) -> Dict:
        """
        Iteratively optimize storage for a single CSO to meet spill target.
        """
        storage = 0  # Start with no storage
        iteration = 0
        test_points = []

        target_spills = cso['Spill_Target']

        while iteration < max_iterations:
            iteration += 1

            # Simulate with current storage
            sim_data = self._simulate_cso_storage(
                flow_data.copy(), cso, storage)

            # Count spills
            entire_count, bathing_count, spill_list = self._count_spills_for_cso(
                sim_data, cso, bathing_season
            )

            test_points.append((storage, entire_count, bathing_count))

            logging.info(
                f"    Iteration {iteration}: Storage={storage:.1f} m³, "
                f"Spills={entire_count} ({bathing_count} bathing)")

            # Check if target met
            if entire_count <= target_spills:
                logging.info(f"    ✓ Target met!")
                return {
                    'storage_volume': storage,
                    'spill_count': entire_count,
                    'bathing_spill_count': bathing_count,
                    'iterations': iteration,
                    'test_points': test_points,
                    'spill_events': spill_list
                }

            # Calculate storage increase
            if len(spill_list) > target_spills:
                spills_over = spill_list.iloc[target_spills:]
                mean_volume = spills_over['Spill Volume (m3)'].mean()
                storage_increase = max(mean_volume, 0.05 * storage, 10)
            else:
                storage_increase = max(0.05 * storage, 10)

            storage += storage_increase

        logging.warning(f"    Max iterations reached")
        return {
            'storage_volume': storage,
            'spill_count': entire_count if 'entire_count' in locals() else None,
            'bathing_spill_count': bathing_count if 'bathing_count' in locals() else None,
            'iterations': iteration,
            'test_points': test_points,
            'status': 'Max iterations reached'
        }

    def _simulate_cso_fixed_storage(self, flow_data: pd.DataFrame, cso: Dict,
                                    bathing_season) -> Dict:
        """Simulate CSO with fixed storage volume."""
        sim_data = self._simulate_cso_storage(
            flow_data.copy(), cso, cso['Tank_Volume'])

        entire_count, bathing_count, spill_list = self._count_spills_for_cso(
            sim_data, cso, bathing_season
        )

        return {
            'storage_volume': cso['Tank_Volume'],
            'spill_count': entire_count,
            'bathing_spill_count': bathing_count,
            'spill_events': spill_list
        }

    def _simulate_cso_storage(self, flow_data: pd.DataFrame, cso: Dict,
                              storage_volume: float) -> pd.DataFrame:
        """
        Simulate CSO tank storage behavior.

        Simplified version - full implementation would include:
        - Pump control logic (fixed/variable)
        - Draindown based on model_id
        - Upstream/downstream tank interactions
        """
        current_stored_vol = 0
        spill_col = cso['Name']
        cont_col = cso['Continuation_Link']

        flow_data['Tank_Volume'] = 0.0
        flow_data['Spill_In_Time_Delay'] = 0.0

        # Calculate time delay window
        time_delay_steps = int(
            cso['Time_Delay'].total_seconds() / self.timestep_length)

        for idx in range(len(flow_data)):
            # Simplified draindown logic
            draindown_allowed = False

            if current_stored_vol > 0:
                # Check return thresholds
                if (flow_data[cont_col].iloc[idx] < cso['Flow_Return_Threshold'] and
                        flow_data[spill_col].iloc[idx] == 0):
                    draindown_allowed = True

            # Draindown
            if draindown_allowed and cso['Pumping_Mode'] == 'Fixed':
                stored_before = current_stored_vol
                current_stored_vol -= cso['Pump_Rate'] * self.timestep_length

                if current_stored_vol < 0:
                    current_stored_vol = 0

                # Return flow to continuation
                returned = (stored_before - current_stored_vol) / \
                    self.timestep_length
                flow_data.loc[flow_data.index[idx], cont_col] += returned

            # Tank filling
            if current_stored_vol < storage_volume and flow_data[spill_col].iloc[idx] > 0:
                inflow_volume = flow_data[spill_col].iloc[idx] * \
                    self.timestep_length
                current_stored_vol += inflow_volume

                if current_stored_vol <= storage_volume:
                    flow_data.loc[flow_data.index[idx], spill_col] = 0
                else:
                    overflow = (current_stored_vol -
                                storage_volume) / self.timestep_length
                    flow_data.loc[flow_data.index[idx], spill_col] = overflow
                    current_stored_vol = storage_volume

            flow_data.loc[flow_data.index[idx],
                          'Tank_Volume'] = current_stored_vol

        return flow_data

    def _count_spills_for_cso(self, flow_data: pd.DataFrame, cso: Dict,
                              bathing_season) -> tuple:
        """Count spills for a single CSO using 12/24 hour method."""
        spill_col = cso['Name']
        flow_threshold = cso['Spill_Flow_Threshold']
        volume_threshold = cso['Spill_Volume_Threshold']

        # Add month_day for bathing season
        if bathing_season:
            flow_data['month_day'] = list(
                zip(flow_data['Time'].dt.month, flow_data['Time'].dt.day))

        # Filter by threshold
        flow_data['Spill_Filtered'] = flow_data[spill_col].where(
            flow_data[spill_col] > flow_threshold, 0
        )

        # Rolling windows
        timestep_hours = self.timestep_length / 3600
        half_day = int(12 / timestep_hours)
        full_day = int(24 / timestep_hours)

        flow_data['Spill_Volume_12hr'] = (
            flow_data['Spill_Filtered']
            .rolling(window=half_day, min_periods=1, closed='left')
            .sum() * self.timestep_length
        )
        flow_data['Spill_Volume_24hr'] = (
            flow_data['Spill_Filtered']
            .rolling(window=full_day, min_periods=1, closed='left')
            .sum() * self.timestep_length
        )

        # Count spills
        spill_events = []
        EAcount = 0
        cooldown = 0

        for idx in range(len(flow_data)):
            spill_flow = flow_data['Spill_Filtered'].iloc[idx]

            if EAcount == 0:
                if spill_flow > 0:
                    EAcount = 1
            else:
                if EAcount < half_day:
                    EAcount += 1

                    if EAcount == half_day:
                        spill_vol_12 = flow_data['Spill_Volume_12hr'].iloc[idx]
                        if spill_vol_12 >= volume_threshold:
                            cooldown = full_day
                            spill_start_idx = idx - half_day
                            spill_start_time = flow_data['Time'].iloc[spill_start_idx]

                            in_bathing = False
                            if bathing_season:
                                month_day = flow_data['month_day'].iloc[idx]
                                in_bathing = self._is_in_season(
                                    month_day, bathing_season[0], bathing_season[1])

                            spill_events.append({
                                'DateTime': spill_start_time,
                                'Spill Volume (m3)': spill_vol_12,
                                'In Bathing Season': in_bathing
                            })

                        EAcount = 0

                elif cooldown > 0:
                    cooldown -= 1

                    if cooldown == 0:
                        spill_vol_24 = flow_data['Spill_Volume_24hr'].iloc[idx]
                        if len(spill_events) > 0:
                            spill_events[-1]['Spill Volume (m3)'] = spill_vol_24
                        EAcount = 0

        spill_df = pd.DataFrame(spill_events)
        entire_count = len(spill_df)
        bathing_count = len(
            spill_df[spill_df['In Bathing Season']]) if bathing_season else 0

        return entire_count, bathing_count, spill_df

    def _is_in_season(self, date_tuple, start_tuple, end_tuple) -> bool:
        """Check if date is within seasonal range."""
        month, day = date_tuple
        start_m, start_d = start_tuple
        end_m, end_d = end_tuple

        if start_m <= end_m:
            return (month > start_m or (month == start_m and day >= start_d)) and \
                   (month < end_m or (month == end_m and day <= end_d))
        else:
            return (month > start_m or (month == start_m and day >= start_d)) or \
                   (month < end_m or (month == end_m and day <= end_d))
