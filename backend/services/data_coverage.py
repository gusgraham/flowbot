"""
Data Coverage Service
Calculates data coverage metrics for interim reviews.
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlmodel import Session

def calculate_data_coverage(
    session: Session,
    install_id: int,
    start_date: datetime,
    end_date: datetime,
    storage_service,
    install_type: str = None
) -> Tuple[float, List[Dict]]:
    """
    Calculate data coverage percentage and identify gaps for an install.
    
    For pump loggers and event-based monitors, we only check for gaps at the 
    start and end of the period (since they only record state changes, not
    regular intervals).
    
    Args:
        session: Database session
        install_id: Install ID
        start_date: Interim start date
        end_date: Interim end date
        storage_service: Storage service for reading timeseries
        install_type: Type of install (e.g., 'Pump Logger', 'Flow Monitor')
    
    Returns:
        Tuple of (coverage_percentage, gaps_list)
    """
    from domain.fsm import TimeSeries
    import pandas as pd
    
    # Determine if this is event-based data (pump logger records state changes only)
    is_event_based = install_type and ('pump' in install_type.lower() or 'logger' in install_type.lower())
    
    # Get all timeseries for this install
    timeseries = session.query(TimeSeries).filter(
        TimeSeries.install_id == install_id
    ).all()
    
    if not timeseries:
        return 0.0, []
    
    # Expected time range
    total_expected_minutes = (end_date - start_date).total_seconds() / 60
    
    # Collect all timestamps from all variables
    all_timestamps = set()
    
    for ts in timeseries:
        try:
            # Read from the parquet file stored in TimeSeries.filename
            if not ts.filename:
                continue
                
            data = storage_service.read_parquet(ts.filename)
            
            if data is not None and not data.empty:
                # Find time column (could be 'time', 'timestamp', 'Date')
                time_col = None
                for col in ['time', 'timestamp', 'Date']:
                    if col in data.columns:
                        time_col = col
                        break
                
                if time_col:
                    data[time_col] = pd.to_datetime(data[time_col])
                    # Make start/end timezone-naive if they have timezone
                    start_dt = start_date
                    end_dt = end_date
                    if hasattr(start_date, 'tzinfo') and start_date.tzinfo is not None:
                        start_dt = start_date.replace(tzinfo=None)
                    if hasattr(end_date, 'tzinfo') and end_date.tzinfo is not None:
                        end_dt = end_date.replace(tzinfo=None)
                    
                    # Also remove timezone from data if present
                    if hasattr(data[time_col].dt, 'tz') and data[time_col].dt.tz is not None:
                        data[time_col] = data[time_col].dt.tz_localize(None)
                    
                    mask = (data[time_col] >= start_dt) & (data[time_col] <= end_dt)
                    filtered = data.loc[mask, time_col]
                    all_timestamps.update(filtered.tolist())
        except Exception as e:
            print(f"Error reading timeseries {ts.variable} from {ts.filename}: {e}")
            continue
    
    if not all_timestamps:
        return 0.0, [{"start": start_date.isoformat(), "end": end_date.isoformat(), 
                      "duration_hours": total_expected_minutes / 60}]
    
    # Sort timestamps
    sorted_timestamps = sorted(all_timestamps)
    
    # Gap threshold - 30 mins for interval data, no internal gaps for event-based
    gap_threshold_minutes = 30
    gaps = []
    
    # Check gap at start (applies to all types)
    if sorted_timestamps:
        first_ts = sorted_timestamps[0]
        if isinstance(first_ts, str):
            first_ts = pd.to_datetime(first_ts)
        
        start_gap = (first_ts - start_date).total_seconds() / 60
        if start_gap > gap_threshold_minutes:
            gaps.append({
                "start": start_date.isoformat(),
                "end": first_ts.isoformat() if hasattr(first_ts, 'isoformat') else str(first_ts),
                "duration_hours": start_gap / 60
            })
    
    # Check internal gaps - ONLY for interval-based data (not pump loggers)
    if not is_event_based:
        for i in range(len(sorted_timestamps) - 1):
            t1 = sorted_timestamps[i]
            t2 = sorted_timestamps[i + 1]
            
            if isinstance(t1, str):
                t1 = pd.to_datetime(t1)
            if isinstance(t2, str):
                t2 = pd.to_datetime(t2)
            
            gap_minutes = (t2 - t1).total_seconds() / 60
            
            if gap_minutes > gap_threshold_minutes:
                gaps.append({
                    "start": t1.isoformat() if hasattr(t1, 'isoformat') else str(t1),
                    "end": t2.isoformat() if hasattr(t2, 'isoformat') else str(t2),
                    "duration_hours": gap_minutes / 60
                })
    
    # Check gap at end (applies to all types)
    if sorted_timestamps:
        last_ts = sorted_timestamps[-1]
        if isinstance(last_ts, str):
            last_ts = pd.to_datetime(last_ts)
        
        end_gap = (end_date - last_ts).total_seconds() / 60
        if end_gap > gap_threshold_minutes:
            gaps.append({
                "start": last_ts.isoformat() if hasattr(last_ts, 'isoformat') else str(last_ts),
                "end": end_date.isoformat(),
                "duration_hours": end_gap / 60
            })
    
    # Calculate coverage
    total_gap_minutes = sum(g["duration_hours"] * 60 for g in gaps)
    covered_minutes = total_expected_minutes - total_gap_minutes
    coverage_pct = max(0, min(100, (covered_minutes / total_expected_minutes) * 100)) if total_expected_minutes > 0 else 0
    
    return coverage_pct, gaps


def update_review_coverage(
    session: Session,
    review_id: int,
    storage_service
) -> Dict:
    """
    Calculate and update data coverage for a specific review.
    """
    from domain.interim import InterimReview, Interim
    
    review = session.get(InterimReview, review_id)
    if not review:
        return {"error": "Review not found"}
    
    interim = session.get(Interim, review.interim_id)
    if not interim:
        return {"error": "Interim not found"}
    
    coverage_pct, gaps = calculate_data_coverage(
        session=session,
        install_id=review.install_id,
        start_date=interim.start_date,
        end_date=interim.end_date,
        storage_service=storage_service,
        install_type=review.install_type
    )
    
    review.data_coverage_pct = coverage_pct
    review.gaps_json = json.dumps(gaps)
    
    session.add(review)
    session.commit()
    
    return {
        "coverage_pct": coverage_pct,
        "gaps_count": len(gaps),
        "gaps": gaps
    }
