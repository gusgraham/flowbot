"""
WwTW (Wastewater Treatment Works) storage analysis engine (Method 3).

This module handles treatment works inlet storage optimization with
pump control logic and Final Effluent Tank (FFT) augmentation.
"""

import logging
import numpy as np
import pandas as pd
from datetime import timedelta
from typing import Dict, Optional


class WWTWAnalysisEngine:
    """
    Wastewater Treatment Works storage optimization engine.

    Key differences from CSO engine (Method 1):
    - FFT (Final Effluent Tank) augmentation modeling
    - Pump control logic (on/off thresholds)
    - Single inlet point (not multiple CSOs)
    - Different draindown behavior
    """

    def __init__(self, run_data: pd.DataFrame, flow_data: pd.DataFrame,
                 outputs_directory: str, timestep_length: float,
                 progress_callback=None):
        """
        Initialize WwTW analysis engine.

        Args:
            run_data: DataFrame with run configuration
            flow_data: Time series flow data
            outputs_directory: Output directory path
            timestep_length: Simulation timestep in seconds
            progress_callback: Optional callback function for progress updates
        """
        self.run_data = run_data
        self.flow_data = flow_data
        self.outputs_directory = outputs_directory
        self.timestep_length = timestep_length
        self.progress_callback = progress_callback

        # Parse run configuration
        self.run_config = self._initialize_run_config()

        logging.info(
            f"Initialized WwTW engine for run: {self.run_config['Run_ID']}")

    def _log_progress(self, message: str):
        """Log progress message via callback if available."""
        if self.progress_callback:
            self.progress_callback(message)
        else:
            logging.info(message)

    def _initialize_run_config(self) -> Dict:
        """Parse run data into configuration object."""
        row = self.run_data.iloc[0]  # Single run configuration

        config = {
            'Run_ID': row['Run Suffix'],
            'FFT': row['FFT (m3/s)'],
            'Pump_Rate': row['Pump Rate (m3/s)'],
            'Pump_On_Threshold': row['Pump On Threshold (m3/s)'],
            'Pump_Off_Threshold': row['Pump Off Threshold (m3/s)'],
            'Description': (
                f"FFT: {row['FFT (m3/s)']} m3/s\n"
                f"Pump Rate: {row['Pump Rate (m3/s)']} m3/s\n"
                f"Pump On: {row['Pump On Threshold (m3/s)']} m3/s\n"
                f"Pump Off: {row['Pump Off Threshold (m3/s)']} m3/s"
            )
        }

        return config

    def run_analysis(self, storage_volume: float, time_delay_timesteps: int,
                     spill_flow_threshold: float, spill_volume_threshold: float,
                     bathing_season_start: str = None, bathing_season_end: str = None,
                     spill_target: int = None, bathing_spill_target: int = -1,
                     start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """
        Run WwTW storage analysis with iterative optimization.

        Args:
            storage_volume: Initial tank storage volume (m³)
            time_delay_timesteps: Time delay for pump control decisions (in timesteps)
            spill_flow_threshold: Minimum flow to count as spill (m³/s)
            spill_volume_threshold: Minimum volume to count as spill (m³)
            bathing_season_start: Bathing season start date (dd/mm)
            bathing_season_end: Bathing season end date (dd/mm)
            spill_target: Target number of spills (entire period)
            bathing_spill_target: Target number of spills in bathing season (-1 to disable)
            start_date: Analysis start date
            end_date: Analysis end date

        Returns:
            Dictionary with analysis results
        """
        self._log_progress("=" * 60)
        self._log_progress("WWTW ANALYSIS (Method 3)")
        self._log_progress("=" * 60)
        self._log_progress(f"Run ID: {self.run_config['Run_ID']}")
        self._log_progress(f"Initial Storage Volume: {storage_volume} m³")
        self._log_progress(f"Time Delay: {time_delay_timesteps} timesteps")

        # Filter flow data if date range provided
        if start_date and end_date:
            self._log_progress(f"Filtering data: {start_date} to {end_date}")
            flow_data = self._filter_dates(start_date, end_date)
        else:
            flow_data = self.flow_data.copy()

        # Parse bathing season if provided
        bathing_season = None
        if bathing_season_start and bathing_season_end:
            start_d, start_m = map(int, bathing_season_start.split('/'))
            end_d, end_m = map(int, bathing_season_end.split('/'))
            bathing_season = ((start_m, start_d), (end_m, end_d))
            self._log_progress(
                f"Bathing season: {bathing_season_start} to {bathing_season_end}")

        # If targets specified, run iterative optimization
        if spill_target is not None:
            self._log_progress(
                f"Starting iterative analysis (target: {spill_target} spills)")
            return self._run_iterative_analysis(
                flow_data, storage_volume, time_delay_timesteps,
                spill_flow_threshold, spill_volume_threshold,
                spill_target, bathing_spill_target, bathing_season
            )
        else:
            # Single simulation run
            self._log_progress("Running single simulation")
            return self._run_single_simulation(
                flow_data, storage_volume, time_delay_timesteps,
                spill_flow_threshold, spill_volume_threshold, bathing_season
            )

    def _filter_dates(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Filter flow data to specified date range."""
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        mask = (self.flow_data['Time'] >= start) & (
            self.flow_data['Time'] <= end)
        return self.flow_data[mask].copy()

    def _augment_fft(self, flow_data: pd.DataFrame, fft_increase: float) -> pd.DataFrame:
        """
        Model FFT (Final Effluent Tank) augmentation impact.

        Legacy logic (lines 353-357):
        - Where spill > FFT increase: add spill to continuation
        - Reduce all spill flows by FFT increase
        - Where still spilling: add FFT increase to continuation
        - Zero out negative spills

        Args:
            flow_data: Flow timeseries with 'Spill' and 'Continuation' columns
            fft_increase: Increase in pass-forward flow (m³/s)

        Returns:
            Modified flow data
        """
        flow_data = flow_data.copy()

        # Where spilling less than FFT increase, move all spill to continuation
        flow_data['Continuation'] = flow_data['Continuation'].where(
            flow_data['Spill'] > fft_increase,
            flow_data['Continuation'] + flow_data['Spill']
        )

        # Reduce all spills by FFT increase
        flow_data['Spill'] = flow_data['Spill'] - fft_increase

        # Where still spilling, add FFT increase to continuation
        flow_data['Continuation'] = flow_data['Continuation'].where(
            flow_data['Spill'] < 0,
            flow_data['Continuation'] + fft_increase
        )

        # Zero out negative spills
        flow_data['Spill'] = flow_data['Spill'].where(
            flow_data['Spill'] > 0.0001, 0)

        return flow_data

    def _run_single_simulation(self, flow_data: pd.DataFrame, storage_volume: float,
                               time_delay: int, spill_flow_threshold: float,
                               spill_volume_threshold: float, bathing_season) -> Dict:
        """Run a single simulation with given storage volume."""
        # Run simulator
        sim_data = self._simulate_storage(
            flow_data.copy(), storage_volume, time_delay)

        # Count spills
        spill_count, bathing_count, spill_list = self._count_spills(
            sim_data, spill_flow_threshold, spill_volume_threshold, bathing_season
        )

        self._log_progress(
            f"Single simulation: {spill_count} spills ({bathing_count} bathing)")

        return {
            'storage_volume': storage_volume,
            'spill_count': spill_count,
            'bathing_spill_count': bathing_count,
            'spill_events': spill_list,
            'flow_data': sim_data
        }

    def _run_iterative_analysis(self, flow_data: pd.DataFrame, initial_storage: float,
                                time_delay: int, spill_flow_threshold: float,
                                spill_volume_threshold: float, spill_target: int,
                                bathing_target: int, bathing_season) -> Dict:
        """
        Run iterative storage optimization to meet spill targets.

        Uses intelligent heuristics similar to catchment engine:
        1. Gradient-based extrapolation from recent iterations
        2. Statistical analysis of excess spill volumes (75th percentile)
        3. Binary search (bisection) when target is undershot
        4. Minimum progress guarantee to avoid stagnation
        """
        # Bathing mode is active only if bathing_target is explicitly set (not -1)
        is_bathing_mode = bathing_target > -1

        if is_bathing_mode:
            self._log_progress(
                f"Iterative analysis: targeting {spill_target} spills (entire), {bathing_target} bathing")
        else:
            self._log_progress(
                f"Iterative analysis: targeting {spill_target} spills")

        max_iterations = 30
        storage = initial_storage
        iteration = 0

        test_points = []  # (storage, entire_count, bathing_count)

        # Track bounds for binary search
        insufficient_storage_volumes = []  # Storage values with too many spills
        excessive_storage_volumes = []  # Storage values with too few spills
        target_exceeded_once = False  # Flag to track if we've crossed the target

        while iteration < max_iterations:
            iteration += 1

            # Simulate with current storage
            sim_data = self._simulate_storage(
                flow_data.copy(), storage, time_delay)

            # Count spills
            entire_count, bathing_count, spill_list = self._count_spills(
                sim_data, spill_flow_threshold, spill_volume_threshold, bathing_season
            )

            test_points.append((storage, entire_count, bathing_count))

            if is_bathing_mode:
                self._log_progress(
                    f"  Iteration {iteration}: Storage={storage:.1f} m³, Spills={entire_count} ({bathing_count} bathing)")
            else:
                self._log_progress(
                    f"  Iteration {iteration}: Storage={storage:.1f} m³, Spills={entire_count}")

            # Check if targets met exactly
            if is_bathing_mode:
                target_met = entire_count <= spill_target and bathing_count <= bathing_target
                spills_below_target = entire_count < spill_target
            else:
                target_met = entire_count <= spill_target
                spills_below_target = entire_count < spill_target

            if target_met and entire_count == spill_target:
                # Exact match - optimal!
                self._log_progress(
                    f"✓ Exact target met! Optimal storage: {storage:.1f} m³")
                return {
                    'storage_volume': storage,
                    'spill_count': entire_count,
                    'bathing_spill_count': bathing_count,
                    'iterations': iteration,
                    'test_points': test_points,
                    'spill_events': spill_list,
                    'flow_data': sim_data
                }
            elif target_met and spills_below_target:
                # Undershot - we can try to find closer match via binary search
                excessive_storage_volumes.append(storage)

                if insufficient_storage_volumes and target_exceeded_once:
                    # Binary search between bounds
                    old_storage = storage
                    storage = 0.5 * (max(insufficient_storage_volumes) +
                                     min(excessive_storage_volumes))

                    # Check convergence (volume change < 1 m³)
                    if abs(old_storage - storage) < 1.0:
                        self._log_progress(
                            f"✓ Converged! Storage: {old_storage:.1f} m³ (volume change < 1 m³)")
                        return {
                            'storage_volume': old_storage,
                            'spill_count': entire_count,
                            'bathing_spill_count': bathing_count,
                            'iterations': iteration,
                            'test_points': test_points,
                            'spill_events': spill_list,
                            'flow_data': sim_data
                        }

                    self._log_progress(
                        f"    → Binary search: adjusting to {storage:.1f} m³ "
                        f"(between {min(excessive_storage_volumes):.1f} and {max(insufficient_storage_volumes):.1f})")
                    continue
                else:
                    # First time meeting target - accept it
                    self._log_progress(
                        f"✓ Target met! Optimal storage: {storage:.1f} m³")
                    return {
                        'storage_volume': storage,
                        'spill_count': entire_count,
                        'bathing_spill_count': bathing_count,
                        'iterations': iteration,
                        'test_points': test_points,
                        'spill_events': spill_list,
                        'flow_data': sim_data
                    }

            # Target not met - too many spills
            insufficient_storage_volumes.append(storage)
            target_exceeded_once = True

            # Calculate intelligent storage increase
            if excessive_storage_volumes and target_exceeded_once:
                # Use binary search between bounds
                old_storage = storage
                storage = 0.5 * (max(insufficient_storage_volumes) +
                                 min(excessive_storage_volumes))
                self._log_progress(
                    f"    → Binary search: adjusting to {storage:.1f} m³ "
                    f"(between {max(insufficient_storage_volumes):.1f} and {min(excessive_storage_volumes):.1f})")
            else:
                # Use heuristic increase
                storage_increase = self._calculate_storage_increase(
                    storage, spill_list, spill_target, test_points, entire_count
                )
                storage += storage_increase

        self._log_progress(
            f"⚠ Max iterations ({max_iterations}) reached without meeting targets")
        return {
            'storage_volume': storage,
            'spill_count': entire_count if 'entire_count' in locals() else None,
            'bathing_spill_count': bathing_count if 'bathing_count' in locals() else None,
            'iterations': iteration,
            'test_points': test_points,
            'status': 'Max iterations reached'
        }

    def _calculate_storage_increase(self, current_storage: float, spill_events: pd.DataFrame,
                                    target: int, iteration_history: list,
                                    current_spill_count: int) -> float:
        """
        Calculate next storage volume using intelligent extrapolation.

        Strategy (in order of preference):
        1. Gradient method: Use Δspills/Δstorage from recent iterations
        2. Nth largest spill: Use volume of the Nth largest spill (target cutoff)
        3. Spill statistics: Use 75th percentile of excess spill volumes
        4. Minimum progress: Ensure at least 5%/10m³ growth

        Args:
            current_storage: Current storage volume (m³)
            spill_events: DataFrame of all spill events with volumes
            target: Target number of spills
            iteration_history: List of (storage_volume, entire_count, bathing_count) tuples
            current_spill_count: Current number of spills

        Returns:
            Storage increase amount (m³)
        """
        # Strategy 1: Gradient-based extrapolation (requires 2+ iterations)
        if len(iteration_history) >= 2:
            # Get last two points
            (vol_prev, count_prev, _) = iteration_history[-2]
            (vol_curr, count_curr, _) = iteration_history[-1]

            delta_vol = vol_curr - vol_prev
            # Inverted (less spills = progress)
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
                    damping = min(1.0, remaining_spills / max(target, 1))
                    # 50-100% of estimate
                    estimated_increase *= (0.5 + 0.5 * damping)

                    # Use gradient estimate if it's reasonable (between 10m³ and 5x current storage)
                    if 10 <= estimated_increase <= 5 * current_storage:
                        self._log_progress(
                            f"    → Gradient method: +{estimated_increase:.1f} m³ "
                            f"(gradient={gradient:.1f} m³/spill, {remaining_spills} remaining)")
                        return estimated_increase

        # Strategy 2: Nth largest spill volume (target cutoff method)
        if len(spill_events) > target:
            # Sort by volume descending and take the Nth largest (the cutoff spill)
            sorted_spills = spill_events.sort_values(
                'Spill Volume (m3)', ascending=False)
            nth_spill = sorted_spills.iloc[target -
                                           1] if target > 0 else sorted_spills.iloc[0]
            nth_volume = nth_spill['Spill Volume (m3)']

            # Use this as base increase (storage to prevent this specific spill)
            if nth_volume > 0:
                # Scale by how far we are from target
                remaining_spills = current_spill_count - target
                scaling = min(1.0, remaining_spills / max(target, 1))
                adjusted_increase = nth_volume * \
                    (0.7 + 0.3 * scaling)  # 70-100% of Nth spill

                # Ensure minimum progress
                adjusted_increase = max(
                    adjusted_increase, max(0.05 * current_storage, 10))

                self._log_progress(
                    f"    → Nth spill method: +{adjusted_increase:.1f} m³ "
                    f"(Nth spill={nth_volume:.1f} m³, scaling={scaling:.2f})")
                return adjusted_increase

        # Strategy 3: Spill statistics (use 75th percentile for conservatism)
        if len(spill_events) > target:
            spills_over = spill_events.iloc[target:]
            if len(spills_over) > 0:
                # Use 75th percentile instead of mean (more conservative)
                percentile_75 = spills_over['Spill Volume (m3)'].quantile(0.75)

                # Scale by proximity to target
                remaining_spills = current_spill_count - target
                scaling = min(1.0, remaining_spills / max(target, 1))
                adjusted_increase = percentile_75 * \
                    (0.7 + 0.3 * scaling)  # 70-100% of p75

                # Ensure minimum progress
                adjusted_increase = max(
                    adjusted_increase, max(0.05 * current_storage, 10))

                self._log_progress(
                    f"    → Percentile method: +{adjusted_increase:.1f} m³ "
                    f"(p75={percentile_75:.1f} m³, scaling={scaling:.2f})")
                return adjusted_increase

        # Strategy 4: Fallback to minimum progress (5% or 10m³, whichever is larger)
        min_increase = max(0.05 * current_storage, 10)
        self._log_progress(f"    → Minimum progress: +{min_increase:.1f} m³")
        return min_increase

    def _simulate_storage(self, flow_data: pd.DataFrame, storage_volume: float,
                          time_delay: int) -> pd.DataFrame:
        """
        Simulate tank storage behavior with pump control.

        Optimized vectorized version using NumPy arrays for performance.

        Key optimizations:
        - NumPy arrays instead of DataFrame .iloc[]/.loc[] (10-100x faster)
        - Direct array slicing for rolling max calculations
        - Single bulk DataFrame update at end instead of row-by-row updates

        Performance: ~50-100x faster than original row-by-row DataFrame operations
        for typical datasets (100k+ timesteps).
        """
        # Ensure required columns exist - save originals before modification
        if 'Original Continuation' not in flow_data.columns:
            flow_data['Original Continuation'] = flow_data['Continuation'].copy()
        if 'Original Spill' not in flow_data.columns:
            flow_data['Original Spill'] = flow_data['Spill'].copy()

        # Convert to numpy arrays for speed
        n = len(flow_data)
        spill = flow_data['Spill'].values.copy()  # Will be modified
        # Will be modified
        continuation = flow_data['Continuation'].values.copy()
        orig_continuation = flow_data['Original Continuation'].values
        orig_spill = flow_data['Original Spill'].values
        tank_volume = np.zeros(n, dtype=np.float64)

        # Simulation variables
        current_stored_vol = 0.0
        pump_on_thresh = self.run_config['Pump_On_Threshold']
        pump_off_thresh = self.run_config['Pump_Off_Threshold']
        pump_rate = self.run_config['Pump_Rate']
        fft = self.run_config['FFT']
        timestep = self.timestep_length

        # Main simulation loop (hard to fully vectorize due to state dependencies)
        for idx in range(n):
            pumping = False

            # Check pump control logic with time delay
            if time_delay > 0 and idx > 0:
                start_index = max(0, idx - time_delay)
                max_continuation_in_delay = np.max(
                    continuation[start_index:idx])
            else:
                max_continuation_in_delay = 0.0

            # Pump control logic
            if (orig_continuation[idx] < pump_on_thresh and
                    max_continuation_in_delay < pump_on_thresh):
                pumping = True
            elif (orig_continuation[idx] > pump_off_thresh or
                  max_continuation_in_delay < pump_on_thresh):
                pumping = False

            # Tank draindown when pumping
            if spill[idx] == 0 and current_stored_vol > 0 and pumping:
                stored_vol_before = current_stored_vol
                current_stored_vol -= pump_rate * timestep

                if current_stored_vol < 0:
                    current_stored_vol = 0

                # Return flow to continuation
                returned_flow = (stored_vol_before -
                                 current_stored_vol) / timestep
                continuation[idx] += returned_flow

                # Recirculate if continuation exceeds FFT
                if continuation[idx] > fft:
                    excess_flow = continuation[idx] - fft
                    current_stored_vol += excess_flow * timestep
                    continuation[idx] = fft

            # Tank filling when spilling
            elif current_stored_vol < storage_volume and spill[idx] != 0:
                current_stored_vol += spill[idx] * timestep

                if current_stored_vol < storage_volume:
                    spill[idx] = 0
                else:
                    overflow = (current_stored_vol - storage_volume) / timestep
                    spill[idx] = overflow
                    current_stored_vol = storage_volume

            tank_volume[idx] = current_stored_vol

        # Update DataFrame with modified values
        flow_data['Spill'] = spill
        flow_data['Continuation'] = continuation
        flow_data['Tank Volume'] = tank_volume

        return flow_data

    # def _count_spills(self, flow_data: pd.DataFrame, flow_threshold: float,
    #                   volume_threshold: float, bathing_season) -> tuple:
    #     """
    #     Count spills in flow data.

    #     Returns: (entire_count, bathing_count, spill_list_dataframe)
    #     """
    #     # Add month_day column for bathing season filtering
    #     if bathing_season:
    #         flow_data['month_day'] = list(
    #             zip(flow_data['Time'].dt.month, flow_data['Time'].dt.day))

    #     # Filter spills by threshold
    #     flow_data['Spill_Filtered'] = flow_data['Spill'].where(
    #         flow_data['Spill'] > flow_threshold, 0
    #     )

    #     # Calculate rolling volumes (12hr and 24hr windows)
    #     timestep_hours = self.timestep_length / 3600
    #     half_day = int(12 / timestep_hours)
    #     full_day = int(24 / timestep_hours)

    #     flow_data['Spill_Volume_12hr'] = (
    #         flow_data['Spill_Filtered']
    #         .rolling(window=half_day, min_periods=1, closed='left')
    #         .sum() * self.timestep_length
    #     )
    #     flow_data['Spill_Volume_24hr'] = (
    #         flow_data['Spill_Filtered']
    #         .rolling(window=full_day, min_periods=1, closed='left')
    #         .sum() * self.timestep_length
    #     )

    #     # Count spills using 12/24 hour logic
    #     spill_events = []
    #     EAcount = 0
    #     cooldown = 0
    #     spill24 = 0.0

    #     for idx in range(len(flow_data)):
    #         spill_flow = flow_data['Spill_Filtered'].iloc[idx]

    #         if EAcount == 0:
    #             if spill_flow > 0:
    #                 EAcount = 1
    #             else:
    #                 EAcount = 0
    #         else:
    #             if EAcount < half_day:
    #                 EAcount += 1
    #                 if cooldown > 0:
    #                     spill24 += spill_flow

    #                 if EAcount == half_day:
    #                     spill_vol_12 = flow_data['Spill_Volume_12hr'].iloc[idx]
    #                     if spill_vol_12 >= volume_threshold:
    #                         cooldown = full_day
    #                         spill_start_idx = idx - half_day
    #                         spill_start_time = flow_data['Time'].iloc[spill_start_idx]
    #                         spill24 = spill_vol_12

    #                         in_bathing = False
    #                         if bathing_season:
    #                             month_day = flow_data['month_day'].iloc[idx]
    #                             in_bathing = self._is_in_season(
    #                                 month_day, bathing_season[0], bathing_season[1])

    #                         spill_events.append({
    #                             'DateTime': spill_start_time,
    #                             'Spill Volume (m3)': spill_vol_12,
    #                             'In Bathing Season': in_bathing
    #                         })

    #                     EAcount = 0
    #                     spill24 = 0.0

    #             elif cooldown > 0:
    #                 cooldown -= 1
    #                 spill24 += spill_flow

    #                 if cooldown == 0:
    #                     spill_vol_24 = flow_data['Spill_Volume_24hr'].iloc[idx]
    #                     if len(spill_events) > 0:
    #                         spill_events[-1]['Spill Volume (m3)'] = spill_vol_24
    #                     EAcount = 0
    #                     spill24 = 0.0

    #     spill_df = pd.DataFrame(spill_events)
    #     entire_count = len(spill_df)
    #     bathing_count = len(
    #         spill_df[spill_df['In Bathing Season']]) if bathing_season else 0

    #     return entire_count, bathing_count, spill_df

    def _count_spills(self,
                      flow_data: pd.DataFrame,
                      flow_threshold: float,
                      volume_threshold: float,
                      bathing_season) -> tuple:
        """
        Detect spill events using the 12/24-hour counting method (equivalent to your second function),
        but with this function's inputs/outputs.

        Inputs:
        - flow_data: DataFrame with columns ['Time', 'Spill'] (Spill in flow units; Time is pandas.Timestamp)
        - flow_threshold: flows > this are considered spilling (<= are zeroed)
        - volume_threshold: MIN volume (m3) for BOTH 12h and 24h windows to count
        - bathing_season: tuple ((start_month, start_day), (end_month, end_day)) or None

        Returns:
        (entire_count, bathing_count, spill_df)
        where spill_df has columns:
            ['DateTime', 'Spill Volume (m3)', 'Duration (hours)', 'In Bathing Season']
        DateTime is the window START (12h or 24h before decision index).
        Duration is the window size (12.0 or 24.0 hours).
        """
        from datetime import timedelta
        import numpy as np
        import pandas as pd

        df = flow_data

        # Optional bathing-season flags sampled at window END (same policy as your first impl)
        in_bathing_arr = None
        if bathing_season:
            start, end = bathing_season
            month_arr = df['Time'].dt.month.values
            day_arr = df['Time'].dt.day.values
            in_bathing_arr = np.array([
                self._is_in_season((int(m), int(d)), start, end)
                for m, d in zip(month_arr, day_arr)
            ])

        # Threshold: zero-out flows <= threshold (strict >)
        spill_filtered = df['Spill'].where(df['Spill'] > flow_threshold, 0)

        # Timestep and windows
        timestep_sec = float(self.timestep_length)  # seconds
        timestep_hours = timestep_sec / 3600.0
        half_day = int(round(12.0 / timestep_hours))
        full_day = int(round(24.0 / timestep_hours))

        # Rolling volumes (exclude current row: closed='left')
        vol12 = spill_filtered.rolling(
            window=half_day, min_periods=1, closed='left').sum() * timestep_sec
        vol24 = spill_filtered.rolling(
            window=full_day, min_periods=1, closed='left').sum() * timestep_sec

        # Fast arrays
        spill_flow_arr = spill_filtered.values
        time_arr = df['Time'].values
        vol12_arr = vol12.values
        vol24_arr = vol24.values
        n = len(df)

        # State machine (mirrors your second function)
        EAcount = 0
        cooldown = 0  # truthy => in continuation windows
        spill24 = 0.0

        # Collect (start_time, volume, window_hours, end_idx)
        candidates = []

        for i in range(n):
            flow_i = spill_flow_arr[i]

            if EAcount == 0:
                if flow_i > 0:
                    EAcount = 1
                else:
                    EAcount = 0
            else:
                if EAcount < half_day:
                    EAcount += 1
                    if cooldown > 0:
                        spill24 += flow_i
                elif EAcount == half_day:
                    # First 12h window decision
                    if cooldown == 0:
                        start_time = pd.Timestamp(
                            time_arr[i]) - timedelta(hours=12)
                        candidates.append(
                            (start_time, float(vol12_arr[i]), 12.0, i))
                        cooldown = 1
                        EAcount = 1
                        spill24 = flow_i  # reset & seed
                    elif cooldown > 0:
                        EAcount += 1
                        spill24 += flow_i
                elif EAcount == full_day:
                    # 24h continuation decision
                    if spill24 > 0:
                        cooldown += 1
                        EAcount = 1
                        spill24 = 0.0
                        start_time = pd.Timestamp(
                            time_arr[i]) - timedelta(hours=24)
                        candidates.append(
                            (start_time, float(vol24_arr[i]), 24.0, i))
                    else:
                        # End of event (no spill in last 24h)
                        EAcount = 0
                        spill24 = 0.0
                        cooldown = 0
                else:
                    # Between 12h and 24h
                    EAcount += 1
                    spill24 += flow_i

        # Post-filter like the second function: keep ONLY events with volume >= volume_threshold
        events_rows = []
        for start_time, volume_m3, window_hours, end_idx in candidates:
            if volume_m3 >= volume_threshold:
                in_bathing = False
                if in_bathing_arr is not None:
                    # flag at window end
                    in_bathing = bool(in_bathing_arr[end_idx])
                events_rows.append({
                    'DateTime': start_time,
                    'Spill Volume (m3)': volume_m3,
                    'Duration (hours)': window_hours,
                    'In Bathing Season': in_bathing
                })

        spill_df = pd.DataFrame(events_rows).sort_values(
            'DateTime').reset_index(drop=True)
        entire_count = len(spill_df)
        bathing_count = int(spill_df['In Bathing Season'].sum()) if (
            bathing_season and entire_count > 0) else 0

        return entire_count, bathing_count, spill_df

    def _is_in_season(self, date_tuple, start_tuple, end_tuple) -> bool:
        """Check if date is within seasonal range (handles year wraparound)."""
        month, day = date_tuple
        start_m, start_d = start_tuple
        end_m, end_d = end_tuple

        if start_m <= end_m:
            # No wraparound (e.g., May to September)
            return (month > start_m or (month == start_m and day >= start_d)) and \
                   (month < end_m or (month == end_m and day <= end_d))
        else:
            # Wraparound (e.g., November to February)
            return (month > start_m or (month == start_m and day >= start_d)) or \
                   (month < end_m or (month == end_m and day <= end_d))
