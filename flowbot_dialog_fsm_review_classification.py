# from ast import List
# import site
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
from matplotlib.ticker import MaxNLocator, FuncFormatter
from flowbot_helper import get_classification_legend_dataframe, get_classification_color_mapping
import math
import pandas as pd
from bisect import bisect_left
import numpy as np

from PyQt5 import QtWidgets, QtCore

# from flowbot_monitors import plottedFlowMonitors
from flowbot_management import fsmInterim, fsmInterimReview, fsmMonitor, fsmProject, fsmSite, fsmInstall
from ui_elements.ui_flowbot_dialog_fsm_review_classification_base import Ui_Dialog


class flowbot_dialog_fsm_review_classification(QtWidgets.QDialog, Ui_Dialog):
    # def __init__(self, a_installs: List[fsmInstall], sites: Dict[str, fsmSite], start_date: datetime, end_date: datetime, parent=None):
    def __init__(self, interim_id: int, a_project: fsmProject, parent=None):
        """Constructor."""
        super(flowbot_dialog_fsm_review_classification, self).__init__(parent)
        self.setupUi(self)

        self.btnDone.clicked.connect(self.onAccept)

        self.a_project: fsmProject = a_project

        self.interim_id = interim_id
        self.interim = self.a_project.dict_fsm_interims[self.interim_id]
        self.start_date: datetime = self.interim.interim_start_date
        self.end_date: datetime = self.interim.interim_end_date
        self.interim_reviews: list[fsmInterimReview] = []

        for a_inst in self.a_project.dict_fsm_installs.values():
            a_int_cr = self.a_project.get_interim_review(
                interim_id=interim_id, install_id=a_inst.install_id)
            if not a_int_cr:
                a_int_cr = fsmInterimReview()
                a_int_cr.interim_review_id = self.a_project.get_next_interim_review_id()
                a_int_cr.interim_id = interim_id
                a_int_cr.install_id = a_inst.install_id
                self.a_project.add_interim_review(a_int_cr)
            self.interim_reviews.append(a_int_cr)

        self.current_interim_review_index = 0
        self.current_interim_review: fsmInterimReview = self.interim_reviews[
            self.current_interim_review_index]
        self.current_inst = self.a_project.dict_fsm_installs[self.current_interim_review.install_id]
        self.selected_days = set()
        self.last_selected_day = None
        self.dict_class_codes = {'Not Working': 'X', 'Dry Pipe': 'G', 'Low Flow <10l/s': 'L', 'Pluming': 'P', 'Dislodged Sensor': 'U',
                                 'Taken Out': 'O', 'Velocity Problem': 'V', 'Blocked Filter RG': 'B', 'Sediment': 'T', 'Monitor Submerged': 'K',
                                 'Standing Water': 'H', 'Monitor Changed': 'M', 'Depth Problem': 'D', 'Ragging': 'R', 'Surcharged': 'S',
                                 'Working': 'W', 'Installed': 'I'}
        self.df_class_combined_filtered: Optional[pd.DataFrame] = None

        self.plot_axis_rg: Optional[axes.Axes] = None
        self.plot_axis_legend: Optional[axes.Axes] = None
        self.plot_axis_depth: Optional[axes.Axes] = None
        self.plot_axis_flow: Optional[axes.Axes] = None
        self.plot_axis_velocity: Optional[axes.Axes] = None

        self.fig_width = 14.1
        self.fig_height = 10

        self.current_plot_type = 'FM'

        self.plotCanvasReviewClassification.figure.set_dpi(100)
        self.plotCanvasReviewClassification.figure.set_figwidth(self.fig_width)
        self.plotCanvasReviewClassification.figure.set_figheight(
            self.fig_height)

        self.plotCanvasReviewClassification.mouseClicked.connect(
            self.handle_mouse_click)

        self.btnPrevious.clicked.connect(self.on_previous_clicked)
        self.btnNext.clicked.connect(self.on_next_clicked)

        self.update_button_states()
        self.update_plot()
        self.update_widgets()

    def handle_mouse_click(self, event):

        if event.button == 1:
            modifiers = QtWidgets.QApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.ShiftModifier:
                self.handle_shift_click(event)
            elif modifiers == QtCore.Qt.ControlModifier:
                self.handle_control_click(event)
            else:
                self.handle_single_click(event)

            self.highlight_selected_days()

        elif event.button == 3:
            self.handle_right_click(event)

    def handle_right_click(self, event):
        context_menu = QtWidgets.QMenu(self)

        menu_items = [
            'Working', 'Not Working', 'Surcharged', 'Depth Problem', 'Velocity Problem', 'Dry Pipe', 'Standing Water',
            'Installed', 'Taken Out', 'Monitor Changed', 'Sediment', 'Ragging', 'Low Flow <10l/s', 'Pluming', 'Monitor Submerged',
            'Dislodged Sensor', 'Blocked Filter RG']

        for item in menu_items:
            action = QtWidgets.QAction(item, self)
            action.triggered.connect(
                lambda checked, item=item: self.handle_context_menu_action(item))
            context_menu.addAction(action)

        # Get the screen position of the click
        # screen_pos = self.plotCanvasReviewClassification.canvas.mapToGlobal(QtCore.QPoint(event.x, event.y))
        screen_pos = self.plotCanvasReviewClassification.canvas.mapToGlobal(
            QtCore.QPoint(event.x, self.plotCanvasReviewClassification.canvas.height() - event.y))

        context_menu.exec_(screen_pos)

    def handle_context_menu_action(self, item):

        if self.current_inst.class_data_user is None:
            self.current_inst.class_data_user = pd.DataFrame(
                columns=['Date', 'Classification', 'Confidence'])

        class_code = self.dict_class_codes[item]
        for selected_day in self.selected_days:
            # Find the equivalent day in the dataframe self.current_inst.class_data_ml['Date']
            matching_dates = self.current_inst.class_data_ml[self.current_inst.class_data_ml['Date'] == np.datetime64(
                selected_day, 'D')]

            for date in matching_dates['Date']:
                # if date not in self.current_inst.class_data_user['Date'].values:
                new_entry = pd.DataFrame({
                    'Date': [date],
                    'Classification': [class_code],
                    # or any default confidence value you wish to use
                    'Confidence': [1.0]
                })

                # Find the index of the date in the existing dataframe
                idx = self.current_inst.class_data_user.index[self.current_inst.class_data_user['Date'] == date].tolist(
                )

                if idx:  # if the date exists, update the existing entry
                    self.current_inst.class_data_user.loc[idx[0],
                                                          'Classification'] = class_code
                    self.current_inst.class_data_user.loc[idx[0],
                                                          'Confidence'] = 1.0
                else:  # if the date does not exist, append the new entry
                    self.current_inst.class_data_user = pd.concat(
                        [self.current_inst.class_data_user, new_entry], ignore_index=True)

        self.update_plot()

    def handle_single_click(self, event):
        clicked_day = np.datetime64(num2date(event.xdata), 'D')
        self.selected_days = {clicked_day}
        self.last_selected_day = clicked_day

    def handle_shift_click(self, event):
        clicked_day = np.datetime64(num2date(event.xdata), 'D')
        if self.last_selected_day:
            start_day = min(self.last_selected_day, clicked_day)
            end_day = max(self.last_selected_day, clicked_day)
            new_selection = {np.datetime64(day, 'D') for day in np.arange(
                start_day, end_day + np.timedelta64(1, 'D'))}
            self.selected_days.update(new_selection)
        else:
            self.selected_days = {clicked_day}
        self.last_selected_day = clicked_day

    def handle_control_click(self, event):
        clicked_day = np.datetime64(num2date(event.xdata), 'D')
        if clicked_day in self.selected_days:
            self.selected_days.remove(clicked_day)
        else:
            self.selected_days.add(clicked_day)
        self.last_selected_day = clicked_day

    def highlight_selected_days(self):

        if self.current_inst.install_type == 'Flow Monitor':
            current_axes = [self.plot_axis_flow,
                            self.plot_axis_depth, self.plot_axis_velocity]
        elif self.current_inst.install_type == 'Depth Monitor':
            current_axes = [self.plot_axis_depth]
        else:
            current_axes = [self.plot_axis_rg]

        for ax in current_axes:
            # Remove existing highlight patches
            for patch in ax.patches:
                if hasattr(patch, 'is_highlight'):
                    patch.remove()

            for selected_day in self.selected_days:
                start_index = bisect_left(
                    ax.lines[0].get_xdata(), selected_day)
                # Find the next day after the selected day
                end_index = next((i for i, date in enumerate(ax.lines[0].get_xdata()[
                                 start_index:], start=start_index) if np.datetime64(date, 'D') > selected_day), None)
                if end_index is None:
                    end_index = len(ax.lines[0].get_xdata())

                x_start = ax.lines[0].get_xdata()[start_index]
                # Set the width of the patch to be the duration between start and end x values
                if end_index < len(ax.lines[0].get_xdata()):
                    x_end = ax.lines[0].get_xdata()[end_index]
                else:
                    # Assume a single day width if at the end of the data
                    x_end = x_start + np.timedelta64(1, 'D')

                width = x_end - x_start
                highlight_patch = mpl_patches.Rectangle((x_start, ax.get_ylim()[0]), width, ax.get_ylim()[
                                                        1] - ax.get_ylim()[0], color='red', alpha=0.3, zorder=1)
                setattr(highlight_patch, 'is_highlight',
                        True)  # Set custom property
                ax.add_patch(highlight_patch)

        self.plotCanvasReviewClassification.canvas.draw_idle()

    def on_previous_clicked(self):

        if self.current_interim_review_index > 0:
            self.current_interim_review_index -= 1
            self.update_interim_review()
            self.current_interim_review = self.interim_reviews[self.current_interim_review_index]
            self.current_inst = self.a_project.dict_fsm_installs[
                self.current_interim_review.install_id]
            self.update_plot()
            self.update_widgets()
            self.update_button_states()

    def on_next_clicked(self):
        if self.current_interim_review_index < len(self.interim_reviews) - 1:
            self.current_interim_review_index += 1
            self.update_interim_review()
            self.current_interim_review = self.interim_reviews[self.current_interim_review_index]
            self.current_inst = self.a_project.dict_fsm_installs[
                self.current_interim_review.install_id]
            self.update_plot()
            self.update_widgets()
            self.update_button_states()

    def update_interim_review(self):

        self.current_interim_review.cr_complete = self.chk_classification_acceptable.isChecked()
        self.current_interim_review.cr_comment = self.txt_review_comments.text()

    def update_widgets(self):

        self.chk_classification_acceptable.setChecked(
            self.current_interim_review.cr_complete)
        self.txt_review_comments.setText(
            self.current_interim_review.cr_comment)

    def update_button_states(self):
        self.btnPrevious.setEnabled(self.current_interim_review_index > 0)
        self.btnNext.setEnabled(
            self.current_interim_review_index < len(self.interim_reviews) - 1)

    def dodgyForceUpdate(self):
        oldSize = self.size()
        self.resize(oldSize.width() - 1, oldSize.height() - 1)
        self.resize(oldSize)

    def update_plot(self):

        self.plotCanvasReviewClassification.figure.clear()
        self.createPlot()
        self.dodgyForceUpdate()

    def createPlot(self):
        self.filter_data()
        self.setup_axes()
        self.create_legend()
        self.plot_data()
        self.add_classifications()
        self.add_statistics()
        self.finalize_plot()

    def filter_data(self):

        self.df_filtered = self.current_inst.data[(self.current_inst.data['Date'] >= self.start_date)
                                                  & (self.current_inst.data['Date'] <= self.end_date)]

        if self.current_inst.class_data_ml is not None:
            df_class_ml_filtered = self.current_inst.class_data_ml[(self.current_inst.class_data_ml['Date'] >= self.start_date)
                                                                   & (self.current_inst.class_data_ml['Date'] <= self.end_date)]
        else:
            df_class_ml_filtered = pd.DataFrame(
                columns=['Date', 'Classification', 'Confidence'])

        if self.current_inst.class_data_user is not None:
            df_class_user_filtered = self.current_inst.class_data_user[(self.current_inst.class_data_user['Date'] >= self.start_date)
                                                                       & (self.current_inst.class_data_user['Date'] <= self.end_date)]
        else:
            df_class_user_filtered = pd.DataFrame(
                columns=['Date', 'Classification', 'Confidence'])

        if not df_class_ml_filtered.empty or not df_class_user_filtered.empty:
            combined = pd.concat(
                [df_class_user_filtered, df_class_ml_filtered])
            self.df_class_combined_filtered = combined.drop_duplicates(
                subset='Date', keep='first')
        else:
            self.df_class_combined_filtered = pd.DataFrame(
                columns=['Date', 'Classification', 'Confidence'])

    def setup_axes(self):
        col_0_width = 30
        col_1_width = 140
        col_2_width = 5
        row_height = 30
        legend_total_width = 6 * (col_0_width + col_1_width + col_2_width)
        legend_total_height = (3 * row_height) + 10
        legend_fig_height = (
            (self.fig_width / legend_total_width) * legend_total_height)
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
                    x_offset = math.floor(
                        col/3) * (col_0_width + col_1_width + col_2_width)
                    my_x = x_offset
                    text_color = '#ffffff' if color_mapping.get(
                        code, '#ffffff') == '#000000' else '#000000'
                    rect = mpl_patches.Rectangle((my_x, my_y), col_0_width, row_height, edgecolor='black',
                                                 facecolor=color_mapping.get(code, 'white'), linewidth=1)
                    self.plot_axis_legend.add_patch(rect)
                    self.plot_axis_legend.text(my_x + 15, my_y + 15, code, va='center', ha='center',
                                               fontsize=my_fontsize, fontweight='bold', color=text_color)
                    my_x = my_x + col_0_width
                    rect = mpl_patches.Rectangle(
                        (my_x, my_y), col_1_width, row_height, edgecolor='black', facecolor='none', linewidth=0)
                    self.plot_axis_legend.add_patch(rect)
                    self.plot_axis_legend.text(my_x + 15, my_y + 15, description, va='center', ha='left',
                                               fontsize=my_fontsize, fontweight='normal', color='black')
                    my_x = my_x + col_1_width
                    rect = mpl_patches.Rectangle(
                        (my_x, my_y), col_2_width, row_height, edgecolor='black', facecolor='none', linewidth=0)
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

            if len(self.df_filtered["Date"]) > 0:
                self.plot_axis_depth.plot(
                    self.df_filtered['Date'], self.df_filtered['DepthData'], label='Depth', color='b')
                self.plot_axis_depth.yaxis.set_major_locator(
                    MaxNLocator(integer=True))
                self.plot_axis_depth.xaxis.set_major_locator(
                    MaxNLocator(integer=False))
                self.plot_axis_depth.xaxis.set_major_formatter(
                    FuncFormatter(major_tick_format))
                self.plot_axis_depth.set_ylabel('Depth')

                self.plot_axis_flow.plot(
                    self.df_filtered['Date'], self.df_filtered['FlowData'], label='Flow', color='g')
                self.plot_axis_flow.yaxis.set_major_locator(
                    MaxNLocator(integer=True))
                self.plot_axis_flow.xaxis.set_major_locator(
                    MaxNLocator(integer=False))
                self.plot_axis_flow.xaxis.set_major_formatter(
                    FuncFormatter(major_tick_format))
                self.plot_axis_flow.set_ylabel('Flow')

                self.plot_axis_velocity.plot(
                    self.df_filtered['Date'], self.df_filtered['VelocityData'], label='Velocity', color='r')
                self.plot_axis_velocity.yaxis.set_major_locator(MaxNLocator(8))
                self.plot_axis_velocity.xaxis.set_major_locator(
                    MaxNLocator(integer=False))
                self.plot_axis_velocity.xaxis.set_major_formatter(
                    FuncFormatter(major_tick_format))
                self.plot_axis_velocity.set_ylabel('Velocity')

                self.plot_axis_velocity.set_xlim(self.df_filtered['Date'].min().floor(
                    'D'), self.df_filtered['Date'].max().ceil('D'))
                self.plot_axis_velocity.xaxis.set_major_locator(
                    HourLocator(byhour=0))
                self.plot_axis_velocity.xaxis.set_minor_locator(
                    HourLocator(interval=6))
                self.plot_axis_velocity.xaxis.set_major_formatter(
                    major_tick_format)
            else:
                # ax = self.main_window_plot_widget.figure.subplots()
                self.plot_axis_depth.text(
                    0.5,
                    0.5,
                    "No data found",
                    horizontalalignment="center",
                    verticalalignment="center",
                    fontsize=16,
                )
                self.plot_axis_depth.set_axis_off()  # Hide the axes
                self.plot_axis_flow.text(
                    0.5,
                    0.5,
                    "No data found",
                    horizontalalignment="center",
                    verticalalignment="center",
                    fontsize=16,
                )
                self.plot_axis_flow.set_axis_off()  # Hide the axes
                self.plot_axis_velocity.text(
                    0.5,
                    0.5,
                    "No data found",
                    horizontalalignment="center",
                    verticalalignment="center",
                    fontsize=16,
                )
                self.plot_axis_velocity.set_axis_off()  # Hide the axes

        elif self.current_inst.install_type == 'Depth Monitor':

            if len(self.df_filtered["Date"]) > 0:
                self.plot_axis_depth.plot(
                    self.df_filtered['Date'], self.df_filtered['DepthData'], label='Depth', color='b')
                self.plot_axis_depth.set_xlim(self.df_filtered['Date'].min().floor(
                    'D'), self.df_filtered['Date'].max().ceil('D'))
                self.plot_axis_depth.xaxis.set_major_locator(HourLocator(byhour=0))
                self.plot_axis_depth.xaxis.set_minor_locator(
                    HourLocator(interval=6))
                self.plot_axis_depth.xaxis.set_major_formatter(major_tick_format)
                self.plot_axis_depth.set_ylabel('Depth')
            else:
                # ax = self.main_window_plot_widget.figure.subplots()
                self.plot_axis_depth.text(
                    0.5,
                    0.5,
                    "No data found",
                    horizontalalignment="center",
                    verticalalignment="center",
                    fontsize=16,
                )
                self.plot_axis_depth.set_axis_off()  # Hide the axes

        else:

            if len(self.df_filtered["Date"]) > 0:
                self.plot_axis_rg.plot(
                    self.df_filtered['Date'], self.df_filtered['IntensityData'], label='Intensity', color='b')
                self.plot_axis_rg.set_xlim(self.df_filtered['Date'].min().floor(
                    'D'), self.df_filtered['Date'].max().ceil('D'))
                self.plot_axis_rg.xaxis.set_major_locator(HourLocator(byhour=0))
                self.plot_axis_rg.xaxis.set_minor_locator(HourLocator(interval=6))
                self.plot_axis_rg.xaxis.set_major_formatter(major_tick_format)
                self.plot_axis_rg.set_ylabel('Rainfall Intensity')
            else:
                # ax = self.main_window_plot_widget.figure.subplots()
                self.plot_axis_rg.text(
                    0.5,
                    0.5,
                    "No data found",
                    horizontalalignment="center",
                    verticalalignment="center",
                    fontsize=16,
                )
                self.plot_axis_rg.set_axis_off()  # Hide the axes

    def add_classifications(self):
        color_mapping = get_classification_color_mapping()

        for index, row in self.df_class_combined_filtered.iterrows():
            start = pd.to_datetime(row['Date'], format='%d/%m/%Y')
            end = start + pd.Timedelta(days=1)
            color = color_mapping.get(row['Classification'], '#ffffff')

            if self.current_inst.install_type == 'Flow Monitor':
                self.plot_axis_depth.axvspan(
                    start, end, facecolor=color, alpha=1)
                self.plot_axis_flow.axvspan(
                    start, end, facecolor=color, alpha=1)
                self.plot_axis_velocity.axvspan(
                    start, end, facecolor=color, alpha=1)
            elif self.current_inst.install_type == 'Depth Monitor':
                self.plot_axis_depth.axvspan(
                    start, end, facecolor=color, alpha=1)
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
            total_volume = (
                self.df_filtered['FlowData'].sum() * time_interval_seconds) / 1000

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
            total_depth = (
                self.df_filtered['IntensityData'] * (self.current_inst.data_interval/60)).sum()
            duration_hrs = (self.df_filtered['Date'].max(
            ) - self.df_filtered['Date'].min()).total_seconds() / 3600
            return_period = round(
                10/(1.25*duration_hrs*(((0.0394*total_depth)+0.1)**-3.55)), 2)

            rainfall_textstr = 'Max intensity(mm/hr) = ' + str(round(max_intensity, 1))+'\nDepth(mm) = ' + str(
                round(total_depth, 1)) + '\nReturn Period(yr) = ' + str(round(return_period, 1))

            plot_rg_stats_box = self.plotCanvasReviewClassification.figure.text(
                0.05, 0.95, "", transform=self.plot_axis_rg.transAxes, fontsize=8, verticalalignment='top', bbox=a_props)

            plot_rg_stats_box.set_text(rainfall_textstr)

            self.plot_axis_rg.grid(True)

    def finalize_plot(self):
        self.plotCanvasReviewClassification.figure.autofmt_xdate()
        self.plotCanvasReviewClassification.figure.subplots_adjust(
            left=0.09, right=0.98, bottom=0.17, top=0.94)
        currentPlotTitle = f'Site: {self.current_inst.install_site_id}, Monitor: {self.current_inst.install_monitor_asset_id}, Client Ref: {self.current_inst.client_ref}'
        self.plotCanvasReviewClassification.figure.suptitle(
            currentPlotTitle, fontsize=12)

    def enable_update_button(self):
        """Enable the update button."""
        self.btnUpdate.setEnabled(True)

    def onAccept(self):
        self.update_interim_review()
        self.accept()
