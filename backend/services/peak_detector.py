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
        prominence: Optional[float] = None,
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
            prominence: Minimum peak prominence (None = no threshold)
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
        
        # Configure find_peaks args
        kwargs = {
            'width': width,
            'distance': distance
        }
        if prominence is not None:
            kwargs['prominence'] = prominence

        # Find peaks
        peak_indices, properties = find_peaks(smoothed, **kwargs)
        
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
        
        # Filter NaNs
        mask = ~(np.isnan(obs_arr) | np.isnan(pred_arr))
        obs_valid = obs_arr[mask]
        pred_valid = pred_arr[mask]
        
        if len(obs_valid) < 2:
            return -99999.0
            
        mean_obs = np.mean(obs_valid)
        numerator = np.sum((obs_valid - pred_valid) ** 2)
        denominator = np.sum((obs_valid - mean_obs) ** 2)
        
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
    
    def calculate_kge_components(self, obs: List[float], pred: List[float]) -> Dict[str, float]:
        """
        Calculate Kling-Gupta Efficiency and return all components.
        
        Returns:
            Dictionary with keys:
            - 'kge': Overall KGE value
            - 'r': Correlation coefficient (Pearson)
            - 'alpha': Variability ratio (σ_pred / σ_obs)
            - 'beta': Bias ratio (μ_pred / μ_obs)
        """
        if len(obs) != len(pred) or len(obs) < 2:
            return {'kge': -99999.0, 'r': -99999.0, 'alpha': -99999.0, 'beta': -99999.0}
        
        df = pd.DataFrame({'obs': obs, 'pred': pred})
        
        # Correlation (r)
        r = df['obs'].corr(df['pred'])
        if np.isnan(r):
            r = -1.0  # Worst case
        
        # Standard deviations
        obs_std = df['obs'].std()
        pred_std = df['pred'].std()
        
        # Means
        obs_mean = df['obs'].mean()
        pred_mean = df['pred'].mean()
        
        # Avoid division by zero
        if obs_std == 0 or obs_mean == 0:
            return {'kge': -99999.0, 'r': float(r), 'alpha': -99999.0, 'beta': -99999.0}
        
        # α (alpha) = variability ratio = σ_pred / σ_obs
        alpha = pred_std / obs_std
        
        # β (beta) = bias ratio = μ_pred / μ_obs
        beta = pred_mean / obs_mean
        
        # Calculate KGE
        kge = 1 - np.sqrt(
            (r - 1) ** 2 +
            (alpha - 1) ** 2 +
            (beta - 1) ** 2
        )
        
        return {
            'kge': round(float(kge), 4),
            'r': round(float(r), 4),
            'alpha': round(float(alpha), 4),
            'beta': round(float(beta), 4)
        }
    
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
        
        Uses greedy temporal matching to pair peaks, then returns the 
        worst (maximum absolute) time difference across all pairs.
        """
        matched_pairs = self.match_peaks_by_time(obs_peaks, pred_peaks)
        
        if not matched_pairs:
            return -99999.0
        
        # Calculate time diff for each pair, return worst case
        max_diff_hrs = 0.0
        for obs_peak, pred_peak in matched_pairs:
            diff_seconds = (pred_peak.timestamp - obs_peak.timestamp).total_seconds()
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
        
        Uses greedy temporal matching to pair peaks, then returns the 
        worst (maximum absolute) differences.
        
        Returns:
            Tuple of (percentage difference, absolute difference)
        """
        matched_pairs = self.match_peaks_by_time(obs_peaks, pred_peaks)
        
        if not matched_pairs:
            return (-99999.0, -99999.0)
        
        # Calculate diffs for each pair, track worst case
        max_diff_pct = 0.0
        max_diff_abs = 0.0
        
        for obs_peak, pred_peak in matched_pairs:
            diff_abs = pred_peak.value - obs_peak.value
            if obs_peak.value != 0:
                diff_pct = (diff_abs / obs_peak.value) * 100
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
        
        # Convert to numpy for easier NaN handling
        obs_arr = np.array(obs)
        pred_arr = np.array(pred)
        
        # For volume, we just ignore NaNs in each series independently? 
        # Or should we only count valid pairs?
        # Usually volume is total volume. So Independent Sum is better.
        # Just filter NaNs from each.
        
        obs_valid = obs_arr[~np.isnan(obs_arr)]
        pred_valid = pred_arr[~np.isnan(pred_arr)]
        
        if len(obs_valid) == 0:
            return -99999.0
            
        obs_volume = np.sum(obs_valid) * timestep_minutes * 60
        pred_volume = np.sum(pred_valid) * timestep_minutes * 60
        
        if obs_volume == 0:
            return 0.0
        
        diff_pct = ((pred_volume - obs_volume) / obs_volume) * 100
        return float(diff_pct)
    
    def match_peaks_by_time(
        self,
        obs_peaks: List[PeakInfo],
        pred_peaks: List[PeakInfo],
        max_time_gap_hours: float = 24.0
    ) -> List[Tuple[PeakInfo, PeakInfo]]:
        """
        Match peaks between observed and predicted by minimizing temporal difference.
        
        Uses greedy matching: sort all possible pairs by time difference, 
        then greedily select pairs ensuring no peak is matched twice.
        Orphaned peaks (no match within max_time_gap_hours) are ignored.
        
        Returns:
            List of (obs_peak, pred_peak) tuples, sorted by time
        """
        if not obs_peaks or not pred_peaks:
            return []
        
        # Build all possible pairs with their time differences
        pairs = []
        for obs in obs_peaks:
            for pred in pred_peaks:
                diff_hrs = abs((pred.timestamp - obs.timestamp).total_seconds()) / 3600
                if diff_hrs <= max_time_gap_hours:
                    pairs.append((diff_hrs, obs, pred))
        
        # Sort by time difference (closest first)
        pairs.sort(key=lambda x: x[0])
        
        # Greedy matching - select pairs without reuse
        matched_pairs = []
        used_obs = set()
        used_pred = set()
        
        for diff_hrs, obs, pred in pairs:
            if obs.index not in used_obs and pred.index not in used_pred:
                matched_pairs.append((obs, pred))
                used_obs.add(obs.index)
                used_pred.add(pred.index)
        
        # Sort matched pairs by observed peak time
        matched_pairs.sort(key=lambda x: x[0].timestamp)
        
        return matched_pairs
    
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
        smoothing_frac: float = 0.0,
        n_peaks: int = 1
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
            n_peaks: Max peaks to detect (default 1 for single peak comparison)
            
        Returns:
            VerificationMetrics with all calculated values
        """
        # Detect peaks
        obs_peaks = self.detect_peaks(obs_series, timestamps, smoothing_frac, n_peaks=n_peaks)
        pred_peaks = self.detect_peaks(pred_series, timestamps, smoothing_frac, n_peaks=n_peaks)
        
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
