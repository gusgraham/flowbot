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
from ui_elements.ui_flowbot_dialog_fsm_review_raingauge_base import Ui_Dialog

class flowbot_dialog_fsm_review_raingauge(QtWidgets.QDialog, Ui_Dialog):
    # def __init__(self, a_installs: List[fsmInstall], sites: Dict[str, fsmSite], start_date: datetime, end_date: datetime, parent=None):
    def __init__(self, interim_id: int, a_project: fsmProject, parent=None):
        """Constructor."""
        super(flowbot_dialog_fsm_review_raingauge, self).__init__(parent)
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
            if a_inst.install_type == 'Rain Gauge':
                a_int_rg = self.a_project.get_interim_review(interim_id=interim_id, install_id=a_inst.install_id)
                if not a_int_rg:
                    a_int_rg = fsmInterimReview()
                    a_int_rg.interim_review_id = self.a_project.get_next_interim_review_id()
                    a_int_rg.interim_id = interim_id
                    a_int_rg.install_id = a_inst.install_id
                    self.a_project.add_interim_review(a_int_rg)
                # self.interim_reviews.append(a_int_rg)
                if a_int_rg.dr_data_covered:
                    self.interim_reviews.append(a_int_rg)
                else:
                    a_int_rg.rg_complete = True
                    a_int_rg.rg_comment = 'No data in interim period'                

        self.df_filtered: pd.DataFrame

        self.current_interim_review_index = 0

        if len(self.interim_reviews) > 0:
            self.current_interim_review: fsmInterimReview = self.interim_reviews[self.current_interim_review_index]
            self.current_inst = self.a_project.dict_fsm_installs[self.current_interim_review.install_id]
        else:
            self.current_interim_review: fsmInterimReview = None
            self.current_inst: fsmInstall = None

        self.plot_axis_rg: Optional[axes.Axes] = None
        self.plot_axis_depth: Optional[axes.Axes] = None
        self.plot_axis_flow: Optional[axes.Axes] = None
        self.plot_axis_velocity: Optional[axes.Axes] = None

        self.fig_width = 14.1
        self.fig_height = 10

        # self.current_plot_type = 'FM'

        self.plotCanvasReviewRG.figure.set_dpi(100)
        self.plotCanvasReviewRG.figure.set_figwidth(self.fig_width)
        self.plotCanvasReviewRG.figure.set_figheight(self.fig_height)

        self.btnPrevious.clicked.connect(self.on_previous_clicked)
        self.btnNext.clicked.connect(self.on_next_clicked)
        self.tabWidget.currentChanged.connect(self.onTabChanged)
        
        self.chk_dep_full_period.clicked.connect(self.update_plot)
        self.chk_dep_compare_full_period.clicked.connect(self.update_plot) 
        self.chk_show_cumulative.clicked.connect(self.update_plot)
        self.chk_dep_compare_all_rgs.clicked.connect(self.update_plot)
        self.rbnAverage.clicked.connect(self.update_plot)
        self.rbnIndividual.clicked.connect(self.update_plot)

        self.update_plot()

        self.plotCanvasReviewRG.scrollZoomCompleted.connect(self.update_rg_statistics)

    # def enable_dep_update_button(self):
    #     """Enable the update button."""
    #     self.btn_dep_update.setEnabled(True)

    # def enable_cum_update_button(self):
    #     """Enable the update button."""
    #     self.btn_cum_update.setEnabled(True)

    def onTabChanged(self, index):
        self.update_plot()

    def update_widgets(self):

        if self.current_interim_review is not None:
            self.chk_rg_review_complete.setChecked(self.current_interim_review.rg_complete)
            self.txt_review_comments.setText(self.current_interim_review.rg_comment)
        else:
            self.chk_rg_review_complete.setChecked(True)
            self.txt_review_comments.setText('No data in the interim')


    def update_button_states(self):
        if self.current_interim_review is not None:        
            self.btnPrevious.setEnabled(self.current_interim_review_index > 0)
            self.btnNext.setEnabled(self.current_interim_review_index < len(self.interim_reviews) - 1)
            self.rbnAverage.setEnabled(self.chk_dep_compare_all_rgs.isChecked())
            self.rbnIndividual.setEnabled(self.chk_dep_compare_all_rgs.isChecked())
        else:
            self.btnPrevious.setEnabled(False)
            self.btnNext.setEnabled(False)
            self.rbnAverage.setEnabled(False)
            self.rbnIndividual.setEnabled(False)

    def dodgyForceUpdate(self):
            oldSize = self.size()
            self.resize(oldSize.width() - 1, oldSize.height() - 1)
            self.resize(oldSize)

    def update_plot(self):

        self.plotCanvasReviewRG.figure.clear()
        currentTabName = self.tabWidget.currentWidget().objectName()
        if currentTabName == 'tabDepth':
            self.plotCanvasReviewRG.scroll_zoom_enabled = True
            self.plotCanvasReviewRG.x_pan_enabled = True
            self.create_dep_plot()

        self.update_button_states()
        self.update_widgets()            
        self.dodgyForceUpdate()

    def create_dep_plot(self):

        if self.current_inst is not None:
            filename = self.current_inst.client_ref
            # i_soffit_mm = self.current_inst.fm_pipe_height_mm

            self.filter_dep_data()

            if self.chk_show_cumulative.isChecked():
                self.plot_axis_cum, self.plot_axis_rg = self.plotCanvasReviewRG.figure.subplots(
                    nrows=2, sharex=True,  gridspec_kw={'height_ratios': [1, 1]})
            else:
                self.plot_axis_rg = self.plotCanvasReviewRG.figure.subplots(nrows=1,  gridspec_kw={'height_ratios': [1]})

            if self.chk_dep_compare_full_period.isChecked():

                self.plot_axis_rg.plot(self.df_compare['Date'], self.df_compare['IntensityData'], color='grey')
                if self.chk_show_cumulative.isChecked():
                    self.plot_axis_cum.plot(self.df_compare['Date'], self.df_compare['CumulativeRainfallDepth_mm'], color='grey')


            if self.chk_dep_compare_all_rgs.isChecked():
                if self.rbnAverage.isChecked():
                    self.plot_axis_rg.plot(self.df_compare_all_rgs['Date'], self.df_compare_all_rgs['IntensityData'], color='grey')
                else:
                    grouped = self.df_compare_all_rgs.groupby(self.df_compare_all_rgs['InstallID'])

                    for id, group in grouped:
                        self.plot_axis_rg.plot(group['Date'], group['IntensityData'], color='grey')

            self.plot_axis_rg.plot(self.df_filtered['Date'], self.df_filtered['IntensityData'], color='darkblue')
            self.plot_axis_rg.set_ylabel('Intensity (mm/hr)')

            if self.chk_show_cumulative.isChecked():
                if self.chk_dep_compare_all_rgs.isChecked():
                    if self.rbnAverage.isChecked():
                        self.plot_axis_cum.plot(self.df_compare_all_rgs['Date'],
                                                self.df_compare_all_rgs['CumulativeRainfallDepth_mm'], color='grey')
                    else:
                        grouped = self.df_compare_all_rgs.groupby(self.df_compare_all_rgs['InstallID'])

                        for id, group in grouped:
                            self.plot_axis_cum.plot(group['Date'],
                                                    group['CumulativeRainfallDepth_mm'], color='grey')

                if self.chk_dep_compare_full_period.isChecked():
                    self.plot_axis_cum.plot(self.df_filtered['Date'], self.df_filtered['FP_CumulativeRainfallDepth_mm'], color='darkblue')
                else:
                    self.plot_axis_cum.plot(self.df_filtered['Date'], self.df_filtered['CumulativeRainfallDepth_mm'], color='darkblue')
                self.plot_axis_cum.set_ylabel('Cumulative Depth (mm)')
                self.plot_axis_cum.set_title(f'Rainfall: {filename}', loc='left', fontsize=16)  # Adding filename to title
            else:
                self.plot_axis_rg.set_title(f'Rainfall: {filename}', loc='left', fontsize=16)  # Adding filename to title

            self.plot_axis_rg.set_xlabel('Date')
            
            # Set major and minor locators
            self.plot_axis_rg.xaxis.set_major_locator(mpl_dates.DayLocator())
            self.plot_axis_rg.xaxis.set_major_formatter(mpl_dates.DateFormatter("%a %d/%m/%Y"))
            self.plot_axis_rg.xaxis.set_minor_locator(mpl_dates.HourLocator(byhour=[0, 6, 12, 18]))

            self.plot_axis_rg.xaxis.set_major_formatter(mpl_dates.ConciseDateFormatter(mpl_dates.AutoDateLocator()))
            
            self.update_rg_statistics()

            # Adjust layout
            self.plotCanvasReviewRG.figure.subplots_adjust(left=0.15, right=0.85, bottom=0.15, top=0.85)
            self.plotCanvasReviewRG.figure.tight_layout()

            # Show plot
            self.plotCanvasReviewRG.canvas.show()

    def update_rg_statistics(self):

        self.update_rg_y_axes()

        for text in self.plot_axis_rg.texts:
            if text.get_text().startswith('Min:'):  # Check if text starts with 'Min:' (or another unique identifier)
                text.remove()

        x_min, x_max = mpl_dates.num2date(self.plot_axis_rg.get_xlim())
        x_min = np.datetime64(x_min)
        x_max = np.datetime64(x_max)
        df_filtered = self.df_filtered[(self.df_filtered['Date'] >= x_min) & (self.df_filtered['Date'] <= x_max)].copy()

        rain_min = df_filtered['IntensityData'].min()
        rain_max = df_filtered['IntensityData'].max()
        rain_range = rain_max - rain_min
        rain_avg = df_filtered['IntensityData'].mean()
        # rain_depth = self.df_rgs_filtered['IntensityData'].mean()

        total_rain_depth_mm = df_filtered['RainfallDepth_mm'].sum()

        # Add statistics to the right of the plot
        rain_stats_text = f"Min: {rain_min:.2f}\nMax: {rain_max:.2f}\nRange: {rain_range:.2f}\nAverage: {rain_avg:.2f}\nDepth (mm): {total_rain_depth_mm:.1f} mm"
        self.plot_axis_rg.text(1.02, 0.5, rain_stats_text, transform=self.plot_axis_rg.transAxes, verticalalignment='center')

    def update_rg_y_axes(self):

        # Get the new x-axis limits from one of the axes
        new_xmin, new_xmax = mpl_dates.num2date(self.plot_axis_rg.get_xlim())
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
        if self.chk_show_cumulative.isChecked():
            update_y_limits(self.plot_axis_cum)
        update_y_limits(self.plot_axis_rg)

        self.plotCanvasReviewRG.canvas.draw_idle()

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

        if self.current_interim_review is not None:
            self.current_interim_review.rg_complete = self.chk_rg_review_complete.isChecked()
            self.current_interim_review.rg_comment = self.txt_review_comments.text()

    def filter_dep_data(self):

        self.df_filtered = self.current_inst.data.copy()
        # Ensure data is sorted by Date
        self.df_filtered = self.df_filtered.sort_values(by='Date')
        self.df_filtered['RainfallDepth_mm'] = self.df_filtered['IntensityData'] * (self.current_inst.data_interval / 60)
        # Calculate cumulative rainfall depth
        self.df_filtered['FP_CumulativeRainfallDepth_mm'] = self.df_filtered['RainfallDepth_mm'].cumsum()

        if not self.chk_dep_full_period.isChecked():
            self.df_filtered = self.df_filtered[(self.df_filtered['Date'] >= self.start_date)
                                                & (self.df_filtered['Date'] <= self.end_date)]
            
        self.df_filtered = self.df_filtered.sort_values(by='Date')
        self.df_filtered['CumulativeRainfallDepth_mm'] = self.df_filtered['RainfallDepth_mm'].cumsum()
            
        if self.chk_dep_compare_full_period.isChecked():
            self.df_compare = self.current_inst.data.copy()
            
            # Ensure data is sorted by Date
            self.df_compare = self.df_compare.sort_values(by='Date')
            self.df_compare['RainfallDepth_mm'] = self.df_compare['IntensityData'] * (self.current_inst.data_interval / 60)
            # Calculate cumulative rainfall depth for the comparison dataframe
            self.df_compare['CumulativeRainfallDepth_mm'] = self.df_compare['RainfallDepth_mm'].cumsum()

        if self.chk_dep_compare_all_rgs.isChecked():
            all_rainfall_data = []

            for a_inst in self.a_project.dict_fsm_installs.values():
                if a_inst.install_type == 'Rain Gauge':
                    if self.chk_dep_full_period.isChecked():
                        a_instance_rainfall_data = a_inst.data[['Date', 'IntensityData']].copy()
                    else:
                        a_instance_rainfall_data = a_inst.data[(a_inst.data['Date'] >= self.start_date)
                                                               & (a_inst.data['Date'] <= self.end_date)].copy()
                    a_instance_rainfall_data = a_instance_rainfall_data.sort_values(by='Date')
                    a_instance_rainfall_data['RainfallDepth_mm'] = a_instance_rainfall_data['IntensityData'] * (a_inst.data_interval / 60)
                    a_instance_rainfall_data['CumulativeRainfallDepth_mm'] = a_instance_rainfall_data['RainfallDepth_mm'].cumsum()
                    a_instance_rainfall_data['InstallID'] = a_inst.install_id
                    all_rainfall_data.append(a_instance_rainfall_data)

            if all_rainfall_data:
                combined_rainfall_data = pd.concat(all_rainfall_data)
                # average_rainfall_data = combined_rainfall_data.groupby('Date', as_index=False)['IntensityData'].mean()
            else:
                combined_rainfall_data = pd.DataFrame(columns=['Date', 'IntensityData', 'RainfallDepth_mm', 'InstallID'])

            if self.rbnAverage.isChecked():
                combined_rainfall_data = combined_rainfall_data.groupby('Date', as_index=False).agg({
                    'IntensityData': 'mean',
                    'RainfallDepth_mm': 'mean'
                    })
                combined_rainfall_data = combined_rainfall_data.sort_values(by='Date')
                combined_rainfall_data['CumulativeRainfallDepth_mm'] = combined_rainfall_data['RainfallDepth_mm'].cumsum()

            self.df_compare_all_rgs = combined_rainfall_data.copy()
            
    def enable_update_button(self):
        """Enable the update button."""
        self.btnUpdate.setEnabled(True)

    def onAccept(self):
        self.update_interim_review()
        self.accept()
