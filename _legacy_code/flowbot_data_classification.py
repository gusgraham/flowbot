from datetime import datetime as dt, date
from typing import Optional
import numpy as np
import statistics
from statistics import mean
import matplotlib
from matplotlib.artist import Artist
from matplotlib.dates import DayLocator, DateFormatter, ConciseDateFormatter, AutoDateLocator
from matplotlib.ticker import FuncFormatter
import pandas as pd
from pandas import ExcelWriter
from xlsxwriter.utility import xl_rowcol_to_cell
from sklearn.ensemble import RandomForestClassifier
import time
from PyQt5.QtWidgets import (QApplication, QMessageBox)
from flowbot_helper import PlotWidget, resource_path, getBlankFigure
from flowbot_monitors import classifiedFlowMonitors
from flowbot_survey_events import plottedSurveyEvents, surveyEvent


class dataClassification():

    dictCat = {'B': 0, 'D': 1, 'E': 2, 'H': 3, 'L': 4, 'P': 5,
               'Q': 6, 'R': 7, 'S': 8, 'V': 9, 'W': 10, 'G': 11, 'X': 12}
    dictColor = {'B': (0.7569, 0.0588, 0.3137),
                 'D': (0.3529, 0.6745, 0.8863),
                 'E': (0.5373, 0.4824, 0.2039),
                 'H': (0.949, 0.9216, 0.7373),
                 'L': (0.6902, 0.9569, 0.2588),
                 'P': (0.6784, 0.9294, 0.9059),
                 'Q': (0.2078, 0.302, 0.5373),
                 'R': (0.2039, 0.4824, 0.7569),
                 'S': (0.949, 0.7765, 0.549),
                 'V': (1, 0.9725, 0.1765),
                 #  'W': (1, 1, 1),
                 'W': (0, 0.6275, 0),
                 'G': (1, 0.9725, 0.1765),
                 'X': (0.9569, 0.2549, 0.2549)}
    dictLabels = {'B': 'B (Backing Up)',
                  'D': 'D (Depth Problem)',
                  'E': 'E (Surcharge)',
                  'H': 'H (Standing Water)',
                  'L': 'L (Low Depth)',
                  'P': 'P (Pluming)',
                  'Q': 'Q (Low Flow)',
                  'R': 'R (Ragging)',
                  'S': 'S (Sediment)',
                  'V': 'V (Velocity Problem)',
                  'W': 'W (Working)',
                  'G': 'G (Dry Pipe)',
                  'X': 'X (Not Working)'}

    # def __init__(self, mwPW: Optional[PlotWidget]=None, myApp: Optional[QApplication]=None, parent=None, giveFeedback: bool = True):
    def __init__(self, mwPW: PlotWidget, myApp: Optional[QApplication]=None, parent=None, giveFeedback: bool = True):    

        self.plotAxisClassification = None
        self.plotAxisConfidence = None

        self.plotAxisDCPie = None
        self.plotDCStatsBox = None
        self.blnBootstrap = True
        self.strMaxDepth = "110"
        self.strMinSamplesLeaf = "4"
        self.strMinSamplesSplit = "5"
        self.strN_Estimators = "200"
        self.strMaxFeatures = "auto"
        self.blnFullPeriod = True
        self.class_date_range_start = '1/1/1066'
        self.class_date_range_end = '9/9/9999'
        self.strOutputFileSpec = ""
        self.strTrainingDataFileSpec = resource_path(
            "resources\\training_data_4.csv")
        self.join_df: pd.DataFrame = pd.DataFrame()
        self.main_window_plot_widget: PlotWidget = mwPW
        getBlankFigure(self.main_window_plot_widget)
        self.isBlank = True
        self.useDefaultParams = True
        self.classifiedFMs = classifiedFlowMonitors()
        self.plottedEvents = plottedSurveyEvents()
        self.giveFeedback = giveFeedback
        self.app = myApp
        self.parent = parent
        self.classificationNeedsRefreshed = False

    def updatePlot(self):

        self.main_window_plot_widget.figure.clear()
        if not self.classificationNeedsRefreshed:
            if len(self.classifiedFMs.classFMs) > 0:
                self.plotEventClassification()
                self.isBlank = False
            else:
                getBlankFigure(self.main_window_plot_widget)
                self.isBlank = True
        else:
            getBlankFigure(self.main_window_plot_widget)
            self.isBlank = True
        self.updateCanvas()

    def updateCanvas(self):
        self.main_window_plot_widget.showToolbar(False)

    def get_width_in_px(self, item):
        bbox = item.get_window_extent(self.main_window_plot_widget.figure.canvas.get_renderer(
        )).transformed(self.main_window_plot_widget.figure.dpi_scale_trans.inverted())
        width = bbox.width
        width *= self.main_window_plot_widget.figure.get_dpi()
        return width

    def plotEventClassification(self):

        DAY_List, FM_List, CATEGORY_List, CONFIDENCE_List = self.getPerDiemData()

        (self.plotAxisClassification, self.plotAxisConfidence) = self.main_window_plot_widget.figure.subplots(
            2, sharex=True, gridspec_kw={'height_ratios': [1, 1]})

        CATEGORY_Data = []
        for lst in CATEGORY_List:
            newRow = []
            for val in lst:
                if val in self.dictCat:
                    newRow.append(self.dictCat[val])
                else:
                    newRow.append(np.nan)
            CATEGORY_Data.append(newRow)

        CATEGORY_Data = np.array(CATEGORY_Data)
        CATEGORY_Label = np.array(CATEGORY_List)

        cMap = matplotlib.colors.ListedColormap([self.dictColor['B'], self.dictColor['D'], self.dictColor['E'], self.dictColor['H'],
                                                 self.dictColor['L'], self.dictColor['P'], self.dictColor['Q'], self.dictColor['R'],
                                                 self.dictColor['S'], self.dictColor['V'], self.dictColor['W'], self.dictColor['G'],
                                                 self.dictColor['X']])
        im = self.plotAxisClassification.pcolormesh(
            DAY_List, FM_List, CATEGORY_Data, cmap=cMap, vmin=0, vmax=12)

        colWidth = self.get_width_in_px(self.plotAxisClassification)
        colWidth = colWidth / len(DAY_List)
        pxBuffer = 2
        for i in range(len(FM_List)):
            for j in range(len(DAY_List)):
                text = self.plotAxisClassification.text(
                    DAY_List[j], i, CATEGORY_Label[i, j], ha="center", va="center", color="k")
                txtWidth = self.get_width_in_px(text)
                if (txtWidth + (2 * pxBuffer)) >= colWidth:
                    Artist.remove(text)

        cbar = self.plotAxisClassification.figure.colorbar(
            im, ax=self.plotAxisClassification)
        cbar.set_ticks(np.linspace(0.5, 11.5, 13))
        cbar.set_ticklabels(dataClassification.dictLabels.values())
        cbar.ax.set_ylabel("Classification", rotation=-90, va="bottom")

        CONFIDENCE_Data = np.array(CONFIDENCE_List)
        CONFIDENCE_Label = np.array(CONFIDENCE_List)

        im = self.plotAxisConfidence.pcolormesh(
            DAY_List, FM_List, CONFIDENCE_Data, cmap="RdYlGn", vmin=0, vmax=1)
        self.plotAxisConfidence.tick_params(top=False, bottom=True, labeltop=False, labelbottom=True)
        self.plotAxisConfidence.tick_params(top=False, bottom=True, labeltop=False, labelbottom=True)

        locator = AutoDateLocator(minticks=6, maxticks=15)
        formatter = ConciseDateFormatter(locator)
        self.plotAxisConfidence.xaxis.set_major_locator(locator)
        self.plotAxisConfidence.xaxis.set_major_formatter(formatter)

        # self.plotAxisConfidence.xaxis.set_major_locator(DayLocator())
        # self.plotAxisConfidence.xaxis.set_major_formatter(FuncFormatter(DateFormatter("%d/%m/%Y")))

        colWidth = self.get_width_in_px(self.plotAxisConfidence)
        colWidth = colWidth / len(DAY_List)
        pxBuffer = 2
        for i in range(len(FM_List)):
            for j in range(len(DAY_List)):
                text = self.plotAxisConfidence.text(DAY_List[j], i, round(CONFIDENCE_Label[i, j], 2),
                                                    ha="center", va="center", color="k")
                txtWidth = self.get_width_in_px(text)
                if (txtWidth + (2 * pxBuffer)) >= colWidth:
                    Artist.remove(text)

        cbar = self.plotAxisConfidence.figure.colorbar(
            im, ax=self.plotAxisConfidence)
        cbar.set_ticks(np.linspace(0, 1, 11))
        cbar.ax.set_ylabel("Confidence", rotation=-90, va="bottom")

        self.main_window_plot_widget.figure.autofmt_xdate()
        self.main_window_plot_widget.figure.subplots_adjust(
            left=0.09, right=0.98, bottom=0.05, top=0.94)

    def getEventBasedFMClassifications(self, se: surveyEvent):
        # dateformat = '%d/%m/%Y %H:%M:%S'

        dtStart = se.eventStart
        dtEnd = se.eventEnd

        start_truncated = date(dtStart.year, dtStart.month, dtStart.day)
        end_truncated = date(dtEnd.year, dtEnd.month, dtEnd.day)

        p = int(((end_truncated - start_truncated).total_seconds() / 86400)+1)

        event_day_range = pd.date_range(
            start=start_truncated, periods=p, freq='D').tolist()

        DAY_List = [d for d in event_day_range]

        event_analysis_df = self.join_df[pd.to_datetime(self.join_df["Day"], format="%d/%m/%Y").isin(DAY_List)]

        majorityClass = event_analysis_df.groupby(["FM"])["Predicted_rf"].agg(
            pd.Series.mode).to_frame()['Predicted_rf'].to_list()
        cleanData = []
        for item in majorityClass:
            if len(item) > 1:
                if 'W' in item:
                    cleanData.append('W')
                elif 'X' in item:
                    cleanData.append('X')
                else:
                    cleanData.append(item[0])
            else:
                cleanData.append(str(item))

        return cleanData

    def getPerDiemData(self):

        # dateformat = '%d/%m/%Y %H:%M:%S'

        if len(self.plottedEvents.plotEvents) > 0:
            dtStart = self.plottedEvents.getEaliestStart()
            dtEnd = self.plottedEvents.getLatestEnd()
        else:
            dtStart = self.classifiedFMs.classEarliestStart
            dtEnd = self.classifiedFMs.classLatestEnd

        start_truncated = date(dtStart.year, dtStart.month, dtStart.day)
        end_truncated = date(dtEnd.year, dtEnd.month, dtEnd.day)

        p = int(((end_truncated - start_truncated).total_seconds() / 86400)+1)

        event_day_range = pd.date_range(
            start=start_truncated, periods=p, freq='D').tolist()

        DAY_List = [d for d in event_day_range]
        FM_List = self.join_df["FM"].unique().tolist()

        event_analysis_df = self.join_df[pd.to_datetime(
            self.join_df["Day"], format="%d/%m/%Y").isin(DAY_List)]
        CATEGORY_List = []
        CONFIDENCE_List = []
        for fm in FM_List:
            currentCatRow = []
            currentConfRow = []
            for d in DAY_List:
                myD = d.strftime("%d/%m/%Y")
                # event_analysis_df_2 = event_analysis_df.query(r'Day == @myD and FM == @fm')
                event_analysis_df_2 = event_analysis_df.query(f'Day == "{myD}" and FM == "{fm}"')
                if len(event_analysis_df_2) > 0:
                    currentCatRow.append(
                        event_analysis_df_2.iloc[0]['Predicted_rf'])
                    dfMax = event_analysis_df_2[[
                        'B', 'D', 'E', 'H', 'L', 'P', 'Q', 'R', 'S', 'V', 'W', 'X']].max(axis=1)
                    currentConfRow.append(dfMax.iloc[0])
                else:
                    currentCatRow.append('')
                    currentConfRow.append(np.nan)

            CATEGORY_List.append(currentCatRow)
            CONFIDENCE_List.append(currentConfRow)

        return (DAY_List, FM_List, CATEGORY_List, CONFIDENCE_List)

    # def updateFlowSurveyDataClassification(self):

    #     results_list = []

    #     #             FDV_zip_list = list(zip(FDV_zip_list_dates, FDV_zip_list_days,
    #     #                                 fm.flowDataRange, fm.depthDataRange, fm.velocityDataRange))

    #     #             FDV_dataframe = pd.DataFrame(FDV_zip_list, columns=[
    #     #                                          'Date', 'Day', 'Flow', 'Depth', 'Velocity'])

    #     #     start_date = dt.strptime(self.class_date_range_start, "%d/%m/%Y")
    #     #     end_date = dt.strptime(self.class_date_range_end, "%d/%m/%Y")

    #     # self.dateRange: List[datetime] = []
    #     # self.flowDataRange: List[float] = []
    #     # self.depthDataRange: List[float] = []
    #     # self.velocityDataRange: List[float] = []

    #     for fm in self.classifiedFMs.classFMs.values():
    #         # Create a DataFrame
    #         data = {
    #             "Date": fm.dateRange,
    #             "FlowData": fm.flowDataRange,
    #             "DepthData": fm.depthDataRange,
    #             "VelocityData": fm.velocityDataRange,
    #         }
    #         df_fm_data = pd.DataFrame(data)

    #         start_date = df_fm_data["Date"].iloc[0]
    #         end_date = df_fm_data['Date'].iloc[-1]

    #         current_date = start_date

    #         while current_date <= end_date:

    #             features = pd.DataFrame()
    #             data = df_fm_data[
    #                 (df_fm_data["Date"] >= current_date)
    #                 & (df_fm_data["Date"] < current_date + timedelta(days=1))
    #             ]

    #             features = pd.DataFrame(columns=['month'])
    #             features.loc[0, 'month'] = current_date.month

    #             try:
    #                 area = int(fm.modelDataPipeHeight) * int(fm.modelDataPipeHeight)
    #             except:
    #                 area = np.NaN

    #             features.loc[0, "area"] = area

    #             features.loc[0, 'flow_entropy'] = entropy(data['FlowData'])
    #             features.loc[0, 'depth_range'] = data['DepthData'].max(
    #             ) - data['DepthData'].min()
    #             features.loc[0, 'depth_skewness'] = data['DepthData'].skew()
    #             features.loc[0, 'depth_entropy'] = entropy(data['DepthData'])
    #             features.loc[0, 'velocity_iqr'] = data['VelocityData'].quantile(
    #                 0.75) - data['VelocityData'].quantile(0.25)
    #             features.loc[0, 'velocity_entropy'] = entropy(
    #                 data['VelocityData'])

    #             try:
    #                 frequencies, psd, psd_normalized, low_freq_power, medium_freq_power, high_freq_power, total_power = self.frequencies(
    #                     data, 'FlowData')
    #                 features.loc[0, 'flow_power_low_freq_ratio'] = low_freq_power / total_power
    #                 features.loc[0, 'flow_power_medium_freq_ratio'] = medium_freq_power / total_power
    #             except:
    #                 features.loc[0, 'flow_power_low_freq_ratio'] = np.NaN
    #                 features.loc[0, 'flow_power_medium_freq_ratio'] = np.NaN

    #             try:
    #                 frequencies, psd, psd_normalized, low_freq_power, medium_freq_power, high_freq_power, total_power = self.frequencies(
    #                     data, 'DepthData')
    #                 features.loc[0, 'depth_power_skewness'] = skew(psd)
    #                 features.loc[0, 'depth_power_low_freq_ratio'] = low_freq_power / total_power
    #                 features.loc[0, 'depth_power_high_freq_ratio'] = high_freq_power / total_power
    #             except:
    #                 features.loc[0, 'depth_power_skewness'] = np.NaN
    #                 features.loc[0, 'depth_power_low_freq_ratio'] = np.NaN
    #                 features.loc[0, 'depth_power_high_freq_ratio'] = np.NaN

    #             try:
    #                 frequencies, psd, psd_normalized, low_freq_power, medium_freq_power, high_freq_power, total_power = self.frequencies(
    #                     data, 'VelocityData')
    #                 features.loc[0, 'velocity_dom_freq'] = frequencies[np.argmax(
    #                     psd)]
    #                 features.loc[0, 'velocity_shannon_entropy'] = - \
    #                     np.sum(psd_normalized * np.log2(psd_normalized))
    #             except:
    #                 features.loc[0, 'velocity_dom_freq'] = np.NaN
    #                 features.loc[0, 'velocity_shannon_entropy'] = np.NaN

    #             features.loc[0, 'velocity_to_flow'] = data.VelocityData.mean(
    #             ) / data.FlowData.mean()
    #             features.loc[0, 'depth_to_flow'] = data.DepthData.mean(
    #             ) / data.FlowData.mean()
    #             features.loc[0, 'velocity_to_depth'] = data.VelocityData.mean(
    #             ) / data.DepthData.mean()
    #             features.loc[0, 'depth_to_depth'] = data.DepthData.mean(
    #             ) / aInst.fm_pipe_depth_to_invert_mm
    #             features.loc[0, 'depth_max_to_depth'] = data.DepthData.max(
    #             ) / aInst.fm_pipe_depth_to_invert_mm
    #             features.loc[0, 'depth_to_area'] = data.DepthData.mean() / area
    #             features.loc[0, 'velocity_to_area'] = data.VelocityData.mean() / \
    #                 area

    #             features.loc[0, 'pipe_B'] = False
    #             features.loc[0, 'pipe_D'] = False
    #             features.loc[0, 'pipe_E'] = False
    #             features.loc[0, 'pipe_Y'] = False
    #             features.loc[0, 'pipe_Z'] = False

    #             features.loc[0, 'shape_C'] = fm.modelDataPipeShape == "Circular"

    #             with pd.option_context("future.no_silent_downcasting", True):
    #                 features.replace([np.inf, -np.inf], 1000000, inplace=True)

    #             model = CatBoostClassifier()
    #             model.load_model(self.FM_MODEL_PATH)

    #             # make predictions
    #             # prints only string without numpy arrays
    #             PREDICTION = model.predict(features)[0][0]
    #             # finds index of prediction of all possible classes
    #             index = list(model.classes_).index(PREDICTION)
    #             # gets confidence score of this class only. can remove [index] to get confidence for each class
    #             CONFIDENCE = model.predict_proba(features)[0][index]

    #             # Store results in a list
    #             results_list.append(
    #                 {'date': current_date, 'prediction': PREDICTION, 'confidence': CONFIDENCE})

    #             # Move to the next day
    #             current_date += timedelta(days=1)

    #     # Convert results list to DataFrame
    #     results = pd.DataFrame(results_list)
    #     results = results.rename(columns={
    #                              'date': 'Date', 'prediction': 'Classification', 'confidence': 'Confidence'})
    #     # results['Date'] = pd.to_datetime(results['Date']).dt.strftime('%d/%m/%Y')
    #     # # Convert column types
    #     # results['Date'] = results['Date'].astype(datetime)
    #     # results['Classification'] = results['Classification'].astype(str)
    #     # results['Confidence'] = results['Confidence'].astype(float)

    #     return results

    def updateFlowSurveyDataClassification(self):
        # ret = False

        # start_time = time.time()

        self.parent.progressBar.setMinimum(0)
        # add extra two steps to account for building the classifier and then classifying
        self.parent.progressBar.setMaximum(
            len(self.classifiedFMs.classFMs) + 4)
        self.parent.progressBar.setValue(0)
        self.parent.progressBar.show()

        start_date = dt.strptime(self.class_date_range_start, "%d/%m/%Y")
        end_date = dt.strptime(self.class_date_range_end, "%d/%m/%Y")

        try:

            # class_start_time = dt.now()
            # dateformat = '%d/%m/%Y'

            data_columns = ['monitor_name', 'day', 'max_depth', 'min_depth', 'ave_depth', 'std_dev_depth',
                            'zero_depth', 'max_velocity', 'min_velocity', 'ave_velocity', 'std_dev_velocity', 'zero_velocity']

            data_df = pd.DataFrame(columns=data_columns)

            # total_m = len(self.classifiedFMs.classFMs)

            # m_list = ['FM', 'DM']

            # y = 0

            data_df = data_df.iloc[0:0]

            progress_count = 0
            self.parent.progressBar.setValue(progress_count)
            self.parent.statusBar().showMessage(
                'Progress: Refreshing FM Classification Data...')

            for fm in self.classifiedFMs.classFMs.values():

                FDV_zip_list_dates = []
                FDV_zip_list_days = []
                for i in range(len(fm.dateRange)):

                    FDV_zip_list_dates.append(
                        fm.dateRange[i].strftime("%d/%m/%Y %H:%M"))

                    FDV_zip_list_days.append(
                        fm.dateRange[i].strftime("%d/%m/%Y"))

                FDV_zip_list = list(zip(FDV_zip_list_dates, FDV_zip_list_days,
                                    fm.flowDataRange, fm.depthDataRange, fm.velocityDataRange))

                FDV_dataframe = pd.DataFrame(FDV_zip_list, columns=[
                                             'Date', 'Day', 'Flow', 'Depth', 'Velocity'])

                list_of_days = []

                list_of_days = list(set(FDV_zip_list_days))

                # list_of_flow = []
                list_of_depth = []
                list_of_velocity = []
                zero_depth = 0
                zero_velocity = 0
                std_dev_depth = 0
                std_dev_velocity = 0
                ave_depth = 0
                ave_velocity = 0

                for i in range(len(list_of_days)):

                    if start_date <= dt.strptime(list_of_days[i], "%d/%m/%Y") <= end_date:

                        day = list_of_days[i]

                        day_variable = FDV_dataframe['Day'] == day

                        day_df = FDV_dataframe[day_variable]

                        list_of_depth = day_df['Depth'].tolist()

                        list_of_velocity = day_df['Velocity'].tolist()

                        # This allows for days that arnt installed for a full day to utilise the zero stats
                        norm_factor = 720/len(list_of_depth)

                        zero_depth = list_of_depth.count(0.0) * norm_factor

                        zero_velocity = list_of_velocity.count(
                            0.0) * norm_factor

                        if int(len(list_of_depth)) > 5:

                            max_depth = (max(list_of_depth))
                            min_depth = (min(list_of_depth))
                            std_dev_depth = (statistics.stdev(list_of_depth))
                            ave_depth = mean(list_of_depth)

                            max_velocity = (max(list_of_velocity))
                            min_velocity = (min(list_of_velocity))
                            std_dev_velocity = (
                                statistics.stdev(list_of_velocity))
                            ave_velocity = mean(list_of_velocity)

                            new_data = pd.DataFrame({'monitor_name': [fm.monitorName], 'day': [day], 'max_depth': [max_depth],
                                                     'min_depth': [min_depth], 'ave_depth': [ave_depth], 'std_dev_depth': [std_dev_depth],
                                                     'zero_depth': [zero_depth], 'max_velocity': [max_velocity], 'min_velocity': [min_velocity],
                                                     'ave_velocity': [ave_velocity], 'std_dev_velocity': [std_dev_velocity], 'zero_velocity': [zero_velocity]})
                            data_df = pd.concat([data_df, new_data], ignore_index=True)
                            # data_df = data_df.append({'monitor_name': fm.monitorName, 'day': day, 'max_depth': max_depth,
                            #                           'min_depth': min_depth, 'ave_depth': ave_depth, 'std_dev_depth': std_dev_depth,
                            #                           'zero_depth': zero_depth, 'max_velocity': max_velocity, 'min_velocity': min_velocity,
                            #                           'ave_velocity': ave_velocity, 'std_dev_velocity': std_dev_velocity,
                            #                           'zero_velocity': zero_velocity}, ignore_index=True)

                progress_count += 1
                self.parent.progressBar.setValue(progress_count)
                if self.app is not None:
                    self.app.processEvents()

            self.parent.statusBar().showMessage('Progress: Building Classifier...')
            progress_count += 1
            self.parent.progressBar.setValue(progress_count)
            if self.app is not None:
                self.app.processEvents()

            m_type = 'FM'  # Just using FMs at the moment

            if m_type == 'FM':
                data_df_2 = data_df.copy()
            elif m_type == 'DM':
                data_df_2 = data_df_2.append(data_df, ignore_index=True)

            balance_data = pd.read_csv(
                self.strTrainingDataFileSpec, sep=',', header=0)

            M_variable = balance_data['m_type'] == m_type
            training_df = balance_data[M_variable]

            if m_type == 'FM':

                X_train = training_df.values[:, 5:15]
                y_train = training_df.values[:, 4]

                X_test = data_df.iloc[:, 2:12].values.tolist()

            elif m_type == 'DM':

                X_train = training_df.values[:, 5:10]
                y_train = training_df.values[:, 4]

                X_test = data_df.iloc[:, 2:7].values.tolist()

            if len(X_train) > 0 and len(y_train) > 0 and len(X_test) > 0:

                # rf = RandomForestClassifier(bootstrap=self.blnBootstrap,
                #                             max_depth=int(
                #                                 self.strMaxDepth),
                #                             max_features=(self.strMaxFeatures if self.strMaxFeatures == 'auto' else int(
                #                                 self.strMaxFeatures)),
                #                             min_samples_leaf=int(
                #                                 self.strMinSamplesLeaf),
                #                             min_samples_split=int(
                #                                 self.strMinSamplesSplit),
                #                             n_estimators=int(
                #                                 self.strN_Estimators),
                #                             random_state=1234567)

                rf = RandomForestClassifier(bootstrap=self.blnBootstrap,
                                            max_depth=int(
                                                self.strMaxDepth),
                                            max_features=('sqrt' if self.strMaxFeatures == 'auto' else int(
                                                self.strMaxFeatures)),
                                            min_samples_leaf=int(
                                                self.strMinSamplesLeaf),
                                            min_samples_split=int(
                                                self.strMinSamplesSplit),
                                            n_estimators=int(
                                                self.strN_Estimators),
                                            random_state=1234567)

                self.parent.statusBar().showMessage('Progress: Building Classifier...')
                rf.fit(X_train, y_train)
                progress_count += 1
                self.parent.progressBar.setValue(progress_count)
                if self.app is not None:
                    self.app.processEvents()

                self.parent.statusBar().showMessage('Progress: Classifiying Data...')
                y_pred_rf = rf.predict(X_test)
                progress_count += 1
                self.parent.progressBar.setValue(progress_count)
                if self.app is not None:
                    self.app.processEvents()

                class_names = rf.classes_.tolist()
                predictions = rf.predict_proba(X_test)

                if m_type == 'FM':

                    fm_df = pd.DataFrame({'FM': data_df['monitor_name'], 'Day': data_df['day'], 'Predicted_rf': y_pred_rf,
                                          class_names[0]: predictions[:, 0],
                                          class_names[1]: predictions[:, 1],
                                          class_names[2]: predictions[:, 2],
                                          class_names[3]: predictions[:, 3],
                                          class_names[4]: predictions[:, 4],
                                          class_names[5]: predictions[:, 5],
                                          class_names[6]: predictions[:, 6],
                                          class_names[7]: predictions[:, 7],
                                          class_names[8]: predictions[:, 8],
                                          class_names[9]: predictions[:, 9],
                                          class_names[10]: predictions[:, 10],
                                          class_names[11]: predictions[:, 11]})

                    fm_df = fm_df[['FM',
                                   'Day',
                                   'Predicted_rf',
                                   class_names[0],
                                   class_names[1],
                                   class_names[2],
                                   class_names[3],
                                   class_names[4],
                                   class_names[5],
                                   class_names[6],
                                   class_names[7],
                                   class_names[8],
                                   class_names[9],
                                   class_names[10],
                                   class_names[11]]]
                elif m_type == 'DM':

                    dm_df = pd.DataFrame({'FM': data_df['monitor_name'], 'Day': data_df['day'], 'Predicted_rf': y_pred_rf,
                                          class_names[0]: predictions[:, 0],
                                          class_names[1]: predictions[:, 1],
                                          class_names[2]: predictions[:, 2]})

                    dm_df = dm_df[['FM', 'Day', 'Predicted_rf',
                                   class_names[0], class_names[1], class_names[2]]]

            self.join_df = fm_df.copy()

            FM = self.join_df['FM']
            Day = self.join_df['Day']
            Predicted_rf = self.join_df['Predicted_rf']

            self.join_df.drop(
                labels=['FM'], axis=1, inplace=True)
            self.join_df.drop(
                labels=['Day'], axis=1, inplace=True)
            self.join_df.drop(
                labels=['Predicted_rf'], axis=1, inplace=True)

            self.join_df.insert(0, 'FM', FM)
            self.join_df.insert(1, 'Day', Day)
            self.join_df.insert(
                2, 'Predicted_rf', Predicted_rf)

            concec_df = self.join_df.copy()
            concec_df = concec_df.iloc[:, [0, 1, 2]]

            concec_df['Day'] = concec_df['Day'].apply(
                lambda x: dt.strptime(x, "%d/%m/%Y"))

            concec_df.sort_values(['FM', 'Day'], ascending=[
                                  True, True], inplace=True)

            labels = (concec_df.Predicted_rf !=
                      concec_df.Predicted_rf .shift()).cumsum()

            concec_df['flag'] = (labels.map(labels.value_counts()) >= 1).astype(int)

            concec_df = concec_df.loc[(concec_df['flag'] == 1) & (
                concec_df['Predicted_rf'] == 'X')]

            # this means all coulms of df will be printed
            pd.set_option('display.max_columns', None)

            data_df_2.rename(columns={'day': 'Day'}, inplace=True)
            data_df_2.rename(columns={'monitor_name': 'FM'}, inplace=True)

            combined_df = pd.merge(
                data_df_2, self.join_df, on=['FM', 'Day'])

            class_refine = 1
            if class_refine == 1:

                # ----------------------------------------
                H_df = combined_df.loc[(combined_df['zero_velocity'] >= 600) & (
                    combined_df['Predicted_rf'] == 'R')]

                G_df = combined_df.loc[(combined_df['zero_velocity'] >= 600) & (combined_df['zero_depth'] <= 10) & (
                    combined_df['Predicted_rf'] == 'L') & (combined_df['ave_depth'] <= 20) & (combined_df['max_depth'] <= 20)]

                L_df = combined_df.loc[(combined_df['max_depth'] <= 100) & (combined_df['min_depth'] <= 100) & (
                    combined_df['ave_depth'] <= 100) & (combined_df['Predicted_rf'] == 'H')]

                # ----------------------------------------
                for r in range(len(self.join_df)):

                    row_FM = self.join_df.iloc[r, self.join_df.columns.get_loc(
                        'FM')]
                    row_Day = self.join_df.iloc[r, self.join_df.columns.get_loc(
                        'Day')]

                    # -------------------------------------------------------------------------------------------------------------------------------------------------
                    # This updates Standing Water that has be classed as ragging

                    if len(H_df.loc[(H_df.FM == row_FM) & (H_df.Day == row_Day)]) == 1:

                        self.join_df.iloc[r, self.join_df.columns.get_loc(
                            'Predicted_rf')] = 'H'
                        self.join_df.iloc[r, self.join_df.columns.get_loc(
                            'R')] = 0.999

                    # -------------------------------------------------------------------------------------------------------------------------------------------------
                    # This updates Dry Pipes that have be classed as low flow

                    if len(G_df.loc[(G_df.FM == row_FM) & (G_df.Day == row_Day)]) == 1:

                        self.join_df.iloc[r, self.join_df.columns.get_loc(
                            'Predicted_rf')] = 'G'
                        self.join_df.iloc[r, self.join_df.columns.get_loc(
                            'L')] = 0.999

                    # -------------------------------------------------------------------------------------------------------------------------------------------------
                    # This updates Low Flows that have been classed as standing water

                    if len(L_df.loc[(L_df.FM == row_FM) & (L_df.Day == row_Day)]) == 1:

                        self.join_df.iloc[r, self.join_df.columns.get_loc(
                            'Predicted_rf')] = 'L'
                        self.join_df.iloc[r, self.join_df.columns.get_loc(
                            'H')] = 0.999

            self.classificationNeedsRefreshed = False
            progress_count += 1
            self.parent.progressBar.setValue(progress_count)

            self.parent.statusBar().showMessage('')
            if self.app is not None:
                self.app.processEvents()

            if self.giveFeedback:
                QMessageBox.information(
                    self.parent, "Update Data Classification", "Complete")

        except Exception as e:
            if self.giveFeedback:
                QMessageBox.information(self.parent, "Update Data Classification", 'Update raised an exception')

    def exportDataClassificationToExcel(self):

        # _____________________________________________________________________________________________________________________________________________
        # This is the intial import of the dataframe and setup of the data worksheet

        wb_location = self.strOutputFileSpec
        # ________________________________________________________
        # This combines the list of moniotrs with & without data
        monitor_names_1D = self.join_df["FM"].unique()

        monitor_names = []
        no_data_list = []

        for u in range(len(monitor_names_1D)):

            monitor_names.append(monitor_names_1D[u])

        monitor_names = monitor_names + no_data_list

        # ________________________________________________________

        days = self.join_df["Day"].unique()

        monitor_names.sort()

        sorted_days = sorted(days, key=lambda x: dt.strptime(x, "%d/%m/%Y"))

        writer = ExcelWriter(wb_location)

        self.join_df.to_excel(writer, 'Data', startcol=2,
                              startrow=0, index=False)

        workbook = writer.book

        worksheet = writer.sheets['Data']

        header = workbook.add_format({'bold': True, 'border': 1})

        worksheet.write('A1', 'KEY', header)
        worksheet.write('B1', 'MAX', header)

        worksheet.set_column(0, 0, 17.82)
        worksheet.set_column(1, 4, 10.55)

        for r in range(1, len(self.join_df)+1):
            worksheet.write_formula(xl_rowcol_to_cell(r, 0), f'={xl_rowcol_to_cell(r, 2)}&"_"&{xl_rowcol_to_cell(r, 3)}')
            worksheet.write_formula(xl_rowcol_to_cell(r, 1), f'=MAX({xl_rowcol_to_cell(r, 5)}:{xl_rowcol_to_cell(r, 22)})')
        # _____________________________________________________
        # This is the setup of the output worksheet

        L_class_conditonal_format = workbook.add_format()
        L_class_conditonal_format.set_bg_color('#b0f442')

        X_class_conditonal_format = workbook.add_format()
        X_class_conditonal_format.set_bg_color('#f44141')

        Q_class_conditonal_format = workbook.add_format()
        Q_class_conditonal_format.set_bg_color('#354d89')

        E_class_conditonal_format = workbook.add_format()
        E_class_conditonal_format.set_bg_color('#897b34')

        R_class_conditonal_format = workbook.add_format()
        R_class_conditonal_format.set_bg_color('#347bc1')

        B_class_conditonal_format = workbook.add_format()
        B_class_conditonal_format.set_bg_color('#c10f50')

        H_class_conditonal_format = workbook.add_format()
        H_class_conditonal_format.set_bg_color('#f2ebbc')

        D_class_conditonal_format = workbook.add_format()
        D_class_conditonal_format.set_bg_color('#5aace2')

        V_class_conditonal_format = workbook.add_format()
        V_class_conditonal_format.set_bg_color('#fff82d')

        P_class_conditonal_format = workbook.add_format()
        P_class_conditonal_format.set_bg_color('#adede7')

        S_class_conditonal_format = workbook.add_format()
        S_class_conditonal_format.set_bg_color('#f2c68c')

        G_class_conditonal_format = workbook.add_format()
        G_class_conditonal_format.set_bg_color('#fff82d')

        y_col_format = workbook.add_format({'bold': True, 'border': 1})
        x_col_format = workbook.add_format({'bold': True, 'border': 1})
        x_col_format.set_rotation(90)

        event_x_col_format = workbook.add_format({'bold': True, 'border': 1})
        event_x_col_format.set_rotation(90)
        event_x_col_format.set_bg_color('#FFEE58')

        worksheet = workbook.add_worksheet(name='Output')
        worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(
            sorted_days)), {'type': 'text', 'criteria': 'containing', 'value': 'L', 'format': L_class_conditonal_format})
        worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(
            sorted_days)), {'type': 'text', 'criteria': 'containing', 'value': 'X', 'format': X_class_conditonal_format})
        worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(
            sorted_days)), {'type': 'text', 'criteria': 'containing', 'value': 'Q', 'format': Q_class_conditonal_format})
        worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(
            sorted_days)), {'type': 'text', 'criteria': 'containing', 'value': 'E', 'format': E_class_conditonal_format})
        worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(
            sorted_days)), {'type': 'text', 'criteria': 'containing', 'value': 'R', 'format': R_class_conditonal_format})
        worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(
            sorted_days)), {'type': 'text', 'criteria': 'containing', 'value': 'B', 'format': B_class_conditonal_format})
        worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(
            sorted_days)), {'type': 'text', 'criteria': 'containing', 'value': 'H', 'format': H_class_conditonal_format})
        worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(
            sorted_days)), {'type': 'text', 'criteria': 'containing', 'value': 'D', 'format': D_class_conditonal_format})
        worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(
            sorted_days)), {'type': 'text', 'criteria': 'containing', 'value': 'V', 'format': V_class_conditonal_format})
        worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(
            sorted_days)), {'type': 'text', 'criteria': 'containing', 'value': 'P', 'format': P_class_conditonal_format})
        worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(
            sorted_days)), {'type': 'text', 'criteria': 'containing', 'value': 'S', 'format': S_class_conditonal_format})

        worksheet.conditional_format(xl_rowcol_to_cell(5, 1)+':'+xl_rowcol_to_cell(len(monitor_names)+4, len(
            sorted_days)), {'type': 'text', 'criteria': 'containing', 'value': 'G', 'format': G_class_conditonal_format})

        for r in range(len(monitor_names)):

            worksheet.write(xl_rowcol_to_cell(r+5, 0),
                            monitor_names[r], y_col_format)

            for c in range(len(sorted_days)):

                worksheet.write_formula(xl_rowcol_to_cell(r+5, c+1),
                                        f'IFERROR(VLOOKUP({xl_rowcol_to_cell(r+5, 0)}&"_"&{xl_rowcol_to_cell(4, c+1)},Data!$A:$E,5,FALSE),"-")')

        worksheet.set_column(1, len(sorted_days)+67, 2.73)

        for c in range(len(sorted_days)):

            worksheet.write(xl_rowcol_to_cell(4, c+1),
                            sorted_days[c], x_col_format)

        key_text = workbook.add_format({'bold': True, })

        worksheet.write(xl_rowcol_to_cell(1, 2), 'B',
                        B_class_conditonal_format)
        worksheet.write(xl_rowcol_to_cell(1, 3), 'Backing Up', key_text)

        worksheet.write(xl_rowcol_to_cell(1, 8), 'D',
                        D_class_conditonal_format)
        worksheet.write(xl_rowcol_to_cell(1, 9), 'Depth Problem', key_text)

        worksheet.write(xl_rowcol_to_cell(1, 14), 'E',
                        E_class_conditonal_format)
        worksheet.write(xl_rowcol_to_cell(1, 15), 'Surcharge', key_text)

        worksheet.write(xl_rowcol_to_cell(1, 19), 'H',
                        H_class_conditonal_format)
        worksheet.write(xl_rowcol_to_cell(1, 20), 'Standing Water', key_text)

        worksheet.write(xl_rowcol_to_cell(1, 25), 'L',
                        L_class_conditonal_format)
        worksheet.write(xl_rowcol_to_cell(1, 26), 'Low Depth', key_text)

        worksheet.write(xl_rowcol_to_cell(1, 30), 'P',
                        P_class_conditonal_format)
        worksheet.write(xl_rowcol_to_cell(1, 31), 'Pluming', key_text)

        worksheet.write(xl_rowcol_to_cell(1, 35), 'Q',
                        Q_class_conditonal_format)
        worksheet.write(xl_rowcol_to_cell(1, 36), 'Low Flow', key_text)

        worksheet.write(xl_rowcol_to_cell(1, 40), 'R',
                        R_class_conditonal_format)
        worksheet.write(xl_rowcol_to_cell(1, 41), 'Ragging', key_text)

        worksheet.write(xl_rowcol_to_cell(1, 45), 'S',
                        S_class_conditonal_format)
        worksheet.write(xl_rowcol_to_cell(1, 46), 'Sediment', key_text)

        worksheet.write(xl_rowcol_to_cell(1, 50), 'V',
                        V_class_conditonal_format)
        worksheet.write(xl_rowcol_to_cell(1, 51), 'Velocity Problem', key_text)

        worksheet.write(xl_rowcol_to_cell(1, 56), 'W')
        worksheet.write(xl_rowcol_to_cell(1, 57), 'Working', key_text)

        worksheet.write(xl_rowcol_to_cell(1, 61), 'G',
                        G_class_conditonal_format)
        worksheet.write(xl_rowcol_to_cell(1, 62), 'Dry Pipe', key_text)

        worksheet.write(xl_rowcol_to_cell(1, 66), 'X',
                        X_class_conditonal_format)
        worksheet.write(xl_rowcol_to_cell(1, 67), 'Not Working', key_text)

        worksheet = workbook.add_worksheet(name='Confidence')

        two_decimal_place = workbook.add_format()
        two_decimal_place.set_num_format('0.00')

        worksheet.set_column(1, len(sorted_days), 4.45)

        for r in range(len(monitor_names)):

            worksheet.write(xl_rowcol_to_cell(r+1, 0),
                            monitor_names[r], y_col_format)

            for c in range(len(sorted_days)):

                worksheet.write_formula(xl_rowcol_to_cell(r+1, c+1),
                                        f'IFERROR(VLOOKUP({xl_rowcol_to_cell(r+1, 0)}&"_"&{xl_rowcol_to_cell(0, c+1)},Data!$A:$B,2,FALSE),"-")',
                                        two_decimal_place)

        for c in range(len(sorted_days)):

            worksheet.write(xl_rowcol_to_cell(0, c+1),
                            sorted_days[c], x_col_format)

        worksheet.conditional_format(f'{xl_rowcol_to_cell(1, 1)}:{xl_rowcol_to_cell(len(monitor_names), len(sorted_days))}', {
                                     'type': '3_color_scale'})

        writer.save()
        writer.close()

        time.sleep(1)

        # class_end_time = dt.now()

        QMessageBox.information(None, "Export Data Classification", "Complete")
