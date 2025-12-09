"""
Head-Discharge Relationship Analysis

This module provides functionality to reverse-engineer the head vs discharge
relationship from existing overflow data during remaining spill events.

The analysis looks at overflow link depth and flow during spills that remain
after storage intervention, revealing the hydraulic control characteristics.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy.optimize import curve_fit
from scipy.stats import linregress


class HeadDischargeAnalyzer:
    """
    Analyzes remaining spill events to determine the head-discharge relationship
    of the existing hydraulic control on the overflow link.

    Uses actual depth and flow data from the overflow link during remaining spills
    to fit a hydraulic relationship (e.g., Q = C * H^n for orifice/weir flow).
    """

    def __init__(self):
        """Initialize analyzer."""
        pass

    def analyze_scenario(self,
                         scenario_result: Dict,
                         overflow_link: str,
                         depth_data: pd.DataFrame,
                         flow_data: pd.DataFrame) -> Dict:
        """
        Analyze a scenario's remaining spills to determine head-discharge relationship.

        Args:
            scenario_result: Result dictionary from analysis with '_full_result' key
            overflow_link: Name of the overflow link (e.g., 'O1')
            depth_data: DataFrame with 'Time' column and depth columns for each link (m)
            flow_data: DataFrame with 'Time' column and flow columns for each link (m³/s)

        Returns:
            Dictionary with:
                - 'head_discharge_points': List of (head_m, discharge_m3s) tuples
                - 'fitted_params': Fitted parameters for Q = C * H^n
                - 'r_squared': Goodness of fit
                - 'equation': String representation of fitted equation
                - 'spill_events_analyzed': Number of spill events used
        """
        full_result = scenario_result.get('_full_result')
        if not full_result:
            return {'error': 'No full result data available'}

        # Get remaining spill events (after storage intervention)
        spill_events = full_result.spill_events
        if not spill_events:
            return {'error': 'No remaining spill events - storage eliminated all spills'}

        # Check if we have the required data columns
        if overflow_link not in depth_data.columns:
            return {'error': f'Depth data not found for overflow link {overflow_link}'}

        if overflow_link not in flow_data.columns:
            return {'error': f'Flow data not found for overflow link {overflow_link}'}

        # Collect head-discharge data points from remaining spill events
        head_discharge_points = []
        events_analyzed = 0

        for event in spill_events:
            # Find overflow link data during this spill event
            # Match times in both depth and flow data
            depth_mask = (depth_data['Time'] >= event.start_time) & \
                (depth_data['Time'] <= event.end_time)
            flow_mask = (flow_data['Time'] >= event.start_time) & \
                (flow_data['Time'] <= event.end_time)

            event_depths = depth_data.loc[depth_mask, ['Time', overflow_link]]
            event_flows = flow_data.loc[flow_mask, ['Time', overflow_link]]

            # Merge on time to ensure we have matching depth and flow values
            event_data = pd.merge(event_depths, event_flows,
                                  on='Time', suffixes=('_depth', '_flow'))

            if event_data.empty:
                continue

            # Extract depth (head) and flow (discharge)
            heads = event_data[f'{overflow_link}_depth'].values
            flows = event_data[f'{overflow_link}_flow'].values

            # Filter for actual spilling timesteps (flow > threshold)
            # Use a small threshold to avoid noise
            spilling = flows > 0.0001  # 0.1 L/s threshold

            if np.any(spilling):
                valid_heads = heads[spilling]
                valid_flows = flows[spilling]

                # Add points to our dataset (only where head > 0)
                for h, q in zip(valid_heads, valid_flows):
                    if h > 0 and q > 0:  # Valid points only
                        head_discharge_points.append((h, q))

                events_analyzed += 1

        if not head_discharge_points:
            return {'error': 'No valid head-discharge points found during remaining spills'}

        # Convert to arrays
        heads = np.array([p[0] for p in head_discharge_points])
        discharges = np.array([p[1] for p in head_discharge_points])

        # Fit power law: Q = C * H^n (orifice/weir equation form)
        fitted_params, r_squared = self._fit_power_law(heads, discharges)

        if fitted_params is None:
            return {'error': 'Could not fit power law to data'}

        C, n = fitted_params

        # Generate fitted curve for plotting
        head_range = np.linspace(heads.min(), heads.max(), 100)
        fitted_discharge = C * head_range ** n

        # Classify hydraulic control type based on exponent
        if n < 0.7:
            control_type = "Orifice-like (n < 0.7)"
        elif n > 1.2:
            control_type = "Weir-like (n > 1.2)"
        else:
            control_type = "Mixed flow (0.7 ≤ n ≤ 1.2)"

        return {
            'head_discharge_points': head_discharge_points,
            'fitted_params': {'C': C, 'n': n},
            'r_squared': r_squared,
            'equation': f'Q = {C:.4f} × H^{n:.3f}',
            'control_type': control_type,
            'head_range': head_range.tolist(),
            'fitted_discharge': fitted_discharge.tolist(),
            'spill_events_analyzed': events_analyzed,
            'num_points': len(head_discharge_points),
            'head_min': heads.min(),
            'head_max': heads.max(),
            'discharge_min': discharges.min(),
            'discharge_max': discharges.max(),
            'overflow_link': overflow_link,
        }

    def _fit_power_law(self, heads: np.ndarray, discharges: np.ndarray) -> Tuple[Optional[Tuple[float, float]], float]:
        """
        Fit Q = C * H^n to head-discharge data.

        Returns:
            ((C, n), r_squared) or (None, 0) if fit fails
        """
        try:
            # Use log-log regression for more stable fitting
            # log(Q) = log(C) + n * log(H)
            log_h = np.log(heads)
            log_q = np.log(discharges)

            # Linear regression on log-log data
            slope, intercept, r_value, p_value, std_err = linregress(
                log_h, log_q)

            # Convert back to power law parameters
            n = slope
            C = np.exp(intercept)
            r_squared = r_value ** 2

            return (C, n), r_squared

        except Exception as e:
            print(f"Power law fit failed: {e}")
            return None, 0.0

    def compare_scenarios(self, scenario_results: Dict[str, Dict]) -> pd.DataFrame:
        """
        Compare head-discharge relationships across multiple scenarios.

        Args:
            scenario_results: Dict of {scenario_name: result_dict}

        Returns:
            DataFrame with columns: scenario, C, n, r_squared, equation, control_type
        """
        comparisons = []

        for scenario_name, result in scenario_results.items():
            if 'fitted_params' in result and result['fitted_params']:
                comparisons.append({
                    'Scenario': scenario_name,
                    'C': result['fitted_params']['C'],
                    'n': result['fitted_params']['n'],
                    'R²': result['r_squared'],
                    'Equation': result['equation'],
                    'Control Type': result.get('control_type', 'Unknown'),
                    'Points': result.get('num_points', 0),
                    'Spill Events': result.get('spill_events_analyzed', 0),
                    'Overflow Link': result.get('overflow_link', ''),
                })

        return pd.DataFrame(comparisons)
