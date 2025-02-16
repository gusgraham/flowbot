# from ast import List
import site
from PyQt5 import QtWidgets, QtCore
# from flowbot_graphing import GraphFDV
from typing import Optional, List, Dict
from datetime import datetime

import matplotlib.patches as mpl_patches
import matplotlib.dates as mpl_dates
import matplotlib.gridspec as mpl_gridspec
from matplotlib import pyplot as plt
from matplotlib import axes, lines, text
from collections import Counter
from matplotlib.dates import DateFormatter, HourLocator, num2date
import matplotlib.ticker as ticker
from matplotlib.ticker import MaxNLocator, FuncFormatter
import matplotlib.colors as mcolors

# from flowbot_helper import get_classification_legend_dataframe, get_classification_color_mapping
import math
import pandas as pd
from bisect import bisect_left
import numpy as np

# from flowbot_monitors import plottedFlowMonitors
from flowbot_management import fsmInterim, fsmInterimReview, fsmMonitor, fsmProject, fsmSite, fsmInstall
from ui_elements.ui_flowbot_dialog_fsm_review_flowmonitor_base import Ui_Dialog

class flowbot_dialog_fsm_review_flowmonitor(QtWidgets.QDialog, Ui_Dialog):
    # def __init__(self, a_installs: List[fsmInstall], sites: Dict[str, fsmSite], start_date: datetime, end_date: datetime, parent=None):
    def __init__(self, interim_id: int, a_project: fsmProject, parent=None):
        """Constructor."""
        super(flowbot_dialog_fsm_review_flowmonitor, self).__init__(parent)
        self.setupUi(self)
        
        self.btnDone.clicked.connect(self.onAccept)

        self.a_project: fsmProject = a_project
        # self.class_reviews: Dict[int, fsmInterimClassificationReview] = {}
        # self.installs: List[fsmInstall] = []
        # self.a_int_crs: fsmInterim = self.a_project.filter_interim_classification_reviews_by_interim_id(interim_id)  
            
        # self.sites: Dict[str, fsmSite] = sites

        self.interim_id = interim_id
        self.interim = self.a_project.dict_fsm_interims[self.interim_id]
        self.start_date: datetime = self.interim.interim_start_date
        self.end_date: datetime = self.interim.interim_end_date
        self.interim_reviews: list[fsmInterimReview] = []

        for a_inst in self.a_project.dict_fsm_installs.values():
            if a_inst.install_type != 'Rain Gauge':
                a_int_fm = self.a_project.get_interim_review(interim_id=interim_id, install_id=a_inst.install_id)
                if not a_int_fm:
                    a_int_fm = fsmInterimReview()
                    a_int_fm.interim_review_id = self.a_project.get_next_interim_review_id()
                    a_int_fm.interim_id = interim_id
                    a_int_fm.install_id = a_inst.install_id
                    self.a_project.add_interim_review(a_int_fm)
                self.interim_reviews.append(a_int_fm)

        self.df_filtered: pd.DataFrame

        # for a_int_cr in self.a_project.dict_fsm_interim_class_reviews.values():
        #     if a_int_cr.interim_id == interim_id:
        #         self.interim_reviews.append(a_int_cr)

            # for a_inst in self.a_project.dict_fsm_installs.values():
            #     if a_int_cr.install_id == a_inst.install_id:
            #         if a_inst.data is not None and not a_inst.data.empty:
            #             self.installs.append(a_inst)

        self.current_interim_review_index = 0
        self.current_interim_review: fsmInterimReview = self.interim_reviews[self.current_interim_review_index]
        self.current_inst = self.a_project.dict_fsm_installs[self.current_interim_review.install_id]
        # self.current_inst_index = 0
        # self.current_inst = self.installs[self.current_inst_index]

        self.plot_axis_rg: Optional[axes.Axes] = None
        self.plot_axis_depth: Optional[axes.Axes] = None
        self.plot_axis_flow: Optional[axes.Axes] = None
        self.plot_axis_velocity: Optional[axes.Axes] = None

        self.fig_width = 14.1
        self.fig_height = 10

        self.current_plot_type = 'FM'

        self.plotCanvasReviewFM.figure.set_dpi(100)
        self.plotCanvasReviewFM.figure.set_figwidth(self.fig_width)
        self.plotCanvasReviewFM.figure.set_figheight(self.fig_height)

        self.btnPrevious.clicked.connect(self.on_previous_clicked)
        self.btnNext.clicked.connect(self.on_next_clicked)
        self.tabWidget.currentChanged.connect(self.onTabChanged)
        
        self.chk_fdv_plot_rg.clicked.connect(self.update_plot)
        self.chk_fdv_full_period.clicked.connect(self.update_plot)
        self.chk_fdv_compare_full_period.clicked.connect(self.update_plot)
        # self.btn_fdv_update.clicked.connect(self.update_plot)

        self.chk_dwf_full_period.clicked.connect(self.update_plot)
        self.chk_dwf_no_zeros.clicked.connect(self.update_plot)
        self.chk_dwf_compare_full_period.clicked.connect(self.update_plot)
        self.spin_dwf_threshold.valueChanged.connect(self.update_plot)
        self.spin_dwf_prec_dd.valueChanged.connect(self.update_plot)
        # self.btn_dwf_update.clicked.connect(self.update_plot)

        self.chk_scatter_full_period.clicked.connect(self.update_plot)
        self.chk_scatter_compare_full_period.clicked.connect(self.update_plot)
        self.chk_scatter_show_hist.stateChanged.connect(self.scatter_show_hist_state_changed)
        # self.btn_scatter_update.clicked.connect(self.update_plot)
        self.spin_scatter_depth.valueChanged.connect(self.update_plot)

        self.update_plot()
        self.plotCanvasReviewFM.scrollZoomCompleted.connect(self.update_fdv_statistics)
        # self.plotCanvasReviewFM.mouseClicked.connect(self.handle_mouse_click)

    def scatter_show_hist_state_changed(self, state):
        self.lbl_scatter_depth.setEnabled(self.chk_scatter_show_hist.isChecked())
        self.spin_scatter_depth.setEnabled(self.chk_scatter_show_hist.isChecked())
        self.update_plot()
        # self.btn_scatter_update.setEnabled(True)

    # def enable_fdv_update_button(self):
    #     """Enable the update button."""
    #     self.btn_fdv_update.setEnabled(True)

    # def enable_dwf_update_button(self):
    #     """Enable the update button."""
    #     self.btn_dwf_update.setEnabled(True)

    # def enable_scatter_update_button(self):
    #     """Enable the update button."""
    #     self.btn_scatter_update.setEnabled(True)

    def onTabChanged(self, index):
        self.update_plot()

    def update_widgets(self):

        self.chk_fm_review_complete.setChecked(self.current_interim_review.fm_complete)
        self.txt_review_comments.setText(self.current_interim_review.fm_comment)

    def update_button_states(self):
        self.btnPrevious.setEnabled(self.current_interim_review_index > 0)
        self.btnNext.setEnabled(self.current_interim_review_index < len(self.interim_reviews) - 1)
        # self.btn_fdv_update.setEnabled(False)
        # self.btn_dwf_update.setEnabled(False)        

    def dodgyForceUpdate(self):
            oldSize = self.size()
            self.resize(oldSize.width() - 1, oldSize.height() - 1)
            self.resize(oldSize)

    def update_plot(self):

        self.plotCanvasReviewFM.figure.clear()
        currentTabName = self.tabWidget.currentWidget().objectName()
        if currentTabName == 'tabFDV':
            self.plotCanvasReviewFM.scroll_zoom_enabled = True
            self.plotCanvasReviewFM.x_pan_enabled = True
            self.create_fdv_plot()
        elif currentTabName == 'tabDWF':
            self.plotCanvasReviewFM.scroll_zoom_enabled = False
            self.plotCanvasReviewFM.x_pan_enabled = False
            self.create_dwf_plot()
        elif currentTabName == 'tabScatter':
            self.plotCanvasReviewFM.scroll_zoom_enabled = False
            self.plotCanvasReviewFM.x_pan_enabled = False
            self.create_scatter_plot()

        self.update_button_states()
        self.update_widgets()            
        self.dodgyForceUpdate()

    def create_fdv_plot(self):

        filename = self.current_inst.client_ref
        i_soffit_mm = self.current_inst.fm_pipe_height_mm

        self.filter_fdv_data()

        # Create a figure and subplots
        if self.chk_fdv_plot_rg.isChecked():
            (self.plot_axis_rg, self.plot_axis_flow, self.plot_axis_depth, self.plot_axis_velocity) = self.plotCanvasReviewFM.figure.subplots(
                nrows=4, sharex=True, gridspec_kw={'height_ratios': [1, 1, 1, 1]})
        else:
            (self.plot_axis_flow, self.plot_axis_depth, self.plot_axis_velocity) = self.plotCanvasReviewFM.figure.subplots(
                nrows=3, sharex=True, gridspec_kw={'height_ratios': [1, 1, 1]})

        if self.chk_fdv_plot_rg.isChecked():
            if self.chk_fdv_compare_full_period.isChecked():
                self.plot_axis_rg.plot(self.df_rgs_compare['Date'], self.df_rgs_compare['IntensityData'], color='grey')

            self.plot_axis_rg.plot(self.df_rgs_filtered['Date'], self.df_rgs_filtered['IntensityData'], color='darkblue')
            self.plot_axis_rg.set_ylabel('Intensity (mm/hr)')
            self.plot_axis_rg.set_title(f'Flow: {filename}', loc='left', fontsize=16)  # Adding filename to title

        if self.chk_fdv_compare_full_period.isChecked():
            self.plot_axis_flow.plot(self.df_compare['Date'], self.df_compare['FlowData'], color='grey')
        self.plot_axis_flow.plot(self.df_filtered['Date'], self.df_filtered['FlowData'], color='blue')
        self.plot_axis_flow.set_ylabel('Flow (l/sec)')
        if self.chk_fdv_plot_rg.isChecked():
            self.plot_axis_flow.set_title('Flow', loc='left', fontsize=16)  # Adding filename to title
        else:
            self.plot_axis_flow.set_title(f'Flow: {filename}', loc='left', fontsize=16)  # Adding filename to title

        if self.chk_fdv_compare_full_period.isChecked():
            self.plot_axis_depth.plot(self.df_compare['Date'], self.df_compare['DepthData'], color='grey')
        i_soffit_mm_array = np.full(len(self.df_filtered), i_soffit_mm)
        self.plot_axis_depth.plot(self.df_filtered['Date'], self.df_filtered['DepthData'], color='red')
        self.plot_axis_depth.plot(self.df_filtered['Date'], i_soffit_mm_array, color='darkblue', label='Soffit')
        self.plot_axis_depth.set_ylabel('Depth (mm)')
        self.plot_axis_depth.set_title('Depth', loc='left', fontsize=16)

        # Add Soffit height label
        if self.chk_fdv_compare_full_period.isChecked():
            self.plot_axis_depth.text(self.df_compare['Date'].iloc[0], i_soffit_mm - 10, 
                                      f"Soffit Height = {i_soffit_mm}mm", color='darkblue', verticalalignment='top', horizontalalignment='left')            
        else:
            self.plot_axis_depth.text(self.df_filtered['Date'].iloc[0], i_soffit_mm - 10,
                                      f"Soffit Height = {i_soffit_mm}mm", color='darkblue', verticalalignment='top', horizontalalignment='left')

        if self.chk_fdv_compare_full_period.isChecked():
            self.plot_axis_velocity.plot(self.df_compare['Date'], self.df_compare['VelocityData'], color='grey')
        self.plot_axis_velocity.plot(self.df_filtered['Date'], self.df_filtered['VelocityData'], color='green')
        self.plot_axis_velocity.set_ylabel('Velocity (m/sec)')
        self.plot_axis_velocity.set_title('Velocity', loc='left', fontsize=16)
        self.plot_axis_velocity.set_xlabel('Date')

        # # Set x-axis major locator to midnight
        # self.plot_axis_velocity.xaxis.set_major_locator(HourLocator(byhour=0))
        # # Set the formatter for the major ticks
        # self.plot_axis_velocity.xaxis.set_major_formatter(DateFormatter("%a %d/%m/%Y"))

        # if self.chk_fdv_compare_full_period.isChecked():
        #     start_date = self.df_compare['Date'].min().replace(hour=0, minute=0, second=0, microsecond=0)  # Start from midnight of the first date
        #     minor_ticks = pd.date_range(start=start_date, end=self.df_compare['Date'].max(), freq='6h')
        # else:
        #     start_date = self.df_filtered['Date'].min().replace(hour=0, minute=0, second=0, microsecond=0)  # Start from midnight of the first date
        #     minor_ticks = pd.date_range(start=start_date, end=self.df_filtered['Date'].max(), freq='6h')

        # self.plot_axis_velocity.set_xticks(minor_ticks, minor=True)
        # self.plot_axis_velocity.set_xticklabels(self.plot_axis_velocity.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')

        # Set major and minor locators
        self.plot_axis_velocity.xaxis.set_major_locator(mpl_dates.DayLocator())
        self.plot_axis_velocity.xaxis.set_major_formatter(mpl_dates.DateFormatter("%a %d/%m/%Y"))
        # self.plot_axis_velocity.xaxis.set_minor_locator(mpl_dates.HourLocator(interval=6))
        self.plot_axis_velocity.xaxis.set_minor_locator(mpl_dates.HourLocator(byhour=[0, 6, 12, 18]))


        self.plot_axis_velocity.xaxis.set_major_formatter(mpl_dates.ConciseDateFormatter(mpl_dates.AutoDateLocator()))

        self.update_fdv_statistics()

        self.plotCanvasReviewFM.figure.subplots_adjust(left=0.15, right=0.85, bottom=0.15, top=0.85)
        self.plotCanvasReviewFM.figure.tight_layout()

    def update_fdv_y_axes(self):
        # Get the new x-axis limits from one of the axes
        new_xmin, new_xmax = mpl_dates.num2date(self.plot_axis_velocity.get_xlim())
        new_xmin = np.datetime64(new_xmin)
        new_xmax = np.datetime64(new_xmax)

        # Function to update y-axis limits for a given axis
        def update_y_limits(ax):
            all_lines = ax.get_lines()
            min_y = float('inf')
            max_y = float('-inf')

            for line in all_lines:
                x_data = line.get_xdata()
                y_data = line.get_ydata()

                mask = (x_data >= new_xmin) & (x_data <= new_xmax)
                if np.any(mask):
                    min_y = min(min_y, np.min(y_data[mask]))
                    max_y = max(max_y, np.max(y_data[mask]))

            if min_y != float('inf') and max_y != float('-inf'):
                padding = 0.1 * (max_y - min_y)  # Optional padding around the data range
                ax.set_ylim(min_y - padding, max_y + padding)

        # Update y-limits for each axis
        if self.chk_fdv_plot_rg.isChecked():
            update_y_limits(self.plot_axis_rg)
        update_y_limits(self.plot_axis_flow)
        update_y_limits(self.plot_axis_depth)
        update_y_limits(self.plot_axis_velocity)

        self.plotCanvasReviewFM.canvas.draw_idle()

    def update_fdv_statistics(self):

        self.update_fdv_y_axes()

        # Clear existing statistics text
        if self.chk_fdv_plot_rg.isChecked():
            # self.plot_axis_rg.texts.clear()
            for text in self.plot_axis_rg.texts:
                if text.get_text().startswith('Min:'):
                    text.remove()
        for artist in [self.plot_axis_flow, self.plot_axis_depth, self.plot_axis_velocity]:
            for text in artist.texts:
                if text.get_text().startswith('Min:'):  # Check if text starts with 'Min:' (or another unique identifier)
                    text.remove()

        x_min, x_max = mpl_dates.num2date(self.plot_axis_velocity.get_xlim())
        x_min = np.datetime64(x_min)
        x_max = np.datetime64(x_max)
        df_filtered = self.df_filtered[(self.df_filtered['Date'] >= x_min) & (self.df_filtered['Date'] <= x_max)].copy()

        # Calculate the time interval between the first two data points
        time_interval_seconds = (df_filtered['Date'].iloc[1] - df_filtered['Date'].iloc[0]).total_seconds()
        # Calculate total volume of flow in m³
        total_flow_volume_m3 = (df_filtered['FlowData'].sum() * time_interval_seconds) / \
            1000  # Assuming flow values are in liters per second

        if self.chk_fdv_plot_rg.isChecked():
            df_rgs_filtered = self.df_rgs_filtered[(self.df_rgs_filtered['Date'] >= x_min) & (self.df_rgs_filtered['Date'] <= x_max)]
            rain_min = df_rgs_filtered['IntensityData'].min()
            rain_max = df_rgs_filtered['IntensityData'].max()
            rain_range = rain_max - rain_min
            rain_avg = df_rgs_filtered['IntensityData'].mean()
            # rain_depth = self.df_rgs_filtered['IntensityData'].mean()

            total_rain_depth_mm = self.df_rgs_filtered['RainfallDepth_mm'].sum()

            # Add statistics to the right of the plot
            rain_stats_text = f"Min: {rain_min:.2f}\nMax: {rain_max:.2f}\nRange: {rain_range:.2f}\nAverage: {rain_avg:.2f}\nDepth (mm): {total_rain_depth_mm:.1f} mm"
            self.plot_axis_rg.text(1.02, 0.5, rain_stats_text, transform=self.plot_axis_rg.transAxes, verticalalignment='center')

        # Plotting Flow vs Date
        flow_min = df_filtered['FlowData'].min()
        flow_max = df_filtered['FlowData'].max()
        flow_range = flow_max - flow_min
        flow_avg = df_filtered['FlowData'].mean()

        # Add statistics to the right of the plot
        flow_stats_text = f"Min: {flow_min:.2f}\nMax: {flow_max:.2f}\nRange: {flow_range:.2f}\nAverage: {flow_avg:.2f}\nTotal Volume: {total_flow_volume_m3:.1f} m³"
        self.plot_axis_flow.text(1.02, 0.5, flow_stats_text, transform=self.plot_axis_flow.transAxes, verticalalignment='center')

        # Plotting Depth vs Date
        depth_min = df_filtered['DepthData'].min()
        depth_max = df_filtered['DepthData'].max()
        depth_range = depth_max - depth_min
        depth_avg = df_filtered['DepthData'].mean()

        # Add statistics to the right of the plot
        self.plot_axis_depth.text(1.02, 0.5, f"Min: {depth_min:.2f}\nMax: {depth_max:.2f}\nRange: {depth_range:.2f}\nAverage: {depth_avg:.2f}",
                                  transform=self.plot_axis_depth.transAxes, verticalalignment='center')

        # Plotting Velocity vs Date
        velocity_min = df_filtered['VelocityData'].min()
        velocity_max = df_filtered['VelocityData'].max()
        velocity_range = velocity_max - velocity_min
        velocity_avg = df_filtered['VelocityData'].mean()

        # Add statistics to the right of the plot
        self.plot_axis_velocity.text(1.02, 0.5, f"Min: {velocity_min:.2f}\nMax: {velocity_max:.2f}\nRange: {velocity_range:.2f}\nAverage: {velocity_avg:.2f}", transform=self.plot_axis_velocity.transAxes, verticalalignment='center')        

        self.plotCanvasReviewFM.canvas.draw_idle()

    # def create_fdv_plot(self):

    #     filename = self.current_inst.client_ref
    #     i_soffit_mm = self.current_inst.fm_pipe_height_mm

    #     self.filter_fdv_data()

    #     # # Calculate the time interval between the first two data points
    #     # time_interval_seconds = (self.df_filtered['Date'].iloc[1] - self.df_filtered['Date'].iloc[0]).total_seconds()
    #     # # Calculate total volume of flow in m³
    #     # total_flow_volume_m3 = (self.df_filtered['FlowData'].sum() * time_interval_seconds) / \
    #     #     1000  # Assuming flow values are in liters per second

    #     # Create a figure and subplots
    #     if self.chk_fdv_plot_rg.isChecked():
    #         (self.plot_axis_rg, self.plot_axis_flow, self.plot_axis_depth, self.plot_axis_velocity) = self.plotCanvasReviewFM.figure.subplots(
    #             nrows=4, sharex=True, gridspec_kw={'height_ratios': [1, 1, 1, 1]})
    #     else:
    #         (self.plot_axis_flow, self.plot_axis_depth, self.plot_axis_velocity) = self.plotCanvasReviewFM.figure.subplots(
    #             nrows=3, sharex=True, gridspec_kw={'height_ratios': [1, 1, 1]})

    #     if self.chk_fdv_plot_rg.isChecked():
    #         # rain_min = self.df_rgs_filtered['IntensityData'].min()
    #         # rain_max = self.df_rgs_filtered['IntensityData'].max()
    #         # rain_range = rain_max - rain_min
    #         # rain_avg = self.df_rgs_filtered['IntensityData'].mean()
    #         # # rain_depth = self.df_rgs_filtered['IntensityData'].mean()

    #         # total_rain_depth_mm = self.df_rgs_filtered['RainfallDepth_mm'].sum()

    #         if self.chk_fdv_compare_full_period.isChecked():
    #             self.plot_axis_rg.plot(self.df_rgs_compare['Date'], self.df_rgs_compare['IntensityData'], color='grey')

    #         self.plot_axis_rg.plot(self.df_rgs_filtered['Date'], self.df_rgs_filtered['IntensityData'], color='darkblue')
    #         self.plot_axis_rg.set_ylabel('Intensity (mm/hr)')
    #         self.plot_axis_rg.set_title(f'Flow: {filename}', loc='left', fontsize=16)  # Adding filename to title

    #         # # Add statistics to the right of the plot
    #         # rain_stats_text = f"Min: {rain_min:.2f}\nMax: {rain_max:.2f}\nRange: {rain_range:.2f}\nAverage: {rain_avg:.2f}\nDepth (mm): {total_rain_depth_mm:.1f} mm"
    #         # self.plot_axis_rg.text(1.02, 0.5, rain_stats_text, transform=self.plot_axis_rg.transAxes, verticalalignment='center')

    #     # # Plotting Flow vs Date
    #     # flow_min = self.df_filtered['FlowData'].min()
    #     # flow_max = self.df_filtered['FlowData'].max()
    #     # flow_range = flow_max - flow_min
    #     # flow_avg = self.df_filtered['FlowData'].mean()

    #     if self.chk_fdv_compare_full_period.isChecked():
    #         self.plot_axis_flow.plot(self.df_compare['Date'], self.df_compare['FlowData'], color='grey')
    #     self.plot_axis_flow.plot(self.df_filtered['Date'], self.df_filtered['FlowData'], color='blue')
    #     self.plot_axis_flow.set_ylabel('Flow (l/sec)')
    #     if self.chk_fdv_plot_rg.isChecked():
    #         self.plot_axis_flow.set_title('Flow', loc='left', fontsize=16)  # Adding filename to title
    #     else:
    #         self.plot_axis_flow.set_title(f'Flow: {filename}', loc='left', fontsize=16)  # Adding filename to title

    #     # # Add statistics to the right of the plot
    #     # flow_stats_text = f"Min: {flow_min:.2f}\nMax: {flow_max:.2f}\nRange: {flow_range:.2f}\nAverage: {flow_avg:.2f}\nTotal Volume: {total_flow_volume_m3:.1f} m³"
    #     # self.plot_axis_flow.text(1.02, 0.5, flow_stats_text, transform=self.plot_axis_flow.transAxes, verticalalignment='center')

    #     # # Plotting Depth vs Date
    #     # depth_min = self.df_filtered['DepthData'].min()
    #     # depth_max = self.df_filtered['DepthData'].max()
    #     # depth_range = depth_max - depth_min
    #     # depth_avg = self.df_filtered['DepthData'].mean()

    #     if self.chk_fdv_compare_full_period.isChecked():
    #         self.plot_axis_depth.plot(self.df_compare['Date'], self.df_compare['DepthData'], color='grey')
    #     i_soffit_mm_array = np.full(len(self.df_filtered), i_soffit_mm)
    #     self.plot_axis_depth.plot(self.df_filtered['Date'], self.df_filtered['DepthData'], color='red')
    #     self.plot_axis_depth.plot(self.df_filtered['Date'], i_soffit_mm_array, color='darkblue', label='Soffit')
    #     self.plot_axis_depth.set_ylabel('Depth (mm)')
    #     self.plot_axis_depth.set_title('Depth', loc='left', fontsize=16)

    #     # Add Soffit height label
    #     if self.chk_fdv_compare_full_period.isChecked():
    #         self.plot_axis_depth.text(self.df_compare['Date'].iloc[0], i_soffit_mm - 10, 
    #                                   f"Soffit Height = {i_soffit_mm}mm", color='darkblue', verticalalignment='top', horizontalalignment='left')            
    #     else:
    #         self.plot_axis_depth.text(self.df_filtered['Date'].iloc[0], i_soffit_mm - 10,
    #                                   f"Soffit Height = {i_soffit_mm}mm", color='darkblue', verticalalignment='top', horizontalalignment='left')

    #     # # Add statistics to the right of the plot
    #     # self.plot_axis_depth.text(1.02, 0.5, f"Min: {depth_min:.2f}\nMax: {depth_max:.2f}\nRange: {depth_range:.2f}\nAverage: {depth_avg:.2f}", transform=self.plot_axis_depth.transAxes, verticalalignment='center')

    #     # # Plotting Velocity vs Date
    #     # velocity_min = self.df_filtered['VelocityData'].min()
    #     # velocity_max = self.df_filtered['VelocityData'].max()
    #     # velocity_range = velocity_max - velocity_min
    #     # velocity_avg = self.df_filtered['VelocityData'].mean()

    #     if self.chk_fdv_compare_full_period.isChecked():
    #         self.plot_axis_velocity.plot(self.df_compare['Date'], self.df_compare['VelocityData'], color='grey')
    #     self.plot_axis_velocity.plot(self.df_filtered['Date'], self.df_filtered['VelocityData'], color='green')
    #     self.plot_axis_velocity.set_ylabel('Velocity (m/sec)')
    #     self.plot_axis_velocity.set_title('Velocity', loc='left', fontsize=16)
    #     self.plot_axis_velocity.set_xlabel('Date')

    #     # # Add statistics to the right of the plot
    #     # self.plot_axis_velocity.text(1.02, 0.5, f"Min: {velocity_min:.2f}\nMax: {velocity_max:.2f}\nRange: {velocity_range:.2f}\nAverage: {velocity_avg:.2f}", transform=self.plot_axis_velocity.transAxes, verticalalignment='center')
    #     # Set x-axis major locator to midnight
    #     self.plot_axis_velocity.xaxis.set_major_locator(HourLocator(byhour=0))
    #     # Set the formatter for the major ticks
    #     self.plot_axis_velocity.xaxis.set_major_formatter(DateFormatter("%a %d/%m/%Y"))

    #     if self.chk_fdv_compare_full_period.isChecked():
    #         start_date = self.df_compare['Date'].min().replace(hour=0, minute=0, second=0, microsecond=0)  # Start from midnight of the first date
    #         minor_ticks = pd.date_range(start=start_date, end=self.df_compare['Date'].max(), freq='6h')
    #     else:
    #         start_date = self.df_filtered['Date'].min().replace(hour=0, minute=0, second=0, microsecond=0)  # Start from midnight of the first date
    #         minor_ticks = pd.date_range(start=start_date, end=self.df_filtered['Date'].max(), freq='6h')

    #     # self.plot_axis_velocity.set_xticks(self.plot_axis_velocity.get_xticks())  # Ensure ticks are set
    #     self.plot_axis_velocity.set_xticks(minor_ticks, minor=True)
    #     self.plot_axis_velocity.set_xticklabels(self.plot_axis_velocity.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')

    #     # # Adjust layout
    #     # self.plotCanvasReviewFM.figure.tight_layout()

    #     self.update_fdv_statistics()
    #     # # Show plot
    #     # self.plotCanvasReviewFM.canvas.show()

    # def update_fdv_statistics(self):

    #     x_min, x_max = mpl_dates.num2date(self.plot_axis_velocity.get_xlim())
    #     x_min = np.datetime64(x_min)
    #     x_max = np.datetime64(x_max)
    #     df_filtered = self.df_filtered[(self.df_filtered['Date'] >= x_min) & (self.df_filtered['Date'] <= x_max)].copy()

    #     # Calculate the time interval between the first two data points
    #     time_interval_seconds = (df_filtered['Date'].iloc[1] - df_filtered['Date'].iloc[0]).total_seconds()
    #     # Calculate total volume of flow in m³
    #     total_flow_volume_m3 = (df_filtered['FlowData'].sum() * time_interval_seconds) / \
    #         1000  # Assuming flow values are in liters per second

    #     if self.chk_fdv_plot_rg.isChecked():
    #         df_rgs_filtered = self.df_rgs_filtered[(self.df_rgs_filtered['Date'] >= x_min) & (self.df_rgs_filtered['Date'] <= x_max)]
    #         rain_min = df_rgs_filtered['IntensityData'].min()
    #         rain_max = df_rgs_filtered['IntensityData'].max()
    #         rain_range = rain_max - rain_min
    #         rain_avg = df_rgs_filtered['IntensityData'].mean()
    #         # rain_depth = self.df_rgs_filtered['IntensityData'].mean()

    #         total_rain_depth_mm = self.df_rgs_filtered['RainfallDepth_mm'].sum()

    #         # Add statistics to the right of the plot
    #         rain_stats_text = f"Min: {rain_min:.2f}\nMax: {rain_max:.2f}\nRange: {rain_range:.2f}\nAverage: {rain_avg:.2f}\nDepth (mm): {total_rain_depth_mm:.1f} mm"
    #         self.plot_axis_rg.text(1.02, 0.5, rain_stats_text, transform=self.plot_axis_rg.transAxes, verticalalignment='center')

    #     # Plotting Flow vs Date
    #     flow_min = df_filtered['FlowData'].min()
    #     flow_max = df_filtered['FlowData'].max()
    #     flow_range = flow_max - flow_min
    #     flow_avg = df_filtered['FlowData'].mean()

    #     # Add statistics to the right of the plot
    #     flow_stats_text = f"Min: {flow_min:.2f}\nMax: {flow_max:.2f}\nRange: {flow_range:.2f}\nAverage: {flow_avg:.2f}\nTotal Volume: {total_flow_volume_m3:.1f} m³"
    #     self.plot_axis_flow.text(1.02, 0.5, flow_stats_text, transform=self.plot_axis_flow.transAxes, verticalalignment='center')

    #     # Plotting Depth vs Date
    #     depth_min = df_filtered['DepthData'].min()
    #     depth_max = df_filtered['DepthData'].max()
    #     depth_range = depth_max - depth_min
    #     depth_avg = df_filtered['DepthData'].mean()

    #     # Add statistics to the right of the plot
    #     self.plot_axis_depth.text(1.02, 0.5, f"Min: {depth_min:.2f}\nMax: {depth_max:.2f}\nRange: {depth_range:.2f}\nAverage: {depth_avg:.2f}",
    #                               transform=self.plot_axis_depth.transAxes, verticalalignment='center')

    #     # Plotting Velocity vs Date
    #     velocity_min = df_filtered['VelocityData'].min()
    #     velocity_max = df_filtered['VelocityData'].max()
    #     velocity_range = velocity_max - velocity_min
    #     velocity_avg = df_filtered['VelocityData'].mean()

    #     # Add statistics to the right of the plot
    #     self.plot_axis_velocity.text(1.02, 0.5, f"Min: {velocity_min:.2f}\nMax: {velocity_max:.2f}\nRange: {velocity_range:.2f}\nAverage: {velocity_avg:.2f}", transform=self.plot_axis_velocity.transAxes, verticalalignment='center')        

    #     self.plotCanvasReviewFM.canvas.draw_idle()

    # def update_statistics(self):
    #     x_min, x_max = self.plot_axis_velocity.get_xlim()
    #     df_filtered = self.df_filtered[(self.df_filtered['Date'] >= x_min) & (self.df_filtered['Date'] <= x_max)]

    #     if self.plot_axis_rg:
    #         df_rgs_filtered = self.df_rgs_filtered[(self.df_rgs_filtered['Date'] >= x_min) & (self.df_rgs_filtered['Date'] <= x_max)]
    #         rain_min = df_rgs_filtered['IntensityData'].min()
    #         rain_max = df_rgs_filtered['IntensityData'].max()
    #         rain_range = rain_max - rain_min
    #         rain_avg = df_rgs_filtered['IntensityData'].mean()
    #         total_rain_depth_mm = df_rgs_filtered['RainfallDepth_mm'].sum()
    #         rain_stats_text = f"Min: {rain_min:.2f}\nMax: {rain_max:.2f}\nRange: {rain_range:.2f}\nAverage: {rain_avg:.2f}\nDepth (mm): {total_rain_depth_mm:.1f} mm"
    #         self.plot_axis_rg.text(1.02, 0.5, rain_stats_text, transform=self.plot_axis_rg.transAxes, verticalalignment='center')

    #     if self.plot_axis_flow:
    #         flow_min = df_filtered['FlowData'].min()
    #         flow_max = df_filtered['FlowData'].max()
    #         flow_range = flow_max - flow_min
    #         flow_avg = df_filtered['FlowData'].mean()
    #         time_interval_seconds = (df_filtered['Date'].iloc[1] - df_filtered['Date'].iloc[0]).total_seconds()
    #         total_flow_volume_m3 = (df_filtered['FlowData'].sum() * time_interval_seconds) / 1000
    #         flow_stats_text = f"Min: {flow_min:.2f}\nMax: {flow_max:.2f}\nRange: {flow_range:.2f}\nAverage: {flow_avg:.2f}\nTotal Volume: {total_flow_volume_m3:.1f} m³"
    #         self.plot_axis_flow.text(1.02, 0.5, flow_stats_text, transform=self.plot_axis_flow.transAxes, verticalalignment='center')

    #     if self.plot_axis_depth:
    #         depth_min = df_filtered['DepthData'].min()
    #         depth_max = df_filtered['DepthData'].max()
    #         depth_range = depth_max - depth_min
    #         depth_avg = df_filtered['DepthData'].mean()
    #         self.plot_axis_depth.text(1.02, 0.5, f"Min: {depth_min:.2f}\nMax: {depth_max:.2f}\nRange: {depth_range:.2f}\nAverage: {depth_avg:.2f}",
    #                                 transform=self.plot_axis_depth.transAxes, verticalalignment='center')

    #     if self.plot_axis_velocity:
    #         velocity_min = df_filtered['VelocityData'].min()
    #         velocity_max = df_filtered['VelocityData'].max()
    #         velocity_range = velocity_max - velocity_min
    #         velocity_avg = df_filtered['VelocityData'].mean()
    #         self.plot_axis_velocity.text(1.02, 0.5, f"Min: {velocity_min:.2f}\nMax: {velocity_max:.2f}\nRange: {velocity_range:.2f}\nAverage: {velocity_avg:.2f}",
    #                                     transform=self.plot_axis_velocity.transAxes, verticalalignment='center')

    #     self.plotCanvasReviewFM.canvas.draw_idle()

    def create_scatter_plot(self):

        self.filter_scatter_data()

        # Filter out invalid pairs
        valid_pairs_mask = (self.df_filtered['FlowData'] > 0) & (self.df_filtered['DepthData'] > 0)
        valid_fdv_data = self.df_filtered[valid_pairs_mask]
        i_soffit_mm = self.current_inst.fm_pipe_height_mm

        # Category 1: Anything below 100mm likely affected by poor flow conditions
        cat_1_val = np.log(100)
        cat_1_text = "Cat.1: <100mm (Data probably inacurate due to poor flow conditions)"

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
            cat_3_text = "Cat.3: <30% of sewer height (Scatter of data gradually reduce)"

        # Category 4: Anything below 50% of sewer height is likely to show very little scatter
        cat_4_val = np.log(0.5 * i_soffit_mm)
        cat_4_text = "Cat.4: <50% of sewer height (Very little scatter of data)"

        # Category 4: Anything below 50% of sewer height is likely to show very little scatter
        cat_5_val = np.log(i_soffit_mm)
        cat_5_text = "Cat.5: Sewer Height (Minimal scatter of data)"

        # Log-transformed data of valid pairs
        log_flow = np.log(valid_fdv_data['FlowData'])
        log_depth = np.log(valid_fdv_data['DepthData'])

        if self.chk_scatter_show_hist.isChecked():
            gs = self.plotCanvasReviewFM.figure.add_gridspec(2, 2, width_ratios=[40, 1], height_ratios=[1, 3], hspace=0.05)
            self.plot_axis_scatter = self.plotCanvasReviewFM.figure.add_subplot(gs[1, 0])
            self.plot_axis_hist = self.plotCanvasReviewFM.figure.add_subplot(gs[0, 0], sharex=self.plot_axis_scatter)
            cbar_ax = self.plotCanvasReviewFM.figure.add_subplot(gs[:, 1])
        else:
            gs = self.plotCanvasReviewFM.figure.add_gridspec(1, 2, width_ratios=[40, 1])
            self.plot_axis_scatter = self.plotCanvasReviewFM.figure.add_subplot(gs[0, 0])
            cbar_ax = self.plotCanvasReviewFM.figure.add_subplot(gs[0, 1])

        # 1. Compute the valid pairs and log-transformed data for comparison
        if self.chk_scatter_compare_full_period.isChecked():
            valid_comp_pairs_mask = (self.df_compare['FlowData'] > 0) & (self.df_compare['DepthData'] > 0)
            valid_comp_fdv_data = self.df_compare[valid_comp_pairs_mask]            
            log_comp_flow = np.log(valid_comp_fdv_data['FlowData'])
            log_comp_depth = np.log(valid_comp_fdv_data['DepthData'])

            # 2. Compute hexbin counts for comparison dataset
            hb_comp = self.plot_axis_scatter.hexbin(log_comp_flow, log_comp_depth, gridsize=40)
            comp_counts = hb_comp.get_array()
            self.plot_axis_scatter.clear()

            # 2. Compute hexbin counts for primary dataset
            hb = self.plot_axis_scatter.hexbin(log_flow, log_depth, gridsize=40)
            primary_counts = hb.get_array()
            self.plot_axis_scatter.clear()

            # 3. Find the maximum count value from both datasets
            max_count = max(comp_counts.max(), primary_counts.max())

            # 4. Set a common normalization for both plots
            common_norm = mcolors.LogNorm(vmin=1, vmax=max_count)

            hb_comp = self.plot_axis_scatter.hexbin(log_comp_flow, log_comp_depth, gridsize=40, cmap='Greys', norm=common_norm)

            # Plot the primary dataset with the common norm
            hb = self.plot_axis_scatter.hexbin(log_flow, log_depth, gridsize=40, cmap='GnBu', norm=common_norm)
        else:
            # Plot the primary dataset with the common norm
            hb = self.plot_axis_scatter.hexbin(log_flow, log_depth, gridsize=40, cmap='GnBu', norm=mcolors.LogNorm())

        cb = self.plotCanvasReviewFM.figure.colorbar(hb, cax=cbar_ax, format='%d')
        cb.set_label('Counts', color='blue')
        cb.ax.yaxis.set_tick_params(color='blue')
        plt.setp(plt.getp(cb.ax.axes, 'yticklabels'), color='blue')

        self.plot_axis_scatter.plot([log_flow.min(), log_flow.max()], [np.log(i_soffit_mm), np.log(i_soffit_mm)], color='darkblue', linestyle='--', label='Soffit')
        self.plot_axis_scatter.text(log_flow.min(), np.log(i_soffit_mm), 'Soffit', color='darkblue', verticalalignment='bottom', horizontalalignment='left')

        self.plot_axis_scatter.plot([log_flow.min(), log_flow.max()], [cat_1_val, cat_1_val], color='red', linestyle='--', label=cat_1_text)
        self.plot_axis_scatter.text(log_flow.min(), cat_1_val, cat_1_text, color='red', verticalalignment='top', horizontalalignment='left')

        if cat_2_val > cat_1_val:
            self.plot_axis_scatter.plot([log_flow.min(), log_flow.max()], [cat_2_val, cat_2_val], color='red', linestyle='--', label=cat_2_text)
            self.plot_axis_scatter.text(log_flow.min(), cat_2_val, cat_2_text, color='red', verticalalignment='top', horizontalalignment='left')

        if cat_3_val > cat_2_val and cat_3_val > cat_1_val:
            self.plot_axis_scatter.plot([log_flow.min(), log_flow.max()], [cat_3_val, cat_3_val], color='red', linestyle='--', label=cat_3_text)
            self.plot_axis_scatter.text(log_flow.min(), cat_3_val, cat_3_text, color='red', verticalalignment='top', horizontalalignment='left')

        if cat_4_val > cat_3_val and cat_4_val > cat_2_val and cat_4_val > cat_1_val:
            self.plot_axis_scatter.plot([log_flow.min(), log_flow.max()], [cat_4_val, cat_4_val], color='red', linestyle='--', label=cat_4_text)
            self.plot_axis_scatter.text(log_flow.min(), cat_4_val, cat_4_text, color='red', verticalalignment='top', horizontalalignment='left')

        if cat_5_val > cat_4_val and cat_5_val > cat_3_val and cat_5_val > cat_2_val and cat_5_val > cat_1_val:
            self.plot_axis_scatter.plot([log_flow.min(), log_flow.max()], [cat_5_val, cat_5_val], color='red', linestyle='--', label=cat_5_text)
            self.plot_axis_scatter.text(log_flow.min(), cat_5_val, cat_5_text, color='red',
                                        verticalalignment='top', horizontalalignment='left')

        if not self.chk_scatter_show_hist.isChecked():
            self.plot_axis_scatter.set_title('2D Histogram of Log Flow vs Log Depth')
        self.plot_axis_scatter.set_xlabel('Log Flow')
        self.plot_axis_scatter.set_ylabel('Log Depth')

        # Get existing x-axis ticks (now they are integer positions), convert them to non-log values, and set as labels
        x_ticks = self.plot_axis_scatter.get_xticks()
        x_labels = [f"{np.exp(value):.1f}" for value in x_ticks]
        self.plot_axis_scatter.set_xticklabels(x_labels)

        # Get existing y-axis ticks (now they are integer positions), convert them to non-log values, and set as labels
        y_ticks = self.plot_axis_scatter.get_yticks()
        y_labels = [f"{int(np.round(np.exp(value)))}" for value in y_ticks]
        self.plot_axis_scatter.set_yticklabels(y_labels)

        if self.chk_scatter_show_hist.isChecked():
            depth_val = self.spin_scatter_depth.value()
            specified_log_depth = np.log(depth_val)
            flow_values_at_depth = np.log(valid_fdv_data['FlowData'][np.isclose(log_depth, specified_log_depth, atol=0.1)])

            self.plot_axis_hist.hist(flow_values_at_depth, bins=30, color='skyblue', edgecolor='black')
            self.plot_axis_hist.set_title('2D Histogram of Log Flow vs Log Depth')
            self.plot_axis_hist.set_ylabel('Frequency')
            self.plot_axis_scatter.plot([log_flow.min(), log_flow.max()], [
                                        specified_log_depth, specified_log_depth], color='deepskyblue', linestyle='--', label=f'Flow/Depth Relationship @ {depth_val} mm')
            self.plot_axis_scatter.text(log_flow.max(), specified_log_depth, f'{depth_val} mm', color='deepskyblue', verticalalignment='bottom', horizontalalignment='right')
            plt.setp(self.plot_axis_hist.get_xticklabels(), visible=False)
            
        # Adjust layout
        self.plotCanvasReviewFM.figure.tight_layout()

        self.plotCanvasReviewFM.canvas.draw()

    def create_dwf_plot(self):
        filename = self.current_inst.client_ref
        i_soffit_mm = self.current_inst.fm_pipe_height_mm

        self.filter_dwf_data()

        if self.df_dwf_filtered.empty:
            # Create a figure with a single subplot
            ax = self.plotCanvasReviewFM.figure.subplots()
            ax.text(0.5, 0.5, 'No dry days identified', horizontalalignment='center', verticalalignment='center', fontsize=16)
            ax.set_axis_off()  # Hide the axes
            # self.plotCanvasReviewFM.figure = fig
            return

        # # Extract the time of day in seconds from midnight
        # self.df_dwf_filtered['TimeOfDay'] = self.df_dwf_filtered['Date'].dt.hour * 3600 + \
        #     self.df_dwf_filtered['Date'].dt.minute * 60 + self.df_dwf_filtered['Date'].dt.second

        # Create a figure and subplots
        (self.plot_axis_flow, self.plot_axis_depth, self.plot_axis_velocity) = self.plotCanvasReviewFM.figure.subplots(
            nrows=3, sharex=True, gridspec_kw={'height_ratios': [1, 1, 1]}
        )

        if self.chk_dwf_compare_full_period.isChecked():
            # Group the data by day
            grouped = self.df_dwf_compare.groupby(self.df_dwf_compare['Date'].dt.date)

            for day, group in grouped:
                # Plot Flow vs Time of Day
                self.plot_axis_flow.plot(group['TimeOfDay'], group['FlowData'], color='lightgrey')

                # Plot Depth vs Time of Day
                self.plot_axis_depth.plot(group['TimeOfDay'], group['DepthData'], color='lightgrey')

                # Plot Velocity vs Time of Day
                self.plot_axis_velocity.plot(group['TimeOfDay'], group['VelocityData'], color='lightgrey')

        # Group the data by day
        grouped = self.df_dwf_filtered.groupby(self.df_dwf_filtered['Date'].dt.date)

        for day, group in grouped:
            # Plot Flow vs Time of Day
            self.plot_axis_flow.plot(group['TimeOfDay'], group['FlowData'], color='lightblue')

            # Plot Depth vs Time of Day
            self.plot_axis_depth.plot(group['TimeOfDay'], group['DepthData'], color='lightsalmon')

            # Plot Velocity vs Time of Day
            self.plot_axis_velocity.plot(group['TimeOfDay'], group['VelocityData'], color='palegreen')
                    
        self.plot_axis_depth.plot(self.df_dwf_average['TimeOfDay'], [i_soffit_mm] *
                                  len(self.df_dwf_average), color='darkblue', linestyle='--', label='Soffit')

        if self.chk_dwf_compare_full_period.isChecked():
            self.plot_axis_flow.plot(self.df_dwf_compare_average['TimeOfDay'], self.df_dwf_compare_average['AvgFlowData'], color='grey')
            self.plot_axis_depth.plot(self.df_dwf_compare_average['TimeOfDay'], self.df_dwf_compare_average['AvgDepthData'], color='grey')
            self.plot_axis_velocity.plot(self.df_dwf_compare_average['TimeOfDay'], self.df_dwf_compare_average['AvgVelocityData'], color='grey')
            
        self.plot_axis_flow.plot(self.df_dwf_average['TimeOfDay'], self.df_dwf_average['AvgFlowData'], color='blue')
        self.plot_axis_depth.plot(self.df_dwf_average['TimeOfDay'], self.df_dwf_average['AvgDepthData'], color='red')
        self.plot_axis_velocity.plot(self.df_dwf_average['TimeOfDay'], self.df_dwf_average['AvgVelocityData'], color='green')

        # Add labels and titles
        self.plot_axis_flow.set_ylabel('Flow (l/sec)')
        self.plot_axis_flow.set_title(f'Flow: {filename}', loc='left', fontsize=16)

        self.plot_axis_depth.set_ylabel('Depth (mm)')
        self.plot_axis_depth.set_title('Depth', loc='left', fontsize=16)
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

        # # Optional: Add legend
        # self.plot_axis_flow.legend(loc='upper right')
        # self.plot_axis_depth.legend(loc='upper right')
        # self.plot_axis_velocity.legend(loc='upper right')


    # def create_dwf_plot(self):

    #     filename = 'temp.filename'
    #     i_soffit_mm = self.current_inst.fm_pipe_height_mm

    #     self.filter_dwf_data()

    #     self.df_dwf_filtered['TimeOfDay'] = self.df_dwf_filtered['Date'].dt.hour * 3600 + self.df_dwf_filtered['Date'].dt.minute * 60 + self.df_dwf_filtered['Date'].dt.second

    #     # self.df_filtered['TimeOfDay'] = self.df_filtered['Date'].dt.time

    #     # # import matplotlib.pyplot as plt
    #     # # Calculate the time interval between the first two data points
    #     # time_interval_seconds = (self.df_filtered['Date'].iloc[1] - self.df_filtered['Date'].iloc[0]).total_seconds()
    #     # # Calculate total volume of flow in m³
    #     # total_flow_volume_m3 = (self.df_filtered['FlowData'].sum() * time_interval_seconds) / \
    #     #     1000  # Assuming flow values are in liters per second

    #     # Create a figure and subplots
    #     (self.plot_axis_flow, self.plot_axis_depth, self.plot_axis_velocity) = self.plotCanvasReviewFM.figure.subplots(
    #         nrows=3, sharex=True, gridspec_kw={'height_ratios': [1, 1, 1]})

    #     # Plotting Flow vs Date
    #     flow_min = self.df_dwf_filtered['FlowData'].min()
    #     flow_max = self.df_dwf_filtered['FlowData'].max()
    #     flow_range = flow_max - flow_min
    #     flow_avg = self.df_dwf_filtered['FlowData'].mean()

    #     self.plot_axis_flow.plot(self.df_dwf_filtered['TimeOfDay'], self.df_dwf_filtered['FlowData'], color='blue')
    #     self.plot_axis_flow.set_ylabel('Flow (l/sec)')
    #     self.plot_axis_flow.set_title(f'Flow: {filename}', loc='left', fontsize=16)  # Adding filename to title

    #     # Add statistics to the right of the plot
    #     flow_stats_text = f"Min: {flow_min:.2f}\nMax: {flow_max:.2f}\nRange: {flow_range:.2f}\nAverage: {flow_avg:.2f}"
    #     self.plot_axis_flow.text(1.02, 0.5, flow_stats_text, transform=self.plot_axis_flow.transAxes, verticalalignment='center')

    #     # Plotting Depth vs Date
    #     depth_min = self.df_dwf_filtered['DepthData'].min()
    #     depth_max = self.df_dwf_filtered['DepthData'].max()
    #     depth_range = depth_max - depth_min
    #     depth_avg = self.df_dwf_filtered['DepthData'].mean()

    #     i_soffit_mm_array = np.full(len(self.df_dwf_filtered), i_soffit_mm)
    #     self.plot_axis_depth.plot(self.df_dwf_filtered['TimeOfDay'], self.df_dwf_filtered['DepthData'], color='red')
    #     self.plot_axis_depth.plot(self.df_dwf_filtered['TimeOfDay'], i_soffit_mm_array, color='darkblue', label='Soffit')
    #     self.plot_axis_depth.set_ylabel('Depth (mm)')
    #     self.plot_axis_depth.set_title('Depth', loc='left', fontsize=16)

    #     # Add Soffit height label
    #     self.plot_axis_depth.text(self.df_dwf_filtered['TimeOfDay'].iloc[0], i_soffit_mm - 10,
    #                               f"Soffit Height = {i_soffit_mm}mm", color='darkblue', verticalalignment='top', horizontalalignment='left')

    #     # Add statistics to the right of the plot
    #     self.plot_axis_depth.text(
    #         1.02, 0.5, f"Min: {depth_min:.2f}\nMax: {depth_max:.2f}\nRange: {depth_range:.2f}\nAverage: {depth_avg:.2f}", transform=self.plot_axis_depth.transAxes, verticalalignment='center')

    #     # Plotting Velocity vs Date
    #     velocity_min = self.df_dwf_filtered['VelocityData'].min()
    #     velocity_max = self.df_dwf_filtered['VelocityData'].max()
    #     velocity_range = velocity_max - velocity_min
    #     velocity_avg = self.df_dwf_filtered['VelocityData'].mean()

    #     self.plot_axis_velocity.plot(self.df_dwf_filtered['TimeOfDay'], self.df_dwf_filtered['VelocityData'], color='green')
    #     self.plot_axis_velocity.set_ylabel('Velocity (m/sec)')
    #     self.plot_axis_velocity.set_title('Velocity', loc='left', fontsize=16)
    #     self.plot_axis_velocity.set_xlabel('Time of Day')

    #     # Add statistics to the right of the plot
    #     self.plot_axis_velocity.text(1.02, 0.5, f"Min: {velocity_min:.2f}\nMax: {velocity_max:.2f}\nRange: {velocity_range:.2f}\nAverage: {velocity_avg:.2f}",
    #                                  transform=self.plot_axis_velocity.transAxes, verticalalignment='center')

        # # Set x-axis major locator to hour
        # self.plot_axis_velocity.xaxis.set_major_locator(HourLocator(interval=1))
        # # Set the formatter for the major ticks
        # self.plot_axis_velocity.xaxis.set_major_formatter(DateFormatter("%H:%M"))

        # Set x-axis major locator to hour
        self.plot_axis_velocity.xaxis.set_major_locator(ticker.MultipleLocator(3600))
        # Custom formatter for the x-axis to display HH:MM
        def format_func(value, tick_number):
            hours = int(value // 3600)
            minutes = int((value % 3600) // 60)
            return f'{hours:02d}:{minutes:02d}'
        self.plot_axis_velocity.xaxis.set_major_formatter(ticker.FuncFormatter(format_func))
        
        # # Set x-axis major locator to midnight
        # self.plot_axis_velocity.xaxis.set_major_locator(HourLocator(byhour=0))
        # # Set the formatter for the major ticks
        # self.plot_axis_velocity.xaxis.set_major_formatter(DateFormatter("%a %d/%m/%Y"))

        # start_date = self.df_filtered['Date'].min().replace(hour=0, minute=0, second=0, microsecond=0)  # Start from midnight of the first date
        # minor_ticks = pd.date_range(start=start_date, end=self.df_filtered['TimeOfDay'].max(), freq='6h')

        # self.plot_axis_velocity.set_xticks(self.plot_axis_velocity.get_xticks())  # Ensure ticks are set
        # self.plot_axis_velocity.set_xticks(minor_ticks, minor=True)
        self.plot_axis_velocity.set_xticklabels(self.plot_axis_velocity.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')
        
        # # Plot data for each instance
        # self.plot_axis_depth.plot(self.merged_df['Date'], self.merged_df['DepthData_y'], color='grey')
        # self.plot_axis_flow.plot(self.merged_df['Date'], self.merged_df['FlowData_y'], color='grey')
        # self.plot_axis_velocity.plot(self.merged_df['Date'], self.merged_df['VelocityData_y'], color='grey')

        # Adjust layout
        self.plotCanvasReviewFM.figure.tight_layout()

        # Show plot
        self.plotCanvasReviewFM.canvas.show()

    def on_previous_clicked(self):

        if self.current_interim_review_index > 0:
            self.current_interim_review_index -= 1
            self.update_interim_review()
            self.current_interim_review = self.interim_reviews[self.current_interim_review_index]
            self.current_inst = self.a_project.dict_fsm_installs[self.current_interim_review.install_id]
            self.update_plot()
            self.update_widgets()
            self.update_button_states()

    def on_next_clicked(self):
        if self.current_interim_review_index < len(self.interim_reviews) - 1:
            self.current_interim_review_index += 1
            self.update_interim_review()
            self.current_interim_review = self.interim_reviews[self.current_interim_review_index]
            self.current_inst = self.a_project.dict_fsm_installs[self.current_interim_review.install_id]
            self.update_plot()
            self.update_widgets()
            self.update_button_states()

    def update_interim_review(self):

        self.current_interim_review.fm_complete = self.chk_fm_review_complete.isChecked()
        self.current_interim_review.fm_comment = self.txt_review_comments.text()



    # def createPlot(self):
    #     self.filter_data()
    #     self.setup_axes()
    #     self.create_legend()
    #     self.plot_data()
    #     self.add_classifications()
    #     self.add_statistics()
    #     self.finalize_plot()

    def filter_fdv_data(self):

        if self.chk_fdv_full_period.isChecked():
            self.df_filtered = self.current_inst.data.copy()
        else:
            self.df_filtered = self.current_inst.data[(self.current_inst.data['Date'] >= self.start_date)
                                                      & (self.current_inst.data['Date'] <= self.end_date)].copy()

        if self.chk_fdv_compare_full_period.isChecked():
            self.df_compare = self.current_inst.data.copy()
        
        if self.chk_fdv_plot_rg.isChecked():
            all_rainfall_data = []

            for a_inst in self.a_project.dict_fsm_installs.values():
                if a_inst.install_type == 'Rain Gauge':
                    a_instance_rainfall_data = a_inst.data[['Date', 'IntensityData']].copy()
                    a_instance_rainfall_data['RainfallDepth_mm'] = a_instance_rainfall_data['IntensityData'] * (a_inst.data_interval / 60)
                    all_rainfall_data.append(a_instance_rainfall_data)

            if all_rainfall_data:
                combined_rainfall_data = pd.concat(all_rainfall_data)
                average_rainfall_data = combined_rainfall_data.groupby('Date', as_index=False).agg({
                'IntensityData': 'mean',
                'RainfallDepth_mm': 'mean'
                })
                # average_rainfall_data = combined_rainfall_data.groupby('Date', as_index=False)['IntensityData'].mean()
            else:
                average_rainfall_data = pd.DataFrame(columns=['Date', 'IntensityData', 'RainfallDepth_mm'])

            if self.chk_fdv_full_period.isChecked():
                self.df_rgs_filtered = average_rainfall_data.copy()
            else:    
                self.df_rgs_filtered = average_rainfall_data[(average_rainfall_data['Date'] >= self.start_date)
                                                             & (average_rainfall_data['Date'] <= self.end_date)].copy()
                
            if self.chk_fdv_compare_full_period.isChecked():
                self.df_rgs_compare = average_rainfall_data.copy()
                
    def filter_scatter_data(self):

        if self.chk_scatter_full_period.isChecked():
            self.df_filtered = self.current_inst.data.copy()
        else:
            self.df_filtered = self.current_inst.data[(self.current_inst.data['Date'] >= self.start_date)
                                                      & (self.current_inst.data['Date'] <= self.end_date)].copy()
                        
        if self.chk_scatter_compare_full_period.isChecked():
            self.df_compare = self.current_inst.data.copy()

    def filter_dwf_data(self):

        if self.chk_dwf_full_period.isChecked():
            self.df_filtered = self.current_inst.data.copy()
        else:
            self.df_filtered = self.current_inst.data[(self.current_inst.data['Date'] >= self.start_date)
                                                      & (self.current_inst.data['Date'] <= self.end_date)].copy()

        if self.chk_dwf_compare_full_period.isChecked():
            self.df_compare = self.current_inst.data.copy()
            
        # Initialize an empty list to collect daily rainfall data
        all_daily_rainfall = []

        dwf_threshold = self.spin_dwf_threshold.value()
        preceeding_dry_days = self.spin_dwf_prec_dd.value()

        # Assuming self.a_project.dict_fsm_installs is a dictionary of instances
        for a_inst in self.a_project.dict_fsm_installs.values():
            if a_inst.install_type == 'Rain Gauge':
                # Copy relevant data
                df_dwf = a_inst.data[['Date', 'IntensityData']].copy()
                # df_dwf['Date'] = pd.to_datetime(df_dwf['Date'])
                # Convert intensity from mm/hr to mm per interval (assuming a_inst.data_interval is in minutes)
                df_dwf['RainfallDepth_mm'] = df_dwf['IntensityData'] * (a_inst.data_interval / 60)
                # Extract date (day) part for grouping
                df_dwf['Day'] = df_dwf['Date'].dt.date
                # Group by 'Day' and sum the 'RainfallDepth_mm'
                daily_rainfall = df_dwf.groupby('Day')['RainfallDepth_mm'].sum().reset_index()
                # Rename columns for clarity
                daily_rainfall.columns = ['Date', 'TotalRainfallDepth_mm']
        #         # Add instance name to distinguish between different instances
                daily_rainfall['Instance'] = a_inst.install_id  # Assuming each instance has a unique name
        #         # Append the daily rainfall data to the list
                all_daily_rainfall.append(daily_rainfall)
        # # Combine all daily rainfall data into a single dataframe
        combined_daily_rainfall = pd.concat(all_daily_rainfall)
        # # Group by date and sum the rainfall depths from all instances
        total_daily_rainfall = combined_daily_rainfall.groupby('Date')['TotalRainfallDepth_mm'].sum().reset_index()
        # # Filter out the days where the total rainfall depth exceeds the threshold
        # filtered_daily_rainfall = total_daily_rainfall[total_daily_rainfall['TotalRainfallDepth_mm'] <= dwf_threshold]

        dry_days = []

        for i in range(len(total_daily_rainfall)):
            if i < preceeding_dry_days:
                is_dry = False  # If there are not enough preceding days, mark as not dry
            else:
                # Check if the previous 'preceeding_dry_days' days are dry
                preceding_days = total_daily_rainfall.iloc[i - preceeding_dry_days:i]
                is_dry = all(preceding_days['TotalRainfallDepth_mm'] <= dwf_threshold) & (
                    total_daily_rainfall['TotalRainfallDepth_mm'].iloc[i] <= dwf_threshold)
            dry_days.append(is_dry)

        # Create a new dataframe with only the days that meet the criteria
        dry_days_df = total_daily_rainfall[dry_days]

        if self.current_inst.install_type == 'Flow Monitor':

            # flow_monitor_data = self.current_inst.data.copy()  # Make a copy of the data
            flow_monitor_data = self.df_filtered.copy()  # Make a copy of the data

            if self.chk_dwf_no_zeros.isChecked():
                flow_monitor_data = flow_monitor_data[flow_monitor_data['FlowData'] != 0]
            
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
            
            if self.chk_dwf_compare_full_period.isChecked():

                flow_monitor_data = self.current_inst.data.copy()

                if self.chk_dwf_no_zeros.isChecked():
                    flow_monitor_data = flow_monitor_data[flow_monitor_data['FlowData'] != 0]
                
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

                self.df_dwf_compare = pd.merge(flow_monitor_data, avg_dwf_per_time, on='TimeOfDay', how='right')

                self.df_dwf_compare['TimeOfDay'] = self.df_dwf_compare['Date'].dt.hour * 3600 + \
                    self.df_dwf_compare['Date'].dt.minute * 60 + self.df_dwf_compare['Date'].dt.second

                self.df_dwf_compare_average = self.df_dwf_compare.drop_duplicates(
                    subset=['TimeOfDay', 'AvgFlowData', 'AvgDepthData', 'AvgVelocityData'])
            
    def setup_axes(self):
        col_0_width = 30
        col_1_width = 140
        col_2_width = 5
        row_height = 30
        legend_total_width = 6 * (col_0_width + col_1_width + col_2_width)
        legend_total_height = (3 * row_height) + 10
        legend_fig_height = ((self.fig_width / legend_total_width) * legend_total_height)
        fdv_height = self.fig_height - legend_fig_height

        if self.current_inst.install_type == 'Flow Monitor':
            (self.plot_axis_legend, self.plot_axis_depth, self.plot_axis_flow, self.plot_axis_velocity) = self.plotCanvasReviewClassification.figure.subplots(
                nrows=4, sharex=False, gridspec_kw={'height_ratios': [legend_fig_height, fdv_height / 3, fdv_height / 3, fdv_height / 3]})

            self.plot_axis_flow.sharex(self.plot_axis_velocity)
            self.plot_axis_depth.sharex(self.plot_axis_flow)
        elif self.current_inst.install_type == 'Depth Monitor':
            (self.plot_axis_legend, self.plot_axis_depth) = self.plotCanvasReviewClassification.figure.subplots(
                nrows=2, sharex=False, gridspec_kw={'height_ratios': [legend_fig_height, fdv_height]})
        else:
            (self.plot_axis_legend, self.plot_axis_rg) = self.plotCanvasReviewClassification.figure.subplots(
                nrows=2, sharex=False, gridspec_kw={'height_ratios': [legend_fig_height, fdv_height]})

    def create_legend(self):
        dfLegend = get_classification_legend_dataframe()
        color_mapping = get_classification_color_mapping()

        col_0_width = 30
        col_1_width = 140
        col_2_width = 5
        row_height = 30
        my_fontsize = 10
        padding = 2

        legend_total_width = 6 * (col_0_width + col_1_width + col_2_width)
        legend_total_height = (3 * row_height) + 10

        for row in range(dfLegend.shape[0]):
            for col in range(0, dfLegend.shape[1], 3):
                code = dfLegend.iloc[row, col]
                description = dfLegend.iloc[row, col+1]
                if code and description:
                    my_y = legend_total_height - ((row + 1) * row_height)
                    x_offset = math.floor(col/3) * (col_0_width + col_1_width + col_2_width)
                    my_x = x_offset
                    text_color = '#ffffff' if color_mapping.get(code, '#ffffff') == '#000000' else '#000000'
                    rect = mpl_patches.Rectangle((my_x, my_y), col_0_width, row_height, edgecolor='black',
                                                facecolor=color_mapping.get(code, 'white'), linewidth=1)
                    self.plot_axis_legend.add_patch(rect)
                    self.plot_axis_legend.text(my_x + 15, my_y + 15, code, va='center', ha='center',
                                            fontsize=my_fontsize, fontweight='bold', color=text_color)
                    my_x = my_x + col_0_width
                    rect = mpl_patches.Rectangle((my_x, my_y), col_1_width, row_height, edgecolor='black', facecolor='none', linewidth=0)
                    self.plot_axis_legend.add_patch(rect)
                    self.plot_axis_legend.text(my_x + 15, my_y + 15, description, va='center', ha='left',
                                            fontsize=my_fontsize, fontweight='normal', color='black')
                    my_x = my_x + col_1_width
                    rect = mpl_patches.Rectangle((my_x, my_y), col_2_width, row_height, edgecolor='black', facecolor='none', linewidth=0)
                    self.plot_axis_legend.add_patch(rect)

        self.plot_axis_legend.set_xlim(-padding, legend_total_width + padding)
        self.plot_axis_legend.set_ylim(-padding, legend_total_height + padding)
        self.plot_axis_legend.xaxis.set_visible(False)
        self.plot_axis_legend.yaxis.set_visible(False)
        self.plot_axis_legend.set_frame_on(False)
        self.plot_axis_legend.set_autoscale_on(False)

    def plot_data(self):

        major_tick_format = DateFormatter("%a %d/%m/%Y")

        if self.current_inst.install_type == 'Flow Monitor':

            self.plot_axis_depth.plot(self.df_filtered['Date'], self.df_filtered['DepthData'], label='Depth', color='b')
            self.plot_axis_depth.yaxis.set_major_locator(MaxNLocator(integer=True))
            self.plot_axis_depth.xaxis.set_major_locator(MaxNLocator(integer=False))
            self.plot_axis_depth.xaxis.set_major_formatter(FuncFormatter(major_tick_format))
            self.plot_axis_depth.set_ylabel('Depth')

            self.plot_axis_flow.plot(self.df_filtered['Date'], self.df_filtered['FlowData'], label='Flow', color='g')
            self.plot_axis_flow.yaxis.set_major_locator(MaxNLocator(integer=True))
            self.plot_axis_flow.xaxis.set_major_locator(MaxNLocator(integer=False))
            self.plot_axis_flow.xaxis.set_major_formatter(FuncFormatter(major_tick_format))
            self.plot_axis_flow.set_ylabel('Flow')

            self.plot_axis_velocity.plot(self.df_filtered['Date'], self.df_filtered['VelocityData'], label='Velocity', color='r')
            self.plot_axis_velocity.yaxis.set_major_locator(MaxNLocator(8))
            self.plot_axis_velocity.xaxis.set_major_locator(MaxNLocator(integer=False))
            self.plot_axis_velocity.xaxis.set_major_formatter(FuncFormatter(major_tick_format))
            self.plot_axis_velocity.set_ylabel('Velocity')

            self.plot_axis_velocity.set_xlim(self.df_filtered['Date'].min().floor('D'), self.df_filtered['Date'].max().ceil('D'))
            self.plot_axis_velocity.xaxis.set_major_locator(HourLocator(byhour=0))
            self.plot_axis_velocity.xaxis.set_minor_locator(HourLocator(interval=6))
            self.plot_axis_velocity.xaxis.set_major_formatter(major_tick_format)
        
        elif self.current_inst.install_type == 'Depth Monitor':

            self.plot_axis_depth.plot(self.df_filtered['Date'], self.df_filtered['DepthData'], label='Depth', color='b')
            self.plot_axis_depth.set_xlim(self.df_filtered['Date'].min().floor('D'), self.df_filtered['Date'].max().ceil('D'))
            self.plot_axis_depth.xaxis.set_major_locator(HourLocator(byhour=0))
            self.plot_axis_depth.xaxis.set_minor_locator(HourLocator(interval=6))
            self.plot_axis_depth.xaxis.set_major_formatter(major_tick_format)
            self.plot_axis_depth.set_ylabel('Depth')

        else:

            self.plot_axis_rg.plot(self.df_filtered['Date'], self.df_filtered['IntensityData'], label='Intensity', color='b')
            self.plot_axis_rg.set_xlim(self.df_filtered['Date'].min().floor('D'), self.df_filtered['Date'].max().ceil('D'))
            self.plot_axis_rg.xaxis.set_major_locator(HourLocator(byhour=0))
            self.plot_axis_rg.xaxis.set_minor_locator(HourLocator(interval=6))
            self.plot_axis_rg.xaxis.set_major_formatter(major_tick_format)
            self.plot_axis_rg.set_ylabel('Rainfall Intensity')

    def add_classifications(self):
        color_mapping = get_classification_color_mapping()

        for index, row in self.df_class_combined_filtered.iterrows():
            start = pd.to_datetime(row['Date'], format='%d/%m/%Y')
            end = start + pd.Timedelta(days=1)
            color = color_mapping.get(row['Classification'], '#ffffff')

            if self.current_inst.install_type == 'Flow Monitor':
                self.plot_axis_depth.axvspan(start, end, facecolor=color, alpha=1)
                self.plot_axis_flow.axvspan(start, end, facecolor=color, alpha=1)
                self.plot_axis_velocity.axvspan(start, end, facecolor=color, alpha=1)
            elif self.current_inst.install_type == 'Depth Monitor':
                self.plot_axis_depth.axvspan(start, end, facecolor=color, alpha=1)
            else:
                self.plot_axis_rg.axvspan(start, end, facecolor=color, alpha=1)

    def add_statistics(self):

        a_props = dict(boxstyle='round', facecolor='teal', alpha=0.5)

        if self.current_inst.install_type in ['Flow Monitor', 'Depth Monitor']:

            # Calculate statistics for Depth
            max_depth = self.df_filtered['DepthData'].max() / 1000
            min_depth = self.df_filtered['DepthData'].min() / 1000
            mean_depth = self.df_filtered['DepthData'].mean() / 1000

            depth_textstr = f'Max Depth (m) = {max_depth:.3f}\nMin Depth (m) = {min_depth:.3f}\nMean Depth (m) = {mean_depth:.4f}'

            plot_depth_stats_box = self.plotCanvasReviewClassification.figure.text(
                0.05, 0.95, "", transform=self.plot_axis_depth.transAxes, fontsize=8, verticalalignment='top', bbox=a_props)

            plot_depth_stats_box.set_text(depth_textstr)

            self.plot_axis_depth.grid(True)

        if self.current_inst.install_type == 'Flow Monitor':

            # Calculate statistics for Flow
            max_flow = self.df_filtered['FlowData'].max() / 1000
            min_flow = self.df_filtered['FlowData'].min() / 1000
            mean_flow = self.df_filtered['FlowData'].mean() / 1000

            # Calculate statistics for Velocity
            max_velocity = self.df_filtered['VelocityData'].max()
            min_velocity = self.df_filtered['VelocityData'].min()
            mean_velocity = self.df_filtered['VelocityData'].mean()

            # Calculate volume of flow
            time_interval_seconds = 120
            total_volume = (self.df_filtered['FlowData'].sum() * time_interval_seconds) / 1000

            flow_textstr = f'Max Flow (m\u00B3/s) = {max_flow:.3f}\nMin Flow (m\u00B3/s) = {min_flow:.3f}\nMean Flow (m\u00B3/s) = {mean_flow:.4f}\nVolume (m\u00B3) = {total_volume:.1f}'
            velocity_textstr = f'Max Velocity (m/s) = {max_velocity:.2f}\nMin Velocity (m/s) = {min_velocity:.2f}\nMean Velocity (m/s) = {mean_velocity:.3f}'

            plot_flow_stats_box = self.plotCanvasReviewClassification.figure.text(
                0.05, 0.95, "", transform=self.plot_axis_flow.transAxes, fontsize=8, verticalalignment='top', bbox=a_props)
            plot_velocity_stats_box = self.plotCanvasReviewClassification.figure.text(
                0.05, 0.95, "", transform=self.plot_axis_velocity.transAxes, fontsize=8, verticalalignment='top', bbox=a_props)

            plot_flow_stats_box.set_text(flow_textstr)
            plot_velocity_stats_box.set_text(velocity_textstr)

            self.plot_axis_flow.grid(True)
            self.plot_axis_velocity.grid(True)

        if self.current_inst.install_type == 'Rain Gauge':

            # Calculate statistics for Rain
            max_intensity = self.df_filtered['IntensityData'].max()
            total_depth = (self.df_filtered['IntensityData'] * (self.current_inst.data_interval/60)).sum()
            duration_hrs = (self.df_filtered['Date'].max() - self.df_filtered['Date'].min()).total_seconds() / 3600
            return_period = round(10/(1.25*duration_hrs*(((0.0394*total_depth)+0.1)**-3.55)), 2)

            rainfall_textstr = 'Max intensity(mm/hr) = ' + str(round(max_intensity, 1))+'\nDepth(mm) = ' + str(round(total_depth, 1)) + '\nReturn Period(yr) = ' + str(round(return_period, 1))

            plot_rg_stats_box = self.plotCanvasReviewClassification.figure.text(
                0.05, 0.95, "", transform=self.plot_axis_rg.transAxes, fontsize=8, verticalalignment='top', bbox=a_props)

            plot_rg_stats_box.set_text(rainfall_textstr)
            
            self.plot_axis_rg.grid(True)

    def finalize_plot(self):
        self.plotCanvasReviewClassification.figure.autofmt_xdate()
        self.plotCanvasReviewClassification.figure.subplots_adjust(left=0.09, right=0.98, bottom=0.17, top=0.94)
        currentPlotTitle = f'Site: {self.current_inst.install_site_id}, Monitor: {self.current_inst.install_monitor_asset_id}, Client Ref: {self.current_inst.client_ref}'
        self.plotCanvasReviewClassification.figure.suptitle(currentPlotTitle, fontsize=12)

    def enable_update_button(self):
        """Enable the update button."""
        self.btnUpdate.setEnabled(True)

    def onAccept(self):
        self.update_interim_review()
        self.accept()
