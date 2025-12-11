"""
Peak Detection and Metrics Calculation Service

Implements peak detection using scipy.signal and calculates verification metrics
including NSE, KGE, peak timing, peak magnitude, and volume differences.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from scipy.signal import find_peaks, peak_prominences, savgol_filter

@dataclass
class PeakInfo:
    """Information about a detected peak."""
    index: int
    timestamp: datetime
    value: float
    prominence: float


@dataclass
class MetricResult:
    """Result of a single metric calculation."""
    name: str
    value: float
    unit: str = ""


@dataclass
class VerificationMetrics:
    """Complete set of verification metrics for a parameter."""
    parameter: str  # FLOW, DEPTH
    
    # Scoring metrics
    nse: float  # Nash-Sutcliffe Efficiency
    peak_time_diff_hrs: float  # Maximum time difference between peaks
    peak_diff_pct: float  # Maximum peak magnitude difference (%)
    peak_diff_abs: float  # Maximum peak magnitude difference (absolute)
    volume_diff_pct: Optional[float]  # Volume difference (flow only)
    
    # Display metrics (not for scoring)
    kge: float  # Kling-Gupta Efficiency
    cv_obs: float  # Coefficient of Variation (observed)
    
    # Peak lists for visualization
    obs_peaks: List[PeakInfo]
    pred_peaks: List[PeakInfo]

class PeakDetector:
    """
    Peak detection and verification metrics calculation.
    
    Uses scipy.signal for peak detection with optional Savitzky-Golay smoothing.
    """
    
    def __init__(self, default_smoothing_frac: float = 0.0):
        """
        Initialize peak detector.
        
        Args:
            default_smoothing_frac: Default smoothing fraction (0.0-1.0)
                                  Mapped to window length for Savitzky-Golay
        """
        self.default_smoothing_frac = default_smoothing_frac
    
    def detect_peaks(
        self, 
        series: List[float],
        timestamps: List[datetime],
        smoothing_frac: float = None,
        prominence: float = 0.0009,
        width: int = 1,
        distance: int = 1,
        n_peaks: Optional[int] = None
    ) -> List[PeakInfo]:
        """
        Detect peaks in a time series.
        
        Args:
            series: List of values
            timestamps: Corresponding timestamps
            smoothing_frac: Smoothing fraction (0.0 = no smoothing)
            prominence: Minimum peak prominence
            width: Minimum peak width
            distance: Minimum distance between peaks
            n_peaks: If specified, return only the N most prominent peaks
            
        Returns:
            List of PeakInfo objects
        """
        if not series or len(series) < 3:
            return []
        
        frac = smoothing_frac if smoothing_frac is not None else self.default_smoothing_frac
        
        # Apply smoothing if requested
        if frac > 0:
            smoothed = self.smooth_series(series, frac)
        else:
            smoothed = np.array(series)
        
        # Find peaks
        peak_indices, properties = find_peaks(
            smoothed,
            prominence=prominence,
            width=width,
            distance=distance
        )
        
        if len(peak_indices) == 0:
            return []
        
        # Get prominences
        prominences, _, _ = peak_prominences(smoothed, peak_indices)
        
        # If n_peaks specified, filter to most prominent
        if n_peaks is not None and len(peak_indices) > n_peaks:
            # Sort by prominence descending
            sorted_indices = np.argsort(prominences)[::-1][:n_peaks]
            # Re-sort by time (indices) to maintain chronological order
            # Note: sorted_indices are indices INTO peak_indices
            peaks_subset_indices = sorted(sorted_indices, key=lambda i: peak_indices[i])
            # Wait, easier way:
            top_indices = sorted_indices
            # We want to keep them in time order
            top_indices_sorted_by_time = sorted(top_indices, key=lambda i: peak_indices[i])
            
            peak_indices = peak_indices[top_indices_sorted_by_time]
            prominences = prominences[top_indices_sorted_by_time]
        
        # Build results
        peaks = []
        for i, idx in enumerate(peak_indices):
            if idx < len(timestamps):
                peaks.append(PeakInfo(
                    index=int(idx),
                    timestamp=timestamps[idx],
                    value=float(smoothed[idx]),
                    prominence=float(prominences[i]) if i < len(prominences) else 0.0
                ))
        
        return peaks
    
    def smooth_series(self, series: List[float], frac: float) -> np.ndarray:
        """
        Apply smoothing to a series.
        Uses Savitzky-Golay filter.
        
        Args:
            series: Data to smooth
            frac: Fraction of data length to use as window size (0.0 - 1.0)
        """
        data = np.array(series)
        n = len(data)
        if n < 4:
            return data
            
        # Map frac to window length
        # Window length must be odd and positive
        window_length = int(n * frac)
        if window_length % 2 == 0:
            window_length += 1
        
        if window_length < 3:
            return data
            
        if window_length >= n:
            window_length = n - 2 if n % 2 == 0 else n - 1
            
        try:
            # Polyorder 2 or 3 is typical
            polyorder = 2
            if window_length <= polyorder:
               polyorder = window_length - 1
            
            smoothed = savgol_filter(data, window_length=window_length, polyorder=polyorder)
            return smoothed
        except Exception as e:
            print(f"Smoothing error: {e}")
            return data
    
    def calculate_nse(self, obs: List[float], pred: List[float]) -> float:
        """
        Calculate Nash-Sutcliffe Efficiency.
        
        NSE = 1 - (sum((obs - pred)^2) / sum((obs - mean(obs))^2))
        
        Range: -inf to 1.0 (1.0 = perfect, <0 = worse than mean)
        """
        if len(obs) != len(pred) or len(obs) < 2:
            return -99999.0
        
        obs_arr = np.array(obs)
        pred_arr = np.array(pred)
        
        mean_obs = np.mean(obs_arr)
        numerator = np.sum((obs_arr - pred_arr) ** 2)
        denominator = np.sum((obs_arr - mean_obs) ** 2)
        
        if denominator == 0:
            return 0.0
        
        return float(1 - (numerator / denominator))
    
    def calculate_kge(self, obs: List[float], pred: List[float]) -> float:
        """
        Calculate Kling-Gupta Efficiency.
        
        KGE = 1 - sqrt((r-1)^2 + (σ_pred/σ_obs - 1)^2 + (μ_pred/μ_obs - 1)^2)
        
        Where r is correlation coefficient.
        Range: -inf to 1.0 (1.0 = perfect)
        """
        if len(obs) != len(pred) or len(obs) < 2:
            return -99999.0
        
        df = pd.DataFrame({'obs': obs, 'pred': pred})
        
        # Correlation
        correl = df['obs'].corr(df['pred'])
        if np.isnan(correl):
            correl = -1  # Worst case
        
        # Standard deviations
        obs_std = df['obs'].std()
        pred_std = df['pred'].std()
        
        # Means
        obs_mean = df['obs'].mean()
        pred_mean = df['pred'].mean()
        
        # Avoid division by zero
        if obs_std == 0 or obs_mean == 0:
            return -99999.0
        
        # Calculate KGE
        kge = 1 - np.sqrt(
            (correl - 1) ** 2 +
            (pred_std / obs_std - 1) ** 2 +
            (pred_mean / obs_mean - 1) ** 2
        )
        
        return round(float(kge), 4)
    
    def calculate_cv(self, series: List[float]) -> float:
        """
        Calculate Coefficient of Variation.
        
        CV = σ / μ
        """
        if len(series) < 2:
            return 0.0
        
        arr = np.array(series)
        mean = np.mean(arr)
        
        if mean == 0:
            return 0.0
        
        return float(np.std(arr) / mean)
    
    def calculate_peak_time_diff(
        self, 
        obs_peaks: List[PeakInfo], 
        pred_peaks: List[PeakInfo]
    ) -> float:
        """
        Calculate maximum time difference between matched peaks in hours.
        
        Returns the worst (maximum absolute) time difference.
        """
        if not obs_peaks or not pred_peaks:
            return -99999.0
        
        max_diff_hrs = 0.0
        
        # For each observed peak, find closest predicted peak
        for obs_peak in obs_peaks:
            closest = self._find_closest_peak(obs_peak, pred_peaks)
            if closest:
                diff_seconds = abs((closest.timestamp - obs_peak.timestamp).total_seconds())
                diff_hrs = diff_seconds / 3600
                if abs(diff_hrs) > abs(max_diff_hrs):
                    max_diff_hrs = diff_hrs
        
        # For each predicted peak, find closest observed peak
        for pred_peak in pred_peaks:
            closest = self._find_closest_peak(pred_peak, obs_peaks)
            if closest:
                diff_seconds = (pred_peak.timestamp - closest.timestamp).total_seconds()
                diff_hrs = diff_seconds / 3600
                if abs(diff_hrs) > abs(max_diff_hrs):
                    max_diff_hrs = diff_hrs
        
        return float(max_diff_hrs)
    
    def calculate_peak_diff(
        self, 
        obs_peaks: List[PeakInfo], 
        pred_peaks: List[PeakInfo]
    ) -> Tuple[float, float]:
        """
        Calculate maximum peak magnitude difference.
        
        Returns:
            Tuple of (percentage difference, absolute difference)
        """
        if not obs_peaks or not pred_peaks:
            return (-99999.0, -99999.0)
        
        max_diff_pct = 0.0
        max_diff_abs = 0.0
        
        for pred_peak in pred_peaks:
            closest_obs = self._find_closest_peak(pred_peak, obs_peaks)
            if closest_obs:
                diff_abs = pred_peak.value - closest_obs.value
                if closest_obs.value != 0:
                    diff_pct = (diff_abs / closest_obs.value) * 100
                else:
                    diff_pct = 99999.0
                
                if abs(diff_pct) > abs(max_diff_pct):
                    max_diff_pct = diff_pct
                if abs(diff_abs) > abs(max_diff_abs):
                    max_diff_abs = diff_abs
        
        return (float(max_diff_pct), float(max_diff_abs))
    
    def calculate_volume_diff(
        self, 
        obs: List[float], 
        pred: List[float], 
        timestep_minutes: int
    ) -> float:
        """
        Calculate volume difference as percentage.
        
        Volume = sum(flow) * timestep * 60 (in m3 if flow is m3/s)
        """
        if len(obs) != len(pred) or len(obs) < 2:
            return -99999.0
        
        obs_volume = sum(obs) * timestep_minutes * 60
        pred_volume = sum(pred) * timestep_minutes * 60
        
        if obs_volume == 0:
            return 0.0
        
        diff_pct = ((pred_volume - obs_volume) / obs_volume) * 100
        return float(diff_pct)
    
    def _find_closest_peak(
        self, 
        target: PeakInfo, 
        candidates: List[PeakInfo]
    ) -> Optional[PeakInfo]:
        """Find the peak from candidates closest in time to target."""
        if not candidates:
            return None
        
        closest = None
        min_diff = float('inf')
        
        for candidate in candidates:
            diff = abs((candidate.timestamp - target.timestamp).total_seconds())
            if diff < min_diff:
                min_diff = diff
                closest = candidate
        
        return closest
    
    def calculate_all_metrics(
        self,
        obs_series: List[float],
        pred_series: List[float],
        timestamps: List[datetime],
        parameter: str,
        timestep_minutes: int,
        smoothing_frac: float = 0.0
    ) -> VerificationMetrics:
        """
        Calculate all verification metrics for a parameter.
        
        Args:
            obs_series: Observed data
            pred_series: Predicted data
            timestamps: Timestamps for data
            parameter: 'FLOW' or 'DEPTH'
            timestep_minutes: Data timestep
            smoothing_frac: Smoothing for peak detection
            
        Returns:
            VerificationMetrics with all calculated values
        """
        # Detect peaks
        obs_peaks = self.detect_peaks(obs_series, timestamps, smoothing_frac)
        pred_peaks = self.detect_peaks(pred_series, timestamps, smoothing_frac)
        
        # Calculate metrics
        nse = self.calculate_nse(obs_series, pred_series)
        kge = self.calculate_kge(obs_series, pred_series)
        cv_obs = self.calculate_cv(obs_series)
        
        peak_time_diff = self.calculate_peak_time_diff(obs_peaks, pred_peaks)
        peak_diff_pct, peak_diff_abs = self.calculate_peak_diff(obs_peaks, pred_peaks)
        
        # Volume only for flow
        volume_diff_pct = None
        if parameter.upper() == 'FLOW':
            volume_diff_pct = self.calculate_volume_diff(obs_series, pred_series, timestep_minutes)
        
        return VerificationMetrics(
            parameter=parameter.upper(),
            nse=nse,
            peak_time_diff_hrs=peak_time_diff,
            peak_diff_pct=peak_diff_pct,
            peak_diff_abs=peak_diff_abs,
            volume_diff_pct=volume_diff_pct,
            kge=kge,
            cv_obs=cv_obs,
            obs_peaks=obs_peaks,
            pred_peaks=pred_peaks
        )


# Convenience function
def calculate_verification_metrics(
    obs_flow: List[float],
    pred_flow: List[float],
    obs_depth: List[float],
    pred_depth: List[float],
    timestamps: List[datetime],
    timestep_minutes: int,
    smoothing_frac: float = 0.0
) -> Dict[str, VerificationMetrics]:
    """
    Calculate metrics for both flow and depth.
    
    Returns dict with 'flow' and 'depth' keys.
    """
    detector = PeakDetector()
    
    return {
        'flow': detector.calculate_all_metrics(
            obs_flow, pred_flow, timestamps, 'FLOW', timestep_minutes, smoothing_frac
        ),
        'depth': detector.calculate_all_metrics(
            obs_depth, pred_depth, timestamps, 'DEPTH', timestep_minutes, smoothing_frac
        )
    }
