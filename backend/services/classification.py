"""
Data Classification Service
Ports the legacy fsmDataClassification logic for ML-based daily data classification.
"""
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from scipy.stats import entropy, skew, kurtosis
from scipy.signal import welch

# Models are loaded lazily to avoid startup delays
_models_cache: Dict[str, Any] = {}

# Model paths relative to backend directory
MODELS_DIR = Path(__file__).parent.parent / "resources" / "classifier" / "models"


def get_model(model_type: str):
    """Load and cache ML models."""
    global _models_cache
    
    if model_type in _models_cache:
        return _models_cache[model_type]
    
    if model_type == "DM":
        import joblib
        model_path = MODELS_DIR / "DM_model.pkl"
        if model_path.exists():
            _models_cache["DM"] = joblib.load(model_path)
        else:
            raise FileNotFoundError(f"DM model not found at {model_path}")
            
    elif model_type == "RG":
        import joblib
        model_path = MODELS_DIR / "RG_model.pkl"
        if model_path.exists():
            _models_cache["RG"] = joblib.load(model_path)
        else:
            raise FileNotFoundError(f"RG model not found at {model_path}")
            
    elif model_type == "FM":
        from catboost import CatBoostClassifier
        model_path = MODELS_DIR / "FM_model.cbm"
        if model_path.exists():
            model = CatBoostClassifier()
            model.load_model(str(model_path))
            _models_cache["FM"] = model
        else:
            raise FileNotFoundError(f"FM model not found at {model_path}")
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    return _models_cache[model_type]


def calculate_frequencies(data: pd.DataFrame, column: str):
    """Calculate frequency domain features using Welch's method."""
    try:
        segments = 10
        # Calculate sampling rate from time differences
        if 'Date' in data.columns:
            sr = 60 / data['Date'].diff().mean().total_seconds()
        else:
            sr = 1  # Default to 1 sample per minute
        
        nperseg = min(len(data), int(2 * len(data) * sr / segments))
        if nperseg < 4:
            nperseg = 4
            
        frequencies, psd = welch(data[column].dropna(), fs=sr, nperseg=nperseg)
        psd_normalized = psd / np.sum(psd) if np.sum(psd) > 0 else psd
        
        freq_range = frequencies[-1] - frequencies[0] if len(frequencies) > 1 else 1
        low_band = frequencies[0] + freq_range / 3
        high_band = frequencies[-1] - freq_range / 3
        
        low_freq_power = np.sum(psd[frequencies < low_band])
        medium_freq_power = np.sum(psd[(frequencies > low_band) & (frequencies < high_band)])
        high_freq_power = np.sum(psd[frequencies > high_band])
        total_power = np.sum(psd)
        
        return {
            "frequencies": frequencies,
            "psd": psd,
            "psd_normalized": psd_normalized,
            "low_freq_power": low_freq_power,
            "medium_freq_power": medium_freq_power,
            "high_freq_power": high_freq_power,
            "total_power": total_power
        }
    except Exception:
        return None


def extract_dm_features(data: pd.DataFrame) -> pd.DataFrame:
    """Extract features for Depth Monitor classification."""
    features = pd.DataFrame(columns=['depth_entropy'])
    
    if 'DepthData' in data.columns and len(data) > 0:
        features.loc[0, 'depth_entropy'] = entropy(data['DepthData'].dropna())
    else:
        features.loc[0, 'depth_entropy'] = 0
    
    features.fillna(0, inplace=True)
    features.replace([np.inf, -np.inf], 1000000, inplace=True)
    
    return features


def extract_rg_features(data: pd.DataFrame, current_date: datetime) -> pd.DataFrame:
    """Extract features for Rain Gauge classification."""
    features = pd.DataFrame()
    
    intensity_col = 'IntensityData' if 'IntensityData' in data.columns else 'Rain'
    
    features.loc[0, 'month'] = current_date.month
    
    if intensity_col in data.columns and len(data) > 0:
        intensity = data[intensity_col].dropna()
        features.loc[0, 'rain_median'] = intensity.median()
        features.loc[0, 'rain_skewness'] = intensity.skew()
        features.loc[0, 'rain_percentile_25'] = intensity.quantile(0.25)
        features.loc[0, 'rain_percentile_75'] = intensity.quantile(0.75)
        features.loc[0, 'rain_entropy'] = entropy(intensity) if len(intensity) > 0 else 0
        
        freq_result = calculate_frequencies(data, intensity_col)
        if freq_result:
            features.loc[0, 'rain_dom_freq'] = freq_result['frequencies'][np.argmax(freq_result['psd'])] if len(freq_result['psd']) > 0 else np.nan
            features.loc[0, 'rain_power_peak'] = np.max(freq_result['psd'])
            features.loc[0, 'rain_power_skewness'] = skew(freq_result['psd'])
            features.loc[0, 'rain_power_kurtosis'] = kurtosis(freq_result['psd'])
            features.loc[0, 'rain_power_low_freq_ratio'] = freq_result['low_freq_power'] / freq_result['total_power'] if freq_result['total_power'] > 0 else np.nan
            features.loc[0, 'rain_power_high_freq_ratio'] = freq_result['high_freq_power'] / freq_result['total_power'] if freq_result['total_power'] > 0 else np.nan
        else:
            for col in ['rain_dom_freq', 'rain_power_peak', 'rain_power_skewness', 'rain_power_kurtosis', 'rain_power_low_freq_ratio', 'rain_power_high_freq_ratio']:
                features.loc[0, col] = np.nan
    
    features.replace([np.inf, -np.inf], 1000000, inplace=True)
    
    return features


def extract_fm_features(data: pd.DataFrame, current_date: datetime, install_data: Dict) -> pd.DataFrame:
    """Extract features for Flow Monitor classification."""
    features = pd.DataFrame()
    
    features.loc[0, 'month'] = current_date.month
    
    # Pipe area
    try:
        height = install_data.get('fm_pipe_height_mm', 225)
        width = install_data.get('fm_pipe_width_mm', 225)
        area = int(height) * int(width)
    except:
        area = np.nan
    features.loc[0, 'area'] = area
    
    depth_col = 'DepthData' if 'DepthData' in data.columns else 'Depth'
    velocity_col = 'VelocityData' if 'VelocityData' in data.columns else 'Velocity'
    flow_col = 'FlowData' if 'FlowData' in data.columns else 'Flow'
    
    if flow_col in data.columns and len(data) > 0:
        features.loc[0, 'flow_entropy'] = entropy(data[flow_col].dropna())
    
    if depth_col in data.columns and len(data) > 0:
        depth = data[depth_col].dropna()
        features.loc[0, 'depth_range'] = depth.max() - depth.min()
        features.loc[0, 'depth_skewness'] = depth.skew()
        features.loc[0, 'depth_entropy'] = entropy(depth)
    
    if velocity_col in data.columns and len(data) > 0:
        velocity = data[velocity_col].dropna()
        features.loc[0, 'velocity_iqr'] = velocity.quantile(0.75) - velocity.quantile(0.25)
        features.loc[0, 'velocity_entropy'] = entropy(velocity)
    
    # Frequency features for Flow
    if flow_col in data.columns:
        freq_result = calculate_frequencies(data, flow_col)
        if freq_result and freq_result['total_power'] > 0:
            features.loc[0, 'flow_power_low_freq_ratio'] = freq_result['low_freq_power'] / freq_result['total_power']
            features.loc[0, 'flow_power_medium_freq_ratio'] = freq_result['medium_freq_power'] / freq_result['total_power']
        else:
            features.loc[0, 'flow_power_low_freq_ratio'] = np.nan
            features.loc[0, 'flow_power_medium_freq_ratio'] = np.nan
    
    # Frequency features for Depth
    if depth_col in data.columns:
        freq_result = calculate_frequencies(data, depth_col)
        if freq_result and freq_result['total_power'] > 0:
            features.loc[0, 'depth_power_skewness'] = skew(freq_result['psd'])
            features.loc[0, 'depth_power_low_freq_ratio'] = freq_result['low_freq_power'] / freq_result['total_power']
            features.loc[0, 'depth_power_high_freq_ratio'] = freq_result['high_freq_power'] / freq_result['total_power']
        else:
            features.loc[0, 'depth_power_skewness'] = np.nan
            features.loc[0, 'depth_power_low_freq_ratio'] = np.nan
            features.loc[0, 'depth_power_high_freq_ratio'] = np.nan
    
    # Frequency features for Velocity
    if velocity_col in data.columns:
        freq_result = calculate_frequencies(data, velocity_col)
        if freq_result:
            features.loc[0, 'velocity_dom_freq'] = freq_result['frequencies'][np.argmax(freq_result['psd'])] if len(freq_result['psd']) > 0 else np.nan
            features.loc[0, 'velocity_shannon_entropy'] = -np.sum(freq_result['psd_normalized'] * np.log2(freq_result['psd_normalized'] + 1e-10))
        else:
            features.loc[0, 'velocity_dom_freq'] = np.nan
            features.loc[0, 'velocity_shannon_entropy'] = np.nan
    
    # Ratio features
    if all(col in data.columns for col in [velocity_col, flow_col, depth_col]):
        v_mean = data[velocity_col].mean()
        f_mean = data[flow_col].mean()
        d_mean = data[depth_col].mean()
        d_max = data[depth_col].max()
        
        features.loc[0, 'velocity_to_flow'] = v_mean / f_mean if f_mean != 0 else np.nan
        features.loc[0, 'depth_to_flow'] = d_mean / f_mean if f_mean != 0 else np.nan
        features.loc[0, 'velocity_to_depth'] = v_mean / d_mean if d_mean != 0 else np.nan
        
        pipe_depth = install_data.get('fm_pipe_depth_to_invert_mm', 0)
        features.loc[0, 'depth_to_depth'] = d_mean / pipe_depth if pipe_depth else np.nan
        features.loc[0, 'depth_max_to_depth'] = d_max / pipe_depth if pipe_depth else np.nan
        features.loc[0, 'depth_to_area'] = d_mean / area if area else np.nan
        features.loc[0, 'velocity_to_area'] = v_mean / area if area else np.nan
    
    # Pipe letter one-hot encoding
    pipe_letter = install_data.get('fm_pipe_letter', 'A')
    for letter in ['B', 'D', 'E', 'Y', 'Z']:
        features.loc[0, f'pipe_{letter}'] = pipe_letter == letter
    
    # Pipe shape one-hot encoding
    pipe_shape = install_data.get('fm_pipe_shape', 'Circular')
    features.loc[0, 'shape_C'] = pipe_shape == 'Circular'
    
    features.replace([np.inf, -np.inf], 1000000, inplace=True)
    
    return features


def run_classification(
    install_type: str,
    data: pd.DataFrame,
    start_date: datetime,
    end_date: datetime,
    install_data: Optional[Dict] = None
) -> List[Dict]:
    """
    Run daily classification on timeseries data.
    
    Args:
        install_type: 'Flow Monitor', 'Rain Gauge', or 'Depth Monitor'
        data: DataFrame with Date column and data columns
        start_date: Start of classification period
        end_date: End of classification period
        install_data: Install attributes (for FM: pipe dimensions, etc.)
    
    Returns:
        List of dicts with 'date', 'classification', 'confidence'
    """
    if install_data is None:
        install_data = {}
    
    results = []
    current_date = start_date
    
    # Determine model type
    if install_type == 'Depth Monitor':
        model_type = 'DM'
    elif install_type == 'Rain Gauge':
        model_type = 'RG'
    elif install_type == 'Flow Monitor':
        model_type = 'FM'
    elif install_type in ['Pump Logger', 'Pump Station']:
        # Pump loggers don't have ML classification - just generate date entries for manual override
        current_date = start_date
        while current_date <= end_date:
            results.append({
                'date': current_date.isoformat(),
                'classification': None,  # No ML classification
                'confidence': None
            })
            current_date = current_date + timedelta(days=1)
        return results
    else:
        raise ValueError(f"Unknown install type: {install_type}")
    
    # Load model
    try:
        model = get_model(model_type)
    except FileNotFoundError as e:
        # Return empty results if model not available
        return []
    
    # Ensure Date column is datetime
    if 'Date' in data.columns:
        data['Date'] = pd.to_datetime(data['Date'])
    
    while current_date <= end_date:
        next_date = current_date + timedelta(days=1)
        
        # Filter data for current day
        if 'Date' in data.columns:
            day_data = data[(data['Date'] >= current_date) & (data['Date'] < next_date)]
        else:
            day_data = data
        
        if len(day_data) == 0:
            current_date = next_date
            continue
        
        try:
            # Extract features based on install type
            if model_type == 'DM':
                features = extract_dm_features(day_data)
            elif model_type == 'RG':
                features = extract_rg_features(day_data, current_date)
            elif model_type == 'FM':
                features = extract_fm_features(day_data, current_date, install_data)
            
            # Fill NaN values
            features = features.fillna(0)
            
            # Debug: Print feature comparison for first day only
            if current_date == start_date and model_type == 'FM':
                print(f"Our features ({len(features.columns)}): {list(features.columns)}")
                if hasattr(model, 'feature_names_'):
                    print(f"Model expects ({len(model.feature_names_)}): {model.feature_names_}")
            
            # Reorder features to match model's expected order (for CatBoost)
            if model_type == 'FM' and hasattr(model, 'feature_names_'):
                expected_cols = model.feature_names_
                # Add any missing columns with 0
                for col in expected_cols:
                    if col not in features.columns:
                        features[col] = 0
                # Reorder to match model
                features = features[expected_cols]
            
            # Make prediction
            prediction = model.predict(features)[0]
            if isinstance(prediction, (list, np.ndarray)):
                prediction = prediction[0] if len(prediction) > 0 else 'Unknown'
            
            # Get confidence
            try:
                proba = model.predict_proba(features)[0]
                if hasattr(model, 'classes_'):
                    pred_index = list(model.classes_).index(prediction)
                    confidence = float(proba[pred_index])
                else:
                    confidence = float(max(proba))
            except:
                confidence = 0.0
            
            results.append({
                'date': current_date.isoformat(),
                'classification': str(prediction),
                'confidence': confidence
            })
            
        except Exception as e:
            # Log error but continue with next day
            print(f"Classification error for {current_date}: {e}")
        
        current_date = next_date
    
    return results


def check_models_available() -> Dict[str, bool]:
    """Check which ML models are available."""
    return {
        'DM': (MODELS_DIR / "DM_model.pkl").exists(),
        'RG': (MODELS_DIR / "RG_model.pkl").exists(),
        'FM': (MODELS_DIR / "FM_model.cbm").exists(),
    }
