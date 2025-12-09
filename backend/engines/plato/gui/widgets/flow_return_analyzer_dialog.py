"""
Flow Return Analyzer Dialog.

Interactive dialog for visualizing continuation flow and analyzing
drain capacity based on flow return thresholds and pump rates.
"""
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QDoubleSpinBox, QGroupBox, QPushButton,
                             QTextEdit)
import pandas as pd
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas)
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar)


class FlowReturnAnalyzerDialog(QDialog):
    """
    Dialog for analyzing flow return capacity.

    Shows continuation flow time series with overlays indicating:
    - Flow return threshold (horizontal line)
    - Maximum return capacity (shaded area)
    - Actual pump rate capability

    Can work with either:
    - Full time series data (slower but accurate)
    - Sampled statistics (fast, representative)
    """

    def __init__(self,
                 cso_name: str,
                 continuation_flow: Optional[pd.Series] = None,
                 flow_statistics: Optional[Dict[str, Any]] = None,
                 initial_pump_rate: float = 0.0,
                 initial_threshold: float = None,
                 pff_increase: float = 0.0,
                 timestep_seconds: float = 300,
                 parent=None):
        """
        Initialize the flow return analyzer dialog.

        Args:
            cso_name: Name of the CSO being analyzed
            continuation_flow: Optional full time series of continuation link flow (m3/s)
            flow_statistics: Optional dict with statistics (min, max, mean, median, sample_data)
            initial_pump_rate: Initial pump rate value (m3/s)
            initial_threshold: Initial flow return threshold (m3/s)
            pff_increase: Additional PFF capacity from storage (m3/s)
            timestep_seconds: Length of each timestep in seconds
            parent: Parent widget
        """
        super().__init__(parent)

        self.cso_name = cso_name
        self.pff_increase = pff_increase
        self.timestep_seconds = timestep_seconds
        self.using_statistics = flow_statistics is not None

        # Use either full data or statistics
        if flow_statistics is not None:
            # Use sampled/statistical data
            self.continuation_flow = flow_statistics['sample_data'].iloc[:, 0]
            self.flow_times = flow_statistics['sample_times']
            self.max_continuation = flow_statistics['max']
            self.min_continuation = flow_statistics['min']
            self.mean_continuation = flow_statistics['mean']
            self.sample_interval = flow_statistics.get('sample_interval', 1)
            self.is_sampled = True
            self.is_spill_focused = flow_statistics.get('spill_focused', False)
            self.spill_timesteps = flow_statistics.get('spill_timesteps', 0)
            self.total_timesteps = flow_statistics.get(
                'total_sampled_timesteps', 0)

            # New spill analysis metrics
            self.avg_spill_volume = flow_statistics.get(
                'avg_spill_volume_m3', None)
            self.avg_non_spill_flow = flow_statistics.get(
                'avg_non_spill_continuation_flow', None)
            self.max_pump_estimate = flow_statistics.get(
                'max_pump_return_estimate', None)
            self.num_spill_events = flow_statistics.get('num_events', None)
        elif continuation_flow is not None:
            # Use full data
            self.continuation_flow = continuation_flow
            self.flow_times = continuation_flow.index if hasattr(
                continuation_flow, 'index') else None
            self.max_continuation = continuation_flow.max()
            self.min_continuation = continuation_flow.min()
            self.mean_continuation = continuation_flow.mean()
            self.sample_interval = 1
            self.is_sampled = False
            self.is_spill_focused = False
            self.spill_timesteps = 0
            self.total_timesteps = len(continuation_flow) if hasattr(
                continuation_flow, '__len__') else 0

            # No spill analysis metrics for full data
            self.avg_spill_volume = None
            self.avg_non_spill_flow = None
            self.max_pump_estimate = None
            self.num_spill_events = None
        else:
            raise ValueError(
                "Either continuation_flow or flow_statistics must be provided")

        self.effective_capacity = self.max_continuation + pff_increase

        # Set initial values
        if initial_threshold is None:
            initial_threshold = self.mean_continuation

        title = f"Flow Return Analyzer - {cso_name}"
        if self.is_sampled:
            if self.is_spill_focused and self.spill_timesteps > 0:
                spill_pct = (self.spill_timesteps / self.total_timesteps *
                             100) if self.total_timesteps > 0 else 0
                title += f" (Spill-Focused: {self.spill_timesteps}/{self.total_timesteps} timesteps, {spill_pct:.1f}%)"
            else:
                title += f" (Sampled 1:{self.sample_interval})"
        self.setWindowTitle(title)
        self.resize(1000, 700)

        self._setup_ui(initial_pump_rate, initial_threshold)
        self._update_analysis()

    def _setup_ui(self, initial_pump_rate: float, initial_threshold: float):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)

        # Controls panel
        controls_group = QGroupBox("Analysis Parameters")
        controls_layout = QHBoxLayout()

        # Pump rate control
        pump_layout = QVBoxLayout()
        pump_layout.addWidget(QLabel("Pump Rate (m³/s):"))
        self.pump_rate_spin = QDoubleSpinBox()
        self.pump_rate_spin.setRange(0.0, 10.0)
        self.pump_rate_spin.setDecimals(5)
        self.pump_rate_spin.setSingleStep(0.00001)
        self.pump_rate_spin.setValue(initial_pump_rate)
        self.pump_rate_spin.valueChanged.connect(self._update_analysis)
        pump_layout.addWidget(self.pump_rate_spin)
        controls_layout.addLayout(pump_layout)

        # Flow return threshold control
        threshold_layout = QVBoxLayout()
        threshold_layout.addWidget(QLabel("Flow Return Threshold (m³/s):"))
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.0, self.max_continuation * 2)
        self.threshold_spin.setDecimals(5)
        self.threshold_spin.setSingleStep(0.00001)
        self.threshold_spin.setValue(initial_threshold)
        self.threshold_spin.valueChanged.connect(self._update_analysis)
        threshold_layout.addWidget(self.threshold_spin)
        controls_layout.addLayout(threshold_layout)

        # Suggest button
        suggest_btn = QPushButton("Suggest Values")
        suggest_btn.clicked.connect(self._suggest_values)
        controls_layout.addWidget(suggest_btn)

        controls_layout.addStretch()
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # Main content area with plot on left, stats on right
        content_layout = QHBoxLayout()

        # Left side: Plot with toolbar
        plot_layout = QVBoxLayout()
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        content_layout.addLayout(plot_layout, 3)  # 3 parts width for plot

        # Right side: Statistics panel
        stats_group = QGroupBox("Analysis Results")
        stats_layout = QVBoxLayout()
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMinimumWidth(300)
        stats_layout.addWidget(self.stats_text)
        stats_group.setLayout(stats_layout)
        content_layout.addWidget(stats_group, 1)  # 1 part width for stats

        layout.addLayout(content_layout)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _update_analysis(self):
        """Update the plot and statistics based on current parameters."""
        pump_rate = self.pump_rate_spin.value()
        threshold = self.threshold_spin.value()

        # Calculate analysis
        results = self._calculate_drain_analysis(pump_rate, threshold)

        # Update plot
        self._update_plot(pump_rate, threshold, results)

        # Update statistics
        self._update_statistics(results)

    def _calculate_drain_analysis(self, pump_rate: float, threshold: float) -> dict:
        """
        Calculate drain capacity analysis for spill + return projection.

        For spill-focused data:
        - Phase 1: Shows composite average spill event
        - Phase 2: Projects pump return starting after spill ends

        Returns:
            Dictionary with analysis results
        """
        if not self.is_spill_focused or self.avg_spill_volume is None:
            # Fall back to original analysis for non-spill-focused data
            return self._calculate_traditional_analysis(pump_rate, threshold)

        # === PHASE 1: Composite Average Spill Event ===
        spill_length = len(self.continuation_flow)

        # === PHASE 2: Project Pump Return After Spill ===
        if pump_rate > 0:
            # Minimum time needed to return all spilled volume
            min_return_timesteps = int(
                np.ceil(self.avg_spill_volume / (pump_rate * self.timestep_seconds)))
        else:
            min_return_timesteps = 0

        # Project continuation flow after spill (assume returns to baseline)
        # We'll use a simple model: gradually return to non-spill baseline
        max_projection_timesteps = max(
            min_return_timesteps * 2, 100)  # Project enough time

        # Create projected continuation flow (declining from end of spill to baseline)
        if len(self.continuation_flow) > 0:
            last_spill_flow = self.continuation_flow.iloc[-1]
        else:
            last_spill_flow = self.mean_continuation

        baseline_flow = self.avg_non_spill_flow if self.avg_non_spill_flow is not None else self.min_continuation

        # Linear decline from end of spill to baseline over some timesteps
        decline_timesteps = min(50, max_projection_timesteps // 2)
        decline_flows = np.linspace(
            last_spill_flow, baseline_flow, decline_timesteps)

        # Then maintain baseline
        baseline_flows = np.full(
            max_projection_timesteps - decline_timesteps, baseline_flow)
        projected_continuation = np.concatenate(
            [decline_flows, baseline_flows])

        # Calculate when we can pump (below threshold and have capacity)
        available_capacity_projection = np.clip(
            self.effective_capacity - projected_continuation, 0, None)
        below_threshold_projection = projected_continuation < threshold
        can_pump_projection = below_threshold_projection & (
            available_capacity_projection >= pump_rate)

        # Simulate actual pumping with tank emptying
        remaining_volume = self.avg_spill_volume
        actual_pump_flow = np.zeros(len(projected_continuation))

        for i in range(len(projected_continuation)):
            if remaining_volume <= 0:
                break

            if can_pump_projection[i]:
                # Pump at full rate if capacity allows and below threshold
                pump_this_step = min(
                    pump_rate, available_capacity_projection[i])
                volume_this_step = pump_this_step * self.timestep_seconds

                if volume_this_step > remaining_volume:
                    # Last bit of pumping - partial timestep
                    pump_this_step = remaining_volume / self.timestep_seconds
                    volume_this_step = remaining_volume

                actual_pump_flow[i] = pump_this_step
                remaining_volume -= volume_this_step

        # Calculate when tank is empty
        timesteps_to_empty = np.where(actual_pump_flow > 0)[0]
        if len(timesteps_to_empty) > 0:
            tank_empty_timestep = timesteps_to_empty[-1] + 1
        else:
            tank_empty_timestep = 0

        total_pumped = (actual_pump_flow * self.timestep_seconds).sum()
        pump_efficiency = (total_pumped / self.avg_spill_volume *
                           100) if self.avg_spill_volume > 0 else 0

        return {
            'spill_length': spill_length,
            'projected_continuation': projected_continuation,
            'actual_pump_flow': actual_pump_flow,
            'can_pump_projection': can_pump_projection,
            'available_capacity_projection': available_capacity_projection,
            'remaining_volume': remaining_volume,
            'total_pumped': total_pumped,
            'pump_efficiency': pump_efficiency,
            'tank_empty_timestep': tank_empty_timestep,
            'min_return_timesteps': min_return_timesteps,
        }

    def _calculate_traditional_analysis(self, pump_rate: float, threshold: float) -> dict:
        """Traditional analysis for non-spill-focused data."""
        # Available capacity for return flow at each timestep
        available_capacity = (self.effective_capacity -
                              self.continuation_flow).clip(lower=0)

        # Can drain if: continuation flow < threshold AND available capacity >= pump rate
        below_threshold = self.continuation_flow < threshold
        enough_capacity = available_capacity >= pump_rate
        can_drain = below_threshold & enough_capacity

        # Calculate drain volumes
        potential_drain_volume = (
            can_drain * pump_rate * self.timestep_seconds).sum()

        # Calculate statistics
        percent_below_threshold = below_threshold.mean() * 100
        percent_can_drain = can_drain.mean() * 100

        # Maximum possible return at each timestep (limited by available capacity)
        max_possible_return = available_capacity.clip(upper=pump_rate)
        max_possible_volume = (max_possible_return *
                               self.timestep_seconds).sum()

        return {
            'can_drain': can_drain,
            'available_capacity': available_capacity,
            'max_possible_return': max_possible_return,
            'potential_drain_volume': potential_drain_volume,
            'max_possible_volume': max_possible_volume,
            'percent_below_threshold': percent_below_threshold,
            'percent_can_drain': percent_can_drain,
            'max_safe_continuation': self.effective_capacity - pump_rate,
            'spill_length': len(self.continuation_flow),
        }

    def _update_plot(self, pump_rate: float, threshold: float, results: dict):
        """Update the matplotlib plot."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if self.is_spill_focused and self.avg_spill_volume is not None:
            # TWO-PHASE PLOT: Spill Event + Return Projection

            # === PHASE 1: Composite Average Spill Event ===
            spill_length = results['spill_length']
            spill_time_index = range(spill_length)

            # Plot actual spill continuation flow
            ax.plot(spill_time_index, self.continuation_flow.values,
                    label='Spill Event (Composite Mean)', color='blue', linewidth=2, alpha=0.8)

            # === PHASE 2: Projected Return ===
            projected_continuation = results['projected_continuation']
            actual_pump_flow = results['actual_pump_flow']

            # Create time index for projection (starts after spill)
            projection_length = len(projected_continuation)
            projection_time_index = range(
                spill_length, spill_length + projection_length)

            # Plot projected continuation flow (after spill ends)
            ax.plot(projection_time_index, projected_continuation,
                    label='Projected Continuation (Post-Spill)', color='skyblue',
                    linewidth=1.5, linestyle='--', alpha=0.7)

            # Plot projected continuation + pump return
            total_flow_projection = projected_continuation + actual_pump_flow
            ax.plot(projection_time_index, total_flow_projection,
                    label=f'Projected + Pump Return ({pump_rate:.3f} m³/s)',
                    color='purple', linewidth=2, alpha=0.8)

            # Shade pumping periods
            for i in range(len(actual_pump_flow)):
                if actual_pump_flow[i] > 0:
                    ax.axvspan(spill_length + i, spill_length + i + 1,
                               alpha=0.15, color='green')

            # Mark when tank is empty
            if results['tank_empty_timestep'] > 0:
                empty_timestep = spill_length + results['tank_empty_timestep']
                ax.axvline(x=empty_timestep, color='darkgreen', linestyle=':',
                           linewidth=2, label='Tank Empty', alpha=0.7)

            # Mark spill/projection boundary
            ax.axvline(x=spill_length, color='gray', linestyle='-',
                       linewidth=1, alpha=0.5, label='Spill End / Projection Start')

        else:
            # TRADITIONAL PLOT: Full dataset analysis
            time_index = range(len(self.continuation_flow))

            # Plot continuation flow
            ax.plot(time_index, self.continuation_flow.values,
                    label='Continuation Flow', color='blue', linewidth=1, alpha=0.7)

            # Shade area where draining is possible
            can_drain = results['can_drain']
            for i in range(len(can_drain)):
                if can_drain.iloc[i]:
                    ax.axvspan(i, i+1, alpha=0.2, color='green')

            # Plot maximum possible return flow
            max_return_line = self.continuation_flow + \
                results['max_possible_return']
            ax.plot(time_index, max_return_line.values,
                    label='Continuation + Max Return', color='green',
                    linewidth=1, linestyle='--', alpha=0.6)

            # Plot what happens with pump rate
            pump_return_line = self.continuation_flow.copy()
            pump_return_line[can_drain] += pump_rate
            ax.plot(time_index, pump_return_line.values,
                    label=f'Continuation + Pump ({pump_rate:.3f} m³/s)',
                    color='purple', linewidth=1.5, alpha=0.8)

        # Common elements for both plot types
        # Plot flow return threshold
        ax.axhline(y=threshold, color='orange', linestyle='--',
                   linewidth=2, label=f'Flow Return Threshold ({threshold:.3f} m³/s)')

        # Plot effective capacity line
        ax.axhline(y=self.effective_capacity, color='red', linestyle=':',
                   linewidth=2, label=f'Effective Capacity ({self.effective_capacity:.3f} m³/s)')

        ax.set_xlabel('Timestep')
        ax.set_ylabel('Flow (m³/s)')

        if self.is_spill_focused and self.avg_spill_volume is not None:
            ax.set_title(f'Spill + Pump Return Projection - {self.cso_name}')
        else:
            ax.set_title(f'Flow Return Analysis - {self.cso_name}')

        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)

        self.canvas.draw()

    def _update_statistics(self, results: dict):
        """Update the statistics text display."""
        sampling_note = ""
        if self.is_sampled:
            if self.is_spill_focused and self.spill_timesteps > 0:
                spill_pct = (self.spill_timesteps / self.total_timesteps *
                             100) if self.total_timesteps > 0 else 0
                sampling_note = (
                    f"<i><b>Spill-Focused Analysis:</b> Statistics computed from "
                    f"the composite mean of {self.num_spill_events} spill events</i><br><br>"
                )
            else:
                sampling_note = f"<i>(Based on 1:{self.sample_interval} sampled data)</i><br><br>"

        # Build spill analysis section if available
        spill_analysis_section = ""
        pump_projection_section = ""

        if self.avg_spill_volume is not None:
            spill_analysis_section = f"""
        <b>Spill Event Analysis:</b><br>
        • Number of spill events: {self.num_spill_events}<br>
        • Average spill volume: {self.avg_spill_volume:.1f} m³<br>
        • Non-spill baseline flow: {self.avg_non_spill_flow:.4f} m³/s<br>
        • <b>Estimated max pump return:</b> <span style='color: green;'>{self.max_pump_estimate:.4f} m³/s</span><br>
        <i>(Difference between peak spill flow and baseline)</i><br>
        <br>
        """

            # Add pump return projection metrics if available
            if 'total_pumped' in results:
                # minutes
                min_return_time = results['min_return_timesteps'] * \
                    self.timestep_seconds / 60
                # minutes
                actual_return_time = results['tank_empty_timestep'] * \
                    self.timestep_seconds / 60
                pump_efficiency = results['pump_efficiency']
                remaining_volume = results['remaining_volume']

                efficiency_color = "green" if pump_efficiency >= 95 else "orange"

                pump_projection_section = f"""
        <b>Pump Return Projection:</b><br>
        • Minimum return time: {min_return_time:.1f} minutes<br>
        • Actual return time: {actual_return_time:.1f} minutes<br>
        • Volume pumped: {results['total_pumped']:.1f} m³<br>
        • Pump efficiency: <span style='color: {efficiency_color};'>{pump_efficiency:.1f}%</span><br>
        • Remaining in tank: {remaining_volume:.1f} m³<br>
        <i>(Based on threshold constraints and available capacity)</i><br>
        <br>
        """

        stats_html = f"""
        {sampling_note}
        {spill_analysis_section}
        {pump_projection_section}
        <b>Composite Mean Continuation Flow Statistics:</b><br>
        • Maximum: {self.max_continuation:.3f} m³/s<br>
        • Mean: {self.mean_continuation:.3f} m³/s<br>
        • Minimum: {self.min_continuation:.3f} m³/s<br>
        <br>
        <b>Capacity Analysis:</b><br>
        • Effective Capacity: {self.effective_capacity:.3f} m³/s<br>
        • PFF Increase: {self.pff_increase:.3f} m³/s<br>
        • Max Safe Continuation: {results.get('max_safe_continuation', self.effective_capacity):.3f} m³/s<br>
        <br>
        """

        # Add traditional drain analysis if available (non-spill-focused mode)
        if 'percent_can_drain' in results:
            stats_html += f"""
        <b>Drain Analysis:</b><br>
        • Flow below threshold: {results['percent_below_threshold']:.1f}% of timesteps<br>
        • Can actually drain: {results['percent_can_drain']:.1f}% of timesteps<br>
        • Potential drain volume: {results['potential_drain_volume']:.1f} m³<br>
        • Max possible drain volume: {results['max_possible_volume']:.1f} m³<br>
        """

            # Add warnings if applicable
            if results['percent_can_drain'] < 10:
                stats_html += "<br><b style='color: red;'>⚠ Warning: Very limited drainage opportunity (&lt;10%)</b>"
            elif results['percent_can_drain'] < 30:
                stats_html += "<br><b style='color: orange;'>⚠ Caution: Limited drainage opportunity (&lt;30%)</b>"

        self.stats_text.setHtml(stats_html)

    def _suggest_values(self):
        """Suggest sensible threshold and pump rate values."""
        # Suggest threshold as 90th percentile of safe flows
        max_safe_continuation = self.effective_capacity - self.pump_rate_spin.value()
        safe_flows = self.continuation_flow[self.continuation_flow <=
                                            max_safe_continuation]

        if len(safe_flows) > 0:
            suggested_threshold = safe_flows.quantile(0.90)
            self.threshold_spin.setValue(suggested_threshold)

        # Suggest pump rate as median available capacity
        available_capacity = (self.effective_capacity -
                              self.continuation_flow).clip(lower=0)
        suggested_pump = available_capacity.quantile(0.50)
        self.pump_rate_spin.setValue(
            min(suggested_pump, 1.0))  # Cap at reasonable value

        self._update_analysis()
