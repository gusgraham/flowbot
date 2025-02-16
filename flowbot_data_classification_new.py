# import libraries

# data processing
import pandas as pd
import numpy as np
import os
import datetime
from sklearn.utils.class_weight import compute_class_weight
from scipy.stats import entropy, skew, kurtosis
from scipy.signal import welch
import joblib
from flowbot_helper import resource_path

# models
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from catboost import CatBoostClassifier


# INPUTS: provide data for one sensor

RAW_DATA_PATH = os.path.join("Data", "Raw", "T1070 Middleton", "T1070 CSV", "T1070DM001.CSV")  # in CSV - using an example here in local env
DATE = "21/08/2023"  # in str format with day/month/year format
DATE = datetime.datetime.strptime(DATE, '%d/%m/%Y')
SENSOR_INFO_PATH = os.path.join("Data", "Raw", "T1070.xls")  # at the moment from excel sheet - "FM loc"
SENSOR_TYPE = "DM"  # this can be automated through file names - either "DM", "RG" or "FM"
SENSOR_NAME = "DM001"  # this can be automated through file names

# model specific paths
DM_MODEL_PATH = resource_path("resources\\classifier\\models\\DM_model.pkl")
RG_MODEL_PATH = resource_path("resources\\classifier\\models\\RG_model.pkl")
FM_MODEL_PATH = resource_path("resources\\classifier\\models\\FM_model.cbm")

# process data (per sensor)


def read_data(RAW_DATA_PATH, DATE):
    data = pd.read_csv(RAW_DATA_PATH)
    data.Date = pd.to_datetime(data.Date, format="%d/%m/%Y %H:%M:%S")
    data = data[(data['Date'] >= DATE) & (data['Date'] < DATE + datetime.timedelta(days=1))]
    return data


def frequencies(data, column):
    segments = 10
    sr = 60 / data.Date.diff().mean().total_seconds()
    nperseg = 2 * data.shape[0] * sr / segments
    frequencies, psd = welch(data[column], fs=sr, nperseg=nperseg)
    psd_normalized = psd / np.sum(psd)
    freq_range = frequencies[-1] - frequencies[0]
    low_band = frequencies[0] + freq_range / 3
    high_band = frequencies[-1] - freq_range / 3
    low_freq_power = np.sum(psd[frequencies < low_band])
    medium_freq_power = np.sum(psd[(frequencies > low_band) & (frequencies < high_band)])
    high_freq_power = np.sum(psd[frequencies > high_band])
    total_power = np.sum(psd)

    return frequencies, psd, psd_normalized, low_freq_power, medium_freq_power, high_freq_power, total_power


if SENSOR_TYPE == 'DM':

    data = read_data(RAW_DATA_PATH, DATE)

    features = pd.DataFrame(columns=['depth_entropy'])
    features.loc[0, f'depth_entropy'] = entropy(data['Depth'])
    features.fillna(0, inplace=True)
    features.replace([np.inf, -np.inf], 1000000, inplace=True)

elif SENSOR_TYPE == 'RG':
    data = read_data(RAW_DATA_PATH, DATE)

    data.columns = ['Date', 'Rain']

    features = pd.DataFrame(columns=['month'])
    features.loc[0, 'month'] = DATE.month
    features.loc[0, 'rain_median'] = data['Rain'].median()
    features.loc[0, 'rain_skewness'] = data['Rain'].skew()
    features.loc[0, 'rain_percentile_25'] = data['Rain'].quantile(0.25)
    features.loc[0, 'rain_percentile_75'] = data['Rain'].quantile(0.75)
    features.loc[0, 'rain_entropy'] = entropy(data['Rain'])
    try:
        frequencies, psd, psd_normalized, low_freq_power, medium_freq_power, high_freq_power, total_power = frequencies(data, 'Rain')

        features.loc[0, 'rain_dom_freq'] = frequencies[np.argmax(psd)]
        features.loc[0, 'rain_power_peak'] = np.max(psd)
        features.loc[0, 'rain_power_skewness'] = skew(psd)
        features.loc[0, 'rain_power_kurtosis'] = kurtosis(psd)
        features.loc[0, 'rain_power_low_freq_ratio'] = low_freq_power / total_power
        features.loc[0, 'rain_power_high_freq_ratio'] = high_freq_power / total_power
    except:
        features.loc[0, 'rain_dom_freq'] = np.NaN
        features.loc[0, 'rain_power_peak'] = np.NaN
        features.loc[0, 'rain_power_skewness'] = np.NaN
        features.loc[0, 'rain_power_kurtosis'] = np.NaN
        features.loc[0, 'rain_power_low_freq_ratio'] = np.NaN
        features.loc[0, 'rain_power_high_freq_ratio'] = np.NaN

    features.replace([np.inf, -np.inf], 1000000, inplace=True)

elif SENSOR_TYPE == 'FM':
    data = read_data(RAW_DATA_PATH, DATE)
    sensor_info_excel = pd.read_excel(SENSOR_INFO_PATH, sheet_name='FM loc', skiprows=3)
    sensor_info_excel.columns = [col.strip() for col in sensor_info_excel.columns]
    sensor_info_excel.columns.values[0] = "sensor"
    sensor_info = sensor_info_excel[sensor_info_excel.sensor == SENSOR_NAME]
    features = pd.DataFrame(columns=['month'])

    features.loc[0, 'month'] = DATE.month

    pipe = sensor_info.Pipe.values[0].strip().upper()
    shape = sensor_info.Shape.values[0].strip().upper()
    height = sensor_info['Height mm'].values[0]
    width = sensor_info['Width mm'].values[0]
    depth = sensor_info['Depth mm'].values[0]
    try:
        area = int(height) * int(width)
    except:
        area = np.NaN

    features.loc[0, "area"] = area

    features.loc[0, 'flow_entropy'] = entropy(data['Flow'])
    features.loc[0, 'depth_range'] = data['Depth'].max() - data['Depth'].min()
    features.loc[0, 'depth_skewness'] = data['Depth'].skew()
    features.loc[0, 'depth_entropy'] = entropy(data['Depth'])
    features.loc[0, 'velocity_iqr'] = data['Velocity'].quantile(0.75) - data['Velocity'].quantile(0.25)
    features.loc[0, 'velocity_entropy'] = entropy(data['Velocity'])

    try:
        frequencies, psd, psd_normalized, low_freq_power, medium_freq_power, high_freq_power, total_power = frequencies(data, 'Flow')
        features.loc[0, 'flow_power_low_freq_ratio'] = low_freq_power / total_power
        features.loc[0, 'flow_power_medium_freq_ratio'] = medium_freq_power / total_power
    except:
        features.loc[0, 'flow_power_low_freq_ratio'] = np.NaN
        features.loc[0, 'flow_power_medium_freq_ratio'] = np.NaN

    try:
        frequencies, psd, psd_normalized, low_freq_power, medium_freq_power, high_freq_power, total_power = frequencies(data, 'Depth')
        features.loc[0, 'depth_power_skewness'] = skew(psd)
        features.loc[0, 'depth_power_low_freq_ratio'] = low_freq_power / total_power
        features.loc[0, 'depth_power_high_freq_ratio'] = high_freq_power / total_power
    except:
        features.loc[0, 'depth_power_skewness'] = np.NaN
        features.loc[0, 'depth_power_low_freq_ratio'] = np.NaN
        features.loc[0, 'depth_power_high_freq_ratio'] = np.NaN

    try:
        frequencies, psd, psd_normalized, low_freq_power, medium_freq_power, high_freq_power, total_power = frequencies(data, 'Velocity')
        features.loc[0, 'velocity_dom_freq'] = frequencies[np.argmax(psd)]
        features.loc[0, 'velocity_shannon_entropy'] = -np.sum(psd_normalized * np.log2(psd_normalized))
    except:
        features.loc[0, 'velocity_dom_freq'] = np.NaN
        features.loc[0, 'velocity_shannon_entropy'] = np.NaN

    features.loc[0, 'velocity_to_flow'] = data.Velocity.mean() / data.Flow.mean()
    features.loc[0, 'depth_to_flow'] = data.Depth.mean() / data.Flow.mean()
    features.loc[0, 'velocity_to_depth'] = data.Velocity.mean() / data.Depth.mean()
    features.loc[0, 'depth_to_depth'] = data.Depth.mean() / depth
    features.loc[0, 'depth_max_to_depth'] = data.Depth.max() / depth
    features.loc[0, 'depth_to_area'] = data.Depth.mean() / area
    features.loc[0, 'velocity_to_area'] = data.Velocity.mean() / area

    features.loc[0, 'pipe_B'] = pipe == "B"
    features.loc[0, 'pipe_D'] = pipe == "D"
    features.loc[0, 'pipe_E'] = pipe == "E"
    features.loc[0, 'pipe_Y'] = pipe == "Y"
    features.loc[0, 'pipe_Z'] = pipe == "Z"

    features.loc[0, 'shape_A'] = pipe == "A"
    features.loc[0, 'shape_B'] = pipe == "B"
    features.loc[0, 'shape_E'] = pipe == "E"
    features.loc[0, 'shape_X'] = pipe == "X"
    features.loc[0, 'shape_c'] = pipe == "C"

    features.replace([np.inf, -np.inf], 1000000, inplace=True)

# load trained model

if SENSOR_TYPE == 'DM':
    model = joblib.load(DM_MODEL_PATH)
elif SENSOR_TYPE == 'RG':
    model = joblib.load(RG_MODEL_PATH)
elif SENSOR_TYPE == 'FM':
    model = CatBoostClassifier()
    model.load_model(FM_MODEL_PATH)

# make predictions
PREDICTION = model.predict(features)[0][0]  # prints only string without numpy arrays
index = list(model.classes_).index(PREDICTION)  # finds index of prediction of all possible classes
# gets confidence score of this class only. can remove [index] to get confidence for each class
CONFIDENCE = model.predict_proba(features)[0][index]

# output
print(PREDICTION)
print(CONFIDENCE)
