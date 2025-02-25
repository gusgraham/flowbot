import matplotlib.patches as mpl_patches
import matplotlib.dates as mpl_dates
import matplotlib.gridspec as mpl_gridspec
from matplotlib import pyplot as plt
from matplotlib import axes, lines, text
from matplotlib.backend_bases import MouseButton
from collections import Counter
# from matplotlib.dates import DateFormatter
import matplotlib.ticker as ticker
from matplotlib.ticker import MaxNLocator, FuncFormatter
from matplotlib.dates import DateFormatter, HourLocator, DayLocator, MonthLocator, YearLocator, ConciseDateFormatter, AutoDateLocator
from typing import Optional, Dict, Tuple, List, Any
from dataclasses import dataclass, field
from itertools import cycle
from flowbot_helper import (
    PlotWidget,
    get_classification_color_mapping,
    get_classification_legend_dataframe,
    getBlankFigure,
    rps_or_tt,
    resource_path,
)
from flowbot_management import (
    fsmInstall,
    fsmProject,
    fsmRawData,
    MonitorDataFlowCalculator,
)
from flowbot_monitors import (
    plottedFlowMonitors,
    plottedRainGauges,
    flowMonitor,
    rainGauge,
)
from flowbot_survey_events import surveyEvent, plottedSurveyEvents
from flowbot_verification import plottedICMTrace, icmTraceLocation, icmTrace
from flowbot_water_quality import plottedWQMonitors
import mplcursors
import numpy as np
import math
import pandas as pd
from datetime import timedelta, datetime
import textwrap as twp
from matplotlib.table import table
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import matplotlib.colors as mcolors
import scipy.stats as st
# from matplotlib.widgets import Button
from matplotlib.backend_bases import PickEvent
# from matplotlib.figure import Figure
# from matplotlib.patches import Rectangle


class GraphFDV:
    """Class to create and modify the Flow, Depth, Velocity Plots"""

    def __init__(self, mw_pw: Optional[PlotWidget] = None):

        self.main_window_plot_widget: PlotWidget = mw_pw
        getBlankFigure(self.main_window_plot_widget)
        self.isBlank: bool = True

        self.plotted_fms: plottedFlowMonitors = plottedFlowMonitors()
        self.plotted_rgs: plottedRainGauges = plottedRainGauges()

        self.plot_axis_rg: Optional[axes.Axes] = None
        self.plot_axis_depth: Optional[axes.Axes] = None
        self.plot_axis_flow: Optional[axes.Axes] = None
        self.plot_axis_velocity: Optional[axes.Axes] = None
        self.plot_flow_stats_box: Optional[text.Text] = None
        self.plot_depth_stats_box: Optional[text.Text] = None
        self.plot_velocity_stats_box: Optional[text.Text] = None
        self.plot_rainfall_stats_box: Optional[text.Text] = None
        self.__plot_event: Optional[surveyEvent] = None
        self.c_flow_lines: Optional[list[lines.Line2D]] = None
        self.c_depth_lines: Optional[list[lines.Line2D]] = None
        self.c_vel_lines: Optional[list[lines.Line2D]] = None
        self.c_flow_legend_lines: Optional[list[lines.Line2D]] = None
        self.c_depth_legend_lines: Optional[list[lines.Line2D]] = None
        self.c_vel_legend_lines: Optional[list[lines.Line2D]] = None

    def set_plot_event(self, se: surveyEvent):

        self.__plot_event = se
        if self.plotted_fms is not None:
            if self.__plot_event is None:
                self.plotted_fms.setPlotDateLimits(None, None)
            else:
                self.plotted_fms.setPlotDateLimits(se.eventStart, se.eventEnd)
        if self.plotted_rgs is not None:
            if self.__plot_event is None:
                self.plotted_rgs.setPlotDateLimits(None, None)
            else:
                self.plotted_rgs.setPlotDateLimits(se.eventStart, se.eventEnd)

    def get_plot_event(self) -> Optional[surveyEvent]:

        return self.__plot_event

    def has_plot_event(self) -> bool:

        if self.__plot_event is None:
            return False
        else:
            return True

    def get_plot_eventName(self) -> Optional[str]:

        if self.__plot_event is not None:
            return self.__plot_event.eventName

    def update_plot(self):

        self.main_window_plot_widget.figure.clear()

        if len(self.plotted_fms.plotFMs) + len(self.plotted_rgs.plotRGs) == 0:
            getBlankFigure(self.main_window_plot_widget)
            self.isBlank = True
            # self.localFigure = None
            self.updateCanvas()
            return

        (
            self.plot_axis_rg,
            self.plot_axis_depth,
            self.plot_axis_flow,
            self.plot_axis_velocity,
        ) = self.main_window_plot_widget.figure.subplots(
            nrows=4, sharex=True, gridspec_kw={"height_ratios": [1, 1, 1, 1]}
        )

        major_tick_format = DateFormatter("%d/%m/%Y %H:%M")

        fm_title = "No FM Plotted"
        colors = cycle(
            [
                "mediumseagreen",
                "indianred",
                "steelblue",
                "goldenrod",
                "deepskyblue",
                "lime",
                "black",
                "purple",
                "navy",
                "olive",
                "fuchsia",
                "grey",
                "silver",
                "teal",
                "red",
            ]
        )
        self.c_flow_lines = []
        self.c_depth_lines = []
        self.c_vel_lines = []

        for fm in self.plotted_fms.plotFMs.values():

            if len(self.plotted_fms.plotFMs) == 1:
                flow_colour = "steelblue"
                depth_colour = "indianred"
                velocityColour = "mediumseagreen"
                fm_title = fm.monitorName
            else:
                multi_plot_colour = next(colors)

                flow_colour = multi_plot_colour
                depth_colour = multi_plot_colour
                velocityColour = multi_plot_colour

                fm_title = fm_title + ", " + fm.monitorName

            (multi_flow,) = self.plot_axis_flow.plot(
                fm.dateRange,
                fm.flowDataRange,
                "-",
                linewidth=1.1,
                label=fm.monitorName,
                color=flow_colour,
            )
            (multi_depth,) = self.plot_axis_depth.plot(
                fm.dateRange,
                fm.depthDataRange,
                "-",
                linewidth=1,
                label=fm.monitorName,
                color=depth_colour,
            )
            (multi_velocity,) = self.plot_axis_velocity.plot(
                fm.dateRange,
                fm.velocityDataRange,
                "-",
                linewidth=1,
                label=fm.monitorName,
                color=velocityColour,
            )

            self.c_flow_lines.append(multi_flow)
            self.c_depth_lines.append(multi_depth)
            self.c_vel_lines.append(multi_velocity)

        rg_count = 0
        rg_title = "No RG Plotted"

        for rg in self.plotted_rgs.plotRGs.values():

            rg_count += 1

            if rg_count == 1:
                rg_title = rg.gaugeName
            else:
                rg_title = rg_title + ", " + rg.gaugeName

            self.plot_axis_rg.plot(
                rg.dateRange,
                rg.rainfallDataRange,
                "-",
                linewidth=1,
                color="midnightblue",
                label=rg.gaugeName,
            )

        multi_leg = self.plot_axis_flow.legend(loc="best", prop={"size": 6})

        self.c_flow_legend_lines = {}

        for legline, origline in zip(multi_leg.get_lines(), self.c_flow_lines):
            legline.set_picker(5)  # 5 pts tolerance
            self.c_flow_legend_lines[legline] = origline

        self.c_depth_legend_lines = {}

        for legline, origline in zip(multi_leg.get_lines(), self.c_depth_lines):
            legline.set_picker(5)  # 5 pts tolerance
            self.c_depth_legend_lines[legline] = origline

        self.c_vel_legend_lines = {}

        for legline, origline in zip(multi_leg.get_lines(), self.c_vel_lines):
            legline.set_picker(5)  # 5 pts tolerance
            self.c_vel_legend_lines[legline] = origline

        self.plot_axis_rg.set_title(
            fm_title + " : " + rg_title, color="grey", fontsize=15
        )

        self.plot_axis_flow.set_ylabel("Flow l/s", fontsize=8)
        self.plot_axis_flow.tick_params(axis="y", which="major", labelsize=8)

        # Depth
        self.plot_axis_depth.set_ylabel("Depth mm", fontsize=8)
        self.plot_axis_depth.tick_params(axis="y", which="major", labelsize=8)

        # Velocity
        self.plot_axis_velocity.set_ylabel("Velocity m/s", fontsize=8)
        self.plot_axis_velocity.tick_params(axis="y", which="major", labelsize=8)

        self.plot_axis_rg.set_ylabel("Rainfall mm/hr", fontsize=8)
        self.plot_axis_rg.tick_params(axis="y", which="major", labelsize=8)

        if self.has_plot_event():
            self.plot_axis_rg.set_xlim(
                self.get_plot_event().eventStart, self.get_plot_event().eventEnd
            )

        xmin, xmax = mpl_dates.num2date(self.plot_axis_rg.get_xlim())

        a_props = dict(boxstyle="round", facecolor="teal", alpha=0.5)

        if len(self.plotted_fms.plotFMs) == 1:
            self.plot_flow_stats_box = self.main_window_plot_widget.figure.text(
                0.05,
                0.95,
                "",
                transform=self.plot_axis_flow.transAxes,
                fontsize=8,
                verticalalignment="top",
                bbox=a_props,
            )
        else:
            self.plot_flow_stats_box = self.main_window_plot_widget.figure.text(
                0,
                -0.06,
                "",
                transform=self.plot_axis_flow.transAxes,
                fontsize=8,
                verticalalignment="top",
                bbox=a_props,
                wrap=True,
            )

        self.plot_depth_stats_box = self.main_window_plot_widget.figure.text(
            0.05,
            0.95,
            "",
            transform=self.plot_axis_depth.transAxes,
            fontsize=8,
            verticalalignment="top",
            bbox=a_props,
        )
        self.plot_velocity_stats_box = self.main_window_plot_widget.figure.text(
            0.05,
            0.95,
            "",
            transform=self.plot_axis_velocity.transAxes,
            fontsize=8,
            verticalalignment="top",
            bbox=a_props,
        )
        self.plot_rainfall_stats_box = self.main_window_plot_widget.figure.text(
            0.05,
            0.95,
            "",
            transform=self.plot_axis_rg.transAxes,
            fontsize=8,
            verticalalignment="top",
            bbox=a_props,
        )

        self.update_plotStats(xmin, xmax)

        self.plot_axis_flow.grid(True)
        self.plot_axis_rg.grid(True)

        self.plot_axis_depth.grid(True)
        self.plot_axis_velocity.grid(True)

        locator = AutoDateLocator(minticks=6, maxticks=15)
        formatter = ConciseDateFormatter(locator)
        self.plot_axis_velocity.xaxis.set_major_locator(locator)
        self.plot_axis_velocity.xaxis.set_major_formatter(formatter)

        self.main_window_plot_widget.figure.autofmt_xdate()
        self.main_window_plot_widget.figure.subplots_adjust(left=0.06, right=0.97, bottom=0.07, top=0.95)
        self.plot_axis_velocity.callbacks.connect("xlim_changed", self.onPlotXlimsChange)

        self.isBlank = False
        self.updateCanvas()

    def updateCanvas(self):
        self.main_window_plot_widget.event_connections.append(self.main_window_plot_widget.figure.canvas.mpl_connect("pick_event", self.onPick))
        self.main_window_plot_widget.pan_finished.connect(self.on_pan_finished)
        self.main_window_plot_widget.showToolbar(not self.isBlank)
        self.main_window_plot_widget.toolbar.lockNavigation(self.has_plot_event())

    def on_pan_finished(self, event_ax):
        if event_ax:  # Ensure axes are provided
            xmin, xmax = mpl_dates.num2date(event_ax.get_xlim())
            self.update_plotStats(xmin, xmax)

    def onPlotXlimsChange(self, event_ax):
        if not self.main_window_plot_widget._dragging:
            xmin, xmax = mpl_dates.num2date(event_ax.get_xlim())
            self.update_plotStats(xmin, xmax)

    def onPick(self, event):

        legline = event.artist

        origline = self.c_flow_legend_lines[legline]
        vis = not origline.get_visible()
        origline.set_visible(vis)

        origline = self.c_depth_legend_lines[legline]
        vis = not origline.get_visible()
        origline.set_visible(vis)

        origline = self.c_vel_legend_lines[legline]
        vis = not origline.get_visible()
        origline.set_visible(vis)
        # Change the alpha on the line in the legend so we can see what lines have been toggled
        if vis:
            legline.set_alpha(1.0)
        else:
            legline.set_alpha(0.2)

        self.main_window_plot_widget.figure.canvas.draw()

    def update_plotStats(self, xMin, xMax):

        # xmin_python_datetime = dt.fromordinal(int(xMin)) + timedelta(days=xMin%1)
        # xmax_python_datetime = dt.fromordinal(int(xMax)) + timedelta(days=xMax%1)
        # _____________________________________________
        # This section rounds the xmin & xmax times to the nearest 2 mins so that they can be searched for in the date time range

        # rounded_xmax_python_datetime = xmax_python_datetime
        rounded_xmax_python_datetime = xMax
        rounded_xmax_python_datetime += timedelta(minutes=0.5)
        rounded_xmax_python_datetime -= timedelta(
            minutes=rounded_xmax_python_datetime.minute % 2,
            seconds=rounded_xmax_python_datetime.second,
            microseconds=rounded_xmax_python_datetime.microsecond,
        )

        # rounded_xmin_python_datetime = xmin_python_datetime
        rounded_xmin_python_datetime = xMin
        rounded_xmin_python_datetime += timedelta(minutes=0.5)
        rounded_xmin_python_datetime -= timedelta(
            minutes=rounded_xmin_python_datetime.minute % 2,
            seconds=rounded_xmin_python_datetime.second,
            microseconds=rounded_xmin_python_datetime.microsecond,
        )

        self.plotted_fms.setPlotDateLimits(
            rounded_xmin_python_datetime, rounded_xmax_python_datetime
        )
        self.plotted_rgs.setPlotDateLimits(
            rounded_xmin_python_datetime, rounded_xmax_python_datetime
        )

        self.plot_axis_rg.set_ylim(
            [
                self.plotted_rgs.plotMinIntensity - (1),
                self.plotted_rgs.plotMaxIntensity
                + (self.plotted_rgs.plotMaxIntensity * 0.1),
            ]
        )
        self.plot_axis_flow.set_ylim(
            [
                self.plotted_fms.plotMinFlow - (1),
                self.plotted_fms.plotMaxFlow + (self.plotted_fms.plotMaxFlow * 0.1),
            ]
        )
        self.plot_axis_depth.set_ylim(
            [
                self.plotted_fms.plotMinDepth - (5),
                self.plotted_fms.plotMaxDepth + (self.plotted_fms.plotMaxDepth * 0.1),
            ]
        )
        self.plot_axis_velocity.set_ylim(
            [
                self.plotted_fms.plotMinVelocity - (0.2),
                self.plotted_fms.plotMaxVelocity
                + (self.plotted_fms.plotMaxVelocity * 0.5),
            ]
        )

        if len(self.plotted_fms.plotFMs) > 0:
            if len(self.plotted_fms.plotFMs) == 1:
                flow_textstr = f"Max Flow(m\u00B3/s) = {(self.plotted_fms.plotMaxFlow/1000):.3f}\nMin Flow(m\u00B3/s) = {(self.plotted_fms.plotMinFlow/1000):.3f}\nMean Flow(m\u00B3/s) = {(self.plotted_fms.plotAvgFlow/1000):.4f}\nVolume (m\u00B3) = {(self.plotted_fms.plotTotalVolume):.1f}"
            else:
                multi_volume_string = ""
                for aLine in self.plot_axis_flow.lines:

                    fm = self.plotted_fms.plotFMs[aLine.get_label()]
                    if fm is not None:
                        myVol = fm.getFlowVolumeBetweenDates(
                            rounded_xmin_python_datetime, rounded_xmax_python_datetime
                        )
                        if len(multi_volume_string) == 0:
                            multi_volume_string = (
                                "Volume(m\u00B3): "
                                + fm.monitorName
                                + " = "
                                + str(myVol)
                            )
                        else:
                            multi_volume_string = (
                                multi_volume_string
                                + ", "
                                + fm.monitorName
                                + " = "
                                + str(myVol)
                            )

                flow_textstr = multi_volume_string

            if self.plot_flow_stats_box is not None:
                self.plot_flow_stats_box.set_text(flow_textstr)

            if self.plot_depth_stats_box is not None:
                depth_textstr = (
                    "Max Depth(m) = "
                    + str(round(self.plotted_fms.plotMaxDepth / 1000, 3))
                    + "\nMin Depth(m) = "
                    + str(round(self.plotted_fms.plotMinDepth / 1000, 3))
                    + "\nMean Depth(m) = "
                    + str(round(self.plotted_fms.plotAvgDepth / 1000, 4))
                )
                self.plot_depth_stats_box.set_text(depth_textstr)

            if self.plot_velocity_stats_box is not None:
                velocity_textstr = (
                    "Max velocity(m/s) = "
                    + str(round(self.plotted_fms.plotMaxVelocity, 2))
                    + "\nMin Velocity(m/s) = "
                    + str(round(self.plotted_fms.plotMinVelocity, 2))
                    + "\nMean Velocity(m/s) = "
                    + str(round(self.plotted_fms.plotAvgVelocity, 3))
                )
                self.plot_velocity_stats_box.set_text(velocity_textstr)

        if len(self.plotted_rgs.plotRGs) > 0:
            if self.plot_rainfall_stats_box is not None:
                rainfall_textstr = (
                    "Max intensity(mm/hr) = "
                    + str(round(self.plotted_rgs.plotMaxIntensity, 1))
                    + "\nDepth(mm) = "
                    + str(round(self.plotted_rgs.plotTotalDepth, 1))
                    + "\nReturn Period(yr) = "
                    + str(round(self.plotted_rgs.plotReturnPeriod, 1))
                )
                self.plot_rainfall_stats_box.set_text(rainfall_textstr)

# class graphScatter:
#     def __init__(self, mw_pw: PlotWidget = None):
#         self.main_window_plot_widget: PlotWidget = mw_pw
#         # self.plot_widget = plot_widget
#         self.config = scatterGraphConfig()
#         self._initialize_attributes()
#         self._initialize_plot_options()
#         getBlankFigure(self.main_window_plot_widget)

#     def _initialize_attributes(self):
#         """Initialize all class attributes with default values"""
#         self.is_blank = True
#         self.plot_velocity_scattergraph = True
#         self.plotted_events = plottedSurveyEvents()
#         self._plot_flow_monitor: flowMonitor = None

#         # Plot axes
#         self.plot_axis_scatter = None
#         self.plot_axis_cbw = None
#         self.plot_axis_isoq = None
#         self.plot_axis_pipe_profile = None

#         # Data storage
#         self.cbw_data = {"depth": [], "flow": [], "velocity": []}
#         # self.pipe_profile = {"x": [], "y": [], "depth_prop": []}

#         # Axis limits
#         self.axis_limits = {
#             "x_min": 0, "x_max": 0,
#             "y_min": 0, "y_max": 0,
#             "plot_x_min": 0, "plot_x_max": 0
#         }

#         # Pipe stations
#         self.pipe_stations = {"in": 0, "out": 0}
#         self.axis_ratio = 1
#         self.pipe_exag = 0.1

#         # Legend
#         self.scatter_legend_lines = None
#         self.scatter_lines = None

#     def _initialize_plot_options(self):
#         """Initialize plotting options with default values"""
#         self.plot_options = {
#             "plot_fp_data": True,
#             "ignore_data_above_soffit": False,
#             "ignore_zeros": False,
#             "label_on_hover": False,
#             "plot_model_data": False,
#             "show_pipe_profile": True,
#             "plot_cbw_line": True,
#             "plot_iso_q_lines": True,
#             "iso_q_lines_count": 2,
#             "iso_q_lower_bound": 1,
#             "iso_q_upper_bound": 10
#         }

#     @property
#     def flow_monitor(self) -> flowMonitor:
#         return self._plot_flow_monitor

#     @flow_monitor.setter
#     def flow_monitor(self, fm: flowMonitor):
#         self._plot_flow_monitor = fm
#         if fm and self.plot_options["plot_model_data"]:
#             self.plot_options["plot_model_data"] = fm.hasModelData

#     def _calculate_gradient(self) -> float:
#         """Calculate pipe gradient from model data"""
#         if (self.flow_monitor.modelDataPipeUSInvert > 0 and
#             self.flow_monitor.modelDataPipeDSInvert > 0):
#             gradient = ((self.flow_monitor.modelDataPipeUSInvert -
#                         self.flow_monitor.modelDataPipeDSInvert) /
#                        self.flow_monitor.modelDataPipeLength)
#             return max(gradient, 0.00001)
#         return 0.00001

#     def _clear_figure(self):
#         self.main_window_plot_widget.figure.clear()

#         if self.plot_axis_scatter is not None:
#             self.plot_axis_scatter.clear()
#             self.plot_axis_scatter = None
#         if self.plot_axis_cbw is not None:
#             self.plot_axis_cbw.clear()
#             self.plot_axis_cbw = None
#         if self.plot_axis_isoq is not None:
#             self.plot_axis_isoq.clear()
#             self.plot_axis_isoq = None
#         if self.plot_axis_pipe_profile is not None:
#             self.plot_axis_pipe_profile.clear()
#             self.plot_axis_pipe_profile = None


#     # def _compute_cbw_values_alt(self) -> Dict[str, List[float]]:
#     #     # Convert diameter from mm to meters
#     #     diameter_m = self.flow_monitor.modelDataPipeDia / 1000.0
#     #     roughness_m = self.flow_monitor.modelDataPipeRoughness / 1000.0
#     #     gravity = 9.81  # m/s²
#     #     gradient = ((self._plot_flow_monitor.modelDataPipeUSInvert - self._plot_flow_monitor.modelDataPipeDSInvert) / self._plot_flow_monitor.modelDataPipeLength if self._plot_flow_monitor.modelDataPipeUSInvert > 0 and self._plot_flow_monitor.modelDataPipeDSInvert > 0 else 0)
#     #     gradient = max(gradient, 0.00001)


#     #     # Initialize result dictionary
#     #     self.cbw_data = {"depth": [], "flow": [], "velocity": []}

#     #     for proportion in self.config.depth_proportions:
#     #         # Calculate depth for the current proportion
#     #         depth = proportion * diameter_m
#     #         if depth <= 0:
#     #             self.cbw_data["depth"].append(0)
#     #             self.cbw_data["flow"].append(0)
#     #             self.cbw_data["velocity"].append(0)
#     #             continue

#     #         # Calculate hydraulic radius and area
#     #         wetted_perimeter = diameter_m * math.pi * proportion
#     #         wetted_area = (diameter_m**2 / 4) * math.acos(1 - 2 * proportion) - (
#     #             (diameter_m / 2) * math.sqrt(2 * depth * diameter_m - depth**2)
#     #         )
#     #         hydraulic_radius = wetted_area / wetted_perimeter

#     #         # Solve for friction factor using the Colebrook-White equation
#     #         def colebrook_white(f: float, re: float, k: float, d: float) -> float:
#     #             return -2 * math.log10(k / (3.7 * d) + 2.51 / (re * math.sqrt(f))) - 1 / math.sqrt(f)

#     #         # Iterative solution for the friction factor
#     #         velocity = 1.0  # Initial velocity guess
#     #         tolerance = 1e-6
#     #         max_iterations = 50
#     #         friction_factor = 0.02  # Initial guess
#     #         iteration = 0
#     #         while iteration < max_iterations:
#     #             reynolds_number = (velocity * hydraulic_radius * 4) / (1e-6)  # Assume kinematic viscosity ~1e-6 m²/s
#     #             f_new = colebrook_white(friction_factor, reynolds_number, roughness_m, diameter_m)
#     #             if abs(f_new - friction_factor) < tolerance:
#     #                 break
#     #             friction_factor = f_new
#     #             iteration += 1

#     #         # Calculate flow and velocity
#     #         slope_term = math.sqrt(friction_factor * gradient)
#     #         velocity = (hydraulic_radius ** (2 / 3)) * slope_term
#     #         flow = velocity * wetted_area

#     #         # Append values to the result dictionary
#     #         self.cbw_data["depth"].append(depth)
#     #         self.cbw_data["flow"].append(flow)
#     #         self.cbw_data["velocity"].append(velocity)

#     #     return True

#     # def _compute_cbw_values_alt(self) -> Dict[str, List[float]]:
#     #     # Convert diameter from mm to meters
#     #     diameter_m = self.flow_monitor.modelDataPipeDia / 1000.0
#     #     roughness_m = self.flow_monitor.modelDataPipeRoughness / 1000.0
#     #     gravity = 9.81  # m/s²
#     #     gradient = ((self._plot_flow_monitor.modelDataPipeUSInvert - self._plot_flow_monitor.modelDataPipeDSInvert) / self._plot_flow_monitor.modelDataPipeLength
#     #                 if self._plot_flow_monitor.modelDataPipeUSInvert > 0 and self._plot_flow_monitor.modelDataPipeDSInvert > 0 else 0)
#     #     gradient = max(gradient, 0.00001)  # Ensure gradient is positive

#     #     # Initialize result dictionary
#     #     self.cbw_data = {"depth": [], "flow": [], "velocity": []}

#     #     for proportion in self.config.depth_proportions:
#     #         # Calculate depth for the current proportion
#     #         depth = proportion * diameter_m
#     #         if depth <= 0:
#     #             self.cbw_data["depth"].append(0)
#     #             self.cbw_data["flow"].append(0)
#     #             self.cbw_data["velocity"].append(0)
#     #             continue

#     #         # Calculate hydraulic radius and wetted area
#     #         wetted_perimeter = diameter_m * math.pi * proportion
#     #         wetted_area = (diameter_m**2 / 4) * math.acos(1 - 2 * proportion) - (
#     #             (diameter_m / 2) * math.sqrt(2 * depth * diameter_m - depth**2)
#     #         )
#     #         hydraulic_radius = wetted_area / wetted_perimeter

#     #         # Solve for friction factor using the Colebrook-White equation
#     #         def colebrook_white(f: float, re: float, k: float, d: float) -> float:
#     #             if f <= 0:
#     #                 raise ValueError("Friction factor f must be positive.")
#     #             if re <= 0 or d <= 0 or k < 0:
#     #                 raise ValueError("Reynolds number, diameter, and roughness must be positive.")
#     #             try:
#     #                 return -2 * math.log10(k / (3.7 * d) + 2.51 / (re * math.sqrt(f))) - 1 / math.sqrt(f)
#     #             except ValueError as e:
#     #                 raise ValueError(f"Math domain error in Colebrook-White equation: {e}")

#     #         # Iterative solver for friction factor
#     #         def solve_friction_factor(re: float, k: float, d: float, initial_guess=0.02, tolerance=1e-6, max_iterations=50) -> float:
#     #             f = initial_guess
#     #             for i in range(max_iterations):
#     #                 try:
#     #                     f_new = colebrook_white(f, re, k, d)
#     #                     if abs(f_new - f) < tolerance:  # Convergence check
#     #                         return f_new
#     #                     f = f_new
#     #                 except ValueError:
#     #                     raise ValueError("Invalid input caused divergence in Colebrook-White solution.")
#     #             raise RuntimeError("Colebrook-White equation did not converge within the maximum number of iterations.")

#     #         # Calculate Reynolds number and friction factor
#     #         velocity = 1.0  # Initial velocity guess
#     #         reynolds_number = max((velocity * hydraulic_radius * 4) / (1e-6), 0)  # Ensure Re > 0
#     #         try:
#     #             friction_factor = solve_friction_factor(reynolds_number, roughness_m, diameter_m)
#     #         except ValueError as e:
#     #             # Handle failure to solve for friction factor
#     #             self.cbw_data["depth"].append(depth)
#     #             self.cbw_data["flow"].append(0)
#     #             self.cbw_data["velocity"].append(0)
#     #             continue

#     #         # Calculate flow and velocity
#     #         slope_term = math.sqrt(friction_factor * gradient)
#     #         velocity = (hydraulic_radius ** (2 / 3)) * slope_term
#     #         flow = velocity * wetted_area

#     #         # Append values to the result dictionary
#     #         self.cbw_data["depth"].append(depth)
#     #         self.cbw_data["flow"].append(flow)
#     #         self.cbw_data["velocity"].append(velocity)

#     #     return True


#     def _compute_cbw_values(self) -> bool:
#         self.cbw_data = {"depth": [], "flow": [], "velocity": []}
#         if (
#             self.flow_monitor.modelDataPipeLength <= 0
#             or self.flow_monitor.modelDataPipeDia <= 0
#             or self.flow_monitor.modelDataPipeRoughness <= 0
#             or self.flow_monitor.modelDataPipeShape == ""
#             or self.flow_monitor.modelDataPipeHeight <= 0
#         ):
#             return False

#         # gradient = ((self._plot_flow_monitor.modelDataPipeUSInvert - self._plot_flow_monitor.modelDataPipeDSInvert) / self._plot_flow_monitor.modelDataPipeLength if self._plot_flow_monitor.modelDataPipeUSInvert > 0 and self._plot_flow_monitor.modelDataPipeDSInvert > 0 else 0)
#         # gradient = max(gradient, 0.00001)
#         gradient = self._calculate_gradient()

#         # Constants
#         pipe_diameter_m = self.flow_monitor.modelDataPipeDia / 1000  # Convert mm to meters
#         roughness_m = self.flow_monitor.modelDataPipeRoughness / 1000  # Convert mm to meters
#         g = 9.807  # Gravitational acceleration (m/s²)

#         # Initialize outputs
#         self.cbw_data['depth'] = [0]  # Start with zero depth
#         self.cbw_data['flow'] = [0]   # Start with zero flow
#         self.cbw_data['velocity'] = [0]  # Start with zero velocity

#         # Loop through depth proportions
#         for depth_ratio in self.config.depth_proportions:
#             # 1. Calculate flow area (A) and wetted perimeter (P)
#             depth = pipe_diameter_m * depth_ratio
#             theta = 2 * math.acos(1 - 2 * depth_ratio)  # Angle subtended by the flow
#             flow_area = (theta - math.sin(theta)) / 8 * math.pi * pipe_diameter_m**2
#             wetted_perimeter = pipe_diameter_m * theta / (2 * math.pi)

#             # 2. Calculate hydraulic radius (R)
#             hydraulic_radius = flow_area / wetted_perimeter

#             # 3. Calculate friction factor using the Swamee-Jain approximation
#             reynolds_number = (4 * flow_area * math.sqrt(gradient * hydraulic_radius * g)) / (1.002e-3)  # Kinematic viscosity of water
#             if reynolds_number > 4000:  # Turbulent flow
#                 friction_factor = 0.25 / (math.log10((roughness_m / (3.7 * pipe_diameter_m)) + (5.74 / reynolds_number**0.9)))**2
#             else:  # Laminar flow (fallback)
#                 friction_factor = 64 / reynolds_number if reynolds_number > 0 else 0

#             # 4. Calculate velocity and flow
#             velocity = math.sqrt(gradient * hydraulic_radius * g / friction_factor)
#             flow = flow_area * velocity

#             # Append results
#             self.cbw_data['depth'].append(depth * 1000)  # Convert to mm
#             self.cbw_data['flow'].append(flow * 1000)  # Convert to L/s
#             self.cbw_data['velocity'].append(velocity)

#         return True

#     # def _compute_cbw_values(self) -> Dict[str, List[float]]:
#     #     """Compute Colebrook-White equation values"""
#     #     self.cbw_data = {"depth": [], "flow": [], "velocity": []}
#     #     pipe_dia = self.flow_monitor.modelDataPipeDia
#     #     roughness = self.flow_monitor.modelDataPipeRoughness / 1000
#     #     gradient = ((self._plot_flow_monitor.modelDataPipeUSInvert - self._plot_flow_monitor.modelDataPipeDSInvert) / self._plot_flow_monitor.modelDataPipeLength if self._plot_flow_monitor.modelDataPipeUSInvert > 0 and self._plot_flow_monitor.modelDataPipeDSInvert > 0 else 0)
#     #     gradient = max(gradient, 0.00001)

#     #     for depth_prop in self.config.depth_proportions:
#     #         depth = depth_prop * pipe_dia

#     #         # Calculate hydraulic parameters
#     #         theta = math.acos(1 - 2 * depth_prop) * pipe_dia / 1000
#     #         flow_area = ((math.acos(1 - 2 * depth_prop) / 4 -
#     #                      (0.5 - depth_prop) *
#     #                      (depth_prop - depth_prop ** 2) ** 0.5) *
#     #                     (pipe_dia / 1000) ** 2)
#     #         hydraulic_radius = flow_area / theta

#     #         # Calculate flow using Colebrook-White equation
#     #         velocity_term = (32 * hydraulic_radius * 9.807 * gradient) ** 0.5
#     #         roughness_term = roughness / (14.8 * hydraulic_radius)
#     #         reynolds_term = 1.255 * 0.00000135 / (hydraulic_radius * velocity_term)

#     #         friction_factor = -2 * math.log10(roughness_term + reynolds_term)
#     #         velocity = -velocity_term * friction_factor
#     #         flow = flow_area * velocity * 1000  # Convert to l/s

#     #         self.cbw_data["depth"].append(depth)
#     #         self.cbw_data["flow"].append(flow)
#     #         self.cbw_data["velocity"].append(velocity)

#     #     # Add zero point
#     #     self.cbw_data["depth"].insert(0, 0)
#     #     self.cbw_data["flow"].insert(0, 0)
#     #     self.cbw_data["velocity"].insert(0, 0)

#     #     return True

#     def _calculate_axis_limits(self, x_values: np.ndarray, y_values: np.ndarray):
#         """Calculate axis limits with buffer"""
#         x_range = np.ptp(x_values)
#         y_range = np.ptp(y_values)

#         self.axis_limits.update({
#             "x_min": np.min(x_values) - (x_range * (self.config.x_buffer_factor - 1) / 2),
#             "x_max": np.max(x_values) + (x_range * (self.config.x_buffer_factor - 1) / 2),
#             "y_min": np.min(y_values) - (y_range * (self.config.y_buffer_factor - 1) / 2),
#             "y_max": np.max(y_values) + (y_range * (self.config.y_buffer_factor - 1) / 2)
#         })

#     def _update_scatter_graph(self):
#         """Update the scatter graph with current data"""
#         self.scatter_lines = []
#         colors = cycle(self.config.plot_colors)

#         # Get data
#         dates = np.array(self.flow_monitor.dateRange)
#         depth = np.array(self.flow_monitor.depthDataRange)
#         x_values = (np.array(self.flow_monitor.velocityDataRange) if self.plot_velocity_scattergraph else np.array(self.flow_monitor.flowDataRange))
#         # Filter data
#         mask = np.ones(len(depth), dtype=bool)
#         if self.plot_options["ignore_data_above_soffit"] and self.flow_monitor.hasModelData:
#             mask &= depth <= self.flow_monitor.modelDataPipeDia
#         if self.plot_options["ignore_zeros"]:
#             mask &= x_values != 0

#         dates = dates[mask]
#         depth = depth[mask]
#         x_values = x_values[mask]

#         # Create scatter plot
#         self.plot_axis_scatter = self.main_window_plot_widget.figure.subplots(1)

#         if self.plot_options["plot_fp_data"]:
#             line = self.plot_axis_scatter.scatter(
#                 x_values, depth, s=5, label="Full Period", color="gray"
#             )
#             self.scatter_lines.append(line)

#         # Plot events
#         for event in self.plotted_events.plotEvents.values():
#             event_mask = (dates >= event.eventStart) & (dates <= event.eventEnd)
#             event_x = x_values[event_mask]
#             event_depth = depth[event_mask]

#             line = self.plot_axis_scatter.scatter(
#                 event_x, event_depth, s=5,
#                 label=event.eventName, color=next(colors)
#             )
#             self.scatter_lines.append(line)

#         # Set axis limits and labels
#         self._calculate_axis_limits(x_values, depth)
#         self._set_axis_properties()
#         self._create_legend()

#     def _set_axis_properties(self):
#         """Set axis properties including labels and grid"""
#         self.plot_axis_scatter.set_xlim(self.axis_limits["x_min"], self.axis_limits["x_max"])
#         self.plot_axis_scatter.set_ylim(self.axis_limits["y_min"], self.axis_limits["y_max"])

#         self.plot_axis_scatter.set_ylabel("Depth (mm)", fontsize=8)
#         xlabel = "Velocity (m/s)" if self.plot_velocity_scattergraph else "Flow (l/s)"
#         self.plot_axis_scatter.set_xlabel(xlabel, fontsize=8)

#         if self.flow_monitor:
#             self.plot_axis_scatter.set_title(
#                 self.flow_monitor.monitorName, color="grey", fontsize=15
#             )
#         self.plot_axis_scatter.grid(True)

#     def _create_legend(self):
#         """Create and configure the plot legend"""
#         legend = self.plot_axis_scatter.legend(loc="best")
#         self.scatter_legend_lines = {}

#         for leg_line, orig_line in zip(legend.legend_handles, self.scatter_lines):
#             leg_line.set_picker(5)
#             self.scatter_legend_lines[leg_line] = orig_line

#     def _update_cbw_line(self):
#         """Update the Colebrook-White line"""
#         if not (self.plot_options["plot_model_data"] and
#                 self.plot_options["plot_cbw_line"]):
#             return

#         if self.plot_axis_cbw is not None:
#             self.plot_axis_cbw.remove()
#             self.plot_axis_cbw = None

#         # self._compute_cbw_values_alt()
#         # test = self.cbw_data.copy()
#         if self._compute_cbw_values() and self.flow_monitor.modelDataPipeShape == "CIRC":
#             self.plot_axis_cbw = self.plot_axis_scatter.twinx()
#             x_values = (self.cbw_data["velocity"] if self.plot_velocity_scattergraph
#                        else self.cbw_data["flow"])

#             self.plot_axis_cbw.plot(
#                 x_values,
#                 self.cbw_data["depth"],
#                 linewidth=0.75,
#                 linestyle="dotted",
#                 color="black",
#                 label="CBW"
#             )

#             self._calculate_axis_limits(x_values, self.cbw_data["depth"])
#             # self._update_axis_limits_with_cbw(y_values)
#             self._set_axis_properties()

#     def _update_pipe_profile_lines(self):

#         if self.plot_axis_pipe_profile is not None:
#             self.plot_axis_pipe_profile.remove()
#             self.plot_axis_pipe_profile = None

#         if self.plot_options["plot_model_data"] and self.plot_options["show_pipe_profile"]:

#             self.plot_axis_pipe_profile = self.plot_axis_scatter.twinx()
#             self.plot_axis_pipe_profile.set_ylim(self.axis_limits['y_min'], self.axis_limits['y_max'])
#             self.plot_axis_pipe_profile.axes.yaxis.set_visible(False)

#             pipe_station_in = self.axis_limits['x_min']
#             pipe_station_out= self.axis_limits['x_max']
#             pipe_profile_depth_prop = [i / 24 for i in range(25)]

#             pipe_profile_x = []
#             pipe_profile_y = []

#             # Pipe profile calculations
#             pipe_profile_x, pipe_profile_y = self.calculate_pipe_profile(pipe_profile_depth_prop, pipe_station_out, invert=True)
#             x_part, y_part = self.calculate_pipe_profile(reversed(pipe_profile_depth_prop), pipe_station_in, invert=True)
#             pipe_profile_x += x_part
#             pipe_profile_y += y_part
#             pipe_profile_x.append(pipe_station_out)
#             pipe_profile_y.append(0)

#             self.plot_pipe_profile(pipe_profile_x, pipe_profile_y)

#             # Half-pipe calculations (left and right arcs)
#             for station, invert in [
#                 (pipe_station_out, False),
#                 (pipe_station_in, False),
#             ]:
#                 half_profile_x, half_profile_y = self.calculate_pipe_profile(pipe_profile_depth_prop[: len(pipe_profile_depth_prop) // 2 + 1], station, invert=invert,)
#                 self.plot_pipe_profile(half_profile_x, half_profile_y)

#             # Bottom arc calculations
#             bottom_arc_x, bottom_arc_y = [], []
#             for depth in pipe_profile_depth_prop:
#                 angle = math.radians((depth * 180) + 180)
#                 bottom_arc_x.append((((self.flow_monitor.modelDataPipeDia / 2) / self.axis_ratio) * math.sin(angle)) + pipe_station_in)
#                 bottom_arc_y.append((self.flow_monitor.modelDataPipeDia / 2) + ((self.flow_monitor.modelDataPipeDia / 2) * math.cos(angle)))
#             self.plot_pipe_profile(bottom_arc_x, bottom_arc_y)

#     def plot_pipe_profile(self, profile_x, profile_y):
#         self.plot_axis_pipe_profile.plot(profile_x, profile_y, linewidth=1.5, color="black", label="Pipe Profile")

#     def calculate_pipe_profile(self, depth_props, station, invert=False):
#         profile_x, profile_y = [], []
#         for depth in depth_props:
#             angle = math.radians((depth * 360) + (180 if invert else 0))
#             profile_x.append((math.sin(angle) * ((self.flow_monitor.modelDataPipeDia / 2) / self.axis_ratio) * self.pipe_exag) + station)
#             profile_y.append(depth * self.flow_monitor.modelDataPipeDia)
#         return profile_x, profile_y

#     # def _update_pipe_profile(self):
#     #     """Update the pipe profile visualization"""
#     #     if not (self.plot_options["plot_model_data"] and
#     #             self.plot_options["show_pipe_profile"]):
#     #         return

#     #     if self.plot_axis_pipe_profile is not None:
#     #         self.plot_axis_pipe_profile.remove()
#     #         self.plot_axis_pipe_profile = None

#     #     self.plot_axis_pipe_profile = self.plot_axis_scatter.twinx()
#     #     self._calculate_pipe_profile()
#     #     self._plot_pipe_profile()

#     # def _calculate_pipe_profile(self):
#     #     """Calculate pipe profile coordinates"""
#     #     pipe_dia = self.flow_monitor.modelDataPipeDia
#     #     proportions = np.linspace(0, 1, 25)

#     #     # Calculate profile points
#     #     theta = np.radians(proportions * 360 + 180)
#     #     radius = pipe_dia / 2 / self.axis_ratio

#     #     x_out = np.sin(theta) * radius * self.config.pipe_exaggeration + self.pipe_stations["out"]
#     #     x_in = np.sin(theta) * radius * self.config.pipe_exaggeration + self.pipe_stations["in"]
#     #     y = proportions * pipe_dia

#     #     self.pipe_profile["x"] = np.concatenate([x_out, x_in[::-1], [x_out[0]]])
#     #     self.pipe_profile["y"] = np.concatenate([y, y[::-1], [y[0]]])

#     # def _plot_pipe_profile(self):
#     #     """Plot the pipe profile"""
#     #     self.plot_axis_pipe_profile.plot(
#     #         self.pipe_profile["x"],
#     #         self.pipe_profile["y"],
#     #         linewidth=1.5,
#     #         color="black",
#     #         label="Pipe Profile"
#     #     )
#     #     self.plot_axis_pipe_profile.set_ylim(
#     #         self.axis_limits["y_min"],
#     #         self.axis_limits["y_max"]
#     #     )
#     #     self.plot_axis_pipe_profile.axes.yaxis.set_visible(False)

#     def _update_iso_lines(self):
#         """Update iso-Q lines on the plot"""
#         if not (self.plot_options["plot_model_data"] and
#                 self.plot_options["plot_iso_q_lines"]):
#             return

#         if self.plot_axis_isoq is not None:
#             self.plot_axis_isoq.remove()
#             self.plot_axis_isoq = None

#         self.plot_axis_isoq = self.plot_axis_scatter.twinx()
#         self._calculate_and_plot_iso_lines()

#     def _calculate_and_plot_iso_lines(self):
#         """Calculate and plot iso-Q lines"""
#         range_values = (self.plot_options["iso_q_upper_bound"] - self.plot_options["iso_q_lower_bound"])
#         step_value = range_values / (self.plot_options["iso_q_lines_count"] - 1)

#         for i in range(self.plot_options["iso_q_lines_count"]):
#             value = self.plot_options["iso_q_lower_bound"] + (i * step_value)
#             self._plot_single_iso_line(value, i)

#     def _plot_single_iso_line(self, value: float, index: int):
#         """Plot a single iso-Q line with the given value"""
#         iso_values = []
#         iso_depths = []
#         pipe_dia = self.flow_monitor.modelDataPipeDia

#         for depth_prop in self.config.depth_proportions:
#             depth = pipe_dia * depth_prop

#             if self.plot_velocity_scattergraph:
#                 # Calculate velocity for given flow rate
#                 flow_area = self._calculate_flow_area(pipe_dia, depth)
#                 velocity = (value / 1000) / flow_area

#                 if velocity <= self.pipe_stations["out"]:
#                     iso_depths.append(depth)
#                     iso_values.append(velocity)
#             else:
#                 # Calculate flow for given velocity
#                 flow_area = self._calculate_flow_area(pipe_dia, depth)
#                 flow = value * flow_area * 1000  # Convert to l/s

#                 if flow <= self.pipe_stations["out"]:
#                     iso_depths.append(depth)
#                     iso_values.append(flow)

#         if not iso_values:
#             return

#         # Add point at maximum velocity/flow if plotting velocity
#         if self.plot_velocity_scattergraph:
#             iso_values.insert(0, self.axis_limits["x_max"])
#             iso_depths.insert(0, self._calculate_flow_depth(
#                 pipe_dia, (value / 1000) / self.axis_limits["x_max"]
#             ))

#         # Plot the line
#         self.plot_axis_isoq.plot(
#             iso_values,
#             iso_depths,
#             linewidth=1,
#             linestyle="dashdot",
#             color="forestgreen",
#             label=f"{value:.3g} {'l/s' if self.plot_velocity_scattergraph else 'm/s'}"
#         )

#         # Add label to the line
#         self._add_iso_line_label(iso_values, iso_depths, index)

#     def _add_iso_line_label(self, values: List[float], depths: List[float], index: int):
#         """Add a label to an iso-Q line"""
#         label_props = dict(boxstyle="round", facecolor="white", alpha=0.5)

#         # Calculate label position
#         x_pos = min(values) + (max(values) - min(values)) * (
#             0.1 + (index * (0.225 / (self.plot_options["iso_q_lines_count"] - 1)))
#         )

#         # Find closest point on line to desired x position
#         closest_idx = min(range(len(values)),
#                          key=lambda i: abs(values[i] - x_pos))

#         if values[closest_idx] is not None and depths[closest_idx] is not None:
#             self.plot_axis_isoq.text(
#                 values[closest_idx],
#                 depths[closest_idx],
#                 self.plot_axis_isoq.axes.lines[-1].get_label(),
#                 bbox=label_props
#             )

#     def _calculate_flow_area(self, pipe_dia: float, depth: float) -> float:
#         """Calculate flow area for circular pipe"""
#         radius = pipe_dia / 2000  # Convert to meters
#         depth_m = depth / 1000    # Convert to meters

#         if depth_m >= 2 * radius:  # Full pipe
#             return math.pi * radius ** 2

#         theta = 2 * math.acos((radius - depth_m) / radius)
#         return (radius ** 2 * (theta - math.sin(theta))) / 2

#     def _calculate_flow_depth(self, pipe_dia: float, flow_area: float) -> float:
#         """Calculate flow depth from area using binary search"""
#         target_area = flow_area
#         tolerance = 0.0001
#         min_depth = 0
#         max_depth = pipe_dia

#         while max_depth - min_depth > tolerance:
#             depth = (min_depth + max_depth) / 2
#             area = self._calculate_flow_area(pipe_dia, depth)

#             if abs(area - target_area) < tolerance:
#                 return depth
#             elif area < target_area:
#                 min_depth = depth
#             else:
#                 max_depth = depth

#         return (min_depth + max_depth) / 2

#     def update_plot(self):
#         """Main method to update the entire plot"""
#         self._clear_figure()

#         if not self.flow_monitor:
#             getBlankFigure(self.main_window_plot_widget)
#             return

#         self._update_scatter_graph()
#         self._update_cbw_line()
#         self._update_pipe_profile_lines()
#         # self._update_pipe_profile()
#         self._update_iso_lines()
#         self._adjust_plot_layout()
#         self._update_canvas()

#     def _adjust_plot_layout(self):
#         """Adjust the plot layout and margins"""
#         self.main_window_plot_widget.figure.subplots_adjust(
#             left=0.05, right=0.95, bottom=0.05, top=0.95
#         )
#         self.main_window_plot_widget.figure.tight_layout()
#         self.is_blank = False

#     def _update_canvas(self):
#         """Update the plot canvas and connect events"""
#         self.main_window_plot_widget.event_connections.append(
#             self.main_window_plot_widget.figure.canvas.mpl_connect("pick_event", self._on_pick)
#         )
#         self.main_window_plot_widget.showToolbar(not self.is_blank)
#         self.main_window_plot_widget.toolbar.lockNavigation(False)

#     def _on_pick(self, event: PickEvent):
#         """Handle pick events on the legend"""
#         legline = event.artist
#         origline = self.scatter_legend_lines[legline]
#         vis = not origline.get_visible()

#         origline.set_visible(vis)
#         legline.set_alpha(1.0 if vis else 0.2)

#         self.main_window_plot_widget.figure.canvas.draw()

@dataclass
class scatterGraphConfig:
    depth_proportions: List[float] = field(default_factory=lambda: [
        0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.15, 0.2, 0.25, 
        0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 
        0.75, 0.8, 0.85, 0.9, 0.95, 0.96, 0.97, 0.98, 0.99, 1
    ])
    pipe_profile_depth_prop = [i / 24 for i in range(25)]
    x_buffer_factor: float = 1.25
    y_buffer_factor: float = 1.5
    pipe_exaggeration: float = 0.1
    plot_colors: List[str] = field(default_factory=lambda: [
        "aqua", "red", "lime", "fuchsia", "green", "teal", 
        "black", "navy", "olive", "purple", "maroon", "silver", 
        "blue", "yellow", "Gold", "crimson"
    ])

class graphScatter:

    # depthProportion = [
    #     0.01,
    #     0.02,
    #     0.03,
    #     0.04,
    #     0.05,
    #     0.1,
    #     0.15,
    #     0.2,
    #     0.25,
    #     0.3,
    #     0.35,
    #     0.4,
    #     0.45,
    #     0.5,
    #     0.55,
    #     0.6,
    #     0.65,
    #     0.7,
    #     0.75,
    #     0.8,
    #     0.85,
    #     0.9,
    #     0.95,
    #     1,
    # ]
    xBufferFactor: float = 1.25
    yBufferFactor: float = 1.5
    pipeExag: float = 0.1

    def __init__(self, mw_pw: PlotWidget = None):

        self.main_window_plot_widget: PlotWidget = mw_pw
        self.config = scatterGraphConfig()
        self._initialize_attributes()
        self._initialize_plot_options()
        getBlankFigure(self.main_window_plot_widget)
        self.isBlank: bool = True

        # self.__plotFM: flowMonitor = None
        # self.plotAxisScatter: axes.Axes = None
        # self.plot_axis_cbw: axes.Axes = None
        # self.plotAxisIsoQ: axes.Axes = None
        # self.plot_axis_pipe_profile: axes.Axes = None
        # self.plottedEvents: plottedSurveyEvents = None
        self.CBW_depth: list[float] = []
        self.CBW_flow: list[float] = []
        self.CBW_velocity: list[float] = []
        # self.pipeProfileX: list[float] = []
        # self.pipeProfileY: list[float] = []
        # self.pipeProfileDepthProp: list[float] = []
        # self.xAxisMin: float = 0
        # self.xAxisMax: float = 0
        # self.yAxisMin: float = 0
        # self.yAxisMax: float = 0
        # self.plotXMin: float = 0
        # self.plotXMax: float = 0
        # self.pipeInStation: float = 0
        self.pipeOutStation: float = 0
        self.axisRatio: float = 1

        self.cScatterLegendLines: list[lines.Line2D] = None
        self.cScatterLines: list[lines.Line2D] = None

    def _initialize_attributes(self):
        """Initialize all class attributes with default values"""
        self.is_blank = True
        # self.plot_velocity_scattergraph = True
        self.plotted_events = plottedSurveyEvents()
        self.plotVelocityScattergraph: bool = True
        # self.plottedEvents = plottedSurveyEvents()
        self._plot_flow_monitor: flowMonitor = None

        # Plot axes
        self.plot_axis_scatter: axes.Axes = None
        self.plot_axis_cbw: axes.Axes = None
        self.plot_axis_isoq: axes.Axes = None
        self.plot_axis_pipe_profile: axes.Axes = None

        # Data storage
        self.cbw_data = {"depth": [], "flow": [], "velocity": []}
        # self.pipe_profile = {"x": [], "y": [], "depth_prop": []}

        # Axis limits
        self.axis_limits = {
            "x_min": 0, "x_max": 0, 
            "y_min": 0, "y_max": 0,
            "plot_x_min": 0, "plot_x_max": 0
        }

        # Pipe stations
        self.pipe_stations = {"in": 0, "out": 0}
        self.axis_ratio = 1
        self.pipe_exag = 0.1

        # Legend
        self.scatter_legend_lines = None
        self.scatter_lines = None

        self.useOriginal = True

    def _initialize_plot_options(self):
        """Initialize plotting options with default values"""
        self.plotFPData: bool = True
        self.ignoreDataAboveSoffit: bool = False
        self.ignoreZeros: bool = False
        self.labelOnHover: bool = False
        self.plotModelData: bool = False
        self.showPipeProfile: bool = True
        self.plotCBWLine: bool = True
        self.plotIsoQLines: bool = True
        self.noOfIsoQLines: float = 2
        self.isoQLBound: float = 1
        self.isoQUBound: float = 10

        # self.plot_options = {
        #     "plot_fp_data": True,
        #     "ignore_data_above_soffit": False,
        #     "ignore_zeros": False,
        #     "label_on_hover": False,
        #     "plot_model_data": False,
        #     "show_pipe_profile": True,
        #     "plot_cbw_line": True,
        #     "plot_iso_q_lines": True,
        #     "iso_q_lines_count": 2,
        #     "iso_q_lower_bound": 1,
        #     "iso_q_upper_bound": 10
        # }

    @property
    def plot_flow_monitor(self) -> flowMonitor:
        return self._plot_flow_monitor

    @plot_flow_monitor.setter
    def plot_flow_monitor(self, fm: flowMonitor):
        self._plot_flow_monitor = fm
        if fm and self.plotModelData:
            self.plotModelData = fm.hasModelData    

    def update_plot(self):

        self.clearFigure()
        if self._plot_flow_monitor is not None:
            self.updateScattergraphLines()
            self._update_cbw_line()
            # self.updateCBWLine()
            self.updatePipeProfileLines()
            self.updateIsoLines()
            # self.plotFigure.subplots_adjust(
            #     left=0.01, right=0.99, bottom=0.01, top=0.99)
            self.main_window_plot_widget.figure.subplots_adjust(
                left=0.05, right=0.95, bottom=0.05, top=0.95
            )
            self.isBlank = False
        else:
            getBlankFigure(self.main_window_plot_widget)
            self.isBlank = True

        self.updateCanvas()

    def clearFigure(self):
        self.main_window_plot_widget.figure.clear()

        if self.plot_axis_scatter is not None:
            self.plot_axis_scatter.clear()
            self.plot_axis_scatter = None
        if self.plot_axis_cbw is not None:
            self.plot_axis_cbw.clear()
            self.plot_axis_cbw = None
        if self.plot_axis_isoq is not None:
            self.plot_axis_isoq.clear()
            self.plot_axis_isoq = None
        if self.plot_axis_pipe_profile is not None:
            self.plot_axis_pipe_profile.clear()
            self.plot_axis_pipe_profile = None

        # Axis limits
        self.axis_limits = {
            "x_min": 0, "x_max": 0, 
            "y_min": 0, "y_max": 0,
            "plot_x_min": 0, "plot_x_max": 0
        }            

    def updateScattergraphLines(self):

        self.cScatterLines = []

        dates = self._plot_flow_monitor.dateRange
        depth = self._plot_flow_monitor.depthDataRange

        if self.plotVelocityScattergraph:
            plotYalues = self._plot_flow_monitor.velocityDataRange
        else:
            plotYalues = self._plot_flow_monitor.flowDataRange

        tobedeleted = []

        if self.ignoreDataAboveSoffit and self._plot_flow_monitor.hasModelData:
            for i in reversed(range(len(depth))):
                if depth[i] > self._plot_flow_monitor.modelDataPipeDia:
                    tobedeleted.append(i)

        if self.ignoreZeros:
            for i in range(len(plotYalues)):
                if float(plotYalues[i]) == 0.0:
                    tobedeleted.append(i)

        if len(tobedeleted) > 0:
            dates = np.delete(dates, tobedeleted)
            depth = np.delete(depth, tobedeleted)
            plotYalues = np.delete(plotYalues, tobedeleted)

        self.plot_axis_scatter = self.main_window_plot_widget.figure.subplots(1)
        if self.plotFPData:
            cLine = self.plot_axis_scatter.scatter(
                plotYalues, depth, s=5, label="Full Period", color="gray"
            )
            self.cScatterLines.append(cLine)

        if len(self.plotted_events.plotEvents) > 0:
            for se in self.plotted_events.plotEvents.values():

                tobedeleted = []

                for i in reversed(range(len(dates))):
                    # if dt.strptime(dates[i], "%d/%m/%Y %H:%M") < se.eventStart or dt.strptime(dates[i], "%d/%m/%Y %H:%M") > se.eventEnd:
                    if dates[i] < se.eventStart or dates[i] > se.eventEnd:
                        tobedeleted.append(i)

                if len(tobedeleted) > 0:
                    eventPlotValues = np.delete(plotYalues, tobedeleted)
                    eventDepthValues = np.delete(depth, tobedeleted)

                cLine = self.plot_axis_scatter.scatter(
                    eventPlotValues,
                    eventDepthValues,
                    s=5,
                    label=se.eventName,
                    color=next(self.config.plot_colors),
                )
                self.cScatterLines.append(cLine)

        self.axis_limits["x_min"], self.axis_limits["x_max"] = self.plot_axis_scatter.get_xlim()
        self.axis_limits["y_min"], self.axis_limits["y_max"] = self.plot_axis_scatter.get_ylim()

    def _update_cbw_line(self):
        """Update the Colebrook-White line"""
        if not (self.plotModelData and self.plotCBWLine):
            return

        if self.plot_axis_cbw is not None:
            self.plot_axis_cbw.remove()
            self.plot_axis_cbw = None

        if self._compute_cbw_values() and self._plot_flow_monitor.modelDataPipeShape == "CIRC":

            self.useOriginal = not self.useOriginal

            if self.plotModelData and self.plotCBWLine:
                self.plot_axis_cbw = self.plot_axis_scatter.twinx()
            # Select data to plot
            plotXValues = self.CBW_velocity if self.plotVelocityScattergraph else self.CBW_flow

            # Plot CBW data
            self.plot_axis_cbw.plot(
                plotXValues,
                self.CBW_depth,
                linewidth=0.75,
                linestyle="dotted",
                color="black",
                label="CBW",
            )

            # Calculate x-axis range with buffer
            self.axis_limits['x_min'], self.axis_limits['x_max'] = self.update_axis_limits(self.axis_limits['x_min'], self.axis_limits['x_max'], min(plotXValues), max(plotXValues), self.xBufferFactor)

            # Calculate y-axis range with buffer
            self.axis_limits['y_min'], self.axis_limits['y_max'] = self.update_axis_limits(self.axis_limits['y_min'], self.axis_limits['y_max'], min(self.CBW_depth), max(self.CBW_depth), self.yBufferFactor)

            self.update_plot_axis_limits()

            # Set axis limits for scatter and CBW plots
            self.plot_axis_scatter.set_xlim(self.axis_limits['plot_x_min'], self.axis_limits['plot_x_max'])
            self.plot_axis_scatter.set_ylim(self.axis_limits['y_min'], self.axis_limits['y_max'])
            self.plot_axis_cbw.set_xlim(self.axis_limits['plot_x_min'], self.axis_limits['plot_x_max'])
            self.plot_axis_cbw.set_ylim(self.axis_limits['y_min'], self.axis_limits['y_max'])

    def update_plot_axis_limits(self):
        # Determine aspect ratio and scaling
        xsize, ysize = self.main_window_plot_widget.figure.get_size_inches()
        aspectRatio = ysize / xsize

        xAxisRange = self.axis_limits['x_max'] - self.axis_limits['x_min']
        yAxisRange = self.axis_limits['y_max'] - self.axis_limits['y_min']
        self.axisRatio = (yAxisRange / xAxisRange) / aspectRatio

        # Adjust plot X-axis limits considering pipe exaggeration and buffer
        pipeRadius = self._plot_flow_monitor.modelDataPipeDia / 2
        xOffset = (pipeRadius / self.axisRatio) * self.xBufferFactor
        self.axis_limits['plot_x_min'] = self.axis_limits['x_min'] - xOffset
        self.axis_limits['plot_x_max'] = self.axis_limits['x_max'] + xOffset * self.pipeExag

    def update_axis_limits(self, current_axis_min, current_axis_max, min_value, max_value, buffer_factor):
        """Helper function to calculate axis range with a buffer."""

        range_diff = max_value - min_value
        buffer = ((range_diff * buffer_factor) - range_diff) / 2
        # xAxisMin = min(current_axis_min, min_value - buffer)
        # xAxisMax = max(current_axis_max, max_value + buffer)
        return min(current_axis_min, min_value - buffer), max(current_axis_max, max_value + buffer)

    def _calculate_gradient(self) -> float:
        """Calculate pipe gradient from model data"""
        if (self._plot_flow_monitor.modelDataPipeUSInvert > 0 and 
            self._plot_flow_monitor.modelDataPipeDSInvert > 0):
            gradient = ((self._plot_flow_monitor.modelDataPipeUSInvert - 
                        self._plot_flow_monitor.modelDataPipeDSInvert) / 
                       self._plot_flow_monitor.modelDataPipeLength)
            return max(gradient, 0.00001)
        return 0.00001

    def _compute_cbw_values(self) -> bool:
        self.CBW_depth = []
        self.CBW_flow = []
        self.CBW_velocity = []

        if (
            self._plot_flow_monitor.modelDataPipeLength <= 0
            or self._plot_flow_monitor.modelDataPipeDia <= 0
            or self._plot_flow_monitor.modelDataPipeRoughness <= 0
            or self._plot_flow_monitor.modelDataPipeShape == ""
            or self._plot_flow_monitor.modelDataPipeHeight <= 0
        ):
            return False

        # gradient = ((self._plot_flow_monitor.modelDataPipeUSInvert - self._plot_flow_monitor.modelDataPipeDSInvert) / self._plot_flow_monitor.modelDataPipeLength if self._plot_flow_monitor.modelDataPipeUSInvert > 0 and self._plot_flow_monitor.modelDataPipeDSInvert > 0 else 0)
        # gradient = max(gradient, 0.00001)
        gradient = self._calculate_gradient()

        # Constants
        pipe_diameter_m = self._plot_flow_monitor.modelDataPipeDia / 1000  # Convert mm to meters
        roughness_m = self._plot_flow_monitor.modelDataPipeRoughness / 1000  # Convert mm to meters
        g = 9.807  # Gravitational acceleration (m/s²)

        # Initialize outputs
        self.CBW_depth = [0]  # Start with zero depth
        self.CBW_flow = [0]   # Start with zero flow
        self.CBW_velocity = [0]  # Start with zero velocity

        # Loop through depth proportions
        for depth_ratio in self.config.depth_proportions:
            # 1. Calculate flow area (A) and wetted perimeter (P)
            depth = pipe_diameter_m * depth_ratio
            theta = 2 * math.acos(1 - 2 * depth_ratio)  # Angle subtended by the flow
            flow_area = (theta - math.sin(theta)) / 8 * math.pi * pipe_diameter_m**2
            wetted_perimeter = pipe_diameter_m * theta / (2 * math.pi)

            # 2. Calculate hydraulic radius (R)
            hydraulic_radius = flow_area / wetted_perimeter

            # 3. Calculate friction factor using the Swamee-Jain approximation
            reynolds_number = (4 * flow_area * math.sqrt(gradient * hydraulic_radius * g)) / (1.002e-3)  # Kinematic viscosity of water
            if reynolds_number > 4000:  # Turbulent flow
                friction_factor = 0.25 / (math.log10((roughness_m / (3.7 * pipe_diameter_m)) + (5.74 / reynolds_number**0.9)))**2
            else:  # Laminar flow (fallback)
                friction_factor = 64 / reynolds_number if reynolds_number > 0 else 0

            # 4. Calculate velocity and flow
            velocity = math.sqrt(gradient * hydraulic_radius * g / friction_factor)
            flow = flow_area * velocity

            # Append results
            self.CBW_depth.append(depth * 1000)  # Convert to mm
            self.CBW_flow.append(flow * 1000)  # Convert to L/s
            self.CBW_velocity.append(velocity)

        return True

    def updatePipeProfileLines(self):

        if self.plot_axis_pipe_profile is not None:
            self.plot_axis_pipe_profile.remove()
            self.plot_axis_pipe_profile = None

        if self.plotModelData and self.showPipeProfile and (self.plotFPData or self.plotCBWLine):

            self.update_plot_axis_limits()

            self.plot_axis_pipe_profile = self.plot_axis_scatter.twinx()
            # self.plot_axis_scatter
            self.plot_axis_pipe_profile.set_ylim(self.axis_limits['y_min'], self.axis_limits['y_max'])
            self.plot_axis_pipe_profile.axes.yaxis.set_visible(False)

            pipeInStation = self.axis_limits['x_min']
            self.pipeOutStation = self.axis_limits['x_max']

            # self.pipeProfileDepthProp = [
            #     0,
            #     1 / 24,
            #     2 / 24,
            #     3 / 24,
            #     4 / 24,
            #     5 / 24,
            #     6 / 24,
            #     7 / 24,
            #     8 / 24,
            #     9 / 24,
            #     10 / 24,
            #     11 / 24,
            #     12 / 24,
            #     13 / 24,
            #     14 / 24,
            #     15 / 24,
            #     16 / 24,
            #     17 / 24,
            #     18 / 24,
            #     19 / 24,
            #     20 / 24,
            #     21 / 24,
            #     22 / 24,
            #     23 / 24,
            #     24 / 24,
            # ]
            pipeProfileX = []
            pipeProfileY = []

            for i in range(0, len(self.config.pipe_profile_depth_prop)):

                pipeProfileX.append(((math.sin(math.radians((self.config.pipe_profile_depth_prop[i] * 360) + 180)) * ((self._plot_flow_monitor.modelDataPipeDia / 2) / self.axisRatio)) * self.pipeExag) + self.pipeOutStation)
                pipeProfileY.append(self.config.pipe_profile_depth_prop[i] * self._plot_flow_monitor.modelDataPipeDia)

            for i in range(len(self.config.pipe_profile_depth_prop) - 1, -1, -1):

                pipeProfileX.append(((math.sin(math.radians((self.config.pipe_profile_depth_prop[i] * 360) + 180)) * ((self._plot_flow_monitor.modelDataPipeDia / 2) / self.axisRatio)) * self.pipeExag) + pipeInStation)
                pipeProfileY.append(self.config.pipe_profile_depth_prop[i] * self._plot_flow_monitor.modelDataPipeDia)

            pipeProfileX.append(self.pipeOutStation)
            pipeProfileY.append(0)

            self.plot_axis_pipe_profile.plot(
                pipeProfileX,
                pipeProfileY,
                linewidth=1.5,
                color="black",
                label="Pipe Profile",
            )

            pipeProfileX = []
            pipeProfileY = []

            for i in range(0, int(len(self.config.pipe_profile_depth_prop) / 2) + 1):

                pipeProfileX.append(((math.sin(math.radians(self.config.pipe_profile_depth_prop[i] * 360)) * ((self._plot_flow_monitor.modelDataPipeDia / 2) / self.axisRatio)) * self.pipeExag) + self.pipeOutStation)
                pipeProfileY.append(self.config.pipe_profile_depth_prop[i] * self._plot_flow_monitor.modelDataPipeDia)

            self.plot_axis_pipe_profile.plot(
                pipeProfileX,
                pipeProfileY,
                linewidth=1.5,
                color="black",
                label="Pipe Profile",
            )

            pipeProfileX = []
            pipeProfileY = []

            for i in range(len(self.config.pipe_profile_depth_prop) - 1, int(len(self.config.pipe_profile_depth_prop) / 2) - 1, -1):

                pipeProfileX.append(((math.sin(math.radians(self.config.pipe_profile_depth_prop[i] * 360)) * ((self._plot_flow_monitor.modelDataPipeDia / 2) / self.axisRatio)) * self.pipeExag) + pipeInStation)
                pipeProfileY.append(self.config.pipe_profile_depth_prop[i] * self._plot_flow_monitor.modelDataPipeDia)

            self.plot_axis_pipe_profile.plot(
                pipeProfileX,
                pipeProfileY,
                linewidth=1.5,
                color="black",
                label="Pipe Profile",
            )

            pipeProfileX = []
            pipeProfileY = []

            for i in range(0, len(self.config.pipe_profile_depth_prop)):

                pipeProfileX.append((((self._plot_flow_monitor.modelDataPipeDia / 2) / self.axisRatio) * math.sin(math.radians((self.config.pipe_profile_depth_prop[i] * 180) + 180))) + pipeInStation)
                pipeProfileY.append((self._plot_flow_monitor.modelDataPipeDia / 2) + ((self._plot_flow_monitor.modelDataPipeDia / 2) * (math.cos(math.radians((self.config.pipe_profile_depth_prop[i] * 180) + 180)))))

            self.plot_axis_pipe_profile.plot(
                pipeProfileX,
                pipeProfileY,
                linewidth=1.5,
                color="black",
                label="Pipe Profile",
            )

    def updateIsoLines(self):

        if self.plot_axis_isoq is not None:
            self.plot_axis_isoq.remove()
            self.plot_axis_isoq = None

        if self.plotModelData and self.plotIsoQLines:
            self.plot_axis_isoq = self.plot_axis_scatter.twinx()
            rangeValues = self.isoQUBound - self.isoQLBound
            stepValue = rangeValues / (self.noOfIsoQLines - 1)

            for i in range(self.noOfIsoQLines):

                aValue = self.isoQLBound + (i * stepValue)
                Iso_val = []
                Iso_dep = []

                if self.plotVelocityScattergraph:
                    for j in range(len(self.config.depth_proportions)):  # J

                        if self._plot_flow_monitor.modelDataPipeDia != 0:
                            myVel = (aValue / 1000) / self.flowAreaByDepth(self._plot_flow_monitor.modelDataPipeDia, ((self._plot_flow_monitor.modelDataPipeDia) * self.config.depth_proportions[j]))
                            if myVel <= self.pipeOutStation:
                                Iso_dep.append(((self._plot_flow_monitor.modelDataPipeDia) * self.config.depth_proportions[j]))
                                Iso_val.append((aValue / 1000) / self.flowAreaByDepth(self._plot_flow_monitor.modelDataPipeDia, ((self._plot_flow_monitor.modelDataPipeDia) * self.config.depth_proportions[j])))
                else:
                    for j in range(len(self.config.depth_proportions)):  # J
                        if self._plot_flow_monitor.modelDataPipeDia != 0:
                            myFlow = (aValue * self.flowAreaByDepth(self._plot_flow_monitor.modelDataPipeDia, ((self._plot_flow_monitor.modelDataPipeDia) * self.config.depth_proportions[j]))) * 1000
                            if myFlow <= self.pipeOutStation:
                                Iso_dep.append(((self._plot_flow_monitor.modelDataPipeDia) * self.config.depth_proportions[j]))
                                Iso_val.append((aValue * self.flowAreaByDepth(self._plot_flow_monitor.modelDataPipeDia, ((self._plot_flow_monitor.modelDataPipeDia) * self.config.depth_proportions[j]))) * 1000)

                if self.plotVelocityScattergraph:
                    Iso_val.insert(0, self.axis_limits['x_max'])
                    Iso_dep.insert(0, self.flowDepthByArea(int(self._plot_flow_monitor.modelDataPipeDia), (aValue / 1000) / self.axis_limits['x_max']))

                if self.plotVelocityScattergraph:
                    self.plot_axis_isoq.plot(
                        Iso_val,
                        Iso_dep,
                        linewidth=1,
                        linestyle="dashdot",
                        color="forestgreen",
                        label="{0:.3g}".format(aValue) + "l/s",
                    )
                else:
                    self.plot_axis_isoq.plot(
                        Iso_val,
                        Iso_dep,
                        linewidth=1,
                        linestyle="dashdot",
                        color="forestgreen",
                        label="{0:.3g}".format(aValue) + "m/s",
                    )
                self.plot_axis_isoq.set_ylim(self.axis_limits['y_min'], self.axis_limits['y_max'])
                self.plot_axis_isoq.axes.yaxis.set_visible(False)

                # Total pockle to label the Iso Lines
                if len(Iso_val) > 0:
                    flow_props = dict(boxstyle="round", facecolor="white", alpha=0.5)
                    txtX = (max(Iso_val) - min(Iso_val)) * (0.1 + (i * ((0.25 - 0.025) / (self.noOfIsoQLines - 1))))
                    myIndex = Iso_val.index(min(Iso_val, key=lambda x: abs(x - txtX)))
                    if not Iso_val[myIndex] is None and not Iso_dep[myIndex] is None:
                        self.plot_axis_isoq.text(
                            Iso_val[myIndex],
                            Iso_dep[myIndex],
                            self.plot_axis_isoq.axes.lines[i].get_label(),
                            bbox=flow_props,
                        )

    def flowAreaByDepth(self, pipeDiaInMM: int, flowDepthInMM: int):

        r = (pipeDiaInMM / 1000) / 2
        h = flowDepthInMM / 1000
        theta = 2 * math.acos((r - h) / r)
        area = (r**2 * (theta - math.sin(theta))) / 2

        return area

    def flowDepthByArea(self, pipeDiaInMM: int, flowAreaInM2: float):

        # r = (pipeDiaInMM / 1000) / 2
        for h in range(pipeDiaInMM):

            check = flowAreaInM2 - self.flowAreaByDepth(pipeDiaInMM, h)
            if check <= 0:
                return h

    def updateCanvas(self):

        self.main_window_plot_widget.event_connections.append(self.main_window_plot_widget.figure.canvas.mpl_connect("pick_event", self.onPick))
        self.main_window_plot_widget.showToolbar(not self.isBlank)
        self.main_window_plot_widget.toolbar.lockNavigation(False)

    def onPick(self, event):

        legline = event.artist
        origline = self.cScatterLegendLines[legline]
        vis = not origline.get_visible()

        origline.set_visible(vis)
        # Change the alpha on the line in the legend so we can see what lines have been toggled
        if vis:
            legline.set_alpha(1.0)
        else:
            legline.set_alpha(0.2)

        self.main_window_plot_widget.figure.canvas.draw()


class graphDWF:

    def __init__(self, mw_pw: PlotWidget = None):

        self.main_window_plot_widget: PlotWidget = mw_pw
        self._initialize_attributes()
        getBlankFigure(self.main_window_plot_widget)

        self.CBW_depth: list[float] = []
        self.CBW_flow: list[float] = []
        self.CBW_velocity: list[float] = []

    def _initialize_attributes(self):
        """Initialize all class attributes with default values"""
        self.is_blank = True
        # self.plot_velocity_scattergraph = True
        self.plotted_events = plottedSurveyEvents()
        self._plot_flow_monitor: flowMonitor = None

        # Plot axes
        self.plot_axis_flow: axes.Axes = None
        self.plot_axis_depth: axes.Axes = None
        self.plot_axis_velocity: axes.Axes = None

        # Data storage
        self.df_filtered: pd.DataFrame
        self.df_dwf_filtered: pd.DataFrame
        # self.cbw_data = {"depth": [], "flow": [], "velocity": []}

    @property
    def plot_flow_monitor(self) -> flowMonitor:
        return self._plot_flow_monitor

    @plot_flow_monitor.setter
    def plot_flow_monitor(self, fm: flowMonitor):
        self._plot_flow_monitor = fm
        # if fm and self.plotModelData:
        #     self.plotModelData = fm.hasModelData    

    def update_plot(self):

        self.clearFigure()
        if self._plot_flow_monitor is not None:
            self.update_dwf_plot()
            self.main_window_plot_widget.figure.subplots_adjust(left=0.05, right=0.85, bottom=0.1, top=0.95)
            self.isBlank = False
        else:
            getBlankFigure(self.main_window_plot_widget)
            self.isBlank = True

        self.updateCanvas()

    def update_dwf_plot(self):
        filename = self._plot_flow_monitor.monitorName
        if self._plot_flow_monitor.hasModelData:
            i_soffit_mm = self._plot_flow_monitor.modelDataPipeHeight
        else:
            i_soffit_mm = 0

        self.filter_dwf_data()

        if self.df_dwf_filtered.empty:
            # Create a figure with a single subplot
            ax = self.main_window_plot_widget.figure.subplots()
            ax.text(0.5, 0.5, 'No dry days identified', horizontalalignment='center', verticalalignment='center', fontsize=16)
            ax.set_axis_off()  # Hide the axes
            # self.main_window_plot_widget.figure = fig
            return

        # Create a figure and subplots
        (self.plot_axis_flow, self.plot_axis_depth, self.plot_axis_velocity) = self.main_window_plot_widget.figure.subplots(
            nrows=3, sharex=True, gridspec_kw={'height_ratios': [1, 1, 1]}
        )

        # Group the data by day
        grouped = self.df_dwf_filtered.groupby(self.df_dwf_filtered['Date'].dt.date)

        for day, group in grouped:
            # Plot Flow vs Time of Day
            self.plot_axis_flow.plot(group['TimeOfDay'], group['FlowData'], color='lightblue')

            # Plot Depth vs Time of Day
            self.plot_axis_depth.plot(group['TimeOfDay'], group['DepthData'], color='lightsalmon')

            # Plot Velocity vs Time of Day
            self.plot_axis_velocity.plot(group['TimeOfDay'], group['VelocityData'], color='palegreen')

        if i_soffit_mm > 0:
            self.plot_axis_depth.plot(self.df_dwf_average['TimeOfDay'], [i_soffit_mm] *
                                    len(self.df_dwf_average), color='darkblue', linestyle='--', label='Soffit')

        self.plot_axis_flow.plot(self.df_dwf_average['TimeOfDay'], self.df_dwf_average['AvgFlowData'], color='blue')
        self.plot_axis_depth.plot(self.df_dwf_average['TimeOfDay'], self.df_dwf_average['AvgDepthData'], color='red')
        self.plot_axis_velocity.plot(self.df_dwf_average['TimeOfDay'], self.df_dwf_average['AvgVelocityData'], color='green')

        # Add labels and titles
        self.plot_axis_flow.set_ylabel('Flow (l/sec)')
        self.plot_axis_flow.set_title(f'Flow: {filename}', loc='left', fontsize=16)

        self.plot_axis_depth.set_ylabel('Depth (mm)')
        self.plot_axis_depth.set_title('Depth', loc='left', fontsize=16)
        if i_soffit_mm > 0:
            self.plot_axis_depth.text(self.df_dwf_average['TimeOfDay'].iloc[0], i_soffit_mm - 10, f"Soffit Height = {i_soffit_mm}mm", color='darkblue', verticalalignment='top', horizontalalignment='left')

        self.plot_axis_velocity.set_ylabel('Velocity (m/sec)')
        self.plot_axis_velocity.set_title('Velocity', loc='left', fontsize=16)
        self.plot_axis_velocity.set_xlabel('Time of Day')

        # Add statistics text (optional)
        flow_min = self.df_dwf_average['AvgFlowData'].min()
        flow_max = self.df_dwf_average['AvgFlowData'].max()
        flow_range = flow_max - flow_min
        flow_avg = self.df_dwf_average['AvgFlowData'].mean()
        total_flow_volume_m3 = (flow_avg * (24 * 60 * 60)) / 1000
        self.plot_axis_flow.text(1.02, 0.5, f"Min: {flow_min:.2f}\nMax: {flow_max:.2f}\nRange: {flow_range:.2f}\nAverage: {flow_avg:.2f}\nTotal Volume: {total_flow_volume_m3:.1f} m³",
                                transform=self.plot_axis_flow.transAxes, verticalalignment='center')

        depth_min = self.df_dwf_average['AvgDepthData'].min()
        depth_max = self.df_dwf_average['AvgDepthData'].max()
        depth_range = depth_max - depth_min
        depth_avg = self.df_dwf_average['AvgDepthData'].mean()
        self.plot_axis_depth.text(1.02, 0.5, f"Min: {depth_min:.2f}\nMax: {depth_max:.2f}\nRange: {depth_range:.2f}\nAverage: {depth_avg:.2f}",
                                transform=self.plot_axis_depth.transAxes, verticalalignment='center')

        velocity_min = self.df_dwf_average['AvgVelocityData'].min()
        velocity_max = self.df_dwf_average['AvgVelocityData'].max()
        velocity_range = velocity_max - velocity_min
        velocity_avg = self.df_dwf_average['AvgVelocityData'].mean()
        self.plot_axis_velocity.text(1.02, 0.5, f"Min: {velocity_min:.2f}\nMax: {velocity_max:.2f}\nRange: {velocity_range:.2f}\nAverage: {velocity_avg:.2f}",
                                    transform=self.plot_axis_velocity.transAxes, verticalalignment='center')

        # Set x-axis major locator to hour
        self.plot_axis_velocity.xaxis.set_major_locator(ticker.MultipleLocator(3600))
        # Custom formatter for the x-axis to display HH:MM
        def format_func(value, tick_number):
            hours = int(value // 3600)
            minutes = int((value % 3600) // 60)
            return f'{hours:02d}:{minutes:02d}'
        self.plot_axis_velocity.xaxis.set_major_formatter(ticker.FuncFormatter(format_func))

        self.plot_axis_velocity.set_xticklabels(self.plot_axis_velocity.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')

        # Adjust layout
        self.main_window_plot_widget.figure.tight_layout()

        # Show plot
        self.main_window_plot_widget.canvas.show()

    def filter_dwf_data(self):

        # Create the DataFrame
        self.df_filtered = pd.DataFrame(
            {
                "Date": self._plot_flow_monitor.dateRange,
                "FlowData": self._plot_flow_monitor.flowDataRange,
                "DepthData": self._plot_flow_monitor.depthDataRange,
                "VelocityData": self._plot_flow_monitor.velocityDataRange,
            }
        )

        dry_days_df = pd.DataFrame({"Date": []})

        # Create a new dataframe with only the dry day event dates
        for se in self.plotted_events.plotEvents.values():
            # Append the date part to the DataFrame
            dry_days_df = pd.concat([dry_days_df, pd.DataFrame({"Date": [se.eventStart.date()]})], ignore_index=True)

        # flow_monitor_data = self.current_inst.data.copy()  # Make a copy of the data
        flow_monitor_data = self.df_filtered.copy()  # Make a copy of the data

        # Filter flow monitor data to include only dry days
        flow_monitor_data['Date'] = pd.to_datetime(flow_monitor_data['Date'])
        flow_monitor_data['Day'] = flow_monitor_data['Date'].dt.date
        flow_monitor_data = flow_monitor_data[flow_monitor_data['Day'].isin(dry_days_df['Date'])]

        # Remove date information and keep only time part
        flow_monitor_data['TimeOfDay'] = flow_monitor_data['Date'].dt.time

        # Group by time and calculate the average flow, velocity, and depth for each time point
        avg_dwf_per_time = flow_monitor_data.groupby('TimeOfDay').agg({
            'FlowData': 'mean',
            'DepthData': 'mean',
            'VelocityData': 'mean'
            }).reset_index()

        # Rename the columns for clarity
        avg_dwf_per_time.columns = ['TimeOfDay', 'AvgFlowData', 'AvgDepthData', 'AvgVelocityData']

        # Optional: sort by time if needed
        avg_dwf_per_time = avg_dwf_per_time.sort_values(by='TimeOfDay').reset_index(drop=True)

        self.df_dwf_filtered = pd.merge(flow_monitor_data, avg_dwf_per_time, on='TimeOfDay', how='right')

        self.df_dwf_filtered['TimeOfDay'] = self.df_dwf_filtered['Date'].dt.hour * 3600 + \
            self.df_dwf_filtered['Date'].dt.minute * 60 + self.df_dwf_filtered['Date'].dt.second

        self.df_dwf_average = self.df_dwf_filtered.drop_duplicates(
            subset=['TimeOfDay', 'AvgFlowData', 'AvgDepthData', 'AvgVelocityData'])


    def clearFigure(self):
        self.main_window_plot_widget.figure.clear()

        if self.plot_axis_flow is not None:
            self.plot_axis_flow.clear()
            self.plot_axis_flow = None
        if self.plot_axis_depth is not None:
            self.plot_axis_depth.clear()
            self.plot_axis_depth = None
        if self.plot_axis_velocity is not None:
            self.plot_axis_velocity.clear()
            self.plot_axis_velocity = None

    def updateCanvas(self):

        # self.main_window_plot_widget.event_connections.append(self.main_window_plot_widget.figure.canvas.mpl_connect("pick_event", self.onPick))
        self.main_window_plot_widget.showToolbar(not self.isBlank)
        self.main_window_plot_widget.toolbar.lockNavigation(False)

    # def onPick(self, event):

    #     legline = event.artist
    #     origline = self.cScatterLegendLines[legline]
    #     vis = not origline.get_visible()

    #     origline.set_visible(vis)
    #     # Change the alpha on the line in the legend so we can see what lines have been toggled
    #     if vis:
    #         legline.set_alpha(1.0)
    #     else:
    #         legline.set_alpha(0.2)

    #     self.main_window_plot_widget.figure.canvas.draw()


class graphRainfallAnalysis:

    rainfallDepthTolerance: int = int(0)  # mm
    precedingDryDays: int = int(4)  # days
    consecZero: int = int(5)  # timesteps
    requiredDepth: int = int(5)  # mm
    requiredIntensity: float = float(6)  # mm/hr
    requiredIntensityDuration: int = int(4)  # mins
    partialPercent: int = int(20)  # %
    useConsecutiveIntensities: bool = True
    useDefaultParams: bool = True

    def __init__(self, mw_pw: PlotWidget = None):

        self.plotAxisHistogram: axes.Axes = None
        self.plotAxisGant: axes.Axes = None
        self.plotAxisIntensity: axes.Axes = None
        self.plot_depth_stats_box: plt.Text = None
        # self.startDate: datetime = datetime.strptime('2172-05-12', '%Y-%m-%d')
        self.startDate: datetime = datetime.strptime("1972-05-12", "%Y-%m-%d")

        self.rIntLegendLines: Dict[lines.Line2D, lines.Line2D] = None
        self.rIntLines: list[lines.Line2D] = None
        self.lstStormDatesForHistogram: list = []
        self.lstStormCountForHistogram: list = []
        self.lstDWFDatesForHistogram: list = []
        self.lstDWFCountForHistogram: list = []
        self.dfRainBlock: pd.DataFrame = None
        self.dictRainfallSubsets: dict[pd.DataFrame] = {}
        self.hasStormEvents: bool = False
        self.hasDWFEvents: bool = False

        self.main_window_plot_widget: PlotWidget = mw_pw
        getBlankFigure(self.main_window_plot_widget)
        self.isBlank: bool = True

        self.rainfallDepthTolerance: int = int(0)  # mm
        self.precedingDryDays: int = int(4)  # days
        self.consecZero: int = int(5)  # timesteps
        self.requiredDepth: int = int(5)  # mm
        self.requiredIntensity: float = float(6)  # mm/hr
        self.requiredIntensityDuration: int = int(4)  # mins
        self.partialPercent: int = int(20)  # %
        self.useConsecutiveIntensities: bool = True
        self.useDefaultParams: bool = True
        self.useNewMethod: bool = True        

        self.plotted_rgs: plottedRainGauges = plottedRainGauges()
        self.analysisNeedsRefreshed: bool = True
        self.update_plot()

    def update_plot(self):

        self.main_window_plot_widget.figure.clear()
        if len(self.plotted_rgs.plotRGs) > 0:
            if self.analysisNeedsRefreshed:
                self.updateRainfallAnalysis()
            self.refreshPlots()
            self.isBlank = False
        else:
            getBlankFigure(self.main_window_plot_widget)
            self.isBlank = True
        self.updateCanvas()

    def updateCanvas(self):
        self.main_window_plot_widget.event_connections.append(self.main_window_plot_widget.figure.canvas.mpl_connect("pick_event", self.onPick))
        self.main_window_plot_widget.event_connections.append(self.main_window_plot_widget.figure.canvas.mpl_connect("button_press_event", self.onClick))
        self.main_window_plot_widget.showToolbar(not self.isBlank)
        self.main_window_plot_widget.toolbar.lockNavigation(False)

    def getSubsetOfRainfallFromRaingauge(self, rg: rainGauge):

        dates = rg.dateRange.copy()
        intencities = rg.rainfallDataRange.copy()
        tobedeleted = []

        for i in reversed(range(len(rg.dateRange))):
            if rg.dateRange[i] < self.startDate:
                tobedeleted.append(i)

        if len(tobedeleted) > 0:
            dates = np.delete(dates, tobedeleted)
            intencities = np.delete(intencities, tobedeleted)

        dfRainfallSubset = pd.DataFrame(columns=["rain_date", "rainfall"])
        dfRainfallSubset["rain_datetime"] = dates
        dfRainfallSubset["rain_date"] = dates
        dfRainfallSubset["rainfall"] = intencities
        dfRainfallSubset["rainfall_mm"] = [
            intVals * (rg.rgTimestep / 60) for intVals in intencities
        ]

        dfRainfallSubset["rain_date"] = pd.to_datetime(
            dfRainfallSubset["rain_datetime"]
        ).dt.date
        return dfRainfallSubset

    def getListOfDryDays(self, dfPerDiemRainfallData: pd.DataFrame):

        lstDryDays = []
        dry_day_count = 0

        for r in range(len(dfPerDiemRainfallData)):

            if dfPerDiemRainfallData.iloc[r, 1] <= self.rainfallDepthTolerance:

                dry_day_count += 1

                if dry_day_count > self.precedingDryDays:

                    dry_day = dfPerDiemRainfallData.iloc[r, 0]

                    lstDryDays.append(dry_day)
            else:

                dry_day_count = 0

        return lstDryDays

    def getPotentialWAPUGEventsNM(
        self, df_rainfall_subset: pd.DataFrame, time_step: int, gauge_name: str
    ) -> Tuple[List[pd.Timestamp], pd.DataFrame]:
        """
        Detect potential WAPUG events in rainfall data.

        Args:
            df_rainfall_subset (pd.DataFrame): DataFrame with rainfall data
            time_step (int): Time step in minutes
            gauge_name (str): Name of the rainfall gauge

        Returns:
            Tuple containing:
            - List of historical dates for identified events
            - DataFrame with event details
        """
        # Extract rainfall and datetime series
        rainfall = df_rainfall_subset["rainfall"].values
        dates = df_rainfall_subset["rain_datetime"].values

        # Initialize tracking variables
        hist_dates = []
        rain_block_df = pd.DataFrame(
            columns=["RG", "Start", "End", "Depth", "Intensity_Count", "Passed"]
        )

        # State tracking
        state = {
            "running_depth": 0,
            "consecutive_zeros": 0,
            "intensity_count": 0,
            "partial_intensity_count": 0,
            "cumulative_sum": [],
            "potential_event_start_index": 0,
        }

        def _reset_state():
            """Reset the state tracking variables."""
            state["running_depth"] = 0
            state["consecutive_zeros"] = 0
            state["intensity_count"] = 0
            state["partial_intensity_count"] = 0
            state["cumulative_sum"].clear()

        def _check_event_criteria(running_depth, intensity_count) -> float:
            """
            Determine if an event meets the criteria.

            Returns:
            - 1 for full event
            - 0.5 for partial event
            - 0 for non-event
            """
            # Full event condition
            if (
                running_depth > self.requiredDepth
                and intensity_count >= self.requiredIntensityDuration
            ):
                return 1.0

            # Partial event conditions
            partial_depth_condition = (
                running_depth
                >= (((100 - self.partialPercent) / 100) * self.requiredDepth)
                and running_depth < self.requiredDepth
            )
            partial_intensity_condition = (
                intensity_count
                >= (
                    ((100 - self.partialPercent) / 100) * self.requiredIntensityDuration
                )
                and intensity_count < self.requiredIntensityDuration
            )

            # Check various partial event scenarios
            if (
                (partial_depth_condition and partial_intensity_condition)
                or (
                    partial_depth_condition
                    and intensity_count >= self.requiredIntensityDuration
                )
                or (partial_intensity_condition and running_depth > self.requiredDepth)
                or (
                    state["partial_intensity_count"] >= self.requiredIntensityDuration
                    and self.useConsecutiveIntensities
                    and running_depth > self.requiredDepth
                )
            ):
                return 0.5

            return 0.0

        for i, rainfall_val in enumerate(rainfall):
            # Handle zero rainfall
            if rainfall_val == 0:
                state["consecutive_zeros"] += 1
            else:
                state["consecutive_zeros"] = 0
                state["running_depth"] += rainfall_val / (60 / time_step)
                state["cumulative_sum"].append(float(state["running_depth"]))

                # Handle intensity tracking
                if self.useConsecutiveIntensities:  # Consecutive intensities
                    if rainfall_val > self.requiredIntensity:
                        items = rainfall[
                            i : int(i + (self.requiredIntensityDuration / time_step))
                        ]
                        state["partial_intensity_count"] += time_step

                        if all(item > self.requiredIntensity for item in items):
                            state["intensity_count"] = self.requiredIntensityDuration
                else:  # Non-consecutive intensities
                    if rainfall_val > self.requiredIntensity:
                        state["intensity_count"] += time_step

            # Check for event when consecutive zeros threshold is reached
            if state["consecutive_zeros"] >= self.consecZero:
                # Only process if there's a cumulative sum
                if state["cumulative_sum"]:
                    last_depth = state["cumulative_sum"][-1]
                    event_status = _check_event_criteria(
                        state["running_depth"], state["intensity_count"]
                    )

                    if event_status >= 0:
                        # Full or partial event processing
                        event_start_index = state["potential_event_start_index"]
                        event_end_index = i
                        event_start = dates[event_start_index]
                        event_end = dates[event_end_index]

                        # Create date range for the event
                        event_dates = pd.date_range(
                            start=event_start, end=event_end, freq="2min"
                        ).tolist()
                        if event_status == 1:
                            hist_dates.extend(event_dates)

                        # Record event details
                        event_record = pd.DataFrame(
                            [
                                {
                                    "RG": gauge_name,
                                    "Start": event_start,
                                    "End": event_end,
                                    "Depth": last_depth,
                                    "Intensity_Count": state["intensity_count"],
                                    "Passed": event_status,
                                }
                            ]
                        )
                        # Drop empty or all-NA columns from both DataFrames
                        rain_block_df_cleaned = rain_block_df.dropna(axis=1, how='all')
                        event_record_cleaned = event_record.dropna(axis=1, how='all')

                        rain_block_df = pd.concat([rain_block_df_cleaned, event_record_cleaned], ignore_index=True)

                        # rain_block_df = pd.concat(
                        #     [rain_block_df, event_record], ignore_index=True
                        # )

                    # if event_status > 0:
                    #     # Full or partial event processing
                    #     event_start_index = state["potential_event_start_index"]
                    #     event_end_index = i
                    #     event_start = dates[event_start_index]
                    #     event_end = dates[event_end_index]

                    #     # Create date range for the event
                    #     event_dates = pd.date_range(
                    #         start=event_start, end=event_end, freq="2min"
                    #     ).tolist()
                    #     hist_dates.extend(event_dates)

                    #     # Record event details
                    #     event_record = pd.DataFrame(
                    #         [
                    #             {
                    #                 "RG": gauge_name,
                    #                 "Start": event_start,
                    #                 "End": event_end,
                    #                 "Depth": last_depth,
                    #                 "Intensity_Count": state["intensity_count"],
                    #                 "Passed": event_status,
                    #             }
                    #         ]
                    #     )
                    #     # Drop empty or all-NA columns from both DataFrames
                    #     rain_block_df_cleaned = rain_block_df.dropna(axis=1, how='all')
                    #     event_record_cleaned = event_record.dropna(axis=1, how='all')

                    #     rain_block_df = pd.concat([rain_block_df_cleaned, event_record_cleaned], ignore_index=True)

                    #     # rain_block_df = pd.concat(
                    #     #     [rain_block_df, event_record], ignore_index=True
                    #     # )

                # Reset state for next potential event
                state["potential_event_start_index"] = i
                _reset_state()

        return hist_dates, rain_block_df

    def getPotentialWAPUGEvents(
        self, dfRainfallSubset: pd.DataFrame, timeStep: int, gaugeName: str
    ):

        hist_dates = []
        csum = []
        running_depth = 0
        currentNoOfConsecutiveZeros = 0
        intensity_count = 0
        potential_wapug_event_start_loc = 0
        partial_intensity_count = 0

        rainfall = dfRainfallSubset["rainfall"].values
        dates = dfRainfallSubset["rain_datetime"].values

        rain_block_df = pd.DataFrame(
            columns=["RG", "Start", "End", "Depth", "Intensity_Count", "Passed"]
        )

        for i in range(len(rainfall)):

            if rainfall[i] == 0:
                # This count tracks the number of consecutive zeros
                currentNoOfConsecutiveZeros += 1
            else:
                currentNoOfConsecutiveZeros = 0

                running_depth += rainfall[i] / (60 / timeStep)
                csum.append(float(running_depth))

                # --------------------------------------------------------
                if self.useConsecutiveIntensities == 1:  # Consecutive

                    if rainfall[i] > self.requiredIntensity:

                        items = rainfall[
                            i : int(i + (self.requiredIntensityDuration / timeStep))
                        ]

                        partial_intensity_count += timeStep

                        if all(item > self.requiredIntensity for item in items):

                            intensity_count = self.requiredIntensityDuration
                else:  # Non-Consecutive

                    if rainfall[i] > self.requiredIntensity:
                        intensity_count += timeStep

                # --------------------------------------------------------

            # ______________________________________________

            # If the number of concecutive zeros goes over a threshold(self.consecZero)the Csum is set to zero
            if currentNoOfConsecutiveZeros >= self.consecZero:

                if (
                    running_depth > self.requiredDepth
                    and intensity_count >= self.requiredIntensityDuration
                ):

                    wapug_event_start_loc = potential_wapug_event_start_loc
                    wapug_event_end_loc = i

                    wapug_event_start = dates[wapug_event_start_loc]
                    wapug_event_end = dates[wapug_event_end_loc]

                    # ____________________________________________________
                    # Create list of dates from idenfied start & end date

                    p = int(
                        (
                            pd.Timedelta(
                                (wapug_event_end - wapug_event_start)
                            ).total_seconds()
                            / 120
                        )
                        + 1
                    )

                    mydates = pd.date_range(
                        start=wapug_event_start, periods=p, freq="2min"
                    ).tolist()

                    hist_dates.extend(mydates)

                    rain_block_df = pd.concat(
                        [
                            rain_block_df,
                            pd.DataFrame(
                                [
                                    {
                                        "RG": gaugeName,
                                        "Start": wapug_event_start,
                                        "End": wapug_event_end,
                                        "Depth": csum[-1],
                                        "Intensity_Count": intensity_count,
                                        "Passed": 1,
                                    }
                                ]
                            ),
                        ],
                        ignore_index=True,
                    )

                # -----------------------------------------------------
                # This is to store stats on partial events

                elif (
                    (
                        running_depth
                        >= (((100 - self.partialPercent) / 100) * self.requiredDepth)
                        and running_depth < self.requiredDepth
                        and intensity_count >= self.requiredIntensityDuration
                    )
                    or (
                        intensity_count
                        >= (
                            ((100 - self.partialPercent) / 100)
                            * self.requiredIntensityDuration
                        )
                        and intensity_count < self.requiredIntensityDuration
                        and running_depth > self.requiredDepth
                    )
                    or (
                        running_depth
                        >= (
                            ((100 - self.partialPercent) / 100) * self.requiredDepth
                            and running_depth < self.requiredDepth
                        )
                    )
                    and (
                        (
                            intensity_count
                            >= (
                                ((100 - self.partialPercent) / 100)
                                * self.requiredIntensityDuration
                            )
                        )
                        and intensity_count < self.requiredIntensityDuration
                    )
                    or (
                        partial_intensity_count >= self.requiredIntensityDuration
                        and self.useConsecutiveIntensities
                        and running_depth > self.requiredDepth
                    )
                ):

                    if len(csum) > 0:

                        if csum[-1] > 0:

                            non_depth = csum[-1]

                            rain_block_df = pd.concat(
                                [
                                    rain_block_df,
                                    pd.DataFrame(
                                        [
                                            {
                                                "RG": gaugeName,
                                                "Start": dates[
                                                    potential_wapug_event_start_loc
                                                ],
                                                "End": dates[i],
                                                "Depth": non_depth,
                                                "Intensity_Count": intensity_count,
                                                "Passed": 0.5,
                                            }
                                        ]
                                    ),
                                ],
                                ignore_index=True,
                            )

                            # rain_block_df = rain_block_df.append({'RG': rg.gaugeName, 'Start': dates[potential_wapug_event_start_loc], 'End': dates[i], 'Depth': non_depth,
                            #                                       'Intensity_Count': intensity_count, 'Passed': 0.5}, ignore_index=True)

                # -----------------------------------------------------
                # This is to store stats on non-events
                else:

                    if len(csum) > 0:

                        if csum[-1] > 0:

                            non_depth = csum[-1]

                            # test_df = test_df.append({'RG': rg.gaugeName, 'Start': dates[potential_wapug_event_start_loc], 'End': dates[
                            #     i], 'Depth': non_depth, 'Intensity_Count': intensity_count, 'Passed': 0}, ignore_index=True)

                            # dfTest = pd.DataFrame([{'RG': rg.gaugeName, 'Start': dates[potential_wapug_event_start_loc],
                            #                       'End': dates[i], 'Depth': non_depth, 'Intensity_Count': intensity_count, 'Passed': 0}])

                            rain_block_df = pd.concat(
                                [
                                    rain_block_df,
                                    pd.DataFrame(
                                        [
                                            {
                                                "RG": gaugeName,
                                                "Start": dates[
                                                    potential_wapug_event_start_loc
                                                ],
                                                "End": dates[i],
                                                "Depth": non_depth,
                                                "Intensity_Count": intensity_count,
                                                "Passed": 0,
                                            }
                                        ]
                                    ),
                                ],
                                ignore_index=True,
                            )
                            # rain_block_df = rain_block_df.append({'RG': rg.gaugeName, 'Start': dates[potential_wapug_event_start_loc], 'End': dates[
                            #                                      i], 'Depth': non_depth, 'Intensity_Count': intensity_count, 'Passed': 0}, ignore_index=True)
                # _______________________________________________________________________________________

                potential_wapug_event_start_loc = i
                running_depth = 0
                currentNoOfConsecutiveZeros = 0
                csum.clear()
                intensity_count = 0
                partial_intensity_count = 0

        return (hist_dates, rain_block_df)

    def developStormPlotData(self, lstEventDates: list):

        self.lstStormDatesForHistogram = []
        self.lstStormCountForHistogram = []
        self.hasStormEvents = False

        if len(lstEventDates) > 0:

            self.hasStormEvents = True
            lstEventDates = sorted(lstEventDates)

            whole_range_start = lstEventDates[0] - timedelta(days=1)
            whole_range_end = lstEventDates[-1] + timedelta(days=1)

            noOfPeriods = int(
                ((whole_range_end - whole_range_start).total_seconds() / 120) + 1
            )

            whole_range_dates = pd.date_range(
                start=whole_range_start, periods=noOfPeriods, freq="2min"
            ).tolist()

            dates_df = pd.DataFrame({"rain_date": whole_range_dates})
            count_df = pd.DataFrame({"rain_date": lstEventDates})
            count_df["count"] = 0
            count_df["count"] = count_df.groupby(["rain_date"])["count"].transform(
                "count"
            )
            count_df.sort_values(by="rain_date", inplace=True)

            hist_df = pd.merge(
                dates_df,
                count_df,
                how="left",
                left_on="rain_date",
                right_on="rain_date",
            )

            hist_dates_timsestamp = hist_df["rain_date"].tolist()
            self.lstStormDatesForHistogram = mpl_dates.date2num(hist_dates_timsestamp)

            hist_count = hist_df["count"].tolist()
            self.lstStormCountForHistogram = [
                0 if math.isnan(x) else x for x in hist_count
            ]

    # def developDWFPlotData(self, lstDryDays):

    #     self.lstDWFCountForHistogram = []
    #     self.lstDWFDatesForHistogram = []
    #     self.hasDWFEvents = False

    #     if len(lstDryDays) > 0:

    #         self.hasDWFEvents = True

    #         lstDryDays = sorted(lstDryDays)

    #         DWF_whole_range_start = lstDryDays[0] - timedelta(days=1)
    #         DWF_whole_range_end = lstDryDays[-1] + timedelta(days=1)

    #         noOfPeriods = int(
    #             ((DWF_whole_range_end - DWF_whole_range_start).total_seconds() / 120)+1)

    #         DWF_whole_range_dates = pd.date_range(
    #             start=DWF_whole_range_start, periods=noOfPeriods, freq='2min').tolist()

    #         DWF_dates_df = pd.DataFrame({'rain_date': DWF_whole_range_dates})
    #         DWF_count_df = pd.DataFrame({'rain_date': lstDryDays})
    #         DWF_count_df['count'] = 0
    #         DWF_count_df['count'] = DWF_count_df.groupby(
    #             ['rain_date'])['count'].transform("count")
    #         DWF_count_df.sort_values(by='rain_date', inplace=True)

    #         DWF_dates_df['rain_date'] = pd.to_datetime(
    #             DWF_dates_df['rain_date']).dt.date

    #         DWF_hist_df = pd.merge(
    #             DWF_dates_df, DWF_count_df, how='left', left_on='rain_date', right_on='rain_date')

    #         DWF_hist_dates_timsestamp = DWF_hist_df['rain_date'].tolist()

    #         self.lstDWFDatesForHistogram = mpl_dates.date2num(
    #             DWF_hist_dates_timsestamp)

    #         DWF_hist_count = DWF_hist_df['count'].tolist()

    #         self.lstDWFCountForHistogram = [
    #             0 if math.isnan(x) else x for x in DWF_hist_count]

    def developDWFPlotData(self, lstDryDays):

        self.lstDWFCountForHistogram = []
        self.lstDWFDatesForHistogram = []
        self.hasDWFEvents = False

        if len(lstDryDays) > 0:

            self.hasDWFEvents = True

            lstDryDays = sorted(lstDryDays)

            DWF_whole_range_start = lstDryDays[0] - timedelta(days=1)
            DWF_whole_range_end = lstDryDays[-1] + timedelta(days=1)

            noOfPeriods = int(
                ((DWF_whole_range_end - DWF_whole_range_start).total_seconds() / 86400)
                + 1
            )
            # DWF_whole_range_dates = pd.date_range(
            #     start=DWF_whole_range_start, periods=noOfPeriods, freq="24H"
            # ).tolist()
            DWF_whole_range_dates = pd.date_range(
                start=DWF_whole_range_start, periods=noOfPeriods, freq="24h"
            ).tolist()            
            DWF_dates_df = pd.DataFrame({"rain_date": DWF_whole_range_dates})
            DWF_count_df = pd.DataFrame({"rain_date": lstDryDays})
            DWF_count_df["count"] = 0
            DWF_count_df["count"] = DWF_count_df.groupby(["rain_date"])[
                "count"
            ].transform("count")
            DWF_count_df.sort_values(by="rain_date", inplace=True)
            DWF_dates_df["rain_date"] = pd.to_datetime(
                DWF_dates_df["rain_date"]
            ).dt.date
            DWF_hist_df = pd.merge(
                DWF_dates_df, DWF_count_df, how="left", on="rain_date"
            )
            DWF_hist_df.drop_duplicates(ignore_index=True, inplace=True)
            DWF_hist_dates_timsestamp = DWF_hist_df["rain_date"].tolist()

            self.lstDWFDatesForHistogram = mpl_dates.date2num(DWF_hist_dates_timsestamp)
            DWF_hist_count = DWF_hist_df["count"].tolist()
            self.lstDWFCountForHistogram = [
                0 if math.isnan(x) else x for x in DWF_hist_count
            ]

    def updateRainfallAnalysis(self):

        lstDryDays = []
        lstEventDates = []
        self.dfRainBlock = pd.DataFrame(
            columns=["RG", "Start", "End", "Depth", "Intensity_Count", "Passed"]
        )
        self.dictRainfallSubsets = {}

        for rg in self.plotted_rgs.plotRGs.values():

            dfRainfallSubset = self.getSubsetOfRainfallFromRaingauge(rg)
            self.dictRainfallSubsets[rg.gaugeName] = dfRainfallSubset
            dfRainfallSubsetByDay = dfRainfallSubset.groupby(
                "rain_date", as_index=False
            )["rainfall_mm"].sum()

            lstRGDryDays = self.getListOfDryDays(dfRainfallSubsetByDay)
            lstDryDays.extend(lstRGDryDays)

            # if self.useNewMethod:
            #     lstRGEventDates, dfRGRainBlock = self.getPotentialWAPUGEventsNM(
            #         dfRainfallSubset, rg.rgTimestep, rg.gaugeName
            #     )
            # else:
            #     lstRGEventDates, dfRGRainBlock = self.getPotentialWAPUGEvents(
            #         dfRainfallSubset, rg.rgTimestep, rg.gaugeName
            #     )

            lstRGEventDates, dfRGRainBlock = self.getPotentialWAPUGEventsNM(dfRainfallSubset, rg.rgTimestep, rg.gaugeName)
            # lstRGEventDates, dfRGRainBlock = self.getPotentialWAPUGEvents(dfRainfallSubset, rg.rgTimestep, rg.gaugeName)
                        
            lstEventDates.extend(lstRGEventDates)

            # Drop empty or all-NA columns from both DataFrames
            RainBlock_cleaned = self.dfRainBlock.dropna(axis=1, how='all')
            RGRainBlock_cleaned = dfRGRainBlock.dropna(axis=1, how='all')

            self.dfRainBlock = pd.concat([RainBlock_cleaned, RGRainBlock_cleaned], ignore_index=True)
                        
            # self.dfRainBlock = pd.concat(
            #     [self.dfRainBlock, dfRGRainBlock], ignore_index=True
            # )

        self.developDWFPlotData(lstDryDays)
        self.developStormPlotData(lstEventDates)

        self.dfRainBlock["Start_sec"] = [
            mpl_dates.date2num(t) for t in self.dfRainBlock.Start
        ]
        self.dfRainBlock["End_sec"] = [
            mpl_dates.date2num(t) for t in self.dfRainBlock.End
        ]
        self.dfRainBlock["Diff"] = self.dfRainBlock.End_sec - self.dfRainBlock.Start_sec

        self.analysisNeedsRefreshed = False

    def refreshPlots(self):

        self.rIntLines = []
        gs = mpl_gridspec.GridSpec(3, 1, height_ratios=[1.5, 3, 2])
        gs.update(wspace=0.025, hspace=0.16)

        (self.plotAxisHistogram, self.plotAxisGant, self.plotAxisIntensity) = (
            self.main_window_plot_widget.figure.subplots(
                3, sharex=True, gridspec_kw={"height_ratios": [1.5, 3, 2]}
            )
        )

        colors = cycle(
            [
                "aqua",
                "crimson",
                "lime",
                "fuchsia",
                "gray",
                "olive",
                "teal",
                "orange",
                "green",
                "purple",
                "maroon",
                "blue",
                "yellow",
                "Gold",
                "red",
                "peru",
                "skyblue",
                "olivedrab",
                "royalblue",
                "cornflowerblue",
                "yellowgreen",
                "mediumaquamarine",
                "indianred",
                "darkseagreen",
                "steelblue",
                "darkslateblue",
                "thistle",
                "darkorchid",
                "seagreen",
                "pink",
                "hotpink",
            ]
        )

        for rgName, dfRain in self.dictRainfallSubsets.items():
            # dfRainfallSubset = self.getSubsetOfRainfallFromRaingauge(rg)
            (rIntLine,) = self.plotAxisIntensity.plot(
                dfRain["rain_datetime"],
                dfRain["rainfall"],
                label=rgName,
                color=next(colors),
                gid=rgName,
            )
            self.rIntLines.append(rIntLine)  # Event intensity lines

        color = {1: "#33FF33", 0: "#E57373", 0.5: "#FFA726"}

        labels = []
        for i, RG in enumerate(self.dfRainBlock.groupby("RG")):
            labels.append(RG[0])

            for r in RG[1].groupby("Passed"):
                data = r[1][["Start_sec", "Diff"]]
                self.plotAxisGant.broken_barh(
                    data.values, (i - 0.4, 0.8), color=color[r[0]], label=RG[0]
                )

        self.plotAxisGant.set_yticks(range(len(labels)))
        self.plotAxisGant.set_yticklabels(labels)
        self.plotAxisGant.grid(True)
        self.plotAxisGant.xaxis_date()

        red_patch = mpl_patches.Patch(color="#E57373", label="No Event")
        orange_patch = mpl_patches.Patch(
            color="#FFA726", label="Partial Event (" + str(self.partialPercent) + "%)"
        )
        green_patch = mpl_patches.Patch(color="#33FF33", label="Event")
        self.plotAxisGant.legend(
            loc="best", handles=[red_patch, orange_patch, green_patch], prop={"size": 6}
        )

        # major_tick_format = DateFormatter("%d/%m/%Y %H:%M")
        # self.plotAxisGant.xaxis.set_major_locator(MaxNLocator(integer=False))
        # self.plotAxisGant.xaxis.set_major_formatter(FuncFormatter(major_tick_format))
        self.plotAxisGant.tick_params(labelbottom=False)
        self.plotAxisGant.tick_params(axis="y", which="major", labelsize=8, direction="in", pad=-70)
        self.plotAxisGant.set_ylabel("Rainfall Gantt Chart", fontsize=8)
        self.plotAxisGant.autoscale(enable=True, axis="y", tight=None)

        self.plotAxisHistogram.step(
            self.lstStormDatesForHistogram,
            self.lstStormCountForHistogram,
            label="Storm Event",
            where="post",
        )
        self.plotAxisHistogram.step(
            self.lstDWFDatesForHistogram,
            self.lstDWFCountForHistogram,
            label="Dry Day",
            where="post",
        )

        if len(self.plotted_rgs.plotRGs) <= 18:
            fsize = 8
        else:
            fsize = 6

        depth_props = dict(boxstyle="round", facecolor="teal", alpha=0.5)
        self.plot_depth_stats_box = self.plotAxisIntensity.text(
            -0.01,
            1.14,
            "Depth(mm) - ",
            transform=self.plotAxisIntensity.transAxes,
            fontsize=fsize,
            verticalalignment="top",
            bbox=depth_props,
            wrap=True,
        )

        self.plotAxisIntensity.margins(0.1)
        self.plotAxisIntensity.grid(True)

        if self.hasStormEvents or self.hasDWFEvents:

            self.plotAxisHistogram.margins(0.1)
            self.plotAxisHistogram.grid(True)

            self.plotAxisHistogram.tick_params(axis="y", which="major", labelsize=8)

            self.plotAxisHistogram.axhline(
                y=len(self.plotted_rgs.plotRGs),
                xmin=0,
                xmax=3,
                c="springgreen",
                linewidth=2,
                zorder=0,
                linestyle="dashed",
            )  # install height

            # hist_title = (
            #     str(len(self.plotted_rgs.plotRGs))
            #     + " Rain Gauge Storm Event & Dry Day Analysis (Storm: Consecutive Zeros >= "
            #     + str(self.consecZero)
            #     + ", Depth > "
            #     + str(self.requiredDepth)
            #     + ", Intensity > "
            #     + str(self.requiredIntensity)
            #     + ", Intensity Duration >= "
            #     + str(self.requiredIntensityDuration)
            #     + " - DWF: Depth Tolerance <= "
            #     + str(self.rainfallDepthTolerance)
            #     + " , Preceding Dry Days > "
            #     + str(self.precedingDryDays)
            #     + ", Consecutive Intensities = "
            #     + str(self.useConsecutiveIntensities)
            #     + ")"
            # )
            hist_title = (f"{len(self.plotted_rgs.plotRGs)} Rain Gauge Storm Event & Dry Day Analysis/n(Storm: Consecutive Zeros >= {self.consecZero}, Depth > {self.requiredDepth}, Intensity > {self.requiredIntensity}, Intensity Duration >= {self.requiredIntensityDuration} - DWF: Depth Tolerance <= {self.rainfallDepthTolerance}, Preceding Dry Days > {self.precedingDryDays}, Consecutive Intensities = {self.useConsecutiveIntensities})")

            self.plotAxisHistogram.set_title(hist_title, color="grey", fontsize=9)

            # major_tick_format = DateFormatter("%d/%m/%Y %H:%M")
            # self.plotAxisHistogram.xaxis.set_major_locator(MaxNLocator(integer=False))
            # self.plotAxisHistogram.xaxis.set_major_formatter(
            #     FuncFormatter(major_tick_format)
            # )         
            self.plotAxisHistogram.autoscale(enable=True, axis="y", tight=None)
            self.plotAxisHistogram.tick_params(labelbottom=False)
            self.plotAxisHistogram.tick_params(axis="y", which="major", labelsize=4)

            self.plotAxisHistogram.set_ylabel(
                "Number of RGs that Passed DWF \n or Storm Event Criteria", fontsize=6
            )
            self.plotAxisHistogram.autoscale(enable=True, axis="y", tight=None)

        locator = AutoDateLocator(minticks=6, maxticks=15)
        formatter = ConciseDateFormatter(locator)
        self.plotAxisIntensity.xaxis.set_major_locator(locator)
        self.plotAxisIntensity.xaxis.set_major_formatter(formatter)   

        self.plotAxisIntensity.tick_params(axis="y", which="major", labelsize=6)
        self.plotAxisIntensity.set_ylabel("Rainfall Intensty (mm/hr)", fontsize=8)
        self.plotAxisIntensity.autoscale(enable=True, axis="y", tight=None)

        # self.plotCanvas = FigureCanvasTkAgg(fig_event_hist, self)
        self.plotAxisHistogram.legend(loc="best", prop={"size": 6})
        leg = self.plotAxisIntensity.legend(
            loc="best", prop={"size": 6}, ncol=2, fancybox=True
        )

        self.rIntLegendLines = dict()
        for legline, origline in zip(leg.get_lines(), self.rIntLines):
            legline.set_picker(5)  # 5 pts tolerance
            self.rIntLegendLines[legline] = origline

        self.main_window_plot_widget.figure.autofmt_xdate()
        self.main_window_plot_widget.figure.subplots_adjust(
            left=0.05, right=0.98, bottom=0.075, top=0.94
        )

        self.plotAxisHistogram.callbacks.connect("xlim_changed", self.onPlotXlimsChange)
        self.plotAxisGant.callbacks.connect("xlim_changed", self.onPlotXlimsChange)
        self.plotAxisIntensity.callbacks.connect("xlim_changed", self.onPlotXlimsChange)

        self.onPlotXlimsChange(self.plotAxisIntensity)

    def onPick(self, event):

        legline = event.artist
        origline = self.rIntLegendLines[legline]
        vis = not origline.get_visible()

        origline.set_visible(vis)
        # Change the alpha on the line in the legend so we can see what lines have been toggled
        if vis:
            legline.set_alpha(1.0)
        else:
            legline.set_alpha(0.2)

        self.main_window_plot_widget.figure.canvas.draw()

    # __________________________________________________________________________________________
    # This is the right click on legend

    def onClick(self, event):

        if event.button == 3:

            for legline in self.rIntLegendLines:

                origline = self.rIntLegendLines[legline]
                origline.set_visible(False)
                legline.set_alpha(0.2)

        if event.button == 2:

            for legline in self.rIntLegendLines:

                origline = self.rIntLegendLines[legline]
                origline.set_visible(True)
                legline.set_alpha(1)

        self.main_window_plot_widget.figure.canvas.draw()

    # __________________________________________________________________________________________

    def onPlotXlimsChange(self, event_ax):

        xmin, xmax = mpl_dates.num2date(event_ax.get_xlim())

        i = 0
        for rg in self.plotted_rgs.plotRGs.values():
            stats = rg.statsBetweenDates(xmin, xmax)

            if i == 0:
                multi_depth_string = (
                    "Depth(mm) - " + rg.gaugeName + " = " + str(stats["totDepth"])
                )
            else:
                multi_depth_string = (
                    multi_depth_string
                    + ", "
                    + rg.gaugeName
                    + " = "
                    + str(stats["totDepth"])
                )

            if not self.plot_depth_stats_box is None:
                self.plot_depth_stats_box.set_text(multi_depth_string)
            i += 1


class graphCumulativeDepth:

    plotAxisCumDepth = None
    plot_depth_stats_box = None
    plotted_rgs = None
    __plot_event = None
    startDate = datetime.strptime("2172-05-12", "%Y-%m-%d")

    c_depth_legend_lines = None
    c_depth_lines = None

    main_window_plot_widget: PlotWidget = None
    isBlank = True

    def __init__(self, mw_pw: PlotWidget = None):

        self.main_window_plot_widget = mw_pw
        getBlankFigure(self.main_window_plot_widget)
        self.isBlank = True

        # self.plotFigure = self.getBlankFigure()
        # self.plotCanvas = MplCanvas(self.plotFigure)

        self.plotted_rgs = plottedRainGauges()
        self.update_plot()

    def set_plot_event(self, se):

        self.__plot_event = se
        if not self.plotted_rgs is None:
            if self.__plot_event is None:
                self.plotted_rgs.setPlotDateLimits(None, None)
            else:
                self.plotted_rgs.setPlotDateLimits(se.eventStart, se.eventEnd)

    def get_plot_event(self):

        return self.__plot_event

    def has_plot_event(self):

        if self.__plot_event is None:
            return False
        else:
            return True

    def get_plot_eventName(self):

        if not self.__plot_event is None:
            return self.__plot_event.eventName

    def update_plot(self):

        self.main_window_plot_widget.figure.clear()
        if len(self.plotted_rgs.plotRGs) > 0:
            self.updateCumulativeDepthLines()
            self.isBlank = False
        else:
            getBlankFigure(self.main_window_plot_widget)
            self.isBlank = True

            # self.plotCanvas = MplCanvas(self.plotFigure)
        self.updateCanvas()

    def updateCanvas(self):

        if not self.plotAxisCumDepth is None:
            mplcursors.cursor(self.plotAxisCumDepth, hover=True)
            self.main_window_plot_widget.event_connections.append(self.main_window_plot_widget.figure.canvas.mpl_connect("pick_event", self.onPick))

        self.main_window_plot_widget.showToolbar(not self.isBlank)
        self.main_window_plot_widget.toolbar.lockNavigation(self.has_plot_event())

    def updateCumulativeDepthLines(self):
        # X = []
        # Y = []
        # sData = []
        # cMap = []
        self.plotAxisCumDepth = self.main_window_plot_widget.figure.subplots(1)
        self.c_depth_lines = []

        colors = cycle(
            [
                "aqua",
                "crimson",
                "lime",
                "fuchsia",
                "gray",
                "olive",
                "teal",
                "orange",
                "green",
                "purple",
                "maroon",
                "blue",
                "yellow",
                "Gold",
                "red",
                "peru",
                "skyblue",
                "olivedrab",
                "royalblue",
                "cornflowerblue",
                "yellowgreen",
                "mediumaquamarine",
                "indianred",
                "darkseagreen",
                "steelblue",
                "darkslateblue",
                "thistle",
                "darkorchid",
                "seagreen",
                "pink",
                "hotpink",
            ]
        )

        for rg in self.plotted_rgs.plotRGs.values():

            dates = rg.dateRange
            intencities = rg.rainfallDataRange
            cum_depths = intencities.copy()
            # cumDepth = 0
            tobedeleted = []

            if self.has_plot_event():

                for i in reversed(range(len(rg.dateRange))):
                    if (
                        rg.dateRange[i] < self.__plot_event.eventStart
                        or rg.dateRange[i] > self.__plot_event.eventEnd
                    ):
                        tobedeleted.append(i)
            else:
                for i in reversed(range(len(rg.dateRange))):
                    if rg.dateRange[i] < self.startDate:
                        tobedeleted.append(i)

            if len(tobedeleted) > 0:
                dates = np.delete(dates, tobedeleted)
                intencities = np.delete(intencities, tobedeleted)
                cum_depths = np.delete(cum_depths, tobedeleted)

            for i in range(len(dates)):

                if i == 0:
                    cum_depths[0] = 0.0
                else:
                    timeDelta = int((dates[i] - dates[i - 1]).seconds / 60)
                    avgIntensity = (intencities[i] + intencities[i - 1]) / 2
                    inc_depth = avgIntensity * (timeDelta / 60)
                    cum_depths[i] = cum_depths[i - 1] + inc_depth

            (cdepth_line,) = self.plotAxisCumDepth.plot(
                dates,
                cum_depths,
                label=rg.gaugeName,
                color=next(colors),
                gid=rg.gaugeName,
            )
            self.c_depth_lines.append(cdepth_line)

        self.plotAxisCumDepth.margins(0.1)
        self.main_window_plot_widget.figure.tight_layout()
        self.plotAxisCumDepth.grid(True)
        self.plotAxisCumDepth.tick_params(axis="y", which="major", labelsize=8)

        # major_tick_format = DateFormatter("%d/%m/%Y %H:%M")
        # self.plotAxisCumDepth.xaxis.set_major_locator(MaxNLocator(integer=False))
        # self.plotAxisCumDepth.xaxis.set_major_formatter(
        #     FuncFormatter(major_tick_format)
        # )
        locator = AutoDateLocator(minticks=6, maxticks=15)
        formatter = ConciseDateFormatter(locator)
        self.plotAxisCumDepth.xaxis.set_major_locator(locator)
        self.plotAxisCumDepth.xaxis.set_major_formatter(formatter)

        self.plotAxisCumDepth.set_ylabel("Rainfall Depth (mm)", fontsize=8)
        self.plotAxisCumDepth.autoscale(enable=True, axis="y", tight=None)

        self.main_window_plot_widget.figure.autofmt_xdate()
        # self.plotAxisCumDepth.tick_params(axis="x", which="major", labelsize=8)

        self.main_window_plot_widget.figure.subplots_adjust(
            left=0.03, right=0.98, bottom=0.15, top=0.94
        )

        self.plotAxisCumDepth.legend(loc="best", prop={"size": 6})
        leg = self.plotAxisCumDepth.legend(loc="best", prop={"size": 6})

        self.c_depth_legend_lines = dict()
        for legline, origline in zip(leg.get_lines(), self.c_depth_lines):
            legline.set_picker(5)  # 5 pts tolerance
            self.c_depth_legend_lines[legline] = origline

    def onPick(self, event):

        legline = event.artist
        origline = self.c_depth_legend_lines[legline]
        vis = not origline.get_visible()

        origline.set_visible(vis)
        # Change the alpha on the line in the legend so we can see what lines have been toggled
        if vis:
            legline.set_alpha(1.0)
        else:
            legline.set_alpha(0.2)

        self.main_window_plot_widget.figure.canvas.draw()


class graphICMTrace:

    plot_axis_depth = None
    plot_axis_flow = None
    plot_axis_velocity = None
    plotAxisTable = None
    plottedICMTrace = None
    plot_flow_stats_box = None
    c_flow_lines = None
    c_depth_lines = None
    c_vel_lines = None
    c_flow_legend_lines = None
    c_depth_legend_lines = None
    c_vel_legend_lines = None
    currentTitle = ""

    main_window_plot_widget: PlotWidget = None
    isBlank = True

    def __init__(self, mw_pw: PlotWidget = None):

        self.main_window_plot_widget = mw_pw
        getBlankFigure(self.main_window_plot_widget)
        self.isBlank = True

        self.plottedICMTrace = plottedICMTrace()

    def update_plot(self):

        self.main_window_plot_widget.figure.clear()
        if self.plottedICMTrace.plotTrace is None:
            getBlankFigure(self.main_window_plot_widget)
            self.isBlank = True
            return

        # (self.plotAxisTable, self.plot_axis_depth, self.plot_axis_flow, self.plot_axis_velocity) = self.main_window_plot_widget.figure.subplots(4, dpi=100, figsize=(15.4, 10.0), gridspec_kw={'height_ratios': [0.6, 1, 1, 1]})
        (
            self.plotAxisTable,
            self.plot_axis_depth,
            self.plot_axis_flow,
            self.plot_axis_velocity,
        ) = self.main_window_plot_widget.figure.subplots(
            4, gridspec_kw={"height_ratios": [0.6, 1, 1, 1]}
        )
        self.plot_axis_depth.sharex(self.plot_axis_velocity)
        self.plot_axis_flow.sharex(self.plot_axis_depth)

        # major_tick_format = DateFormatter("%d/%m/%Y %H:%M")

        colors = cycle(
            [
                "mediumseagreen",
                "indianred",
                "steelblue",
                "goldenrod",
                "deepskyblue",
                "lime",
                "black",
                "purple",
                "navy",
                "olive",
                "fuchsia",
                "grey",
                "silver",
                "teal",
                "red",
            ]
        )
        self.c_flow_lines = []
        self.c_depth_lines = []
        self.c_vel_lines = []

        obsColour = "indianred"
        obsPeakColour = "red"
        predColour = "lime"
        predPeakColour = "green"

        aLoc = list(self.plottedICMTrace.plotTrace.dictLocations.values())[
            self.plottedICMTrace.plotTrace.currentLocation
        ]
        self.currentTitle = aLoc.pageTitle[16:-1]

        (aObsFlow,) = self.plot_axis_flow.plot(
            aLoc.dates,
            aLoc.rawData[aLoc.iObsFlow],
            "-",
            linewidth=1.1,
            label="Observed",
            color=obsColour,
        )
        (aObsDepth,) = self.plot_axis_depth.plot(
            aLoc.dates,
            aLoc.rawData[aLoc.iObsDepth],
            "-",
            linewidth=1.1,
            label="Observed",
            color=obsColour,
        )
        (aObsVelocity,) = self.plot_axis_velocity.plot(
            aLoc.dates,
            aLoc.rawData[aLoc.iObsVelocity],
            "-",
            linewidth=1.1,
            label="Observed",
            color=obsColour,
        )
        (aPredFlow,) = self.plot_axis_flow.plot(
            aLoc.dates,
            aLoc.rawData[aLoc.iPredFlow],
            "-",
            linewidth=1.1,
            label="Predicted",
            color=predColour,
        )
        (aPredDepth,) = self.plot_axis_depth.plot(
            aLoc.dates,
            aLoc.rawData[aLoc.iPredDepth],
            "-",
            linewidth=1.1,
            label="Predicted",
            color=predColour,
        )
        (aPredVelocity,) = self.plot_axis_velocity.plot(
            aLoc.dates,
            aLoc.rawData[aLoc.iPredVelocity],
            "-",
            linewidth=1.1,
            label="Predicted",
            color=predColour,
        )

        if aLoc.verifyForFlow:
            if not aLoc.peaksInitialized[aLoc.iObsFlow]:
                aLoc.updatePeaks(aLoc.iObsFlow)
            (aObsFlowPk,) = self.plot_axis_flow.plot(
                aLoc.peaksDates[aLoc.iObsFlow],
                aLoc.peaksData[aLoc.iObsFlow],
                "o",
                label="Observed Peaks",
                color=obsPeakColour,
            )

            if not aLoc.peaksInitialized[aLoc.iPredFlow]:
                aLoc.updatePeaks(aLoc.iPredFlow)
            (aPredFlowPk,) = self.plot_axis_flow.plot(
                aLoc.peaksDates[aLoc.iPredFlow],
                aLoc.peaksData[aLoc.iPredFlow],
                "o",
                label="Predicted Peaks",
                color=predPeakColour,
            )

            self.createUDGTable(aLoc)

        if aLoc.verifyForDepth:
            if not aLoc.peaksInitialized[aLoc.iObsDepth]:
                aLoc.updatePeaks(aLoc.iObsDepth)
            (aObsDepthPk,) = self.plot_axis_depth.plot(
                aLoc.peaksDates[aLoc.iObsDepth],
                aLoc.peaksData[aLoc.iObsDepth],
                "o",
                label="Observed Peaks",
                color=obsPeakColour,
            )

            if not aLoc.peaksInitialized[aLoc.iPredDepth]:
                aLoc.updatePeaks(aLoc.iPredDepth)
            (aPredDepthPk,) = self.plot_axis_depth.plot(
                aLoc.peaksDates[aLoc.iPredDepth],
                aLoc.peaksData[aLoc.iPredDepth],
                "o",
                label="Predicted Peaks",
                color=predPeakColour,
            )

            self.createUDGDepthTable(aLoc)

        self.c_flow_lines.append(aObsFlow)
        self.c_flow_lines.append(aPredFlow)
        self.c_depth_lines.append(aObsDepth)
        self.c_depth_lines.append(aPredDepth)
        self.c_vel_lines.append(aObsVelocity)
        self.c_vel_lines.append(aPredVelocity)

        # Depth
        self.plot_axis_depth.yaxis.set_major_locator(MaxNLocator(integer=True))
        self.plot_axis_depth.set_ylabel("Depth (m)", fontsize=8)
        self.plot_axis_depth.tick_params(axis="y", which="major", labelsize=8)

        self.plot_axis_flow.yaxis.set_major_locator(MaxNLocator(integer=True))
        self.plot_axis_flow.set_ylabel("Flow (m³/s)", fontsize=8)
        self.plot_axis_flow.tick_params(axis="y", which="major", labelsize=8)

        # Velocity
        self.plot_axis_velocity.yaxis.set_major_locator(MaxNLocator(8))
        # self.plot_axis_velocity.xaxis.set_major_locator(MaxNLocator(integer=False))
        # self.plot_axis_velocity.xaxis.set_major_formatter(FuncFormatter(major_tick_format))

        locator = AutoDateLocator(minticks=6, maxticks=15)
        formatter = ConciseDateFormatter(locator)
        self.plot_axis_velocity.xaxis.set_major_locator(locator)
        self.plot_axis_velocity.xaxis.set_major_formatter(formatter)

        self.plot_axis_velocity.set_ylabel("Velocity (m/s)", fontsize=8)
        self.plot_axis_velocity.tick_params(axis="y", which="major", labelsize=8)

        self.plot_axis_flow.callbacks.connect("xlim_changed", self.onPlotXlimsChange)
        self.plot_axis_depth.callbacks.connect("xlim_changed", self.onPlotXlimsChange)
        self.plot_axis_velocity.callbacks.connect(
            "xlim_changed", self.onPlotXlimsChange
        )

        self.refreshTable()

        p = int(
            (
                (
                    self.plottedICMTrace.plotLatestEnd
                    - self.plottedICMTrace.plotEarliestStart
                ).total_seconds()
                / 120
            )
            + 1
        )

        self.plot_axis_flow.grid(True)
        self.plot_axis_depth.grid(True)
        self.plot_axis_velocity.grid(True)

        self.main_window_plot_widget.figure.autofmt_xdate()
        # self.plotFigure.subplots_adjust(left=0.09, right=0.98, bottom=0.17, top=0.94)
        self.main_window_plot_widget.figure.subplots_adjust(
            left=0.09, right=0.98, bottom=0.10, top=0.94
        )

        # if aLoc.showFlowPeaks:
        #     self.createUDGTable(aLoc)

        # if aLoc.showDepthPeaks:
        #     self.createUDGDepthTable(aLoc)

        self.updateCanvas()

    def refreshTable(self):

        if not self.plotAxisTable is None:

            self.plotAxisTable.clear()

            self.plotAxisTable.set_title(self.currentTitle, color="black", fontsize=15)

            df = pd.DataFrame()

            df["Min Depth"] = formatTableData(
                self.plottedICMTrace.plotMinObsDepth,
                self.plottedICMTrace.plotMinPredDepth,
                3,
            )

            df["Max Depth"] = formatTableData(
                self.plottedICMTrace.plotMaxObsDepth,
                self.plottedICMTrace.plotMaxPredDepth,
                3,
            )

            df["Min Flow"] = formatTableData(
                self.plottedICMTrace.plotMinObsFlow,
                self.plottedICMTrace.plotMinPredFlow,
                3,
            )

            df["Max Flow"] = formatTableData(
                self.plottedICMTrace.plotMaxObsFlow,
                self.plottedICMTrace.plotMaxPredFlow,
                3,
            )

            df["Volume"] = formatTableData(
                self.plottedICMTrace.plotTotalObsVolume,
                self.plottedICMTrace.plotTotalPredVolume,
                1,
            )

            df["Min Velocity"] = formatTableData(
                self.plottedICMTrace.plotMinObsVelocity,
                self.plottedICMTrace.plotMinPredVelocity,
                3,
            )

            df["Max Velocity"] = formatTableData(
                self.plottedICMTrace.plotMaxObsVelocity,
                self.plottedICMTrace.plotMaxPredVelocity,
                3,
            )

            self.plotAxisTable.axis("off")
            fs = 8
            add_cell(
                self.plotAxisTable,
                [["Difference"]],
                [0, 0, 0.125, 0.1875],
                [["#71004b"]],
                fs,
                "w",
                "bold",
            )
            add_cell(
                self.plotAxisTable,
                [["Predicted"]],
                [0, 0.1875, 0.125, 0.1875],
                [["#71004b"]],
                fs,
                "w",
                "bold",
            )
            add_cell(
                self.plotAxisTable,
                [["Observed"]],
                [0, 0.375, 0.125, 0.1875],
                [["#71004b"]],
                fs,
                "w",
                "bold",
            )
            add_cell(
                self.plotAxisTable, df.values, [0.125, 0, 0.875, 0.5625], None, fs, "k"
            )
            add_cell(
                self.plotAxisTable,
                [["Min\n(m)", "Max\n(m)"]],
                [0.125, 0.5625, 0.25, 0.25],
                [["#71004b", "#71004b"]],
                fs,
                "w",
                "bold",
            )
            add_cell(
                self.plotAxisTable,
                [["Depth"]],
                [0.125, 0.8125, 0.25, 0.1875],
                [["#71004b"]],
                fs,
                "w",
                "bold",
            )
            add_cell(
                self.plotAxisTable,
                [["Min\n(m3/s)", "Max\n(m3/s)", "Volume\n(m3)"]],
                [0.375, 0.5625, 0.375, 0.25],
                [["#71004b", "#71004b", "#71004b"]],
                fs,
                "w",
                "bold",
            )
            add_cell(
                self.plotAxisTable,
                [["Flow"]],
                [0.375, 0.8125, 0.375, 0.1875],
                [["#71004b"]],
                fs,
                "w",
                "bold",
            )
            add_cell(
                self.plotAxisTable,
                [["Min\n(m/s)", "Max\n(m/s)"]],
                [0.75, 0.5625, 0.25, 0.25],
                [["#71004b", "#71004b"]],
                fs,
                "w",
                "bold",
            )
            add_cell(
                self.plotAxisTable,
                [["Velocity"]],
                [0.75, 0.8125, 0.25, 0.1875],
                [["#71004b"]],
                fs,
                "w",
                "bold",
            )

            # self.plotAxisTable.axis("off")
            # fs = 8
            # add_cell(self.plotAxisTable, [['Difference']], [
            #     0, 0, 0.125, 0.1875], [["#d4f1ff"]], fs)
            # add_cell(self.plotAxisTable, [['Predicted']], [
            #     0, 0.1875, 0.125, 0.1875], [["#d4f1ff"]], fs)
            # add_cell(self.plotAxisTable, [['Observed']], [
            #     0, 0.375, 0.125, 0.1875], [["#d4f1ff"]], fs)
            # add_cell(self.plotAxisTable, df.values, [
            #     0.125, 0, 0.875, 0.5625], None, fs)
            # add_cell(self.plotAxisTable, [['Min\n(m)', 'Max\n(m)']], [
            #     0.125, 0.5625, 0.25, 0.25], [["#d4f1ff", "#d4f1ff"]], fs)
            # add_cell(self.plotAxisTable, [['Depth']], [
            #     0.125, 0.8125, 0.25, 0.1875], [["#d4f1ff"]], fs)
            # add_cell(self.plotAxisTable, [['Min\n(m3/s)', 'Max\n(m3/s)', 'Volume\n(m3)']], [
            #     0.375, 0.5625, 0.375, 0.25], [["#d4f1ff", "#d4f1ff", "#d4f1ff"]], fs)
            # add_cell(self.plotAxisTable, [['Flow']], [
            #     0.375, 0.8125, 0.375, 0.1875], [["#d4f1ff"]], fs)
            # add_cell(self.plotAxisTable, [[
            #     'Min\n(m/s)', 'Max\n(m/s)']], [0.75, 0.5625, 0.25, 0.25], [["#d4f1ff", "#d4f1ff"]], fs)
            # add_cell(self.plotAxisTable, [['Velocity']], [
            #     0.75, 0.8125, 0.25, 0.1875], [["#d4f1ff"]], fs)

    # def add_cell(self, ax, cellText: list[list[str]], bbox, ccolors: list[list[str]] = None, font_size: int = 8):
    #     t = ax.table(cellText=cellText,
    #                  loc='bottom',
    #                  bbox=bbox,
    #                  cellLoc='center',
    #                  cellColours=ccolors)
    #     t.auto_set_font_size(False)
    #     t.set_fontsize(font_size)

    # def formatTableData(self, obVal, predVal, number_of_decimals):
    #     diffVal = predVal - obVal
    #     if obVal != 0:
    #         diffPcnt = f'({((diffVal / obVal) * 100):.0f}%)'
    #     else:
    #         diffPcnt = f'(-%)'
    #     return [f'{obVal:.{number_of_decimals}f}', f'{predVal:.{number_of_decimals}f}', f'{diffVal:.{number_of_decimals}f} {diffPcnt}']

    def createUDGTable(self, aLoc: icmTraceLocation):

        hexGreen = "#47d655"
        hexRed = "#e87676"

        if aLoc.isCritical:
            table_data = [
                [
                    twp.fill("Parameter", 10),
                    twp.fill("Actual Value", 10),
                    twp.fill("Critical Location", 10),
                ],
                [twp.fill("Shape (NSE)", 10), f"{aLoc.flowNSE:.{2}f}", ">0.5"],
                [
                    twp.fill("Time of Peaks", 10),
                    f"{aLoc.flowTp_Diff_Hrs:.{2}f}",
                    "±0.5Hr",
                ],
                [twp.fill("Peak Flow", 10), f"{aLoc.flowQp_Diff_Pcnt:.{1}f}", "±10%"],
                [
                    twp.fill("Flow Volume", 10),
                    f"{aLoc.flowVol_Diff_Pcnt:.{1}f}",
                    "±10%",
                ],
            ]

            cell_colours = [
                ["#71004b", "#71004b", "#71004b"],
                ["#ffffff", "#ffffff", hexGreen if (aLoc.flowNSE > 0.5) else hexRed],
                [
                    "#ffffff",
                    "#ffffff",
                    hexGreen if (0.5 > aLoc.flowTp_Diff_Hrs > -0.5) else hexRed,
                ],
                [
                    "#ffffff",
                    "#ffffff",
                    hexGreen if (10 > aLoc.flowQp_Diff_Pcnt > -10) else hexRed,
                ],
                [
                    "#ffffff",
                    "#ffffff",
                    hexGreen if (10 > aLoc.flowVol_Diff_Pcnt > -10) else hexRed,
                ],
            ]

        else:
            table_data = [
                [
                    twp.fill("Parameter", 10),
                    twp.fill("Actual Value", 10),
                    twp.fill("General Location", 10),
                ],
                [twp.fill("Shape (NSE)", 10), f"{aLoc.flowNSE:.{2}f}", ">0.5"],
                [
                    twp.fill("Time of Peaks", 10),
                    f"{aLoc.flowTp_Diff_Hrs:.{2}f}",
                    "±0.5Hr",
                ],
                [
                    twp.fill("Peak Flow", 10),
                    f"{aLoc.flowQp_Diff_Pcnt:.{1}f}",
                    "+25% to -15%",
                ],
                [
                    twp.fill("Flow Volume", 10),
                    f"{aLoc.flowVol_Diff_Pcnt:.{1}f}",
                    "+20% to -10%",
                ],
            ]

            cell_colours = [
                ["#71004b", "#71004b", "#71004b"],
                ["#ffffff", "#ffffff", hexGreen if (aLoc.flowNSE > 0.5) else hexRed],
                [
                    "#ffffff",
                    "#ffffff",
                    hexGreen if (0.5 > aLoc.flowTp_Diff_Hrs > -0.5) else hexRed,
                ],
                [
                    "#ffffff",
                    "#ffffff",
                    hexGreen if (25 > aLoc.flowQp_Diff_Pcnt > -15) else hexRed,
                ],
                [
                    "#ffffff",
                    "#ffffff",
                    hexGreen if (20 > aLoc.flowVol_Diff_Pcnt > -10) else hexRed,
                ],
            ]

        col_widths = [0.33, 0.28, 0.39]
        myBbx = [0.05, 0.35, 0.15, 0.64]

        testTb = table(
            self.plot_axis_flow,
            cellText=table_data,
            cellColours=cell_colours,
            cellLoc="center",
            colWidths=col_widths,
            rowLoc="center",
            colLoc="center",
            bbox=myBbx,
        )
        testTb.auto_set_font_size(False)
        testTb.set_fontsize(6)
        testTb.set_zorder(100)
        for i in range(len(table_data[0])):
            txt = testTb[(0, i)].get_text()
            txt.set_color("white")
            txt.set_fontweight("bold")

    def createUDGDepthTable(self, aLoc: icmTraceLocation):

        hexGreen = "#47d655"
        hexRed = "#e87676"

        if aLoc.isCritical:
            if aLoc.isSurcharged:
                table_data = [
                    [
                        twp.fill("Parameter", 10),
                        twp.fill("Actual Value", 10),
                        twp.fill("Critical Location", 10),
                    ],
                    [
                        twp.fill("Time of Peaks", 10),
                        f"{aLoc.depthTp_Diff_Hrs:.{2}f}",
                        "±0.5Hr",
                    ],
                    [
                        twp.fill("Peak Depth (Surch)", 10),
                        f"{aLoc.depthDp_Diff:.{2}f}",
                        "±0.1m",
                    ],
                ]

                cell_colours = [
                    ["#71004b", "#71004b", "#71004b"],
                    [
                        "#ffffff",
                        "#ffffff",
                        hexGreen if (0.5 > aLoc.depthTp_Diff_Hrs > -0.5) else hexRed,
                    ],
                    [
                        "#ffffff",
                        "#ffffff",
                        hexGreen if (0.1 > aLoc.depthDp_Diff > -0.1) else hexRed,
                    ],
                ]

            else:
                table_data = [
                    [
                        twp.fill("Parameter", 10),
                        twp.fill("Actual Value", 10),
                        twp.fill("Critical Location", 10),
                    ],
                    [
                        twp.fill("Time of Peaks", 10),
                        f"{aLoc.depthTp_Diff_Hrs:.{2}f}",
                        "±0.5Hr",
                    ],
                    [twp.fill("Peak Depth", 10), f"{aLoc.depthDp_Diff:.{2}f}", "±0.1m"],
                ]

                cell_colours = [
                    ["#71004b", "#71004b", "#71004b"],
                    [
                        "#ffffff",
                        "#ffffff",
                        hexGreen if (0.5 > aLoc.depthTp_Diff_Hrs > -0.5) else hexRed,
                    ],
                    [
                        "#ffffff",
                        "#ffffff",
                        hexGreen if (0.1 > aLoc.depthDp_Diff > -0.1) else hexRed,
                    ],
                ]

        else:
            if aLoc.isSurcharged:
                table_data = [
                    [
                        twp.fill("Parameter", 10),
                        twp.fill("Actual Value", 10),
                        twp.fill("General Location", 10),
                    ],
                    [
                        twp.fill("Time of Peaks", 10),
                        f"{aLoc.depthTp_Diff_Hrs:.{2}f}",
                        "±0.5Hr",
                    ],
                    [
                        twp.fill("Peak Depth (Surch)", 10),
                        f"{aLoc.depthDp_Diff:.{2}f}",
                        "+0.5m to -0.1m",
                    ],
                ]

                cell_colours = [
                    ["#71004b", "#71004b", "#71004b"],
                    [
                        "#ffffff",
                        "#ffffff",
                        hexGreen if (0.5 > aLoc.depthTp_Diff_Hrs > -0.5) else hexRed,
                    ],
                    [
                        "#ffffff",
                        "#ffffff",
                        hexGreen if (0.5 > aLoc.depthDp_Diff > -0.1) else hexRed,
                    ],
                ]

            else:

                table_data = [
                    [
                        twp.fill("Parameter", 10),
                        twp.fill("Actual Value", 10),
                        twp.fill("General Location", 10),
                    ],
                    [
                        twp.fill("Time of Peaks", 10),
                        f"{aLoc.depthTp_Diff_Hrs:.{2}f}",
                        "±0.5Hr",
                    ],
                    [
                        twp.fill("Peak Depth", 10),
                        f"{aLoc.depthDp_Diff:.{2}f}m/{aLoc.depthDp_Diff_Pcnt:.{0}f}%",
                        "±0.1m or ±10%",
                    ],
                ]

                cell_colours = [
                    ["#71004b", "#71004b", "#71004b"],
                    [
                        "#ffffff",
                        "#ffffff",
                        hexGreen if (0.5 > aLoc.depthTp_Diff_Hrs > -0.5) else hexRed,
                    ],
                    [
                        "#ffffff",
                        "#ffffff",
                        (
                            hexGreen
                            if (
                                (10 > aLoc.depthDp_Diff_Pcnt > -10)
                                and (0.1 > aLoc.depthDp_Diff > -0.1)
                            )
                            else hexRed
                        ),
                    ],
                ]

        col_widths = [0.33, 0.28, 0.39]
        # myBbx = [0.05, 0.35, 0.15, 0.64]
        myBbx = [0.05, 0.60, 0.15, 0.39]

        testTb = table(
            self.plot_axis_depth,
            cellText=table_data,
            cellColours=cell_colours,
            cellLoc="center",
            colWidths=col_widths,
            rowLoc="center",
            colLoc="center",
            bbox=myBbx,
        )
        testTb.auto_set_font_size(False)
        testTb.set_fontsize(6)
        testTb.set_zorder(100)
        for i in range(len(table_data[0])):
            txt = testTb[(0, i)].get_text()
            txt.set_color("white")
            txt.set_fontweight("bold")

    def updateCanvas(self):

        self.main_window_plot_widget.event_connections.append(self.main_window_plot_widget.figure.canvas.mpl_connect("pick_event", self.onPick))
        self.main_window_plot_widget.showToolbar(not self.isBlank)
        self.main_window_plot_widget.toolbar.lockNavigation(False)

    def onPlotXlimsChange(self, event_ax):

        xmin, xmax = mpl_dates.num2date(event_ax.get_xlim())

        self.update_plotStats(xmin, xmax)

    def onPick(self, event):

        legline = event.artist

        origline = self.c_flow_legend_lines[legline]
        vis = not origline.get_visible()
        origline.set_visible(vis)

        origline = self.c_depth_legend_lines[legline]
        vis = not origline.get_visible()
        origline.set_visible(vis)

        origline = self.c_vel_legend_lines[legline]
        vis = not origline.get_visible()
        origline.set_visible(vis)
        # Change the alpha on the line in the legend so we can see what lines have been toggled
        if vis:
            legline.set_alpha(1.0)
        else:
            legline.set_alpha(0.2)

        self.main_window_plot_widget.figure.canvas.draw()

    def update_plotStats(self, xMin, xMax):

        rounded_xmax_python_datetime = xMax
        rounded_xmax_python_datetime += timedelta(minutes=0.5)
        rounded_xmax_python_datetime -= timedelta(
            minutes=rounded_xmax_python_datetime.minute % 2,
            seconds=rounded_xmax_python_datetime.second,
            microseconds=rounded_xmax_python_datetime.microsecond,
        )

        rounded_xmin_python_datetime = xMin
        rounded_xmin_python_datetime += timedelta(minutes=0.5)
        rounded_xmin_python_datetime -= timedelta(
            minutes=rounded_xmin_python_datetime.minute % 2,
            seconds=rounded_xmin_python_datetime.second,
            microseconds=rounded_xmin_python_datetime.microsecond,
        )

        self.plottedICMTrace.setPlotDateLimits(
            rounded_xmin_python_datetime, rounded_xmax_python_datetime
        )
        self.refreshTable()


class graph_fsm_classification:

    def __init__(
        self,
        a_pw: PlotWidget,
        a_project: fsmProject,
        interim_id: int,
        footer_text: str = "",
    ):

        # self.dfTable = dfTable
        self.interim_id: int = interim_id
        self.a_project: fsmProject = a_project
        self.current_plot_type = "FM"
        self.footer_text: str = footer_text

        self.a_plot_widget: PlotWidget = a_pw
        self.fig_width = self.a_plot_widget.figure.get_figwidth()
        self.fig_height = self.a_plot_widget.figure.get_figheight()

    def update_plot(self):

        self.a_plot_widget.figure.clear()

        dfLegend = get_classification_legend_dataframe()
        color_mapping = get_classification_color_mapping()

        # date_delta = self.a_project.dict_fsm_interims[self.interim_id].interim_end_date - self.a_project.survey_start_date
        # no_of_weeks = date_delta.days / 7

        # if no_of_weeks <= 5:
        #     fig_width = 14.1
        # else:
        #     fig_width = (((14.1 - 2) * no_of_weeks) / 5) + 2

        # fig_height = (fig_width * 10) / 14.1

        # tempPW = PlotWidget(self, False, (fig_width, fig_height), dpi=100)

        col_list = ["RowNames"]
        week_list = ["Week"]
        days_list = ["Day"]
        dates_list = ["Date"]

        fm_data_dict: Dict[str, list] = {}
        dm_data_dict: Dict[str, list] = {}
        rg_data_dict: Dict[str, list] = {}

        fm_data_list = []
        dm_data_list = []
        rg_data_list = []
        for a_int_rev in self.a_project.dict_fsm_interim_reviews.values():
            if a_int_rev.interim_id == self.interim_id:
                if (
                    self.a_project.dict_fsm_installs[a_int_rev.install_id].install_type
                    == "Flow Monitor"
                ):
                    fm_data_list.append(
                        [
                            self.a_project.dict_fsm_installs[
                                a_int_rev.install_id
                            ].client_ref
                        ]
                        + self.a_project.get_class_list(
                            self.interim_id, a_int_rev.install_id
                        )
                    )
                elif (
                    self.a_project.dict_fsm_installs[a_int_rev.install_id].install_type
                    == "Depth Monitor"
                ):
                    dm_data_list.append(
                        [
                            self.a_project.dict_fsm_installs[
                                a_int_rev.install_id
                            ].client_ref
                        ]
                        + self.a_project.get_class_list(
                            self.interim_id, a_int_rev.install_id
                        )
                    )
                elif (
                    self.a_project.dict_fsm_installs[a_int_rev.install_id].install_type
                    == "Rain Gauge"
                ):
                    rg_data_list.append(
                        [
                            self.a_project.dict_fsm_installs[
                                a_int_rev.install_id
                            ].client_ref
                        ]
                        + self.a_project.get_class_list(
                            self.interim_id, a_int_rev.install_id
                        )
                    )

        for a_interim in self.a_project.dict_fsm_interims.values():
            if a_interim.interim_id <= self.interim_id:
                col_list.extend(self.a_project.get_column_list(a_interim.interim_id))
                week_list.extend(self.a_project.get_week_list(a_interim.interim_id))
                days_list.extend(self.a_project.get_day_list(a_interim.interim_id))
                dates_list.extend(self.a_project.get_date_list(a_interim.interim_id))

                for a_int_rev in self.a_project.dict_fsm_interim_reviews.values():
                    if a_int_rev.interim_id == a_interim.interim_id:
                        if (
                            self.a_project.dict_fsm_installs[
                                a_int_rev.install_id
                            ].install_type
                            == "Flow Monitor"
                        ):
                            current_list = fm_data_dict.get(
                                self.a_project.dict_fsm_installs[
                                    a_int_rev.install_id
                                ].client_ref,
                                [],
                            )
                            current_list.extend(
                                self.a_project.get_class_list(
                                    a_interim.interim_id, a_int_rev.install_id
                                )
                            )
                            fm_data_dict[
                                self.a_project.dict_fsm_installs[
                                    a_int_rev.install_id
                                ].client_ref
                            ] = current_list
                        elif (
                            self.a_project.dict_fsm_installs[
                                a_int_rev.install_id
                            ].install_type
                            == "Depth Monitor"
                        ):
                            current_list = dm_data_dict.get(
                                self.a_project.dict_fsm_installs[
                                    a_int_rev.install_id
                                ].client_ref,
                                [],
                            )
                            current_list.extend(
                                self.a_project.get_class_list(
                                    a_interim.interim_id, a_int_rev.install_id
                                )
                            )
                            dm_data_dict[
                                self.a_project.dict_fsm_installs[
                                    a_int_rev.install_id
                                ].client_ref
                            ] = current_list
                        elif (
                            self.a_project.dict_fsm_installs[
                                a_int_rev.install_id
                            ].install_type
                            == "Rain Gauge"
                        ):
                            current_list = rg_data_dict.get(
                                self.a_project.dict_fsm_installs[
                                    a_int_rev.install_id
                                ].client_ref,
                                [],
                            )
                            current_list.extend(
                                self.a_project.get_class_list(
                                    a_interim.interim_id, a_int_rev.install_id
                                )
                            )
                            rg_data_dict[
                                self.a_project.dict_fsm_installs[
                                    a_int_rev.install_id
                                ].client_ref
                            ] = current_list

        fm_data_list = []
        for a_id, a_list in fm_data_dict.items():
            fm_data_list.append([a_id] + a_list)
        dm_data_list = []
        for a_id, a_list in dm_data_dict.items():
            dm_data_list.append([a_id] + a_list)
        rg_data_list = []
        for a_id, a_list in rg_data_dict.items():
            rg_data_list.append([a_id] + a_list)

        fm_data_list.sort(key=lambda x: x[0])
        dm_data_list.sort(key=lambda x: x[0])
        rg_data_list.sort(key=lambda x: x[0])

        tableData = [col_list, week_list, days_list, dates_list]

        # Extend tableData with sorted data lists
        tableData.extend(fm_data_list)
        tableData.extend(dm_data_list)
        tableData.extend(rg_data_list)

        header = tableData[0]
        data_rows = tableData[1:]
        # Create the DataFrame
        dfTable = pd.DataFrame(data_rows, columns=header)
        dfTable.set_index("RowNames", inplace=True)
        # Change day names to single character
        dfTable.iloc[1] = dfTable.iloc[1].str[0]

        leg_col_0_width = 30
        leg_col_1_width = 140
        leg_col_2_width = 5

        tab_col_0_width = 80
        tab_col_1_width = 30

        row_height = 30

        # row_header_factor = 2
        date_row_factor = 5
        date_row_offset = 0

        my_fontsize = 8

        padding = 2

        legend_total_width = 6 * (leg_col_0_width + leg_col_1_width + leg_col_2_width)
        legend_total_height = 3 * row_height

        # legend_fig_height = fig_width / (legend_total_width / legend_total_height)
        # table_fig_height = fig_height - legend_fig_height

        table_row_count = dfTable.shape[0]
        table_col_count = dfTable.shape[1]

        table_total_width = tab_col_0_width + (table_col_count * tab_col_1_width)
        table_total_height = ((table_row_count - 1) * row_height) + (
            1 * date_row_factor * row_height
        )
        # print(table_total_height)

        # Plotting the tables using matplotlib
        # fig, (plot_axis_legend, plot_axis_table) = plt.subplots(2, sharex=False, gridspec_kw={'height_ratios': [legend_total_height, table_total_height]}, figsize=(fig_width, fig_height))
        (plot_axis_legend, plot_axis_table) = self.a_plot_widget.figure.subplots(
            2, sharex=False
        )

        plot_axis_legend.xaxis.set_visible(False)
        plot_axis_legend.yaxis.set_visible(False)
        plot_axis_legend.set_frame_on(False)
        plot_axis_legend.set_autoscale_on(False)

        plot_axis_table.xaxis.set_visible(False)
        plot_axis_table.yaxis.set_visible(False)
        plot_axis_table.set_frame_on(False)
        plot_axis_table.set_autoscale_on(False)

        # Create the legend table
        for row in range(dfLegend.shape[0]):
            for col in range(0, dfLegend.shape[1], 3):
                code = dfLegend.iloc[row, col]
                description = dfLegend.iloc[row, col + 1]
                if code and description:
                    my_y = legend_total_height - ((row + 1) * row_height)
                    x_offset = math.floor(col / 3) * (
                        leg_col_0_width + leg_col_1_width + leg_col_2_width
                    )
                    my_x = x_offset
                    text_color = (
                        "#ffffff"
                        if color_mapping.get(code, "#ffffff") == "#000000"
                        else "#000000"
                    )

                    rect = mpl_patches.Rectangle(
                        (my_x, my_y),
                        leg_col_0_width,
                        row_height,
                        edgecolor="black",
                        facecolor=color_mapping.get(code, "white"),
                        linewidth=1,
                    )
                    plot_axis_legend.add_patch(rect)
                    plot_axis_legend.text(
                        my_x + 15,
                        my_y + 15,
                        code,
                        va="center",
                        ha="center",
                        fontsize=my_fontsize,
                        fontweight="bold",
                        color=text_color,
                    )

                    my_x = my_x + leg_col_0_width
                    rect = mpl_patches.Rectangle(
                        (my_x, my_y),
                        leg_col_1_width,
                        row_height,
                        edgecolor="black",
                        facecolor="none",
                        linewidth=0,
                    )
                    plot_axis_legend.add_patch(rect)
                    plot_axis_legend.text(
                        my_x + 15,
                        my_y + 15,
                        description,
                        va="center",
                        ha="left",
                        fontsize=my_fontsize,
                        fontweight="normal",
                        color="black",
                    )

                    my_x = my_x + leg_col_1_width
                    rect = mpl_patches.Rectangle(
                        (my_x, my_y),
                        leg_col_2_width,
                        row_height,
                        edgecolor="black",
                        facecolor="none",
                        linewidth=0,
                    )
                    plot_axis_legend.add_patch(rect)

        # Set the limits of the plot to better visualize the rectangle
        plot_axis_legend.set_box_aspect(legend_total_height / legend_total_width)
        plot_axis_legend.set_xlim(-padding, legend_total_width + padding)
        plot_axis_legend.set_ylim(-padding, legend_total_height + padding)

        # Create the data table
        for row in range(dfTable.shape[0]):
            row_name = dfTable.index[row]
            my_x = 0
            if row == 2:
                table_row_height = row_height * date_row_factor
                date_row_offset = (row_height * date_row_factor) - row_height
            else:
                table_row_height = row_height

            my_y = table_total_height - (((row + 1) * row_height) + date_row_offset)
            #     print(my_y)
            rect = mpl_patches.Rectangle(
                (my_x, my_y),
                tab_col_0_width,
                table_row_height,
                edgecolor="black",
                facecolor="white",
                linewidth=1,
            )
            plot_axis_table.add_patch(rect)
            plot_axis_table.text(
                my_x,
                my_y + (table_row_height / 2),
                row_name,
                va="center",
                ha="left",
                fontsize=my_fontsize,
                fontweight="bold",
                color="black",
            )

            if row == 0:
                "Create Week Header"
                for col in range(0, dfTable.shape[1], 7):
                    my_x = tab_col_0_width + ((col / 7) * (tab_col_1_width * 7))
                    rect = mpl_patches.Rectangle(
                        (my_x, my_y),
                        (tab_col_1_width * 7),
                        table_row_height,
                        edgecolor="black",
                        facecolor="white",
                        linewidth=1,
                    )
                    plot_axis_table.add_patch(rect)
                    plot_axis_table.text(
                        my_x + ((tab_col_1_width * 7) / 2),
                        my_y + (table_row_height / 2),
                        dfTable.iloc[row, col],
                        va="center",
                        ha="center",
                        fontsize=my_fontsize,
                        fontweight="bold",
                        color="black",
                    )

            elif row == 1:
                "Create Day Header"
                for col in range(dfTable.shape[1]):
                    my_x = tab_col_0_width + (col * tab_col_1_width)
                    rect = mpl_patches.Rectangle(
                        (my_x, my_y),
                        tab_col_1_width,
                        table_row_height,
                        edgecolor="black",
                        facecolor="white",
                        linewidth=1,
                    )
                    plot_axis_table.add_patch(rect)
                    plot_axis_table.text(
                        my_x + (tab_col_1_width / 2),
                        my_y + (table_row_height / 2),
                        dfTable.iloc[row, col],
                        va="center",
                        ha="center",
                        fontsize=my_fontsize,
                        fontweight="bold",
                        color="black",
                    )

            elif row == 2:
                "Create Date Header"
                for col in range(dfTable.shape[1]):
                    my_x = tab_col_0_width + (col * tab_col_1_width)
                    rect = mpl_patches.Rectangle(
                        (my_x, my_y),
                        tab_col_1_width,
                        table_row_height,
                        edgecolor="black",
                        facecolor="white",
                        linewidth=1,
                    )
                    plot_axis_table.add_patch(rect)
                    plot_axis_table.text(
                        my_x + (tab_col_1_width / 2),
                        my_y + (table_row_height / 2),
                        dfTable.iloc[row, col],
                        va="center",
                        ha="center",
                        fontsize=my_fontsize,
                        fontweight="bold",
                        color="black",
                        rotation="vertical",
                    )
            else:
                "Create data row"
                for col in range(dfTable.shape[1]):
                    my_x = tab_col_0_width + (col * tab_col_1_width)
                    cell_color = color_mapping[dfTable.iloc[row, col]]
                    rect = mpl_patches.Rectangle(
                        (my_x, my_y),
                        tab_col_1_width,
                        table_row_height,
                        edgecolor="black",
                        facecolor=cell_color,
                        linewidth=1,
                    )
                    plot_axis_table.add_patch(rect)
                    text_color = "#000000"
                    if cell_color == "#000000":  # If background color is black
                        text_color = "#FFFFFF"
                    plot_axis_table.text(
                        my_x + (tab_col_1_width / 2),
                        my_y + (table_row_height / 2),
                        dfTable.iloc[row, col],
                        va="center",
                        ha="center",
                        fontsize=my_fontsize,
                        fontweight="bold",
                        color=text_color,
                    )

        # Set the limits of the plot to better visualize the rectangle
        plot_axis_table.set_box_aspect(table_total_height / table_total_width)
        plot_axis_table.set_xlim(-padding, table_total_width + padding)
        plot_axis_table.set_ylim(-padding, table_total_height + padding)

        # Add header and footer
        self.a_plot_widget.figure.text(
            0.95, 0.95, f"Data Classification Overview", ha="right", fontsize=16
        )
        self.a_plot_widget.figure.text(
            0.5, 0.02, self.footer_text, ha="center", fontsize=12
        )

        # Add an image to the header
        im = Image.open(resource_path(f"resources/{rps_or_tt}_logo_report.png"))
        aspect_ratio = im.width / im.height
        desired_height_inch = 0.5
        desired_width_inch = desired_height_inch * aspect_ratio
        fig_dpi = self.a_plot_widget.figure.get_dpi()
        desired_width_px = int(desired_width_inch * fig_dpi)
        desired_height_px = int(desired_height_inch * fig_dpi)
        # Resize the image to fit in the header
        im = im.resize((desired_width_px, desired_height_px))
        imagebox = OffsetImage(im)
        ab = AnnotationBbox(
            imagebox, (0.1, 0.95), frameon=False, xycoords="figure fraction"
        )
        self.a_plot_widget.figure.add_artist(ab)

        # # Adjust layout
        # self.a_plot_widget.figure.subplots_adjust(left=0.15, right=0.85, bottom=0.15, top=0.85)

        # Show plot
        plt.show()


# class graph_fsm_classification():

#     def __init__(self, a_pw: PlotWidget = None, dfTable: pd.DataFrame = None):

#         self.dfTable = dfTable
#         self.current_plot_type = 'FM'

#         self.a_plot_widget: PlotWidget = a_pw
#         self.fig_width = self.a_plot_widget.figure.get_figwidth()
#         self.fig_height = self.a_plot_widget.figure.get_figheight()

#     def update_plot(self):

#         self.a_plot_widget.figure.clear()

#         dfLegend = get_classification_legend_dataframe()
#         color_mapping = get_classification_color_mapping()

#         col_0_width = 30
#         col_1_width = 140
#         col_2_width = 5
#         row_height = 30

#         row_header_factor = 2
#         date_row_factor = 3
#         date_row_offset = 0

#         my_fontsize = 10

#         padding = 2

#         legend_total_width = 6 * (col_0_width + col_1_width + col_2_width)
#         legend_total_height = 3 * row_height

#         legend_fig_height = self.fig_width / (legend_total_width / legend_total_height)
#         table_fig_height = self.fig_height - legend_fig_height

#         table_total_width = legend_total_width
#         table_total_height = table_total_width / (self.fig_width / table_fig_height)

#         col_width = table_total_width / (self.dfTable.shape[1] + row_header_factor)

#         # Plotting the tables using matplotlib
#         (self.plot_axis_legend, self.plot_axis_table) = self.a_plot_widget.figure.subplots(2, sharex=False, gridspec_kw={'height_ratios': [legend_fig_height, table_fig_height]})

#         self.plot_axis_legend.xaxis.set_visible(False)
#         self.plot_axis_legend.yaxis.set_visible(False)
#         self.plot_axis_legend.set_frame_on(False)
#         self.plot_axis_legend.set_autoscale_on(False)

#         self.plot_axis_table.xaxis.set_visible(False)
#         self.plot_axis_table.yaxis.set_visible(False)
#         self.plot_axis_table.set_frame_on(False)
#         self.plot_axis_table.set_autoscale_on(False)

#         # Create the legend table
#         for row in range(dfLegend.shape[0]):
#             for col in range(0, dfLegend.shape[1], 3):
#                 code = dfLegend.iloc[row, col]
#                 description = dfLegend.iloc[row, col+1]
#                 if code and description:
#                     my_y = legend_total_height - ((row + 1) * row_height)
#                     x_offset = math.floor(col/3) * (col_0_width + col_1_width + col_2_width)
#                     my_x = x_offset
#                     text_color = '#ffffff' if color_mapping.get(code, '#ffffff') == '#000000' else '#000000'

#                     rect = mpl_patches.Rectangle((my_x, my_y), col_0_width, row_height, edgecolor='black', facecolor=color_mapping.get(code, 'white'), linewidth=1)
#                     self.plot_axis_legend.add_patch(rect)
#                     self.plot_axis_legend.text(my_x + 15, my_y + 15, code, va='center', ha='center', fontsize=my_fontsize, fontweight='bold', color=text_color)

#                     my_x = my_x + col_0_width
#                     rect = mpl_patches.Rectangle((my_x, my_y), col_1_width, row_height, edgecolor='black', facecolor='none', linewidth=0)
#                     self.plot_axis_legend.add_patch(rect)
#                     self.plot_axis_legend.text(my_x + 15, my_y + 15, description, va='center', ha='left', fontsize=my_fontsize, fontweight='normal', color='black')

#                     my_x = my_x + col_1_width
#                     rect = mpl_patches.Rectangle((my_x, my_y), col_2_width, row_height, edgecolor='black', facecolor='none', linewidth=0)
#                     self.plot_axis_legend.add_patch(rect)

#         # Set the limits of the plot to better visualize the rectangle
#         self.plot_axis_legend.set_box_aspect(legend_total_height/legend_total_width)
#         self.plot_axis_legend.set_xlim(-padding, legend_total_width + padding)
#         self.plot_axis_legend.set_ylim(-padding, legend_total_height + padding)

#         # Create the data table
#         for row in range(self.dfTable.shape[0]):
#             row_name = self.dfTable.index[row]
#             my_x = 0
#             if row == 2:
#                 table_row_height = row_height * date_row_factor
#                 date_row_offset = (row_height * date_row_factor) - row_height
#             else:
#                 table_row_height = row_height

#             my_y = table_total_height - (((row + 1) * row_height) + date_row_offset)
#             rect = mpl_patches.Rectangle((my_x, my_y), col_width * row_header_factor, table_row_height,
#                                          edgecolor='black', facecolor='white', linewidth=1)
#             self.plot_axis_table.add_patch(rect)
#             self.plot_axis_table.text(my_x, my_y + (table_row_height / 2), row_name, va='center', ha='left', fontsize=my_fontsize, fontweight='bold', color='black')

#             if row == 0:
#                 'Create Week Header'
#                 for col in range(0, self.dfTable.shape[1], 7):
#                     my_x = (col_width * row_header_factor) + ((col / 7) * (col_width * 7))
#                     rect = mpl_patches.Rectangle((my_x, my_y), (col_width * 7), table_row_height, edgecolor='black', facecolor='white', linewidth=1)
#                     self.plot_axis_table.add_patch(rect)
#                     self.plot_axis_table.text(my_x + ((col_width * 7) / 2), my_y + (table_row_height / 2), self.dfTable.iloc[row, col], va='center', ha='center', fontsize=my_fontsize, fontweight='bold', color='black')

#             elif row == 1:
#                 'Create Day Header'
#                 for col in range(self.dfTable.shape[1]):
#                     my_x = (col_width * row_header_factor) + (col * col_width)
#                     rect = mpl_patches.Rectangle((my_x, my_y), col_width, table_row_height, edgecolor='black', facecolor='white', linewidth=1)
#                     self.plot_axis_table.add_patch(rect)
#                     self.plot_axis_table.text(my_x + (col_width / 2), my_y + (table_row_height / 2), self.dfTable.iloc[row, col], va='center', ha='center', fontsize=my_fontsize, fontweight='bold', color='black')

#             elif row == 2:
#                 'Create Date Header'
#                 for col in range(self.dfTable.shape[1]):
#                     my_x = (col_width * row_header_factor) + (col * col_width)
#                     rect = mpl_patches.Rectangle((my_x, my_y), col_width, table_row_height, edgecolor='black', facecolor='white', linewidth=1)
#                     self.plot_axis_table.add_patch(rect)
#                     self.plot_axis_table.text(my_x + (col_width / 2), my_y + (table_row_height / 2), self.dfTable.iloc[row, col], va='center', ha='center', fontsize=my_fontsize, fontweight='bold', color='black', rotation='vertical')
#             else:
#                 'Create data row'
#                 for col in range(self.dfTable.shape[1]):
#                     my_x = (col_width * row_header_factor) + (col * col_width)
#                     cell_color = color_mapping[self.dfTable.iloc[row, col]]
#                     rect = mpl_patches.Rectangle((my_x, my_y), col_width, table_row_height, edgecolor='black', facecolor=cell_color, linewidth=1)
#                     self.plot_axis_table.add_patch(rect)
#                     text_color = '#000000'
#                     if cell_color == '#000000':  # If background color is black
#                         text_color = '#FFFFFF'
#                     self.plot_axis_table.text(my_x + (col_width / 2), my_y + (table_row_height / 2), self.dfTable.iloc[row, col], va='center', ha='center', fontsize=my_fontsize, fontweight='bold', color=text_color)

#         # Set the limits of the plot to better visualize the rectangle
#         self.plot_axis_table.set_box_aspect(table_total_height/table_total_width)
#         self.plot_axis_table.set_xlim(-padding, table_total_width + padding)
#         self.plot_axis_table.set_ylim(-padding, table_total_height + padding)

#         self.a_plot_widget.figure.tight_layout()

#         # Display the tables
#         plt.show()


class graph_fsm_fm_install_summary:

    def __init__(
        self,
        a_pw: PlotWidget,
        a_project: fsmProject,
        interim_id: int,
        footer_text: str = "",
    ):

        # self.dfTable = dfTable
        self.interim_id: int = interim_id
        self.a_project: fsmProject = a_project
        self.footer_text: str = footer_text
        self.a_plot_widget: PlotWidget = a_pw
        self.fig_width = self.a_plot_widget.figure.get_figwidth()
        self.fig_height = self.a_plot_widget.figure.get_figheight()

    def update_plot(self):

        self.a_plot_widget.figure.clear()

        # CREATE INPUT DATA
        data = []
        fm_data = []
        dm_data = []
        for a_int_rev in self.a_project.dict_fsm_interim_reviews.values():
            if a_int_rev.interim_id == self.interim_id:
                a_inst = self.a_project.dict_fsm_installs[a_int_rev.install_id]
                if a_inst.install_type != "Rain Gauge":
                    a_site = self.a_project.dict_fsm_sites[a_inst.install_site_id]
                    a_mon = self.a_project.dict_fsm_monitors[
                        a_inst.install_monitor_asset_id
                    ]
                    data_list = []
                    data_list.append(a_inst.client_ref)
                    data_list.append(a_site.address)
                    data_list.append(a_inst.fm_pipe_letter)
                    data_list.append(str(a_inst.fm_pipe_height_mm))
                    data_list.append(str(a_inst.fm_pipe_width_mm))
                    data_list.append(
                        self.a_project.get_pipe_shape_code(a_inst.fm_pipe_shape)
                    )
                    data_list.append(str(a_inst.fm_pipe_depth_to_invert_mm))
                    data_list.append(a_mon.monitor_sub_type[0])
                    data_list.append(a_site.mh_ref)
                    data_list.append(a_inst.install_date.strftime("%d/%m/%Y"))
                    if a_inst.remove_date > a_inst.install_date:
                        data_list.append(a_inst.remove_date.strftime("%d/%m/%Y"))
                        date_delta = a_inst.remove_date - a_inst.install_date
                        no_of_weeks = math.floor(date_delta.days / 7)
                        no_of_days = math.floor((date_delta.days - (no_of_weeks * 7)))
                        data_list.append(str(no_of_weeks))
                        data_list.append(str(no_of_days))
                    elif (
                        self.a_project.dict_fsm_interims[
                            self.interim_id
                        ].interim_end_date
                        > a_inst.install_date
                    ):
                        data_list.append("")
                        date_delta = (
                            self.a_project.dict_fsm_interims[
                                self.interim_id
                            ].interim_end_date
                            - a_inst.install_date
                        )
                        no_of_weeks = math.floor(date_delta.days / 7)
                        no_of_days = math.floor((date_delta.days - (no_of_weeks * 7)))
                        data_list.append(str(no_of_weeks))
                        data_list.append(str(no_of_days))
                    if a_inst.install_type == "Flow Monitor":
                        fm_data.append(data_list)
                    else:
                        dm_data.append(data_list)

        fm_data.sort(key=lambda x: x[0])
        dm_data.sort(key=lambda x: x[0])
        data.extend(fm_data)
        data.extend(dm_data)
        dfTable = pd.DataFrame(
            data,
            columns=[
                "Monitor No.",
                "Location",
                "Pipe",
                "Height (mm)",
                "Width (mm)",
                "Shape",
                "Depth (mm)",
                "Type",
                "MH Ref.",
                "Installed Date",
                "Removed Date",
                "Weeks",
                "Days",
            ],
        )

        col_0_width = 66
        col_1_width = 420
        col_2_width = 22
        col_3_width = 44
        col_4_width = 44
        col_5_width = 22
        col_6_width = 44
        col_7_width = 22
        col_8_width = 88
        col_9_width = 88
        col_10_width = 88
        col_11_width = 33
        col_12_width = 33
        row_height = 25
        header_row_height = row_height * 2
        install_row_height = row_height

        padding = 2
        a_font_size = 10

        total_width = (
            col_0_width
            + col_1_width
            + col_2_width
            + col_3_width
            + col_4_width
            + col_5_width
            + col_6_width
            + col_7_width
            + col_8_width
            + col_9_width
            + col_10_width
            + col_11_width
            + col_12_width
        )
        total_height = (
            install_row_height + header_row_height + (row_height * (dfTable.shape[0]))
        )  # including header row

        # Plotting the table using matplotlib
        self.plot_axis = self.a_plot_widget.figure.add_subplot(111)

        self.plot_axis.xaxis.set_visible(False)
        self.plot_axis.yaxis.set_visible(False)
        self.plot_axis.set_frame_on(False)
        self.plot_axis.set_autoscale_on(False)

        column_widths = [
            col_0_width,
            col_1_width,
            col_2_width,
            col_3_width,
            col_4_width,
            col_5_width,
            col_6_width,
            col_7_width,
            col_8_width,
            col_9_width,
            col_10_width,
            col_11_width,
            col_12_width,
        ]

        # Create the table header
        headers = [
            "Monitor\nNo.",
            "Location",
            "Pipe",
            "Height\n(mm)",
            "Width\n(mm)",
            "Shape",
            "Depth\n(mm)",
            "Type",
            "MH Ref.",
            "Installed\nDate",
            "Removed\nDate",
            "Weeks",
            "Days",
        ]

        my_y = total_height - (header_row_height + install_row_height)
        my_x = 0

        for idx, header in enumerate(headers):
            if header == "Weeks":
                temp_y = total_height - install_row_height
                rect = mpl_patches.Rectangle(
                    (my_x, temp_y),
                    (column_widths[idx] + column_widths[idx + 1]),
                    install_row_height,
                    edgecolor="black",
                    facecolor="grey",
                    linewidth=1,
                )
                self.plot_axis.add_patch(rect)
                self.plot_axis.text(
                    my_x + ((column_widths[idx] + column_widths[idx + 1]) / 2),
                    temp_y + install_row_height / 2,
                    "Installed",
                    va="center",
                    ha="center",
                    fontsize=a_font_size,
                    fontweight="bold",
                    color="black",
                )
            rect = mpl_patches.Rectangle(
                (my_x, my_y),
                column_widths[idx],
                header_row_height,
                edgecolor="black",
                facecolor="grey",
                linewidth=1,
            )
            self.plot_axis.add_patch(rect)
            if header in ["Pipe", "Shape", "Type", "Weeks", "Days"]:
                self.plot_axis.text(
                    my_x + column_widths[idx] / 2,
                    my_y + header_row_height / 2,
                    header,
                    va="center",
                    ha="center",
                    fontsize=a_font_size,
                    fontweight="bold",
                    color="black",
                    rotation="vertical",
                )
            else:
                self.plot_axis.text(
                    my_x + column_widths[idx] / 2,
                    my_y + header_row_height / 2,
                    header,
                    va="center",
                    ha="center",
                    fontsize=a_font_size,
                    fontweight="bold",
                    color="black",
                )
            my_x += column_widths[idx]

        # Create the data table
        for row in range(dfTable.shape[0]):
            my_y = total_height - (
                install_row_height + header_row_height + ((row + 1) * row_height)
            )
            my_x = 0
            for col in range(dfTable.shape[1]):
                rect = mpl_patches.Rectangle(
                    (my_x, my_y),
                    column_widths[col],
                    row_height,
                    edgecolor="black",
                    facecolor="white",
                    linewidth=1,
                )
                self.plot_axis.add_patch(rect)
                self.plot_axis.text(
                    my_x + column_widths[col] / 2,
                    my_y + row_height / 2,
                    dfTable.iloc[row, col],
                    va="center",
                    ha="center",
                    fontsize=a_font_size,
                    fontweight="normal",
                    color="black",
                )
                my_x += column_widths[col]

        # Set the limits of the plot to better visualize the rectangle
        self.plot_axis.set_box_aspect(total_height / total_width)
        self.plot_axis.set_xlim(-padding, total_width + padding)
        self.plot_axis.set_ylim(-padding, total_height + padding)

        # Add header and footer
        self.a_plot_widget.figure.text(
            0.95,
            0.95,
            f"Flow Monitor Locations and Install/Remove Dates",
            ha="right",
            fontsize=16,
        )
        self.a_plot_widget.figure.text(
            0.5, 0.02, self.footer_text, ha="center", fontsize=12
        )

        # Add an image to the header
        im = Image.open(resource_path(f"resources/{rps_or_tt}_logo_report.png"))
        aspect_ratio = im.width / im.height
        desired_height_inch = 0.5
        desired_width_inch = desired_height_inch * aspect_ratio
        fig_dpi = self.a_plot_widget.figure.get_dpi()
        desired_width_px = int(desired_width_inch * fig_dpi)
        desired_height_px = int(desired_height_inch * fig_dpi)
        # Resize the image to fit in the header
        im = im.resize((desired_width_px, desired_height_px))
        imagebox = OffsetImage(im)
        ab = AnnotationBbox(
            imagebox, (0.1, 0.95), frameon=False, xycoords="figure fraction"
        )
        self.a_plot_widget.figure.add_artist(ab)

        # # Adjust layout
        # self.a_plot_widget.figure.subplots_adjust(left=0.15, right=0.85, bottom=0.15, top=0.85)

        # Show plot
        plt.show()


# class graph_fsm_fm_install_summary:

#     def __init__(self, a_pw: PlotWidget = None, dfTable: pd.DataFrame = None):
#         self.dfTable = dfTable
#         self.a_plot_widget: PlotWidget = a_pw
#         self.fig_width = self.a_plot_widget.figure.get_figwidth()
#         self.fig_height = self.a_plot_widget.figure.get_figheight()

#     def update_plot(self):

#         self.a_plot_widget.figure.clear()

#         col_0_width = 66
#         col_1_width = 420
#         col_2_width = 22
#         col_3_width = 44
#         col_4_width = 44
#         col_5_width = 22
#         col_6_width = 44
#         col_7_width = 22
#         col_8_width = 88
#         col_9_width = 88
#         col_10_width = 88
#         col_11_width = 33
#         col_12_width = 33
#         row_height = 25
#         header_row_height = row_height * 2
#         install_row_height = row_height

#         padding = 2
#         a_font_size = 10

#         total_width = (col_0_width + col_1_width + col_2_width + col_3_width + col_4_width + col_5_width + col_6_width +
#                        col_7_width + col_8_width + col_9_width + col_10_width + col_11_width + col_12_width)
#         total_height = install_row_height + header_row_height + (row_height * (self.dfTable.shape[0]))  # including header row

#         # Plotting the table using matplotlib
#         self.plot_axis = self.a_plot_widget.figure.add_subplot(111)

#         self.plot_axis.xaxis.set_visible(False)
#         self.plot_axis.yaxis.set_visible(False)
#         self.plot_axis.set_frame_on(False)
#         self.plot_axis.set_autoscale_on(False)

#         column_widths = [col_0_width, col_1_width, col_2_width, col_3_width, col_4_width, col_5_width, col_6_width, col_7_width,
#                          col_8_width, col_9_width, col_10_width, col_11_width, col_12_width]

#         # Create the table header
#         headers = ['Monitor\nNo.', 'Location', 'Pipe', 'Height\n(mm)', 'Width\n(mm)', 'Shape', 'Depth\n(mm)', 'Type', 'MH Ref.',
#                    'Installed\nDate', 'Removed\nDate', 'Weeks', 'Days']

#         my_y = total_height - (header_row_height + install_row_height)
#         my_x = 0

#         for idx, header in enumerate(headers):
#             if header == 'Weeks':
#                 temp_y = total_height - install_row_height
#                 rect = mpl_patches.Rectangle((my_x, temp_y), (column_widths[idx] + column_widths[idx + 1]), install_row_height,
#                                              edgecolor='black', facecolor='grey', linewidth=1)
#                 self.plot_axis.add_patch(rect)
#                 self.plot_axis.text(my_x + ((column_widths[idx] + column_widths[idx + 1]) / 2), temp_y + install_row_height / 2, 'Installed',
#                                     va='center', ha='center', fontsize=a_font_size, fontweight='bold', color='black')
#             rect = mpl_patches.Rectangle((my_x, my_y), column_widths[idx], header_row_height, edgecolor='black',
#                                          facecolor='grey', linewidth=1)
#             self.plot_axis.add_patch(rect)
#             if header in ['Pipe', 'Shape', 'Type', 'Weeks', 'Days']:
#                 self.plot_axis.text(my_x + column_widths[idx] / 2, my_y + header_row_height / 2, header,
#                                     va='center', ha='center', fontsize=a_font_size, fontweight='bold', color='black', rotation='vertical')
#             else:
#                 self.plot_axis.text(my_x + column_widths[idx] / 2, my_y + header_row_height / 2, header,
#                                     va='center', ha='center', fontsize=a_font_size, fontweight='bold', color='black')
#             my_x += column_widths[idx]

#         # Create the data table
#         for row in range(self.dfTable.shape[0]):
#             my_y = total_height - (install_row_height + header_row_height + ((row + 1) * row_height))
#             my_x = 0
#             for col in range(self.dfTable.shape[1]):
#                 rect = mpl_patches.Rectangle((my_x, my_y), column_widths[col], row_height, edgecolor='black', facecolor='white', linewidth=1)
#                 self.plot_axis.add_patch(rect)
#                 self.plot_axis.text(my_x + column_widths[col] / 2, my_y + row_height / 2, self.dfTable.iloc[row, col], va='center', ha='center', fontsize=a_font_size, fontweight='normal', color='black')
#                 my_x += column_widths[col]

#         # Set the limits of the plot to better visualize the rectangle
#         self.plot_axis.set_box_aspect(total_height / total_width)
#         self.plot_axis.set_xlim(-padding, total_width + padding)
#         self.plot_axis.set_ylim(-padding, total_height + padding)

#         self.a_plot_widget.figure.tight_layout()

#         # Display the table
#         plt.show()


class graph_fsm_rg_install_summary:

    def __init__(
        self,
        a_pw: PlotWidget,
        a_project: fsmProject,
        interim_id: int,
        footer_text: str = "",
    ):

        self.interim_id: int = interim_id
        self.a_project: fsmProject = a_project
        self.footer_text: str = footer_text
        self.a_plot_widget: PlotWidget = a_pw
        self.fig_width = self.a_plot_widget.figure.get_figwidth()
        self.fig_height = self.a_plot_widget.figure.get_figheight()

    def update_plot(self):

        self.a_plot_widget.figure.clear()

        # CREATE INPUT DATA
        data = []
        rg_data = []
        for a_int_rev in self.a_project.dict_fsm_interim_reviews.values():
            if a_int_rev.interim_id == self.interim_id:
                a_inst = self.a_project.dict_fsm_installs[a_int_rev.install_id]
                if a_inst.install_type == "Rain Gauge":
                    a_site = self.a_project.dict_fsm_sites[a_inst.install_site_id]
                    a_mon = self.a_project.dict_fsm_monitors[
                        a_inst.install_monitor_asset_id
                    ]
                    data_list = []
                    data_list.append(a_inst.client_ref)
                    data_list.append(a_site.address)
                    data_list.append(
                        self.a_project.get_rg_position_code(a_inst.rg_position)
                    )
                    data_list.append(a_mon.monitor_sub_type[0])
                    data_list.append(a_site.easting)
                    data_list.append(a_site.northing)
                    data_list.append(a_inst.install_date.strftime("%d/%m/%Y"))
                    if a_inst.remove_date > a_inst.install_date:
                        data_list.append(a_inst.remove_date.strftime("%d/%m/%Y"))
                        date_delta = a_inst.remove_date - a_inst.install_date
                        no_of_weeks = math.floor(date_delta.days / 7)
                        no_of_days = math.floor((date_delta.days - (no_of_weeks * 7)))
                        data_list.append(str(no_of_weeks))
                        data_list.append(str(no_of_days))
                    elif (
                        self.a_project.dict_fsm_interims[
                            self.interim_id
                        ].interim_end_date
                        > a_inst.install_date
                    ):
                        data_list.append("")
                        date_delta = (
                            self.a_project.dict_fsm_interims[
                                self.interim_id
                            ].interim_end_date
                            - a_inst.install_date
                        )
                        no_of_weeks = math.floor(date_delta.days / 7)
                        no_of_days = math.floor((date_delta.days - (no_of_weeks * 7)))
                        data_list.append(str(no_of_weeks))
                        data_list.append(str(no_of_days))
                    rg_data.append(data_list)

        rg_data.sort(key=lambda x: x[0])
        data.extend(rg_data)
        dfTable = pd.DataFrame(
            data,
            columns=[
                "Monitor No.",
                "Location",
                "Posit'n",
                "Type",
                "Easting",
                "Northing",
                "Installed Date",
                "Removed Date",
                "Weeks",
                "Days",
            ],
        )

        col_0_width = 66
        col_1_width = 420
        col_2_width = 22
        col_3_width = 22
        col_4_width = 110
        col_5_width = 110
        col_6_width = 88
        col_7_width = 88
        col_8_width = 33
        col_9_width = 33
        row_height = 25
        header_row_height = row_height * 2
        install_row_height = row_height

        padding = 2
        a_font_size = 10

        total_width = (
            col_0_width
            + col_1_width
            + col_2_width
            + col_3_width
            + col_4_width
            + col_5_width
            + col_6_width
            + col_7_width
            + col_8_width
            + col_9_width
        )
        total_height = (
            install_row_height + header_row_height + (row_height * (dfTable.shape[0]))
        )  # including header row

        # Plotting the table using matplotlib
        self.plot_axis = self.a_plot_widget.figure.add_subplot(111)

        self.plot_axis.xaxis.set_visible(False)
        self.plot_axis.yaxis.set_visible(False)
        self.plot_axis.set_frame_on(False)
        self.plot_axis.set_autoscale_on(False)

        column_widths = [
            col_0_width,
            col_1_width,
            col_2_width,
            col_3_width,
            col_4_width,
            col_5_width,
            col_6_width,
            col_7_width,
            col_8_width,
            col_9_width,
        ]

        # Create the table header
        headers = [
            "Monitor\nNo.",
            "Location",
            "Posit'n",
            "Type",
            "Easting",
            "Northing",
            "Installed\nDate",
            "Removed\nDate",
            "Weeks",
            "Days",
        ]

        my_y = total_height - (header_row_height + install_row_height)
        my_x = 0

        for idx, header in enumerate(headers):
            if header == "Weeks":
                temp_y = total_height - install_row_height
                rect = mpl_patches.Rectangle(
                    (my_x, temp_y),
                    (column_widths[idx] + column_widths[idx + 1]),
                    install_row_height,
                    edgecolor="black",
                    facecolor="grey",
                    linewidth=1,
                )
                self.plot_axis.add_patch(rect)
                self.plot_axis.text(
                    my_x + ((column_widths[idx] + column_widths[idx + 1]) / 2),
                    temp_y + install_row_height / 2,
                    "Installed",
                    va="center",
                    ha="center",
                    fontsize=a_font_size,
                    fontweight="bold",
                    color="black",
                )
            rect = mpl_patches.Rectangle(
                (my_x, my_y),
                column_widths[idx],
                header_row_height,
                edgecolor="black",
                facecolor="grey",
                linewidth=1,
            )
            self.plot_axis.add_patch(rect)
            if header in ["Posit'n", "Type", "Weeks", "Days"]:
                self.plot_axis.text(
                    my_x + column_widths[idx] / 2,
                    my_y + header_row_height / 2,
                    header,
                    va="center",
                    ha="center",
                    fontsize=a_font_size,
                    fontweight="bold",
                    color="black",
                    rotation="vertical",
                )
            else:
                self.plot_axis.text(
                    my_x + column_widths[idx] / 2,
                    my_y + header_row_height / 2,
                    header,
                    va="center",
                    ha="center",
                    fontsize=a_font_size,
                    fontweight="bold",
                    color="black",
                )
            my_x += column_widths[idx]

        # Create the data table
        for row in range(dfTable.shape[0]):
            my_y = total_height - (
                install_row_height + header_row_height + ((row + 1) * row_height)
            )
            my_x = 0
            for col in range(dfTable.shape[1]):
                rect = mpl_patches.Rectangle(
                    (my_x, my_y),
                    column_widths[col],
                    row_height,
                    edgecolor="black",
                    facecolor="white",
                    linewidth=1,
                )
                self.plot_axis.add_patch(rect)
                self.plot_axis.text(
                    my_x + column_widths[col] / 2,
                    my_y + row_height / 2,
                    dfTable.iloc[row, col],
                    va="center",
                    ha="center",
                    fontsize=a_font_size,
                    fontweight="normal",
                    color="black",
                )
                my_x += column_widths[col]

        # Set the limits of the plot to better visualize the rectangle
        self.plot_axis.set_box_aspect(total_height / total_width)
        self.plot_axis.set_xlim(-padding, total_width + padding)
        self.plot_axis.set_ylim(-padding, total_height + padding)

        # Add header and footer
        self.a_plot_widget.figure.text(
            0.95,
            0.95,
            f"Rain Gauge Locations and Install/Remove Dates",
            ha="right",
            fontsize=16,
        )
        self.a_plot_widget.figure.text(
            0.5, 0.02, self.footer_text, ha="center", fontsize=12
        )

        # Add an image to the header
        im = Image.open(resource_path(f"resources/{rps_or_tt}_logo_report.png"))
        aspect_ratio = im.width / im.height
        desired_height_inch = 0.5
        desired_width_inch = desired_height_inch * aspect_ratio
        fig_dpi = self.a_plot_widget.figure.get_dpi()
        desired_width_px = int(desired_width_inch * fig_dpi)
        desired_height_px = int(desired_height_inch * fig_dpi)
        # Resize the image to fit in the header
        im = im.resize((desired_width_px, desired_height_px))
        imagebox = OffsetImage(im)
        ab = AnnotationBbox(
            imagebox, (0.1, 0.95), frameon=False, xycoords="figure fraction"
        )
        self.a_plot_widget.figure.add_artist(ab)

        # # Adjust layout
        # self.a_plot_widget.figure.subplots_adjust(left=0.15, right=0.85, bottom=0.15, top=0.85)

        # Show plot
        plt.show()


# class graph_fsm_rg_install_summary:

#     def __init__(self, a_pw: PlotWidget = None, dfTable: pd.DataFrame = None):
#         self.dfTable = dfTable
#         self.a_plot_widget: PlotWidget = a_pw
#         self.fig_width = self.a_plot_widget.figure.get_figwidth()
#         self.fig_height = self.a_plot_widget.figure.get_figheight()

#     def update_plot(self):

#         self.a_plot_widget.figure.clear()

#         col_0_width = 66
#         col_1_width = 420
#         col_2_width = 22
#         col_3_width = 22
#         col_4_width = 110
#         col_5_width = 110
#         col_6_width = 88
#         col_7_width = 88
#         col_8_width = 33
#         col_9_width = 33
#         row_height = 25
#         header_row_height = row_height * 2
#         install_row_height = row_height

#         padding = 2
#         a_font_size = 10

#         total_width = (col_0_width + col_1_width + col_2_width + col_3_width + col_4_width + col_5_width + col_6_width +
#                        col_7_width + col_8_width + col_9_width)
#         total_height = install_row_height + header_row_height + (row_height * (self.dfTable.shape[0]))  # including header row

#         # Plotting the table using matplotlib
#         self.plot_axis = self.a_plot_widget.figure.add_subplot(111)

#         self.plot_axis.xaxis.set_visible(False)
#         self.plot_axis.yaxis.set_visible(False)
#         self.plot_axis.set_frame_on(False)
#         self.plot_axis.set_autoscale_on(False)

#         column_widths = [col_0_width, col_1_width, col_2_width, col_3_width, col_4_width, col_5_width, col_6_width, col_7_width,
#                          col_8_width, col_9_width]

#         # Create the table header
#         headers = ['Monitor\nNo.', 'Location', 'Posit\'n', 'Type', 'Easting', 'Northing',
#                    'Installed\nDate', 'Removed\nDate', 'Weeks', 'Days']

#         my_y = total_height - (header_row_height + install_row_height)
#         my_x = 0

#         for idx, header in enumerate(headers):
#             if header == 'Weeks':
#                 temp_y = total_height - install_row_height
#                 rect = mpl_patches.Rectangle((my_x, temp_y), (column_widths[idx] + column_widths[idx + 1]), install_row_height,
#                                              edgecolor='black', facecolor='grey', linewidth=1)
#                 self.plot_axis.add_patch(rect)
#                 self.plot_axis.text(my_x + ((column_widths[idx] + column_widths[idx + 1]) / 2), temp_y + install_row_height / 2, 'Installed',
#                                     va='center', ha='center', fontsize=a_font_size, fontweight='bold', color='black')
#             rect = mpl_patches.Rectangle((my_x, my_y), column_widths[idx], header_row_height, edgecolor='black',
#                                          facecolor='grey', linewidth=1)
#             self.plot_axis.add_patch(rect)
#             if header in ['Posit\'n', 'Type', 'Weeks', 'Days']:
#                 self.plot_axis.text(my_x + column_widths[idx] / 2, my_y + header_row_height / 2, header,
#                                     va='center', ha='center', fontsize=a_font_size, fontweight='bold', color='black', rotation='vertical')
#             else:
#                 self.plot_axis.text(my_x + column_widths[idx] / 2, my_y + header_row_height / 2, header,
#                                     va='center', ha='center', fontsize=a_font_size, fontweight='bold', color='black')
#             my_x += column_widths[idx]

#         # Create the data table
#         for row in range(self.dfTable.shape[0]):
#             my_y = total_height - (install_row_height + header_row_height + ((row + 1) * row_height))
#             my_x = 0
#             for col in range(self.dfTable.shape[1]):
#                 rect = mpl_patches.Rectangle((my_x, my_y), column_widths[col], row_height, edgecolor='black', facecolor='white', linewidth=1)
#                 self.plot_axis.add_patch(rect)
#                 self.plot_axis.text(my_x + column_widths[col] / 2, my_y + row_height / 2, self.dfTable.iloc[row, col], va='center', ha='center', fontsize=a_font_size, fontweight='normal', color='black')
#                 my_x += column_widths[col]

#         # Set the limits of the plot to better visualize the rectangle
#         self.plot_axis.set_box_aspect(total_height / total_width)
#         self.plot_axis.set_xlim(-padding, total_width + padding)
#         self.plot_axis.set_ylim(-padding, total_height + padding)

#         self.a_plot_widget.figure.tight_layout()

#         # Display the table
#         plt.show()


class graph_fsm_storm_event_summary:

    def __init__(
        self, a_pw: PlotWidget, a_project: fsmProject, interim_id: int, footer_text: str
    ):
        self.a_plot_widget: PlotWidget = a_pw
        self.a_project: fsmProject = a_project
        self.interim_id: int = interim_id
        self.footer_text: str = footer_text
        self.fig_width = self.a_plot_widget.figure.get_figwidth()
        self.fig_height = self.a_plot_widget.figure.get_figheight()

    def update_plot(self):
        self.a_plot_widget.figure.clear()

        # Define static column widths
        base_col_width = 70
        dynamic_col_width = 40  # Width for RG ID columns
        row_height = 20
        header_row_height = row_height
        install_row_height = row_height

        padding = 2
        a_font_size = 10

        # CREATE INPUT DATA
        headers = ["Ref No.", "Start Time", "End Time", "Duration\n(mins)"]
        headers_ext = False
        data = []
        se_data = []
        for a_se in self.a_project.dict_fsm_stormevents.values():
            if (
                a_se.se_end
                <= self.a_project.dict_fsm_interims[self.interim_id].interim_end_date
            ):
                data_list = []
                data_list.append(a_se.storm_event_id)
                data_list.append(a_se.se_start.strftime("%d/%m/%Y %H:%M"))
                data_list.append(a_se.se_end.strftime("%d/%m/%Y %H:%M"))
                date_delta = a_se.se_end - a_se.se_start
                date_delta_minutes = date_delta.total_seconds() / 60
                data_list.append(math.floor(date_delta_minutes))
                for a_inst in self.a_project.dict_fsm_installs.values():
                    if a_inst.install_type == "Rain Gauge":
                        if not headers_ext:
                            headers.append("RG ID:")
                            headers.append(a_inst.client_ref)
                        data_list.append(
                            a_inst.get_peak_intensity_as_str(a_se.se_start, a_se.se_end)
                        )
                        data_list.append(
                            a_inst.get_total_depth_as_str(a_se.se_start, a_se.se_end)
                        )
                headers_ext = True
                se_data.append(data_list)

        se_data.sort(key=lambda x: x[0])
        data.extend(se_data)
        dfTable = pd.DataFrame(data, columns=headers)

        # Calculate total width and column widths dynamically
        static_columns = 4  # Ref No., Start Time, End Time, Duration (mins)
        dynamic_columns = (dfTable.shape[1] - static_columns) // 2
        total_width = (base_col_width * static_columns) + (
            dynamic_col_width * dynamic_columns * 2
        )

        total_height = (
            install_row_height + header_row_height + (row_height * dfTable.shape[0])
        )

        # Plotting the table using matplotlib
        self.plot_axis = self.a_plot_widget.figure.add_subplot(111)

        self.plot_axis.xaxis.set_visible(False)
        self.plot_axis.yaxis.set_visible(False)
        self.plot_axis.set_frame_on(False)
        self.plot_axis.set_autoscale_on(False)

        column_widths = [base_col_width] * static_columns + [dynamic_col_width] * (
            dynamic_columns * 2
        )

        # Create the table header
        headers = dfTable.columns.tolist()

        my_y = total_height - (header_row_height + install_row_height)
        my_x = 0

        for idx, header in enumerate(headers):
            if header.startswith("RG ID:"):
                temp_y = total_height - install_row_height
                rect = mpl_patches.Rectangle(
                    (my_x, temp_y),
                    (column_widths[idx] + column_widths[idx + 1]),
                    install_row_height,
                    edgecolor="black",
                    facecolor="grey",
                    linewidth=1,
                )
                self.plot_axis.add_patch(rect)
                self.plot_axis.text(
                    my_x + ((column_widths[idx] + column_widths[idx + 1]) / 2),
                    temp_y + install_row_height / 2,
                    headers[idx + 1],
                    va="center",
                    ha="center",
                    fontsize=a_font_size,
                    fontweight="bold",
                    color="black",
                )

            rect = mpl_patches.Rectangle(
                (my_x, my_y),
                column_widths[idx],
                header_row_height,
                edgecolor="black",
                facecolor="grey",
                linewidth=1,
            )
            self.plot_axis.add_patch(rect)

            if header.startswith("RG ID:"):
                self.plot_axis.text(
                    my_x + column_widths[idx] / 2,
                    my_y + header_row_height / 2,
                    "Peak\n(mm/hr)",
                    va="center",
                    ha="center",
                    fontsize=a_font_size,
                    fontweight="bold",
                    color="black",
                )
            elif headers[idx - 1].startswith("RG ID:"):
                self.plot_axis.text(
                    my_x + column_widths[idx] / 2,
                    my_y + header_row_height / 2,
                    "Total\n(mm)",
                    va="center",
                    ha="center",
                    fontsize=a_font_size,
                    fontweight="bold",
                    color="black",
                )
            else:
                self.plot_axis.text(
                    my_x + column_widths[idx] / 2,
                    my_y + header_row_height / 2,
                    header,
                    va="center",
                    ha="center",
                    fontsize=a_font_size,
                    fontweight="bold",
                    color="black",
                )
            my_x += column_widths[idx]

        # Create the data table
        for row in range(dfTable.shape[0]):
            my_y = total_height - (
                install_row_height + header_row_height + ((row + 1) * row_height)
            )
            my_x = 0
            for col in range(dfTable.shape[1]):
                rect = mpl_patches.Rectangle(
                    (my_x, my_y),
                    column_widths[col],
                    row_height,
                    edgecolor="black",
                    facecolor="white",
                    linewidth=1,
                )
                self.plot_axis.add_patch(rect)
                self.plot_axis.text(
                    my_x + column_widths[col] / 2,
                    my_y + row_height / 2,
                    dfTable.iloc[row, col],
                    va="center",
                    ha="center",
                    fontsize=a_font_size,
                    fontweight="normal",
                    color="black",
                )
                my_x += column_widths[col]

        # Set the limits of the plot to better visualize the rectangle
        self.plot_axis.set_box_aspect(total_height / total_width)
        self.plot_axis.set_xlim(-padding, total_width + padding)
        self.plot_axis.set_ylim(-padding, total_height + padding)

        # Add header and footer
        self.a_plot_widget.figure.text(
            0.95, 0.95, "Cumulative Storm Event Summary", ha="right", fontsize=16
        )
        self.a_plot_widget.figure.text(
            0.5, 0.02, self.footer_text, ha="center", fontsize=12
        )

        # Add an image to the header
        im = Image.open(resource_path(f"resources/{rps_or_tt}_logo_report.png"))
        aspect_ratio = im.width / im.height
        desired_height_inch = 0.5
        desired_width_inch = desired_height_inch * aspect_ratio
        fig_dpi = self.a_plot_widget.figure.get_dpi()
        desired_width_px = int(desired_width_inch * fig_dpi)
        desired_height_px = int(desired_height_inch * fig_dpi)
        # Resize the image to fit in the header
        im = im.resize((desired_width_px, desired_height_px))
        imagebox = OffsetImage(im)
        ab = AnnotationBbox(
            imagebox, (0.1, 0.95), frameon=False, xycoords="figure fraction"
        )
        self.a_plot_widget.figure.add_artist(ab)

        # Adjust layout
        self.a_plot_widget.figure.subplots_adjust(
            left=0.15, right=0.85, bottom=0.15, top=0.85
        )
        # Display the table
        plt.show()


# class graph_fsm_storm_event_summary:

#     def __init__(self, a_pw: PlotWidget = None, dfTable: pd.DataFrame = None):
#         self.dfTable = dfTable
#         self.a_plot_widget: PlotWidget = a_pw
#         self.fig_width = self.a_plot_widget.figure.get_figwidth()
#         self.fig_height = self.a_plot_widget.figure.get_figheight()

#     def update_plot(self):
#         self.a_plot_widget.figure.clear()

#         # Define static column widths
#         base_col_width = 60
#         dynamic_col_width = 40  # Width for RG ID columns
#         row_height = 20
#         header_row_height = row_height
#         install_row_height = row_height

#         padding = 2
#         a_font_size = 10

#         # Calculate total width and column widths dynamically
#         static_columns = 4  # Ref No., Start Time, End Time, Duration (mins)
#         dynamic_columns = (self.dfTable.shape[1] - static_columns) // 2
#         total_width = (base_col_width * static_columns) + (dynamic_col_width * dynamic_columns * 2)

#         total_height = install_row_height + header_row_height + (row_height * self.dfTable.shape[0])

#         # Plotting the table using matplotlib
#         self.plot_axis = self.a_plot_widget.figure.add_subplot(111)

#         self.plot_axis.xaxis.set_visible(False)
#         self.plot_axis.yaxis.set_visible(False)
#         self.plot_axis.set_frame_on(False)
#         self.plot_axis.set_autoscale_on(False)

#         column_widths = [base_col_width] * static_columns + [dynamic_col_width] * (dynamic_columns * 2)

#         # Create the table header
#         headers = self.dfTable.columns.tolist()

#         my_y = total_height - (header_row_height + install_row_height)
#         my_x = 0

#         for idx, header in enumerate(headers):
#             if header.startswith('RG ID:'):
#                 temp_y = total_height - install_row_height
#                 rect = mpl_patches.Rectangle((my_x, temp_y), (column_widths[idx] + column_widths[idx + 1]), install_row_height,
#                                              edgecolor='black', facecolor='grey', linewidth=1)
#                 self.plot_axis.add_patch(rect)
#                 self.plot_axis.text(my_x + ((column_widths[idx] + column_widths[idx + 1]) / 2), temp_y + install_row_height / 2,
#                                     headers[idx + 1], va='center', ha='center', fontsize=a_font_size, fontweight='bold', color='black')

#             rect = mpl_patches.Rectangle((my_x, my_y), column_widths[idx], header_row_height, edgecolor='black',
#                                          facecolor='grey', linewidth=1)
#             self.plot_axis.add_patch(rect)

#             if header.startswith('RG ID:'):
#                 self.plot_axis.text(my_x + column_widths[idx] / 2, my_y + header_row_height / 2, 'Peak\n(mm/hr)',
#                                     va='center', ha='center', fontsize=a_font_size, fontweight='bold', color='black')
#             elif headers[idx - 1].startswith('RG ID:'):
#                 self.plot_axis.text(my_x + column_widths[idx] / 2, my_y + header_row_height / 2, 'Total\n(mm)',
#                                     va='center', ha='center', fontsize=a_font_size, fontweight='bold', color='black')
#             else:
#                 self.plot_axis.text(my_x + column_widths[idx] / 2, my_y + header_row_height / 2, header,
#                                     va='center', ha='center', fontsize=a_font_size, fontweight='bold', color='black')
#             my_x += column_widths[idx]

#         # Create the data table
#         for row in range(self.dfTable.shape[0]):
#             my_y = total_height - (install_row_height + header_row_height + ((row + 1) * row_height))
#             my_x = 0
#             for col in range(self.dfTable.shape[1]):
#                 rect = mpl_patches.Rectangle((my_x, my_y), column_widths[col], row_height, edgecolor='black', facecolor='white',
#                                              linewidth=1)
#                 self.plot_axis.add_patch(rect)
#                 self.plot_axis.text(my_x + column_widths[col] / 2, my_y + row_height / 2, self.dfTable.iloc[row, col], va='center',
#                                     ha='center', fontsize=a_font_size, fontweight='normal', color='black')
#                 my_x += column_widths[col]

#         # Set the limits of the plot to better visualize the rectangle
#         self.plot_axis.set_box_aspect(total_height / total_width)
#         self.plot_axis.set_xlim(-padding, total_width + padding)
#         self.plot_axis.set_ylim(-padding, total_height + padding)

#         self.a_plot_widget.figure.tight_layout()

#         # Display the table
#         plt.show()


class graph_fsm_cumulative_interim_summary:

    def __init__(
        self, a_pw: PlotWidget, a_project: fsmProject, interim_id: int, footer_text: str
    ):
        self.a_plot_widget: PlotWidget = a_pw
        self.a_project: fsmProject = a_project
        self.interim_id: int = interim_id
        self.footer_text: str = footer_text
        self.fig_width = self.a_plot_widget.figure.get_figwidth()
        self.fig_height = self.a_plot_widget.figure.get_figheight()

    def update_plot(self):
        self.a_plot_widget.figure.clear()

        # CREATE INPUT DATA
        headers = [
            "Interim",
            "Start",
            "End",
            "Survey Summary for the Interim Report Period",
        ]
        data = []
        ss_data = []
        for a_int in self.a_project.dict_fsm_interims.values():
            if a_int.interim_id <= self.interim_id:
                data_list = []
                data_list.append(a_int.interim_id)
                data_list.append(a_int.interim_start_date.strftime("%d/%m/%Y"))
                data_list.append(a_int.interim_end_date.strftime("%d/%m/%Y"))
                data_list.append(a_int.interim_summary_text)
                ss_data.append(data_list)

        ss_data.sort(key=lambda x: x[0])
        data.extend(ss_data)
        dfTable = pd.DataFrame(data, columns=headers)

        col_0_width = 60
        col_1_width = 60
        col_2_width = 60
        col_3_width = 300
        row_height = 20
        header_row_height = row_height

        padding = 2
        a_font_size = 10

        total_width = col_0_width + col_1_width + col_2_width + col_3_width
        total_height = header_row_height + (
            row_height * (dfTable.shape[0])
        )  # including header row

        # Plotting the table using matplotlib
        self.plot_axis = self.a_plot_widget.figure.add_subplot(111)

        self.plot_axis.xaxis.set_visible(False)
        self.plot_axis.yaxis.set_visible(False)
        self.plot_axis.set_frame_on(False)
        self.plot_axis.set_autoscale_on(False)

        column_widths = [col_0_width, col_1_width, col_2_width, col_3_width]

        # Create the table header
        headers = dfTable.columns.tolist()

        my_y = total_height - header_row_height
        my_x = 0

        for idx, header in enumerate(headers):
            rect = mpl_patches.Rectangle(
                (my_x, my_y),
                column_widths[idx],
                header_row_height,
                edgecolor="black",
                facecolor="grey",
                linewidth=1,
            )
            self.plot_axis.add_patch(rect)
            self.plot_axis.text(
                my_x + column_widths[idx] / 2,
                my_y + header_row_height / 2,
                header,
                va="center",
                ha="center",
                fontsize=a_font_size,
                fontweight="bold",
                color="black",
            )
            my_x += column_widths[idx]

        # Create the data table
        for row in range(dfTable.shape[0]):
            my_y = total_height - (header_row_height + ((row + 1) * row_height))
            my_x = 0
            for col in range(dfTable.shape[1]):
                rect = mpl_patches.Rectangle(
                    (my_x, my_y),
                    column_widths[col],
                    row_height,
                    edgecolor="black",
                    facecolor="white",
                    linewidth=1,
                )
                self.plot_axis.add_patch(rect)
                self.plot_axis.text(
                    my_x + column_widths[col] / 2,
                    my_y + row_height / 2,
                    dfTable.iloc[row, col],
                    va="center",
                    ha="center",
                    fontsize=a_font_size,
                    fontweight="normal",
                    color="black",
                )
                my_x += column_widths[col]

        # Set the limits of the plot to better visualize the rectangle
        self.plot_axis.set_box_aspect(total_height / total_width)
        self.plot_axis.set_xlim(-padding, total_width + padding)
        self.plot_axis.set_ylim(-padding, total_height + padding)

        # Add header and footer
        self.a_plot_widget.figure.text(
            0.95, 0.95, "Cumulative Survey Summary", ha="right", fontsize=16
        )
        self.a_plot_widget.figure.text(
            0.5, 0.02, self.footer_text, ha="center", fontsize=12
        )

        # Add an image to the header
        im = Image.open(resource_path(f"resources/{rps_or_tt}_logo_report.png"))
        aspect_ratio = im.width / im.height
        desired_height_inch = 0.5
        desired_width_inch = desired_height_inch * aspect_ratio
        fig_dpi = self.a_plot_widget.figure.get_dpi()
        desired_width_px = int(desired_width_inch * fig_dpi)
        desired_height_px = int(desired_height_inch * fig_dpi)
        # Resize the image to fit in the header
        im = im.resize((desired_width_px, desired_height_px))
        imagebox = OffsetImage(im)
        ab = AnnotationBbox(
            imagebox, (0.1, 0.95), frameon=False, xycoords="figure fraction"
        )
        self.a_plot_widget.figure.add_artist(ab)

        # # Adjust layout
        # self.a_plot_widget.figure.subplots_adjust(left=0.15, right=0.85, bottom=0.15, top=0.85)
        # Display the table
        plt.show()


# class graph_fsm_cumulative_interim_summary:

#     def __init__(self, a_pw: PlotWidget = None, dfTable: pd.DataFrame = None):
#         self.dfTable = dfTable
#         self.a_plot_widget: PlotWidget = a_pw
#         self.fig_width = self.a_plot_widget.figure.get_figwidth()
#         self.fig_height = self.a_plot_widget.figure.get_figheight()

#     def update_plot(self):
#         self.a_plot_widget.figure.clear()

#         col_0_width = 60
#         col_1_width = 60
#         col_2_width = 60
#         col_3_width = 300
#         row_height = 20
#         header_row_height = row_height

#         padding = 2
#         a_font_size = 10

#         total_width = (col_0_width + col_1_width + col_2_width + col_3_width)
#         total_height = header_row_height + (row_height * (self.dfTable.shape[0]))  # including header row

#         # Plotting the table using matplotlib
#         self.plot_axis = self.a_plot_widget.figure.add_subplot(111)

#         self.plot_axis.xaxis.set_visible(False)
#         self.plot_axis.yaxis.set_visible(False)
#         self.plot_axis.set_frame_on(False)
#         self.plot_axis.set_autoscale_on(False)

#         column_widths = [col_0_width, col_1_width, col_2_width, col_3_width]

#         # Create the table header
#         headers = self.dfTable.columns.tolist()

#         my_y = total_height - header_row_height
#         my_x = 0

#         for idx, header in enumerate(headers):
#             rect = mpl_patches.Rectangle((my_x, my_y), column_widths[idx], header_row_height, edgecolor='black',
#                                          facecolor='grey', linewidth=1)
#             self.plot_axis.add_patch(rect)
#             self.plot_axis.text(my_x + column_widths[idx] / 2, my_y + header_row_height / 2, header,
#                                 va='center', ha='center', fontsize=a_font_size, fontweight='bold', color='black')
#             my_x += column_widths[idx]

#         # Create the data table
#         for row in range(self.dfTable.shape[0]):
#             my_y = total_height - (header_row_height + ((row + 1) * row_height))
#             my_x = 0
#             for col in range(self.dfTable.shape[1]):
#                 rect = mpl_patches.Rectangle((my_x, my_y), column_widths[col], row_height, edgecolor='black', facecolor='white', linewidth=1)
#                 self.plot_axis.add_patch(rect)
#                 self.plot_axis.text(my_x + column_widths[col] / 2, my_y + row_height / 2, self.dfTable.iloc[row, col],
#                                     va='center', ha='center', fontsize=a_font_size, fontweight='normal', color='black')
#                 my_x += column_widths[col]

#         # Set the limits of the plot to better visualize the rectangle
#         self.plot_axis.set_box_aspect(total_height / total_width)
#         self.plot_axis.set_xlim(-padding, total_width + padding)
#         self.plot_axis.set_ylim(-padding, total_height + padding)

#         self.a_plot_widget.figure.tight_layout()

#         # Display the table
#         plt.show()


class graph_fsm_monitor_data_summary:

    def __init__(
        self,
        a_pw: PlotWidget,
        a_project: fsmProject,
        interim_id: int,
        a_inst: fsmInstall,
        footer_text: str,
    ):
        self.a_plot_widget: PlotWidget = a_pw
        self.a_project: fsmProject = a_project
        self.interim_id: int = interim_id
        self.a_inst: fsmInstall = a_inst
        self.footer_text: str = footer_text
        self.fig_width = self.a_plot_widget.figure.get_figwidth()
        self.fig_height = self.a_plot_widget.figure.get_figheight()

    def update_plot(self):
        self.a_plot_widget.figure.clear()

        this_interim = self.a_project.dict_fsm_interims[self.interim_id]
        all_dates = pd.date_range(
            start=self.a_project.survey_start_date,
            end=this_interim.interim_end_date,
            freq="D",
        )
        all_dates_df = pd.DataFrame({"Date": all_dates})

        # Define the order of days in a week
        days_of_week = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        renamed_columns = {
            "Monday": "M",
            "Tuesday": "T",
            "Wednesday": "W",
            "Thursday": "T",
            "Friday": "F",
            "Saturday": "S",
            "Sunday": "S",
        }
        # Find the starting day of the survey
        start_day = pd.Timestamp(self.a_project.survey_start_date).day_name()
        # Create a new order starting from the start_day
        start_index = days_of_week.index(start_day)
        ordered_days = days_of_week[start_index:] + days_of_week[:start_index]

        # plot_count = 1
        # for a_inst in self.fsmProject.dict_fsm_installs.values():

        df_class_data = self.a_inst.get_combined_classification_by_date(
            self.a_project.survey_start_date, this_interim.interim_end_date
        )
        merged_df = pd.merge(all_dates_df, df_class_data, on="Date", how="left")
        merged_df["Week"] = (
            (merged_df["Date"] - self.a_project.survey_start_date).dt.days // 7
        ) + 1
        merged_df["Day"] = merged_df["Date"].dt.day_name()
        merged_df["Week_Start_Date"] = merged_df["Week"].apply(
            lambda x: self.a_project.survey_start_date + pd.DateOffset(weeks=x - 1)
        )
        # Create pivot table
        dfDataTable = merged_df.pivot_table(
            index="Week", columns="Day", values="Classification", aggfunc="first"
        )
        # Reorder columns to match days of the week
        dfDataTable = dfDataTable[ordered_days]
        week_start_dates = merged_df.groupby("Week")["Week_Start_Date"].first()
        dfDataTable.insert(0, "Date", week_start_dates)
        dfDataTable = dfDataTable.fillna("")
        dfDataTable["Comments"] = ""
        #
        # NEED TO UPDATE COMMENTS COLUMN WITH MONITOR DATA COMMENT FOR THAT WEEK/INTERIM################################
        #
        dfDataTable.reset_index(inplace=True)
        dfDataTable["Date"] = dfDataTable["Date"].dt.strftime("%d/%m/%Y")
        # Move the "Comments" column to the desired position (after "Date")
        comments_column = dfDataTable.pop("Comments")  # Remove the "Comments" column
        dfDataTable.insert(2, "Comments", comments_column)  # Insert it at the 3rd position (index 2)

        # dfDataTable = dfDataTable[
        #     [
        #         "Week",
        #         "Date",
        #         "Comments",
        #         "Tuesday",
        #         "Wednesday",
        #         "Thursday",
        #         "Friday",
        #         "Saturday",
        #         "Sunday",
        #         "Monday",
        #     ]
        # ]
        dfDataTable.rename(columns=renamed_columns, inplace=True)

        loc_list = []
        if self.a_inst.install_type == "Flow Monitor":
            loc_list.append(
                [
                    "Location",
                    self.a_project.dict_fsm_sites[self.a_inst.install_site_id].address,
                ]
            )
            loc_list.append(
                [
                    "Pipe",
                    f"{self.a_inst.fm_pipe_shape} {self.a_inst.fm_pipe_width_mm} diameter",
                ]
            )
            loc_list.append(
                [
                    "Monitor Type",
                    self.a_project.dict_fsm_monitors[
                        self.a_inst.install_monitor_asset_id
                    ].monitor_sub_type,
                ]
            )
            loc_list.append(
                ["Installed", self.a_inst.install_date.strftime("%d/%m/%Y")]
            )
            if self.a_inst.remove_date > self.a_inst.install_date:
                loc_list.append(
                    ["Removed", self.a_inst.remove_date.strftime("%d/%m/%Y")]
                )
            else:
                loc_list.append(["Removed", ""])
            loc_list.append(
                [
                    "Comment",
                    self.a_project.get_interim_monitor_comment(
                        self.interim_id,
                        self.a_inst.install_id,
                        self.a_inst.install_type,
                    ),
                ]
            )
            # fm_loc_data.append(loc_list)
            # fm_int_data.append(pivot_df.copy())
            dfLocationTable = pd.DataFrame(loc_list, columns=["Col1", "Col2"])

        if self.a_inst.install_type == "Depth Monitor":
            loc_list.append(
                [
                    "Location",
                    self.a_project.dict_fsm_sites[self.a_inst.install_site_id].address,
                ]
            )
            loc_list.append(["Pipe", ""])
            loc_list.append(
                [
                    "Monitor Type",
                    self.a_project.dict_fsm_monitors[
                        self.a_inst.install_monitor_asset_id
                    ].monitor_sub_type,
                ]
            )
            loc_list.append(
                ["Installed", self.a_inst.install_date.strftime("%d/%m/%Y")]
            )
            if self.a_inst.remove_date > self.a_inst.install_date:
                loc_list.append(
                    ["Removed", self.a_inst.remove_date.strftime("%d/%m/%Y")]
                )
            else:
                loc_list.append(["Removed", ""])
            loc_list.append(
                [
                    "Comment",
                    self.a_project.get_interim_monitor_comment(
                        self.interim_id,
                        self.a_inst.install_id,
                        self.a_inst.install_type,
                    ),
                ]
            )
            # dm_int_data.append(pivot_df.copy())
            # dm_loc_data.append(loc_list)
            dfLocationTable = pd.DataFrame(loc_list, columns=["Col1", "Col2"])

        if self.a_inst.install_type == "Rain Gauge":
            loc_list.append(
                [
                    "Location",
                    self.a_project.dict_fsm_sites[self.a_inst.install_site_id].address,
                ]
            )
            loc_list.append(["Position", self.a_inst.rg_position])
            loc_list.append(
                [
                    "Monitor Type",
                    self.a_project.dict_fsm_monitors[
                        self.a_inst.install_monitor_asset_id
                    ].monitor_sub_type,
                ]
            )
            loc_list.append(
                ["Installed", self.a_inst.install_date.strftime("%d/%m/%Y")]
            )
            if self.a_inst.remove_date > self.a_inst.install_date:
                loc_list.append(
                    ["Removed", self.a_inst.remove_date.strftime("%d/%m/%Y")]
                )
            else:
                loc_list.append(["Removed", ""])
            loc_list.append(
                [
                    "Comment",
                    self.a_project.get_interim_monitor_comment(
                        self.interim_id,
                        self.a_inst.install_id,
                        self.a_inst.install_type,
                    ),
                ]
            )
            # rg_loc_data.append(loc_list)
            # rg_int_data.append(pivot_df.copy())
            dfLocationTable = pd.DataFrame(loc_list, columns=["Col1", "Col2"])

        # Define column widths
        col_0_width = 60
        col_1_width = 100
        col_2_width = 400
        col_3_width = 30
        col_4_width = 30
        col_5_width = 30
        col_6_width = 30
        col_7_width = 30
        col_8_width = 30
        col_9_width = 30
        # dynamic_col_width = 40  # Width for RG ID columns
        row_height = 20
        header_row_height = row_height

        data_table_total_width = (
            col_0_width
            + col_1_width
            + col_2_width
            + col_3_width
            + col_4_width
            + col_5_width
            + col_6_width
            + col_7_width
            + col_8_width
            + col_9_width
        )
        data_table_total_height = header_row_height + (
            row_height * dfDataTable.shape[0]
        )

        loc_col_0_width = 160
        loc_col_1_width = data_table_total_width - loc_col_0_width

        loc_table_total_width = loc_col_0_width + loc_col_1_width
        loc_table_total_height = row_height * dfLocationTable.shape[0]

        padding = 2
        a_font_size = 10

        dt_x = (data_table_total_width / (self.fig_width / self.fig_height)) - (
            loc_table_total_height + data_table_total_height
        )
        total_height_needed = loc_table_total_height + data_table_total_height + dt_x

        # total_fig_height_needed = self.fig_width * (total_height_needed / data_table_total_width)

        # self.a_plot_widget.figure.set_figheight(total_fig_height_needed)

        hr_loc = loc_table_total_height / total_height_needed
        hr_dat = (data_table_total_height + dt_x) / total_height_needed

        # location_fig_height = self.fig_width / (loc_table_total_width / loc_table_total_height)
        # data_fig_height = self.fig_height - location_fig_height

        # # Plotting the table using matplotlib
        (self.plot_axis_loc, self.plot_axis_data) = self.a_plot_widget.figure.subplots(
            2, sharex=False, gridspec_kw={"height_ratios": [hr_loc, hr_dat]}
        )

        self.plot_axis_loc.xaxis.set_visible(False)
        self.plot_axis_loc.yaxis.set_visible(False)
        self.plot_axis_loc.set_frame_on(False)
        self.plot_axis_loc.set_autoscale_on(False)

        loc_column_widths = [loc_col_0_width, loc_col_1_width]

        # Create the data table
        for row in range(dfLocationTable.shape[0]):
            my_y = loc_table_total_height - ((row + 1) * row_height)
            my_x = 0
            # print(f'X: {my_x}, Y: {my_y}')
            for col in range(dfLocationTable.shape[1]):
                if col == 0:
                    rect = mpl_patches.Rectangle(
                        (my_x, my_y),
                        loc_column_widths[col],
                        row_height,
                        edgecolor="black",
                        facecolor="grey",
                        linewidth=1,
                    )
                    self.plot_axis_loc.add_patch(rect)
                    self.plot_axis_loc.text(
                        my_x + loc_column_widths[col] / 2,
                        my_y + row_height / 2,
                        dfLocationTable.iloc[row, col],
                        va="center",
                        ha="center",
                        fontsize=a_font_size,
                        fontweight="bold",
                        color="black",
                    )
                else:
                    rect = mpl_patches.Rectangle(
                        (my_x, my_y),
                        loc_column_widths[col],
                        row_height,
                        edgecolor="black",
                        facecolor="white",
                        linewidth=1,
                    )
                    #         rect = mpl_patches.Rectangle((my_x, my_y), loc_column_widths[col], row_height, edgecolor='black', facecolor='white', linewidth=1)
                    self.plot_axis_loc.add_patch(rect)
                    self.plot_axis_loc.text(
                        my_x + loc_column_widths[col] / 2,
                        my_y + row_height / 2,
                        dfLocationTable.iloc[row, col],
                        va="center",
                        ha="center",
                        fontsize=a_font_size,
                        fontweight="normal",
                        color="black",
                    )
                my_x += loc_column_widths[col]

        # Set the limits of the plot to better visualize the rectangle
        self.plot_axis_loc.set_box_aspect(
            loc_table_total_height / loc_table_total_width
        )
        self.plot_axis_loc.set_xlim(-padding, loc_table_total_width + padding)
        self.plot_axis_loc.set_ylim(-padding, loc_table_total_height + padding)

        self.plot_axis_data.xaxis.set_visible(False)
        self.plot_axis_data.yaxis.set_visible(False)
        self.plot_axis_data.set_frame_on(False)
        self.plot_axis_data.set_autoscale_on(False)

        data_column_widths = [
            col_0_width,
            col_1_width,
            col_2_width,
            col_3_width,
            col_4_width,
            col_5_width,
            col_6_width,
            col_7_width,
            col_8_width,
            col_9_width,
        ]
        # column_widths = [base_col_width] * static_columns

        # Create the data table header
        headers = dfDataTable.columns.tolist()

        my_y = data_table_total_height - (header_row_height)
        my_x = 0

        for idx, header in enumerate(headers):
            rect = mpl_patches.Rectangle(
                (my_x, my_y),
                data_column_widths[idx],
                header_row_height,
                edgecolor="black",
                facecolor="grey",
                linewidth=1,
            )
            self.plot_axis_data.add_patch(rect)
            self.plot_axis_data.text(
                my_x + data_column_widths[idx] / 2,
                my_y + header_row_height / 2,
                header,
                va="center",
                ha="center",
                fontsize=a_font_size,
                fontweight="bold",
                color="black",
            )
            my_x += data_column_widths[idx]

        # Create the data table
        for row in range(dfDataTable.shape[0]):
            my_y = data_table_total_height - (
                header_row_height + ((row + 1) * row_height)
            )
            my_x = 0
            for col in range(dfDataTable.shape[1]):
                rect = mpl_patches.Rectangle(
                    (my_x, my_y),
                    data_column_widths[col],
                    row_height,
                    edgecolor="black",
                    facecolor="white",
                    linewidth=1,
                )
                self.plot_axis_data.add_patch(rect)
                self.plot_axis_data.text(
                    my_x + data_column_widths[col] / 2,
                    my_y + row_height / 2,
                    dfDataTable.iloc[row, col],
                    va="center",
                    ha="center",
                    fontsize=a_font_size,
                    fontweight="normal",
                    color="black",
                )
                my_x += data_column_widths[col]

        # Set the limits of the plot to better visualize the rectangle
        self.plot_axis_data.set_box_aspect(
            data_table_total_height / data_table_total_width
        )
        self.plot_axis_data.set_xlim(-padding, data_table_total_width + padding)
        self.plot_axis_data.set_ylim(-padding, data_table_total_height + padding)

        # Add header and footer
        self.a_plot_widget.figure.text(
            0.95,
            0.95,
            f"Cumulative Install Summary: {self.a_inst.install_monitor_asset_id}/{self.a_inst.client_ref}",
            ha="right",
            fontsize=16,
        )
        self.a_plot_widget.figure.text(
            0.5, 0.02, self.footer_text, ha="center", fontsize=12
        )

        # Add an image to the header
        im = Image.open(resource_path(f"resources/{rps_or_tt}_logo_report.png"))
        aspect_ratio = im.width / im.height
        desired_height_inch = 0.5
        desired_width_inch = desired_height_inch * aspect_ratio
        fig_dpi = self.a_plot_widget.figure.get_dpi()
        desired_width_px = int(desired_width_inch * fig_dpi)
        desired_height_px = int(desired_height_inch * fig_dpi)
        # Resize the image to fit in the header
        im = im.resize((desired_width_px, desired_height_px))
        imagebox = OffsetImage(im)
        ab = AnnotationBbox(
            imagebox, (0.1, 0.95), frameon=False, xycoords="figure fraction"
        )
        self.a_plot_widget.figure.add_artist(ab)

        # # Adjust layout
        # self.a_plot_widget.figure.subplots_adjust(left=0.15, right=0.85, bottom=0.15, top=0.85)
        # Display the table
        plt.show()


# class graph_fsm_monitor_data_summary:

#     def __init__(self, a_pw: PlotWidget = None, dfDataTable: pd.DataFrame = None, dfLocationTable: pd.DataFrame = None):
#         self.dfDataTable: pd.DataFrame = dfDataTable
#         self.dfLocationTable: pd.DataFrame = dfLocationTable
#         self.a_plot_widget: PlotWidget = a_pw
#         self.fig_width = self.a_plot_widget.figure.get_figwidth()
#         self.fig_height = self.a_plot_widget.figure.get_figheight()

#     def update_plot(self):
#         self.a_plot_widget.figure.clear()

#         # Define column widths
#         col_0_width = 60
#         col_1_width = 100
#         col_2_width = 400
#         col_3_width = 30
#         col_4_width = 30
#         col_5_width = 30
#         col_6_width = 30
#         col_7_width = 30
#         col_8_width = 30
#         col_9_width = 30
#         # dynamic_col_width = 40  # Width for RG ID columns
#         row_height = 20
#         header_row_height = row_height

#         data_table_total_width = (col_0_width + col_1_width + col_2_width + col_3_width + col_4_width + col_5_width +
#                                   col_6_width + col_7_width + col_8_width + col_9_width)
#         data_table_total_height = header_row_height + (row_height * self.dfDataTable.shape[0])

#         loc_col_0_width = 160
#         loc_col_1_width = data_table_total_width - loc_col_0_width

#         loc_table_total_width = loc_col_0_width + loc_col_1_width
#         loc_table_total_height = row_height * self.dfLocationTable.shape[0]

#         padding = 2
#         a_font_size = 10

#         total_height_needed = loc_table_total_height + data_table_total_height
#         total_fig_height_needed = self.fig_width * (total_height_needed / data_table_total_width)

#         self.a_plot_widget.figure.set_figheight(total_fig_height_needed)

#         hr_loc = (loc_table_total_height / total_height_needed)
#         hr_dat = (data_table_total_height / total_height_needed)

#         # location_fig_height = self.fig_width / (loc_table_total_width / loc_table_total_height)
#         # data_fig_height = self.fig_height - location_fig_height

#         # # Plotting the table using matplotlib
#         (self.plot_axis_loc, self.plot_axis_data) = self.a_plot_widget.figure.subplots(2, sharex=False, gridspec_kw={'height_ratios': [hr_loc, hr_dat]})

#         self.plot_axis_loc.xaxis.set_visible(False)
#         self.plot_axis_loc.yaxis.set_visible(False)
#         self.plot_axis_loc.set_frame_on(False)
#         self.plot_axis_loc.set_autoscale_on(False)

#         loc_column_widths = [loc_col_0_width, loc_col_1_width]

#         # Create the data table
#         for row in range(self.dfLocationTable.shape[0]):
#             my_y = loc_table_total_height - ((row + 1) * row_height)
#             my_x = 0
#             # print(f'X: {my_x}, Y: {my_y}')
#             for col in range(self.dfLocationTable.shape[1]):
#                 if col == 0:
#                     rect = mpl_patches.Rectangle((my_x, my_y), loc_column_widths[col], row_height, edgecolor='black',
#                                                 facecolor='grey', linewidth=1)
#                     self.plot_axis_loc.add_patch(rect)
#                     self.plot_axis_loc.text(my_x + loc_column_widths[col] / 2, my_y + row_height / 2, self.dfLocationTable.iloc[row, col],
#                                     va='center', ha='center', fontsize=a_font_size, fontweight='bold', color='black')
#                 else:
#                     rect = mpl_patches.Rectangle((my_x, my_y), loc_column_widths[col], row_height, edgecolor='black', facecolor='white', linewidth=1)
#         #         rect = mpl_patches.Rectangle((my_x, my_y), loc_column_widths[col], row_height, edgecolor='black', facecolor='white', linewidth=1)
#                     self.plot_axis_loc.add_patch(rect)
#                     self.plot_axis_loc.text(my_x + loc_column_widths[col] / 2, my_y + row_height / 2, self.dfLocationTable.iloc[row, col],
#                                     va='center', ha='center', fontsize=a_font_size, fontweight='normal', color='black')
#                 my_x += loc_column_widths[col]

#         # Set the limits of the plot to better visualize the rectangle
#         self.plot_axis_loc.set_box_aspect(loc_table_total_height / loc_table_total_width)
#         self.plot_axis_loc.set_xlim(-padding, loc_table_total_width + padding)
#         self.plot_axis_loc.set_ylim(-padding, loc_table_total_height + padding)

#         self.plot_axis_data.xaxis.set_visible(False)
#         self.plot_axis_data.yaxis.set_visible(False)
#         self.plot_axis_data.set_frame_on(False)
#         self.plot_axis_data.set_autoscale_on(False)

#         data_column_widths = [col_0_width, col_1_width, col_2_width, col_3_width, col_4_width, col_5_width,
#                               col_6_width, col_7_width, col_8_width, col_9_width]
#         # column_widths = [base_col_width] * static_columns

#         # Create the data table header
#         headers = self.dfDataTable.columns.tolist()

#         my_y = data_table_total_height - (header_row_height)
#         my_x = 0

#         for idx, header in enumerate(headers):
#             rect = mpl_patches.Rectangle((my_x, my_y), data_column_widths[idx], header_row_height, edgecolor='black',
#                                         facecolor='grey', linewidth=1)
#             self.plot_axis_data.add_patch(rect)
#             self.plot_axis_data.text(my_x + data_column_widths[idx] / 2, my_y + header_row_height / 2, header,
#                                     va='center', ha='center', fontsize=a_font_size, fontweight='bold', color='black')
#             my_x += data_column_widths[idx]

#         # Create the data table
#         for row in range(self.dfDataTable.shape[0]):
#             my_y = data_table_total_height - (header_row_height + ((row + 1) * row_height))
#             my_x = 0
#             for col in range(self.dfDataTable.shape[1]):
#                 rect = mpl_patches.Rectangle((my_x, my_y), data_column_widths[col], row_height, edgecolor='black', facecolor='white',
#                                             linewidth=1)
#                 self.plot_axis_data.add_patch(rect)
#                 self.plot_axis_data.text(my_x + data_column_widths[col] / 2, my_y + row_height / 2, self.dfDataTable.iloc[row, col], va='center',
#                                         ha='center', fontsize=a_font_size, fontweight='normal', color='black')
#                 my_x += data_column_widths[col]

#         # Set the limits of the plot to better visualize the rectangle
#         self.plot_axis_data.set_box_aspect(data_table_total_height / data_table_total_width)
#         self.plot_axis_data.set_xlim(-padding, data_table_total_width + padding)
#         self.plot_axis_data.set_ylim(-padding, data_table_total_height + padding)

#         # a_plot_widget.figure.tight_layout()
#         # plt.tight_layout()
#         # Display the table
#         plt.show()


class graph_fsm_raingauge_plot:

    def __init__(
        self,
        a_pw: PlotWidget,
        a_install: fsmInstall,
        start_date: datetime,
        end_date: datetime,
        footer_text: str = "",
    ):
        self.a_plot_widget: PlotWidget = a_pw
        self.current_inst: fsmInstall = a_install
        self.footer_text: str = footer_text
        self.start_date: datetime = start_date
        self.end_date: datetime = end_date

    def update_plot(self):

        self.a_plot_widget.figure.clear()

        a_linewidth = 0.5

        # self.filter_dep_data()
        df_filtered = self.current_inst.data.copy()
        df_filtered = df_filtered.sort_values(by="Date")
        df_filtered = df_filtered[
            (df_filtered["Date"] >= self.start_date)
            & (df_filtered["Date"] <= self.end_date)
        ]
        df_filtered["RainfallDepth_mm"] = df_filtered["IntensityData"] * (
            self.current_inst.data_interval / 60
        )

        self.plot_axis_rg = self.a_plot_widget.figure.subplots(
            nrows=1, gridspec_kw={"height_ratios": [1]}
        )
        self.plot_axis_rg.plot(
            df_filtered["Date"],
            df_filtered["IntensityData"],
            color="darkblue",
            linewidth=a_linewidth,
        )
        self.plot_axis_rg.set_ylabel("Intensity (mm/hr)")
        self.plot_axis_rg.set_xlabel("Date")

        # Set major and minor locators
        self.plot_axis_rg.xaxis.set_major_locator(mpl_dates.DayLocator())
        self.plot_axis_rg.xaxis.set_major_formatter(
            mpl_dates.DateFormatter("%a %d/%m/%Y")
        )
        self.plot_axis_rg.xaxis.set_minor_locator(
            mpl_dates.HourLocator(byhour=[0, 6, 12, 18])
        )

        self.plot_axis_rg.xaxis.set_major_formatter(
            mpl_dates.ConciseDateFormatter(mpl_dates.AutoDateLocator())
        )

        x_min, x_max = mpl_dates.num2date(self.plot_axis_rg.get_xlim())
        x_min = np.datetime64(x_min)
        x_max = np.datetime64(x_max)
        df_stats = df_filtered[
            (df_filtered["Date"] >= x_min) & (df_filtered["Date"] <= x_max)
        ].copy()

        rain_min = df_stats["IntensityData"].min()
        rain_max = df_stats["IntensityData"].max()
        rain_range = rain_max - rain_min
        rain_avg = df_stats["IntensityData"].mean()

        total_rain_depth_mm = df_stats["RainfallDepth_mm"].sum()

        # Add statistics to the right of the plot
        rain_stats_text = f"Min: {rain_min:.2f}\nMax: {rain_max:.2f}\nRange: {rain_range:.2f}\nAverage: {rain_avg:.2f}\nDepth (mm): {total_rain_depth_mm:.1f} mm"
        self.plot_axis_rg.text(
            1.02,
            0.5,
            rain_stats_text,
            transform=self.plot_axis_rg.transAxes,
            verticalalignment="center",
        )

        # Add header and footer
        self.a_plot_widget.figure.text(
            0.95,
            0.95,
            f"Rain Gauge Plot: {self.current_inst.client_ref}",
            ha="right",
            fontsize=16,
        )
        self.a_plot_widget.figure.text(
            0.5, 0.02, self.footer_text, ha="center", fontsize=12
        )

        # Add an image to the header
        im = Image.open(resource_path(f"resources/{rps_or_tt}_logo_report.png"))
        aspect_ratio = im.width / im.height
        desired_height_inch = 0.5
        desired_width_inch = desired_height_inch * aspect_ratio
        fig_dpi = self.a_plot_widget.figure.get_dpi()
        desired_width_px = int(desired_width_inch * fig_dpi)
        desired_height_px = int(desired_height_inch * fig_dpi)
        # Resize the image to fit in the header
        im = im.resize((desired_width_px, desired_height_px))
        imagebox = OffsetImage(im)
        ab = AnnotationBbox(
            imagebox, (0.1, 0.95), frameon=False, xycoords="figure fraction"
        )
        self.a_plot_widget.figure.add_artist(ab)

        # Adjust layout
        self.a_plot_widget.figure.subplots_adjust(
            left=0.15, right=0.85, bottom=0.15, top=0.85
        )

        # Show plot
        plt.show()


class graph_fsm_fdv_plot:

    def __init__(
        self,
        a_pw: PlotWidget,
        a_install: fsmInstall,
        a_project: fsmProject,
        start_date: datetime,
        end_date: datetime,
        footer_text: str = "",
    ):
        self.a_plot_widget: PlotWidget = a_pw
        self.a_project: fsmProject = a_project
        self.current_inst: fsmInstall = a_install
        self.footer_text: str = footer_text
        self.start_date: datetime = start_date
        self.end_date: datetime = end_date

    def update_plot(self):

        self.a_plot_widget.figure.clear()

        a_linewidth = 0.5

        i_soffit_mm = self.current_inst.fm_pipe_height_mm

        df_filtered = self.current_inst.data[
            (self.current_inst.data["Date"] >= self.start_date)
            & (self.current_inst.data["Date"] <= self.end_date)
        ].copy()

        all_rainfall_data = []

        for a_inst in self.a_project.dict_fsm_installs.values():
            if a_inst.install_type == "Rain Gauge":
                a_instance_rainfall_data = a_inst.data[["Date", "IntensityData"]].copy()
                a_instance_rainfall_data["RainfallDepth_mm"] = a_instance_rainfall_data[
                    "IntensityData"
                ] * (a_inst.data_interval / 60)
                all_rainfall_data.append(a_instance_rainfall_data)

        if all_rainfall_data:
            combined_rainfall_data = pd.concat(all_rainfall_data)
            average_rainfall_data = combined_rainfall_data.groupby(
                "Date", as_index=False
            ).agg({"IntensityData": "mean", "RainfallDepth_mm": "mean"})
        else:
            average_rainfall_data = pd.DataFrame(
                columns=["Date", "IntensityData", "RainfallDepth_mm"]
            )

        df_rgs_filtered = average_rainfall_data[
            (average_rainfall_data["Date"] >= self.start_date)
            & (average_rainfall_data["Date"] <= self.end_date)
        ].copy()

        (plot_axis_flow, plot_axis_depth, plot_axis_velocity, plot_axis_rg) = (
            self.a_plot_widget.figure.subplots(
                nrows=4, sharex=True, gridspec_kw={"height_ratios": [1, 1, 1, 1]}
            )
        )

        plot_axis_flow.plot(
            df_filtered["Date"],
            df_filtered["FlowData"],
            color="blue",
            linewidth=a_linewidth,
        )
        plot_axis_flow.set_ylabel("Flow (l/sec)")
        # Adding filename to title
        plot_axis_flow.set_title("Flow", loc="left", fontsize=16)

        i_soffit_mm_array = np.full(len(df_filtered), i_soffit_mm)
        plot_axis_depth.plot(
            df_filtered["Date"],
            df_filtered["DepthData"],
            color="red",
            linewidth=a_linewidth,
        )
        plot_axis_depth.plot(
            df_filtered["Date"],
            i_soffit_mm_array,
            color="darkblue",
            label="Soffit",
            linewidth=a_linewidth,
        )
        plot_axis_depth.set_ylabel("Depth (mm)")
        plot_axis_depth.set_title("Depth", loc="left", fontsize=16)
        # Add Soffit height label
        plot_axis_depth.text(
            df_filtered["Date"].iloc[0],
            i_soffit_mm - 10,
            f"Soffit Height = {i_soffit_mm}mm",
            color="darkblue",
            verticalalignment="top",
            horizontalalignment="left",
            fontsize=8,
        )

        plot_axis_velocity.plot(
            df_filtered["Date"],
            df_filtered["VelocityData"],
            color="green",
            linewidth=a_linewidth,
        )
        plot_axis_velocity.set_ylabel("Velocity (m/sec)")
        plot_axis_velocity.set_title("Velocity", loc="left", fontsize=16)

        plot_axis_rg.plot(
            df_rgs_filtered["Date"],
            df_rgs_filtered["IntensityData"],
            color="darkblue",
            linewidth=a_linewidth,
        )
        plot_axis_rg.set_ylabel("Intensity (mm/hr)")
        # Adding filename to title
        plot_axis_rg.set_title("Flow", loc="left", fontsize=16)
        plot_axis_rg.set_xlabel("Date")

        # Set major and minor locators
        plot_axis_rg.xaxis.set_major_locator(mpl_dates.DayLocator())
        plot_axis_rg.xaxis.set_major_formatter(mpl_dates.DateFormatter("%a %d/%m/%Y"))
        plot_axis_rg.xaxis.set_minor_locator(
            mpl_dates.HourLocator(byhour=[0, 6, 12, 18])
        )

        plot_axis_rg.xaxis.set_major_formatter(
            mpl_dates.ConciseDateFormatter(mpl_dates.AutoDateLocator())
        )

        x_min, x_max = mpl_dates.num2date(plot_axis_rg.get_xlim())
        x_min = np.datetime64(x_min)
        x_max = np.datetime64(x_max)
        df_stats = df_filtered[
            (df_filtered["Date"] >= x_min) & (df_filtered["Date"] <= x_max)
        ].copy()

        # Calculate the time interval between the first two data points
        time_interval_seconds = (
            df_stats["Date"].iloc[1] - df_stats["Date"].iloc[0]
        ).total_seconds()
        # Calculate total volume of flow in m³
        # Assuming flow values are in liters per second
        total_flow_volume_m3 = (
            df_stats["FlowData"].sum() * time_interval_seconds
        ) / 1000

        df_rgs_stats = df_rgs_filtered[
            (df_rgs_filtered["Date"] >= x_min) & (df_rgs_filtered["Date"] <= x_max)
        ].copy()
        rain_min = df_rgs_stats["IntensityData"].min()
        rain_max = df_rgs_stats["IntensityData"].max()
        rain_range = rain_max - rain_min
        rain_avg = df_rgs_stats["IntensityData"].mean()

        total_rain_depth_mm = df_rgs_stats["RainfallDepth_mm"].sum()

        # Add statistics to the right of the plot
        rain_stats_text = f"Min: {rain_min:.2f}\nMax: {rain_max:.2f}\nRange: {rain_range:.2f}\nAverage: {rain_avg:.2f}\nDepth (mm): {total_rain_depth_mm:.1f} mm"
        plot_axis_rg.text(
            1.02,
            0.5,
            rain_stats_text,
            transform=plot_axis_rg.transAxes,
            verticalalignment="center",
        )

        # Plotting Flow vs Date
        flow_min = df_filtered["FlowData"].min()
        flow_max = df_filtered["FlowData"].max()
        flow_range = flow_max - flow_min
        flow_avg = df_filtered["FlowData"].mean()

        # Add statistics to the right of the plot
        flow_stats_text = f"Min: {flow_min:.2f}\nMax: {flow_max:.2f}\nRange: {flow_range:.2f}\nAverage: {flow_avg:.2f}\nTotal Volume: {total_flow_volume_m3:.1f} m³"
        plot_axis_flow.text(
            1.02,
            0.5,
            flow_stats_text,
            transform=plot_axis_flow.transAxes,
            verticalalignment="center",
        )

        # Plotting Depth vs Date
        depth_min = df_filtered["DepthData"].min()
        depth_max = df_filtered["DepthData"].max()
        depth_range = depth_max - depth_min
        depth_avg = df_filtered["DepthData"].mean()

        # Add statistics to the right of the plot
        plot_axis_depth.text(
            1.02,
            0.5,
            f"Min: {depth_min:.2f}\nMax: {depth_max:.2f}\nRange: {depth_range:.2f}\nAverage: {depth_avg:.2f}",
            transform=plot_axis_depth.transAxes,
            verticalalignment="center",
        )

        # Plotting Velocity vs Date
        velocity_min = df_filtered["VelocityData"].min()
        velocity_max = df_filtered["VelocityData"].max()
        velocity_range = velocity_max - velocity_min
        velocity_avg = df_filtered["VelocityData"].mean()

        # Add statistics to the right of the plot
        plot_axis_velocity.text(
            1.02,
            0.5,
            f"Min: {velocity_min:.2f}\nMax: {velocity_max:.2f}\nRange: {velocity_range:.2f}\nAverage: {velocity_avg:.2f}",
            transform=plot_axis_velocity.transAxes,
            verticalalignment="center",
        )

        self.a_plot_widget.figure.subplots_adjust(
            left=0.15, right=0.85, bottom=0.15, top=0.85
        )
        self.a_plot_widget.figure.tight_layout()

        # Add header and footer
        self.a_plot_widget.figure.text(
            0.95,
            0.95,
            f"FDV Plot: {self.current_inst.client_ref}",
            ha="right",
            fontsize=16,
        )
        self.a_plot_widget.figure.text(
            0.5, 0.02, self.footer_text, ha="center", fontsize=12
        )

        # Add an image to the header
        im = Image.open(resource_path(f"resources/{rps_or_tt}_logo_report.png"))
        aspect_ratio = im.width / im.height
        desired_height_inch = 0.5
        desired_width_inch = desired_height_inch * aspect_ratio
        fig_dpi = self.a_plot_widget.figure.get_dpi()
        desired_width_px = int(desired_width_inch * fig_dpi)
        desired_height_px = int(desired_height_inch * fig_dpi)
        # Resize the image to fit in the header
        im = im.resize((desired_width_px, desired_height_px))
        imagebox = OffsetImage(im)
        ab = AnnotationBbox(
            imagebox, (0.1, 0.95), frameon=False, xycoords="figure fraction"
        )
        self.a_plot_widget.figure.add_artist(ab)

        # Adjust layout
        self.a_plot_widget.figure.subplots_adjust(
            left=0.15, right=0.85, bottom=0.15, top=0.85
        )

        # Show plot
        plt.show()


class graph_fsm_dwf_plot:

    def __init__(
        self,
        a_pw: PlotWidget,
        a_install: fsmInstall,
        a_project: fsmProject,
        start_date: datetime,
        end_date: datetime,
        footer_text: str = "",
    ):
        self.a_plot_widget: PlotWidget = a_pw
        self.a_project: fsmProject = a_project
        self.current_inst: fsmInstall = a_install
        self.footer_text: str = footer_text
        self.start_date: datetime = start_date
        self.end_date: datetime = end_date

    def update_plot(self):

        self.a_plot_widget.figure.clear()

        a_linewidth = 0.5

        i_soffit_mm = self.current_inst.fm_pipe_height_mm

        df_filtered = self.current_inst.data[
            (self.current_inst.data["Date"] >= self.start_date)
            & (self.current_inst.data["Date"] <= self.end_date)
        ].copy()
        # df_compare = self.current_inst.data.copy()

        # Initialize an empty list to collect daily rainfall data
        all_daily_rainfall = []

        dwf_threshold = 0
        preceeding_dry_days = 0

        # Assuming self.a_project.dict_fsm_installs is a dictionary of instances
        for a_inst in self.a_project.dict_fsm_installs.values():
            if a_inst.install_type == "Rain Gauge":
                # Copy relevant data
                df_dwf = a_inst.data[["Date", "IntensityData"]].copy()
                # df_dwf['Date'] = pd.to_datetime(df_dwf['Date'])
                # Convert intensity from mm/hr to mm per interval (assuming a_inst.data_interval is in minutes)
                df_dwf["RainfallDepth_mm"] = df_dwf["IntensityData"] * (
                    a_inst.data_interval / 60
                )
                # Extract date (day) part for grouping
                df_dwf["Day"] = df_dwf["Date"].dt.date
                # Group by 'Day' and sum the 'RainfallDepth_mm'
                daily_rainfall = (
                    df_dwf.groupby("Day")["RainfallDepth_mm"].sum().reset_index()
                )
                # Rename columns for clarity
                daily_rainfall.columns = ["Date", "TotalRainfallDepth_mm"]
                #         # Add instance name to distinguish between different instances
                # Assuming each instance has a unique name
                daily_rainfall["Instance"] = a_inst.install_id
                #         # Append the daily rainfall data to the list
                all_daily_rainfall.append(daily_rainfall)
        # # Combine all daily rainfall data into a single dataframe
        combined_daily_rainfall = pd.concat(all_daily_rainfall)
        # # Group by date and sum the rainfall depths from all instances
        total_daily_rainfall = (
            combined_daily_rainfall.groupby("Date")["TotalRainfallDepth_mm"]
            .sum()
            .reset_index()
        )
        # # Filter out the days where the total rainfall depth exceeds the threshold
        # filtered_daily_rainfall = total_daily_rainfall[total_daily_rainfall['TotalRainfallDepth_mm'] <= dwf_threshold]

        dry_days = []

        for i in range(len(total_daily_rainfall)):
            if i < preceeding_dry_days:
                is_dry = (
                    False  # If there are not enough preceding days, mark as not dry
                )
            else:
                # Check if the previous 'preceeding_dry_days' days are dry
                preceding_days = total_daily_rainfall.iloc[i - preceeding_dry_days : i]
                is_dry = all(
                    preceding_days["TotalRainfallDepth_mm"] <= dwf_threshold
                ) & (
                    total_daily_rainfall["TotalRainfallDepth_mm"].iloc[i]
                    <= dwf_threshold
                )
            dry_days.append(is_dry)

        # Create a new dataframe with only the days that meet the criteria
        dry_days_df = total_daily_rainfall[dry_days]

        if self.current_inst.install_type == "Flow Monitor":
            # flow_monitor_data = self.current_inst.data.copy()  # Make a copy of the data
            flow_monitor_data = df_filtered.copy()  # Make a copy of the data

            flow_monitor_data = flow_monitor_data[flow_monitor_data["FlowData"] != 0]

            # Filter flow monitor data to include only dry days
            flow_monitor_data["Date"] = pd.to_datetime(flow_monitor_data["Date"])
            flow_monitor_data["Day"] = flow_monitor_data["Date"].dt.date
            flow_monitor_data = flow_monitor_data[
                flow_monitor_data["Day"].isin(dry_days_df["Date"])
            ]

            # Remove date information and keep only time part
            flow_monitor_data["TimeOfDay"] = flow_monitor_data["Date"].dt.time

            # Group by time and calculate the average flow, velocity, and depth for each time point
            avg_dwf_per_time = (
                flow_monitor_data.groupby("TimeOfDay")
                .agg({"FlowData": "mean", "DepthData": "mean", "VelocityData": "mean"})
                .reset_index()
            )

            # Rename the columns for clarity
            avg_dwf_per_time.columns = [
                "TimeOfDay",
                "AvgFlowData",
                "AvgDepthData",
                "AvgVelocityData",
            ]

            # Optional: sort by time if needed
            avg_dwf_per_time = avg_dwf_per_time.sort_values(by="TimeOfDay").reset_index(
                drop=True
            )

            df_dwf_filtered = pd.merge(
                flow_monitor_data, avg_dwf_per_time, on="TimeOfDay", how="right"
            )

            df_dwf_filtered["TimeOfDay"] = (
                df_dwf_filtered["Date"].dt.hour * 3600
                + df_dwf_filtered["Date"].dt.minute * 60
                + df_dwf_filtered["Date"].dt.second
            )

            df_dwf_average = df_dwf_filtered.drop_duplicates(
                subset=["TimeOfDay", "AvgFlowData", "AvgDepthData", "AvgVelocityData"]
            )

            flow_monitor_data = self.current_inst.data.copy()

            flow_monitor_data = flow_monitor_data[flow_monitor_data["FlowData"] != 0]

            # Filter flow monitor data to include only dry days
            flow_monitor_data["Date"] = pd.to_datetime(flow_monitor_data["Date"])
            flow_monitor_data["Day"] = flow_monitor_data["Date"].dt.date
            flow_monitor_data = flow_monitor_data[
                flow_monitor_data["Day"].isin(dry_days_df["Date"])
            ]

            # Remove date information and keep only time part
            flow_monitor_data["TimeOfDay"] = flow_monitor_data["Date"].dt.time

            # Group by time and calculate the average flow, velocity, and depth for each time point
            avg_dwf_per_time = (
                flow_monitor_data.groupby("TimeOfDay")
                .agg({"FlowData": "mean", "DepthData": "mean", "VelocityData": "mean"})
                .reset_index()
            )

            # Rename the columns for clarity
            avg_dwf_per_time.columns = [
                "TimeOfDay",
                "AvgFlowData",
                "AvgDepthData",
                "AvgVelocityData",
            ]

            # Optional: sort by time if needed
            avg_dwf_per_time = avg_dwf_per_time.sort_values(by="TimeOfDay").reset_index(
                drop=True
            )

            df_dwf_compare = pd.merge(
                flow_monitor_data, avg_dwf_per_time, on="TimeOfDay", how="right"
            )

            df_dwf_compare["TimeOfDay"] = (
                df_dwf_compare["Date"].dt.hour * 3600
                + df_dwf_compare["Date"].dt.minute * 60
                + df_dwf_compare["Date"].dt.second
            )

            df_dwf_compare_average = df_dwf_compare.drop_duplicates(
                subset=["TimeOfDay", "AvgFlowData", "AvgDepthData", "AvgVelocityData"]
            )

        # Create a figure and subplots
        (plot_axis_flow, plot_axis_depth, plot_axis_velocity) = (
            self.a_plot_widget.figure.subplots(
                nrows=3, sharex=True, gridspec_kw={"height_ratios": [1, 1, 1]}
            )
        )

        if df_dwf_filtered.empty:
            plot_axis_flow.text(
                0.5,
                0.5,
                "No dry day data identified",
                horizontalalignment="center",
                verticalalignment="center",
                fontsize=16,
            )
            plot_axis_flow.set_axis_off()  # Hide the axes
            plot_axis_depth.text(
                0.5,
                0.5,
                "No dry day data identified",
                horizontalalignment="center",
                verticalalignment="center",
                fontsize=16,
            )
            plot_axis_depth.set_axis_off()  # Hide the axes
            plot_axis_velocity.text(
                0.5,
                0.5,
                "No dry day data identified",
                horizontalalignment="center",
                verticalalignment="center",
                fontsize=16,
            )
            plot_axis_velocity.set_axis_off()  # Hide the axes
        else:
            # Group the data by day
            grouped = df_dwf_filtered.groupby(df_dwf_filtered["Date"].dt.date)

            for day, group in grouped:
                # Plot Flow vs Time of Day
                plot_axis_flow.plot(
                    group["TimeOfDay"],
                    group["FlowData"],
                    color="lightblue",
                    linewidth=a_linewidth,
                )

                # Plot Depth vs Time of Day
                plot_axis_depth.plot(
                    group["TimeOfDay"],
                    group["DepthData"],
                    color="lightsalmon",
                    linewidth=a_linewidth,
                )

                # Plot Velocity vs Time of Day
                plot_axis_velocity.plot(
                    group["TimeOfDay"],
                    group["VelocityData"],
                    color="palegreen",
                    linewidth=a_linewidth,
                )

            plot_axis_depth.plot(
                df_dwf_average["TimeOfDay"],
                [i_soffit_mm] * len(df_dwf_average),
                color="darkblue",
                linestyle="--",
                label="Soffit",
                linewidth=a_linewidth,
            )
            # plot_axis_flow.plot(df_compare['Date'], df_compare['FlowData'], color='grey', linewidth=a_linewidth)
            plot_axis_flow.plot(
                df_dwf_average["TimeOfDay"],
                df_dwf_average["AvgFlowData"],
                color="blue",
                linewidth=a_linewidth,
            )
            plot_axis_depth.plot(
                df_dwf_average["TimeOfDay"],
                df_dwf_average["AvgDepthData"],
                color="red",
                linewidth=a_linewidth,
            )
            plot_axis_velocity.plot(
                df_dwf_average["TimeOfDay"],
                df_dwf_average["AvgVelocityData"],
                color="green",
                linewidth=a_linewidth,
            )

            # Add labels and titles
            plot_axis_flow.set_ylabel("Flow (l/sec)")
            plot_axis_flow.set_title("Flow", loc="left", fontsize=16)

            plot_axis_depth.set_ylabel("Depth (mm)")
            plot_axis_depth.set_title("Depth", loc="left", fontsize=16)
            plot_axis_depth.text(
                df_dwf_average["TimeOfDay"].iloc[0],
                i_soffit_mm - 10,
                f"Soffit Height = {i_soffit_mm}mm",
                color="darkblue",
                verticalalignment="top",
                horizontalalignment="left",
            )

            plot_axis_velocity.set_ylabel("Velocity (m/sec)")
            plot_axis_velocity.set_title("Velocity", loc="left", fontsize=16)
            plot_axis_velocity.set_xlabel("Time of Day")

            # Add statistics text (optional)
            flow_min = df_dwf_average["AvgFlowData"].min()
            flow_max = df_dwf_average["AvgFlowData"].max()
            flow_range = flow_max - flow_min
            flow_avg = df_dwf_average["AvgFlowData"].mean()
            total_flow_volume_m3 = (flow_avg * (24 * 60 * 60)) / 1000
            plot_axis_flow.text(
                1.02,
                0.5,
                f"Min: {flow_min:.2f}\nMax: {flow_max:.2f}\nRange: {flow_range:.2f}\nAverage: {flow_avg:.2f}\nTotal Volume: {total_flow_volume_m3:.1f} m³",
                transform=plot_axis_flow.transAxes,
                verticalalignment="center",
            )

            depth_min = df_dwf_average["AvgDepthData"].min()
            depth_max = df_dwf_average["AvgDepthData"].max()
            depth_range = depth_max - depth_min
            depth_avg = df_dwf_average["AvgDepthData"].mean()
            plot_axis_depth.text(
                1.02,
                0.5,
                f"Min: {depth_min:.2f}\nMax: {depth_max:.2f}\nRange: {depth_range:.2f}\nAverage: {depth_avg:.2f}",
                transform=plot_axis_depth.transAxes,
                verticalalignment="center",
            )

            velocity_min = df_dwf_average["AvgVelocityData"].min()
            velocity_max = df_dwf_average["AvgVelocityData"].max()
            velocity_range = velocity_max - velocity_min
            velocity_avg = df_dwf_average["AvgVelocityData"].mean()
            plot_axis_velocity.text(
                1.02,
                0.5,
                f"Min: {velocity_min:.2f}\nMax: {velocity_max:.2f}\nRange: {velocity_range:.2f}\nAverage: {velocity_avg:.2f}",
                transform=plot_axis_velocity.transAxes,
                verticalalignment="center",
            )

        self.a_plot_widget.figure.subplots_adjust(
            left=0.15, right=0.85, bottom=0.15, top=0.85
        )
        self.a_plot_widget.figure.tight_layout()

        # Add header and footer
        self.a_plot_widget.figure.text(
            0.95,
            0.95,
            f"FDV Plot: {self.current_inst.client_ref}",
            ha="right",
            fontsize=16,
        )
        self.a_plot_widget.figure.text(
            0.5, 0.02, self.footer_text, ha="center", fontsize=12
        )

        # Add an image to the header
        im = Image.open(resource_path(f"resources/{rps_or_tt}_logo_report.png"))
        aspect_ratio = im.width / im.height
        desired_height_inch = 0.5
        desired_width_inch = desired_height_inch * aspect_ratio
        fig_dpi = self.a_plot_widget.figure.get_dpi()
        desired_width_px = int(desired_width_inch * fig_dpi)
        desired_height_px = int(desired_height_inch * fig_dpi)
        # Resize the image to fit in the header
        im = im.resize((desired_width_px, desired_height_px))
        imagebox = OffsetImage(im)
        ab = AnnotationBbox(
            imagebox, (0.1, 0.95), frameon=False, xycoords="figure fraction"
        )
        self.a_plot_widget.figure.add_artist(ab)

        # Adjust layout
        self.a_plot_widget.figure.subplots_adjust(
            left=0.15, right=0.85, bottom=0.15, top=0.85
        )

        # Show plot
        plt.show()


class graph_fsm_scatter_plot:

    def __init__(
        self,
        a_pw: PlotWidget,
        a_install: fsmInstall,
        a_project: fsmProject,
        start_date: datetime,
        end_date: datetime,
        footer_text: str = "",
    ):
        self.a_plot_widget: PlotWidget = a_pw
        self.a_project: fsmProject = a_project
        self.current_inst: fsmInstall = a_install
        self.footer_text: str = footer_text
        self.start_date: datetime = start_date
        self.end_date: datetime = end_date

    def update_plot(self):

        self.a_plot_widget.figure.clear()

        a_linewidth = 0.5

        i_soffit_mm = self.current_inst.fm_pipe_height_mm

        df_filtered = self.current_inst.data[
            (self.current_inst.data["Date"] >= self.start_date)
            & (self.current_inst.data["Date"] <= self.end_date)
        ].copy()

        # Filter out invalid pairs
        valid_pairs_mask = (df_filtered["FlowData"] > 0) & (
            df_filtered["DepthData"] > 0
        )
        valid_fdv_data = df_filtered[valid_pairs_mask]

        # Category 1: Anything below 100mm likely affected by poor flow conditions
        cat_1_val = np.log(100)
        cat_1_text = (
            "Cat.1: <100mm (Data probably inacurate due to poor flow conditions)"
        )

        # Category 2: Anything below 150mm or 20% of sewer height (whichever is greater) is likely to show large scatter
        if 150 >= (0.2 * i_soffit_mm):
            cat_2_val = np.log(150)
            cat_2_text = "Cat.2: <150mm (Large scatter of data)"
        else:
            cat_2_val = np.log(0.2 * i_soffit_mm)
            cat_2_text = "Cat.2: <20% of sewer height (Large scatter of data)"

        # Category 3: Anything below 225mm or 30% of sewer height (whichever is greater) is likely to show some scatter
        if 225 >= (0.3 * i_soffit_mm):
            cat_3_val = np.log(225)
            cat_3_text = "Cat.3: <225mm (Scatter of data gradually reduce)"
        else:
            cat_3_val = np.log(0.3 * i_soffit_mm)
            cat_3_text = (
                "Cat.3: <30% of sewer height (Scatter of data gradually reduce)"
            )

        # Category 4: Anything below 50% of sewer height is likely to show very little scatter
        cat_4_val = np.log(0.5 * i_soffit_mm)
        cat_4_text = "Cat.4: <50% of sewer height (Very little scatter of data)"

        # Category 4: Anything below 50% of sewer height is likely to show very little scatter
        cat_5_val = np.log(i_soffit_mm)
        cat_5_text = "Cat.5: Sewer Height (Minimal scatter of data)"

        if not valid_fdv_data.empty:
            # Log-transformed data of valid pairs
            log_flow = np.log(valid_fdv_data["FlowData"])
            log_depth = np.log(valid_fdv_data["DepthData"])

            gs = self.a_plot_widget.figure.add_gridspec(1, 2, width_ratios=[40, 1])
            plot_axis_scatter = self.a_plot_widget.figure.add_subplot(gs[0, 0])
            cbar_ax = self.a_plot_widget.figure.add_subplot(gs[0, 1])

            # Plot the primary dataset with the common norm
            hb = plot_axis_scatter.hexbin(
                log_flow, log_depth, gridsize=40, cmap="GnBu", norm=mcolors.LogNorm()
            )

            cb = self.a_plot_widget.figure.colorbar(hb, cax=cbar_ax, format="%d")
            cb.set_label("Counts", color="blue")
            cb.ax.yaxis.set_tick_params(color="blue")
            plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color="blue")

            plot_axis_scatter.plot(
                [log_flow.min(), log_flow.max()],
                [np.log(i_soffit_mm), np.log(i_soffit_mm)],
                color="darkblue",
                linestyle="--",
                label="Soffit",
                linewidth=a_linewidth,
            )
            plot_axis_scatter.text(
                log_flow.min(),
                np.log(i_soffit_mm),
                "Soffit",
                color="darkblue",
                verticalalignment="bottom",
                horizontalalignment="left",
            )

            plot_axis_scatter.plot(
                [log_flow.min(), log_flow.max()],
                [cat_1_val, cat_1_val],
                color="red",
                linestyle="--",
                label=cat_1_text,
                linewidth=a_linewidth,
            )
            plot_axis_scatter.text(
                log_flow.min(),
                cat_1_val,
                cat_1_text,
                color="red",
                verticalalignment="top",
                horizontalalignment="left",
            )

            if cat_2_val > cat_1_val:
                plot_axis_scatter.plot(
                    [log_flow.min(), log_flow.max()],
                    [cat_2_val, cat_2_val],
                    color="red",
                    linestyle="--",
                    label=cat_2_text,
                    linewidth=a_linewidth,
                )
                plot_axis_scatter.text(
                    log_flow.min(),
                    cat_2_val,
                    cat_2_text,
                    color="red",
                    verticalalignment="top",
                    horizontalalignment="left",
                )

            if cat_3_val > cat_2_val and cat_3_val > cat_1_val:
                plot_axis_scatter.plot(
                    [log_flow.min(), log_flow.max()],
                    [cat_3_val, cat_3_val],
                    color="red",
                    linestyle="--",
                    label=cat_3_text,
                    linewidth=a_linewidth,
                )
                plot_axis_scatter.text(
                    log_flow.min(),
                    cat_3_val,
                    cat_3_text,
                    color="red",
                    verticalalignment="top",
                    horizontalalignment="left",
                )

            if (
                cat_4_val > cat_3_val
                and cat_4_val > cat_2_val
                and cat_4_val > cat_1_val
            ):
                plot_axis_scatter.plot(
                    [log_flow.min(), log_flow.max()],
                    [cat_4_val, cat_4_val],
                    color="red",
                    linestyle="--",
                    label=cat_4_text,
                    linewidth=a_linewidth,
                )
                plot_axis_scatter.text(
                    log_flow.min(),
                    cat_4_val,
                    cat_4_text,
                    color="red",
                    verticalalignment="top",
                    horizontalalignment="left",
                )

            if (
                cat_5_val > cat_4_val
                and cat_5_val > cat_3_val
                and cat_5_val > cat_2_val
                and cat_5_val > cat_1_val
            ):
                plot_axis_scatter.plot(
                    [log_flow.min(), log_flow.max()],
                    [cat_5_val, cat_5_val],
                    color="red",
                    linestyle="--",
                    label=cat_5_text,
                    linewidth=a_linewidth,
                )
                plot_axis_scatter.text(
                    log_flow.min(),
                    cat_5_val,
                    cat_5_text,
                    color="red",
                    verticalalignment="top",
                    horizontalalignment="left",
                )

            plot_axis_scatter.set_title("2D Histogram of Log Flow vs Log Depth")
            plot_axis_scatter.set_xlabel("Log Flow")
            plot_axis_scatter.set_ylabel("Log Depth")

            # Get existing x-axis ticks (now they are integer positions), convert them to non-log values, and set as labels
            x_ticks = plot_axis_scatter.get_xticks()
            x_labels = [f"{np.exp(value):.1f}" for value in x_ticks]
            plot_axis_scatter.set_xticklabels(x_labels)

            # Get existing y-axis ticks (now they are integer positions), convert them to non-log values, and set as labels
            y_ticks = plot_axis_scatter.get_yticks()
            y_labels = [f"{int(np.round(np.exp(value)))}" for value in y_ticks]
            plot_axis_scatter.set_yticklabels(y_labels)

        else:
            ax = self.a_plot_widget.figure.subplots()
            ax.text(
                0.5,
                0.5,
                "No valid data",
                horizontalalignment="center",
                verticalalignment="center",
                fontsize=16,
            )
            ax.set_axis_off()  # Hide the axes

        self.a_plot_widget.figure.subplots_adjust(
            left=0.15, right=0.85, bottom=0.15, top=0.85
        )
        self.a_plot_widget.figure.tight_layout()

        # Add header and footer
        self.a_plot_widget.figure.text(
            0.95,
            0.95,
            f"Scatter Plot: {self.current_inst.client_ref}",
            ha="right",
            fontsize=16,
        )
        self.a_plot_widget.figure.text(
            0.5, 0.02, self.footer_text, ha="center", fontsize=12
        )

        # Add an image to the header
        im = Image.open(resource_path(f"resources/{rps_or_tt}_logo_report.png"))
        aspect_ratio = im.width / im.height
        desired_height_inch = 0.5
        desired_width_inch = desired_height_inch * aspect_ratio
        fig_dpi = self.a_plot_widget.figure.get_dpi()
        desired_width_px = int(desired_width_inch * fig_dpi)
        desired_height_px = int(desired_height_inch * fig_dpi)
        # Resize the image to fit in the header
        im = im.resize((desired_width_px, desired_height_px))
        imagebox = OffsetImage(im)
        ab = AnnotationBbox(
            imagebox, (0.1, 0.95), frameon=False, xycoords="figure fraction"
        )
        self.a_plot_widget.figure.add_artist(ab)

        # Adjust layout
        self.a_plot_widget.figure.subplots_adjust(
            left=0.15, right=0.85, bottom=0.15, top=0.85
        )

        # Show plot
        plt.show()


class graphFSMInstall:

    main_window_plot_widget: PlotWidget = None
    isBlank = True

    def __init__(self, mw_pw: PlotWidget = None):

        self.main_window_plot_widget = mw_pw
        # self.plotted_installs: plottedInstalls = plottedInstalls()
        self.plotted_install: fsmInstall = None
        self.plotted_raw: fsmRawData = None
        self.plot_raw = False
        getBlankFigure(self.main_window_plot_widget)
        self.isBlank = True
        self.update_plot()

    def update_plot(self, plot_raw: bool = False, plot_adjustments: bool = False):
        self.main_window_plot_widget.figure.clear()
        self.plot_raw = plot_raw
        self.plot_adjustments = plot_adjustments
        if not self.plotted_install is None:
            # if len(self.plotted_installs.plotInstalls) > 0:
            if self.plotted_install.install_type == "Flow Monitor":
                self.createFMPlot()
            elif self.plotted_install.install_type == "Rain Gauge":
                self.createRGPlot()
            elif self.plotted_install.install_type == "Pump Logger":
                self.createPLPlot()
            self.isBlank = False
        else:
            getBlankFigure(self.main_window_plot_widget)
            self.isBlank = True

        self.updateCanvas()

    def updateCanvas(self):
        self.main_window_plot_widget.showToolbar(not self.isBlank)

    def createRGPlot(self):

        a_linewidth = 1
        if self.plot_raw:

            (plot_axis_battery, plot_axis_intensity) = (
                self.main_window_plot_widget.figure.subplots(
                    nrows=2, sharex=True, gridspec_kw={"height_ratios": [1, 1]}
                )
            )

            if self.plotted_raw is not None and self.plotted_raw.bat_data is not None:
                plot_axis_battery.plot(
                    self.plotted_raw.bat_data["Timestamp"],
                    self.plotted_raw.bat_data["Value"],
                    color="blue",
                    linewidth=a_linewidth,
                )
            plot_axis_battery.set_ylabel("Voltage (V)")
            plot_axis_battery.set_title("Battery", loc="left", fontsize=16)

            if self.plotted_raw is not None and self.plotted_raw.rg_data is not None:
                plot_axis_intensity.stem(
                    self.plotted_raw.rg_data["Timestamp"],
                    [1] * len(self.plotted_raw.rg_data["Timestamp"]),
                )
                # plot_axis_intensity.plot(
                #     self.plotted_raw.rg_data["Timestamp"],
                #     [1] * len(self.plotted_raw.rg_data["Timestamp"]),
                #     color="green",
                #     linewidth=a_linewidth,
                # )
            plot_axis_intensity.set_ylabel("Tips")
            plot_axis_intensity.set_title("Rainfall", loc="left", fontsize=16)

            locator = AutoDateLocator(minticks=6, maxticks=15)
            formatter = ConciseDateFormatter(locator)
            plot_axis_intensity.xaxis.set_major_locator(locator)
            plot_axis_intensity.xaxis.set_major_formatter(formatter)

            self.main_window_plot_widget.figure.tight_layout()
            # Adjust layout
            self.main_window_plot_widget.figure.subplots_adjust(
                left=0.075, right=0.95, bottom=0.05, top=0.95
            )
            # Redraw the figure to ensure all changes are visible
            self.main_window_plot_widget.figure.canvas.draw()

        else:

            (plot_axis_intensity) = self.main_window_plot_widget.figure.subplots(
                nrows=1, sharex=True, gridspec_kw={"height_ratios": [1]}
            )

            if self.plotted_install.data is not None:
                df_filtered = self.plotted_install.data.copy()

                plot_axis_intensity.plot(
                    df_filtered["Date"],
                    df_filtered["IntensityData"],
                    color="darkblue",
                    linewidth=a_linewidth,
                )
            plot_axis_intensity.set_ylabel("Intensity (mm/hr)")
            plot_axis_intensity.set_title("Rainfall", loc="left", fontsize=16)

            locator = AutoDateLocator(minticks=6, maxticks=15)
            formatter = ConciseDateFormatter(locator)
            plot_axis_intensity.xaxis.set_major_locator(locator)
            plot_axis_intensity.xaxis.set_major_formatter(formatter)

            # self.main_window_plot_widget.figure.subplots_adjust(
            #     left=0.15, right=0.85, bottom=0.15, top=0.85)
            self.main_window_plot_widget.figure.tight_layout()

            # Adjust layout
            self.main_window_plot_widget.figure.subplots_adjust(
                left=0.075, right=0.95, bottom=0.05, top=0.95
            )
            # Redraw the figure to ensure all changes are visible
            self.main_window_plot_widget.figure.canvas.draw()

    def createFMPlot(self):

        a_linewidth = 1
        if self.plot_raw:
            if self.plotted_raw is None:
                ax = self.main_window_plot_widget.figure.subplots()
                ax.text(0.5, 0.5, 'No raw data found', horizontalalignment='center', verticalalignment='center', fontsize=16)
                ax.set_axis_off()  # Hide the axes
                return
            
            else:
                (plot_axis_battery, plot_axis_depth, plot_axis_velocity) = (
                    self.main_window_plot_widget.figure.subplots(
                        nrows=3, sharex=True, gridspec_kw={"height_ratios": [1, 1, 1]}
                    )
                )
            
                if self.plotted_raw.bat_data is not None:
                    plot_axis_battery.plot(
                        self.plotted_raw.bat_data["Timestamp"],
                        self.plotted_raw.bat_data["Value"],
                        color="blue",
                        linewidth=a_linewidth,
                    )
                else:
                    plot_axis_battery.text(0.5, 0.5, 'No battery data found', horizontalalignment='center', verticalalignment='center', fontsize=16)
                plot_axis_battery.set_ylabel("Voltage (V)")
                plot_axis_battery.set_title("Battery", loc="left", fontsize=16)

                if self.plotted_raw.dep_data is not None:
                    plot_axis_depth.plot(
                        self.plotted_raw.dep_data["Timestamp"],
                        self.plotted_raw.dep_data["Value"],
                        color="red",
                        linewidth=a_linewidth,
                    )
                else:
                    plot_axis_depth.text(0.5, 0.5, 'No depth data found', horizontalalignment='center', verticalalignment='center', fontsize=16)
                plot_axis_depth.set_ylabel("Depth (m)")
                plot_axis_depth.set_title("Depth", loc="left", fontsize=16)

                if self.plotted_raw.vel_data is not None:
                    plot_axis_velocity.plot(
                        self.plotted_raw.vel_data["Timestamp"],
                        self.plotted_raw.vel_data["Value"],
                        color="green",
                        linewidth=a_linewidth,
                    )
                else:
                    plot_axis_velocity.text(0.5, 0.5, 'No velocity data found', horizontalalignment='center', verticalalignment='center', fontsize=16)
                plot_axis_velocity.set_ylabel("Velocity (m/sec)")
                plot_axis_velocity.set_title("Velocity", loc="left", fontsize=16)

                if self.plot_adjustments:
                    calculator = MonitorDataFlowCalculator(self.plotted_raw)

                    if (
                        self.plotted_raw.dep_data is not None
                        and self.plotted_raw.vel_data is not None
                    ):
                        # Extract data from raw inputs
                        timestamps = pd.to_datetime(self.plotted_raw.dep_data["Timestamp"])
                        original_depths = self.plotted_raw.dep_data["Value"].values
                        original_velocities = self.plotted_raw.vel_data["Value"].values

                        corrected_timestamps = calculator.apply_timing_corrections(
                            timestamps
                        )
                        corrected_depths = calculator.calculate_corrected_depth(
                            original_depths, corrected_timestamps
                        )
                        corrected_velocities = calculator.calculate_corrected_velocities(
                            original_velocities, corrected_timestamps
                        )
                        silt_depths = np.zeros(len(corrected_timestamps))
                        if self.plotted_raw.silt_levels is not None:
                            # Extract and rename necessary columns
                            silt_data_df = self.plotted_raw.silt_levels[
                                ["DateTime", "FloatValue"]
                            ].rename(columns={"FloatValue": "correction"})
                        silt_depths = calculator._interpolate_correction_data(
                            silt_data_df, corrected_timestamps
                        )
                        # Convert from mm to m
                        silt_depths = silt_depths / 1000

                        plot_axis_depth.plot(
                            corrected_timestamps,
                            silt_depths,
                            color="orange",
                            linewidth=a_linewidth,
                            linestyle=(0, (5, 10)),
                        )
                        plot_axis_depth.plot(
                            corrected_timestamps,
                            corrected_depths,
                            color="red",
                            linewidth=a_linewidth,
                            linestyle=(0, (5, 10)),
                        )

                        plot_axis_velocity.plot(
                            corrected_timestamps,
                            corrected_velocities,
                            color="green",
                            linewidth=a_linewidth,
                            linestyle=(0, (5, 10)),
                        )

            locator = AutoDateLocator(minticks=6, maxticks=15)
            formatter = ConciseDateFormatter(locator)
            plot_axis_velocity.xaxis.set_major_locator(locator)
            plot_axis_velocity.xaxis.set_major_formatter(formatter)

            # self.main_window_plot_widget.figure.subplots_adjust(
            #     left=0.15, right=0.85, bottom=0.15, top=0.85)
            self.main_window_plot_widget.figure.tight_layout()

            # Adjust layout
            self.main_window_plot_widget.figure.subplots_adjust(
                left=0.075, right=0.95, bottom=0.05, top=0.95
            )
            # Redraw the figure to ensure all changes are visible
            self.main_window_plot_widget.figure.canvas.draw()

        else:

            (plot_axis_flow, plot_axis_depth, plot_axis_velocity) = (
                self.main_window_plot_widget.figure.subplots(
                    nrows=3, sharex=True, gridspec_kw={"height_ratios": [1, 1, 1]}
                )
            )

            if self.plotted_install.data is not None:
                df_filtered = self.plotted_install.data.copy()

                plot_axis_flow.plot(
                    df_filtered["Date"],
                    df_filtered["FlowData"],
                    color="blue",
                    linewidth=a_linewidth,
                )
                plot_axis_depth.plot(
                    df_filtered["Date"],
                    df_filtered["DepthData"],
                    color="red",
                    linewidth=a_linewidth,
                )
                plot_axis_velocity.plot(
                    df_filtered["Date"],
                    df_filtered["VelocityData"],
                    color="green",
                    linewidth=a_linewidth,
                )
            else:
                plot_axis_flow.text(0.5, 0.5, 'No flow data found', horizontalalignment='center', verticalalignment='center', fontsize=16)
                plot_axis_depth.text(0.5, 0.5, 'No depth data found', horizontalalignment='center', verticalalignment='center', fontsize=16)
                plot_axis_velocity.text(0.5, 0.5, 'No velocity data found', horizontalalignment='center', verticalalignment='center', fontsize=16)

            plot_axis_flow.set_ylabel("Flow (l/sec)")
            plot_axis_flow.set_title("Flow", loc="left", fontsize=16)

            plot_axis_depth.set_ylabel("Depth (mm)")
            plot_axis_depth.set_title("Depth", loc="left", fontsize=16)

            plot_axis_velocity.set_ylabel("Velocity (m/sec)")
            plot_axis_velocity.set_title("Velocity", loc="left", fontsize=16)

            locator = AutoDateLocator(minticks=6, maxticks=15)
            formatter = ConciseDateFormatter(locator)
            plot_axis_velocity.xaxis.set_major_locator(locator)
            plot_axis_velocity.xaxis.set_major_formatter(formatter)

            # self.main_window_plot_widget.figure.subplots_adjust(
            #     left=0.15, right=0.85, bottom=0.15, top=0.85)
            self.main_window_plot_widget.figure.tight_layout()

            # Adjust layout
            self.main_window_plot_widget.figure.subplots_adjust(
                left=0.075, right=0.95, bottom=0.05, top=0.95
            )
            # Redraw the figure to ensure all changes are visible
            self.main_window_plot_widget.figure.canvas.draw()

    # def createPLPlot(self):

    #     a_linewidth = 1
    #     if self.plot_raw:

    #         (plot_axis_onoff) = (self.main_window_plot_widget.figure.subplots(nrows=1, sharex=True, gridspec_kw={"height_ratios": [1]}))

    #         if self.plotted_raw.pl_data is not None:
    #             plot_axis_onoff.step(
    #                 self.plotted_raw.pl_data["Timestamp"],
    #                 self.plotted_raw.pl_data["Value"],
    #                 where = 'post'
    #                 color="blue",
    #                 linewidth=a_linewidth,
    #             )
    #         plot_axis_onoff.set_ylabel("On/Off")
    #         plot_axis_onoff.set_title("Pump Logger", loc="left", fontsize=16)

    #         locator = AutoDateLocator(minticks=6, maxticks=15)
    #         formatter = ConciseDateFormatter(locator)
    #         plot_axis_onoff.xaxis.set_major_locator(locator)
    #         plot_axis_onoff.xaxis.set_major_formatter(formatter)

    #     else:

    #         (plot_axis_onoff) = (self.main_window_plot_widget.figure.subplots(nrows=1, sharex=True, gridspec_kw={"height_ratios": [1]}))

    #         if self.plotted_install.data is not None:
    #             df_filtered = self.plotted_install.data.copy()
    #             plot_axis_onoff.step(
    #                 df_filtered["Date"],
    #                 df_filtered["OnOffData"],
    #                 where = 'post',
    #                 color="blue",
    #                 linewidth=a_linewidth,
    #             )

    #         plot_axis_onoff.set_ylabel("On/Off")
    #         plot_axis_onoff.set_title("Pump Logger", loc="left", fontsize=16)

    #         locator = AutoDateLocator(minticks=6, maxticks=15)
    #         formatter = ConciseDateFormatter(locator)
    #         plot_axis_onoff.xaxis.set_major_locator(locator)
    #         plot_axis_onoff.xaxis.set_major_formatter(formatter)

    #     self.main_window_plot_widget.figure.tight_layout()
    #     # Adjust layout
    #     self.main_window_plot_widget.figure.subplots_adjust(left=0.075, right=0.95, bottom=0.05, top=0.95)
    #     # Redraw the figure to ensure all changes are visible
    #     self.main_window_plot_widget.figure.canvas.draw()

    def human_readable_duration(self, seconds):
        if seconds < 60:
            return f"{seconds:.0f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.2f} minutes"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            minutes = (seconds % 3600) / 60
            return f"{hours} hours {minutes:.2f} minutes"
        else:
            days = int(seconds // 86400)
            hours = int((seconds % 86400) // 3600)
            minutes = ((seconds % 3600) / 60)
            return f"{days} days {hours} hours {minutes:.2f} minutes"

    def createPLPlot(self):
        a_linewidth = 1
        if self.plot_raw:
            plot_axis_onoff = self.main_window_plot_widget.figure.subplots(
                nrows=1, sharex=True, gridspec_kw={"height_ratios": [1]}
            )
            if self.plotted_raw.pl_data is not None:
                # Use a step plot so that the line remains flat between transitions
                plot_axis_onoff.step(
                    self.plotted_raw.pl_data["Timestamp"],
                    self.plotted_raw.pl_data["Value"],
                    where='post',  # Change to 'pre' or 'mid' if preferred
                    color="blue",
                    linewidth=a_linewidth,
                )
                # For convenience, use a common variable name for the data and the time column.
                measured_data = self.plotted_raw.pl_data.copy()
                time_key = "Timestamp"
                value_key = "Value"
            else:
                return
        else:
            plot_axis_onoff = self.main_window_plot_widget.figure.subplots(
                nrows=1, sharex=True, gridspec_kw={"height_ratios": [1]}
            )
            if self.plotted_install.data is not None:
                df_filtered = self.plotted_install.data.copy()
                plot_axis_onoff.step(
                    df_filtered["Date"],
                    df_filtered["OnOffData"],
                    where='post',
                    color="blue",
                    linewidth=a_linewidth,
                )
                measured_data = df_filtered.copy()
                time_key = "Date"
                value_key = "OnOffData"
            else:
                return

        # Set labels and title
        plot_axis_onoff.set_ylabel("On/Off")
        plot_axis_onoff.set_title("Pump Logger", loc="left", fontsize=16)
        locator = AutoDateLocator(minticks=6, maxticks=15)
        formatter = ConciseDateFormatter(locator)
        plot_axis_onoff.xaxis.set_major_locator(locator)
        plot_axis_onoff.xaxis.set_major_formatter(formatter)

        # Create a statistics text box in the top left (in axis coordinates)
        stats_box = plot_axis_onoff.text(
            0.02, 0.98, "", transform=plot_axis_onoff.transAxes,
            fontsize=10, verticalalignment="top",
            bbox=dict(facecolor="white", alpha=0.5, edgecolor="gray")
        )

        def update_stats(ax):
            # Get the current x-axis limits and convert to datetime
            x_min, x_max = ax.get_xlim()
            # ignore timezone localization that comes from the matplotlib library.  Our data is timezone naive
            start_time = pd.Timestamp(mpl_dates.num2date(x_min)).tz_localize(None)
            end_time = pd.Timestamp(mpl_dates.num2date(x_max)).tz_localize(None)

            # Filter the measured_data to the current x-axis extent.
            # (Assumes the time column is already in datetime format.)
            mask = (measured_data[time_key] >= start_time) & (measured_data[time_key] <= end_time)
            df_visible = measured_data.loc[mask]

            if df_visible.empty:
                stats_str = "No data in view"
            else:
                # Ensure the data is sorted by time.
                df_visible = df_visible.sort_values(time_key)

                # Convert the time column to a NumPy array for easier arithmetic.
                times = df_visible[time_key].to_numpy()
                values = df_visible[value_key].to_numpy()

                # Compute transitions: differences between consecutive values.
                # A difference of 1 indicates a transition from 0 to 1 ("on" event).
                # A difference of -1 indicates a transition from 1 to 0 ("off" event).
                diffs = np.diff(values)
                n_on = int(np.sum(diffs == 1))
                n_off = int(np.sum(diffs == -1))

                # If there's at least one value, add the starting state as an event.
                if len(values) > 0:
                    if values[0] == 1:
                        n_on += 1
                    else:
                        # if the first visible value is off and its the start of the dataset then don't count it as an off
                        if times[0] != measured_data[time_key].iloc[0]:
                            n_off += 1                

                # Assume start_time and end_time are the current visible x-axis limits (naive datetimes)
                # Assume times is a numpy array of datetime objects (or pandas Timestamps) and
                # values is a numpy array of ints (0 or 1)
                pump_run_seconds = 0

                # Left edge correction:
                if len(times) > 0:
                    # If the first recorded state is OFF and there is measured data before the visible value, add the time from the x-axis left limit to the first timestamp.
                    if values[0] == 0 and measured_data[time_key].iloc[0] < times[0]:
                        # Using np.timedelta64 division for numpy datetime differences:
                        pump_run_seconds += (times[0] - start_time) / np.timedelta64(1, 's')

                # Middle intervals:
                for i in range(len(times) - 1):
                    # Calculate the duration between consecutive timestamps in seconds.
                    # (Assuming times are numpy datetime64 or pandas Timestamp, using np.timedelta64 division works universally.)
                    dt = (times[i+1] - times[i]) / np.timedelta64(1, 's')
                    if values[i] == 1:
                        pump_run_seconds += dt

                # Right edge correction:
                if len(times) > 0:
                    # If the last recorded state is ON and there is measured data after the visible value, add the time from the last timestamp to the x-axis right limit.
                    if values[-1] == 1 and measured_data[time_key].iloc[-1] > times[-1]:
                        pump_run_seconds += (end_time - times[-1]) / np.timedelta64(1, 's')

                # Calculate the visible measured data (pump_log_duration) using the full data:
                data_start = measured_data[time_key].min()
                data_end   = measured_data[time_key].max()
                visible_measurement_start = max(start_time, data_start)
                visible_measurement_end   = min(end_time, data_end)

                if visible_measurement_start < visible_measurement_end:
                    measurement_duration = visible_measurement_end - visible_measurement_start
                else:
                    measurement_duration = datetime.timedelta(0)

                stats_str = (
                    f"{n_on} Ons\n"
                    f"{n_off} Offs\n"
                    f"{self.human_readable_duration(pump_run_seconds)} of runtime\n"
                    f"{self.human_readable_duration(measurement_duration.total_seconds())} measured duration\n"
                    f"{(n_on / (measurement_duration.total_seconds() / (60 * 60))):.2f} activations/hour\n"
                    f"{self.human_readable_duration(pump_run_seconds / n_on) if n_on != 0 else 'Undefined'} avg. runtime per activation"
                )
            # Update the text box
            stats_box.set_text(stats_str)
            # Redraw the canvas for the update to appear
            ax.figure.canvas.draw_idle()

        # Connect the update_stats callback to changes in the x-axis limits.
        # Whenever the view is updated (e.g. via zooming/panning), update_stats is called.
        plot_axis_onoff.callbacks.connect('xlim_changed', lambda ax: update_stats(ax))

        # Call update_stats once to initialize the statistics box.
        update_stats(plot_axis_onoff)

        # Adjust layout and redraw the figure
        self.main_window_plot_widget.figure.tight_layout()
        self.main_window_plot_widget.figure.subplots_adjust(left=0.075, right=0.95, bottom=0.05, top=0.95)
        self.main_window_plot_widget.figure.canvas.draw()    

class graphWQGraph:

    main_window_plot_widget: PlotWidget = None
    isBlank = True

    def __init__(self, mw_pw: PlotWidget = None):

        self.main_window_plot_widget = mw_pw
        getBlankFigure(self.main_window_plot_widget)
        self.isBlank = True
        self.plot_mean: bool = False
        self.freq: str = "Daily"

        self.plotted_wqs: plottedWQMonitors = plottedWQMonitors()
        self.startDate: datetime = datetime.strptime("2172-05-12", "%Y-%m-%d")
        # self.enable_dynamic_y_rescaling()
        self.update_plot()

    def update_plot(self, plot_raw: bool = False, freq: str = "Daily"):

        self.main_window_plot_widget.figure.clear()
        self.plot_raw = plot_raw
        self.freq = freq
        if len(self.plotted_wqs.plotWQs) > 0:
            self.updateAllLines()
            self.isBlank = False
        else:
            getBlankFigure(self.main_window_plot_widget)
            self.isBlank = True

        self.updateCanvas()

    def updateCanvas(self):
        self.main_window_plot_widget.showToolbar(not self.isBlank)
        self.main_window_plot_widget.event_connections.append(self.main_window_plot_widget.figure.canvas.mpl_connect("button_release_event", self.on_zoom_pan_end))

    def updateAllLines(self):
        # Create subplots
        (
            self.plot_axis_cond,
            self.plot_axis_do,
            self.plot_axis_do_sat,
            self.plot_axis_nh4,
            self.plot_axis_ph,
            self.plot_axis_temp,
        ) = self.main_window_plot_widget.figure.subplots(6, 1, sharex=True)

        # List to hold all plotted lines and labels
        lines = []
        labels = []

        for wq in self.plotted_wqs.plotWQs.values():
            added_monitor_line = False

            if self.plot_raw:
                if wq.data_cond is not None:
                    (line_ts,) = self.plot_axis_cond.plot(
                        pd.to_datetime(wq.data_cond["DateTime"]),
                        wq.data_cond.iloc[:, 1],
                        label=wq.monitor_id,
                    )
                    self.plot_axis_cond.set_ylabel("Cond. (mS/cm)")
                    self.plot_axis_cond.grid(True)
                    if not added_monitor_line:
                        lines.append(line_ts)
                        labels.append(wq.monitor_id)
                        added_monitor_line = True

                if wq.data_do is not None:
                    (line_ts,) = self.plot_axis_do.plot(
                        pd.to_datetime(wq.data_do["DateTime"]),
                        wq.data_do.iloc[:, 1],
                        label=wq.monitor_id,
                    )
                    self.plot_axis_do.set_ylabel("DO (mg/L)")
                    self.plot_axis_do.grid(True)
                    if not added_monitor_line:
                        lines.append(line_ts)
                        labels.append(wq.monitor_id)
                        added_monitor_line = True

                if wq.data_do_sat is not None:
                    (line_ts,) = self.plot_axis_do_sat.plot(
                        pd.to_datetime(wq.data_do_sat["DateTime"]),
                        wq.data_do_sat.iloc[:, 1],
                        label=wq.monitor_id,
                    )
                    self.plot_axis_do_sat.set_ylabel("DO Sat (Sat%)")
                    self.plot_axis_do_sat.grid(True)
                    if not added_monitor_line:
                        lines.append(line_ts)
                        labels.append(wq.monitor_id)
                        added_monitor_line = True

                if wq.data_nh4 is not None:
                    (line_ts,) = self.plot_axis_nh4.plot(
                        pd.to_datetime(wq.data_nh4["DateTime"]),
                        wq.data_nh4.iloc[:, 1],
                        label=wq.monitor_id,
                    )
                    self.plot_axis_nh4.set_ylabel("NH4 (mg/L)")
                    self.plot_axis_nh4.grid(True)
                    if not added_monitor_line:
                        lines.append(line_ts)
                        labels.append(wq.monitor_id)
                        added_monitor_line = True

                if wq.data_ph is not None:
                    (line_ts,) = self.plot_axis_ph.plot(
                        pd.to_datetime(wq.data_ph["DateTime"]),
                        wq.data_ph.iloc[:, 1],
                        label=wq.monitor_id,
                    )
                    self.plot_axis_ph.set_ylabel("pH")
                    self.plot_axis_ph.grid(True)
                    if not added_monitor_line:
                        lines.append(line_ts)
                        labels.append(wq.monitor_id)
                        added_monitor_line = True

                if wq.data_temp is not None:
                    (line_ts,) = self.plot_axis_temp.plot(
                        pd.to_datetime(wq.data_temp["DateTime"]),
                        wq.data_temp.iloc[:, 1],
                        label=wq.monitor_id,
                    )
                    self.plot_axis_temp.set_ylabel("Temp (°C)")
                    self.plot_axis_temp.grid(True)
                    if not added_monitor_line:
                        lines.append(line_ts)
                        labels.append(wq.monitor_id)
                        added_monitor_line = True

            else:
                # Resampled data with CI
                if wq.data_cond is not None:
                    data_resample, ci_lower, ci_upper = self.resample_data(
                        wq.data_cond, self.freq
                    )
                    (line_ts,) = self.plot_axis_cond.plot(
                        pd.to_datetime(data_resample["DateTime"]),
                        data_resample.iloc[:, 1],
                        label=wq.monitor_id,
                    )
                    self.plot_axis_cond.fill_between(
                        pd.to_datetime(data_resample["DateTime"]),
                        ci_lower,
                        ci_upper,
                        color=line_ts.get_color(),
                        alpha=0.3,
                    )
                    self.plot_axis_cond.set_ylabel("Cond. (mS/cm)")
                    self.plot_axis_cond.grid(True)
                    if not added_monitor_line:
                        lines.append(line_ts)
                        labels.append(wq.monitor_id)
                        added_monitor_line = True

                if wq.data_do is not None:
                    data_resample, ci_lower, ci_upper = self.resample_data(
                        wq.data_do, self.freq
                    )
                    (line_ts,) = self.plot_axis_do.plot(
                        pd.to_datetime(data_resample["DateTime"]),
                        data_resample.iloc[:, 1],
                        label=wq.monitor_id,
                    )
                    self.plot_axis_do.fill_between(
                        pd.to_datetime(data_resample["DateTime"]),
                        ci_lower,
                        ci_upper,
                        color=line_ts.get_color(),
                        alpha=0.3,
                    )
                    self.plot_axis_do.set_ylabel("DO (mg/L)")
                    self.plot_axis_do.grid(True)
                    if not added_monitor_line:
                        lines.append(line_ts)
                        labels.append(wq.monitor_id)
                        added_monitor_line = True

                if wq.data_do_sat is not None:
                    data_resample, ci_lower, ci_upper = self.resample_data(
                        wq.data_do_sat, self.freq
                    )
                    (line_ts,) = self.plot_axis_do_sat.plot(
                        pd.to_datetime(data_resample["DateTime"]),
                        data_resample.iloc[:, 1],
                        label=wq.monitor_id,
                    )
                    self.plot_axis_do_sat.fill_between(
                        pd.to_datetime(data_resample["DateTime"]),
                        ci_lower,
                        ci_upper,
                        color=line_ts.get_color(),
                        alpha=0.3,
                    )
                    self.plot_axis_do_sat.set_ylabel("DO Sat (Sat%)")
                    self.plot_axis_do_sat.grid(True)
                    if not added_monitor_line:
                        lines.append(line_ts)
                        labels.append(wq.monitor_id)
                        added_monitor_line = True

                if wq.data_nh4 is not None:
                    data_resample, ci_lower, ci_upper = self.resample_data(
                        wq.data_nh4, self.freq
                    )
                    (line_ts,) = self.plot_axis_nh4.plot(
                        pd.to_datetime(data_resample["DateTime"]),
                        data_resample.iloc[:, 1],
                        label=wq.monitor_id,
                    )
                    self.plot_axis_nh4.fill_between(
                        pd.to_datetime(data_resample["DateTime"]),
                        ci_lower,
                        ci_upper,
                        color=line_ts.get_color(),
                        alpha=0.3,
                    )
                    self.plot_axis_nh4.set_ylabel("NH4 (mg/L)")
                    self.plot_axis_nh4.grid(True)
                    if not added_monitor_line:
                        lines.append(line_ts)
                        labels.append(wq.monitor_id)
                        added_monitor_line = True

                if wq.data_ph is not None:
                    data_resample, ci_lower, ci_upper = self.resample_data(
                        wq.data_ph, self.freq
                    )
                    (line_ts,) = self.plot_axis_ph.plot(
                        pd.to_datetime(data_resample["DateTime"]),
                        data_resample.iloc[:, 1],
                        label=wq.monitor_id,
                    )
                    self.plot_axis_ph.fill_between(
                        pd.to_datetime(data_resample["DateTime"]),
                        ci_lower,
                        ci_upper,
                        color=line_ts.get_color(),
                        alpha=0.3,
                    )
                    self.plot_axis_ph.set_ylabel("pH")
                    self.plot_axis_ph.grid(True)
                    if not added_monitor_line:
                        lines.append(line_ts)
                        labels.append(wq.monitor_id)
                        added_monitor_line = True

                if wq.data_temp is not None:
                    data_resample, ci_lower, ci_upper = self.resample_data(
                        wq.data_temp, self.freq
                    )
                    (line_ts,) = self.plot_axis_temp.plot(
                        pd.to_datetime(data_resample["DateTime"]),
                        data_resample.iloc[:, 1],
                        label=wq.monitor_id,
                    )
                    self.plot_axis_temp.fill_between(
                        pd.to_datetime(data_resample["DateTime"]),
                        ci_lower,
                        ci_upper,
                        color=line_ts.get_color(),
                        alpha=0.3,
                    )
                    self.plot_axis_temp.set_ylabel("Temp (°C)")
                    self.plot_axis_temp.grid(True)
                    if not added_monitor_line:
                        lines.append(line_ts)
                        labels.append(wq.monitor_id)
                        added_monitor_line = True

        # Set x-label only for the bottom plot
        self.plot_axis_temp.set_xlabel("Date/Time")

        if self.plot_raw:
            self.main_window_plot_widget.figure.suptitle(
                f"Water Quality Data - Raw Time Series"
            )
        else:
            self.main_window_plot_widget.figure.suptitle(
                f"Water Quality Data - {self.freq} Mean"
            )

        # Position the legend inside the figure
        legend = self.main_window_plot_widget.figure.legend(
            lines,
            labels,
            loc="center left",
            bbox_to_anchor=(0.85, 0.5),
            bbox_transform=self.main_window_plot_widget.figure.transFigure,
            title="Monitors",
        )

        # Adjust the layout to make space for the legend
        self.main_window_plot_widget.figure.subplots_adjust(right=0.85)

        # Redraw the figure to ensure all changes are visible
        self.main_window_plot_widget.figure.canvas.draw()

    def resample_data(
        self, data: pd.DataFrame, frequency: str
    ) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
        # Dictionary to map custom frequencies to pandas resample codes
        frequency_map = {
            "Daily": "D",
            "Yearly": "YE",
            "Monthly": "ME",
            "Weekly": "W",
            "Hourly": "H",
            "Minutely": "T",  # 'T' is for minutes
            "Second": "S",
        }

        # Check if the frequency is in the dictionary
        if frequency not in frequency_map:
            raise ValueError(
                f"Invalid frequency: {frequency}. Please choose from {list(frequency_map.keys())}."
            )

        # Convert the frequency to the pandas resample code
        resample_code = frequency_map[frequency]

        if data is not None:
            resample_data = data.copy()
            resample_data.set_index("DateTime", inplace=True)
            # Resample using the appropriate code and reset the index
            resampled = resample_data.resample(resample_code).mean().reset_index()

            # Calculate 95% confidence interval
            grouped = resample_data.resample(resample_code)
            means = grouped.mean().iloc[:, 0]
            std_devs = grouped.std().iloc[:, 0]
            sample_sizes = grouped.size()

            # 95% confidence interval using Z-score (1.96 for 95% confidence)
            z_value = st.norm.ppf(0.975)
            ci_width = z_value * (std_devs / np.sqrt(sample_sizes))
            ci_lower = means - ci_width
            ci_upper = means + ci_width

            return resampled, ci_lower, ci_upper

    # def enable_dynamic_y_rescaling(self):


    # def on_zoom_pan_end(self, event):
    #     # Get the new x-limits after zooming/panning
    #     xlim = self.plot_axis_temp.get_xlim()

    #     # Convert the x-limits to datetime
    #     xlim_start = mpl_dates.num2date(xlim[0]).replace(tzinfo=None)  # Convert to naive datetime
    #     xlim_end = mpl_dates.num2date(xlim[1]).replace(tzinfo=None)

    #     # Update y-limits for each subplot based on the visible data
    #     for axis, data_key in zip(
    #         [self.plot_axis_cond, self.plot_axis_do, self.plot_axis_do_sat, self.plot_axis_nh4, self.plot_axis_ph, self.plot_axis_temp],
    #         ['data_cond', 'data_do', 'data_do_sat', 'data_nh4', 'data_ph', 'data_temp']
    #     ):
    #         # Filter data within the new x-limits
    #         if hasattr(self.plotted_wqs, 'plotWQs'):
    #             visible_data = []
    #             for wq in self.plotted_wqs.plotWQs.values():
    #                 data = getattr(wq, data_key)
    #                 if data is not None:
    #                     visible_data.append(data[(pd.to_datetime(data['DateTime']) >= pd.to_datetime(xlim[0])) &
    #                                             (pd.to_datetime(data['DateTime']) <= pd.to_datetime(xlim[1]))].iloc[:, 1])

    #             if visible_data:
    #                 all_visible_data = pd.concat(visible_data)
    #                 axis.set_ylim(all_visible_data.min(), all_visible_data.max())

    #     # Redraw the canvas to apply the changes
    #     self.main_window_plot_widget.figure.canvas.draw()

    def on_zoom_pan_end(self, event):
        # Get the new x-limits in Matplotlib's internal format
        xlim = self.plot_axis_temp.get_xlim()

        # Convert the x-limits to datetime
        xlim_start = mpl_dates.num2date(xlim[0]).replace(
            tzinfo=None
        )  # Convert to naive datetime
        xlim_end = mpl_dates.num2date(xlim[1]).replace(tzinfo=None)

        # Update y-limits for each subplot based on the visible data
        for axis, data_key in zip(
            [
                self.plot_axis_cond,
                self.plot_axis_do,
                self.plot_axis_do_sat,
                self.plot_axis_nh4,
                self.plot_axis_ph,
                self.plot_axis_temp,
            ],
            ["data_cond", "data_do", "data_do_sat", "data_nh4", "data_ph", "data_temp"],
        ):
            # Filter data within the new x-limits
            if hasattr(self.plotted_wqs, "plotWQs"):
                visible_data = []
                for wq in self.plotted_wqs.plotWQs.values():
                    data = getattr(wq, data_key)
                    if data is not None:
                        # Convert the 'DateTime' column to datetime if not already
                        data["DateTime"] = pd.to_datetime(data["DateTime"])

                        # Filter the data based on the new x-limits
                        filtered_data = data[
                            (data["DateTime"] >= xlim_start)
                            & (data["DateTime"] <= xlim_end)
                        ].iloc[
                            :, 1
                        ]  # Extract the relevant column
                        visible_data.append(filtered_data)

                if visible_data:
                    # Concatenate all filtered data
                    all_visible_data = pd.concat(visible_data)

                    # Calculate the range and add padding
                    data_min, data_max = all_visible_data.min(), all_visible_data.max()
                    data_range = data_max - data_min
                    padding = data_range * 0.05  # Add 5% padding
                    # Handle case where all data points are the same
                    if data_range == 0:
                        padding = (
                            0.1 * data_min if data_min != 0 else 0.1
                        )  # Small padding

                    # Update the y-limits
                    axis.set_ylim(data_min - padding, data_max + padding)

        # Redraw the canvas to apply the changes
        self.main_window_plot_widget.figure.canvas.draw()

    # def updateAllLines(self):

    #     # Create subplots
    #     self.plot_axis_cond, self.plot_axis_do, self.plot_axis_do_sat, self.plot_axis_nh4, self.plot_axis_ph, self.plot_axis_temp = self.main_window_plot_widget.figure.subplots(
    #         6, 1, sharex=True)

    #     # List to hold all plotted lines and labels
    #     lines = []
    #     labels = []

    #     for wq in self.plotted_wqs.plotWQs.values():

    #         added_monitor_line = False

    #         if self.plot_raw:
    #             if wq.data_cond is not None:
    #                 line_ts, = self.plot_axis_cond.plot(pd.to_datetime(
    #                     wq.data_cond['DateTime']), wq.data_cond.iloc[:, 1], label=wq.monitor_id)
    #                 self.plot_axis_cond.set_ylabel('Cond. (mS/cm)')
    #                 self.plot_axis_cond.grid(True)
    #                 if not added_monitor_line:
    #                     lines.append(line_ts)
    #                     labels.append(wq.monitor_id)
    #                     added_monitor_line = True

    #             if wq.data_do is not None:
    #                 line_ts, = self.plot_axis_do.plot(pd.to_datetime(
    #                     wq.data_do['DateTime']), wq.data_do.iloc[:, 1], label=wq.monitor_id)
    #                 self.plot_axis_do.set_ylabel('DO (mg/L)')
    #                 self.plot_axis_do.grid(True)
    #                 if not added_monitor_line:
    #                     lines.append(line_ts)
    #                     labels.append(wq.monitor_id)
    #                     added_monitor_line = True

    #             if wq.data_do_sat is not None:
    #                 line_ts, = self.plot_axis_do_sat.plot(pd.to_datetime(
    #                     wq.data_do_sat['DateTime']), wq.data_do_sat.iloc[:, 1], label=wq.monitor_id)
    #                 self.plot_axis_do_sat.set_ylabel('DO Sat (Sat%)')
    #                 self.plot_axis_do_sat.grid(True)
    #                 if not added_monitor_line:
    #                     lines.append(line_ts)
    #                     labels.append(wq.monitor_id)
    #                     added_monitor_line = True

    #             if wq.data_nh4 is not None:
    #                 line_ts, = self.plot_axis_nh4.plot(pd.to_datetime(
    #                     wq.data_nh4['DateTime']), wq.data_nh4.iloc[:, 1], label=wq.monitor_id)
    #                 self.plot_axis_nh4.set_ylabel('NH4 (mg/L)')
    #                 self.plot_axis_nh4.grid(True)
    #                 if not added_monitor_line:
    #                     lines.append(line_ts)
    #                     labels.append(wq.monitor_id)
    #                     added_monitor_line = True

    #             if wq.data_ph is not None:
    #                 line_ts, = self.plot_axis_ph.plot(pd.to_datetime(
    #                     wq.data_ph['DateTime']), wq.data_ph.iloc[:, 1], label=wq.monitor_id)
    #                 self.plot_axis_ph.set_ylabel('pH')
    #                 self.plot_axis_ph.grid(True)
    #                 if not added_monitor_line:
    #                     lines.append(line_ts)
    #                     labels.append(wq.monitor_id)
    #                     added_monitor_line = True

    #             if wq.data_temp is not None:
    #                 line_ts, = self.plot_axis_temp.plot(pd.to_datetime(
    #                     wq.data_temp['DateTime']), wq.data_temp.iloc[:, 1], label=wq.monitor_id)
    #                 self.plot_axis_temp.set_ylabel('Temp (°C)')
    #                 self.plot_axis_temp.grid(True)
    #                 if not added_monitor_line:
    #                     lines.append(line_ts)
    #                     labels.append(wq.monitor_id)
    #                     added_monitor_line = True

    #         else:

    #             if wq.data_cond is not None:
    #                 data_resample = self.resample_data(wq.data_cond, self.freq)
    #                 line_ts, = self.plot_axis_cond.plot(pd.to_datetime(
    #                     data_resample['DateTime']), data_resample.iloc[:, 1], label=wq.monitor_id)
    #                 # Compute the 95% confidence intervals
    #                 lower_ci, upper_ci = self.confidence_interval(
    #                     wq.data_cond.iloc[:, 1])
    #                 # Fill between the lower and upper bounds to show the confidence interval
    #                 self.plot_axis_cond.fill_between(pd.to_datetime(data_resample['DateTime']),
    #                                                  lower_ci, upper_ci, color=line_ts.get_color(), alpha=0.3)
    #                 self.plot_axis_cond.set_ylabel('Cond. (mS/cm)')
    #                 self.plot_axis_cond.grid(True)
    #                 if not added_monitor_line:
    #                     lines.append(line_ts)
    #                     labels.append(wq.monitor_id)
    #                     added_monitor_line = True

    #             if wq.data_do is not None:
    #                 data_resample = self.resample_data(wq.data_do, self.freq)
    #                 line_ts, = self.plot_axis_do.plot(pd.to_datetime(
    #                     data_resample['DateTime']), data_resample.iloc[:, 1], label=wq.monitor_id)
    #                 # Compute the 95% confidence intervals
    #                 lower_ci, upper_ci = self.confidence_interval(
    #                     wq.data_do.iloc[:, 1])
    #                 # Fill between the lower and upper bounds to show the confidence interval
    #                 self.plot_axis_do.fill_between(pd.to_datetime(data_resample['DateTime']),
    #                                                lower_ci, upper_ci, color=line_ts.get_color(), alpha=0.3)
    #                 self.plot_axis_do.set_ylabel('DO (mg/L)')
    #                 self.plot_axis_do.grid(True)
    #                 if not added_monitor_line:
    #                     lines.append(line_ts)
    #                     labels.append(wq.monitor_id)
    #                     added_monitor_line = True

    #             if wq.data_do_sat is not None:
    #                 data_resample = self.resample_data(
    #                     wq.data_do_sat, self.freq)
    #                 line_ts, = self.plot_axis_do_sat.plot(pd.to_datetime(
    #                     data_resample['DateTime']), data_resample.iloc[:, 1], label=wq.monitor_id)
    #                 # Compute the 95% confidence intervals
    #                 lower_ci, upper_ci = self.confidence_interval(
    #                     wq.data_do_sat.iloc[:, 1])
    #                 # Fill between the lower and upper bounds to show the confidence interval
    #                 self.plot_axis_do_sat.fill_between(pd.to_datetime(data_resample['DateTime']),
    #                                                    lower_ci, upper_ci, color=line_ts.get_color(), alpha=0.3)
    #                 self.plot_axis_do_sat.set_ylabel('DO Sat (Sat%)')
    #                 self.plot_axis_do_sat.grid(True)
    #                 if not added_monitor_line:
    #                     lines.append(line_ts)
    #                     labels.append(wq.monitor_id)
    #                     added_monitor_line = True

    #             if wq.data_nh4 is not None:
    #                 data_resample = self.resample_data(wq.data_nh4, self.freq)
    #                 line_ts, = self.plot_axis_nh4.plot(pd.to_datetime(
    #                     data_resample['DateTime']), data_resample.iloc[:, 1], label=wq.monitor_id)
    #                 # Compute the 95% confidence intervals
    #                 lower_ci, upper_ci = self.confidence_interval(
    #                     wq.data_nh4.iloc[:, 1])
    #                 # Fill between the lower and upper bounds to show the confidence interval
    #                 self.plot_axis_nh4.fill_between(pd.to_datetime(data_resample['DateTime']),
    #                                                 lower_ci, upper_ci, color=line_ts.get_color(), alpha=0.3)
    #                 self.plot_axis_nh4.set_ylabel('NH4 (mg/L)')
    #                 self.plot_axis_nh4.grid(True)
    #                 if not added_monitor_line:
    #                     lines.append(line_ts)
    #                     labels.append(wq.monitor_id)
    #                     added_monitor_line = True

    #             if wq.data_ph is not None:
    #                 data_resample = self.resample_data(wq.data_ph, self.freq)
    #                 line_ts, = self.plot_axis_ph.plot(pd.to_datetime(
    #                     data_resample['DateTime']), data_resample.iloc[:, 1], label=wq.monitor_id)
    #                 # Compute the 95% confidence intervals
    #                 lower_ci, upper_ci = self.confidence_interval(
    #                     wq.data_ph.iloc[:, 1])
    #                 # Fill between the lower and upper bounds to show the confidence interval
    #                 self.plot_axis_ph.fill_between(pd.to_datetime(data_resample['DateTime']),
    #                                                lower_ci, upper_ci, color=line_ts.get_color(), alpha=0.3)
    #                 self.plot_axis_ph.set_ylabel('pH')
    #                 self.plot_axis_ph.grid(True)
    #                 if not added_monitor_line:
    #                     lines.append(line_ts)
    #                     labels.append(wq.monitor_id)
    #                     added_monitor_line = True

    #             if wq.data_temp is not None:
    #                 data_resample = self.resample_data(wq.data_temp, self.freq)
    #                 line_ts, = self.plot_axis_temp.plot(pd.to_datetime(
    #                     data_resample['DateTime']), data_resample.iloc[:, 1], label=wq.monitor_id)
    #                 # Compute the 95% confidence intervals
    #                 lower_ci, upper_ci = self.confidence_interval(
    #                     wq.data_temp.iloc[:, 1])
    #                 # Fill between the lower and upper bounds to show the confidence interval
    #                 self.plot_axis_temp.fill_between(pd.to_datetime(data_resample['DateTime']),
    #                                                  lower_ci, upper_ci, color=line_ts.get_color(), alpha=0.3)
    #                 self.plot_axis_temp.set_ylabel('Temp (°C)')
    #                 self.plot_axis_temp.grid(True)
    #                 if not added_monitor_line:
    #                     lines.append(line_ts)
    #                     labels.append(wq.monitor_id)
    #                     added_monitor_line = True

    #     # Set x-label only for the bottom plot
    #     self.plot_axis_temp.set_xlabel('Date/Time')

    #     # Position the legend inside the figure
    #     legend = self.main_window_plot_widget.figure.legend(
    #         lines, labels, loc='center left', bbox_to_anchor=(0.85, 0.5),
    #         bbox_transform=self.main_window_plot_widget.figure.transFigure, title="Monitors")
    #     # Adjust the layout to make space for the legend
    #     self.main_window_plot_widget.figure.subplots_adjust(right=0.85)

    #     # Redraw the figure to ensure all changes are visible
    #     self.main_window_plot_widget.figure.canvas.draw()

    # def resample_data(self, data: pd.DataFrame, frequency: str) -> pd.DataFrame:
    #     # Dictionary to map custom frequencies to pandas resample codes
    #     frequency_map = {
    #         'Daily': 'D',
    #         'Yearly': 'YE',
    #         'Monthly': 'ME',
    #         'Weekly': 'W',
    #         'Hourly': 'H',
    #         'Minutely': 'T',  # 'T' is for minutes
    #         'Second': 'S'
    #     }

    #     # Check if the frequency is in the dictionary
    #     if frequency not in frequency_map:
    #         raise ValueError(
    #             f"Invalid frequency: {frequency}. Please choose from {list(frequency_map.keys())}.")

    #     # Convert the frequency to the pandas resample code
    #     resample_code = frequency_map[frequency]

    #     if data is not None:
    #         resample_data = data.copy()
    #         resample_data.set_index('DateTime', inplace=True)
    #         # Resample using the appropriate code and reset the index
    #         return resample_data.resample(resample_code).mean().reset_index()

    # def confidence_interval(self, data, confidence=0.95):
    #     n = len(data)
    #     if n == 0:
    #         return np.nan, np.nan  # Return NaNs if no data points are available
    #     mean = np.mean(data)
    #     stderr = st.sem(data)  # Standard error of the mean
    #     h = stderr * st.t.ppf((1 + confidence) / 2., n-1)  # Margin of error
    #     return mean - h, mean + h


def createVerificationDetailPlot(tr: icmTrace, aLoc: icmTraceLocation):

    fs = 6
    myFig = plt.figure(dpi=100, figsize=(8.3, 5.85))

    (plotAxisTable, plot_axis_depth, plot_axis_flow, plot_axis_velocity) = (
        myFig.subplots(4, gridspec_kw={"height_ratios": [0.6, 1, 1, 1]})
    )
    plot_axis_depth.sharex(plot_axis_velocity)
    plot_axis_flow.sharex(plot_axis_depth)

    major_tick_format = DateFormatter("%d/%m/%Y %H:%M")

    obsColour = "indianred"
    obsPeakColour = "red"
    predColour = "lime"
    predPeakColour = "green"

    currentTitle = aLoc.pageTitle[16:-1]

    (aObsFlow,) = plot_axis_flow.plot(
        aLoc.dates,
        aLoc.rawData[aLoc.iObsFlow],
        "-",
        linewidth=1.1,
        label="Observed",
        color=obsColour,
    )
    (aObsDepth,) = plot_axis_depth.plot(
        aLoc.dates,
        aLoc.rawData[aLoc.iObsDepth],
        "-",
        linewidth=1.1,
        label="Observed",
        color=obsColour,
    )
    (aObsVelocity,) = plot_axis_velocity.plot(
        aLoc.dates,
        aLoc.rawData[aLoc.iObsVelocity],
        "-",
        linewidth=1.1,
        label="Observed",
        color=obsColour,
    )
    (aPredFlow,) = plot_axis_flow.plot(
        aLoc.dates,
        aLoc.rawData[aLoc.iPredFlow],
        "-",
        linewidth=1.1,
        label="Predicted",
        color=predColour,
    )
    (aPredDepth,) = plot_axis_depth.plot(
        aLoc.dates,
        aLoc.rawData[aLoc.iPredDepth],
        "-",
        linewidth=1.1,
        label="Predicted",
        color=predColour,
    )
    (aPredVelocity,) = plot_axis_velocity.plot(
        aLoc.dates,
        aLoc.rawData[aLoc.iPredVelocity],
        "-",
        linewidth=1.1,
        label="Predicted",
        color=predColour,
    )

    if aLoc.verifyForFlow:
        if not aLoc.peaksInitialized[aLoc.iObsFlow]:
            aLoc.updatePeaks(aLoc.iObsFlow)
        (aObsFlowPk,) = plot_axis_flow.plot(
            aLoc.peaksDates[aLoc.iObsFlow],
            aLoc.peaksData[aLoc.iObsFlow],
            "o",
            label="Observed Peaks",
            color=obsPeakColour,
        )

        if not aLoc.peaksInitialized[aLoc.iPredFlow]:
            aLoc.updatePeaks(aLoc.iPredFlow)
        (aPredFlowPk,) = plot_axis_flow.plot(
            aLoc.peaksDates[aLoc.iPredFlow],
            aLoc.peaksData[aLoc.iPredFlow],
            "o",
            label="Predicted Peaks",
            color=predPeakColour,
        )

    if aLoc.verifyForDepth:
        if not aLoc.peaksInitialized[aLoc.iObsDepth]:
            aLoc.updatePeaks(aLoc.iObsDepth)
        (aObsDepthPk,) = plot_axis_depth.plot(
            aLoc.peaksDates[aLoc.iObsDepth],
            aLoc.peaksData[aLoc.iObsDepth],
            "o",
            label="Observed Peaks",
            color=obsPeakColour,
        )

        if not aLoc.peaksInitialized[aLoc.iPredDepth]:
            aLoc.updatePeaks(aLoc.iPredDepth)
        (aPredDepthPk,) = plot_axis_depth.plot(
            aLoc.peaksDates[aLoc.iPredDepth],
            aLoc.peaksData[aLoc.iPredDepth],
            "o",
            label="Predicted Peaks",
            color=predPeakColour,
        )

    # Depth
    plot_axis_depth.yaxis.set_major_locator(MaxNLocator(integer=True))
    plot_axis_depth.set_ylabel("Depth (m)", fontsize=fs)
    plot_axis_depth.tick_params(axis="y", which="major", labelsize=fs)

    plot_axis_flow.yaxis.set_major_locator(MaxNLocator(integer=True))
    plot_axis_flow.set_ylabel("Flow (m³/s)", fontsize=fs)
    plot_axis_flow.tick_params(axis="y", which="major", labelsize=fs)

    # Velocity
    plot_axis_velocity.yaxis.set_major_locator(MaxNLocator(8))
    plot_axis_velocity.xaxis.set_major_locator(MaxNLocator(integer=False))
    plot_axis_velocity.xaxis.set_major_formatter(FuncFormatter(major_tick_format))
    plot_axis_velocity.set_ylabel("Velocity (m/s)", fontsize=fs)
    plot_axis_velocity.tick_params(axis="y", which="major", labelsize=fs)

    plot_axis_flow.grid(True)
    plot_axis_depth.grid(True)
    plot_axis_velocity.grid(True)

    plotAxisTable.set_title(currentTitle, color="black", fontsize=9)

    df = pd.DataFrame()

    pltTrace = plottedICMTrace()
    pltTrace.addICMTrace(tr)
    pltTrace.plotTrace.currentLocation = aLoc.index
    pltTrace.updatePlottedICMTracesMinMaxValues()

    df["Min Depth"] = formatTableData(
        pltTrace.plotMinObsDepth, pltTrace.plotMinPredDepth, 3
    )

    df["Max Depth"] = formatTableData(
        pltTrace.plotMaxObsDepth, pltTrace.plotMaxPredDepth, 3
    )

    df["Min Flow"] = formatTableData(
        pltTrace.plotMinObsFlow, pltTrace.plotMinPredFlow, 3
    )

    df["Max Flow"] = formatTableData(
        pltTrace.plotMaxObsFlow, pltTrace.plotMaxPredFlow, 3
    )

    df["Volume"] = formatTableData(
        pltTrace.plotTotalObsVolume, pltTrace.plotTotalPredVolume, 1
    )

    df["Min Velocity"] = formatTableData(
        pltTrace.plotMinObsVelocity, pltTrace.plotMinPredVelocity, 3
    )

    df["Max Velocity"] = formatTableData(
        pltTrace.plotMaxObsVelocity, pltTrace.plotMaxPredVelocity, 3
    )

    plotAxisTable.axis("off")
    add_cell(
        plotAxisTable,
        [["Difference"]],
        [0, 0, 0.125, 0.1875],
        [["#71004b"]],
        fs,
        "w",
        "bold",
    )
    add_cell(
        plotAxisTable,
        [["Predicted"]],
        [0, 0.1875, 0.125, 0.1875],
        [["#71004b"]],
        fs,
        "w",
        "bold",
    )
    add_cell(
        plotAxisTable,
        [["Observed"]],
        [0, 0.375, 0.125, 0.1875],
        [["#71004b"]],
        fs,
        "w",
        "bold",
    )
    add_cell(plotAxisTable, df.values, [0.125, 0, 0.875, 0.5625], None, fs)
    add_cell(
        plotAxisTable,
        [["Min\n(m)", "Max\n(m)"]],
        [0.125, 0.5625, 0.25, 0.25],
        [["#71004b", "#71004b"]],
        fs,
        "w",
        "bold",
    )
    add_cell(
        plotAxisTable,
        [["Depth"]],
        [0.125, 0.8125, 0.25, 0.1875],
        [["#71004b"]],
        fs,
        "w",
        "bold",
    )
    add_cell(
        plotAxisTable,
        [["Min\n(m3/s)", "Max\n(m3/s)", "Volume\n(m3)"]],
        [0.375, 0.5625, 0.375, 0.25],
        [["#71004b", "#71004b", "#71004b"]],
        fs,
        "w",
        "bold",
    )
    add_cell(
        plotAxisTable,
        [["Flow"]],
        [0.375, 0.8125, 0.375, 0.1875],
        [["#71004b"]],
        fs,
        "w",
        "bold",
    )
    add_cell(
        plotAxisTable,
        [["Min\n(m/s)", "Max\n(m/s)"]],
        [0.75, 0.5625, 0.25, 0.25],
        [["#71004b", "#71004b"]],
        fs,
        "w",
        "bold",
    )
    add_cell(
        plotAxisTable,
        [["Velocity"]],
        [0.75, 0.8125, 0.25, 0.1875],
        [["#71004b"]],
        fs,
        "w",
        "bold",
    )

    # plotAxisTable.axis("off")
    # add_cell(plotAxisTable, [['Difference']], [
    #     0, 0, 0.125, 0.1875], [["#d4f1ff"]], fs)
    # add_cell(plotAxisTable, [['Predicted']], [
    #     0, 0.1875, 0.125, 0.1875], [["#d4f1ff"]], fs)
    # add_cell(plotAxisTable, [['Observed']], [
    #     0, 0.375, 0.125, 0.1875], [["#d4f1ff"]], fs)
    # add_cell(plotAxisTable, df.values, [
    #     0.125, 0, 0.875, 0.5625], None, fs)
    # add_cell(plotAxisTable, [['Min\n(m)', 'Max\n(m)']], [
    #     0.125, 0.5625, 0.25, 0.25], [["#d4f1ff", "#d4f1ff"]], fs)
    # add_cell(plotAxisTable, [['Depth']], [
    #     0.125, 0.8125, 0.25, 0.1875], [["#d4f1ff"]], fs)
    # add_cell(plotAxisTable, [['Min\n(m3/s)', 'Max\n(m3/s)', 'Volume\n(m3)']], [
    #     0.375, 0.5625, 0.375, 0.25], [["#d4f1ff", "#d4f1ff", "#d4f1ff"]], fs)
    # add_cell(plotAxisTable, [['Flow']], [
    #     0.375, 0.8125, 0.375, 0.1875], [["#d4f1ff"]], fs)
    # add_cell(plotAxisTable, [[
    #     'Min\n(m/s)', 'Max\n(m/s)']], [0.75, 0.5625, 0.25, 0.25], [["#d4f1ff", "#d4f1ff"]], fs)
    # add_cell(plotAxisTable, [['Velocity']], [
    #     0.75, 0.8125, 0.25, 0.1875], [["#d4f1ff"]], fs)
    myFig.autofmt_xdate()
    plot_axis_velocity.tick_params(axis="x", which="major", labelsize=fs)
    myFig.subplots_adjust(left=0.07, right=0.98, bottom=0.10, top=0.94)

    return myFig


def createEventSuitabilityFMClassPiePlot(fmClass: list[str]):
    plotAxisPie = None

    fs = 8
    # tabHeight = max((len(table_data) - 1) * 0.4, 8.3)
    myFig = plt.figure(dpi=100, figsize=(3, 3), tight_layout={"pad": 1})
    plotAxisPie = myFig.subplots(1)

    count_fmClass = Counter(fmClass)
    myLabels = []
    myColors = []
    for key in count_fmClass.keys():
        myColors.append(dataClassification.dictColor[key])
        myLabels.append(dataClassification.dictLabels[key])
    plotAxisPie.pie(
        count_fmClass.values(),
        labels=myLabels,
        startangle=90,
        colors=myColors,
        wedgeprops={"edgecolor": "k", "linewidth": 1, "antialiased": True},
        textprops={"fontsize": fs},
    )

    return myFig


def createEventSuitabilityEventSummaryTablePlot(se: surveyEvent):
    plotAxisTable = None

    fs = 10
    # tabHeight = max((len(table_data) - 1) * 0.4, 8.3)
    myFig = plt.figure(dpi=100, figsize=(8.3, 1), tight_layout={"pad": 1})

    plotAxisTable = myFig.subplots()

    table_data = [
        ["Event Name", "Duration", "Start Date", "Start Time", "End Date", "End Time"]
    ]
    table_data.append(
        [
            se.eventName,
            se.durationFormattedString(),
            datetime.strftime(se.eventStart, "%d/%m/%Y"),
            dt.strftime(se.eventStart, "%H:%M"),
            datetime.strftime(se.eventEnd, "%d/%m/%Y"),
            datetime.strftime(se.eventEnd, "%H:%M"),
        ]
    )

    hexRPS = "#71004b"
    myBbx1 = [0, 0, 1, 1]
    column_headers = table_data[0]
    col_colours = np.full(len(column_headers), hexRPS)
    cell_text = [row[:] for row in table_data[1:]]
    col_widths = [0.2, 0.16, 0.16, 0.16, 0.16, 0.16]

    testTb = table(
        plotAxisTable,
        cellText=cell_text,
        colColours=col_colours,
        cellLoc="center",
        colWidths=col_widths,
        colLabels=column_headers,
        rowLoc="center",
        colLoc="center",
        bbox=myBbx1,
    )
    testTb.auto_set_font_size(False)
    testTb.set_fontsize(fs)
    testTb.set_zorder(100)

    for i in range(len(table_data[0])):
        txt = testTb[(0, i)].get_text()
        txt.set_color("white")
        txt.set_fontweight("bold")

    plotAxisTable.set_axis_off()

    return myFig


def createEventSuitabilityRaingaugeDetailsTablePlot(table_data):
    plotAxisTable = None

    fs = 10
    tabHeight = min((len(table_data) - 1) * 0.5, 4.85)
    myFig = plt.figure(dpi=100, figsize=(8.3, tabHeight), tight_layout={"pad": 1})

    plotAxisTable = myFig.subplots()

    hexRPS = "#71004b"
    myBbx1 = [0, 0, 1, 1]
    column_headers = table_data[0]
    col_colours = np.full(len(column_headers), hexRPS)
    cell_text = [row[:] for row in table_data[1:]]
    col_widths = [0.1, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15]

    testTb = table(
        plotAxisTable,
        cellText=cell_text,
        colColours=col_colours,
        cellLoc="center",
        colWidths=col_widths,
        colLabels=column_headers,
        rowLoc="center",
        colLoc="center",
        bbox=myBbx1,
    )
    testTb.auto_set_font_size(False)
    testTb.set_fontsize(fs)
    testTb.set_zorder(100)

    for i in range(len(table_data[0])):
        txt = testTb[(0, i)].get_text()
        txt.set_color("white")
        txt.set_fontweight("bold")

    plotAxisTable.set_axis_off()

    return myFig


def createVerificationDetailUDGTablePlot(tr: icmTrace, aLoc: icmTraceLocation):

    plotAxisTable = None
    plotAxFit = None

    fs = 7
    myFig = plt.figure(dpi=100, figsize=(3.3, 5.85), tight_layout={"pad": 1})

    roundTo = 1 / 1000  # round up to 1 l/s
    ax_max = (
        math.ceil(
            max(max(aLoc.rawData[aLoc.iObsFlow]), max(aLoc.rawData[aLoc.iPredFlow]))
            / roundTo
        )
        * roundTo
    )
    if ax_max == 0:
        ax_max = 1

    plotAxisTable, plotAxFit = myFig.subplots(
        2, gridspec_kw={"height_ratios": [1.7, 1]}
    )

    plotAxFit.plot(
        aLoc.rawData[aLoc.iObsFlow],
        aLoc.rawData[aLoc.iPredFlow],
        figure=myFig,
        ls="None",
        label="Observed",
        color="red",
        marker="x",
    )
    # plotAxFit.set_title(
    #     aLoc.shortTitle, color='black', fontsize=12)
    (perfectLine,) = plotAxFit.plot(
        [0, ax_max], [0, ax_max], ls="-", label="Perfect Fit", color="green"
    )
    plotAxFit.grid(visible=True, which="both", axis="both")
    plotAxFit.text(
        ax_max * 0.93,
        ax_max * 0.95,
        perfectLine.get_label(),
        horizontalalignment="right",
        verticalalignment="center",
        fontsize=fs,
    )
    plotAxFit.set_xlabel("Observed", fontsize=fs)
    plotAxFit.set_ylabel("Predicted", fontsize=fs)
    plotAxFit.tick_params(axis="both", which="major", labelsize=fs)
    plotAxFit.set_xlim(0, ax_max)
    plotAxFit.set_ylim(0, ax_max)
    # plotAxFit.set_box_aspect(1)
    # plotAxFit.set_aspect('equal')

    myProps = dict(boxstyle="round", facecolor="teal", alpha=0.5)
    myDict = {
        "Obs": aLoc.rawData[aLoc.iObsFlow].copy(),
        "Pred": aLoc.rawData[aLoc.iPredFlow].copy(),
    }
    df = pd.DataFrame(myDict)
    myKG = getKlingGupta(df, "Obs", "Pred")
    myNash = getNashSutcliffe(df, "Obs", "Pred")
    myCV = getCoeffVariation(df, "Obs")
    plotModelEff = plotAxFit.text(
        0.05,
        0.95,
        "",
        transform=plotAxFit.transAxes,
        fontsize=fs,
        verticalalignment="top",
        bbox=myProps,
        family="serif",
    )
    me_textstr = f"Nash Sutcliffe: {(myNash):.2f}\nKling Gupta: {(myKG):.2f}\nCVobs: {(myCV):.2f}"
    plotModelEff.set_text(me_textstr)

    hexGreen = "#47d655"
    hexOrange = "#f58b0a"
    hexRed = "#e87676"

    myBbx1 = [0.03, 0.6967, 0.94, 0.3033]
    myBbx2 = [0.03, 0.2875, 0.94, 0.3792]
    myBbx3 = [0.03, 0.03, 0.94, 0.2275]

    if aLoc.verificationFlowScore + aLoc.verificationDepthScore == 2:
        verifOverall = "Yes"
    elif aLoc.verificationFlowScore + aLoc.verificationDepthScore > 0:
        verifOverall = "Partial"
    else:
        verifOverall = "No"
    if aLoc.verificationFlowScore == 1:
        verifFlow = "Yes"
    elif aLoc.verificationFlowScore > 0:
        verifFlow = "Partial"
    else:
        verifFlow = "No"
    if aLoc.verificationDepthScore == 1:
        verifDepth = "Yes"
    elif aLoc.verificationDepthScore > 0:
        verifDepth = "Partial"
    else:
        verifDepth = "No"

    table_data = [
        [twp.fill("Verification", 12), twp.fill("Result", 10)],
        [twp.fill("Flow", 10), verifFlow],
        [twp.fill("Depth", 10), verifDepth],
        [twp.fill("Overall", 10), verifOverall],
    ]

    cell_colours = [
        ["#71004b", "#71004b"],
        [
            "#ffffff",
            (
                hexGreen
                if verifFlow == "Yes"
                else hexRed if verifFlow == "No" else hexOrange
            ),
        ],
        [
            "#ffffff",
            (
                hexGreen
                if verifDepth == "Yes"
                else hexRed if verifDepth == "No" else hexOrange
            ),
        ],
        [
            "#ffffff",
            (
                hexGreen
                if verifOverall == "Yes"
                else hexRed if verifOverall == "No" else hexOrange
            ),
        ],
    ]

    col_widths = [0.33, 0.39]
    # myBbx = [0.03, 0.6767, 0.94, 0.2933]

    testTb = table(
        plotAxisTable,
        cellText=table_data,
        cellColours=cell_colours,
        cellLoc="center",
        colWidths=col_widths,
        rowLoc="center",
        colLoc="center",
        bbox=myBbx1,
    )
    testTb.auto_set_font_size(False)
    testTb.set_fontsize(fs)
    testTb.set_zorder(100)
    for i in range(len(table_data[0])):
        txt = testTb[(0, i)].get_text()
        txt.set_color("white")
        txt.set_fontweight("bold")

    if aLoc.isCritical:
        table_data = [
            [
                twp.fill("Parameter", 10),
                twp.fill("Actual Value", 10),
                twp.fill("Critical Location", 10),
            ],
            [twp.fill("Shape (NSE)", 10), f"{aLoc.flowNSE:.{2}f}", ">0.5"],
            [twp.fill("Time of Peaks", 10), f"{aLoc.flowTp_Diff_Hrs:.{2}f}", "±0.5Hr"],
            [twp.fill("Peak Flow", 10), f"{aLoc.flowQp_Diff_Pcnt:.{1}f}", "±10%"],
            [twp.fill("Flow Volume", 10), f"{aLoc.flowVol_Diff_Pcnt:.{1}f}", "±10%"],
        ]

        cell_colours = [
            ["#71004b", "#71004b", "#71004b"],
            ["#ffffff", "#ffffff", hexGreen if (aLoc.flowNSE > 0.5) else hexRed],
            [
                "#ffffff",
                "#ffffff",
                hexGreen if (0.5 > aLoc.flowTp_Diff_Hrs > -0.5) else hexRed,
            ],
            [
                "#ffffff",
                "#ffffff",
                hexGreen if (10 > aLoc.flowQp_Diff_Pcnt > -10) else hexRed,
            ],
            [
                "#ffffff",
                "#ffffff",
                hexGreen if (10 > aLoc.flowVol_Diff_Pcnt > -10) else hexRed,
            ],
        ]

    else:
        table_data = [
            [
                twp.fill("Parameter", 10),
                twp.fill("Actual Value", 10),
                twp.fill("General Location", 10),
            ],
            [twp.fill("Shape (NSE)", 10), f"{aLoc.flowNSE:.{2}f}", ">0.5"],
            [twp.fill("Time of Peaks", 10), f"{aLoc.flowTp_Diff_Hrs:.{2}f}", "±0.5Hr"],
            [
                twp.fill("Peak Flow", 10),
                f"{aLoc.flowQp_Diff_Pcnt:.{1}f}",
                "+25% to -15%",
            ],
            [
                twp.fill("Flow Volume", 10),
                f"{aLoc.flowVol_Diff_Pcnt:.{1}f}",
                "+20% to -10%",
            ],
        ]

        cell_colours = [
            ["#71004b", "#71004b", "#71004b"],
            ["#ffffff", "#ffffff", hexGreen if (aLoc.flowNSE > 0.5) else hexRed],
            [
                "#ffffff",
                "#ffffff",
                hexGreen if (0.5 > aLoc.flowTp_Diff_Hrs > -0.5) else hexRed,
            ],
            [
                "#ffffff",
                "#ffffff",
                hexGreen if (25 > aLoc.flowQp_Diff_Pcnt > -15) else hexRed,
            ],
            [
                "#ffffff",
                "#ffffff",
                hexGreen if (20 > aLoc.flowVol_Diff_Pcnt > -10) else hexRed,
            ],
        ]

    col_widths = [0.33, 0.28, 0.39]
    # myBbx = [0.05, 0.35, 0.15, 0.64]

    testTb = table(
        plotAxisTable,
        cellText=table_data,
        cellColours=cell_colours,
        cellLoc="center",
        colWidths=col_widths,
        rowLoc="center",
        colLoc="center",
        bbox=myBbx2,
    )
    testTb.auto_set_font_size(False)
    testTb.set_fontsize(fs)
    testTb.set_zorder(100)
    for i in range(len(table_data[0])):
        txt = testTb[(0, i)].get_text()
        txt.set_color("white")
        txt.set_fontweight("bold")

    # hexGreen = '#47d655'
    # hexRed = '#e87676'

    if aLoc.isCritical:
        if aLoc.isSurcharged:
            table_data = [
                [
                    twp.fill("Parameter", 10),
                    twp.fill("Actual Value", 10),
                    twp.fill("Critical Location", 10),
                ],
                [
                    twp.fill("Time of Peaks", 10),
                    f"{aLoc.depthTp_Diff_Hrs:.{2}f}",
                    "±0.5Hr",
                ],
                [
                    twp.fill("Peak Depth (Surch)", 10),
                    f"{aLoc.depthDp_Diff:.{2}f}",
                    "±0.1m",
                ],
            ]

            cell_colours = [
                ["#71004b", "#71004b", "#71004b"],
                [
                    "#ffffff",
                    "#ffffff",
                    hexGreen if (0.5 > aLoc.depthTp_Diff_Hrs > -0.5) else hexRed,
                ],
                [
                    "#ffffff",
                    "#ffffff",
                    hexGreen if (0.1 > aLoc.depthDp_Diff > -0.1) else hexRed,
                ],
            ]

        else:
            table_data = [
                [
                    twp.fill("Parameter", 10),
                    twp.fill("Actual Value", 10),
                    twp.fill("Critical Location", 10),
                ],
                [
                    twp.fill("Time of Peaks", 10),
                    f"{aLoc.depthTp_Diff_Hrs:.{2}f}",
                    "±0.5Hr",
                ],
                [twp.fill("Peak Depth", 10), f"{aLoc.depthDp_Diff:.{2}f}", "±0.1m"],
            ]

            cell_colours = [
                ["#71004b", "#71004b", "#71004b"],
                [
                    "#ffffff",
                    "#ffffff",
                    hexGreen if (0.5 > aLoc.depthTp_Diff_Hrs > -0.5) else hexRed,
                ],
                [
                    "#ffffff",
                    "#ffffff",
                    hexGreen if (0.1 > aLoc.depthDp_Diff > -0.1) else hexRed,
                ],
            ]

    else:
        if aLoc.isSurcharged:
            table_data = [
                [
                    twp.fill("Parameter", 10),
                    twp.fill("Actual Value", 10),
                    twp.fill("General Location", 10),
                ],
                [
                    twp.fill("Time of Peaks", 10),
                    f"{aLoc.depthTp_Diff_Hrs:.{2}f}",
                    "±0.5Hr",
                ],
                [
                    twp.fill("Peak Depth (Surch)", 10),
                    f"{aLoc.depthDp_Diff:.{2}f}",
                    "+0.5m to -0.1m",
                ],
            ]

            cell_colours = [
                ["#71004b", "#71004b", "#71004b"],
                [
                    "#ffffff",
                    "#ffffff",
                    hexGreen if (0.5 > aLoc.depthTp_Diff_Hrs > -0.5) else hexRed,
                ],
                [
                    "#ffffff",
                    "#ffffff",
                    hexGreen if (0.5 > aLoc.depthDp_Diff > -0.1) else hexRed,
                ],
            ]

        else:

            table_data = [
                [
                    twp.fill("Parameter", 10),
                    twp.fill("Actual Value", 10),
                    twp.fill("General Location", 10),
                ],
                [
                    twp.fill("Time of Peaks", 10),
                    f"{aLoc.depthTp_Diff_Hrs:.{2}f}",
                    "±0.5Hr",
                ],
                [
                    twp.fill("Peak Depth", 10),
                    f"{aLoc.depthDp_Diff:.{2}f}m/{aLoc.depthDp_Diff_Pcnt:.{0}f}%",
                    "±0.1m or ±10%",
                ],
            ]

            cell_colours = [
                ["#71004b", "#71004b", "#71004b"],
                [
                    "#ffffff",
                    "#ffffff",
                    hexGreen if (0.5 > aLoc.depthTp_Diff_Hrs > -0.5) else hexRed,
                ],
                [
                    "#ffffff",
                    "#ffffff",
                    (
                        hexGreen
                        if (
                            (10 > aLoc.depthDp_Diff_Pcnt > -10)
                            and (0.1 > aLoc.depthDp_Diff > -0.1)
                        )
                        else hexRed
                    ),
                ],
            ]

    col_widths = [0.33, 0.28, 0.39]

    testTb = table(
        plotAxisTable,
        cellText=table_data,
        cellColours=cell_colours,
        cellLoc="center",
        colWidths=col_widths,
        rowLoc="center",
        colLoc="center",
        bbox=myBbx3,
    )
    testTb.auto_set_font_size(False)
    testTb.set_fontsize(fs)
    testTb.set_zorder(100)
    for i in range(len(table_data[0])):
        txt = testTb[(0, i)].get_text()
        txt.set_color("white")
        txt.set_fontweight("bold")

    plotAxisTable.set_axis_off()

    return myFig


def add_cell(
    ax,
    cellText: list[list[str]],
    bbox,
    ccolors: list[list[str]] = None,
    font_size: int = 8,
    tcolor="k",
    tweight="normal",
):
    t = ax.table(
        cellText=cellText,
        loc="bottom",
        bbox=bbox,
        cellLoc="center",
        cellColours=ccolors,
    )
    t.auto_set_font_size(False)
    t.set_fontsize(font_size)
    for row, col in t._cells.keys():
        t[row, col].get_text().set_color(tcolor)
        t[row, col].get_text().set_fontweight(tweight)


def formatTableData(obVal, predVal, number_of_decimals):
    diffVal = predVal - obVal
    if obVal != 0:
        diffPcnt = f"({((diffVal / obVal) * 100):.0f}%)"
    else:
        diffPcnt = f"(-%)"
    return [
        f"{obVal:.{number_of_decimals}f}",
        f"{predVal:.{number_of_decimals}f}",
        f"{diffVal:.{number_of_decimals}f} {diffPcnt}",
    ]


def create_fsm_data_classification_plot(table_data):

    self.filter_data()
    self.setup_axes()
    self.create_legend()
    self.plot_data()
    self.add_classifications()
    self.add_statistics()
    self.finalize_plot()

    plotAxisTable = None

    fs = 10
    tabHeight = min((len(table_data) - 1) * 0.5, 4.85)
    myFig = plt.figure(dpi=100, figsize=(8.3, tabHeight), tight_layout={"pad": 1})

    plotAxisTable = myFig.subplots()

    hexRPS = "#71004b"
    myBbx1 = [0, 0, 1, 1]
    column_headers = table_data[0]
    col_colours = np.full(len(column_headers), hexRPS)
    cell_text = [row[:] for row in table_data[1:]]
    col_widths = [0.1, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15]

    testTb = table(
        plotAxisTable,
        cellText=cell_text,
        colColours=col_colours,
        cellLoc="center",
        colWidths=col_widths,
        colLabels=column_headers,
        rowLoc="center",
        colLoc="center",
        bbox=myBbx1,
    )
    testTb.auto_set_font_size(False)
    testTb.set_fontsize(fs)
    testTb.set_zorder(100)

    for i in range(len(table_data[0])):
        txt = testTb[(0, i)].get_text()
        txt.set_color("white")
        txt.set_fontweight("bold")

    plotAxisTable.set_axis_off()

    return myFig


def labelLine(line, x, label=None, align=True, **kwargs):

    ax = line.axes
    xdata = line.get_xdata()
    ydata = line.get_ydata()

    if (x < xdata.min()) or (x > xdata.max()):
        print("x label location is outside data range!")
        return

    # Find corresponding y co-ordinate and angle of the line
    ip = 1
    for i in range(len(xdata)):
        if i > 0:
            if x < xdata[i]:
                ip = i
                break

    y = ydata[ip - 1] + (ydata[ip] - ydata[ip - 1]) * (x - xdata[ip - 1]) / (
        xdata[ip] - xdata[ip - 1]
    )

    if not label:
        label = line.get_label()

    if align:
        # Compute the slope
        dx = xdata[ip] - xdata[ip - 1]
        dy = ydata[ip] - ydata[ip - 1]
        ang = math.degrees(math.atan2(dy, dx))

        # Transform to screen co-ordinates
        pt = np.array([x, y]).reshape((1, 2))
        trans_angle = ax.transData.transform_angles(np.array((ang,)), pt)[0]

    else:
        trans_angle = 0

    # Set a bunch of keyword arguments
    if "color" not in kwargs:
        kwargs["color"] = line.get_color()

    if ("horizontalalignment" not in kwargs) and ("ha" not in kwargs):
        kwargs["ha"] = "center"

    if ("verticalalignment" not in kwargs) and ("va" not in kwargs):
        kwargs["va"] = "center"

    if "backgroundcolor" not in kwargs:
        kwargs["backgroundcolor"] = ax.get_facecolor()

    if "clip_on" not in kwargs:
        kwargs["clip_on"] = True

    if "zorder" not in kwargs:
        kwargs["zorder"] = 2.5

    ax.text(x, y, label, rotation=trans_angle, **kwargs)


def labelLines(lines, align=True, xvals=None, **kwargs):

    ax = lines[0].axes
    labLines = []
    labels = []

    # Take only the lines which have labels other than the default ones
    for line in lines:
        label = line.get_label()
        if "_line" not in label:
            labLines.append(line)
            labels.append(label)

    if xvals is None:
        xmin, xmax = ax.get_xlim()
        xvals = np.linspace(xmin, xmax, len(labLines) + 2)[1:-1]

    for line, x, label in zip(labLines, xvals, labels):
        labelLine(line, x, label, align, **kwargs)


class graphPipeShapeDefinition:
    def __init__(self, a_pw: PlotWidget = None):
        self.a_plot_widget = a_pw or PlotWidget()
        self.df_shape: Optional[pd.DataFrame] = None
        self.isBlank = True
        self.update_plot()

    def update_plot(self):
        """Redraw the plot using the custom PlotWidget."""
        # Clear the previous plot
        self.a_plot_widget.figure.clear()
        ax = self.a_plot_widget.figure.add_subplot(111)
        ax.set_aspect("equal", adjustable="datalim")

        # Check and plot data
        if self.df_shape is not None and not self.df_shape.empty:
            for _, row in self.df_shape.iterrows():
                width = row["Width"]
                height = row["Height"]
                x_start = -width / 2
                x_end = width / 2

                # Plot the line
                ax.plot([x_start, x_end], [height, height], color="blue")

                # Add label to the right-hand side
                label_text = f"{int(width) if width.is_integer() else width:.1f}, {int(height) if height.is_integer() else height:.1f}"
                # label_text = f"W: {width}, H: {height}"
                ax.text(
                    x_end + 0.1,
                    height,
                    label_text,
                    verticalalignment="center",
                    color="black",
                    fontsize=6,
                )

            self.isBlank = False
        else:
            self.isBlank = True

        # Customize the plot
        ax.set_xlabel("X-Axis (Width)")
        ax.set_ylabel("Y-Axis (Height)")
        ax.grid(True, linestyle="--", alpha=0.6)

        # Optionally remove the frame and axis labels
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)

        # Refresh canvas
        self.a_plot_widget.canvas.draw()


# class graphPipeShapeDefinition:
#     def __init__(self, a_pw: PlotWidget = None):
#         self.a_plot_widget = a_pw
#         self.df_shape: Optional[pd.DataFrame] = None
#         self.isBlank = True
#         self.update_plot()

#     def update_plot(self):
#         """Redraw the plot using the custom PlotWidget."""
#         self.a_plot_widget.figure.clear()
#         ax = self.a_plot_widget.figure.add_subplot(111)

#         if self.df_shape is not None:
#             if not self.df_shape.empty:
#                 for _, row in self.df_shape.iterrows():
#                     width = row['Width']
#                     height = row['Height']
#                     x_start = -width / 2
#                     x_end = width / 2
#                     ax.plot([x_start, x_end], [height, height], color="blue")
#                 self.isBlank = False
#         else:
#             self.isBlank = True

#         # Customize the plot
#         # ax.set_title("Pipe Shape Definition")
#         ax.set_xlabel("X-Axis (Width)")
#         ax.set_ylabel("Y-Axis (Height)")
#         ax.grid(True, linestyle='--', alpha=0.6)
#         self.a_plot_widget.canvas.draw()
