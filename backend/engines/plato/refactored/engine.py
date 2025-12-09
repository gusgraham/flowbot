"""
Refactored storage analysis engine.
Clean implementation with better separation of concerns.
"""

import glob
import logging
import os
import pandas as pd
import numpy as np
# from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple
# from pathlib import Path

from .models import CSOConfiguration, SpillEvent, CSOAnalysisResult
from .config import DataSourceInfo, ScenarioSettings


class StorageAnalyzer:
    """
    Core storage analysis engine - refactored from legacy Overflow class.
    Cleaner separation: data loading → simulation → output.
    """

    def __init__(self,
                 config: CSOConfiguration,
                 data_source: DataSourceInfo,
                 scenario: ScenarioSettings,
                 progress_callback=None):
        self.config = config
        self.data_source = data_source
        self.scenario = scenario
        # Optional callback for progress updates
        self.progress_callback = progress_callback

        # Time series data (loaded on demand)
        self.flow_data: Optional[pd.DataFrame] = None

    def _log(self, message: str):
        """Send progress message if callback provided."""
        if self.progress_callback:
            self.progress_callback(message)

    def _get_date_parser_kwargs(self) -> dict:
        """
        Get pandas date parsing kwargs based on configured date format from data_source.

        Returns:
            Dictionary of kwargs to pass to pd.read_csv for date parsing.
            Uses explicit format if configured, otherwise uses dayfirst=True.
        """
        date_format = getattr(self.data_source, 'date_format', None)
        if date_format:
            # Use explicit format for speed
            return {
                'parse_dates': ['Time'],
                'date_format': date_format
            }
        else:
            # Use dayfirst auto-detection (slower but flexible)
            return {
                'parse_dates': ['Time'],
                'dayfirst': True
            }

    def run(self) -> CSOAnalysisResult:
        """Execute full analysis and return structured result."""

        # Step 1: Load and prepare data
        self._log(f"  Loading data for {self.config.cso_name}...")
        self._load_data()

        # Step 2: Apply PFF increase if specified
        if self.config.pff_increase > 0:
            self._log(
                f"  Applying PFF increase of {self.config.pff_increase} m³/s...")
            self._apply_pff_increase()

        # Step 3: Iterate to find required storage
        self._log("  Finding optimal storage volume...")
        final_storage, iterations = self._iterate_storage()

        # Step 4: Run final simulation with optimal storage
        self._log(
            f"  Running final simulation with {final_storage:.1f} m³ storage...")
        self._simulate_storage(final_storage)

        # Step 5: Detect and analyze spills
        self._log("  Detecting spill events...")
        spill_events = self._detect_spills()

        # Step 6: Calculate statistics
        bathing_spills = [
            e for e in spill_events
            if e.is_in_bathing_season(
                self.config.bathing_season_start.month,
                self.config.bathing_season_start.day,
                self.config.bathing_season_end.month,
                self.config.bathing_season_end.day
            )
        ]

        # Log final spill count for comparison
        if self.config.spill_target_bathing >= 0:
            bathing_count = len(bathing_spills)
            self._log(
                f"  Final result: {len(spill_events)} spills ({bathing_count} bathing) "
                f"with {final_storage:.1f} m³ storage"
            )
        else:
            self._log(
                f"  Final result: {len(spill_events)} spills with {final_storage:.1f} m³ storage"
            )

        total_spill_vol = sum(e.volume_m3 for e in spill_events)
        bathing_spill_vol = sum(e.volume_m3 for e in bathing_spills)
        total_duration = sum(e.spill_duration_hours for e in spill_events)
        bathing_duration = sum(e.spill_duration_hours for e in bathing_spills)

        # Check convergence: must meet both targets (if bathing target is set)
        converged = len(spill_events) <= self.config.spill_target_entire
        if self.config.spill_target_bathing >= 0:
            converged = converged and (
                len(bathing_spills) <= self.config.spill_target_bathing)

        return CSOAnalysisResult(
            cso_name=self.config.cso_name,
            run_suffix=self.config.run_suffix,
            converged=converged,
            iterations_count=iterations,
            final_storage_m3=final_storage,
            spill_count=len(spill_events),
            bathing_spills_count=len(bathing_spills),
            total_spill_volume_m3=total_spill_vol,
            bathing_spill_volume_m3=bathing_spill_vol,
            total_spill_duration_hours=total_duration,
            bathing_spill_duration_hours=bathing_duration,
            spill_events=spill_events,
            time_series=self.flow_data.copy(),
            analysis_date=datetime.now(),
        )

    def _load_data(self):
        """Load and filter time series data."""
        import glob
        import os

        data_folder = str(self.data_source.data_folder)

        # Check if we need to build effective series first
        overflow_is_effective = self.config.overflow_link.startswith(
            "Effective(")
        cont_is_effective = self.config.continuation_link.startswith(
            "Effective(")

        # Build effective series if needed
        effective_data = None
        if overflow_is_effective or cont_is_effective:
            self._log("  Building effective link series...")
            self._log(
                f"    Overflow: {self.config.overflow_link} (effective: {overflow_is_effective})")
            self._log(
                f"    Continuation: {self.config.continuation_link} (effective: {cont_is_effective})")
            effective_data = self._build_effective_series()

        # Load flow data with column filtering to reduce memory usage
        # Note: cso_name is user-friendly (e.g., "Beech Ave CSO")
        # overflow_link is the actual column name in data files (e.g., "BS4334543.1")
        cso_col = self.config.overflow_link
        cont_col = self.config.continuation_link

        # Build list of required columns, excluding effective links
        # (they'll be added from effective_data merge)
        required_cols = ['Time']
        if not overflow_is_effective:
            required_cols.append(cso_col)
        if not cont_is_effective:
            required_cols.append(cont_col)

        if self.data_source.file_type == 'csv':
            # Look for both standard (_Q) and ICM default (_us_flow) naming
            flow_files = sorted(
                glob.glob(os.path.join(data_folder, "*_Q.csv")))
            flow_files += sorted(glob.glob(os.path.join(data_folder, "*_us_flow.csv")))

            # Read only required columns to save memory
            # First, peek at columns to verify they exist
            first_file = flow_files[0] if flow_files else None
            if first_file:
                # Check available columns
                available_cols = pd.read_csv(
                    first_file, nrows=0).columns.tolist()

                # Verify required columns exist (excluding effective links)
                missing_cols = [
                    col for col in required_cols if col not in available_cols]
                if missing_cols:
                    raise ValueError(
                        f"Required columns not found in data: {missing_cols}. "
                        f"Available columns: {available_cols[:10]}..."
                    )

                logging.info(f"Loading only {len(required_cols)} columns from CSV "
                             f"(file has {len(available_cols)} columns total)")

                # Load only required columns
                date_kwargs = self._get_date_parser_kwargs()
                flow_dfs = [
                    pd.read_csv(f, usecols=required_cols, **date_kwargs)
                    for f in flow_files
                ]
            else:
                raise ValueError("No flow data files found")
        else:
            raise NotImplementedError(
                f"File type {self.data_source.file_type} not yet supported")

        # Merge all flow files
        self.flow_data = pd.concat(flow_dfs, ignore_index=True)
        self.flow_data.drop_duplicates(
            subset=['Time'], keep='first', inplace=True)
        self.flow_data.sort_values('Time', inplace=True)

        # Merge effective series data if it was created
        if effective_data is not None:
            self.flow_data = pd.merge(
                self.flow_data, effective_data, on='Time', how='left')

        # Filter to date range
        self.flow_data = self.flow_data[
            (self.flow_data['Time'] >= self.config.start_date) &
            (self.flow_data['Time'] <= self.config.end_date)
        ].reset_index(drop=True)

        logging.info(f"Loaded {len(self.flow_data):,} timesteps for analysis")

        # Clean up negative/negligible flows
        self.flow_data[cso_col] = self.flow_data[cso_col].clip(lower=0)

        # Add working columns
        self.flow_data['Tank_Volume'] = 0.0
        self.flow_data['Spill_Flow'] = self.flow_data[cso_col].copy()

        # Store original flows before any modifications (for simulation iterations)
        self.flow_data['CSO_Flow_Original'] = self.flow_data[cso_col].copy()
        self.flow_data['Cont_Flow_Original'] = self.flow_data[cont_col].copy()

        # Calculate time delay for draindown checks (legacy requirement)
        time_delay_steps = int(self.config.time_delay *
                               3600 / self.data_source.timestep_seconds)
        if time_delay_steps == 0:
            self.flow_data['Spill_in_Time_Delay'] = 0.0
        else:
            self.flow_data['Spill_in_Time_Delay'] = (
                self.flow_data[cont_col]
                .rolling(window=time_delay_steps, min_periods=1)
                .max()
            )

    def _build_effective_series(self) -> Optional[pd.DataFrame]:
        """Build effective link series from component links."""

        data_folder = str(self.data_source.data_folder)

        # Parse which links need to be combined
        overflow_components = None
        cont_components = None

        overflow_link = self.config.overflow_link
        cont_link = self.config.continuation_link

        if overflow_link.startswith("Effective(") and overflow_link.endswith(")"):
            # Extract component links from "Effective(link1, link2, ...)"
            # Remove "Effective(" and ")"
            components_str = overflow_link[10:-1]
            overflow_components = [c.strip()
                                   for c in components_str.split(',')]

        if cont_link.startswith("Effective(") and cont_link.endswith(")"):
            components_str = cont_link[10:-1]
            cont_components = [c.strip() for c in components_str.split(',')]

        if not overflow_components and not cont_components:
            return None

        # Collect all component links we need
        all_components = set()
        if overflow_components:
            all_components.update(overflow_components)
        if cont_components:
            all_components.update(cont_components)

        # Load flow data for all component links
        if self.data_source.file_type == 'csv':
            # Look for both standard (_Q) and ICM default (_us_flow) naming
            flow_files = sorted(
                glob.glob(os.path.join(data_folder, "*_Q.csv")))
            flow_files += sorted(glob.glob(os.path.join(data_folder, "*_us_flow.csv")))

            # Load only the component columns we need
            flow_dfs = []
            date_kwargs = self._get_date_parser_kwargs()
            for f in flow_files:
                available_cols = pd.read_csv(f, nrows=0).columns.tolist()
                needed_cols = ['Time'] + \
                    [c for c in all_components if c in available_cols]
                if len(needed_cols) > 1:  # Has Time + at least one component
                    df = pd.read_csv(f, usecols=needed_cols, **date_kwargs)
                    flow_dfs.append(df)

            if not flow_dfs:
                raise ValueError(
                    f"Component links not found in data: {all_components}")

            # Merge all component data
            component_data = flow_dfs[0]
            for df in flow_dfs[1:]:
                component_data = pd.merge(
                    component_data, df, on='Time', how='outer')

            component_data.sort_values('Time', inplace=True)
            component_data.drop_duplicates(
                subset=['Time'], keep='first', inplace=True)
        else:
            raise NotImplementedError(
                f"File type {self.data_source.file_type} not yet supported")

        # Build effective series
        effective_df = pd.DataFrame({'Time': component_data['Time']})

        if overflow_components:
            # Sum flows for overflow effective link
            missing = [
                c for c in overflow_components if c not in component_data.columns]
            if missing:
                raise ValueError(
                    f"Overflow component links not found in data: {missing}")
            effective_df[overflow_link] = component_data[overflow_components].sum(
                axis=1)
            self._log(
                f"    Created effective overflow link from {len(overflow_components)} components")

        if cont_components:
            # Sum flows for continuation effective link
            missing = [
                c for c in cont_components if c not in component_data.columns]
            if missing:
                raise ValueError(
                    f"Continuation component links not found in data: {missing}")
            effective_df[cont_link] = component_data[cont_components].sum(
                axis=1)
            self._log(
                f"    Created effective continuation link from {len(cont_components)} components")

        return effective_df

    def _apply_pff_increase(self):
        """Reduce CSO flow by PFF increase amount."""
        # Modify the ORIGINAL columns (these will be used in subsequent iterations)
        # The simulation will read from CSO_Flow_Original and Cont_Flow_Original
        original_cso = self.flow_data['CSO_Flow_Original'].copy()
        original_cont = self.flow_data['Cont_Flow_Original'].copy()

        # Reduce CSO flow by PFF increase
        reduced_cso = (original_cso - self.config.pff_increase).clip(lower=0)

        # Add diverted flow to continuation
        diverted = original_cso - reduced_cso
        increased_cont = original_cont + diverted

        # Update the original columns with PFF-modified values
        self.flow_data['CSO_Flow_Original'] = reduced_cso
        self.flow_data['Cont_Flow_Original'] = increased_cont

    def _iterate_storage(self, max_iterations: int = 50) -> Tuple[float, int]:
        """
        Smart iterative search to find minimum storage that achieves spill target.
        Uses hybrid approach:
        - Linear interpolation based on spill count gradient (fast convergence)
        - Bounded search with adaptive expansion (handles edge cases)
        - Early exit on exact match

        Returns (storage_volume, iteration_count).
        """
        if self.config.tank_volume is not None:
            # Fixed storage mode
            self._log(
                f"    Using fixed storage volume: {self.config.tank_volume:.1f} m³")
            return self.config.tank_volume, 0

        # Run baseline analysis (no storage) to understand spill distribution
        self._log(f"    Running baseline analysis (no storage)...")
        self._simulate_storage(0.0)
        baseline_spills = self._detect_spills()

        if len(baseline_spills) == 0:
            # Already meets target with no storage
            self._log(f"    ✓ No spills detected - no storage required")
            return 0.0, 0

        # Sort by volume (largest first)
        spill_volumes = sorted(
            [s.volume_m3 for s in baseline_spills], reverse=True)

        if len(spill_volumes) <= self.config.spill_target_entire:
            # Already meets target with no storage
            self._log(
                f"    ✓ Only {len(spill_volumes)} spills (target: {self.config.spill_target_entire}) - no storage required")
            return 0.0, 0

        # Log baseline condition
        is_bathing_mode = self.config.spill_target_bathing >= 0

        if is_bathing_mode:
            # Count baseline bathing spills
            baseline_bathing_spills = [
                s for s in baseline_spills
                if s.is_in_bathing_season(
                    self.config.bathing_season_start.month,
                    self.config.bathing_season_start.day,
                    self.config.bathing_season_end.month,
                    self.config.bathing_season_end.day
                )
            ]
            self._log(
                f"    Baseline: {len(baseline_spills)} spills ({len(baseline_bathing_spills)} bathing), "
                f"targets: {self.config.spill_target_entire} entire / {self.config.spill_target_bathing} bathing")
        else:
            # Default mode - don't count bathing spills
            self._log(
                f"    Baseline: {len(baseline_spills)} spills (target: {self.config.spill_target_entire})")

        # HEURISTIC: Use Nth-largest spill volume as center estimate
        nth_spill_volume = spill_volumes[self.config.spill_target_entire - 1]

        # Initialize search with heuristic
        storage_min = nth_spill_volume * 0.5
        storage_max = nth_spill_volume * 2.0

        self._log(
            f"    {self.config.spill_target_entire}th largest spill volume: {nth_spill_volume:.1f} m³, "
            f"starting search space: [{storage_min:.1f}, {storage_max:.1f}] m³"
        )

        # Tolerance for convergence (matches legacy)
        tolerance = 1.0  # m³ (legacy uses 1 m³)
        # Relaxed tolerance for expansion decisions (avoid premature expansion)
        expansion_tolerance = 10.0  # m³

        # Track test points for interpolation
        # Format: [(storage, spill_count), ...]
        test_points = []

        # Track when we find a solution meeting the target
        solution_found = False
        solution_storage = None

        for iteration in range(1, max_iterations + 1):
            # Choose next test point using interpolation if we have enough data
            if len(test_points) >= 2:
                # Use linear interpolation between best bracketing points
                storage_test = self._interpolate_next_storage(
                    test_points, self.config.spill_target_entire, storage_min, storage_max
                )
                # Check if interpolation suggests a value we've already tested
                # (can happen with dual constraints when one is met but not the other)
                already_tested = any(abs(s - storage_test)
                                     < 0.1 for s, _, _ in test_points)
                if already_tested:
                    # Fall back to midpoint to make progress
                    storage_test = (storage_min + storage_max) / 2.0
            else:
                # First iterations: use midpoint
                storage_test = (storage_min + storage_max) / 2.0

            # Test this storage volume
            self._simulate_storage(storage_test)
            spill_events = self._detect_spills()
            spill_count = len(spill_events)

            # Count bathing season spills if applicable
            bathing_spill_count = 0
            if self.config.spill_target_bathing >= 0:
                bathing_spills = [
                    e for e in spill_events
                    if e.is_in_bathing_season(
                        self.config.bathing_season_start.month,
                        self.config.bathing_season_start.day,
                        self.config.bathing_season_end.month,
                        self.config.bathing_season_end.day
                    )
                ]
                bathing_spill_count = len(bathing_spills)

            # Record this test point (track both counts for logging/interpolation)
            test_points.append(
                (storage_test, spill_count, bathing_spill_count))

            # Log progress
            if iteration % 2 == 0 or iteration <= 3:
                if self.config.spill_target_bathing >= 0:
                    self._log(
                        f"    Iteration {iteration}: {storage_test:.1f} m³ → "
                        f"{spill_count} spills ({bathing_spill_count} bathing)")
                else:
                    self._log(
                        f"    Iteration {iteration}: {storage_test:.1f} m³ → {spill_count} spills")

            # Determine if this storage meets the target(s)
            meets_entire_target = spill_count <= self.config.spill_target_entire
            meets_bathing_target = (
                self.config.spill_target_bathing < 0 or
                bathing_spill_count <= self.config.spill_target_bathing
            )
            meets_all_targets = meets_entire_target and meets_bathing_target

            # Update bounds based on spill count
            # Goal: minimize storage while meeting all constraints
            if meets_all_targets:
                # Storage is sufficient (meets all constraints)
                # Try smaller storage to minimize cost
                storage_max = storage_test

                # Check if we've hit the target exactly (for either method 1 or 4)
                # Method 1: Check if entire period target hit exactly
                # Method 4: Check if either target hit exactly
                at_entire_target = (
                    spill_count == self.config.spill_target_entire)
                at_bathing_target = (
                    self.config.spill_target_bathing >= 0 and
                    bathing_spill_count == self.config.spill_target_bathing
                )

                # Trigger refinement when we hit target exactly
                # Method 1: entire target only
                # Method 4: either entire or bathing target
                should_refine = at_entire_target or at_bathing_target

                if should_refine:
                    # Found target(s) - now refine to find minimum storage
                    if not solution_found:
                        solution_found = True
                        if self.config.spill_target_bathing >= 0:
                            self._log(
                                f"    Targets achieved in {iteration} iterations: "
                                f"{storage_test:.1f} m³ → {spill_count} spills "
                                f"({bathing_spill_count} bathing)")
                        else:
                            self._log(
                                f"    Target achieved in {iteration} iterations: "
                                f"{storage_test:.1f} m³ → {spill_count} spills")
                        self._log(
                            f"    Starting refinement to find minimum storage...")
                    # Do refinement to find minimum
                    final_storage, total_iterations = self._refine_minimum_storage(
                        storage_min, storage_max, iteration
                    )
                    return final_storage, total_iterations

                # Also check tight convergence for safety
                if storage_max - storage_min < tolerance:
                    # Already converged - return result
                    self._log(
                        f"    ✓ Converged in {iteration} iterations: "
                        f"{storage_test:.1f} m³ → {spill_count} spills")
                    return storage_test, iteration

            else:
                # Too little storage (too many spills)
                storage_min = storage_test

                # Check if we need to expand upper bound
                # Use relaxed tolerance for expansion to avoid premature expansion
                if storage_max - storage_min < expansion_tolerance:
                    # Estimate how much more storage we need based on gradient
                    expansion = self._estimate_expansion_needed(
                        test_points, self.config.spill_target_entire, storage_max
                    )
                    old_max = storage_max
                    storage_max = max(storage_max * 2.0,
                                      storage_max + expansion)
                    self._log(
                        f"    Expanding search space: [{storage_min:.1f}, {old_max:.1f}] → [{storage_min:.1f}, {storage_max:.1f}] m³"
                    )

        # Return best attempt
        self._log(
            f"    ! Max iterations reached ({max_iterations}), using {storage_max:.1f} m³")
        return storage_max, max_iterations

    def _refine_minimum_storage(
        self,
        storage_min: float,
        storage_max: float,
        iteration_offset: int
    ) -> Tuple[float, int]:
        """
        Refine the storage estimate to find the minimum storage that meets the spill target.

        After interpolation finds A solution, this performs a binary search downward
        to find THE MINIMUM solution (within 1 m³ tolerance).

        Args:
            storage_min: Lower bound (doesn't meet target)
            storage_max: Upper bound (meets target)
            iteration_offset: Number of iterations already performed

        Returns:
            Tuple of (minimum storage volume that meets the spill target, total iteration count)
        """
        self._log(f"  Phase 2: Refining to find minimum storage...")

        tolerance = 1.0  # m³
        max_refinement_iterations = 10

        for i in range(max_refinement_iterations):
            iteration = iteration_offset + i + 1

            # Check convergence
            if storage_max - storage_min < tolerance:
                self._log(
                    f"    ✓ Converged in {iteration} total iterations: "
                    f"{storage_max:.1f} m³ (minimized)")
                return storage_max, iteration

            # Binary search: test midpoint
            storage_test = (storage_min + storage_max) / 2.0

            # Simulate this storage
            self._simulate_storage(storage_test)
            spill_events = self._detect_spills()
            spill_count = len(spill_events)

            # Count bathing season spills if applicable
            bathing_spill_count = 0
            if self.config.spill_target_bathing >= 0:
                bathing_spills = [
                    e for e in spill_events
                    if e.is_in_bathing_season(
                        self.config.bathing_season_start.month,
                        self.config.bathing_season_start.day,
                        self.config.bathing_season_end.month,
                        self.config.bathing_season_end.day
                    )
                ]
                bathing_spill_count = len(bathing_spills)

            if self.config.spill_target_bathing >= 0:
                self._log(
                    f"  Iter {iteration}: Testing {storage_test:.1f} m³ → "
                    f"{spill_count} spills ({bathing_spill_count} bathing) "
                    f"(refining bounds [{storage_min:.1f}, {storage_max:.1f}])")
            else:
                self._log(
                    f"  Iter {iteration}: Testing {storage_test:.1f} m³ → "
                    f"{spill_count} spills (refining bounds [{storage_min:.1f}, {storage_max:.1f}])")

            # Determine if this storage meets the target(s)
            meets_entire_target = spill_count <= self.config.spill_target_entire
            meets_bathing_target = (
                self.config.spill_target_bathing < 0 or
                bathing_spill_count <= self.config.spill_target_bathing
            )
            meets_all_targets = meets_entire_target and meets_bathing_target

            # Update bounds
            if meets_all_targets:
                # Still meets target - can try smaller storage
                storage_max = storage_test
            else:
                # Too small - need more storage
                storage_min = storage_test

        # Return best attempt
        final_iteration = iteration_offset + max_refinement_iterations
        self._log(
            f"    ⚠ Refinement did not fully converge after {max_refinement_iterations} iterations. "
            f"Using {storage_max:.1f} m³")
        return storage_max, final_iteration

    def _interpolate_next_storage(
        self, test_points: list, target_spills: int,
        min_bound: float, max_bound: float
    ) -> float:
        """
        Use linear interpolation to estimate storage needed for target spills.
        Uses the two most recent bracketing points if available.
        Handles both single-target and dual-target (entire + bathing) modes.
        """
        # Extract just the storage and entire spill count for interpolation
        # test_points format: [(storage, entire_count, bathing_count), ...]
        # For interpolation, we primarily use the entire spill count
        points_for_interp = [(s, c) for s, c, _ in test_points]

        # Find best bracketing pair (one above target, one below)
        above_target = [(s, c)
                        for s, c in points_for_interp if c < target_spills]
        below_target = [(s, c)
                        for s, c in points_for_interp if c > target_spills]

        if above_target and below_target:
            # Get closest points on each side
            # Highest storage with too many spills
            p1 = max(below_target, key=lambda x: x[0])
            # Lowest storage with too few spills
            p2 = min(above_target, key=lambda x: x[0])

            s1, c1 = p1
            s2, c2 = p2

            # Linear interpolation: storage = s1 + (target - c1) * (s2-s1)/(c2-c1)
            if c2 != c1:
                interpolated = s1 + \
                    (target_spills - c1) * (s2 - s1) / (c2 - c1)
                # Clamp to bounds and add small safety margin
                return max(min_bound, min(max_bound, interpolated))

        # Fallback to midpoint
        return (min_bound + max_bound) / 2.0

    def _estimate_expansion_needed(
        self, test_points: list, target_spills: int, current_max: float
    ) -> float:
        """
        Estimate how much to expand the upper bound based on spill count gradient.
        """
        if len(test_points) < 2:
            return current_max  # Double it (handled by caller)

        # Extract storage and entire spill counts for gradient calculation
        # test_points format: [(storage, entire_count, bathing_count), ...]
        points_for_gradient = [(s, c) for s, c, _ in test_points]

        # Use the two highest storage tests to estimate gradient
        sorted_points = sorted(points_for_gradient,
                               key=lambda x: x[0], reverse=True)
        s1, c1 = sorted_points[0]
        s2, c2 = sorted_points[1] if len(
            sorted_points) > 1 else (s1 * 0.5, c1 * 2)

        if c1 == c2 or s1 == s2:
            return current_max  # Can't estimate, just double

        # Spills per m³ of storage
        gradient = (c2 - c1) / (s2 - s1)

        if gradient <= 0:
            return current_max  # Invalid gradient, just double

        # Estimate additional storage needed
        spills_to_eliminate = c1 - target_spills
        estimated_additional = spills_to_eliminate / gradient

        # Add 50% safety margin
        return estimated_additional * 1.5

    def _simulate_storage(self, storage_volume: float):
        """
        Run storage simulation with given tank volume.
        Updates flow_data in place with tank levels and modified spill flows.

        OPTIMIZED: Uses numpy arrays for 10-50x speedup over pandas .at[] calls.
        """
        cso_col = self.config.cso_name
        cont_col = self.config.continuation_link
        timestep_sec = self.data_source.timestep_seconds

        # Check if depth column exists (may not be present)
        depth_col = f"{cont_col}_Depth" if f"{cont_col}_Depth" in self.flow_data.columns else None

        # OPTIMIZATION: Extract to numpy arrays (avoids repeated pandas indexing)
        n_rows = len(self.flow_data)
        # Use ORIGINAL flows (post-PFF if applied) as the source for each iteration
        inflow_arr = self.flow_data['CSO_Flow_Original'].values.copy()
        # Need copy for modifications during simulation
        cont_flow_arr = self.flow_data['Cont_Flow_Original'].values.copy()
        cont_depth_arr = self.flow_data[depth_col].values if depth_col else np.full(
            n_rows, -1.0)
        spill_delay_arr = self.flow_data['Spill_in_Time_Delay'].values

        # Preallocate output arrays
        tank_volume_arr = np.zeros(n_rows, dtype=np.float64)
        spill_flow_arr = inflow_arr.copy()

        # State variable
        current_stored = 0.0

        # Main simulation loop - still sequential but using fast numpy array access
        for i in range(n_rows):
            inflow = inflow_arr[i]
            cont_flow = cont_flow_arr[i]
            cont_depth = cont_depth_arr[i]
            spill_in_delay = spill_delay_arr[i]

            # DRAINDOWN CHECK (legacy requires 5 conditions)
            can_draindown = (
                inflow == 0 and
                current_stored > 0 and
                cont_flow < self.config.flow_return_threshold and
                cont_depth < self.config.depth_return_threshold and
                spill_in_delay < self.config.flow_return_threshold
            )

            if can_draindown:
                # Drain down tank
                current_stored_before = current_stored

                # Determine drain rate (fixed or variable)
                if self.config.pumping_mode == 'Fixed':
                    drain_rate = self.config.pump_rate
                else:
                    # Variable pump rate: discharge at threshold minus current flow
                    drain_rate = self.config.flow_return_threshold - cont_flow

                drain_volume = drain_rate * timestep_sec

                if drain_volume >= current_stored:
                    # Tank empties completely
                    current_stored = 0.0
                else:
                    # Partial drain
                    current_stored -= drain_volume

                # Add drained volume back to continuation link
                returned_flow = (current_stored_before -
                                 current_stored) / timestep_sec
                cont_flow_arr[i] = cont_flow + returned_flow

            # FILLING TANK (when CSO is spilling and tank has space)
            elif current_stored < storage_volume and inflow > 0:
                inflow_volume = inflow * timestep_sec
                current_stored += inflow_volume

                if current_stored <= storage_volume:
                    # All flow stored
                    spill_flow_arr[i] = 0.0
                else:
                    # Tank overflows
                    overflow_volume = current_stored - storage_volume
                    current_stored = storage_volume
                    spill_flow_arr[i] = overflow_volume / timestep_sec

            tank_volume_arr[i] = current_stored

        # Write results back to DataFrame in one batch operation (fast)
        self.flow_data['Tank_Volume'] = tank_volume_arr
        self.flow_data['Spill_Flow'] = spill_flow_arr
        self.flow_data[cont_col] = cont_flow_arr

    def _detect_spills(self) -> list[SpillEvent]:
        """
        Detect spill events using the 12/24 hour counting method (legacy algorithm).

        A spill event is counted when:
        1. There's 12 hours of continuous spilling
        2. If spilling continues or restarts within 24 hours, it's the same event
        3. A 24-hour period with no spilling ends the event

        This matches the proven legacy logic exactly.

        OPTIMIZED: Uses numpy arrays for 5-10x speedup over pandas .at[] calls.
        """
        from datetime import timedelta

        events = []

        # Get thresholds
        flow_threshold = self.scenario.spill_flow_threshold
        volume_threshold = self.scenario.spill_volume_threshold
        timestep_sec = self.data_source.timestep_seconds

        # Calculate 12 and 24 hour periods in timesteps
        half_day = int((12 * 3600) / timestep_sec)  # 12 hours in timesteps
        full_day = int((24 * 3600) / timestep_sec)  # 24 hours in timesteps

        # State tracking (matches legacy variables)
        EAcount = 0  # Event assessment count
        cooldown = 0  # Cooldown period counter
        spill24 = 0.0  # Rolling 24hr spill tracker
        spill_count = 0
        list_of_spill_start_times = []

        # Pre-calculate spill volumes for 12 and 24 hour windows
        # (matches legacy's "Spill Volume (previous 12hrs)" approach)
        # Legacy zeros out flows <= threshold before rolling calculation (line 297)
        # and uses the zeroed column for spill detection (line 303: > 0)
        spill_flow_filtered = self.flow_data['Spill_Flow'].where(
            self.flow_data['Spill_Flow'] > flow_threshold, 0
        )
        self.flow_data['Spill_Volume_12hr'] = (
            spill_flow_filtered
            .rolling(window=half_day, min_periods=1, closed='left')
            .sum() * timestep_sec
        )
        self.flow_data['Spill_Volume_24hr'] = (
            spill_flow_filtered
            .rolling(window=full_day, min_periods=1, closed='left')
            .sum() * timestep_sec
        )

        # OPTIMIZATION: Extract to numpy arrays for fast iteration
        # Use filtered flows (legacy line 303 checks > 0 after threshold filtering)
        spill_flow_arr = spill_flow_filtered.values
        time_arr = self.flow_data['Time'].values
        spill_vol_12hr_arr = self.flow_data['Spill_Volume_12hr'].values
        spill_vol_24hr_arr = self.flow_data['Spill_Volume_24hr'].values
        n_rows = len(self.flow_data)

        # Main counting loop (ported from legacy countSpills)
        for i in range(n_rows):
            spill_flow = spill_flow_arr[i]

            if EAcount == 0:  # No spill has occurred, count has not started/has been reset
                # Legacy line 303: checks > 0 (threshold already applied via .where())
                if spill_flow > 0:  # Spill started
                    EAcount = 1
                else:
                    EAcount = 0

            else:
                if EAcount < half_day:  # 12/24 hour count is mid progress
                    EAcount += 1
                    if cooldown > 0:
                        spill24 += spill_flow  # Add to rolling 24hr tracker

                elif EAcount == half_day:  # Count is at 12 hours, assess if 1st spill
                    if cooldown == 0:  # This is 1st 12 hours of spill
                        spill_count += 1
                        spill_time = pd.Timestamp(
                            time_arr[i]) - timedelta(hours=12)
                        spill_volume = spill_vol_12hr_arr[i]
                        # Store [start_time, volume, duration, is_continuation]
                        list_of_spill_start_times.append(
                            [spill_time, spill_volume, 12.0, False])
                        cooldown = 1  # Initiates first 24hour period
                        EAcount = 1
                        spill24 = 0  # Reset 24hr spill tracker
                        spill24 = spill_flow
                    elif cooldown > 0:
                        EAcount += 1
                        spill24 += spill_flow

                elif EAcount == full_day:  # At 24 hours
                    if spill24 > 0:  # Spill in the 24 hour cooldown
                        cooldown += 1  # Start a new 24 hour cooldown
                        EAcount = 1
                        spill24 = 0
                        spill_count += 1
                        spill_time = pd.Timestamp(
                            time_arr[i]) - timedelta(hours=24)
                        spill_volume = spill_vol_24hr_arr[i]
                        # Store [start_time, volume, duration, is_continuation]
                        list_of_spill_start_times.append(
                            [spill_time, spill_volume, 24.0, True])
                    else:  # No spill, reset
                        EAcount = 0
                        spill24 = 0
                        cooldown = 0

                else:  # Count is between half day & full day
                    EAcount += 1
                    spill24 += spill_flow

        # Create spill events from the collected start times
        # Filter by volume threshold (matches legacy)

        for spill_time, spill_volume, window_hours, is_continuation in list_of_spill_start_times:
            if spill_volume >= volume_threshold:
                # Window is 12 or 24 hours (for counting purposes)
                # But duration should be ACTUAL time spent spilling within that window
                window_end_time = spill_time + timedelta(hours=window_hours)

                # Find actual spilling within this window
                period_mask = (
                    (self.flow_data['Time'] >= spill_time) &
                    (self.flow_data['Time'] <= window_end_time) &
                    (self.flow_data['Spill_Flow'] > flow_threshold)
                )

                # Calculate actual duration: count timesteps with spilling × timestep length
                # (matches legacy: np.count_nonzero(Spill) * Timestep_Length / 3600)
                num_spilling_timesteps = period_mask.sum()
                actual_duration_hours = num_spilling_timesteps * timestep_sec / 3600.0

                # Find peak flow and actual end time
                if period_mask.any():
                    peak_flow = self.flow_data.loc[period_mask, 'Spill_Flow'].max(
                    )
                    # End time is last timestep with spilling in this window
                    # end_time = self.flow_data.loc[period_mask, 'Time'].iloc[-1]
                    # End time of the event is the start time plus the window duration
                    end_time = spill_time + timedelta(hours=window_hours)
                else:
                    peak_flow = 0.0
                    end_time = spill_time

                events.append(SpillEvent(
                    start_time=spill_time,
                    end_time=end_time,
                    window_duration_hours=window_hours,
                    spill_duration_hours=actual_duration_hours,
                    volume_m3=spill_volume,
                    peak_flow_m3s=peak_flow,
                ))

        return events
