"""
Tolerance and Scoring Service

Applies tolerance thresholds to verification metrics and calculates
score bands (OK/FAIR/NO) according to A7P criteria.
"""
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from services.peak_detector import VerificationMetrics


@dataclass
class ToleranceConfig:
    """Configuration for tolerance thresholds."""
    event_type: str = "STORM"
    is_critical: bool = False
    is_surcharged: bool = False
    
    # Depth tolerances
    depth_time_tolerance_hrs: float = 0.5
    depth_peak_tolerance_pct: float = 10.0
    depth_peak_tolerance_abs_m: float = 0.1
    depth_peak_surcharged_upper_m: float = 0.5
    depth_peak_surcharged_lower_m: float = 0.1
    
    # Flow tolerances
    flow_nse_threshold: float = 0.5
    flow_time_tolerance_hrs: float = 0.5
    flow_peak_tolerance_upper_pct: float = 25.0
    flow_peak_tolerance_lower_pct: float = 15.0
    flow_volume_tolerance_upper_pct: float = 20.0
    flow_volume_tolerance_lower_pct: float = 10.0
    
    @classmethod
    def for_critical(cls) -> "ToleranceConfig":
        """Create tolerance config for critical locations."""
        return cls(
            is_critical=True,
            flow_peak_tolerance_upper_pct=10.0,
            flow_peak_tolerance_lower_pct=10.0,
            flow_volume_tolerance_upper_pct=10.0,
            flow_volume_tolerance_lower_pct=10.0,
            depth_peak_tolerance_pct=0.0,  # Use absolute only
            depth_peak_tolerance_abs_m=0.1,
        )
    
    @classmethod
    def for_general(cls, is_surcharged: bool = False) -> "ToleranceConfig":
        """Create tolerance config for general (non-critical) locations."""
        return cls(
            is_critical=False,
            is_surcharged=is_surcharged,
            flow_peak_tolerance_upper_pct=25.0,
            flow_peak_tolerance_lower_pct=15.0,
            flow_volume_tolerance_upper_pct=20.0,
            flow_volume_tolerance_lower_pct=10.0,
            depth_peak_tolerance_pct=10.0,
            depth_peak_tolerance_abs_m=0.1,
            depth_peak_surcharged_upper_m=0.5,
            depth_peak_surcharged_lower_m=0.1,
        )


@dataclass
class MetricScore:
    """Score for a single metric."""
    metric_name: str
    value: float
    score_band: str  # OK, FAIR, NO, NA
    score_points: int  # 3=OK, 2=FAIR, 0=NO, 0=NA
    tolerance_description: str


@dataclass
class ParameterScore:
    """Aggregate score for a parameter (FLOW or DEPTH)."""
    parameter: str
    metrics: Dict[str, MetricScore]
    total_points: int
    max_points: int
    score_fraction: float  # 0.0 to 1.0


class ToleranceScorer:
    """
    Applies tolerance thresholds and calculates verification scores.
    
    Scoring based on A7P Hydraulic Model Verification criteria:
    - OK (3 points): Within tolerance
    - FAIR (2 points): Within near-miss margin
    - NO (0 points): Outside tolerance
    - NA (0 points): Missing/unreliable data
    """
    
    # Near-miss margins for FAIR scoring
    NEAR_MISS_MARGIN = {
        'depth_abs': 0.05,  # Extra 0.05m beyond threshold for FAIR
        'pct': 5.0,  # Extra 5% beyond threshold for FAIR
        'time': 0.25,  # Extra 0.25 hours beyond threshold for FAIR
    }
    
    def __init__(self, config: ToleranceConfig = None):
        self.config = config or ToleranceConfig.for_general()
    
    def score_flow_metrics(self, metrics: VerificationMetrics) -> ParameterScore:
        """Score flow verification metrics."""
        scores = {}
        
        # NSE (Shape)
        scores['nse'] = self._score_nse(metrics.nse)
        
        # Peak timing
        scores['peak_time_diff_hrs'] = self._score_flow_peak_time(metrics.peak_time_diff_hrs)
        
        # Peak flow magnitude
        scores['peak_flow_diff_pcnt'] = self._score_flow_peak_magnitude(metrics.peak_diff_pct)
        
        # Volume
        if metrics.volume_diff_pct is not None:
            scores['volume_diff_pcnt'] = self._score_flow_volume(metrics.volume_diff_pct)
        
        # Calculate totals
        total_points = sum(s.score_points for s in scores.values())
        max_points = len(scores) * 3
        
        return ParameterScore(
            parameter='FLOW',
            metrics=scores,
            total_points=total_points,
            max_points=max_points,
            score_fraction=total_points / max_points if max_points > 0 else 0.0
        )
    
    def score_depth_metrics(self, metrics: VerificationMetrics) -> ParameterScore:
        """Score depth verification metrics."""
        scores = {}
        
        # Peak timing
        scores['peak_time_diff_hrs'] = self._score_depth_peak_time(metrics.peak_time_diff_hrs)
        
        # Peak depth magnitude
        scores['peak_depth_diff_m'] = self._score_depth_peak_magnitude(
            metrics.peak_diff_pct, 
            metrics.peak_diff_abs
        )
        
        # Calculate totals
        total_points = sum(s.score_points for s in scores.values())
        max_points = len(scores) * 3
        
        return ParameterScore(
            parameter='DEPTH',
            metrics=scores,
            total_points=total_points,
            max_points=max_points,
            score_fraction=total_points / max_points if max_points > 0 else 0.0
        )
    
    def _score_nse(self, nse: float) -> MetricScore:
        """Score NSE (Nash-Sutcliffe Efficiency)."""
        threshold = self.config.flow_nse_threshold
        
        if nse == -99999.0:
            return MetricScore(
                metric_name='nse',
                value=nse,
                score_band='NA',
                score_points=0,
                tolerance_description=f'NSE > {threshold}'
            )
        
        if nse > threshold:
            band, points = 'OK', 3
        elif nse > threshold - 0.1:  # Near miss
            band, points = 'FAIR', 2
        else:
            band, points = 'NO', 0
        
        return MetricScore(
            metric_name='nse',
            value=round(nse, 3),
            score_band=band,
            score_points=points,
            tolerance_description=f'NSE > {threshold}'
        )
    
    def _score_flow_peak_time(self, diff_hrs: float) -> MetricScore:
        """Score flow peak timing difference."""
        threshold = self.config.flow_time_tolerance_hrs
        
        if diff_hrs == -99999.0:
            return MetricScore(
                metric_name='peak_time_diff_hrs',
                value=diff_hrs,
                score_band='NA',
                score_points=0,
                tolerance_description=f'±{threshold} hrs'
            )
        
        abs_diff = abs(diff_hrs)
        if abs_diff <= threshold:
            band, points = 'OK', 3
        elif abs_diff <= threshold + self.NEAR_MISS_MARGIN['time']:
            band, points = 'FAIR', 2
        else:
            band, points = 'NO', 0
        
        return MetricScore(
            metric_name='peak_time_diff_hrs',
            value=round(diff_hrs, 2),
            score_band=band,
            score_points=points,
            tolerance_description=f'±{threshold} hrs'
        )
    
    def _score_flow_peak_magnitude(self, diff_pct: float) -> MetricScore:
        """Score flow peak magnitude difference."""
        upper = self.config.flow_peak_tolerance_upper_pct
        lower = self.config.flow_peak_tolerance_lower_pct
        
        if diff_pct == -99999.0 or diff_pct == 99999.0:
            return MetricScore(
                metric_name='peak_flow_diff_pcnt',
                value=diff_pct,
                score_band='NA',
                score_points=0,
                tolerance_description=f'+{upper}% / -{lower}%'
            )
        
        # Check asymmetric tolerance
        if -lower <= diff_pct <= upper:
            band, points = 'OK', 3
        elif -lower - self.NEAR_MISS_MARGIN['pct'] <= diff_pct <= upper + self.NEAR_MISS_MARGIN['pct']:
            band, points = 'FAIR', 2
        else:
            band, points = 'NO', 0
        
        return MetricScore(
            metric_name='peak_flow_diff_pcnt',
            value=round(diff_pct, 1),
            score_band=band,
            score_points=points,
            tolerance_description=f'+{upper}% / -{lower}%'
        )
    
    def _score_flow_volume(self, diff_pct: float) -> MetricScore:
        """Score flow volume difference."""
        upper = self.config.flow_volume_tolerance_upper_pct
        lower = self.config.flow_volume_tolerance_lower_pct
        
        if diff_pct == -99999.0:
            return MetricScore(
                metric_name='volume_diff_pcnt',
                value=diff_pct,
                score_band='NA',
                score_points=0,
                tolerance_description=f'+{upper}% / -{lower}%'
            )
        
        if -lower <= diff_pct <= upper:
            band, points = 'OK', 3
        elif -lower - self.NEAR_MISS_MARGIN['pct'] <= diff_pct <= upper + self.NEAR_MISS_MARGIN['pct']:
            band, points = 'FAIR', 2
        else:
            band, points = 'NO', 0
        
        return MetricScore(
            metric_name='volume_diff_pcnt',
            value=round(diff_pct, 1),
            score_band=band,
            score_points=points,
            tolerance_description=f'+{upper}% / -{lower}%'
        )
    
    def _score_depth_peak_time(self, diff_hrs: float) -> MetricScore:
        """Score depth peak timing difference."""
        threshold = self.config.depth_time_tolerance_hrs
        
        if diff_hrs == -99999.0:
            return MetricScore(
                metric_name='peak_time_diff_hrs',
                value=diff_hrs,
                score_band='NA',
                score_points=0,
                tolerance_description=f'±{threshold} hrs'
            )
        
        abs_diff = abs(diff_hrs)
        if abs_diff <= threshold:
            band, points = 'OK', 3
        elif abs_diff <= threshold + self.NEAR_MISS_MARGIN['time']:
            band, points = 'FAIR', 2
        else:
            band, points = 'NO', 0
        
        return MetricScore(
            metric_name='peak_time_diff_hrs',
            value=round(diff_hrs, 2),
            score_band=band,
            score_points=points,
            tolerance_description=f'±{threshold} hrs'
        )
    
    def _score_depth_peak_magnitude(self, diff_pct: float, diff_abs: float) -> MetricScore:
        """
        Score depth peak magnitude difference.
        
        For critical: ±0.1m only
        For general (un-surcharged): ±0.1m or ±10%, whichever is greater
        For general (surcharged): +0.5m to -0.1m
        """
        is_critical = self.config.is_critical
        is_surcharged = self.config.is_surcharged
        
        if diff_abs == -99999.0:
            return MetricScore(
                metric_name='peak_depth_diff_m',
                value=diff_abs,
                score_band='NA',
                score_points=0,
                tolerance_description='See criteria'
            )
        
        if is_critical:
            # Critical: ±0.1m absolute only
            threshold = self.config.depth_peak_tolerance_abs_m
            if abs(diff_abs) <= threshold:
                band, points = 'OK', 3
            elif abs(diff_abs) <= threshold + self.NEAR_MISS_MARGIN['depth_abs']:
                band, points = 'FAIR', 2
            else:
                band, points = 'NO', 0
            desc = f'±{threshold}m'
            
        elif is_surcharged:
            # Surcharged: +0.5m to -0.1m
            upper = self.config.depth_peak_surcharged_upper_m
            lower = self.config.depth_peak_surcharged_lower_m
            if -lower <= diff_abs <= upper:
                band, points = 'OK', 3
            elif -lower - self.NEAR_MISS_MARGIN['depth_abs'] <= diff_abs <= upper + self.NEAR_MISS_MARGIN['depth_abs']:
                band, points = 'FAIR', 2
            else:
                band, points = 'NO', 0
            desc = f'+{upper}m / -{lower}m'
            
        else:
            # General: ±0.1m or ±10%, whichever is greater
            pct_threshold = self.config.depth_peak_tolerance_pct
            abs_threshold = self.config.depth_peak_tolerance_abs_m
            
            within_pct = abs(diff_pct) <= pct_threshold if diff_pct != -99999.0 else False
            within_abs = abs(diff_abs) <= abs_threshold
            
            if within_pct or within_abs:
                band, points = 'OK', 3
            else:
                # Check near-miss
                near_pct = abs(diff_pct) <= pct_threshold + self.NEAR_MISS_MARGIN['pct'] if diff_pct != -99999.0 else False
                near_abs = abs(diff_abs) <= abs_threshold + self.NEAR_MISS_MARGIN['depth_abs']
                if near_pct or near_abs:
                    band, points = 'FAIR', 2
                else:
                    band, points = 'NO', 0
            desc = f'±{abs_threshold}m or ±{pct_threshold}%'
        
        return MetricScore(
            metric_name='peak_depth_diff_m',
            value=round(diff_abs, 3),
            score_band=band,
            score_points=points,
            tolerance_description=desc
        )
    
    def get_overall_status(self, flow_score: ParameterScore, depth_score: ParameterScore) -> str:
        """
        Determine overall verification status.
        
        Based on aggregate scoring:
        - VERIFIED: ≥75% of max points
        - MARGINAL: 50-75% of max points
        - NOT_VERIFIED: <50% of max points
        """
        total_points = flow_score.total_points + depth_score.total_points
        max_points = flow_score.max_points + depth_score.max_points
        
        if max_points == 0:
            return 'PENDING'
        
        fraction = total_points / max_points
        
        if fraction >= 0.75:
            return 'VERIFIED'
        elif fraction >= 0.5:
            return 'MARGINAL'
        else:
            return 'NOT_VERIFIED'


def score_verification_results(
    flow_metrics: VerificationMetrics,
    depth_metrics: VerificationMetrics,
    is_critical: bool = False,
    is_surcharged: bool = False,
    is_depth_only: bool = False
) -> Dict:
    """
    Convenience function to score verification results.
    
    Returns dict with flow_score, depth_score, and overall_status.
    """
    if is_critical:
        config = ToleranceConfig.for_critical()
    else:
        config = ToleranceConfig.for_general(is_surcharged)
    
    scorer = ToleranceScorer(config)
    
    if is_depth_only:
        # Ignore flow metrics for scoring
        flow_score = ParameterScore(
            parameter='FLOW',
            metrics={},
            total_points=0,
            max_points=0,
            score_fraction=0.0
        )
    else:
        flow_score = scorer.score_flow_metrics(flow_metrics)
        
    depth_score = scorer.score_depth_metrics(depth_metrics)
    overall_status = scorer.get_overall_status(flow_score, depth_score)
    
    return {
        'flow_score': flow_score,
        'depth_score': depth_score,
        'overall_status': overall_status
    }
